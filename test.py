#!/usr/bin/env python

import os
import logging
import rgwadmin
import pprint

logging.basicConfig(level=logging.DEBUG)

access_key = os.environ['OBJ_ACCESS_KEY_ID']
secret_key = os.environ['OBJ_SECRET_ACCESS_KEY']
server = os.environ['OBJ_SERVER']

pp = pprint.PrettyPrinter(indent=4)

rgw = rgwadmin.RGWAdmin(access_key, secret_key, server, secure=True)

pp.pprint(rgw.create_user(uid='foo', display_name='Foo Bar',
          secret_key=rgwadmin.RGWAdmin.gen_secret_key() ))
#pp.pprint(rgw.modify_user(uid='foo', email='foo@bar.com'))
#pp.pprint(rgw.get_usage())
#pp.pprint(rgw.create_subuser(uid='foo', subuser='bar'))
#pp.pprint(rgw.modify_subuser(uid='foo', subuser='bar', access='write'))
#pp.pprint(rgw.remove_subuser(uid='foo', subuser='bar'))
#pp.pprint(rgw.create_key(uid='foo'))
##pp.pprint(rgw.create_bucket(bucket='foo'))
#pp.pprint(rgw.link_bucket(bucket='foo', uid='foo'))
#pip.pprint(rgw.get_bucket(uid='foo'))
#pp.pprint(rgw.get_policy(bucket='foo'))
#pp.pprint(rgw.remove_bucket(bucket='foo', purge_objects=True))
#pp.pprint(rgw.get_user(uid='foo'))
#pp.pprint(rgw.get_users())
#pp.pprint(rgw.remove_user(uid='foo'))
