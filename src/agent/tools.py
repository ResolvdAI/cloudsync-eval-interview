"""
Custom tools for the Customer Support Agent.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from enum import Enum

from llama_index.core.tools import FunctionTool

# Set up logging
logger = logging.getLogger(__name__)

# Interview reference date. Every mock timestamp is relative to this instant
# so billing dates and ticket created_at stay consistent and repeatable.
# last_payment.date is always before this date; next_billing_date is after it.
FIXED_NOW = datetime(2026, 9, 23, 12, 0, 0)


class TicketPriority(Enum):
    """Support ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(Enum):
    """Support ticket categories."""
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    OTHER = "other"


class BillingLookupTool:
    """
    Tool for looking up customer billing information.

    This is a mock implementation that returns simulated billing data.
    In production, this would connect to actual billing systems.
    """

    def __init__(self):
        """Initialize the billing lookup tool."""
        self.name = "lookup_billing"
        self.description = (
            "Look up a customer's billing only when the user asks about billing "
            "and provides an email address or customer ID. "
            "Pass customer_email or customer_id exactly as provided. Do not invent identifiers. "
            "Returns subscription status, billing history, and payment method. "
            "If neither identifier is provided, returns an error."
        )

        # Mock data for demonstration
        self._mock_customers = self._generate_mock_customers()

    def _generate_mock_customers(self) -> Dict[str, Dict[str, Any]]:
        """Generate fixed mock customer billing data (deterministic)."""
        fixtures = [
            {
                "email": "john.doe@example.com",
                "customer_id": "cust_1000",
                "plan": "Professional",
                "status": "active",
                "monthly_amount": 29,
                "next_billing_date": "2026-10-01",
                "payment_method": "card",
                "last_payment": {
                    "date": "2026-09-01",
                    "amount": 29,
                    "status": "successful",
                },
            },
            {
                "email": "jane.smith@company.com",
                "customer_id": "cust_1001",
                "plan": "Professional",
                "status": "active",
                "monthly_amount": 29,
                "next_billing_date": "2026-10-20",
                "payment_method": "card",
                "last_payment": {
                    "date": "2026-08-20",
                    "amount": 29,
                    "status": "successful",
                },
            },
            {
                # Matches sample conv_003 (upgrade from Basic → Professional)
                "email": "support@startup.io",
                "customer_id": "cust_1002",
                "plan": "Basic",
                "status": "active",
                "monthly_amount": 9,
                "next_billing_date": "2026-10-25",
                "payment_method": "ach",
                "last_payment": {
                    "date": "2026-08-25",
                    "amount": 9,
                    "status": "successful",
                },
            },
            {
                "email": "admin@enterprise.org",
                "customer_id": "cust_1003",
                "plan": "Enterprise",
                "status": "active",
                "monthly_amount": 299,
                "next_billing_date": "2026-10-15",
                "payment_method": "invoice",
                "last_payment": {
                    "date": "2026-09-15",
                    "amount": 299,
                    "status": "successful",
                },
            },
            {
                "email": "user@test.com",
                "customer_id": "cust_1004",
                "plan": "Free",
                "status": "trialing",
                "monthly_amount": 0,
                "next_billing_date": "2026-10-08",
                "payment_method": "card",
                "last_payment": {
                    "date": "2026-09-01",
                    "amount": 0,
                    "status": "successful",
                },
            },
        ]

        customers: Dict[str, Dict[str, Any]] = {}
        for fixture in fixtures:
            record = dict(fixture)
            customers[fixture["email"]] = record
            customers[fixture["customer_id"]] = record

        return customers

    def lookup(
        self,
        customer_email: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Look up billing information for a customer.

        Args:
            customer_email: Customer's email address
            customer_id: Customer's ID

        Returns:
            Dictionary containing billing information
        """
        logger.info(
            f"💳 BillingLookupTool called - email: {customer_email}, id: {customer_id}")

        if not customer_email and not customer_id:
            logger.warning(
                "BillingLookupTool: No customer identifier provided")
            return {
                "error": "Either customer_email or customer_id is required"
            }

        # Look up customer
        lookup_key = customer_email or customer_id
        if lookup_key in self._mock_customers:
            return {
                "success": True,
                "data": self._mock_customers[lookup_key]
            }

        # Customer not found — deterministic placeholder (no random IDs)
        return {
            "success": False,
            "data": {
                "customer_id": customer_id or "cust_unknown",
                "email": customer_email or "unknown@example.com",
                "plan": None,
                "status": None,
                "monthly_amount": None,
                "next_billing_date": None,
                "payment_method": None,
                "last_payment": None,
                "message": "Customer not found"
            }
        }

    def as_function_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.lookup,
            name=self.name,
            description=self.description,
        )


class TicketCreationTool:
    """
    Tool for creating support tickets.

    This tool creates support tickets for issues that require escalation
    or cannot be immediately resolved through automated responses.
    """

    def __init__(self):
        """Initialize the ticket creation tool."""
        priorities = ", ".join(priority.value for priority in TicketPriority)
        categories = ", ".join(category.value for category in TicketCategory)
        self.name = "create_ticket"
        self.description = (
            "Create a support ticket only when escalation is appropriate: "
            "the user asks for a ticket or a human, or the issue cannot be resolved "
            "with search, billing, and system status. "
            "Do not claim a ticket was created unless this tool returns success. "
            f"priority must be one of: {priorities}. "
            f"category must be one of: {categories}. "
            "An invalid priority or category returns a validation error and does not create a ticket. "
            "Pass customer_email only when the user provided one. "
            "If no email is supplied it is stored as null; do not invent an email address."
        )
        self._ticket_counter = 1000

    def create(
        self,
        subject: str,
        description: str,
        customer_email: Optional[str] = None,
        priority: str = "medium",
        category: str = "other"
    ) -> Dict[str, Any]:
        """
        Create a new support ticket.

        Args:
            subject: Brief summary of the issue
            description: Detailed description of the problem
            customer_email: Email the user provided. Omit it instead of inventing one.
            priority: One of low, medium, high, critical. Invalid values return an error.
            category: One of billing, technical, account, feature_request, bug_report, other. Invalid values return an error.

        Returns:
            Dictionary containing ticket information, or a validation error.
        """
        priority_error = self._choice_error("priority", priority, TicketPriority)
        category_error = self._choice_error("category", category, TicketCategory)
        errors = [message for message in (priority_error, category_error) if message]
        if errors:
            return {
                "success": False,
                "error": " ".join(errors),
            }

        priority_enum = TicketPriority(priority.lower())
        category_enum = TicketCategory(category.lower())

        # Generate ticket ID only after validation succeeds
        self._ticket_counter += 1
        ticket_id = f"TICKET-{self._ticket_counter}"

        # Estimate response time based on priority
        response_times = {
            TicketPriority.CRITICAL: "1 hour",
            TicketPriority.HIGH: "4 hours",
            TicketPriority.MEDIUM: "24 hours",
            TicketPriority.LOW: "48 hours"
        }

        ticket_data = {
            "ticket_id": ticket_id,
            "subject": subject,
            "description": description,
            "customer_email": (
                customer_email
                if isinstance(customer_email, str) and customer_email.strip()
                else None
            ),
            "priority": priority_enum.value,
            "category": category_enum.value,
            "status": "open",
            "created_at": FIXED_NOW.isoformat(),
            "estimated_response_time": response_times[priority_enum],
            "assigned_to": None,
            "notes": "Ticket created via AI agent"
        }

        return {
            "success": True,
            "message": f"Support ticket {ticket_id} created successfully",
            "data": ticket_data
        }

    @staticmethod
    def _choice_error(field: str, value: Any, enum_cls: Any) -> Optional[str]:
        """Return a validation error when value is not a member of enum_cls."""
        allowed = ", ".join(member.value for member in enum_cls)
        if isinstance(value, str):
            try:
                enum_cls(value.lower())
                return None
            except ValueError:
                pass
        return f"Invalid {field} {value!r}. Expected one of: {allowed}."

    def as_function_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.create,
            name=self.name,
            description=self.description,
        )


class SystemStatusTool:
    """
    Tool for checking CloudSync system status and service health.

    This tool provides information about system outages, maintenance windows,
    and service degradation.
    """

    def __init__(self):
        """Initialize the system status tool."""
        self.name = "check_system_status"
        self._services = self._initialize_services()
        supported = ", ".join(self._services.keys())
        self.description = (
            "Check CloudSync for a current service issue, outage, or degradation. "
            f"If the user names a service, pass service as one of: {supported}. "
            "Omit service when the user does not name one. "
            "An unsupported service name returns an error and does not report every service."
        )

    def _initialize_services(self) -> Dict[str, Dict[str, Any]]:
        """Initialize fixed mock service status data (always operational)."""
        return {
            "file_sync": {
                "name": "File Synchronization",
                "status": "operational",
                "uptime": 99.99,
                "last_incident": None,
                "response_time_ms": 45
            },
            "api": {
                "name": "CloudSync API",
                "status": "operational",
                "uptime": 99.95,
                "last_incident": None,
                "response_time_ms": 120
            },
            "web_dashboard": {
                "name": "Web Dashboard",
                "status": "operational",
                "uptime": 99.98,
                "last_incident": None,
                "response_time_ms": 200
            },
            "mobile_apps": {
                "name": "Mobile Applications",
                "status": "operational",
                "uptime": 99.90,
                "last_incident": None,
                "response_time_ms": 300
            },
            "authentication": {
                "name": "Authentication Services",
                "status": "operational",
                "uptime": 100.0,
                "last_incident": None,
                "response_time_ms": 50
            }
        }

    def check(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Check system status.

        Args:
            service: Service key (file_sync, api, web_dashboard, mobile_apps, authentication). Omit to check all services. Unsupported names return an error.

        Returns:
            Dictionary containing status information, or an error for an unsupported service.
        """
        if service is None:
            return self._all_services_status()

        try:
            known = service in self._services
        except TypeError:
            known = False

        if known:
            return {
                "success": True,
                "service": service,
                "data": self._services[service],
                "overall_status": self._get_overall_status()
            }

        supported = ", ".join(self._services.keys())
        return {
            "success": False,
            "error": (
                f"Unsupported service {service!r}. "
                f"Expected one of: {supported}."
            ),
            "service": service,
        }

    def _all_services_status(self) -> Dict[str, Any]:
        """Return the status of every service."""
        all_operational = all(
            s["status"] == "operational" for s in self._services.values()
        )

        return {
            "success": True,
            "overall_status": "operational" if all_operational else "issues_detected",
            "services": self._services,
            "maintenance_windows": self._get_maintenance_windows(),
            "recent_incidents": self._get_recent_incidents()
        }

    def _get_overall_status(self) -> str:
        """Get overall system status."""
        statuses = [s["status"] for s in self._services.values()]
        if all(s == "operational" for s in statuses):
            return "All systems operational"
        elif any("outage" in s for s in statuses):
            return "Service disruption detected"
        else:
            return "Minor issues detected"

    def _get_maintenance_windows(self) -> List[Dict[str, Any]]:
        """Get scheduled maintenance windows (fixed empty — no random windows)."""
        return []

    def _get_recent_incidents(self) -> List[Dict[str, Any]]:
        """Get recent incidents."""
        incidents = []
        for service_key, service_data in self._services.items():
            if service_data.get("last_incident"):
                incidents.append({
                    "service": service_key,
                    "incident": service_data["last_incident"]
                })
        return incidents

    def as_function_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.check,
            name=self.name,
            description=self.description,
        )
