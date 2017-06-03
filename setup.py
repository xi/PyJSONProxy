#!/usr/bin/env python

import os
import re
from setuptools import setup

DIRNAME = os.path.abspath(os.path.dirname(__file__))
rel = lambda *parts: os.path.abspath(os.path.join(DIRNAME, *parts))

README = open(rel('README.rst')).read()
INIT = open(rel('jsonproxy/__init__.py')).read()
VERSION = re.search("__version__ = '([^']+)'", INIT).group(1)


setup(
    name='jsonproxy',
    version=VERSION,
    description='Generic proxy to allow access to non-jsonp APIs',
    long_description=README,
    url='https://github.com/xi/PyJSONProxy',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    packages=['jsonproxy'],
    include_package_data=True,
    install_requires=[
        'Fakes',
        'beautifulsoup4',
    ],
    entry_points={'console_scripts': [
        'jsonproxy=jsonproxy:main',
    ]},
    license='AGPLv3+',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU Affero General Public License v3 '
            'or later (AGPLv3+)',
        'Topic :: Internet :: Proxy Servers',
    ])
