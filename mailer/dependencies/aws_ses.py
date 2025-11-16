import boto3
from engine.utils.config_util import load_config

config = load_config()

AWS_ACCESS_KEY = config.require_variable("AWS_ACCESS_KEY")
AWS_SECRET_KEY = config.require_variable("AWS_SECRET_KEY")
AWS_REGION = config.require_variable("AWS_REGION")


def get_aws_ses() -> any: # noqa
    if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION]):
        raise ValueError("Missing AWS credentials or region in .env file")

    client = boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    return client
