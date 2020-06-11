# pdftables-api

Python library to interact with the
[PDFTables.com](https://pdftables.com/api) API.

Supported versions of Python are listed in [ci-build.yml](.github/workflows/ci-build.yml).


## Installation

pip: (requires git installed)

    pip install git+https://github.com/pdftables/python-pdftables-api.git

pip: (without git)

    pip install https://github.com/pdftables/python-pdftables-api/archive/master.tar.gz
    
Locally:

    python setup.py install

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

## Test

    python -m unittest test.test_pdftables_api

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
