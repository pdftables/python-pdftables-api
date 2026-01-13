# pdftables-api

Python library to interact with the
[PDFTables.com](https://pdftables.com/api) API.

Supported versions of Python are listed in [ci-build.yml](.github/workflows/ci-build.yml).


## Installation

pip: (requires git installed)

    pip install git+https://github.com/pdftables/python-pdftables-api.git

pip: (without git)

    pip install https://github.com/pdftables/python-pdftables-api/archive/master.tar.gz

For local development:

    uv sync

### Upgrading

If using pip, then use pip with the `--upgrade` flag, e.g.

    pip install --upgrade git+https://github.com/pdftables/python-pdftables-api.git

## Usage

Sign up for an account at [PDFTables.com](https://pdftables.com/) and then visit the
[API page](https://pdftables.com/pdf-to-excel-api) to see your API key.

Replace `my-api-key` below with your API key.

```py
import pdftables_api

c = pdftables_api.Client('my-api-key')
c.xlsx('input.pdf', 'output.xlsx')
```

## Formats

To convert to CSV, XML or HTML simply change `c.xlsx` to be `c.csv`, `c.xml` or `c.html` respectively. 

To specify Excel (single sheet) or Excel (multiple sheets) use `c.xlsx_single` or `c.xlsx_multiple`.

## Extractor

You can specify which extraction engine to use when creating a `Client`. The available extractors are `standard` (default), `ai-1`, and `ai-2`.

For AI extractors (`ai-1` and `ai-2`), you can also specify an `extract` option to control what content is extracted: `tables` (default) or `tables-paragraphs`.

```py
import pdftables_api

# Standard extractor (default)
c = pdftables_api.Client('my-api-key')

# AI extractors for complex documents
c = pdftables_api.Client('my-api-key', extractor='ai-1', extract='tables')
c = pdftables_api.Client('my-api-key', extractor='ai-2', extract='tables-paragraphs')
```

See [PDFTables API documentation](https://pdftables.com/pdf-to-excel-api) for details.

## Test

Tests run with pytest: `make test`

## Linting and formatting

* Format with `make format`
* Apply Ruff fixes with `make fix`

## Configuring a timeout

If you are converting a large document (hundreds or thousands of pages),
you may want to increase the timeout.

Here is an example of the sort of error that might be encountered:

```
ReadTimeout: HTTPSConnectionPool(host='pdftables.com', port=443): Read timed out. (read timeout=300)
```

The below example allows 60 seconds to connect to our server, and 1 hour to convert the document:

```py
import pdftables_api

c = pdftables_api.Client('my-api-key', timeout=(60, 3600))
c.xlsx('input.pdf', 'output.xlsx')
```
