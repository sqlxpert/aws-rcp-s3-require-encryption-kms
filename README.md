# S3 Encryption Tag Magic

Have you been maintaining a separate bucket policy for every encrypted S3
bucket?

&#128161; I've devised **a consistent way to enforce S3 encryption**...in one
bucket or thousands...in one region or many...in one account or many...with one
key or many... Simply tag each S3 bucket with the ARN of a KMS key!

This project is all about scale. It's about getting a policy right one time
and then generalizing it across a whole organization.

>&#128274; Software supply chain security is on everyone's mind. This solution
does not require executable code or dependencies. It creates a resource control
policy, which you can read before attaching. If you do not want to test it by
running Lambda functions, or by installing the AWS command-line interface
locally, I also explain how to test in AWS CloudShell. I've made GitHub
releases immutable.

## How to Use

### Tag a Bucket

 1. Turn on
    [attribute-based access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/buckets-tagging-enable-abac.html)
    for an S3 bucket.

 2. Tag the S3 bucket with a KMS key ARN.

    |Tag&nbsp;Key|`security-s3-require-encryption-kms-key-arn`|
    |---:|:---|
    |Tag&nbsp;Value (Sample)|`arn:aws:kms:us-east-1:112233445566:`<br/>`key/0123abcd-45ef-67ab-89cd-012345efabcd`|

    KMS encryption is now required whenever a new object or object version is
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
|KMS&nbsp;Key&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|
|KMS&nbsp;Key&nbsp;partial&nbsp;ARN|`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|
|KMS&nbsp;Key&nbsp;ID|`key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd` *|

_* Future-proof recommendation: Create `mrk-`
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

&check; Users' permissions and/or the KMS key policy must allow
[usage of the KMS key](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html#:~:text=Permissions).

&check; The S3 bucket's default encryption configuration, if set, must specify
s`aws:kms` and designate the same KMS key. (For uniformity, ~`aws:kms:dsse`~
[_dual-layer_ KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingDSSEncryption.html)
is not allowed.)

&check; SSE-C-encrypted objects can't be created if ABAC is enabled and the
bucket is tagged. Also check that
[SSE-C encryption is blocked](https://docs.aws.amazon.com/AmazonS3/latest/userguide/blocking-unblocking-s3-c-encryption-gpb.html),
especially if the S3 bucket was created before May,&nbsp;2026.

&check; After ABAC has been enabled, you can only set or change the bucket tag
to a correctly-formatted value, and you must remove the bucket tag before you
can disable ABAC.

_Secure recommendation: Block routine use of KMS keys housed in AWS accounts
that are outside your organization. Consider a service control policy statement
with an
[`aws:ResourceOrgID`](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-resourceorgid)
condition._

</details>

### Create Encrypted Objects

Depending on the S3 bucket's default encryption configuration, users may have
to specify the KMS key, and/or `aws:kms` encryption, when creating objects.

<details>
  <summary>Specifying encryption details...</summary>

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
|KMS&nbsp;Key&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd` *|
|KMS&nbsp;Key&nbsp;ID|`0123abcd-45ef-67ab-89cd-012345efabcd`|
||`mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/alias_for_my_customer_managed_kms_key`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/aws/s3`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;Name|`alias/aws/s3`|
||`alias/alias_for_my_customer_managed_kms_key`|

<br/>

&check; The KMS key must be in the same region as the S3 bucket.

&check; The KMS key specified in the `PutObject` request or in the bucket's
default encryption configuration must be the KMS key designated by the
`security-s3-require-encryption-kms-key-arn` bucket tag value.

&check; The requester must be in the same AWS account as the KMS key and the
S3 bucket if a KMS key ID (or a KMS alias name) with no account number is
specified in the `PutObject` request or in the bucket's default encryption
configuration.

_* Secure recommendation: Create KMS keys in a separate AWS account with no
other resources. This is the only way, given the default
["Enable IAM User Permissions"](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam)
statement, to be certain that the
[KMS key policy](https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html#:~:text=Use%20key%20policies)
controls all access._

---

</details>

### Resolve Errors

"AccessDenied" will be the most common error when a user tries to create an
object in a tagged S3 bucket.

&check; Reduce uncertainty by specifying a **KMS key full ARN** in the
`security-s3-require-encryption-kms-key-arn` bucket tag value and in the
`PutObject` request. If this does not resolve the error, review the
[rules](check-rules),
check the user's permissions, and check the KMS key policy.

In case the user missed "require-encryption-kms-key-arn"... in the bucket tag
key, or didn't check the bucket tag value to find the correct key, the error
message tells an administrator where to look: "explicit deny in a resource
control policy", for example.

#### Sample Error Messages

<details>
  <summary>Encryption not requested</summary>

<br/>

```text
An error occurred (AccessDenied) when calling the PutObject operation:
User: arn:aws:sts::112233445566:assumed-role/AWSReservedSSO_PermSetName_0123456789abcdef/abcde
is not authorized to perform: s3:PutObject
on resource: "arn:aws:s3:::test-kms-encryption-required/non-encrypted.txt"
with an explicit deny in a resource control policy
```

</details>

<details>
  <summary>Insufficient KMS key usage permissions</summary>

<br/>

```text
An error occurred (AccessDenied) when calling the PutObject operation:
User: arn:aws:sts::112233445566:assumed-role/AWSReservedSSO_PermSetName_0123456789abcdef/abcde
is not authorized to perform: kms:GenerateDataKey
on this resource
because no identity-based policy allows the kms:GenerateDataKey action"
```

</details>

<details>
  <summary>Non-existent KMS key</summary>

<br/>

```text
An error occurred (KMS.NotFoundException) when calling the PutObject operation:
Key 'arn:aws:kms:us-east-1:112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd'
does not exist
```

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

 1. Authenticate in your AWS&nbsp;Organizations management account. Choose a
    role with administrative privileges. Choose the region where you manage
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

## Test

### Test Manually

<details>
  <summary>Manual test commands...</summary>

 1. Authenticate in your test AWS account or an account in your test
    organizational unit. (RCPs do not affect resources in your
    AWS&nbsp;Organizations management account.) Choose a role with full S3
    permissions.

    - I recommend using
      [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home).
      The AWS CLI is pre-installed and there is no need to obtain credentials
      on a local computer.

 2. Populate a test file, confirm the name of a new S3 bucket, and store the
    bucket name.

    ```shell
    cd /tmp
    echo 'Test data' > test.txt

    TIMESTAMP=$( date --utc '+%s' )  # Seconds since start of 1970
    AWS_ACCT=$( aws sts get-caller-identity --query 'Account' --output text )
    read -p 'S3 bucket     : ' \
      -e -i "deletable-acct-${AWS_ACCT}-ts-${TIMESTAMP}" -r S3_BUCKET_NAME

    ```

 3. Create the bucket.

    ```shell
    aws s3 mb "s3://${S3_BUCKET_NAME}"

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
      --account-id "${AWS_ACCT}" --resource-arn "arn:aws:s3:::${S3_BUCKET_NAME}" \
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

