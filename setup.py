#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='survey-stats',
    version='0.1.0',
    license='BSD',
    description='A package wrapping R survey package using Rpy2, with some helper methods for CDC survey data.',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author='Ajish George',
    author_email='ajish@rootedinsights.com',
    url='https://github.com/uhjish/survey_stats',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    install_requires=[
        'Cython>=0.25.2',
        'cachetools>=2.0.0',
        'Werkzeug>=0.12',
        'aiofiles>=0.3.0',
        'aiohttp>=1.2.0',
        'cached-property>=1.3.0',
        'cytoolz>=0.8.2',
        'feather-format>=0.3.1',
        'gunicorn>=19.6.0',
        'jsonschema>=2.5.1',
        'pandas>=0.19.2',
        'PyYAML>=3.12',
        'requests>=2.11.1',
        'rpy2>=2.8.4',
        'Sanic>=0.3.0',
        'six>=1.10.0',
        'toolz>=0.8.2',
        'ujson>=1.35',
        'uvloop>=0.7.2',
        'xmltodict>=0.10.2',
        'falcon>=1.0.0',
        'py-lru-cache>=0.1.4'
        # eg: 'aspectlib==1.1.1', 'six>=1.7',
    ],
    extras_require={
        # eg:
        #   'rst': ['docutils>=0.11'],
        #   ':python_version=="2.6"': ['argparse'],
    },
    entry_points={
        'console_scripts': [
            'survey_stats = survey_stats.cli:main'
        ]
    },
)
