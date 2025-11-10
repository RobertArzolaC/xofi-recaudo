import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PartnerAPIService:
    """Service to interact with Partner API endpoints."""

    def __init__(self, api_token: Optional[str] = None):
        """Initialize with API token."""
        self.api_token = api_token or getattr(
            settings, "AI_AGENT_API_TOKEN", ""
        )
        self.base_url = getattr(
            settings, "AI_AGENT_API_BASE_URL", "http://localhost:8000"
        )
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def get_partner_detail(self, partner_id: int) -> Dict[str, Any]:
        """Get partner detail from API."""
        url = f"{self.base_url}/api/v1/partners/partners/{partner_id}/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching partner detail: {e}")
            return {}

    def get_account_statement(self, partner_id: int) -> Dict[str, Any]:
        """Get partner's account statement from API."""
        url = f"{self.base_url}/api/v1/partners/partners/{partner_id}/account-statement/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching account statement: {e}")
            return {}

    def get_credits_list(
        self, partner_id: int, status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of partner's credits from API."""
        url = f"{self.base_url}/api/v1/partners/partners/{partner_id}/credits/"
        params = {}
        if status:
            params["status"] = status

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching credits list: {e}")
            return {}

    def get_credit_detail(
        self, partner_id: int, credit_id: int
    ) -> Dict[str, Any]:
        """Get credit detail from API."""
        url = f"{self.base_url}/api/v1/partners/partners/{partner_id}/credits/{credit_id}/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching credit detail: {e}")
            return {}

    def create_support_ticket(
        self,
        partner_document: str,
        subject: str,
        description: str,
        priority: int = 2,
    ) -> Dict[str, Any]:
        """Create a support ticket via API."""
        url = f"{self.base_url}/api/v1/support/tickets/"
        data = {
            "partner_document": partner_document,
            "subject": subject,
            "description": description,
            "priority": priority,
        }
        try:
            response = requests.post(
                url, headers=self.headers, json=data, timeout=10
            )
            logger.info(f"Support ticket created: {response.json()}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error creating support ticket: {e}")
            return {}

    def upload_payment_receipt(
        self,
        partner_id: int,
        receipt_file: bytes,
        filename: str,
        amount: float,
        payment_date: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Upload a payment receipt via API."""
        url = f"{self.base_url}/payments/api/receipts/"

        # Prepare multipart form data
        files = {"receipt_file": (filename, receipt_file)}
        data = {
            "partner": partner_id,
            "amount": amount,
            "payment_date": payment_date,
            "notes": notes,
        }

        # Use Authorization header for multipart
        headers = {"Authorization": self.headers["Authorization"]}

        try:
            response = requests.post(
                url, headers=headers, files=files, data=data, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error uploading payment receipt: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return {}
