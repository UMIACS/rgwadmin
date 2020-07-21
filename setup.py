#!/usr/bin/env python

from os import path
import ast
import re

try:
    from setuptools import setup
    extra = dict(include_package_data=True)
except ImportError:
    from distutils.core import setup
    extra = {}

BASE_DIR = path.abspath(path.dirname(__file__))
with open(path.join(BASE_DIR, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
    "requests",
    "requests-aws",
]

_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('rgwadmin/__init__.py', encoding='utf-8') as f:
    version = str(ast.literal_eval(_version_re.search(f.read()).group(1)))


setup(
    name="rgwadmin",
    packages=["rgwadmin"],
    version=version,
    install_requires=install_requires,
    author="Derek Yarnell",
    author_email="derek@umiacs.umd.edu",
    maintainer="UMIACS Staff",
    maintainer_email="github@umiacs.umd.edu",
    url="https://github.com/UMIACS/rgwadmin",
    license="LGPL v2.1",
    description="Python Rados Gateway Admin API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["ceph", "radosgw", "admin api"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    **extra
)
