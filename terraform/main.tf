# Resource control policy requiring KMS encryption for tagged S3 buckets
# github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
# GPLv3, Copyright Paul Marcelin



locals {
  s3_bucket_tag_value_iam_policy_variable = join(
    "",
    ["$${s3:BucketTag/", var.s3_bucket_tag_key, "}"]
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html
    # This could be done with Terraform HCL string interpolation too, as in
    # "$${s3:BucketTag/${var.s3_bucket_tag_key}}",
    # but I prefer source parity with the CloudFormation template, and the
    # join() expression turns out to be easy for people who are unfamiliar with
    # IAM policy variables to read. In case a future developer forgets to
    # escape "${", the join form yields the more specific error message.
  )
}

resource "aws_organizations_policy" "rcp_s3_bucket_require_encryption" {
  type        = "RESOURCE_CONTROL_POLICY"
  name        = "S3Bucket-${var.rcp_scp_name_suffix}"
  description = "S3 bucket with ABAC enabled, tagged '${var.s3_bucket_tag_key}': Require that all new objects be encrypted with the KMS key specified in the tag value, and forbid disabling ABAC. GPLv3, Copyright Paul Marcelin. github.com/sqlxpert"
  tags        = local.rcp_scp_tags

  # See "NoWildcardOrVariable" comment in
  # ../cloudformation/aws-rcp-s3-require-encryption-kms.yaml

  # I prefer data.aws_iam_policy_document , but a HEREDOC allows source parity
  # with CloudFormation (except for variables):
  content = <<-END_POLICY
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "NoWildcardOrVariable",
          "Effect": "Deny",
          "Principal": "*",
          "Action": "s3:PutObject",
          "Resource": "*",
          "Condition": {
            "Null": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": "false"
            },
            "StringNotLike": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": [
                "*$${*}*",
                "*$${?}*",
                "*$${$}*",
                "*{*",
                "*}*",
                "*\\*",
                "*%*",
                "*=*",
                "*+*",
                "*@*"
              ]
            }
          }
        },
        {
          "Sid": "PartialArnFormat",
          "Effect": "Deny",
          "Principal": "*",
          "Action": "s3:PutObject",
          "Resource": "*",
          "Condition": {
            "Null": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": "false"
            },
            "StringNotLike": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": [
                "????????????:key/????????-????-????-????-????????????",
                "????????????:key/mrk-????????????????????????????????"
              ]
            }
          }
        },
        {
          "Sid": "KmsKeyInRequestMatches",
          "Effect": "Deny",
          "Principal": "*",
          "Action": "s3:PutObject",
          "Resource": "*",
          "Condition": {
            "Null": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": "false"
            },
            "StringNotLike": {
              "s3:x-amz-server-side-encryption-aws-kms-key-id": "arn:${local.partition}:kms:*:${local.s3_bucket_tag_value_iam_policy_variable}"
            }
          }
        },
        {
          "Sid": "CannotDisableAbac",
          "Effect": "Deny",
          "Principal": "*",
          "Action": "s3:PutBucketAbac",
          "Resource": "*",
          "Condition": {
            "Null": {
              "s3:BucketTag/${var.s3_bucket_tag_key}": "false"
            }
          }
        }
      ]
    }
  END_POLICY
}

resource "aws_organizations_policy_attachment" "rcp_s3_bucket_require_encryption" {
  for_each = toset(var.enable_rcp ? var.rcp_target_ids : [])

  policy_id = aws_organizations_policy.rcp_s3_bucket_require_encryption.id
  target_id = each.key
}



locals {
  comma_after_scp_principal_condition = (
    length(var.scp_principal_condition) > 0 ? "," : ""
  )
}

resource "aws_organizations_policy" "scp_s3_bucket_restrict_tag_and_abac_changes" {
  count = local.generate_scp ? 1 : 0

  type        = "SERVICE_CONTROL_POLICY"
  name        = "S3BucketRestrictTagAndAbacChanges-${var.rcp_scp_name_suffix}"
  description = "S3 bucket: Matching IAM principals cannot enable/disable ABAC. If ABAC is enabled, they cannot add/change/remove '${var.s3_bucket_tag_key}' bucket tag. GPLv3, Copyright Paul Marcelin. github.com/sqlxpert"
  tags        = local.rcp_scp_tags

  # I prefer data.aws_iam_policy_document , but a HEREDOC allows source parity
  # with CloudFormation (except for variables) and permits insertion of values
  # that the user specifies in JSON (native for the IAM policy language):
  content = <<-END_POLICY
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Deny",
          "Action": "s3:PutBucketAbac",
          "Resource": "*",
          "Condition": {
            ${var.scp_principal_condition}
          }
        },
        {
          "Effect": "Deny",
          "Action": [
            "s3:TagResource",
            "s3:UntagResource"
          ],
          "Resource": "*",
          "Condition": {
            ${var.scp_principal_condition}${local.comma_after_scp_principal_condition}
            "ForAnyValue:StringEquals": {
              "aws:TagKeys": "${var.s3_bucket_tag_key}"
            }
          }
        }
      ]
    }
  END_POLICY
}

resource "aws_organizations_policy_attachment" "scp_s3_bucket_restrict_tag_and_abac_changes" {
  for_each = toset(
    (local.generate_scp && var.enable_scp) ? var.scp_target_ids : []
  )

  policy_id = aws_organizations_policy.scp_s3_bucket_restrict_tag_and_abac_changes[0].id
  target_id = each.key
}
