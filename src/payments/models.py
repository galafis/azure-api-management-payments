"""Data models for the payment processing system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class PaymentStatus(Enum):
    """Possible states of a payment transaction."""

    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"


class PaymentMethodType(Enum):
    """Supported payment method types."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"
    BOLETO = "boleto"


class RefundStatus(Enum):
    """Possible states of a refund."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PaymentMethod:
    """Represents a payment method.

    Attributes:
        id: Unique identifier.
        type: Payment method type (credit_card, pix, boleto, etc.).
        last_four: Last four digits of card number (cards only).
        brand: Card brand (Visa, Mastercard, etc.) for card payments.
        holder_name: Name of the payment method holder.
        pix_key: PIX key for PIX payments.
        boleto_code: Boleto barcode for boleto payments.
        active: Whether this payment method is active.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: PaymentMethodType = PaymentMethodType.CREDIT_CARD
    last_four: str = ""
    brand: str = ""
    holder_name: str = ""
    pix_key: str = ""
    boleto_code: str = ""
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "last_four": self.last_four,
            "brand": self.brand,
            "holder_name": self.holder_name,
            "pix_key": self.pix_key,
            "boleto_code": self.boleto_code,
            "active": self.active,
        }


@dataclass
class Transaction:
    """Represents a payment transaction.

    Attributes:
        id: Unique transaction identifier.
        idempotency_key: Key to prevent duplicate processing.
        amount: Transaction amount in cents (integer).
        currency: ISO 4217 currency code.
        status: Current transaction status.
        payment_method_id: ID of the payment method used.
        payment_method_type: Type of payment method used.
        description: Transaction description.
        customer_id: Customer identifier.
        customer_email: Customer email address.
        metadata: Additional key-value metadata.
        created_at: Timestamp when created.
        updated_at: Timestamp when last updated.
        approved_at: Timestamp when approved.
        error_message: Error description if failed.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str = ""
    amount: int = 0  # in cents
    currency: str = "BRL"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method_id: str = ""
    payment_method_type: PaymentMethodType = PaymentMethodType.CREDIT_CARD
    description: str = ""
    customer_id: str = ""
    customer_email: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    error_message: str = ""

    @property
    def amount_decimal(self) -> float:
        """Return amount as a decimal value."""
        return self.amount / 100.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "idempotency_key": self.idempotency_key,
            "amount": self.amount,
            "amount_display": f"R$ {self.amount_decimal:,.2f}",
            "currency": self.currency,
            "status": self.status.value,
            "payment_method_id": self.payment_method_id,
            "payment_method_type": self.payment_method_type.value,
            "description": self.description,
            "customer_id": self.customer_id,
            "customer_email": self.customer_email,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "error_message": self.error_message,
        }


@dataclass
class Refund:
    """Represents a refund on a transaction.

    Attributes:
        id: Unique refund identifier.
        transaction_id: ID of the original transaction.
        amount: Refund amount in cents.
        status: Current refund status.
        reason: Reason for the refund.
        created_at: Timestamp when created.
        completed_at: Timestamp when completed.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str = ""
    amount: int = 0  # in cents
    status: RefundStatus = RefundStatus.PENDING
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    @property
    def amount_decimal(self) -> float:
        """Return amount as a decimal value."""
        return self.amount / 100.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "amount_display": f"R$ {self.amount_decimal:,.2f}",
            "status": self.status.value,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
