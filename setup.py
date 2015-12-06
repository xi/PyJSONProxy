#!/usr/bin/env python

from setuptools import setup


setup(
    name='jsonproxy',
    version='1.0.0',
    description='Generic proxy to allow access to non-jsonp APIs',
    long_description=open('README.rst').read(),
    url='https://github.com/xi/PyJSONProxy',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    packages=['jsonproxy'],
    install_requires=[
        'aiohttp',
        'beautifulsoup4',
        'jinja2',
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
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: GNU Affero General Public License v3 '
            'or later (AGPLv3+)',
        'Topic :: Internet :: Proxy Servers',
    ])
