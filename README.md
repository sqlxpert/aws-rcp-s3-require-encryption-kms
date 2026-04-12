# Different Buckets, Different Encryption Keys

Do you maintain a separate bucket policy for every encrypted S3 bucket?

&#128161; I've devised **an easier way to enforce encryption**...in one
bucket or thousands...in one region or many...in one account or many...with one
key or many... Simply tag each S3 bucket with a KMS key!

>&#128274; Software supply chain security is on everyone's mind. This solution
does not require executable code or dependencies. It creates a resource control
policy, which you can read before attaching. I've made GitHub releases
immutable. In case you do not want to install the AWS command-line interface
locally, or execute a shell script, I also explain how to test by hand in AWS
CloudShell.

## How to Use It

### Tag Bucket

Tag a new S3 bucket with the ARN of a KMS key, to require KMS encryption for
all new objects:

|Tag&nbsp;Key|`security-s3-require-encryption-kms-key-arn`|
|---:|:---|
|Tag&nbsp;Value (Sample)|`arn:aws:kms:us-east-1:112233445566:`<br/>`key/0123abcd-45ef-67ab-89cd-012345efabcd`|

#### Check Rules

&check;
[Attribute-based access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/buckets-tagging-enable-abac.html)
must be enabled for the bucket.

<details>
  <summary>Different ways to designate the bucket's KMS key...</summary>

<br/>

|Reference|Bucket Tag Value (Sample)|
|:---|:---|
|KMS&nbsp;Key&nbsp;Full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;Key&nbsp;Partial&nbsp;ARN|`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`112233445566:key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;Key&nbsp;ID|`key/0123abcd-45ef-67ab-89cd-012345efabcd`|
||`key/mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|

I recommend creating every key as an `mrk-`
[multi-region KMS key](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html).
Use the key policy to lock the
[primary region](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-auth.html#mrk-auth-update).
Limit
[replica regions](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-auth.html#mrk-auth-replicate)
until you need replica keys in other regions.

&check; The KMS key must be in the same AWS account as the S3 bucket, unless
the account number is specified in the bucket tag value.

</details>

&check; The KMS key must be in the same region as the S3 bucket.

&check; The S3 bucket's
[default encryption configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html#:~:text=Changes,before%20enabling%20default%20encryption),
if set, must reference the same KMS key and specify `aws:kms` encryption. (For
consistency, no ~`aws:kms:dsse`~
[dual-layer encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingDSSEncryption.html)!)

&check; Users' permissions and/or the KMS key policy must allow
[usage of the KMS key](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html#:~:text=Permissions).

### Create Encrypted Objects

Depending on the S3 bucket's default encryption configuration, users may have
to specify the KMS key, and/or `aws:kms` encryption, when creating objects.

<details>
  <summary>Specifying encryption details...</summary>

<br/>

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

|Reference|Sample Input Value &#8675;|
|:---|:---|
|KMS&nbsp;Key&nbsp;Full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
|KMS&nbsp;Key&nbsp;ID|`0123abcd-45ef-67ab-89cd-012345efabcd`|
||`mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;Full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/alias_for_my_customer_managed_kms_key`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/aws/s3`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;Name|`alias/aws/s3`|
||`alias/alias_for_my_customer_managed_kms_key`|

<br/>

&check; The KMS key must be in the same region as the S3 bucket.

&check; The requester, the KMS key, and the S3 bucket must all be in the same
AWS account, unless the KMS key's account number is specified in the S3
PutObject request or in the S3 bucket's default encryption configuration.

</details>

### Resolve Errors

#### Non-Encrypted Object

Users who try to create non-encrypted S3 objects get an "AccessDenied" error.
In case a user misses the "require-encryption-kms-key-arn"... in the bucket tag
key, or doesn't check the tag's value to find out the correct key to use, the
error message tells an administrator where to look for guidance: "explicit deny
in a resource control policy".

<details>
  <summary>Full error message</summary>

<br/>

```text
An error occurred (AccessDenied) when calling the PutObject operation:
User: arn:aws:sts::112233445566:assumed-role/AWSReservedSSO_PermSetName_0123456789abcdef/abcde
is not authorized to perform: s3:PutObject
on resource: "arn:aws:s3:::test-kms-encryption-only/non-encrypted.txt"
with an explicit deny in a resource control policy
```

</details>

#### Insufficient Key Usage Permissions

#### Non-Existent Key

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

 7. Tag the bucket.

    ```shell
    aws s3api put-bucket-tagging --bucket "${S3_BUCKET_NAME}" \
      --tagging "TagSet=[{Key=${S3_BUCKET_TAG_KEY},Value=${KMS_KEY_ID}}]"

    ```

    &#9888; Tag the bucket _before_ enabling ABAC. The AWS CLI does not yet
    support the new AWS API methods for tagging ABAC-enabled S3 buckets.

 8. Enable ABAC for the bucket.

    ```shell
    aws s3api put-bucket-abac --bucket "${S3_BUCKET_NAME}" \
      --abac-status 'Status=Enabled'

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

### Test with a Script

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
