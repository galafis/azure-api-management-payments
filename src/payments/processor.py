"""Payment processing engine.

Handles the lifecycle of payment transactions including creation,
authorization, capture, cancellation, and refunds across multiple
payment method types (credit card, PIX, boleto).
"""

import uuid
from datetime import datetime
from typing import Optional

from .models import (
    Transaction,
    PaymentMethod,
    PaymentMethodType,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from .idempotency import IdempotencyStore
from ..webhooks.notifier import WebhookNotifier


class PaymentProcessor:
    """Processes payment transactions across multiple payment methods.

    Manages the full payment lifecycle including idempotency checks,
    payment method validation, transaction processing, and refund handling.
    """

    def __init__(self, notifier: Optional[WebhookNotifier] = None) -> None:
        self._transactions: dict[str, Transaction] = {}
        self._payment_methods: dict[str, PaymentMethod] = {}
        self._refunds: dict[str, Refund] = {}
        self._idempotency = IdempotencyStore()
        self._notifier = notifier or WebhookNotifier()

    # --- Payment Method Management ---

    def register_payment_method(self, method: PaymentMethod) -> PaymentMethod:
        """Register a new payment method.

        Args:
            method: The PaymentMethod to register.

        Returns:
            The registered PaymentMethod.
        """
        self._payment_methods[method.id] = method
        return method

    def get_payment_method(self, method_id: str) -> Optional[PaymentMethod]:
        """Retrieve a payment method by ID."""
        return self._payment_methods.get(method_id)

    def list_payment_methods(self, active_only: bool = True) -> list[PaymentMethod]:
        """List payment methods, optionally filtering by active status."""
        methods = list(self._payment_methods.values())
        if active_only:
            methods = [m for m in methods if m.active]
        return methods

    def deactivate_payment_method(self, method_id: str) -> bool:
        """Deactivate a payment method."""
        method = self._payment_methods.get(method_id)
        if method:
            method.active = False
            return True
        return False

    # --- Transaction Processing ---

    def process_payment(
        self,
        amount: int,
        payment_method_id: str,
        description: str = "",
        customer_id: str = "",
        customer_email: str = "",
        idempotency_key: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Process a new payment transaction.

        Args:
            amount: Amount in cents (must be positive).
            payment_method_id: ID of the payment method to use.
            description: Transaction description.
            customer_id: Customer identifier.
            customer_email: Customer email for notifications.
            idempotency_key: Optional key to prevent duplicate processing.
            metadata: Optional additional metadata.

        Returns:
            Response dictionary with transaction details.
        """
        # Check idempotency
        if idempotency_key:
            existing = self._idempotency.get(idempotency_key)
            if existing:
                return existing.response

        # Validate amount
        if amount <= 0:
            return {
                "status": 400,
                "message": "Amount must be greater than zero",
            }

        # Validate payment method
        method = self._payment_methods.get(payment_method_id)
        if not method:
            return {
                "status": 404,
                "message": "Payment method not found",
            }

        if not method.active:
            return {
                "status": 400,
                "message": "Payment method is not active",
            }

        # Create transaction
        transaction = Transaction(
            idempotency_key=idempotency_key,
            amount=amount,
            status=PaymentStatus.PROCESSING,
            payment_method_id=payment_method_id,
            payment_method_type=method.type,
            description=description,
            customer_id=customer_id,
            customer_email=customer_email,
            metadata=metadata or {},
        )

        # Simulate processing based on payment type
        self._execute_payment(transaction, method)

        # Store transaction
        self._transactions[transaction.id] = transaction

        response = {
            "status": 200 if transaction.status == PaymentStatus.APPROVED else 400,
            "message": self._get_status_message(transaction.status),
            "data": transaction.to_dict(),
        }

        # Store idempotency entry
        if idempotency_key:
            self._idempotency.set(idempotency_key, transaction.id, response)

        # Send webhook notification
        self._notifier.notify(
            event="payment.processed",
            data=transaction.to_dict(),
        )

        return response

    def _execute_payment(
        self, transaction: Transaction, method: PaymentMethod
    ) -> None:
        """Execute payment processing based on the payment method type.

        Simulates different processing flows for each payment type.

        Args:
            transaction: The transaction to process.
            method: The payment method being used.
        """
        if method.type == PaymentMethodType.CREDIT_CARD:
            self._process_credit_card(transaction, method)
        elif method.type == PaymentMethodType.DEBIT_CARD:
            self._process_credit_card(transaction, method)
        elif method.type == PaymentMethodType.PIX:
            self._process_pix(transaction)
        elif method.type == PaymentMethodType.BOLETO:
            self._process_boleto(transaction)
        else:
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = "Unsupported payment method type"

    def _process_credit_card(
        self, transaction: Transaction, method: PaymentMethod
    ) -> None:
        """Simulate credit/debit card processing."""
        # Simulate validation: decline if amount > 100000 (R$ 1000.00)
        if transaction.amount > 10000000:
            transaction.status = PaymentStatus.DECLINED
            transaction.error_message = "Transaction amount exceeds limit"
            return

        if not method.last_four:
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = "Invalid card information"
            return

        transaction.status = PaymentStatus.APPROVED
        transaction.approved_at = datetime.utcnow()

    def _process_pix(self, transaction: Transaction) -> None:
        """Simulate PIX payment processing (instant approval)."""
        transaction.status = PaymentStatus.APPROVED
        transaction.approved_at = datetime.utcnow()

    def _process_boleto(self, transaction: Transaction) -> None:
        """Simulate boleto processing (pending until paid)."""
        transaction.status = PaymentStatus.PENDING

    # --- Transaction Queries ---

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Retrieve a transaction by ID."""
        return self._transactions.get(transaction_id)

    def list_transactions(
        self,
        customer_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
    ) -> list[Transaction]:
        """List transactions with optional filtering."""
        txns = list(self._transactions.values())
        if customer_id:
            txns = [t for t in txns if t.customer_id == customer_id]
        if status:
            txns = [t for t in txns if t.status == status]
        return sorted(txns, key=lambda t: t.created_at, reverse=True)

    # --- Transaction Lifecycle ---

    def cancel_transaction(self, transaction_id: str) -> dict:
        """Cancel a pending or processing transaction.

        Args:
            transaction_id: The transaction to cancel.

        Returns:
            Response dictionary with updated transaction.
        """
        transaction = self._transactions.get(transaction_id)
        if not transaction:
            return {"status": 404, "message": "Transaction not found"}

        if transaction.status not in (
            PaymentStatus.PENDING,
            PaymentStatus.PROCESSING,
        ):
            return {
                "status": 400,
                "message": f"Cannot cancel transaction in '{transaction.status.value}' status",
            }

        transaction.status = PaymentStatus.CANCELLED
        transaction.updated_at = datetime.utcnow()

        self._notifier.notify(
            event="payment.cancelled",
            data=transaction.to_dict(),
        )

        return {
            "status": 200,
            "message": "Transaction cancelled",
            "data": transaction.to_dict(),
        }

    def refund_transaction(
        self,
        transaction_id: str,
        amount: Optional[int] = None,
        reason: str = "",
    ) -> dict:
        """Refund a completed transaction (full or partial).

        Args:
            transaction_id: The transaction to refund.
            amount: Refund amount in cents (None for full refund).
            reason: Reason for the refund.

        Returns:
            Response dictionary with refund details.
        """
        transaction = self._transactions.get(transaction_id)
        if not transaction:
            return {"status": 404, "message": "Transaction not found"}

        if transaction.status not in (
            PaymentStatus.APPROVED,
            PaymentStatus.PARTIALLY_REFUNDED,
        ):
            return {
                "status": 400,
                "message": f"Cannot refund transaction in '{transaction.status.value}' status",
            }

        # Calculate refund amount
        refund_amount = amount if amount is not None else transaction.amount

        # Check total refunds do not exceed transaction amount
        existing_refunds = [
            r
            for r in self._refunds.values()
            if r.transaction_id == transaction_id
            and r.status == RefundStatus.COMPLETED
        ]
        total_refunded = sum(r.amount for r in existing_refunds)

        if total_refunded + refund_amount > transaction.amount:
            return {
                "status": 400,
                "message": "Refund amount exceeds remaining transaction balance",
            }

        # Create refund
        refund = Refund(
            transaction_id=transaction_id,
            amount=refund_amount,
            status=RefundStatus.COMPLETED,
            reason=reason,
            completed_at=datetime.utcnow(),
        )
        self._refunds[refund.id] = refund

        # Update transaction status
        total_refunded += refund_amount
        if total_refunded >= transaction.amount:
            transaction.status = PaymentStatus.REFUNDED
        else:
            transaction.status = PaymentStatus.PARTIALLY_REFUNDED
        transaction.updated_at = datetime.utcnow()

        self._notifier.notify(
            event="payment.refunded",
            data={
                "transaction": transaction.to_dict(),
                "refund": refund.to_dict(),
            },
        )

        return {
            "status": 200,
            "message": "Refund processed",
            "data": {
                "refund": refund.to_dict(),
                "transaction": transaction.to_dict(),
            },
        }

    def get_refund(self, refund_id: str) -> Optional[Refund]:
        """Retrieve a refund by ID."""
        return self._refunds.get(refund_id)

    def list_refunds(
        self, transaction_id: Optional[str] = None
    ) -> list[Refund]:
        """List refunds, optionally filtered by transaction ID."""
        refunds = list(self._refunds.values())
        if transaction_id:
            refunds = [r for r in refunds if r.transaction_id == transaction_id]
        return sorted(refunds, key=lambda r: r.created_at, reverse=True)

    @staticmethod
    def _get_status_message(status: PaymentStatus) -> str:
        """Get a human-readable message for a payment status."""
        messages = {
            PaymentStatus.PENDING: "Payment is pending",
            PaymentStatus.PROCESSING: "Payment is being processed",
            PaymentStatus.APPROVED: "Payment approved successfully",
            PaymentStatus.DECLINED: "Payment was declined",
            PaymentStatus.CANCELLED: "Payment was cancelled",
            PaymentStatus.REFUNDED: "Payment has been refunded",
            PaymentStatus.FAILED: "Payment processing failed",
        }
        return messages.get(status, "Unknown status")
