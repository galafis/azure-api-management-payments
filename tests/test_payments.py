"""Tests for the payment processing system - models, processor, idempotency, and webhooks."""

import unittest
from datetime import datetime, timedelta

from src.payments.models import (
    Transaction,
    PaymentMethod,
    PaymentMethodType,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from src.payments.processor import PaymentProcessor
from src.payments.idempotency import IdempotencyStore
from src.webhooks.notifier import WebhookNotifier


class TestPaymentModels(unittest.TestCase):
    """Test payment data models."""

    def test_transaction_creation(self):
        txn = Transaction(amount=1000, currency="BRL")
        self.assertEqual(txn.amount, 1000)
        self.assertEqual(txn.status, PaymentStatus.PENDING)

    def test_transaction_amount_decimal(self):
        txn = Transaction(amount=15050)
        self.assertEqual(txn.amount_decimal, 150.50)

    def test_transaction_to_dict(self):
        txn = Transaction(amount=1000, description="Test")
        d = txn.to_dict()
        self.assertIn("id", d)
        self.assertIn("amount_display", d)
        self.assertEqual(d["amount"], 1000)

    def test_payment_method_creation(self):
        pm = PaymentMethod(
            type=PaymentMethodType.CREDIT_CARD, last_four="1234", brand="Visa"
        )
        self.assertEqual(pm.last_four, "1234")
        self.assertTrue(pm.active)

    def test_payment_method_to_dict(self):
        pm = PaymentMethod(type=PaymentMethodType.PIX, pix_key="test@test.com")
        d = pm.to_dict()
        self.assertEqual(d["type"], "pix")
        self.assertEqual(d["pix_key"], "test@test.com")

    def test_refund_creation(self):
        refund = Refund(transaction_id="txn_123", amount=500, reason="Defective")
        self.assertEqual(refund.amount, 500)
        self.assertEqual(refund.status, RefundStatus.PENDING)

    def test_refund_amount_decimal(self):
        refund = Refund(amount=2550)
        self.assertEqual(refund.amount_decimal, 25.50)

    def test_payment_status_values(self):
        self.assertEqual(PaymentStatus.APPROVED.value, "approved")
        self.assertEqual(PaymentStatus.DECLINED.value, "declined")

    def test_payment_method_types(self):
        self.assertEqual(PaymentMethodType.CREDIT_CARD.value, "credit_card")
        self.assertEqual(PaymentMethodType.PIX.value, "pix")
        self.assertEqual(PaymentMethodType.BOLETO.value, "boleto")


class TestIdempotencyStore(unittest.TestCase):
    """Test idempotency key management."""

    def setUp(self):
        self.store = IdempotencyStore(ttl_hours=24)

    def test_set_and_get(self):
        self.store.set("key1", "txn_1", {"status": 200})
        entry = self.store.get("key1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.transaction_id, "txn_1")

    def test_get_nonexistent(self):
        entry = self.store.get("nonexistent")
        self.assertIsNone(entry)

    def test_exists(self):
        self.store.set("key1", "txn_1", {})
        self.assertTrue(self.store.exists("key1"))
        self.assertFalse(self.store.exists("key2"))

    def test_remove(self):
        self.store.set("key1", "txn_1", {})
        self.assertTrue(self.store.remove("key1"))
        self.assertFalse(self.store.exists("key1"))

    def test_remove_nonexistent(self):
        self.assertFalse(self.store.remove("nonexistent"))

    def test_size(self):
        self.assertEqual(self.store.size, 0)
        self.store.set("k1", "t1", {})
        self.store.set("k2", "t2", {})
        self.assertEqual(self.store.size, 2)

    def test_expired_entry_returns_none(self):
        self.store.set("key1", "txn_1", {})
        entry = self.store._store["key1"]
        entry.expires_at = datetime.utcnow() - timedelta(hours=1)
        self.assertIsNone(self.store.get("key1"))

    def test_cleanup_expired(self):
        self.store.set("k1", "t1", {})
        self.store.set("k2", "t2", {})
        # Expire one entry
        self.store._store["k1"].expires_at = datetime.utcnow() - timedelta(hours=1)
        removed = self.store.cleanup_expired()
        self.assertEqual(removed, 1)
        self.assertEqual(self.store.size, 1)


class TestPaymentProcessor(unittest.TestCase):
    """Test payment processor operations."""

    def setUp(self):
        self.notifier = WebhookNotifier()
        self.processor = PaymentProcessor(notifier=self.notifier)

        self.credit_card = self.processor.register_payment_method(
            PaymentMethod(
                type=PaymentMethodType.CREDIT_CARD,
                last_four="4242",
                brand="Visa",
                holder_name="Test User",
            )
        )
        self.pix = self.processor.register_payment_method(
            PaymentMethod(
                type=PaymentMethodType.PIX,
                pix_key="test@test.com",
                holder_name="Test User",
            )
        )
        self.boleto = self.processor.register_payment_method(
            PaymentMethod(
                type=PaymentMethodType.BOLETO,
                holder_name="Test User",
            )
        )

    def test_register_payment_method(self):
        methods = self.processor.list_payment_methods()
        self.assertEqual(len(methods), 3)

    def test_deactivate_payment_method(self):
        self.assertTrue(self.processor.deactivate_payment_method(self.credit_card.id))
        methods = self.processor.list_payment_methods(active_only=True)
        self.assertEqual(len(methods), 2)

    def test_process_credit_card_payment(self):
        response = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
            customer_id="cust_1",
        )
        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["status"], "approved")

    def test_process_pix_payment(self):
        response = self.processor.process_payment(
            amount=3000,
            payment_method_id=self.pix.id,
        )
        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["status"], "approved")

    def test_process_boleto_payment(self):
        response = self.processor.process_payment(
            amount=10000,
            payment_method_id=self.boleto.id,
        )
        # Boleto stays pending
        self.assertEqual(response["data"]["status"], "pending")

    def test_process_payment_invalid_amount(self):
        response = self.processor.process_payment(
            amount=0,
            payment_method_id=self.credit_card.id,
        )
        self.assertEqual(response["status"], 400)

    def test_process_payment_invalid_method(self):
        response = self.processor.process_payment(
            amount=1000,
            payment_method_id="nonexistent",
        )
        self.assertEqual(response["status"], 404)

    def test_process_payment_inactive_method(self):
        self.processor.deactivate_payment_method(self.credit_card.id)
        response = self.processor.process_payment(
            amount=1000,
            payment_method_id=self.credit_card.id,
        )
        self.assertEqual(response["status"], 400)

    def test_idempotency_returns_same_result(self):
        r1 = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
            idempotency_key="idem_001",
        )
        r2 = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
            idempotency_key="idem_001",
        )
        self.assertEqual(r1["data"]["id"], r2["data"]["id"])

    def test_cancel_pending_transaction(self):
        response = self.processor.process_payment(
            amount=10000,
            payment_method_id=self.boleto.id,
        )
        cancel = self.processor.cancel_transaction(response["data"]["id"])
        self.assertEqual(cancel["status"], 200)
        self.assertEqual(cancel["data"]["status"], "cancelled")

    def test_cancel_approved_fails(self):
        response = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
        )
        cancel = self.processor.cancel_transaction(response["data"]["id"])
        self.assertEqual(cancel["status"], 400)

    def test_cancel_nonexistent_transaction(self):
        cancel = self.processor.cancel_transaction("nonexistent")
        self.assertEqual(cancel["status"], 404)

    def test_full_refund(self):
        response = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
        )
        refund = self.processor.refund_transaction(response["data"]["id"])
        self.assertEqual(refund["status"], 200)
        self.assertEqual(refund["data"]["transaction"]["status"], "refunded")

    def test_partial_refund(self):
        response = self.processor.process_payment(
            amount=10000,
            payment_method_id=self.credit_card.id,
        )
        refund = self.processor.refund_transaction(
            response["data"]["id"], amount=3000
        )
        self.assertEqual(refund["status"], 200)
        self.assertEqual(
            refund["data"]["transaction"]["status"], "partially_refunded"
        )

    def test_refund_exceeds_amount(self):
        response = self.processor.process_payment(
            amount=5000,
            payment_method_id=self.credit_card.id,
        )
        self.processor.refund_transaction(response["data"]["id"], amount=3000)
        over_refund = self.processor.refund_transaction(
            response["data"]["id"], amount=3000
        )
        self.assertEqual(over_refund["status"], 400)

    def test_list_transactions_filter_by_customer(self):
        self.processor.process_payment(
            amount=1000, payment_method_id=self.credit_card.id, customer_id="c1"
        )
        self.processor.process_payment(
            amount=2000, payment_method_id=self.credit_card.id, customer_id="c2"
        )
        txns = self.processor.list_transactions(customer_id="c1")
        self.assertEqual(len(txns), 1)


