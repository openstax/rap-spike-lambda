# Just do

This is an application to display the contents of openstax

## 3 Books of interest

1. Elementary Algebra (col12116) - 0889907c-f0ef-496a-bcb8-2a5bb121717f@8.42
1. Intermediate Algebra (col12119) - 02776133-d49d-49cb-bfaa-67c7f61b25a1@8.13
1. Prealgebra (col11756) - caa57dab-41c7-455e-bd6f-f443cda5519c@19.5

## Installation and usage

```sh
pip install -r requirements.txt
```

### Initialize the data source

```sh
export YOUR_BUCKET=ce-rap-$USER
./dump-to-bucket.py \
  -v \
  -b 0889907c-f0ef-496a-bcb8-2a5bb121717f@8.42 \
  -b 02776133-d49d-49cb-bfaa-67c7f61b25a1 \
  -b caa57dab-41c7-455e-bd6f-f443cda5519c@19.5 \
  $YOUR_BUCKET
```

## S3 bucket data structures

- `/raw/{uuid}@{version}.json`
- `/raw/{uuid}@{version}.html`

For baked content

- `/baked/{uuid}@{version}.json`
- `/baked/{uuid}@{version}.html`
- `/baked/{uuid}@{version}:{uuid}.json`
- `/baked/{uuid}@{version}:{uuid}.html`

For resources:

- `/resources/{sha1}`

## Semi-repeatable instructions

### Create an S3 bucket

Create an S3 bucket through the web console. Name it something like `ce-rap-{name}-web`. Be sure to enable public access on the bucket. Also set the tags to something similar to those in: https://openstax.slack.com/files/U0F988KSQ/FN89FMUGN/screen_shot_2019-09-09_at_12.51.39.png

Make sure you select the us-east-2 region.

### Create a CloudFront distribution

1. Services -> (search) 'cloudfront' -> (click) CloudFront
1. (click) Create Distribution -> under 'Web' click Get Started
1. Fill in the 'Origin Domain Name' value, which is your S3 bucket (i.e. `ce-rap-{name}-web.s3.amazonaws.com`) -> scroll to the bottom and click 'Create Distribution' button

### Creating a Lambda function

TODO

### Hooking up the Lambda functions to CloudFront

TODO
