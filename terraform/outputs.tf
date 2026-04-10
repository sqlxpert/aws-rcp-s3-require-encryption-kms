# Resource control policy requiring KMS encryption for tagged S3 buckets
# github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
# GPLv3, Copyright Paul Marcelin

output "rcp_s3_bucket_require_encryption_arn" {
  value       = aws_organizations_policy.rcp_s3_bucket_require_encryption.arn
  description = "ARN of resource control policy requiring KMS encryption for tagged S3 buckets"
}
output "rcp_s3_bucket_require_encryption_id" {
  value       = aws_organizations_policy.rcp_s3_bucket_require_encryption.id
  description = "Physical identifier of resource control policy"
}

output "scp_s3_bucket_restrict_tag_and_abac_changes_arn" {
  value = (
    local.generate_scp
    ? aws_organizations_policy.scp_s3_bucket_restrict_tag_and_abac_changes[0].arn
    : ""
  )
  description = "ARN of system control policy to restrict S3 bucket tag and ABAC changes"
}
output "scp_s3_bucket_restrict_tag_and_abac_changes_id" {
  value = (
    local.generate_scp
    ? aws_organizations_policy.scp_s3_bucket_restrict_tag_and_abac_changes[0].id
    : ""
  )
  description = "Physical identifier of system control policy"
}
