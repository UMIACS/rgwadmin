#!/usr/bin/env python

import json
import logging
import unittest

import rgwadmin
from rgwadmin.utils import get_environment_creds, id_generator

logging.basicConfig(level=logging.WARNING)


class MetadataTest(unittest.TestCase):

    def setUp(self):
        self.rgw = rgwadmin.RGWAdmin(secure=False, verify=False,
                                     **get_environment_creds())
        rgwadmin.RGWAdmin.set_connection(self.rgw)

    def test_get_metadata(self):
        bucket_name = id_generator()
        self.assertTrue(bucket_name not in self.rgw.get_metadata('bucket'))
        self.rgw.create_bucket(bucket=bucket_name)
        self.assertTrue(bucket_name in self.rgw.get_metadata('bucket'))
        self.rgw.remove_bucket(bucket=bucket_name, purge_objects=True)

    def test_put_metadata(self):
        bucket_name = id_generator()
        self.assertTrue(bucket_name not in self.rgw.get_metadata('bucket'))
        self.rgw.create_bucket(bucket=bucket_name)

        ret_json = self.rgw.get_metadata('bucket', key=bucket_name)
        self.assertEqual(ret_json['data']['bucket']['name'], bucket_name)
        json_str = json.dumps(ret_json)

        self.rgw.put_metadata('bucket', key=bucket_name, json_string=json_str)
        self.rgw.remove_bucket(bucket=bucket_name, purge_objects=True)

    def test_metadata_lock_unlock(self):
        bucket_name = id_generator()
        self.rgw.create_bucket(bucket=bucket_name)
        self.rgw.lock_metadata('bucket', key=bucket_name, lock_id='abc',
                               length=5)
        self.rgw.unlock_metadata('bucket', key=bucket_name, lock_id='abc')
        self.rgw.remove_bucket(bucket=bucket_name, purge_objects=True)

    def test_invalid_metadata_unlock(self):
        with self.assertRaises(rgwadmin.exceptions.NoSuchKey):
            key = id_generator()
            self.rgw.unlock_metadata('bucket', key=key, lock_id='abc')

    def test_metadata_type_valid(self):
        with self.assertRaises(Exception):
            self.rgw.get_metadata('bucketttt')

    def test_get_bucket_instances(self):
        bucket_name = id_generator()
        self.rgw.create_bucket(bucket=bucket_name)
        instances = self.rgw.get_bucket_instances()
        bucket = self.rgw.get_bucket(bucket_name)
        expected_instance = '%s:%s' % (bucket_name, bucket['id'])
        self.assertTrue(expected_instance in instances)
        self.rgw.remove_bucket(bucket=bucket_name, purge_objects=True)


if __name__ == '__main__':
    unittest.main()
