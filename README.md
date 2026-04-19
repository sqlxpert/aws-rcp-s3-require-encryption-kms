# S3 Encryption Tags

Have you and your colleagues been maintaining a separate bucket policy for
every encrypted S3 bucket?

&#128161; I've devised a consistent way to enforce S3 encryption...in one
bucket or thousands...in one region or many...in one account or many...with one
key or many... **Simply tag each S3 bucket with the ARN of a KMS key!**

>&#128274; Software supply chain security is on everyone's mind. This solution
does not require executable code or dependencies. It creates a resource control
policy, which you can read before attaching. If you do not want to test it by
running Lambda functions, or by installing the AWS command-line interface
locally, I also explain how to test in AWS CloudShell. I've made GitHub
releases immutable.

Jump to:
[Installation](#install)
&bull;
[Protection](#protect-bucket-tags)
&bull;
[Testing](#test)

## How to Use

### Tag a Bucket

 1. Turn on
    [attribute-based access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/buckets-tagging-enable-abac.html)
    for an S3 bucket.

 2. Tag the S3 bucket with a KMS key ARN.

    |Tag&nbsp;Key|`security-s3-require-encryption-kms-key-arn`|
    |---:|:---|
    |Tag&nbsp;Value (Sample)|`arn:aws:kms:us-east-1:112233445566:`<br/>`key/0123abcd-45ef-67ab-89cd-012345efabcd`|

    Now, KMS encryption is required whenever a new object or object version is
    created, or an object is overwritten.

 3. Optionally, specify `aws:kms` and the same KMS key, in the bucket's
    [default encryption configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html#:~:text=Changes,before%20enabling%20default%20encryption).
    Users won't have to specify the KMS key.

#### Check the Rules

<details>
  <summary>Detailed rules...</summary>

<br/>

&check; Attribute-based access control must be enabled for the S3 bucket.

<details>
  <summary>Different ways to designate the KMS key...</summary>

---

|Identifier|Bucket Tag Value (Sample)|
|:---|:---|
|KMS&nbsp;key&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|
|KMS&nbsp;key&nbsp;partial&nbsp;ARN|`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|
|KMS&nbsp;key&nbsp;ID|`key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|

_* Future-proofing recommendation: Create `mrk-`
[multi-region KMS keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html).
Use the KMS key policy to lock the
[primary region](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-auth.html#mrk-auth-update).
Limit
[replica regions](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-auth.html#mrk-auth-replicate)
until you need replica keys in other regions._

&check; A KMS key alias cannot be used here.

&check; The KMS key must be in the same AWS account as the S3 bucket, unless
the KMS key's account number is in the bucket tag value.

---

</details>

&check; The KMS key must be in the same region as the S3 bucket.

&check; Users' and roles' permissions and/or the KMS key policy must allow
[usage of the KMS key](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html#:~:text=Permissions).

&check; The S3 bucket's default encryption configuration, if set, must specify
`aws:kms` and designate the same KMS key. (For uniformity, ~`aws:kms:dsse`~
[_dual-layer_ KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingDSSEncryption.html)
is not allowed.)

&check; The
[S3 Bucket Keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html)
setting, if configured, must reference the same KMS key. _Cost-saving
recommendation: Use this feature to reduce KMS API charges._

&check; SSE-C-encrypted objects can't be created if ABAC is enabled and the
bucket is tagged. Also check that
[SSE-C encryption is blocked](https://docs.aws.amazon.com/AmazonS3/latest/userguide/blocking-unblocking-s3-c-encryption-gpb.html),
especially if the S3 bucket was created before May,&nbsp;2026.

&check; After ABAC has been enabled, you can only set or change the bucket tag
to a correctly-formatted value, and you must remove the bucket tag before you
can disable ABAC.

_Security recommendation: Block routine use of KMS keys housed in AWS accounts
that are outside your organization. Consider a service control policy statement
with an
[`aws:ResourceOrgID`](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-resourceorgid)
condition._

</details>

### Create Encrypted Objects

Depending on the S3 bucket's default encryption configuration, users may need
to specify `aws:kms` and the KMS key, when creating objects.

<details>
  <summary>If encryption details are needed...</summary>

---

|Command or API&nbsp;Method|Option, Parameter, or Header|Input Value|
|:---|---:|:---:|
|`aws s3 cp`|`--sse`|`'aws:kms'`|
||`--sse-kms-key-id`|&#8675;|
|`aws s3api put-object`|`--server-side-encryption`|`'aws:kms'`|
||`--ssekms-key-id`|&#8675;|
|`client("s3").put_object()`<br/>or equivalent in a different AWS&nbsp;SDK|`ServerSideEncryption=`|`"aws:kms"`|
||`SSEKMSKeyId=`|&#8675;|
|`PutObject`|`x-amz-server-side-encryption:`|`aws:kms`|
||`x-amz-server-side-encryption-aws-kms-key-id:`|&#8675;|

<br/>

|Identifier|Sample Input Value &#8675;|
|:---|:---|
|KMS&nbsp;key&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd` *|
|KMS&nbsp;key&nbsp;ID|`0123abcd-45ef-67ab-89cd-012345efabcd`|
||`mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;key&nbsp;alias&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/alias_for_my_customer_managed_kms_key`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/aws/s3`|
|KMS&nbsp;key&nbsp;alias&nbsp;name|`alias/alias_for_my_customer_managed_kms_key`|
||`alias/aws/s3`|

<br/>

&check; The KMS key must be in the same region as the S3 bucket.

&check; The KMS key specified in the `PutObject` request or in the bucket's
default encryption configuration must be the KMS key designated by the
`security-s3-require-encryption-kms-key-arn` bucket tag value.

&check; The requester must be in the same AWS account as the KMS key and the
S3 bucket if a KMS key ID (or a KMS alias name) with no account number is
specified in the `PutObject` request or in the bucket's default encryption
configuration.

_* Security recommendation: Create KMS keys in a separate AWS account with no
other resources. This is the only way, given the default
["Enable IAM User Permissions"](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam)
statement, to be certain that the
[KMS key policy](https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html#:~:text=Use%20key%20policies)
controls all access._

---

</details>

### Resolve Errors

"AccessDenied" is the most common error when a user tries to create an object
in a tagged S3 bucket.

&check; If specifying the same **KMS key full ARN** in the
`security-s3-require-encryption-kms-key-arn` bucket tag value and in the
`PutObject` request does not resolve the error, review the
[rules](#check-the-rules),
check the user or role's permissions (identity-based policies), and check the
KMS key policy (resource-based policy).

In case the user missed "require-encryption-kms-key-arn"... in the bucket tag
key, or didn't check the bucket tag value to find the correct key, the error
message tells a local administrator where to look: "explicit deny in a resource
control policy", for example.

#### Error Messages

<details>
  <summary>Sample error messages</summary>

<br/>

 1. Creating objects

    The KMS key specified in the `PutObject` request or in the bucket's default
    encryption configuration is relevant here.

    The error for a non-existent KMS key is:

    ```text
    An error occurred (KMS.NotFoundException)
    when calling the PutObject operation:
    Key 'arn:aws:kms:us-east-1:112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd'
    does not exist
    ```

    Most other error messages begin with...

    ```text
    An error occurred (AccessDenied) when calling the PutObject operation:
    User: arn:aws:sts::112233445566:assumed-role/AWSReservedSSO_PermSetName_0123456789abcdef/abcde
    is not authorized to perform:
    ```

    ...and continue with...

    - Encryption not requested (or KMS key does not match bucket tag value)

      ```text
      s3:PutObject
      on resource: "arn:aws:s3:::test-kms-encryption-required/non-encrypted.txt"
      with an explicit deny in a resource control policy
      ```

    - Insufficient KMS key usage permissions

      ```text
      kms:GenerateDataKey
      on this resource
      because no identity-based policy allows the kms:GenerateDataKey action"
      ```

    - Insufficient KMS key usage permissions (key is in a different AWS account)

      ```text
      kms:GenerateDataKey
      on this resource
      because the resource does not exist in this Region,
      no resource-based policies allow access,
      or a resource-based policy explicitly denies access
      ```

 2. Tagging a bucket or changing the ABAC setting

    If a user tries to disable ABAC for an S3 bucket tagged with
    `security-s3-require-encryption-kms-key-arn`&nbsp;, the following error
    occurs:

    ```text
    An error occurred (AccessDenied) when calling the
    PutBucketAbac operation:
    User: arn:aws:sts::112233445566:assumed-role/AWSReservedSSO_PermSetName_0123456789abcdef/abcde
    is not authorized to perform: s3:PutBucketAbac on resource:
    "arn:aws:s3:::test-kms-encryption-required"
    with an explicit deny in a resource control policy
    ```

    Remove the bucket tag first, then disable ABAC.

    If ABAC is enabled and a user tries to set or change the bucket tag to an
    incorrectly-formatted value, the error message is similar but the operation
    is "TagResource". Use of one of the KMS key identifier formats listed in
    the
    [rules](#check-the-rules),
    under "Different ways to designate the KMS key..."

    If the optional service control policy applies, a similar error occurs when
    a non-exempt user tries to add, update or delete the
    `security-s3-require-encryption-kms-key-arn` bucket tag (for an S3 bucket
    with ABAC enabled) or to enable or disable ABAC for _any_ S3 bucket. The
    policy type is "service control policy" and the S3 operation is one of:

    - "TagResource"
    - "UntagResource"
    - "PutBucketAbac"

    Use an IAM role that is exempt from the SCP, or ask the local AWS
    administrator to temporarily detach the SCP from the AWS account.

</details>

#### Causes of Error

<details>
  <summary>List of potential causes of error</summary>

<br/>

"AccessDenied" when a user tries to create an object in a tagged S3 bucket
indicates that...

 1. The user...
    - tried to create a non-encrypted S3 object,
    - lacks sufficient key usage permissions for the KMS key designated by the
    `security-s3-require-encryption-kms-key-arn` bucket tag value, or
    - specified a different KMS key, or
 2. The S3 bucket's default encryption configuration specifies...
    - an inconsistent encryption type
      (&nbsp;`SSEAlgorithm`&nbsp;&ne;&nbsp;`aws:kms`&nbsp;) or
    - a different KMS key (in&nbsp;`KMSMasterKeyID`&nbsp;), or
 3. The KMS key specified by the user or by the bucket's default encryption
    configuration, or designated by the bucket tag value...
    - is not in the same region as the S3 bucket, or
    - is not in the same AWS account as the bucket (if a KMS key ID with no
      account number is specified), or
    - is not in the same AWS account as the requester (if a KMS key ID with no
      account number is specified), or
    - does not exist.

</details>

## Install

 1. Authenticate in your AWS&nbsp;Organizations management account. Choose an
    IAM role with administrative privileges. Choose the region where you manage
    infrastructure-as-code templates that create non-regional resources.

 2. Review
    [AWS&nbsp;Organizations Settings](https://console.aws.amazon.com/organizations/v2/home/settings).
    Make sure that the
    [all features](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_org_support-all-features.html)
    feature set is enabled.

    Review
    [AWS&nbsp;Organizations Policies](https://console.aws.amazon.com/organizations/v2/home/policies).
    Make sure that the...

    - [resource control policy](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html)
      and
    - [service control policy](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)

    ...policy types are both enabled.

 3. Install using CloudFormation or Terraform.

    - **CloudFormation**<br/>_Easy_ &check;

      In the AWS Console,
      [create a CloudFormation stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create).

      Select "Upload a template file", then select "Choose file" and navigate
      to a locally-saved copy of
      [cloudformation/aws-rcp-s3-require-encryption-kms.yaml](/../../blob/main/cloudformation/aws-rcp-s3-require-encryption-kms.yaml?raw=true)
      [right-click to save as...].

      On the next page, set:

      - Stack name: `S3RequireEncryptionKms`
      - RCP root IDs, OU IDs, and/or AWS account ID numbers
        (&nbsp;`RcpTargetIds`&nbsp;):
        Enter the number of the account or the `ou-` ID of the organizational
        unit that you use for testing resource control policies.

    - **Terraform**

      Check that you have at least:

      - [Terraform v1.10.0 (2024-11-27)](https://github.com/hashicorp/terraform/releases/tag/v1.10.0)
      - [Terraform AWS provider v6.0.0 (2025-06-18)](https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.0.0)

      Add the following child module to your existing root module:

      ```terraform
      module "s3_require_encryption" {
        source = "git::https://github.com/sqlxpert/aws-rcp-s3-require-encryption-kms.git//terraform?ref=main"
        # Reference a specific version from github.com/sqlxpert/aws-rcp-s3-require-encryption-kms/releases
        # Check that the release is immutable!

        rcp_target_ids = ["112233445566", "ou-abcd-efghijkl",]
      }
      ```

      Populate the `rcp_target_ids` list with a string for the number of the
      account or the `ou-` ID of the organizational unit that you use for
      testing resource control policies.

      Have Terraform download the module's source code. Review the plan before
      typing `yes` to allow Terraform to proceed with applying the changes.

      ```shell
      terraform init
      terraform apply
      ```

 4. <a id="install-step-5-context"></a>Test the RCP as explained below, in
    [Test](#test).

 5. Add other AWS account numbers, `ou-`
    organizational unit IDs, or the `r-` root ID to apply the RCP broadly.

## Protect Bucket Tags

This project is all about scale. It's about getting a policy right one time,
then generalizing it across an entire organization. Successfully scaling our
work as infrastructure engineers also requires transferring knowledge and
control to our "customers" -- developers, data scientists, machine learning
engineers, etc. Now you can delegate permission to require encryption in S3
buckets, but in a consistent way.

Instead of policing the S3 encryption-related settings in miscellaneous
Terraform modules or CloudFormation stacks that your colleagues might adopt, or
helping them write encryption statements for one S3 bucket policy after
another, you can now offer them a universal solution. Choose a KMS key and tag
a bucket! Tag an existing bucket with the ARN of the KMS key already in use,
and retire "one-off" statements from a bucket policy!

If you decide to delegate, you can choose different levels of authority for
different organizational units, and for different IAM roles.

<details>
  <summary>About the optional service control policy...</summary>

<br/>

I provide an optional service control policy that you can apply to
organizational units to prevent non-exempt IAM roles from enabling or disabling
ABAC for any S3 bucket. For buckets with ABAC enabled, the policy also prevents
non-exempt roles from adding/changing/removing the
`security-s3-require-encryption-kms-key-arn`  bucket tag. **The lack of such a
control undermines the security of most real-world ABAC applications.**

Test the SCP before applying it, because it generally reduces existing S3
permissions. Human users or automated processes might rely on those
permissions.

You will need at least one SCP-exempt role in every account, to manage S3
buckets. I recommend
[IAM Identity Center permission sets](https://docs.aws.amazon.com/singlesignon/latest/userguide/permissionsets.html).
You can customize `ScpPrincipalCondition` / `scp_principal_condition` to
[reference permission set roles](https://docs.aws.amazon.com/singlesignon/latest/userguide/referencingpermissionsets.html).

SCPs do not affect roles or other IAM principals in the AWS&nbsp;Organizations
management account.

The SCP offers two-way protection: Non-exempt roles can neither remove
restrictions from S3 buckets nor place new restrictions on them. For one-way
protection, that is, allowing non-exempt roles to enroll buckets but not to
disenroll them, you could write an SCP that:

- does not deny use of `s3:TagResource` to add the
  `security-s3-require-encryption-kms-key-arn` bucket tag,
- does deny use of `s3:TagResource` to change the tag's value,
- still does deny use of `s3:UntagResource` to remove the tag, and
- does not deny `s3:PutBucketAbac`&nbsp;

On the surface, it seems that this would allow enabling _and_ disabling
attribute-based access control. (ABAC is significant because it makes S3
bucket tags effective. When ABAC is disabled, S3 bucket tag IAM condition
keys are not available.) But if the bucket tag can't be removed, ABAC can't
be disabled, thanks to the **R**CP!

You can read more about how the RCP works in the sister project,
[github.com/sqlxpert/aws-rcp-s3-require-intelligent-tiering](https://github.com/sqlxpert/aws-rcp-s3-require-intelligent-tiering#how-it-works)&nbsp;.

</details>

## Test

### Test the RCP Manually

Although automated testing is the only practical way to cover the many cases
that the RCP was designed to handle, I also recommend that you try the manual
test commands. It turns out that manual testing is a good learning experience,
a good way to experiment with modern (2025 and 2026) S3 features like
[attribute-based access control](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-s3-attribute-based-access-control)
and the
[account-regional bucket namespace](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-s3-account-regional-namespaces).


<details>
  <summary>Manual test commands...</summary>

 1. Authenticate in your test AWS account or an account in your test
    organizational unit.  **This AWS account number must be subject to
    the RCP and not subject to the optional SCP.** (RCPs and SCPs do not affect
    resources in your AWS&nbsp;Organizations management account.) Choose a role
    with full S3 permissions.

    - I recommend using
      [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home).
      The AWS CLI is pre-installed, AWS keeps it up-to-date for you, and there
      is no need to obtain AWS credentials, whether long- or hopefully
      short-lived, on your local computer.

 2. Populate a test file, confirm the name of a new S3 bucket, and store the
    bucket name.

    ```shell
    cd /tmp
    echo 'Test data' > test.txt

    DATE=$( date --utc --iso-8601 )
    AWS_ACCOUNT=$( aws sts get-caller-identity --query 'Account' --output text )
    read -p 'S3 bucket     : ' \
      -e -i "delete-after-${DATE}-${AWS_ACCOUNT}-${AWS_REGION:?'Set this first'}-an" -r S3_BUCKET_NAME

    ```

 3. Create the bucket.

    ```shell
    aws s3api create-bucket \
      --create-bucket-configuration "LocationConstraint=${AWS_REGION}" \
      --bucket-namespace 'account-regional' --bucket "${S3_BUCKET_NAME}"

    ```

 4. Create an object encrypted with the `alias/aws/s3` AWS-managed KMS key.
    AWS will create the key, if necessary.

    ```shell
    aws s3 cp test.txt "s3://${S3_BUCKET_NAME}" --sse 'aws:kms'

    ```

 5. Confirm the bucket tag key.

    ```shell
    read -p 'Bucket tag key: ' \
      -e -i 'security-s3-require-encryption-kms-key-arn' -r S3_BUCKET_TAG_KEY

    ```

 6. Get the ID of the AWS-managed KMS key. (&nbsp;`list-aliases` returns KMS
    key IDs, not full ARNs. The RCP accepts a KMS key ID as a bucket tag value.
    This shorthand works as long as the user, the KMS key and the S3 bucket are
    all in the same AWS account.)

    ```shell
    KMS_KEY_ID=$( \
      aws kms list-aliases \
        --query $'Aliases[?AliasName == \'alias/aws/s3\'].TargetKeyId' \
        --output 'text' \
    )
    read -p 'KMS key ID    : ' -e -i "${KMS_KEY_ID}" -r KMS_KEY_ID

    ```

 7. Enable ABAC for the bucket.

    ```shell
    aws s3api put-bucket-abac --bucket "${S3_BUCKET_NAME}" \
      --abac-status 'Status=Enabled'

    ```

 8. Tag the bucket.

    ```shell
    aws s3control tag-resource \
      --account-id "${AWS_ACCOUNT}" --resource-arn "arn:aws:s3:::${S3_BUCKET_NAME}" \
      --tags "Key=${S3_BUCKET_TAG_KEY},Value=${KMS_KEY_ID}"

    ```

 9. Try creating an encrypted object. This should succeed. Try creating a
    non-encrypted object. This should produce "AccessDenied".

    ```shell
    #
    # Encrypted object
    aws s3 cp test.txt "s3://${S3_BUCKET_NAME}" --sse 'aws:kms'
    #
    # Non-encrypted object
    aws s3 cp test.txt "s3://${S3_BUCKET_NAME}"

    ```

10. Try disabling ABAC for the bucket. This should produce "AccessDenied".

    ```shell
    aws s3api put-bucket-abac --bucket "${S3_BUCKET_NAME}" \
      --abac-status 'Status=Disabled'

    ```

11. Untag the bucket

    ```shell
    aws s3control untag-resource \
      --account-id "${AWS_ACCOUNT}" --resource-arn "arn:aws:s3:::${S3_BUCKET_NAME}" \
      --tag-keys "${S3_BUCKET_TAG_KEY}"

    ```

12. Repeat Step&nbsp;10 of these manual testing instructions. Now that the
    bucket is untagged, disabling ABAC should be possible.

13. Delete the bucket.

    ```shell
    aws s3 rb "s3://${S3_BUCKET_NAME}" --force
    ```

14. Continue with
    [Step 5 of the _installation_ instructions](#install-step-5-context).

</details>

### Test the RCP with Lambda

<details>
  <summary>Instructions for automated RCP testing...</summary>

 1. Authenticate to the AWS Console in your test AWS account or an account in
    your test organizational unit. **This AWS account number must be subject to
    the RCP and not subject to the optional SCP.** (RCPs and SCPs do not affect
    resources in your AWS&nbsp;Organizations management account.) Choose a role
    with full S3 permissions.

 2. [Create a CloudFormation stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create)
    from
    [test/test-rcp-s3-encryption-tags.yaml](/../../blob/main/test/test-s3-encryption-tag-rcp.yaml?raw=true)&nbsp;.

    - Copy and paste the **suggested stack name. Do not change it.** Creating
      more than one stack from this template is not supported.
    - Fill in the KMS key ARN. If KMS encryption has already been used with S3
      in this AWS account and region, you can view the AWS-managed
      [`aws/s3`](https://console.aws.amazon.com/kms/home#/kms/defaultKeys)
      key and copy its ARN. (KMS key aliases won't work in bucket tag values,
      because they don't work in policies.)
    - Because this is for temporary use during testing, I do not provide a
      Terraform alternative.
    - Trouble creating the stack usually signals a local permissions problem,
      such as insufficient permissions attached to your IAM role, or the effect
      of a hidden policy such as a permissions boundary or a service control
      policy. For example, make sure that the AWS account number is not subject
      to the optional SCP, or that your role is exempt from the SCP. If you
      cannot resolve the problem, check with your local AWS administrator.

 3. Open the
    [TestDirector](https://console.aws.amazon.com/lambda/home#/functions/TestRcpS3EncryptionTagTestDirector?tab=testing)
    Lambda function's "Test" tab and click the orange "Test" button.

    - The "Event JSON" value will be ignored.

 4. Open the "All events" search page for the
    [Test](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestRcpS3EncryptionTag/log-events$3FfilterPattern$3Derror)
    CloudWatch log group, and filter for `error`&nbsp;. Review any errors.

    - Uncaught exceptions are unexpected, and usually signal local permission
      problems.
    - Resource control policy tests cover a set of 8 (if the KMS key has a
      different AWS account number) or 10 (if it's in the same account)
      numbered S3 buckets with various combinations of ABAC, bucket tags, and
      KMS key identifiers. Each test result is a JSON object.
    - Useful
      [CloudWatch Logs filter patterns](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html#matching-terms-events):

      |Filter Pattern|Scope|
      |:---:|:---|
      |`error`|All errors|
      |`timeout`|Lambda function timeouts (unlikely)|
      |`%TEST-\d+%`|All tests|
      |`"TEST-5."`|Tests on S3 bucket&nbsp;5 (for example)|
      |`%TEST-\d+\.0%`|Tests that create an unencrypted object (decimal&nbsp;0)|
      |`%TEST-\d+\.1%`|Tests that create an encrypted object|
      |`%TEST-\d+\.[2-9]%`|Tests that change bucket tags or the ABAC setting|

 5. To re-test, open the list of log streams in the
    [Test](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestRcpS3EncryptionTag)
    log group, check the topmost checkbox to select all of the log streams,
    then click "Delete". Return to Step&nbsp;3 of these Lambda testing
    instructions.

    - If there were timeouts, or errors changing bucket tags or the ABAC
      setting (decimal 2 through 9 in the test number), check the
      [Test](https://console.aws.amazon.com/cloudformation/home#/stacks?filteringText=TestS3RequireEncryptionKms&filteringStatus=active&viewNested=true)
      CloudFormation stack for drift and correct any drift before re-testing
      ("Stack actions" &rarr; "Detect drift", then "Stack actions" &rarr;
      "View drift results").

 6. When you are finished, delete the CloudFormation stack.

    - If there was an unexpected error, you might first have to delete all
      objects from the test S3 buckets listed in the
      [Test](https://console.aws.amazon.com/cloudformation/home#/stacks?filteringText=TestS3RequireEncryptionKms&filteringStatus=active&viewNested=true)
      CloudFormation stack's "Resources" tab.

</details>

### Test the Optional SCP

<details>
  <summary>Instructions for automated SCP testing...</summary>

<br/>

Testing the **S**CP with Lambda is similar to
[testing the RCP with Lambda](#test-the-rcp-with-lambda).
Differences to note:

- Start in an AWS account that is subject to both the RCP and the **S**CP.
- Before creating the CloudFormation stack, temporarily detach the **S**CP from
  the AWS account. (Make this change in your AWS&nbsp;Organizations management
  account.)
- The CloudFormation template for **S**CP testing is
  [test/test-scp-protect-s3-encryption-tag.yaml](/../../blob/main/test/test-scp-protect-s3-encryption-tag.yaml?raw=true)&nbsp;.
  Set `RcpOn` to `false`&nbsp;.
- If you are advanced user, you can re-attach the **S**CP after creating the
  SCP testing CloudFormation stack but before testing. For the first round
  of testing, exempt `TestScpProtectS3EncryptionTag-TesterLambdaFnRole` from
  the SCP by customizing `ScpPrincipalCondition` / `scp_principal_condition` in
  the SCP CloudFormation stack or Terraform module. (Make these changes in your
  AWS&nbsp;Organizations management account.)
- The direct AWS Console links for **S**CP testing are:
  - [TestDirector Lambda function](https://aws.amazon.com/lambda/home#/functions/TestScpProtectS3EncryptionTagTestDirector?tab=testing)
  - [Log group - all events](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestScpProtectS3EncryptionTag/log-events)
  - [Log group - list of log streams](
https:/console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestScpProtectS3EncryptionTag)
- Only three S3 buckets are needed to test the **S**CP. These correspond to
  buckets 1, 3 (ABAC) and 5 (ABAC + bucket tag) in the RCP test stack. Because
  the **S**CP tests are simpler, decimal ranges identify similar operations: 0
  through 4 for changing bucket tags and 5 through 7 for changing the ABAC
  setting. Gaps between **S**CP test numbers are intentional.
- After testing _without_ the SCP, you must re-test _with_ the SCP. Update the
  CloudFormation stack, changing `RcpOn` to `true`&nbsp;. Re-attach the **S**CP
  to the AWS account containing the CloudFormation stack. Repeat the test
  process.

</details>

### Report Bugs

Please
[report bugs](/../../issues).
Thank you!

## Licenses

|Scope|Link|Included Copy|
|:---|:---|:---|
|Source code, and source code in documentation|[GNU General Public License (GPL) 3.0](http://www.gnu.org/licenses/gpl-3.0.html)|[LICENSE-CODE.md](/LICENSE-CODE.md)|
|Documentation, including this ReadMe file|[GNU Free Documentation License (FDL) 1.3](http://www.gnu.org/licenses/fdl-1.3.html)|[LICENSE-DOC.md](/LICENSE-DOC.md)|

Copyright Paul Marcelin

Contact: `marcelin` at `cmu.edu` (replace "at" with `@`)
