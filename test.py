#!/usr/bin/env python

import os
import logging
import rgwadmin
import unittest

logging.basicConfig(level=logging.WARNING)

access_key = os.environ['OBJ_ACCESS_KEY_ID']
secret_key = os.environ['OBJ_SECRET_ACCESS_KEY']
server = os.environ['OBJ_SERVER']


class RGWAdminTest(unittest.TestCase):

    def setUp(self):
        self.rgw = rgwadmin.RGWAdmin(access_key,
                                     secret_key,
                                     server,
                                     secure=True)
        self.user1 = 'foo1209'
        self.user2 = 'foo1213'
        self.secret = rgwadmin.RGWAdmin.gen_secret_key()
        user1 = self.rgw.create_user(uid=self.user1,
                                     display_name='Unit Test %s' % self.user1,
                                     secret_key=self.secret)
        user2 = self.rgw.create_user(uid=self.user2,
                                     display_name='Unit Test %s' % self.user2,
                                     secret_key=self.secret)
        self.user1_obj = user1
        self.user2_obj = user2
        self.assertTrue(user1['user_id'] == self.user1)
        self.assertTrue(user2['user_id'] == self.user2)

    def tearDown(self):
        self.rgw.remove_user(uid=self.user1)
        self.rgw.remove_user(uid=self.user2)

    def test_modify_user(self):
        user = self.rgw.modify_user(uid=self.user1,
                                    email='%s@test.com' % self.user1)
        self.assertTrue(user['email'] == '%s@test.com' % self.user1)

    def test_get_user(self):
        user = self.rgw.get_user(uid=self.user2)
        self.assertTrue(user['display_name'] == 'Unit Test %s' % self.user2)

    def test_get_users(self):
        users = self.rgw.get_users()
        self.assertTrue(self.user1 in users)
        self.assertTrue(self.user2 in users)

    def test_bucket(self):
        bucket = self.user1 + '_bucket'
        self.rgw.create_bucket(bucket=bucket)
        self.rgw.link_bucket(bucket=bucket, uid=self.user1)
        self.rgw.get_bucket(uid=self.user1, bucket=bucket)
        self.rgw.get_policy(bucket=bucket)
        self.rgw.remove_bucket(bucket=bucket, purge_objects=True)
        self.assertTrue(True)

    def test_get_usage(self):
        summary = self.rgw.get_usage(show_summary=True)
        self.assertTrue('summary' in summary)

    def test_subuser(self):
        self.rgw.create_subuser(uid=self.user2,
                                subuser='swift',
                                key_type='swift',
                                secret_key=self.secret)
        self.rgw.modify_subuser(uid=self.user2,
                                subuser='swift',
                                access='write')
        subuser = self.rgw.get_user(uid=self.user2)
        self.rgw.remove_subuser(uid=self.user2, subuser='swift')
        for subs in subuser['subusers']:
            if subs['id'] == '%s:%s' % (self.user2, 'swift'):
                self.assertTrue(subs['permissions'] == 'write')

    def test_s3_keys(self):
        access = rgwadmin.RGWAdmin.gen_secret_key(size=20)
        secret = rgwadmin.RGWAdmin.gen_secret_key(size=40)
        keys = self.rgw.create_key(uid=self.user1,
                                   access_key=access,
                                   secret_key=secret)
        for key in keys:
            if key['access_key'] == access:
                self.assertTrue(key['secret_key'] == secret)


if __name__ == '__main__':
    unittest.main()
