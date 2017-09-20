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

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


FORMAT_CSV = 'csv'
FORMAT_XLSX_MULTIPLE = 'xlsx-multiple'
FORMAT_XLSX_SINGLE = 'xlsx-single'
FORMAT_XLSX = FORMAT_XLSX_MULTIPLE
FORMAT_XML = 'xml'

_API_URL = 'https://pdftables.com/api'
_DEFAULT_TIMEOUT = (10, 300)  # seconds (connect and read)
_FORMATS_EXT = {
    FORMAT_CSV: '.csv',
    FORMAT_XLSX: '.xlsx',
    FORMAT_XLSX_MULTIPLE: '.xlsx',
    FORMAT_XLSX_SINGLE: '.xlsx',
    FORMAT_XML: '.xml',
}
_EXT_FORMATS = {
    '.csv': FORMAT_CSV,
    '.xlsx': FORMAT_XLSX,
    '.xml': FORMAT_XML,
}

class Client(object):
    def __init__(self, api_key, api_url=_API_URL, timeout=_DEFAULT_TIMEOUT):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def xlsx(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX multiple sheets.
        """
        return self.xlsx_multiple(pdf_path, xlsx_path)

    def xlsx_single(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX single sheet.
        """
        return self.convert(pdf_path, xlsx_path, out_format=FORMAT_XLSX_SINGLE)

    def xlsx_multiple(self, pdf_path, xlsx_path=None):
        """
        Convenience method to convert PDF to XLSX multiple sheets.
        """
        return self.convert(pdf_path, xlsx_path, out_format=FORMAT_XLSX_MULTIPLE)

    def xml(self, pdf_path, xml_path=None):
        """
        Convenience method to convert PDF to XML.
        """
        return self.convert(pdf_path, xml_path, out_format=FORMAT_XML)

    def csv(self, pdf_path, csv_path=None):
        """
        Convenience method to convert PDF to CSV.
        """
        return self.convert(pdf_path, csv_path, out_format=FORMAT_CSV)

    def convert(self, pdf_path, out_path, out_format=None, query_params=None, **requests_params):
        """
        Convert PDF given by `pdf_path` into `format` at `out_path`.
        """
        (out_path, out_format) = Client.ensure_format_ext(out_path, out_format)
        with open(pdf_path, 'rb') as pdf_fo:
            data = self.dump(pdf_fo, out_format, query_params, **requests_params)
            if out_path is None:
                out_fo = StringIO.StringIO()
                for chunk in data:
                        if chunk:
                            out_fo.write(chunk)
                content = out_fo.getvalue()
                out_fo.close()
                return content
            else:
                with open(out_path, 'wb') as out_fo:
                    for chunk in data:
                        if chunk:
                            out_fo.write(chunk)

    def dump(self, pdf_fo, out_format=None, query_params=None, **requests_params):
        """
        Convert PDF given by `pdf_path` into an output stream iterator.
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

        return response.iter_content(chunk_size=4096)

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
