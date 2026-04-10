# Resource control policy requiring KMS encryption for tagged S3 buckets
# github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
# GPLv3, Copyright Paul Marcelin

data "aws_caller_identity" "current" {}
locals {
  caller_arn_parts = provider::aws::arn_parse(
    data.aws_caller_identity.current.arn
  )
  # Provider functions added in Terraform v1.8.0
  # arn_parse added in Terraform AWS provider v5.40.0

  partition = local.caller_arn_parts["partition"]

  module_directory = basename(path.module)
  rcp_scp_tags = merge(
    {
      terraform   = "1"
      name_suffix = var.rcp_scp_name_suffix
      source      = "github.com/sqlxpert/aws-rcp-s3-require-encryption-kms/blob/main/${local.module_directory}"
      rights      = "GPLv3. Copyright Paul Marcelin."
    },
    var.rcp_scp_tags,
  )

  generate_scp = (length(var.scp_principal_condition) > 0)
}
