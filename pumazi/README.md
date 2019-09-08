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
- `/resources/{sha1}/media-type` | `/resources/{sha1}-media-type`


## Stories

### As REX, I want to obtain the baked HTML and metadata for content (book and/or page), so that I can render the REX site.

### As a developer, I want to view the raw HTML of a book, so that I am able to drill down through the links of a book.

### As a developer, I want to view the raw HTML of a page, so that I can view the read the HTML.

### As a developer, I want to view the baked book's HTML, so that I am able to drill down through the links of the book.

### As a developer, I want to view the baked book's HTML pages, so that I am able to read the HTML.

