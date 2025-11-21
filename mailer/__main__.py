"""
 * Framework - Backend and Services
 * MIT License
 * Copyright (c) 2024 Umodzi Source
"""

import asyncio
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

import aio_pika

from engine.utils.config_util import load_config
from mailer.transports.postmark_transport import PostmarkTransport
# from mailer.transports.aws_ses_transport import AWSSESTransport
# from mailer.transports.smtp_transport import SMTPTransport
from mailer.dependencies.logger import logger
from mailer.dependencies.amq import get_amq
from jinja2 import Template

# Email validation regex pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: Optional[str]) -> bool:
    """Check if an email address is valid."""
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))

config = load_config()

AMQ_QUEUE_NAME = config.require_variable("AMQ_QUEUE_NAME")
# Define available transports
TRANSPORTS = {
    "postmark": PostmarkTransport,
    # "awsses": AWSSESTransport,
    # "smtp": SMTPTransport
}


def validate_template_data(message: Dict) -> tuple[bool, List[str]]:
    """
    Validate template and data fields in the message.
    
    Args:
        message (Dict): The message to validate
        
    Returns:
        tuple[bool, List[str]]: (is_valid, list of missing or invalid fields)
    """
    errors = []

    # Check if template is specified
    if "template" not in message:
        errors.append("template field is required")
        return False, errors

    template = message["template"]

    # Validate template structure
    if not isinstance(template, dict):
        errors.append("template must be a dictionary")
        return False, errors

    # Check required template fields
    required_template_fields = {"name", "data"}
    missing_fields = [field for field in required_template_fields if field not in template]
    if missing_fields:
        errors.append(f"Missing required template fields: {missing_fields}")
        return False, errors

    # Validate template name
    template_name = template["name"]
    template_path = Path(__file__).parent / "templates" / f"{template_name}.html"
    if not template_path.exists():
        errors.append(f"Template file not found: {template_name}")
        return False, errors

    # Validate template data
    template_data = template["data"]
    if not isinstance(template_data, dict):
        errors.append("template.data must be a dictionary")
        return False, errors

    return True, errors


def validate_message(message: Dict, transport_name: str) -> tuple[bool, List[str]]:
    """
    Validate message fields based on the transport being used.
    
    Args:
        message (Dict): The message to validate
        transport_name (str): Name of the transport to use
        
    Returns:
        tuple[bool, List[str]]: (is_valid, list of missing fields)
    """
    errors = []

    # Validate transport
    if transport_name not in TRANSPORTS:
        errors.append(f"Unknown transport: {transport_name}")
        return False, errors

    # Validate template and data
    is_valid, template_errors = validate_template_data(message)
    if not is_valid:
        errors.extend(template_errors)
        return False, errors

    return True, errors


async def process_email_message(message: Dict) -> None:
    """
    Process an email message from the queue.
    
    Expected message format:
    {
        "template": {
            "name": "welcome",
            "data": {
                "user": {
                    "email": "recipient@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            }
        }
    }
    """
    transport = None
    try:
        transport_name = message.get("transport", "postmark")
        if not transport_name:
            logger.error("Transport not specified in message")
            return

        is_valid, errors = validate_message(message, transport_name)
        if not is_valid:
            logger.error(f"Message validation failed: {errors}")
            return

        if transport_name not in TRANSPORTS:
            logger.error(f"Transport {transport_name} not found")
            return

        transport_class = TRANSPORTS[transport_name]
        transport = transport_class()

        # Process template
        template_info = message["template"]
        template_name = template_info["name"]
        template_path = Path(__file__).parent / "templates" / f"{template_name}.html"

        with open(template_path, "r") as f:
            template_content = f.read()

        # Render template with provided data
        jinja_template = Template(template_content)
        html_content = jinja_template.render(**template_info["data"])

        # Get email from template data
        to_email = template_info["data"]["user"]["email"]
        subject = template_info['data']['subject']
        
        # Validate and get from_email from template, or use None to let transport use default
        support_email = template_info["data"].get("support_email")
        from_email = None
        if support_email and is_valid_email(support_email):
            from_email = support_email
        elif support_email:
            logger.warning(
                "Invalid support_email '%s' in template data, transport will use default sender",
                support_email
            )

        # Send email
        await transport.connect()
        success = await transport.send_email(
            to_email=to_email,
            subject=subject,
            content="Please check your email for the HTML version of this message.",
            html_content=html_content,
            from_email=from_email
        )

        if success:
            logger.info(f"Successfully sent email to {to_email} using {transport_name}")
        else:
            logger.error(f"Failed to send email to {to_email} using {transport_name}")

    except Exception as e:
        logger.error(f"Error processing email message: {str(e)}")
    finally:
        await transport.disconnect()


