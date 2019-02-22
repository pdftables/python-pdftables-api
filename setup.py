#!/usr/bin/env python

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
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = 'pdftables-api',
    version = '1.1.0',
    author = 'The Sensible Code Company',
    author_email = 'support@sensiblecode.io',
    description = ('PDFTables.com Python API library.'),
    long_description=read('README.md'),
    license = 'Apache License 2.0',
    keywords = 'pdf tables excel csv xml api',
    url = 'https://github.com/sensiblecode/python-pdftables-api',
    packages=['pdftables_api'],
    install_requires=[
        'requests',
    ],
    tests_require=[
        'requests_mock',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking',
    ],
)
