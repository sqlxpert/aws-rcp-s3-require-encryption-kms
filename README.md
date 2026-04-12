# Different S3 Buckets, Different KMS Encryption Keys

Do you maintain a separate bucket policy for every encrypted S3 bucket?

&#128161; I've devised **an easier way to enforce KMS encryption**...in one
bucket or thousands...in one region or many...in one account or many...with one
key or many...just tag S3 buckets with KMS key ARNs!

>&#128274; Software supply chain security is on everyone's mind. This solution
does not require executable code or dependencies. It creates a resource control
policy, which you can read before attaching anywhere. I've also made GitHub
releases immutable.

## How to Use It

### Bucket Tag Key

`security-s3-require-encryption-kms-key-arn` **&larr; Tag a new S3 bucket to
require KMS encryption** for all new objects.

&check;
[Attribute-based access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/buckets-tagging-enable-abac.html)
must be enabled for the bucket.

### Bucket Tag Value

Set the tag to the **ARN of a KMS encryption key &rarr;**
`arn:aws:kms:us-east-1:112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`
(sample).

<details>
  <summary>Different ways to designate the bucket's required KMS key</summary>

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
if set, must reference the same KMS key as the bucket tag, and must specify
`aws:kms` encryption. (~`aws:kms:dsse`~
[dual-layer encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingDSSEncryption.html)
is not allowed. New objects share one consistent encryption type.)

### KMS Key Usage Permissions

&check; Users' permissions and/or the KMS key policy must allow
[usage of the KMS key to encrypt S3 objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html#:~:text=Permissions).

### Creating Encrypted Objects

Depending on the S3 bucket's default encryption configuration, users may have
to specify the KMS key, and/or `aws:kms` encryption, when creating objects.

<details>
  <summary>Specifying encryption details</summary>

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

|Reference|Sample Input Value &#8675;|
|:---|:---|
|KMS&nbsp;Key&nbsp;Full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:key/0123abcd-45ef-67ab-89cd-012345efabcd`|
|KMS&nbsp;Key&nbsp;ID|`0123abcd-45ef-67ab-89cd-012345efabcd`|
||`mrk-01ab23cd45ef67ab89cd01ef23ab45cd`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;Full&nbsp;ARN|`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/alias_for_my_customer_managed_kms_key`|
||`arn:aws:kms:us-east-1:`<br/>`112233445566:alias/aws/s3`|
|KMS&nbsp;Key&nbsp;Alias&nbsp;Name|`alias/aws/s3`|
||`alias/alias_for_my_customer_managed_kms_key`|

&check; The KMS key must be in the same region as the S3 bucket.

&check; The requester, the KMS key, and the S3 bucket must all be in the same
AWS account, unless the KMS key's account number is specified in the S3
PutObject request or in the S3 bucket's default encryption configuration.

&cross; ~`aws:kms:dsse`~ dual-layer encryption is not allowed.

</details>

### Error Messages

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

## Testing

### Bug Reporting

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
