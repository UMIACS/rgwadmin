#!/usr/bin/env python

from __future__ import with_statement

try:
    from setuptools import setup
    extra = dict(test_suite="tests.test.suite", include_package_data=True)
except ImportError:
    from distutils.core import setup
    extra = {}

long_description = \
'''
rgwadmin is a Python interface to the Rados Gateway Admin API.

It allows for the creation, modification, and deletion of users and their
access keys.  Usage information can also be retrieved.  This library is going
to save you from interacting directly with a REST interface, constructing query
strings, parsing error codes, and all that fun stuff!  It's awesome!  Enjoy!
'''

from rgwadmin import __version__
from rgwadmin import __license__

setup(
    name="rgwadmin",
    packages=["rgwadmin"],
    version=__version__,
    author="Derek Yarnell",
    author_email="derek@umiacs.umd.edu",
    maintainer="UMIACS Staff",
    maintainer_email="github@umiacs.umd.edu",
    url="https://github.com/UMIACS/rgwadmin",
    license=__license__,
    description="Python Rados Gateway Admin API",
    long_description=long_description,
    keywords=["ceph", "radosgw", "admin api"],
    **extra
)
