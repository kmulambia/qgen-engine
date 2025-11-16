from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from engine.utils.config_util import load_config
from datetime import datetime


class BaseTransport(ABC):
    """Base class for email transport implementations."""

    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.config = load_config()

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the email service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the email service."""
        pass

    @abstractmethod
    async def send_email(
            self,
            to_email: str,
            subject: str,
            content: str,
            from_email: Optional[str] = None,
            html_content: Optional[str] = None,
            charset: Optional[str] = "UTF-8"
    ) -> bool:
        """Send an email with the given parameters.
        
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
        pass

    def _get_template_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get the complete template context including essential configurations.
        
        Args:
            context: Original template context
            
        Returns:
            Dict[str, Any]: Complete template context
        """
        return {
            **context,
            # System configuration
            "name": self.config.require_variable("NAME"),
            "email": self.config.require_variable("EMAIL"),
            # Organization configuration
            "year": datetime.now().year,
            # Website configuration
            "website_url": self.config.require_variable("WEBSITE_URL"),
            "privacy_url": self.config.require_variable("WEBSITE_PRIVACY_URL"),
            "terms_url": self.config.require_variable("WEBSITE_TERMS_URL")
        }

    def render_template(self, template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
        """Render an HTML template and its plain text version.
        
        Args:
            template_name: Name of the template file (without extension)
            context: Dictionary of template variables
            
        Returns:
            tuple[str, str]: Tuple containing (html_content, plain_text_content)
            
        Raises:
            FileNotFoundError: If a template file doesn't exist
        """
        html_content = None
        template_path = self.templates_dir / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")

        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Get complete template context
        complete_context = self._get_template_context(context)

        # Replace template variables
        for key, value in complete_context.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        # Create a plain text version by removing HTML tags
        import re
        plain_text = re.sub(r'<[^>]+>', '', html_content)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()

        return html_content, plain_text

    async def send_template_email(
            self,
            to_email: str,
            template_name: str,
            context: Dict[str, Any],
            subject: str,
            from_email: Optional[str] = None
    ) -> bool:
        """Send an email using a template.
        
        Args:
            to_email: Recipient email address
            template_name: Name of the template to use
            context: Dictionary of template variables
            subject: Email subject
            from_email: Sender email address (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            html_content, plain_text = self.render_template(template_name, context)
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                content=plain_text,
                from_email=from_email,
                html_content=html_content
            )
        except FileNotFoundError:
            # If a template doesn't exist, send a plain text version
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                content=str(context),
                from_email=from_email
            )
