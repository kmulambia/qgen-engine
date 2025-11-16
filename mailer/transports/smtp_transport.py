import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from mailer.transports.base_transport import BaseTransport
from engine.utils.config_util import load_config
from mailer.dependencies.logger import logger

config = load_config()


class SMTPTransport(BaseTransport):
    """SMTP email transport implementation."""
    
    def __init__(self):
        super().__init__()
        # Load SMTP configuration from environment
        self.smtp_host = config.require_variable("SMTP_HOST")
        self.smtp_port = int(config.get_variable("SMTP_PORT", "587"))
        self.smtp_username = config.require_variable("SMTP_USERNAME")
        self.smtp_password = config.require_variable("SMTP_PASSWORD")
        self.from_email = config.require_variable("EMAIL")
        self.use_tls = config.get_variable("SMTP_USE_TLS", "true").lower() == "true"
        self.use_ssl = config.get_variable("SMTP_USE_SSL", "false").lower() == "true"
        
        self.server = None
        logger.debug("SMTPTransport initialized with host: %s, port: %d", self.smtp_host, self.smtp_port)
    
    async def connect(self) -> None:
        """Establish connection to SMTP server."""
        try:
            logger.debug("Connecting to SMTP server: %s:%d", self.smtp_host, self.smtp_port)
            
            if self.use_ssl:
                # Use SSL connection
                context = ssl.create_default_context()
                self.server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context)
            else:
                # Use regular connection, potentially with STARTTLS
                self.server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                
                if self.use_tls:
                    # Enable TLS
                    context = ssl.create_default_context()
                    self.server.starttls(context=context)
            
            # Authenticate if credentials are provided
            if self.smtp_username and self.smtp_password:
                self.server.login(self.smtp_username, self.smtp_password)
                logger.debug("Successfully authenticated with SMTP server")
            
            logger.info("Successfully connected to SMTP server")
            
        except Exception as e:
            logger.error("Failed to connect to SMTP server: %s", str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close connection to SMTP server."""
        if self.server:
            try:
                logger.debug("Closing SMTP server connection")
                self.server.quit()
                self.server = None
                logger.debug("SMTP connection closed successfully")
            except Exception as e:
                logger.warning("Error closing SMTP connection: %s", str(e))
                # Force close if quit fails
                if self.server:
                    self.server.close()
                    self.server = None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_email: Optional[str] = None,
        html_content: Optional[str] = None,
        charset: Optional[str] = "UTF-8"
    ) -> bool:
        """Send an email using SMTP.
        
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
            
            # Ensure we have a connection
            if not self.server:
                await self.connect()
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or self.from_email
            msg['To'] = to_email
            
            # Add plain text part
            text_part = MIMEText(content, 'plain', charset)
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_content:
                html_part = MIMEText(html_content, 'html', charset)
                msg.attach(html_part)
            
            # Send the email
            self.server.send_message(msg)
            logger.info("Successfully sent email to: %s", to_email)
            return True
            
        except smtplib.SMTPException as e:
            logger.error("SMTP error sending email to %s: %s", to_email, str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending email via SMTP to %s: %s", to_email, str(e))
            return False
        