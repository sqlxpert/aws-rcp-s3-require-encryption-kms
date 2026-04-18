# Resource control policy requiring KMS encryption for tagged S3 buckets
# github.com/sqlxpert/aws-rcp-s3-require-encryption-kms
# GPLv3, Copyright Paul Marcelin

variable "rcp_scp_name_suffix" {
  type        = string
  description = "Resource and service control policy name suffix, for blue/green deployments or other scenarios in which you install multiple instances of this module. If you have also installed the CloudFormation template equivalent to this Terraform module, this suffix must differ from the stack name(s)."

  default = "S3RequireEncryptionKms"
}

variable "enable_rcp" {
  type        = bool
  description = "Whether to apply the resource control policy to its designated targets. Change this to false to detach the RCP but preserve the list of its targets."

  default = true
}

variable "rcp_target_ids" {
  type        = list(string)
  description = "Up to 100 r- root ID strings, ou- organizational unit ID strings, and/or AWS account ID numbers to which the RCP will apply. To view the RCP before applying it leave this empty, or start with enable_rcp set to false . Exercise caution when applying any RCP, but note that this RCP generally does not affect pre-existing S3 buckets; it only affects S3 buckets with the designated tag."

  default = []
}

variable "s3_bucket_tag_key" {
  type        = string
  description = "S3 bucket tag key for requiring KMS encryption. Tag rules: https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging.html#tag-key . Attribute-based access control: https://docs.aws.amazon.com/AmazonS3/latest/userguide/buckets-tagging-enable-abac.html . S3 KMS key usage permissions: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html#:~:text=Permissions . To require encryption, make sure that the AWS account is subject to the RCP, enable ABAC for the bucket, and tag the bucket. Tag value: KMS key ARN, partial ARN (ACCOUNT:key/ID), or ID. The KMS key, multi-region key primary, or replica must be in the same region as the bucket. It must also be in the same AWS account, unless the account number is specified in the tag value. Users' permissions and/or the KMS key policy must allow usage of the key. Depending on the bucket's default encryption configuration, users may have to specify the KMS key ARN and/or specify aws:kms encryption when creating objects. If the bucket is the destination of a replication rule, the rule's ReplicaKmsKeyID and the bucket tag must reference the same KMS key."

  default = "security-s3-require-encryption-kms-key-arn"
}

variable "enable_scp" {
  type        = bool
  description = "Whether to apply the service control policy (if generated) to its designated targets. Change this to false to detach the SCP but preserve the list of its targets."

  default = true
}

variable "scp_target_ids" {
  type        = list(string)
  description = "Up to 100 r- root ID strings, ou- organizational unit ID strings, and/or AWS account ID numbers to which the SCP (if generated) will apply. You may wish to apply the SCP, which restricts S3 bucket tag and ABAC changes, before applying the RCP, which actually enforces encryption. In some organizational units, you might apply the RCP but not the SCP, to leave users in control of the ABAC setting and the bucket tag. To view the SCP before applying it, leave this empty, or start with enable_scp set to false . Exercise caution when applying this SCP, because it generally does reduce existing permissions."

  default = []
}

variable "scp_principal_condition" {
  type        = string
  description = "One or more condition expressions determining which roles (or other IAM principals) are not allowed to set/change/remove the designated S3 bucket tag or enable/disable ABAC, for buckets in AWS accounts subject to the SCP. Separate multiple expressions with commas. Follow Terraform string escape rules for double quotation marks (prefix with a backslash) and any IAM policy variables (double the dollar sign). The default means that a request to change ABAC or the designated tag will be denied if it is not made by the manage-s3 role. (Separately, you would have to create the manage-s3 role and attach an IAM policy allowing the role to read and change S3 bucket tags and ABAC.) To avoid generating the SCP, leave this blank. \"ForAnyValue:StringEquals\" is forbidden; to use this condition operator, write a custom policy. For condition operators, see https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html . For condition keys, see https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principal-properties"

  default = "\"ArnNotLike\": { \"aws:PrincipalArn\": [ \"arn:aws:iam::*:role/manage-s3\" ] }"

  validation {
    error_message = "\"ForAnyValue:StringEquals\" is forbidden. To use this condition operator, write a custom policy."

    condition = length(regexall(
      "\"ForAnyValue:StringEquals\"",
      var.scp_principal_condition
    )) == 0
  }
}

variable "rcp_scp_tags" {
  type        = map(string)
  description = "Tag map for the RCP and SCP. Keys, all optional, are tag keys. Values are tag values. This takes precedence over the Terraform AWS provider's default_tags and over tags attributes defined by the module. To remove tags defined by the module, set the terraform , name_suffix , source and rights tags to null ."

  default = {}
}