class TestWebhookNotifier(unittest.TestCase):
    """Test webhook notification system."""

    def setUp(self):
        self.notifier = WebhookNotifier()

    def test_register_endpoint(self):
        ep = self.notifier.register_endpoint(
            url="https://example.com/hook", events=["payment.processed"]
        )
        self.assertIsNotNone(ep.id)
        self.assertEqual(len(self.notifier.list_endpoints()), 1)

    def test_unregister_endpoint(self):
        ep = self.notifier.register_endpoint(
            url="https://example.com/hook", events=[]
        )
        self.assertTrue(self.notifier.unregister_endpoint(ep.id))
        self.assertEqual(len(self.notifier.list_endpoints()), 0)

    def test_notify_delivers_to_subscribed(self):
        self.notifier.register_endpoint(
            url="https://example.com/hook", events=["payment.processed"]
        )
        deliveries = self.notifier.notify("payment.processed", {"amount": 100})
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0].status, "delivered")

    def test_notify_skips_unsubscribed_event(self):
        self.notifier.register_endpoint(
            url="https://example.com/hook", events=["payment.refunded"]
        )
        deliveries = self.notifier.notify("payment.processed", {"amount": 100})
        self.assertEqual(len(deliveries), 0)

    def test_notify_empty_events_receives_all(self):
        self.notifier.register_endpoint(url="https://example.com/hook", events=[])
        deliveries = self.notifier.notify("any.event", {"data": "test"})
        self.assertEqual(len(deliveries), 1)

    def test_deactivate_endpoint(self):
        ep = self.notifier.register_endpoint(url="https://example.com", events=[])
        self.notifier.deactivate_endpoint(ep.id)
        deliveries = self.notifier.notify("test.event", {})
        self.assertEqual(len(deliveries), 0)

    def test_get_deliveries(self):
        self.notifier.register_endpoint(url="https://example.com", events=[])
        self.notifier.notify("event1", {})
        self.notifier.notify("event2", {})
        deliveries = self.notifier.get_deliveries()
        self.assertEqual(len(deliveries), 2)

    def test_total_deliveries(self):
        self.notifier.register_endpoint(url="https://example.com", events=[])
        self.notifier.notify("e1", {})
        self.notifier.notify("e2", {})
        self.assertEqual(self.notifier.total_deliveries, 2)


if __name__ == "__main__":
    unittest.main()