async def start_consumer() -> None:
    """Start the AMQ consumer for email processing."""
    try:
        amq = await get_amq()
        logger.info("Connected to RabbitMQ")

        async def message_handler(message):
            try:
                # Log raw message
                logger.debug(f"Received raw message: {message.body.decode()}")

                # Decode and parse message
                message_data = json.loads(message.body.decode())

                # Check if it's a batch of messages
                if isinstance(message_data, dict) and "batch" in message_data:
                    email_batch = message_data["batch"]
                    if not isinstance(email_batch, list):
                        logger.error("Invalid batch format: 'batch' should be a list")
                        await message.reject()
                        return

                    logger.info(f"Received a batch of {len(email_batch)} email messages")

                    all_success = True
                    for idx, single_message_data in enumerate(email_batch):
                        try:
                            # Extract email
                            to_email = single_message_data.get("template", {}).get("data", {}).get("user", {}).get(
                                "email")
                            if not to_email:
                                logger.warning(f"[{idx}] Missing email in batch item, skipping.")
                                continue

                            logger.info(f"[{idx}] Processing message for recipient: {to_email}")

                            # Get transport or use default
                            transport_name = single_message_data.get("transport", "postmark")
                            if transport_name not in TRANSPORTS:
                                logger.warning(f"[{idx}] Invalid transport '{transport_name}', skipping.")
                                continue

                            is_valid, errors = validate_template_data(single_message_data)
                            if not is_valid:
                                logger.warning(f"[{idx}] Template validation failed: {errors}, skipping.")
                                continue

                            await process_email_message(single_message_data)
                            logger.info(f"[{idx}] Successfully processed message for {to_email} using {transport_name}")

                        except Exception as err:
                            logger.error(f"[{idx}] Error processing batch message: {str(err)}", exc_info=True)
                            all_success = False  # Don't reject the entire batch unless absolutely needed

                    # Acknowledge the entire batch if no fatal errors
                    if all_success:
                        await message.ack()
                    else:
                        # Consider acking and logging if partial success is acceptable
                        await message.ack()  # or await message.reject() if atomicity is critical

                else:
                    # Single message flow (existing behavior)
                    to_email = message_data.get("template", {}).get("data", {}).get("user", {}).get("email")
                    if not to_email:
                        logger.error("No email found in message template data")
                        await message.reject()
                        return

                    logger.info(f"Processing message for recipient: {to_email}")

                    transport_name = message_data.get("transport", "postmark")
                    logger.debug(f"Using transport: {transport_name}")

                    if transport_name not in TRANSPORTS:
                        logger.error(
                            f"Invalid transport specified: {transport_name}. Available transports: {', '.join(TRANSPORTS.keys())}")
                        await message.reject()
                        return

                    is_valid, errors = validate_template_data(message_data)
                    if not is_valid:
                        logger.error(f"Template validation failed: {errors}")
                        await message.reject()
                        return

                    await process_email_message(message_data)
                    await message.ack()
                    logger.info(f"Successfully processed message for {to_email} using transport {transport_name}")

            except json.JSONDecodeError as error:
                logger.error(f"Invalid JSON message received: {str(error)}")
                await message.reject()
            except Exception as error:
                logger.error(f"Error processing message: {str(error)}", exc_info=True)
                await message.reject()

        # Start consuming messages
        logger.info(f"Starting to consume messages from queue: {amq.queue_name}")
        await amq.queue.consume(message_handler)
        logger.info("Email consumer started successfully")

        # Keep the consumer running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in consumer: {str(e)}", exc_info=True)
        raise


