#!/usr/bin/env python

from setuptools import setup


setup(
    name='jsonproxy',
    version='0.0.0',
    description='Generic proxy to allow access to non-jsonp APIs',
    long_description=open('README.rst').read(),
    url='https://github.com/xi/jsonproxy',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    packages=['jsonproxy'],
    install_requires=[
        'flask',
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
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU Affero General Public License v3 '\
            'or later (AGPLv3+)',
        'Topic :: Internet :: Proxy Servers',
    ])
