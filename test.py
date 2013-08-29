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

pp.pprint(rgw.user('derek'))
pp.pprint(rgw.users())