async def send_test_email(
        emails: List[str],
        transport_name: str = "postmark",
        template_name: str = "welcome"
) -> None:
    """Send a test email to the specified recipients using the given template."""
    if transport_name not in TRANSPORTS:
        logger.error(f"Transport {transport_name} not found. Available transports: {', '.join(TRANSPORTS.keys())}")
        return

    transport_class = TRANSPORTS[transport_name]
    transport = transport_class()

    try:
        await transport.connect()

        # Load template
        template_path = Path(__file__).parent / "templates" / f"{template_name}.html"
        if not template_path.exists():
            logger.error(f"Template {template_name} not found")
            return

        with open(template_path, "r") as f:
            template_content = f.read()

        # Create Jinja2 template and render
        template = Template(template_content)
        html_content = template.render(
            user={
                "first_name": "Joe",
                "last_name": "Doe"
            },
            role={
                "name": "Admin",
            },
            workspace={
                "name": "Admin"
            }
        )

        # Send to each recipient
        for email in emails:
            success = await transport.send_email(
                to_email=email.strip(),
                subject=f"Test Email - {template_name} template",
                content="This is a test email sent from the Amphibia Engine mailer.",
                html_content=html_content
            )

            if success:
                logger.info(f"Successfully sent test email to {email} using {transport_name} transport")
            else:
                logger.error(f"Failed to send test email to {email} using {transport_name} transport")

    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
    finally:
        await transport.disconnect()


async def test_send_amq_message():
    amq = await get_amq()
    await amq.connect()

    try:
        # Example payload
        message = {
            "subject": "Test Message",
            "recipient": "test@example.com",
            "body": "This is a test message sent via AMQ."
        }

        # Prepare message
        message_body = json.dumps(message)
        amq_message = aio_pika.Message(
            body=message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        # Get the exchange (assumes declared in connect)
        exchange = await amq.channel.get_exchange("amphibia_exchange")

        # Send message using the exchange
        await exchange.publish(
            amq_message,
            routing_key=AMQ_QUEUE_NAME
        )

        logger.info(f"✅ Successfully sent email message to queue: {AMQ_QUEUE_NAME}")

    except Exception as e:
        logger.error(f"❌ Failed to send test message: {e}")
    finally:
        await amq.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Amphibia Engine mailer - RabbitMQ consumer")
    parser.add_argument("--queue", default="email_queue",
                        help="RabbitMQ queue name to consume from (default: email_queue)")
    parser.add_argument("--template-dir", default="templates",
                        help="Directory containing email templates (default: templates)")
    parser.add_argument("--default-transport", default="postmark", choices=list(TRANSPORTS.keys()),
                        help="Default email transport to use if not specified in message (default: smtp)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging (default: False)")

    args = parser.parse_args()

    # Set up logging level - INFO by default, DEBUG only if explicitly requested
    if args.debug:
        logger.setLevel("DEBUG")
        logger.info("Debug logging enabled")
    else:
        logger.setLevel("INFO")
        logger.info("Running in normal mode (INFO logging)")

    # Validate template directory
    template_dir = Path(__file__).parent / args.template_dir
    if not template_dir.exists():
        logger.error(f"Template directory not found: {template_dir}")
        return

    # Log startup information
    logger.info(f"Starting email consumer with the following configuration:")
    logger.info(f"Queue: {args.queue}")
    logger.info(f"Template directory: {template_dir}")
    logger.info(f"Default transport: {args.default_transport}")
    logger.info(f"Available transports: {', '.join(TRANSPORTS.keys())}")

    try:
        # Start the consumer
        asyncio.run(start_consumer())
    except KeyboardInterrupt:
        logger.info("Shutting down email consumer...")
    except Exception as e:
        logger.error(f"Fatal error in email consumer: {str(e)}")
        raise


if __name__ == "__main__":
    main()
    # asyncio.run(send_test_email(["innocent.chombo@sparcsystems.africa"]))
    # asyncio.run(test_send_amq_message())
