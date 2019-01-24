# Copyright 2016 The Sensible Code Company
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import requests

from shutil import copyfileobj


FORMAT_CSV = 'csv'
FORMAT_HTML = 'html'
FORMAT_XLSX_MULTIPLE = 'xlsx-multiple'
FORMAT_XLSX_SINGLE = 'xlsx-single'
FORMAT_XLSX = FORMAT_XLSX_MULTIPLE
FORMAT_XML = 'xml'

_API_URL = 'https://pdftables.com/api'
_DEFAULT_TIMEOUT = (10, 300)  # seconds (connect and read)
_FORMATS_EXT = {
    FORMAT_CSV: '.csv',
    FORMAT_HTML: '.html',
    FORMAT_XLSX: '.xlsx',
    FORMAT_XLSX_MULTIPLE: '.xlsx',
    FORMAT_XLSX_SINGLE: '.xlsx',
    FORMAT_XML: '.xml',
}
_EXT_FORMATS = {
    '.csv': FORMAT_CSV,
    '.html': FORMAT_HTML,
    '.xlsx': FORMAT_XLSX,
    '.xml': FORMAT_XML,
}
_STRING_FORMATS = {FORMAT_CSV, FORMAT_HTML, FORMAT_XML}

class Client(object):
    def __init__(self, api_key, api_url=_API_URL, timeout=_DEFAULT_TIMEOUT):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def xlsx(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX multiple sheets.

        If xlsx_path is None, returns the output as a byte string.
        """
        return self.xlsx_multiple(pdf_path, xlsx_path)

    def xlsx_single(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX single sheet.

        If xlsx_path is None, returns the output as a byte string.
        """
        return self.convert(pdf_path, xlsx_path, out_format=FORMAT_XLSX_SINGLE)

    def xlsx_multiple(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX multiple sheets.

        If xlsx_path is None, returns the output as a byte string.
        """
        return self.convert(pdf_path, xlsx_path, out_format=FORMAT_XLSX_MULTIPLE)

    def xml(self, pdf_path, xml_path=None):
        """
        Convenience method to convert PDF to XML.

        If xml_path is None, returns the output as a string.
        """
        return self.convert(pdf_path, xml_path, out_format=FORMAT_XML)

    def csv(self, pdf_path, csv_path=None):
        """
        Convenience method to convert PDF to CSV.

        If csv_path is None, returns the output as a string.
        """
        return self.convert(pdf_path, csv_path, out_format=FORMAT_CSV)

    def html(self, pdf_path, html_path=None):
        """
        Convenience method to convert HTML to CSV.

        If html_path is None, returns the output as a string.
        """
        return self.convert(pdf_path, html_path, out_format=FORMAT_HTML)

    def convert(self, pdf_path, out_path=None, out_format=None, query_params=None, **requests_params):
        """
        Convert PDF given by `pdf_path` into `format` at `out_path`.

        If `out_path` is None, returns a string containing the contents, or a
        bytes for binary output types (e.g, XLSX)
        """
        (out_path, out_format) = Client.ensure_format_ext(out_path, out_format)
        with open(pdf_path, 'rb') as pdf_fo:
            response = self.request(pdf_fo, out_format, query_params,
                                    **requests_params)

            if out_path is None:
                use_text = out_format in _STRING_FORMATS
                return response.text if use_text else response.content

            with open(out_path, 'wb') as out_fo:
                converted_fo = response.raw
                # Ensure that gzip content is decoded.
                converted_fo.decode_content = True
                copyfileobj(converted_fo, out_fo)

    def dump(self, pdf_fo, out_format=None, query_params=None,
             **requests_params):
        """
        Convert PDF file object given by `pdf_fo` into an output stream iterator.
        """
        response = self.request(pdf_fo, out_format, query_params,
                                **requests_params)

        return response.iter_content(chunk_size=4096)

    def request(self, pdf_fo, out_format=None, query_params=None,
                **requests_params):
        """
        Convert PDF given by `pdf_path`, returning requests.Response object.
        """
        if self.api_key == "":
            raise APIException("Invalid API key")

        if 'timeout' not in requests_params:
            requests_params.update({'timeout': self.timeout})

        (_, out_format) = Client.ensure_format_ext(None, out_format)
        url = self.api_url
        files = {'f': ('file.pdf', pdf_fo)}
        params = query_params if query_params else {}
        params.update({'key': self.api_key, 'format': out_format})

        response = requests.post(url,
                                 files=files,
                                 stream=True,
                                 params=params,
                                 **requests_params)

        if response.status_code == 400:
            raise APIException("Unknown file format")
        elif response.status_code == 401:
            raise APIException("Unauthorized API key")
        elif response.status_code == 402:
            raise APIException("Usage limit exceeded")
        elif response.status_code == 403:
            raise APIException("Unknown format requested")
        response.raise_for_status()

        return response

    def remaining(self, query_params=None, **requests_params):
        """
        Provide information of remaining pages quota.
        """
        if self.api_key == "":
            raise APIException("Invalid API key")

        url = self.api_url+'/remaining'
        params = query_params if query_params else {}
        params.update({'key': self.api_key})

        response = requests.get(url, params=params, **requests_params)

        if response.status_code == 401:
            raise APIException("Unauthorized API key")
        response.raise_for_status()

        return int(response.content)

    @staticmethod
    def ensure_format_ext(out_path, out_format):
        """
        Ensure the appropriate file extension and format is given. If not
        provided, try to guess either.
        """
        if out_format != None and out_format not in _FORMATS_EXT.keys():
            raise ValueError('Invalid output format')

        default_format = FORMAT_XLSX_MULTIPLE

        # Check if stdout is desired
        if out_path == None:
            if out_format == None:
                out_format = default_format
            return (None, out_format)

        _, ext = os.path.splitext(out_path)

        # Guess output format by file extension
        if out_format == None:
            if ext in _FORMATS_EXT.values():
                out_format = _EXT_FORMATS[ext]
            else:
                out_format = default_format

        # Ensure correct file extension by output format
        if (ext not in _FORMATS_EXT.values() or
            ext != _FORMATS_EXT[out_format]):
            out_path = out_path + _FORMATS_EXT[out_format]

        return (out_path, out_format)


class APIException(Exception):
    pass
