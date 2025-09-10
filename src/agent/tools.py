"""
Custom tools for the Customer Support Agent.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import json
import logging
from enum import Enum

from llama_index.core.tools import FunctionTool

# Set up logging
logger = logging.getLogger(__name__)


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
        """Generate mock customer billing data."""
        plans = ["Free", "Basic", "Professional", "Enterprise"]
        statuses = ["active", "past_due", "cancelled", "trialing"]

        customers = {}
        emails = [
            "john.doe@example.com",
            "jane.smith@company.com",
            "support@startup.io",
            "admin@enterprise.org",
            "user@test.com"
        ]

        for i, email in enumerate(emails):
            customer_id = f"cust_{1000 + i}"
            customers[email] = {
                "customer_id": customer_id,
                "email": email,
                "plan": random.choice(plans),
                "status": random.choice(statuses),
                "monthly_amount": random.choice([0, 9, 29, 99, 299]),
                "next_billing_date": (
                    datetime.now() + timedelta(days=random.randint(1, 30))
                ).strftime("%Y-%m-%d"),
                "payment_method": random.choice(["card", "invoice", "ach"]),
                "last_payment": {
                    "date": (
                        datetime.now() - timedelta(days=random.randint(1, 30))
                    ).strftime("%Y-%m-%d"),
                    "amount": random.choice([0, 9, 29, 99, 299]),
                    "status": "successful"
                }
            }
            customers[customer_id] = customers[email]

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

        # Customer not found - generate a default response
        return {
            "success": False,
            "data": {
                "customer_id": customer_id or f"cust_{random.randint(2000, 9999)}",
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
            "created_at": datetime.now().isoformat(),
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
        """Initialize mock service status data."""
        services = {
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

        # Randomly add some issues for demonstration
        if random.random() < 0.2:  # 20% chance of an issue
            affected_service = random.choice(list(services.keys()))
            services[affected_service]["status"] = random.choice([
                "degraded_performance",
                "partial_outage",
                "maintenance"
            ])
            services[affected_service]["last_incident"] = {
                "time": datetime.now().isoformat(),
                "description": "Investigating reports of slow performance",
                "affected_regions": ["US-East", "EU-West"]
            }

        return services

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
        """Get scheduled maintenance windows."""
        # Mock maintenance windows
        if random.random() < 0.3:  # 30% chance of scheduled maintenance
            return [{
                "service": "web_dashboard",
                "start_time": (
                    datetime.now() + timedelta(days=7)
                ).strftime("%Y-%m-%d 02:00 UTC"),
                "duration": "2 hours",
                "description": "Database optimization and security updates",
                "impact": "Web dashboard will be unavailable"
            }]
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