10. Delete the bucket.

    ```shell
    aws s3 rb "s3://${S3_BUCKET_NAME}" --force
    ```

    Continue with
    [Step 5 of the _installation_ instructions](#install-step-5-context).

</details>

### Test with Lambda Functions

<details>
  <summary>Instructions for automated testing...</summary>

 1. Authenticate to the AWS Console in your test AWS account or an account in
    your test organizational unit. (RCPs do not affect resources in your
    AWS&nbsp;Organizations management account.) If you use the optional SCP to
    restrict tagging permissions, make sure that this AWS account number is not
    subject to the SCP. Choose a role with full S3 permissions.

 2. [Create a CloudFormation stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create)
    from
    [test/aws-rcp-s3-require-encryption-kms.yaml](/../../blob/main/test/test-aws-rcp-s3-require-encryption-kms.yaml?raw=true)&nbsp;.

    - Copy and paste the suggested stack name.
    - Fill in the KMS key ARN. If you have used KMS with S3 before, you could
      view the AWS-managed
      [`aws/s3`](https://console.aws.amazon.com/kms/home#/kms/defaultKeys)
      key and copy its ARN. (KMS key aliases won't work in bucket tag values,
      because they don't work in policies.)
    - Because this is for temporary use during testing, I do not provide a
      Terraform alternative.
    - Trouble creating the stack usually signals a local permissions problem,
      such as insufficient permissions attached to your IAM role, or the effect
      of a hidden policy such as a permissions boundary or a service control
      policy. If you cannot resolve the problem, check with your AWS
      administrator.

 3. Open the
    [TestDirector](https://console.aws.amazon.com/lambda/home#/functions/TestRcpS3RequireEncryptionKmsTestDirector?tab=testing)
    Lambda function's "Test" tab and click "Test". The contents of the test
    event are ignored.

 4. Open the "All events" search page for the
    [Test](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestRcpS3RequireEncryptionKms/log-events$3FfilterPattern$3Derror)
    CloudWatch log group, and filter for the search term `error`&nbsp;. Review
    any errors.

    - Uncaught exceptions are unexpected, and usually signal local permission
      problems.

 5. Go up to the
    [Test](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/TestRcpS3RequireEncryptionKms)
    log group's main page. Open the log streams and unfold the entries to read
    the test results.

    - The tests are based on a set of 10 (same-account KMS key) or 8 (KMS key
      in a different account) numbered S3 buckets with different combinations
      of ABAC, bucket tags, and KMS key identifiers. A decimal number indicates
      a sub-test.

 6. If you wish to re-test, check the top-most checkbox to select all of the
    log streams, then click "Delete. Return to Lambda Test Step&nbsp;3.

 7. When you are finished, delete the CloudFormation stack.

    - If there was an unexpected error, you might have to empty S3 buckets
      before you can delete the stack.

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
