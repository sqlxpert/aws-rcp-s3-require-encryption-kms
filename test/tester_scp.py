#!/usr/bin/env python3
"""Service control policy tester for

github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
GPLv3, Copyright Paul Marcelin

See TestDirectorLambdaFn for input event format.
"""

import os
import logging
import json
import botocore
import boto3


logger = logging.getLogger()
# Skip "credentials in environment" INFO message, unavoidable in AWS Lambda:
logging.getLogger("botocore").setLevel(logging.WARNING)


ENV = {
    variable_name: os.environ[variable_name]
    for variable_name in [
        "AWS_PARTITION",
        "AWS_ACCOUNT_ID",
        "S3_BUCKET_CONSTANT_NAME_PREFIX",
        "S3_BUCKET_CONSTANT_NAME_SUFFIX",
        "S3_BUCKET_TAG_KEY",
        "KMS_KEY_ARN",
    ]
}
SCP_ON = bool(int(os.environ["SCP_ON"]))
SCP_OFF = not SCP_ON
NON_PROTECTED_TAG_KEY = "non-protected-tag-key"


def log(entry_type, entry_value, log_level=logging.INFO):
    """Take type and value, and emit a JSON-format log entry
    """
    entry_value_out = json.loads(json.dumps(entry_value, default=str))
    # Avoids "Object of type datetime is not JSON serializable" in
    # https://github.com/aws/aws-lambda-python-runtime-interface-client/blob/9efb462/awslambdaric/lambda_runtime_log_utils.py#L109-L135
    #
    # The JSON encoder in the AWS Lambda Python runtime isn't configured to
    # serialize datatime values in responses returned by AWS's own Python SDK!
    #
    # Alternative considered:
    # https://docs.powertools.aws.dev/lambda/python/latest/core/logger

    logger.log(
        log_level, "", extra={"type": entry_type, "value": entry_value_out}
    )


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


def s3_put_bucket_abac(s3_bucket_name, enable_abac):
    """Enable or disable ABAC for an S3 bucket, return response or exception

    As of 2026-04, the Lambda Python 3.14 runtime bundles boto3 v1.40.4
    (2025-08-06), which predates the introduction of attribute-based access
    control for S3 buckets (2025-11-20). Rather than require users to build a
    Lambda bundle, and give up AWS's secure, automatic patching, I use
    CloudControl temporarily.

    https://github.com/boto/botocore/releases/tag/1.40.4
    https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-s3-attribute-based-access-control
    https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html#runtime-management-controls
    https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/resource-operations-update.html
    """
    request_token = ""
    try:
        # For future use (and reduce TesterLambdaFnRole permissions):
        # response = get_aws_client("s3").put_bucket_abac(
        #     Bucket=s3_bucket_name,
        #     AbacStatus={
        #         "Status": "Enabled" if enable_abac else "Disabled"
        #     }
        # )

        response = get_aws_client("cloudcontrol").update_resource(
            TypeName="AWS::S3::Bucket",
            Identifier=s3_bucket_name,
            PatchDocument=json.dumps([{
                "op": "replace",
                "path": "AbacStatus",
                "value": "Enabled" if enable_abac else "Disabled"
            }])
        )
        request_token = (
            response.get("ProgressEvent", {}).get("RequestToken", "")
        )
        waiter = get_aws_client("cloudcontrol").get_waiter(
            "resource_request_success"
        )
        waiter.wait(
            RequestToken=request_token,
            WaiterConfig={
                "Delay": 5,  # Seconds
                "MaxAttempts": 18  # 5 * 18 = 45 seconds; note Lambda Timeout
            }
        )
    except botocore.exceptions.WaiterError as waiter_exception:
        if (
            "Waiter encountered a terminal failure state"
            not in str(waiter_exception)
        ):
            raise
    # No other normal errors expected

    return get_aws_client("cloudcontrol").get_resource_request_status(
        RequestToken=request_token
    )  # No normal error expected


