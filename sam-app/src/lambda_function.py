import json
import re

import boto3

S3_CLIENT = boto3.client("s3")
CONTENTS_BUCKET_NAME = "ce-contents-rap-distribution-373045849756"


def get_matching_s3_objects(s3_client, bucket_name, prefix, suffix):
    paginator = s3_client.get_paginator("list_objects")

    kwargs = {"Bucket": bucket_name, "Prefix": prefix}

    for page in paginator.paginate(**kwargs):
        try:
            contents = page["Contents"]
        except KeyError:
            return

        for obj in contents:
            key = obj["Key"]
            if key.endswith(suffix):
                yield obj


def get_listing(s3_client, bucket_name, prefix, suffix):
    items = [obj["Key"] for obj in get_matching_s3_objects(s3_client, bucket_name, prefix, suffix)]
    items.sort(reverse=True,
               key=lambda a: float(
                   re.search('[0-9a-f]+@([0-9]+(.[0-9]+)?)', a).group(1)))

    return items


def lambda_handler(event, context):
    """Handler for content requests

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    request = event["Records"][0]["cf"]["request"]
    uri = request["uri"]

    request["uri"] = "/".join(uri.split("/", 3)[0:3])

    if uri.startswith("/contents/"):
        return {
            "status": 301,
            "statusDescription": "Found",
            "headers": {
                "location": [{
                    "key": "Location",
                    "value": uri.replace("/contents/", ":" in uri and "/baked/" or "/raw/"),
                }]
            }
        }

    raw = uri.startswith("/raw/")
    baked = uri.startswith("/baked/")

    # redirect to latest version
    if (raw and uri.count('@') < 1
            or baked and ':' in uri and uri.count('@') < 2
            or baked and ':' not in uri and uri.count('@') < 1):
        try:
            path, format_ = request["uri"].rsplit(".", 1)
            path = path[1:]
        except ValueError:
            return {
                "status": "404",
                "statusDescription": "Not Found",
            }

        listing = None
        if baked and ":" in uri:
            book, page = path.split(":", 1)
            if "@" not in book:
                listing = get_listing(S3_CLIENT, CONTENTS_BUCKET_NAME, book, f".{format_}")
        if listing is None:
            listing = get_listing(S3_CLIENT, CONTENTS_BUCKET_NAME, path, f".{format_}")
        if not listing:
            return {
                "status": "404",
                "statusDescription": "Not Found"
            }
        return {
            "status": "301",
            "statusDescription": "Found",
            "headers": {
                "location": [{
                    "key": "Location",
                    "value": f"/{listing[0]}",
                }]
            }
        }

    return request
