# Copyright 2026 Cantabular Ltd
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

import io
import os
from tempfile import NamedTemporaryFile
from unittest import TestCase

import pytest
import requests_mock

from pdftables_api import (
    EXTRACT_TABLES,
    EXTRACT_TABLES_PARAGRAPHS,
    EXTRACTOR_AI_1,
    EXTRACTOR_AI_2,
    EXTRACTOR_STANDARD,
    APIException,
    Client,
)


class TestEnsureExtFormat(TestCase):
    def test_wrong_format(self):
        with pytest.raises(ValueError):
            Client.ensure_format_ext("foo.csv", "txt")
        with pytest.raises(ValueError):
            Client("key").dump("foo.pdf", "txt")

    def test_unmodified(self):
        assert ("foo.csv", "csv") == Client.ensure_format_ext("foo.csv", "csv")
        assert ("foo.xlsx", "xlsx-multiple") == Client.ensure_format_ext(
            "foo.xlsx", "xlsx-multiple"
        )
        assert ("foo.xlsx", "xlsx-multiple") == Client.ensure_format_ext(
            "foo.xlsx", "xlsx-multiple"
        )
        assert ("foo.xml", "xml") == Client.ensure_format_ext("foo.xml", "xml")
        assert ("foo.html", "html") == Client.ensure_format_ext("foo.html", "html")

    def test_missing_format(self):
        assert ("foo.xlsx", "xlsx-multiple") == Client.ensure_format_ext("foo", None)
        assert ("foo.txt.xlsx", "xlsx-multiple") == Client.ensure_format_ext(
            "foo.txt", None
        )
        assert ("foo.xlsx", "xlsx-multiple") == Client.ensure_format_ext(
            "foo.xlsx", None
        )

    def test_missing_ext(self):
        assert ("foo.csv", "csv") == Client.ensure_format_ext("foo", "csv")

    def test_incorrect_ext(self):
        assert ("foo.txt.csv", "csv") == Client.ensure_format_ext("foo.txt", "csv")
        assert ("foo.xlsx.csv", "csv") == Client.ensure_format_ext("foo.xlsx", "csv")

    def test_stdout(self):
        assert (None, "xlsx-multiple") == Client.ensure_format_ext(None, None)
        assert (None, "csv") == Client.ensure_format_ext(None, "csv")


