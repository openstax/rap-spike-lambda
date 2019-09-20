import os
import re
import xml.etree.ElementTree as ET
from urllib.request import urlopen

BAKED_BUCKET = os.environ["S3_BAKED_BUCKET"]
RAW_BUCKET = os.environ["S3_RAW_BUCKET"]
RESOURCES_BUCKET = os.environ["S3_RESOURCES_BUCKET"]


def get_listing(prefix, suffix, bucket=None):
    url = f'https://{bucket}.s3.amazonaws.com/?list-type=2&prefix={prefix}'
    ns = 'http://s3.amazonaws.com/doc/2006-03-01/'
    root = ET.fromstring(urlopen(url).read())
    listing = [a.text for a in root.findall(f'./{{{ns}}}Contents/{{{ns}}}Key')
               if a.text.endswith(suffix)]
    # sort by version
    listing.sort(reverse=True,
                 key=lambda a: float(
                     re.search('[0-9a-f]+@([0-9]+(.[0-9]+)?)', a).group(1)))
    return listing


def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    uri = request['uri']

    # strip out resource / contents filenames
    request['uri'] = '/'.join(uri.split('/', 3)[0:3])

    if uri.startswith('/contents/'):
        return {
            'status': 301,
            'statusDescription': 'Found',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': uri.replace('/contents/', ':' in uri and '/baked/' or '/raw/'),
                }]
            }
        }

    raw = uri.startswith('/raw/')
    baked = uri.startswith('/baked/')
    # redirect to latest version
    if raw and uri.count('@') < 1 or \
            baked and ':' in uri and uri.count('@') < 2 or \
            baked and ':' not in uri and uri.count('@') < 1:
        try:
            path, format_ = request['uri'].rsplit('.', 1)
            path = path[1:]  # remove leading slash
        except ValueError:
            return {
                'status': '404',
                'statusDescription': 'Not Found',
            }
        listing = None
        if baked and ':' in uri:
            book, page = path.split(':', 1)
            if '@' not in book:
                listing = [a for a in get_listing(book, f'.{format_}', bucket=BAKED_BUCKET) if
                           page in a]
        if listing is None:
            listing = get_listing(path, f'.{format_}')
        if not listing:
            return {
                'status': '404',
                'statusDescription': 'Not Found',
            }
        return {
            'status': '301',
            'statusDescription': 'Found',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': f'/{listing[0]}',
                }],
            }
        }

    return request
