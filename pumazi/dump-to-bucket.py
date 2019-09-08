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
- ``/resources/{sha1}/media-type`` | ``/resources/{sha1}-media-type``


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
    def content_path(path_tmplt, ident):
        x = []
        for ident_hash in ident:
            x.append(join_ident_hash(*ident_hash))
        return path_tmplt.format(*x)

    func = {
        'raw-book-json': lambda i: content_path('raw/{0}.json', i),
        'raw-book-html': lambda i: content_path('raw/{0}.html', i),
        'raw-page-json': lambda i: content_path('raw/{0}.json', i),
        'raw-page-html': lambda i: content_path('raw/{0}.html', i),
        'baked-book-json': lambda i: content_path('baked/{0}.json', i),
        'baked-book-html': lambda i: content_path('baked/{0}.html', i),
        'baked-page-json': lambda i: content_path('baked/{0}:{1}.json', i),
        'baked-page-html': lambda i: content_path('baked/{0}:{1}.html', i),
        'resource': lambda i: f'resources/{i}',
        'resource-media-type': lambda i: f'resources/{i}-media-type',
    }[type_]
    return func(ident)

# Some sanity tests...
assert gen_filepath('raw-book-json', [('abc123', '1.1')]) == 'raw/abc123@1.1.json'
assert gen_filepath('raw-book-html', [('abc123', '1.1')]) == 'raw/abc123@1.1.html'
assert gen_filepath('raw-page-json', [('abc123', '1.1')]) == 'raw/abc123@1.1.json'
assert gen_filepath('raw-page-html', [('abc123', '1.1')]) == 'raw/abc123@1.1.html'
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
    resp = requests.get(url)
    version = resp.json()['version']

    info(f'latest version of requested book: {T.bold}{id}@{version}{T.normal}')

    # Get the latest version's contents and resources
    # With this we'll have access to the list of past versions
    for item in scrape_version(id, version, host, visited_locs):
        data, type, id = item
        if type == 'raw-book-json':
            # TODO: Make note of the historical versions for later scraping
            historical = []
        yield item

    # TODO: Yield this latest version before progressing to yielding subversions

    # TODO: Yield the historical versions of this book


def scrape_version(id, version, host, visited_locs):
    """
    """
    ident_hash = join_ident_hash(id, version)
    base_url = f'https://{host}/contents/{ident_hash}'

    # Request the JSON
    url = f'{base_url}.json'
    debug(f'Requesting {T.yellow}{url}{T.normal}')
    resp = requests.get(url)
    yield io.BytesIO(resp.content), f'raw-book-json', [(id, version,)]
    # Save the raw json for later
    raw_json = resp.json()

    # Request the HTML
    url = f'{base_url}.html'
    debug(f'Requesting {T.yellow}{url}{T.normal}')
    resp = requests.get(url)
    yield io.BytesIO(resp.content), f'raw-book-html', [(id, version,)]

    # TODO: Request the resources...
    # TODO: Request the individual pages


def dump_in_bucket(items, bucket_info):
    bucket_name, region_name = bucket_info
    s3 = boto3.resource('s3', region_name=region_name)
    bucket = s3.Bucket(bucket_name)

    for item in items:
        data, type, ident = item
        key = gen_filepath(type, ident)
        debug(f'Dumping {T.blue}{type}{T.normal} into the bucket at "{T.green_bold}{key}{T.normal}"')
        bucket.upload_fileobj(data, key)


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
