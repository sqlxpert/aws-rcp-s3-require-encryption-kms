#!/usr/bin/env python3
"""Test director for

github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
GPLv3, Copyright Paul Marcelin

All inputs are from environment variables. Input event is ignored.
"""

import os
import logging
import json
import boto3


logger = logging.getLogger()
# Skip "credentials in environment" INFO message, unavoidable in AWS Lambda:
logging.getLogger("botocore").setLevel(logging.WARNING)


TESTER_LAMBDA_INVOKE_KWARGS_BASE = {
    "FunctionName": os.environ["TESTER_LAMBDA_FUNCTION_ARN"],
    "InvocationType": "Event",  # asynchronous
}
S3_BUCKET_NAMES = json.loads(os.environ["S3_BUCKET_NAMES_JSON_ARRAY"])


aws_clients = {}


def get_aws_client(aws_service):
    """Return an AWS service client, creating it if necessary

    Alternatives considered:
    https://github.com/boto/boto3/issues/3197#issue-1175578228
    https://github.com/aws-samples/boto-session-manager-project
    """
    if not aws_clients.get(aws_service):
        aws_clients[aws_service] = boto3.client(aws_service)
    return aws_clients[aws_service]


def lambda_handler(event, context):  # pylint: disable=unused-argument
    """Get S3 buckets from environment as JSON, call test Lambda for each
    """
    for s3_bucket_name in S3_BUCKET_NAMES:
        get_aws_client("lambda").invoke(
            **TESTER_LAMBDA_INVOKE_KWARGS_BASE,
            Payload=json.dumps({
                "s3_bucket_name": s3_bucket_name,
        })
    )
