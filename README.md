# pdftables-api

[![Build Status](https://travis-ci.org/pdftables/python-pdftables-api.svg)](https://travis-ci.org/pdftables/python-pdftables-api)

Python library to interact with the
[PDFTables.com](https://pdftables.com/api) API.


## Installation

PIP:

    pip install git+https://github.com/pdftables/python-pdftables-api.git

Locally:

    python setup.py install


## Usage

```py
import pdftables_api

c = pdftables_api.Client('my-api-key')
c.xlsx('input.pdf', 'output.xlsx')
```


## Test

    python -m unittest test.test_pdftables_api