def s3_tag_untag_resource(kwargs_base, tag_key, tag_value=None):
    """Tag or untag (no input value) S3 resource, return response or exception
    """
    try:
        if tag_value is None:
            response = get_aws_client("s3control").untag_resource(
                **kwargs_base,
                TagKeys=[
                    tag_key,
                ]
            )
        else:
            response = get_aws_client("s3control").tag_resource(
                **kwargs_base,
                Tags=[
                    {
                        "Key": tag_key,
                        "Value": tag_value
                    },
                ]
            )
    except Exception as misc_exception:  # pylint: disable=broad-exception-caught
        response = misc_exception
    return response


def s3_tag_untag_bucket(
    s3_bucket_name, tag_key, tag_value=None, untag_after_tag=True
):
    """Tag and/or untag an S3 bucket, return response or exception
    """
    kwargs_base = {
        "AccountId": ENV["AWS_ACCOUNT_ID"],
        "ResourceArn": f"arn:{ENV["AWS_PARTITION"]}:s3:::{s3_bucket_name}",
    }
    if tag_value is not None:
        response = s3_tag_untag_resource(kwargs_base, tag_key, tag_value)
    if (
        (tag_value is None)
        or (untag_after_tag and not isinstance(response, Exception))
    ):
        # Successful tagging response, if any, is discarded
        response = s3_tag_untag_resource(kwargs_base, tag_key)
    return response


def assess_boto3_response_for_deny(response):
    """Take a boto3 response or exception, return flags: Deny, Deny from SCP
    """
    error_message = ""
    if isinstance(response, Exception):
        deny = True
        if isinstance(response, botocore.exceptions.ClientError):
            error_message = getattr(
                response, "response", {}
            ).get("Error", {}).get("Message", "")
    elif "ProgressEvent" in response:
        cloudcontrol_progress = response["ProgressEvent"]
        # pylint: disable=superfluous-parens
        deny = (cloudcontrol_progress.get("OperationStatus", "") == "FAILED")
        # pylint: enable=superfluous-parens
        if deny:
            error_message = cloudcontrol_progress.get("StatusMessage", "")
    else:
        deny = False
    return (
        deny,
        ("explicit deny in a service control policy" in error_message)
        or not deny
    )


def label_result(result_dict):
    """Take test result dict, replace "number" with "test_number": "TEST-N+.N"

    Missing "number" key is an unexpected error.
    """
    result_dict["test_number"] = f"TEST-{result_dict["number"]:.1f}"
    del result_dict["number"]
    return result_dict


def assess_boto3_response(
    method_tested, expected_allow, response, result_dict
):
    """Take test info., expectation, result; assess, update result, and log
    """
    (deny, scp_was_cause_if_deny) = assess_boto3_response_for_deny(response)
    allow = not deny
    result_dict.update({
        "scp": SCP_ON,
        "allow": allow,
        "pass": (expected_allow == allow) and scp_was_cause_if_deny,
    })
    if not result_dict["pass"]:
        result_dict.update({
            "error":
                "Allow was expected"
                if expected_allow else
                "Deny was expected"
                if scp_was_cause_if_deny else
                "Deny from SCP was expected",
        })
        if not scp_was_cause_if_deny:
            result_dict.update({
                "check_cause": response,
        })
    log(f"{method_tested}_TEST_RESULT", label_result(result_dict))


def extract_s3_bucket_traits(event):
    """Take bucket name, return dict of bucket's traits
    """
    s3_bucket_name = event["s3_bucket_name"]
    s3_bucket_traits = s3_bucket_name.removesuffix(
        ENV["S3_BUCKET_CONSTANT_NAME_SUFFIX"]
    ).removeprefix(
        ENV["S3_BUCKET_CONSTANT_NAME_PREFIX"]
    ).split("-")
    s3_bucket = {
        "number": int(s3_bucket_traits[0]),
        "s3_bucket_name": s3_bucket_name,

        "abac": "abac" in s3_bucket_traits,
    }
    return s3_bucket


