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

# Fixed reference time so mock tool payloads are reproducible across runs.
FIXED_NOW = datetime(2024, 6, 15, 12, 0, 0)


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
            "Look up billing information for a customer. "
            "Requires either customer_email or customer_id. "
            "Returns subscription status, billing history, and payment method."
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
                "next_billing_date": "2024-07-01",
                "payment_method": "card",
                "last_payment": {
                    "date": "2024-06-01",
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
                "next_billing_date": "2024-06-20",
                "payment_method": "card",
                "last_payment": {
                    "date": "2024-05-20",
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
                "next_billing_date": "2024-06-25",
                "payment_method": "ach",
                "last_payment": {
                    "date": "2024-05-25",
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
                "next_billing_date": "2024-07-15",
                "payment_method": "invoice",
                "last_payment": {
                    "date": "2024-06-15",
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
                "next_billing_date": "2024-06-30",
                "payment_method": "card",
                "last_payment": {
                    "date": "2024-06-01",
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
        self.name = "create_ticket"
        self.description = (
            "Create a support ticket for issues requiring human intervention. "
            "Use for complex technical issues, account problems, or when "
            "the knowledge base doesn't have sufficient information. "
            "Returns ticket ID and estimated response time."
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
            customer_email: Customer's email address
            priority: Ticket priority (low, medium, high, critical)
            category: Ticket category (billing, technical, account, etc.)

        Returns:
            Dictionary containing ticket information
        """
        # Validate priority
        try:
            priority_enum = TicketPriority(priority.lower())
        except ValueError:
            priority_enum = TicketPriority.MEDIUM

        # Validate category
        try:
            category_enum = TicketCategory(category.lower())
        except ValueError:
            category_enum = TicketCategory.OTHER

        # Generate ticket ID
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
            "customer_email": customer_email or "not_provided@example.com",
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
        self.description = (
            "Check the current status of CloudSync services including "
            "file sync, API, web dashboard, and mobile apps. "
            "Returns information about any ongoing issues or maintenance."
        )

        # Mock service status
        self._services = self._initialize_services()

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
            service: Specific service to check (optional)

        Returns:
            Dictionary containing status information
        """
        if service and service in self._services:
            # Return specific service status
            return {
                "success": True,
                "service": service,
                "data": self._services[service],
                "overall_status": self._get_overall_status()
            }

        # Return all services status
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
