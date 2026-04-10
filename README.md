# Different S3 Buckets, Different KMS Encryption Keys

Do you maintain a separate bucket policy for every encrypted S3 bucket, or a
separate resource control policy for every KMS key used with S3?

&#128161; I've devised **a practical way to enforce KMS encryption**...in one
bucket or thousands...in one region or many...in one account or many...with one
key or many...just tag S3 buckets with KMS key ARNs!

>&#128274; Software supply chain security is on everyone's mind. This solution
does not require executable code or dependencies. It creates a resource control
policy, which you can read before attaching anywhere. I've also made GitHub
releases immutable.

## How to Use It

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
