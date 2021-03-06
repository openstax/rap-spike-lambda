# rap-spike-lambda

## Table of Contents
* [A3 Planning](#a3-planning)
  * [Background](#background-plan)
  * [Current Condition](#current-condition-plan)
  * [Goal / Target Condition](#goal--target-condition-plan)
  * [Root Cause Analysis](#root-cause-analysis-plan)
  * [Epics and Task Cards](#epics-stories-and-task-cards-do)
  * [Confirmation](#confirmation-check)
  * [Follow up](#follow-up-act)
* [Using Cloudformation](#using-cloudformation)
  * [Articles that are useful](#articles-that-are-useful)
  * [Create the rap-distribution stack](#create-the-rap-distribution-stack-in-aws)
  * [Update the stack after changes](#update-the-rap-distribution-after-changes)
* [Loading the books into S3](#loading-the-books-into-s3)
* [Using SAM to build and test the Lambda@Edge function]()

## A3 Planning

A3 planning is a technique created by Toyota and Lean manufacturing. The idea
is to focus on a problem and convey all the information necessary in an A3 
size of paper (11.69 x 16.53 inches). However,  it's not the size of the paper 
that is important but rather the approach to solving the problem and
conveying the right information to the people that need it.

### Background (PLAN)

This spike is an experiment in itself to test the viability of using AWS Lambda
functions (possibly Lambda@edge) to serve content from S3 to help eventually allow
us to retire Legacy. 
 
### Current condition (PLAN)

In the current system, [cnx-archive][cnx-archive] acts as a typical backend
web application. It exposes a web API that consumers use to get content for various books.
The web application queries the database ([cnx-db][cnx-db]) based on the request and returns
the appropriate response.

[![image](https://user-images.githubusercontent.com/8730430/64211160-e841ea80-ce6a-11e9-9452-8c03ad7a0ff3.png)](https://docs.google.com/document/d/1GW5VGrjKmIRw3nbFTIkBZgE0mlHD9ky2TJ_bSUIcJ_w/edit)

### Goal / Target Condition (PLAN)

1. There is an endpoint at archive.openstax.org (cloudfront) that returns content via lambda and s3.
2. We’ve got a book in s3 in the correct directory structure
3. We have the lambda function that can serve the book
4. ?
5. PROFIT


[![image](https://user-images.githubusercontent.com/8730430/64211419-ba10da80-ce6b-11e9-9537-f683f97b13ed.png)](https://docs.google.com/document/d/1GW5VGrjKmIRw3nbFTIkBZgE0mlHD9ky2TJ_bSUIcJ_w/edit)

### Root Cause Analysis (PLAN)

Root cause analysis done at length within the [Archive vision 2 pager][rap-two-pager].

In summary, there are complications due to archive supplying content in various states ie. raw, baked, unbaked, etc.
The various states of the content rely on transformations that are done via database triggers. If we 
can extract the content to s3 via events from a database (see [rap-spike-concourse][rap-spike-concourse]) we can then serve the content as static files
or any other method we dream of.

Once published content is able to be served and is no longer in the database we can start to
remove the database triggers from the database and use them in a more maintainable fashion.

### Epics, Stories, and Task Cards (DO)

* Determine how to do individual (or group) development of AWS
* [Determine the s3 data structure in order to be served as a book.](https://app.zenhub.com/workspace/o/openstax/cnx/issues/655)
* [Develop a wsgi app utilizing zappa and AWS Lambda that serves content from s3](https://app.zenhub.com/workspaces/content-engineering-tech-team-5af1f4cc12da5e6d74331b60/issues/openstax/cnx/657)

 
### Confirmation (CHECK)

Given: a url w/ the full ident_hash  
Then: content to be served directly from s3 / cloudfront  

Given: a url w/ a missing book version  
Then: the lambda function to determine the content to be served by redirecting to s3 (the full ident hash) and getting the latest version  

Given: 400,000 IDs in one S3 directory (40 books * 200 pages per book * 50 versions)  
Then: S3 will not explode  

Given: a url of format archive.openstax.org/contents/<book_uuid>@<version>:<page_uuid>  
Then: return the proper json  

### Follow up (ACT)

## Using Cloudformation

### Articles that are useful

- [AWS CloudFormation Documentation][aws-cloudformation]
- [Managing Lambda@Edge and CloudFront deployments by using a CI/CD pipeline][aws-cf-lambda-ci]
- [Amazon S3 + Amazon CloudFront: A Match Made in the Cloud][aws-cf-s3]
- [Chalice CloudFormation Support][aws-chalice-support]
- [Chalice Pure Lambda Functions][aws-chalice-pure-lambda]
- [AWS Serverless Application Model][aws-sam]

### Create the rap-distribution stack in AWS


To create the stack run the following using the `aws` cli:

    aws cloudformation deploy --template-file cf-templates/cloudfront-single-origin-bucket.yaml --region us-east-1 --stack-name rap-distribution --tags Project=rap-spike-lambda Application=rap-spike-lambda Environment=dev Owner=Mike

Note: This step only needs to be run the first time to create the stack. If you need to make updates please follow the
instructions in [Update the rap-distribution after changes](#update-the-rap-distribution-after-changes).

Note: This command will take about 15-25min to complete. It will create the following resources in AWS:

- Cloudfront distribution
- [Lambda Function](./request-handler/lambda_function.py)
- Artifact S3 Bucket
- Raw JSON S3 Bucket
- Baked HTML S3 Bucket
- Resources S3 Bucket

### Update the rap-distribution after changes

The `aws cloudformation` command can package up the changes and upload to an s3 bucket.
It allows you to do this by using the `package` argument along with `--s3-bucket` and `--output-template-file` options.

This will package up the lambda function, upload to the s3 bucket, and generate a new template that has
the s3 bucket substituted in the proper locations of the template.

To update the rap-distribution stack after a merge run the following: 

    aws cloudformation package --template-file ./cf-templates/cloudfront-single-origin-bucket.yaml \
    --s3-bucket ce-artifacts-rap-distribution-373045849756 --output-template-file ./cf-templates/app-output-sam.yaml

This will output a SAM compiled version of the template that can be used to update the stack.

Run the following command after the one above to update the stack:

    aws cloudformation update-stack --stack-name rap-distribution \
    --region us-east-1 --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM \
    --template-body file://./cf-templates/app-output-sam.yaml

## Loading the books into s3

Follow the instructions in [./dump/README.md](./dump/README.md) file.

## Using SAM to build and test the Lambda@Edge function

Follow the instruction in [.sam-app/README.md](./sam-app/README.md) file.

[cnx-archive]: https://github.com/openstax/cnx-archive
[cnx-db]: https://github.com/openstax/cnx-db
[rap-spike-concourse]: https://github.com/openstax/rap-spike-concourse
[rap-two-pager]: https://docs.google.com/document/d/1GW5VGrjKmIRw3nbFTIkBZgE0mlHD9ky2TJ_bSUIcJ_w/edit#heading=h.6u0c02buvzha
[aws-cloudformation]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html
[aws-chalice-support]: https://chalice.readthedocs.io/en/latest/topics/cfn.html
[aws-chalice-pure-lambda]: https://chalice.readthedocs.io/en/latest/topics/purelambda.html
[aws-sam]: https://aws.amazon.com/serverless/sam/
[aws-cf-lambda-ci]: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-options.html
[aws-cf-s3]: https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-s3-amazon-cloudfront-a-match-made-in-the-cloud/
