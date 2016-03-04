#!/usr/bin/env python

import logging
import rgwadmin
import unittest
from rgwadmin.utils import get_environment_creds, id_generator
from rgwadmin.user import RGWUser

logging.basicConfig(level=logging.WARNING)


class RGWUserTest(unittest.TestCase):
    def setUp(self):
        rgw = rgwadmin.RGWAdmin(**get_environment_creds())
        rgwadmin.RGWAdmin.set_connection(rgw)

    def test_create_user(self):
        user_id = id_generator()
        display_name = id_generator(25)
        print (user_id, display_name)
        u = RGWUser.create(user_id=user_id,
                           display_name=display_name,
                           email="{}@test.com".format(user_id))

        self.assertTrue(u.user_id == user_id and
                        u.display_name == display_name)
        u.delete()

    def test_set_quota(self):
        user_id = id_generator()
        display_name = id_generator(25)
        u = RGWUser.create(user_id=user_id, display_name=display_name)
        u.user_quota.size = 1024000
        u.save()
        nu = RGWUser.fetch(u.user_id)
        self.assertTrue(u.user_quota.size == nu.user_quota.size)
        nu.delete()

if __name__ == '__main__':
    unittest.main()
