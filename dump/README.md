# Dump books into a bucket

This is a script to dump the contents of the following books of interest into a specified S3 bucket.

## Books of interest

1. Elementary Algebra (col12116) - 0889907c-f0ef-496a-bcb8-2a5bb121717f@8.42
1. Intermediate Algebra (col12119) - 02776133-d49d-49cb-bfaa-67c7f61b25a1@8.13
1. Prealgebra (col11756) - caa57dab-41c7-455e-bd6f-f443cda5519c@19.5

## Installation

```sh
pip install -r requirements.txt
```

See [boto3 quick start](https://github.com/boto/boto3#quick-start) for boto3 aws credentials configuration.

## Usage

```sh
export YOUR_BUCKET=ce-rap-$USER
./dump-to-bucket.py \
  -v \
  -b 0889907c-f0ef-496a-bcb8-2a5bb121717f@8.42 \
  -b 02776133-d49d-49cb-bfaa-67c7f61b25a1 \
  -b caa57dab-41c7-455e-bd6f-f443cda5519c@19.5 \
  -h archive-staging.cnx.org \
  $YOUR_BUCKET
```

## S3 bucket data structures

For raw content:

- `raw/{uuid}@{version}.json`
- `raw/{uuid}@{version}.html`

For baked content

- `baked/{uuid}@{version}.json`
- `baked/{uuid}@{version}.html`
- `baked/{uuid}@{version}:{uuid}.json`
- `baked/{uuid}@{version}:{uuid}.html`

For resources:

- `resources/{sha1}`
