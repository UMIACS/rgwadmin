#!/usr/bin/env python

from __future__ import with_statement

try:
    from setuptools import setup
    extra = dict(test_suite="tests.test.suite", include_package_data=True)
except ImportError:
    from distutils.core import setup
    extra = {}

setup(
    name = "rgwadmin",
    packages = ["rgwadmin"],
    version = "0.2.2",
    description = "Python Rados Gateway Admin API",
    author = "Derek Yarnell",
    author_email = "derek@umiacs.umd.edu",
    url = "http://www.umiacs.umd.edu/",
    keywords = ["ceph", "radosgw"],
    **extra
)
