"""Webhook notification system for payment status changes.

Provides an in-memory webhook registration and notification system
that logs events and delivers payloads to registered webhook URLs.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class WebhookEndpoint:
    """Represents a registered webhook endpoint.

    Attributes:
        id: Unique endpoint identifier.
        url: The webhook callback URL.
        events: List of event types to subscribe to.
        active: Whether this endpoint is active.
        secret: Secret key for payload signing.
        created_at: Timestamp when registered.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    events: list[str] = field(default_factory=list)
    active: bool = True
    secret: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class WebhookDelivery:
    """Records a webhook delivery attempt.

    Attributes:
        id: Unique delivery identifier.
        endpoint_id: The webhook endpoint ID.
        event: The event type.
        payload: The JSON payload sent.
        status: Delivery status (pending, delivered, failed).
        response_code: HTTP response code received.
        delivered_at: Timestamp of delivery.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint_id: str = ""
    event: str = ""
    payload: str = ""
    status: str = "pending"
    response_code: Optional[int] = None
    delivered_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "event": self.event,
            "status": self.status,
            "response_code": self.response_code,
            "delivered_at": (
                self.delivered_at.isoformat() if self.delivered_at else None
            ),
        }


class WebhookNotifier:
    """Manages webhook endpoint registration and event notification.

    In production, this would make HTTP POST requests to registered
    webhook URLs. This implementation simulates delivery and stores
    delivery records for testing and demonstration purposes.
    """

    def __init__(self) -> None:
        self._endpoints: dict[str, WebhookEndpoint] = {}
        self._deliveries: list[WebhookDelivery] = []

    def register_endpoint(
        self,
        url: str,
        events: list[str],
        secret: str = "",
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint.

        Args:
            url: The callback URL.
            events: List of event types to subscribe to (e.g., ['payment.processed']).
            secret: Optional secret for HMAC signing.

        Returns:
            The registered WebhookEndpoint.
        """
        endpoint = WebhookEndpoint(url=url, events=events, secret=secret)
        self._endpoints[endpoint.id] = endpoint
        return endpoint

    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Remove a webhook endpoint.

        Args:
            endpoint_id: The endpoint to remove.

        Returns:
            True if the endpoint was found and removed.
        """
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            return True
        return False

    def deactivate_endpoint(self, endpoint_id: str) -> bool:
        """Deactivate a webhook endpoint without removing it."""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint:
            endpoint.active = False
            return True
        return False

    def list_endpoints(self, active_only: bool = True) -> list[WebhookEndpoint]:
        """List registered webhook endpoints."""
        endpoints = list(self._endpoints.values())
        if active_only:
            endpoints = [e for e in endpoints if e.active]
        return endpoints

    def notify(self, event: str, data: dict) -> list[WebhookDelivery]:
        """Send a webhook notification for an event.

        Finds all active endpoints subscribed to the given event type
        and simulates delivery of the payload.

        Args:
            event: The event type (e.g., 'payment.processed').
            data: The event payload data.

        Returns:
            List of WebhookDelivery records for each notification sent.
        """
        deliveries = []
        payload = json.dumps(
            {
                "event": event,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            },
            default=str,
        )

        for endpoint in self._endpoints.values():
            if not endpoint.active:
                continue

            # Check if endpoint subscribes to this event
            # An empty events list means subscribe to all events
            if endpoint.events and event not in endpoint.events:
                continue

            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event=event,
                payload=payload,
                status="delivered",  # Simulated success
                response_code=200,
                delivered_at=datetime.utcnow(),
            )

            self._deliveries.append(delivery)
            deliveries.append(delivery)

        return deliveries

    def get_deliveries(
        self,
        endpoint_id: Optional[str] = None,
        event: Optional[str] = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        """Retrieve webhook delivery records.

        Args:
            endpoint_id: Filter by endpoint ID.
            event: Filter by event type.
            limit: Maximum number of records to return.

        Returns:
            List of matching WebhookDelivery records.
        """
        deliveries = self._deliveries.copy()

        if endpoint_id:
            deliveries = [d for d in deliveries if d.endpoint_id == endpoint_id]
        if event:
            deliveries = [d for d in deliveries if d.event == event]

        return deliveries[-limit:]

    @property
    def total_deliveries(self) -> int:
        """Return total number of delivery records."""
        return len(self._deliveries)
