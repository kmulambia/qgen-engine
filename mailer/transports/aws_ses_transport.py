from mailer.transports.base_transport import BaseTransport
from engine.utils.config_util import load_config
from mailer.dependencies.logger import logger
from botocore.exceptions import ClientError
from mailer.dependencies.aws_ses import get_aws_ses
from typing import Optional

config = load_config()


class AWSSESTransport(BaseTransport):
    """AWS SES transport implementation."""

    def __init__(self):
        super().__init__()
        self.from_email = config.require_variable("EMAIL")
        self.client = get_aws_ses()

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

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
        message = {
            'Subject': {'Data': subject, 'Charset': charset},
            'Body': {
                'Text': {'Data': content, 'Charset': charset},
                'Html': {'Data': html_content, 'Charset': charset}
            }
        }

        # TODO : Check the typing error on Html
        if html_content:
            message['Body']['Html'] = {'Data': html_content, 'Charset': charset}  # Noqa

        try:
            response = self.client.send_email(
                Source=from_email or self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            logger.info("Successfully sent email(%s) to: %s", response['MessageId'], to_email)
            return True
        except ClientError as e:
            logger.error("Unexpected error sending email via AWS SES to %s: %s", to_email,
                         str(e.response['Error']['Message']))
            return False
