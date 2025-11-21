from typing import Optional
import re
import httpx
from mailer.transports.base_transport import BaseTransport
from engine.utils.config_util import load_config
from mailer.dependencies.logger import logger

config = load_config()

# Email validation regex pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: Optional[str]) -> bool:
    """Check if an email address is valid."""
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


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
            
            # Validate and use from_email, fallback to default if invalid
            sender_email = from_email or self.from_email
            if not is_valid_email(sender_email):
                logger.warning(
                    "Invalid 'From' email address '%s', falling back to default: %s",
                    sender_email,
                    self.from_email
                )
                sender_email = self.from_email
            
            # Build payload matching Postmark API format exactly
            # Postmark requires at least one of TextBody or HtmlBody
            payload = {
                "From": sender_email,
                "To": to_email,
                "Subject": subject,
                "MessageStream": "outbound"
            }
            
            # Add TextBody if content is provided (non-empty string)
            if content and content.strip():
                payload["TextBody"] = content
            
            # Add HtmlBody if html_content is provided (non-empty string)
            if html_content and html_content.strip():
                payload["HtmlBody"] = html_content
            
            # Ensure at least one body is present (Postmark requirement)
            if "TextBody" not in payload and "HtmlBody" not in payload:
                logger.error("Both TextBody and HtmlBody are missing. At least one is required by Postmark.")
                return False
            
            # Log payload for debugging (without sensitive data)
            logger.debug("Postmark payload: From=%s, To=%s, Subject=%s, HasTextBody=%s, HasHtmlBody=%s",
                       payload["From"], payload["To"], payload["Subject"],
                       "TextBody" in payload, "HtmlBody" in payload)
            
            response = await self.client.post(self.api_url, json=payload)
            
            # Log response details for debugging
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.error(
                        "Postmark API error (status %d) sending email to %s: %s",
                        response.status_code,
                        to_email,
                        error_data
                    )
                except Exception:
                    logger.error(
                        "Postmark API error (status %d) sending email to %s: %s",
                        response.status_code,
                        to_email,
                        response.text
                    )
            
            response.raise_for_status()
            
            logger.info("Successfully sent email to: %s", to_email)
            return True
            
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors (4xx, 5xx)
            try:
                error_data = e.response.json()
                logger.error(
                    "HTTP error sending email via Postmark to %s (status %d): %s",
                    to_email,
                    e.response.status_code,
                    error_data
                )
            except Exception:
                logger.error(
                    "HTTP error sending email via Postmark to %s (status %d): %s",
                    to_email,
                    e.response.status_code,
                    e.response.text
                )
            return False
        except httpx.HTTPError as e:
            logger.error("HTTP error sending email via Postmark to %s: %s", to_email, str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending email via Postmark to %s: %s", to_email, str(e))
            return False
