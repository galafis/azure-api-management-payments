"""Demo script for the Payment Processing System.

Demonstrates processing payments via credit card, PIX, and boleto,
including refunds, cancellations, and webhook notifications.
"""

from src.payments.processor import PaymentProcessor
from src.payments.models import PaymentMethod, PaymentMethodType
from src.webhooks.notifier import WebhookNotifier


def print_separator() -> None:
    """Print a visual separator line."""
    print("=" * 60)


def demo_payment_processing() -> None:
    """Demonstrate the full payment processing lifecycle."""
    print_separator()
    print("PAYMENT PROCESSING DEMO")
    print_separator()

    # Initialize notifier and processor
    notifier = WebhookNotifier()
    processor = PaymentProcessor(notifier=notifier)

    # Register a webhook endpoint
    webhook = notifier.register_endpoint(
        url="https://example.com/webhook",
        events=["payment.processed", "payment.refunded", "payment.cancelled"],
    )
    print(f"\nWebhook registered: {webhook.url}")

    # Register payment methods
    credit_card = processor.register_payment_method(
        PaymentMethod(
            type=PaymentMethodType.CREDIT_CARD,
            last_four="4242",
            brand="Visa",
            holder_name="Gabriel Lafis",
        )
    )
    print(f"Credit card registered: **** {credit_card.last_four} ({credit_card.brand})")

    pix = processor.register_payment_method(
        PaymentMethod(
            type=PaymentMethodType.PIX,
            pix_key="gabriel@example.com",
            holder_name="Gabriel Lafis",
        )
    )
    print(f"PIX registered: {pix.pix_key}")

    boleto = processor.register_payment_method(
        PaymentMethod(
            type=PaymentMethodType.BOLETO,
            holder_name="Gabriel Lafis",
        )
    )
    print(f"Boleto registered for: {boleto.holder_name}")

    # Process credit card payment
    print(f"\n--- Credit Card Payment ---")
    cc_response = processor.process_payment(
        amount=15000,  # R$ 150.00
        payment_method_id=credit_card.id,
        description="Annual subscription",
        customer_id="cust_001",
        customer_email="customer@example.com",
        idempotency_key="pay_cc_001",
    )
    print(f"Status: {cc_response['message']}")
    print(f"Amount: {cc_response['data']['amount_display']}")
    print(f"Transaction ID: {cc_response['data']['id']}")

    # Test idempotency - same key returns same result
    print(f"\n--- Idempotency Test (same key) ---")
    cc_response_retry = processor.process_payment(
        amount=15000,
        payment_method_id=credit_card.id,
        description="Annual subscription",
        customer_id="cust_001",
        idempotency_key="pay_cc_001",
    )
    print(f"Same transaction returned: {cc_response_retry['data']['id'] == cc_response['data']['id']}")

    # Process PIX payment
    print(f"\n--- PIX Payment ---")
    pix_response = processor.process_payment(
        amount=5000,  # R$ 50.00
        payment_method_id=pix.id,
        description="Product purchase",
        customer_id="cust_002",
        idempotency_key="pay_pix_001",
    )
    print(f"Status: {pix_response['message']}")
    print(f"Amount: {pix_response['data']['amount_display']}")

    # Process boleto payment
    print(f"\n--- Boleto Payment ---")
    boleto_response = processor.process_payment(
        amount=250000,  # R$ 2,500.00
        payment_method_id=boleto.id,
        description="Invoice #12345",
        customer_id="cust_003",
        idempotency_key="pay_boleto_001",
    )
    print(f"Status: {boleto_response['message']}")
    print(f"Amount: {boleto_response['data']['amount_display']}")

    # Partial refund on credit card payment
    print(f"\n--- Partial Refund ---")
    refund_response = processor.refund_transaction(
        transaction_id=cc_response["data"]["id"],
        amount=5000,  # R$ 50.00
        reason="Customer requested partial refund",
    )
    print(f"Refund: {refund_response['message']}")
    print(f"Refund amount: {refund_response['data']['refund']['amount_display']}")
    print(f"Transaction status: {refund_response['data']['transaction']['status']}")

    # Cancel boleto payment
    print(f"\n--- Cancel Boleto ---")
    cancel_response = processor.cancel_transaction(
        transaction_id=boleto_response["data"]["id"]
    )
    print(f"Cancel: {cancel_response['message']}")

    # List all transactions
    print(f"\n--- All Transactions ---")
    transactions = processor.list_transactions()
    for txn in transactions:
        print(f"  {txn.id[:8]}... | {txn.payment_method_type.value:12s} | "
              f"R$ {txn.amount_decimal:>10,.2f} | {txn.status.value}")

    # Webhook deliveries
    print(f"\n--- Webhook Deliveries ---")
    deliveries = notifier.get_deliveries()
    for d in deliveries:
        print(f"  {d.event:25s} | {d.status} | HTTP {d.response_code}")

    print(f"\nTotal webhook deliveries: {notifier.total_deliveries}")
    print()


def main() -> None:
    """Run all demo functions."""
    print("\n  PAYMENT PROCESSING SYSTEM")
    print("  Sistema de Processamento de Pagamentos\n")

    demo_payment_processing()

    print_separator()
    print("Demo complete / Demo concluida")
    print_separator()


if __name__ == "__main__":
    main()