class TestRequests(TestCase):
    def test_successful_conversion(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", text="xlsx output")

            c = Client("fake_key")

            with NamedTemporaryFile(suffix="test.pdf") as tf:
                filename = tf.name

                tf.write(b"Hello world")
                tf.file.close()

                filename_out = filename.replace(".pdf", ".xlsx")

                try:
                    c.convert(filename, filename_out)

                    with open(filename_out) as fd:
                        assert fd.read() == "xlsx output"
                finally:
                    try:
                        os.unlink(filename_out)
                    except OSError:
                        pass

    def test_successful_conversion_bytes(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", content=b"xlsx output")

            with NamedTemporaryFile(suffix="test.pdf") as tf:
                filename = tf.name
                tf.write(b"Hello world")
                tf.file.close()

                output = Client("fake_key").convert(filename)

                assert b"xlsx output" == output

    def test_successful_conversion_string(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", text="csv output")

            with NamedTemporaryFile(suffix="test.pdf") as tf:
                filename = tf.name
                tf.write(b"Hello world")
                tf.file.close()

                output = Client("fake_key").convert(filename, out_format="csv")

                assert "csv output" == output

    def test_different_api_url(self):
        with requests_mock.mock() as m:
            m.post("http://example.com/api?key=fake_key", text="xlsx output")

            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("fake_key", api_url="http://example.com/api")
            s = c.dump(pdf_fo, "csv")
            assert b"xlsx output" == consume(s)

    def test_missing_api_key(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", text="xlsx output")

            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("")
            with pytest.raises(APIException, match="Invalid API key"):
                c.dump(pdf_fo, "csv")

    def test_invalid_format(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", text="xlsx output")

            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("fake_key")
            with pytest.raises(ValueError, match="Invalid output format"):
                c.dump(pdf_fo, "invalid_format")

    def test_remaining(self):
        with requests_mock.mock() as m:
            m.get("https://pdftables.com/api/remaining?key=fake_key", text="8584")

            c = Client("fake_key")
            assert c.remaining() == 8584

    def test_response_invalid_format(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", status_code=400)
            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("fake_key")
            with pytest.raises(APIException, match="Unknown file format"):
                c.dump(pdf_fo)

    def test_response_unauthorized(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=wrong_key", status_code=401)
            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("wrong_key")
            with pytest.raises(APIException, match="Unauthorized API key"):
                c.dump(pdf_fo)

    def test_response_limit_exceeded(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", status_code=402)
            pdf_fo = io.BytesIO(b"pdf content")
            c = Client("fake_key")
            with pytest.raises(APIException, match="Usage limit exceeded"):
                c.dump(pdf_fo)

    def test_response_unknown_file_format(self):
        with requests_mock.mock() as m:
            m.post("https://pdftables.com/api?key=fake_key", status_code=403)
            png_fo = io.BytesIO(b"png content")
            c = Client("fake_key")
            with pytest.raises(APIException, match="Unknown format requested"):
                c.dump(png_fo)


class TestExtractorParameters(TestCase):
    def test_default_extractor(self):
        """Test that default extractor is 'standard' with no extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=xlsx-multiple&extractor=standard",
                text="xlsx output",
            )

            c = Client("fake_key")
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name)

    def test_ai1_extractor_with_no_extract(self):
        """Test ai-1 extractor with no extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=xlsx-multiple&extractor=ai-1",
                text="xlsx output",
            )

            c = Client("fake_key", extractor=EXTRACTOR_AI_1)
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name)

    def test_ai1_extractor_with_tables(self):
        """Test ai-1 extractor with 'tables' extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=xlsx-multiple&extractor=ai-1&extract=tables",
                text="xlsx output",
            )

            c = Client("fake_key", extractor=EXTRACTOR_AI_1, extract=EXTRACT_TABLES)
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name)

    def test_ai1_extractor_with_tables_paragraphs(self):
        """Test ai-1 extractor with 'tables-paragraphs' extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=csv&extractor=ai-1&extract=tables-paragraphs",
                text="csv output",
            )

            c = Client(
                "fake_key", extractor=EXTRACTOR_AI_1, extract=EXTRACT_TABLES_PARAGRAPHS
            )
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name, out_format="csv")

    def test_ai2_extractor_with_no_extract(self):
        """Test ai-2 extractor with no extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=xlsx-multiple&extractor=ai-2",
                text="xlsx output",
            )

            c = Client("fake_key", extractor=EXTRACTOR_AI_2)
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name)

    def test_ai2_extractor_with_tables(self):
        """Test ai-2 extractor with 'tables' extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=xlsx-multiple&extractor=ai-2&extract=tables",
                text="xlsx output",
            )

            c = Client("fake_key", extractor=EXTRACTOR_AI_2, extract=EXTRACT_TABLES)
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name)

    def test_ai2_extractor_with_tables_paragraphs(self):
        """Test ai-2 extractor with 'tables-paragraphs' extract parameter."""
        with requests_mock.mock() as m:
            m.post(
                "https://pdftables.com/api?key=fake_key&format=csv&extractor=ai-2&extract=tables-paragraphs",
                text="csv output",
            )

            c = Client(
                "fake_key", extractor=EXTRACTOR_AI_2, extract=EXTRACT_TABLES_PARAGRAPHS
            )
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name, out_format="csv")

    def test_standard_extractor_no_extract_param_in_url(self):
        """Test that standard extractor doesn't include extract parameter in URL."""
        with requests_mock.mock() as m:
            # Note: no 'extract' parameter in the URL for standard extractor
            m.post(
                "https://pdftables.com/api?key=fake_key&format=csv&extractor=standard",
                text="csv output",
            )

            c = Client("fake_key", extractor=EXTRACTOR_STANDARD, extract=None)
            with NamedTemporaryFile(suffix="test.pdf") as tf:
                tf.write(b"Hello world")
                tf.file.close()
                c.convert(tf.name, out_format="csv")

    def test_invalid_extractor_raises_error(self):
        """Test that invalid extractor raises ValueError."""
        with pytest.raises(
            ValueError,
            match='^Invalid extractor "invalid". Valid options are: standard, ai-1, ai-2$',
        ):
            Client("fake_key", extractor="invalid")

    def test_invalid_extract_for_standard_raises_error(self):
        """Test that providing extract parameter for standard extractor raises ValueError."""
        with pytest.raises(
            ValueError,
            match='^Extractor "standard" does not support extract parameter$',
        ):
            Client("fake_key", extractor=EXTRACTOR_STANDARD, extract=EXTRACT_TABLES)

    def test_invalid_extract_for_ai_raises_error(self):
        """Test that invalid extract value for AI extractor raises ValueError."""
        with pytest.raises(
            ValueError,
            match='^Invalid extract value "invalid" for extractor "ai-1". Valid values are: tables, tables-paragraphs$',
        ):
            Client("fake_key", extractor=EXTRACTOR_AI_1, extract="invalid")

    def test_invalid_extract_for_ai2_raises_error(self):
        """Test that invalid extract value for AI-2 extractor raises ValueError."""
        with pytest.raises(
            ValueError,
            match='^Invalid extract value "invalid" for extractor "ai-2". Valid values are: tables, tables-paragraphs$',
        ):
            Client("fake_key", extractor=EXTRACTOR_AI_2, extract="invalid")


def consume(s):
    r = b""
    for chunk in s:
        r += chunk
    return r
