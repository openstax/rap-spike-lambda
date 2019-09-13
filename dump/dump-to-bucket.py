#!/usr/bin/env python3
"""\
This dumps a book into an S3 bucket using the following S3 filesystem structure:

- ``/raw/{uuid}@{version}.json``
- ``/raw/{uuid}@{version}.html``

For baked content

- ``/baked/{uuid}@{version}.json``
- ``/baked/{uuid}@{version}.html``
- ``/baked/{uuid}@{version}:{uuid}.json``
- ``/baked/{uuid}@{version}:{uuid}.html``

For resources:

- ``/resources/{sha1}``


Note, this is only intended to be used with a book, not individual pages.

"""
import io
import sys

import boto3
import click
import cnxcommon
import requests
from blessings import Terminal
from cnxcommon.ident_hash import join_ident_hash, split_ident_hash


VERBOSE = False
T = Terminal()

s3 = boto3.resource('s3')


session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=5)
session.mount('https://', adapter)


def info(msg):
    print(msg, file=sys.stderr)


def debug(msg):
    if VERBOSE: print(msg, file=sys.stderr)


def gen_filepath(type_, ident):
    """Given a content type and an ids structure
    produce the S3 filepath to the object.

    For json and html the ``ident`` sequence of one or more tuples of UUID and version.
    For a resource the ``ident`` is the SHA1.

    """
    if not type_.startswith('resource'):
        ids = [join_ident_hash(*i) for i in ident]
    else:
        ids = ident

    func = {
        'raw-book-json': lambda i: f'raw/{i[-1]}.json',
        'raw-book-html': lambda i: f'raw/{i[-1]}.html',
        'raw-page-json': lambda i: f'raw/{i[-1]}.json',
        'raw-page-html': lambda i: f'raw/{i[-1]}.html',
        'baked-book-json': lambda i: f'baked/{i[0]}.json',
        'baked-book-html': lambda i: f'baked/{i[0]}.html',
        'baked-page-json': lambda i: f'baked/{i[0]}:{i[1]}.json',
        'baked-page-html': lambda i: f'baked/{i[0]}:{i[1]}.html',
        'resource': lambda i: f'resources/{i}',
        'resource-media-type': lambda i: f'resources/{i}-media-type',
    }[type_]
    return func(ids)

# Some sanity tests...
assert gen_filepath('raw-book-json', [('abc123', '1.1')]) == 'raw/abc123@1.1.json'
assert gen_filepath('raw-book-html', [('abc123', '1.1')]) == 'raw/abc123@1.1.html'
assert gen_filepath('raw-page-json', [('abc123', '1.1')]) == 'raw/abc123@1.1.json'
assert gen_filepath('raw-page-html', [('abc123', '1.1')]) == 'raw/abc123@1.1.html'
assert gen_filepath('raw-page-json', [('abc123', '1.1'), ('def456', '9')]) == 'raw/def456@9.json'
assert gen_filepath('raw-page-html', [('abc123', '1.1'), ('def456', '9')]) == 'raw/def456@9.html'
assert gen_filepath('baked-book-json', [('abc123', '1.1')]) == 'baked/abc123@1.1.json'
assert gen_filepath('baked-book-html', [('abc123', '1.1')]) == 'baked/abc123@1.1.html'
assert gen_filepath('baked-page-json', [('abc123', '1.1'), ('def456', None)]) == 'baked/abc123@1.1:def456.json'
assert gen_filepath('baked-page-html', [('abc123', '1.1'), ('def456', None)]) == 'baked/abc123@1.1:def456.html'
assert gen_filepath('resource', 'deadbeef') == 'resources/deadbeef'
assert gen_filepath('resource-media-type', 'deadbeef') == 'resources/deadbeef-media-type'


VISITED_LOCS_MARKER = object()


def scrape(book, host, visited_locs=VISITED_LOCS_MARKER):
    """Scrape the given book (ident-hash) from the archive.cnx.org site.
    This scrapes the JSON, HTML and resources for all versions of the content.
    """
    # ``visited_locs`` is a shared list of visited locations,
    # primarily so we don't re-visit resources.
    if visited_locs is VISITED_LOCS_MARKER:
        visited_locs = []

    try:
        id, version = split_ident_hash(book)
    except cnxcommon.ident_hash.IdentHashMissingVersion:
        id = book
    base_url = f'https://{host}/contents'

    # Request the latest version
    url = f'{base_url}/{id}.json'
    resp = session.get(url)
    version = resp.json()['version']

    info(f'latest version of requested book: {T.bold}{id}@{version}{T.normal}')

    # Get the latest version's contents and resources
    # With this we'll have access to the list of past versions
    for item in scrape_version(id, version, host, visited_locs):
        data, media_type, type, id = item
        if type == 'raw-book-json':
            # TODO: Make note of the historical versions for later scraping
            historical = []
        yield item

    # TODO: Yield this latest version before progressing to yielding subversions

    # TODO: Yield the historical versions of this book


def flatten_tree_to_ident_hashes(item_or_tree):
    """Flatten a tree's leaves a list of id and version values (ident_hash)"""
    if 'contents' in item_or_tree:
        # FYI This ignores the sub-collection identifiers
        tree = item_or_tree
        for i in tree['contents']:
            yield from flatten_tree_to_ident_hashes(i)
    else:
        item = item_or_tree
        yield item['id']


