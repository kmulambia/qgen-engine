from typing import Optional
import httpx
from mailer.transports.base_transport import BaseTransport
from engine.utils.config_util import load_config
from mailer.dependencies.logger import logger

config = load_config()


class PostmarkTransport(BaseTransport):
    """Postmark email transport implementation."""
    
    def __init__(self):
        super().__init__()
        # Load Postmark configuration from environment
        self.api_token = config.require_variable("POSTMARK_API_TOKEN")
        self.from_email = config.require_variable("EMAIL")
        self.api_url = "https://api.postmarkapp.com/email"
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.api_token
            }
        )
        logger.debug("PostmarkTransport initialized with API URL: %s", self.api_url)
    
    async def connect(self) -> None:
        """Establish connection to Postmark API."""
        # No explicit connection needed for Postmark
        pass
    
    async def disconnect(self) -> None:
        """Close connection to Postmark API."""
        logger.debug("Closing PostmarkTransport HTTP client connection")
        await self.client.aclose()
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_email: Optional[str] = None,
        html_content: Optional[str] = None,
        charset: Optional[str] = "UTF-8"
    ) -> bool:
        """Send an email using Postmark API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Plain text content
            from_email: Sender email address (optional)
            html_content: HTML content (optional)
            charset: Character Set (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            logger.info("Attempting to send email to: %s with subject: %s", to_email, subject)
            payload = {
                "From": from_email or self.from_email,
                "To": to_email,
                "Subject": subject,
                "TextBody": content,
                "HtmlBody": html_content,
                "MessageStream": "outbound"
            }
            
            response = await self.client.post(self.api_url, json=payload)
            response.raise_for_status()
            
            logger.info("Successfully sent email to: %s", to_email)
            return True
            
        except httpx.HTTPError as e:
            logger.error("HTTP error sending email via Postmark to %s: %s", to_email, str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending email via Postmark to %s: %s", to_email, str(e))
            return False