def assess_s3_put_bucket_abac_response(
    s3_bucket, test_number_fraction, enable_abac, expected_allow=True
):
    """Take S3 bucket dict; test PutBucketAbac, log result
    """
    response = s3_put_bucket_abac(s3_bucket["s3_bucket_name"], enable_abac)
    result_dict = s3_bucket | {  # Copy dict, then update
        "number": s3_bucket["number"] + test_number_fraction,
        "enable_abac": enable_abac,
    }
    assess_boto3_response(
        "S3_PUT_BUCKET_ABAC", expected_allow, response, result_dict
    )


def assess_s3_tag_bucket_response(
    s3_bucket,
    test_number_fraction,
    tag_value,
    tag_key=ENV["S3_BUCKET_TAG_KEY"],
    untag_after_tag=True,
    expected_allow=True
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Take S3 bucket dict, tag value; test TagResource, log result
    """
    response = s3_tag_untag_bucket(
        s3_bucket["s3_bucket_name"],
        tag_key,
        tag_value=tag_value,
        untag_after_tag=untag_after_tag
    )
    result_dict = s3_bucket | {  # Copy dict, then update
        "number": s3_bucket["number"] + test_number_fraction,
        "tag_key": tag_key,
        "tag_value": tag_value,
        "untag_after_tag": untag_after_tag,
    }
    assess_boto3_response(
        "S3_TAG_UNTAG_RESOURCE", expected_allow, response, result_dict
    )


def lambda_handler(event, context):  # pylint: disable=unused-argument
    """Take event (S3 bucket name); test, and log results
    """
    s3_bucket = extract_s3_bucket_traits(event)

    assess_s3_tag_bucket_response(
        s3_bucket,
        0.0,
        "tag-value-0-initial",
        tag_key=NON_PROTECTED_TAG_KEY,
        untag_after_tag=False
    )
    assess_s3_tag_bucket_response(
        s3_bucket, 0.1, "tag-value-1-changed", tag_key=NON_PROTECTED_TAG_KEY
    )
    assess_s3_tag_bucket_response(
        s3_bucket, 0.2, ENV["KMS_KEY_ARN"], expected_allow=SCP_OFF
        # Tags then untags by default, so restore in TEST-5.3 (SCP_OFF)
    )

    # Some test numbers are skipped intentionally.
    # SCP bucket/test numbers are consistent with RCP test equivalents.
    # Simple by comparison, the SCP tests all have consistent decimals:
    # N.0 to N.4  Bucket tagging
    # N.5 to N.7  ABAC

    match s3_bucket["number"]:

        case 1:
            assess_s3_put_bucket_abac_response(
                s3_bucket, 0.5, True, expected_allow=SCP_OFF
            )
            assess_s3_put_bucket_abac_response(
                s3_bucket, 0.6, False, expected_allow=True
            )

            # TEST-1.6 passes in spite of the SCP! CloudControl
            # treats disabling ABAC as a success (idempotence?) if ABAC
            # was already disabled. After AWS updates boto3 in the
            # Python Lambda runtime and CloudControl can be replaced with
            # s3.put_bucket_abc , change expected_allow to SCP_OFF .

        case 3:
            assess_s3_put_bucket_abac_response(
                s3_bucket, 0.6, False, expected_allow=SCP_OFF
            )
            assess_s3_put_bucket_abac_response(
                s3_bucket, 0.7, True, expected_allow=True
            )

            # TEST-3.7 passes in spite of the SCP! See above.

        case 5:
            assess_s3_tag_bucket_response(
                s3_bucket, 0.3, None, expected_allow=SCP_OFF
            )
            assess_s3_tag_bucket_response(
                s3_bucket,
                0.4,
                ENV["KMS_KEY_ARN"],
                untag_after_tag=False,  # Restore tag from TEST-5.2 (SCP_OFF)
                expected_allow=SCP_OFF
            )