test_tree = {
    "id": "02776133-d49d-49cb-bfaa-67c7f61b25a1@9.1",
    "contents": [
        {"id": "301d5176-9ace-4219-b44b-85dcf781e1e3@21"},
        {"id": "82ebb7ed-e34f-45a3-a6b0-2b3e7e941c05@9.1",
         "contents": [
             {"id": "1c2686fd-6e5c-417e-8340-38c9eb5e1019@16"},
         ]},
        {"id": "eb680355-ba88-4967-8828-64438b9979b4@9.1",
         "contents": [
             {"id": "0fee78e2-7da7-4f15-8627-4b6ceb783c07@16"},
             {"id": "398667a8-7a81-514d-84cc-05a3dbf5ccd8@9"},
             {"id": "468c7b18-daa6-45da-8276-2eec12400376@9.1",
              "contents": [
                  {"id": "5e0a18b4-90cd-4b10-9067-034b8bd140f4@16"},
              ]},
         ]},
        {"id": "a934a123-39ea-4099-96bc-1b6c8deb55fe@21"},
    ],
}
test_tree_idents = [
    '301d5176-9ace-4219-b44b-85dcf781e1e3@21',
    '1c2686fd-6e5c-417e-8340-38c9eb5e1019@16',
    '0fee78e2-7da7-4f15-8627-4b6ceb783c07@16',
    '398667a8-7a81-514d-84cc-05a3dbf5ccd8@9',
    '5e0a18b4-90cd-4b10-9067-034b8bd140f4@16',
    'a934a123-39ea-4099-96bc-1b6c8deb55fe@21',
]
assert list(flatten_tree_to_ident_hashes(test_tree)) == test_tree_idents


def scrape_version(id, version, host, visited_locs, book=None):
    """
    """
    if book is None:
        is_book = True
        type_ = 'book'
        raw_ident_hash = ident_hash = join_ident_hash(id, version)
        ident_hash_seq = [(id, version)]
    else:
        is_book = False
        type_ = 'page'
        raw_ident_hash = join_ident_hash(id, version)
        ident_hash = ':'.join([join_ident_hash(*book), join_ident_hash(id, None)])
        ident_hash_seq = [book, (id, version,)]

    base_url = f'https://{host}/contents'
    base_raw_url = f'{base_url}/{raw_ident_hash}'
    base_baked_url = f'{base_url}/{ident_hash}'
    raw_postfix = '?as_collated=0'

    # Request the RAW JSON
    temperature = 'raw'
    format_ = 'json'
    url = f'{base_raw_url}.{format_}{raw_postfix}'
    debug(f'Requesting {temperature} JSON {T.bold}{type_}{T.normal} at {T.yellow}{url}{T.normal}')
    resp = session.get(url)
    yield io.BytesIO(resp.content), 'application/json', f'{temperature}-{type_}-json', [ident_hash_seq[-1]]

    # Save the raw json for later
    raw_json = resp.json()

    # Request the BAKED JSON
    temperature = 'baked'
    format_ = 'json'
    url = f'{base_baked_url}.{format_}'
    debug(f'Requesting {temperature} JSON {T.bold}{type_}{T.normal} at {T.yellow}{url}{T.normal}')
    resp = session.get(url)
    yield io.BytesIO(resp.content), 'application/json', f'{temperature}-{type_}-json', ident_hash_seq

    # Save the baked json for later
    baked_json = resp.json()

    # Request the RAW HTML
    temperature = 'raw'
    format_ = 'html'
    url = f'{base_raw_url}.{format_}{raw_postfix}'
    debug(f'Requesting {temperature} HTML {T.bold}{type_}{T.normal} at {T.yellow}{url}{T.normal}')
    resp = session.get(url)
    yield io.BytesIO(resp.content), 'text/html', f'{temperature}-{type_}-html', [ident_hash_seq[-1]]

    # Request the BAKED HTML
    temperature = 'baked'
    format_ = 'html'
    url = f'{base_baked_url}.html'
    debug(f'Requesting {temperature} HTML {T.bold}{type_}{T.normal} at {T.yellow}{url}{T.normal}')
    resp = session.get(url)
    yield io.BytesIO(resp.content), 'text/html', f'{temperature}-{type_}-html', ident_hash_seq

    # Request the resources...
    for res_entity in raw_json['resources']:
        # Request the resource itself
        url = f'https://{host}/resources/{res_entity["id"]}'
        debug(f'Requesting {T.bold}resource{T.normal} at {T.yellow}{url}{T.normal}')
        resp = session.get(url)
        yield io.BytesIO(resp.content), str(res_entity['media_type']), 'resource', res_entity['id']

    if is_book:
        # Request the individual raw pages
        for page_ident_hash in flatten_tree_to_ident_hashes(raw_json['tree']):
            page_id, page_version = split_ident_hash(page_ident_hash)
            yield from scrape_version(page_id, page_version, host, visited_locs, book=(id, version,))


def dump_in_bucket(items, bucket_info):
    bucket_name, region_name = bucket_info
    s3 = boto3.resource('s3', region_name=region_name)
    bucket = s3.Bucket(bucket_name)

    for item in items:
        data, media_type, type, ident = item
        key = gen_filepath(type, ident)
        debug(f'Dumping {T.blue}{type}{T.normal} into the bucket at "{T.green_bold}{key}{T.normal}" ({media_type})')
        bucket.upload_fileobj(data, key, ExtraArgs={'ContentType': media_type})


@click.command()
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
@click.option('-b', '--book', multiple=True)
@click.option('-h', '--host', default='archive.cnx.org', help='archive hostname')
@click.argument('bucket')
@click.argument('region', default='us-west-2')
def main(verbose, book, host, bucket, region):
    global VERBOSE
    VERBOSE = verbose
    books = book
    if not books:
        raise click.UsageError(
            "At least one book must be supplied\n"
            "See the --book option"
        )

    for book in books:
        dump_in_bucket(scrape(book, host), (bucket, region))


if __name__ == '__main__':
    main()
