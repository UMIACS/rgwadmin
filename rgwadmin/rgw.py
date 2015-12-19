import time
import json
from StringIO import StringIO
import logging
import string
import random

import requests
from awsauth import S3Auth

from .exceptions import (
    RGWAdminException, AccessDenied, UserExists,
    InvalidAccessKey, InvalidSecretKey, InvalidKeyType,
    KeyExists, EmailExists, SubuserExists, InvalidAccess,
    IndexRepairFailed, BucketNotEmpty, ObjectRemovalFailed,
    BucketUnlinkFailed, BucketLinkFailed, NoSuchObject,
    IncompleteBody, InvalidCap, NoSuchCap,
    InternalError, NoSuchUser, NoSuchBucket, NoSuchKey,
    ServerDown, InvalidQuotaType, InvalidArgument, BucketAlreadyExists
)

log = logging.getLogger(__name__)


class RGWAdmin:

    def __init__(self, access_key, secret_key, server,
                 admin='admin', response='json', ca_bundle=None,
                 secure=True, verify=True):
        self._access_key = access_key
        self._secret_key = secret_key
        self._server = server
        self._admin = admin
        self._response = response

        # ssl support
        self._ca_bundle = ca_bundle
        self._verify = verify
        if secure:
            self._protocol = 'https'
        else:
            self._protocol = 'http'

    @classmethod
    def connect(cls, **kwargs):
        # set the connection on RGWAdmin
        # note: only one connection can be active in any single process
        cls.set_connection(RGWAdmin(**kwargs))

    @classmethod
    def set_connection(cls, connection):
        cls.connection = connection

    @classmethod
    def get_connection(cls):
        return cls.connection

    def __repr__(self):
        return "%s (%s)" % (self.__class__.__name__, self.get_base_url())

    def __str__(self):
        returning = self.__repr__()
        returning += '\nAccess Key: %s\n' % self._access_key
        returning += 'Secret Key: ******\n'
        returning += 'Response Method: %s\n' % self._response
        if self._ca_bundle is not None:
            returning += 'CA Bundle: %s\n' % self._ca_bundle
        return returning

    def get_base_url(self):
        '''Return a base URL.  I.e. https://ceph.server'''
        return '%s://%s' % (self._protocol, self._server)

    def _load_request(self, r):
        '''Load the request given as JSON handling exceptions if necessary'''
        try:
            j = json.load(StringIO(r.content))
        except ValueError as e:
            # some calls in the admin API encode the info in the headers
            # instead of the body.  The code that follows is an ugly hack
            # due to the fact that there's a bug in the admin API we're
            # interfacing with.

            # set a default value for j in case we don't find json in the
            # headers below
            j = None

            # find a key with a '{', since this will hold the json response
            for k, v in r.headers.items():
                if '{' in k:
                    json_string = ":".join([k, v]).split('}')[0] + '}'
                    j = json.load(StringIO(json_string))
                    break
        if r.status_code == requests.codes.ok:
            return j
        elif r.status_code == requests.codes.no_content:
            return None
        else:
            if j is not None:
                log.error(j)
                code = str(j['Code'])
            else:
                raise ServerDown
            for e in [AccessDenied, UserExists, InvalidAccessKey,
                      InvalidKeyType, InvalidSecretKey, KeyExists, EmailExists,
                      SubuserExists, InvalidAccess, InvalidArgument,
                      IndexRepairFailed, BucketNotEmpty, ObjectRemovalFailed,
                      BucketUnlinkFailed, BucketLinkFailed, NoSuchObject,
                      InvalidCap, NoSuchCap, NoSuchUser, NoSuchBucket,
                      NoSuchKey, IncompleteBody, BucketAlreadyExists,
                      InternalError]:
                if code == e.__name__:
                    raise e
            raise RGWAdminException(code)

    def request(self, method, request, headers=None, data=None):
        url = '%s%s' % (self.get_base_url(), request)
        log.debug('URL: %s' % url)
        log.debug('Access Key: %s' % self._access_key)
        log.debug('Verify: %s  CA Bundle: %s' % (self._verify,
                                                 self._ca_bundle))
        try:
            m = getattr(requests, method.lower())
            if self._ca_bundle:
                verify = self._ca_bundle
            else:
                verify = self._verify
            auth = S3Auth(self._access_key, self._secret_key, self._server)
            r = m(url, headers=headers, auth=auth, verify=verify, data=data)
        except Exception as e:
            log.exception(e)
            return None
        return self._load_request(r)

    def get_metadata(self, metadata_type, key):
        ''' Returns JSON '''
        if metadata_type in ['user', 'bucket']:
            return self.request(
                'get', '/%s/metadata/%s?format=%s&key=%s' %
                (self._admin, metadata_type, self._response, key)
            )

    def set_metadata(self, metadata_type, key, json_string):
        if metadata_type in ['user', 'bucket']:
            return self.request(
                'put', '/%s/metadata/%s?key=%s' %
                (self._admin, metadata_type, key),
                headers={'Content-Type': 'application/json'},
                data=json_string,
            )

    def get_user(self, uid):
        return self.request('get', '/%s/user?format=%s&uid=%s' %
                            (self._admin, self._response, uid))

    def get_users(self):
        return self.request('get', '/%s/metadata/user?format=%s' %
                            (self._admin, self._response))

    def create_user(self, uid, display_name, email=None, key_type='s3',
                    access_key=None, secret_key=None, user_caps=None,
                    generate_key=True, max_buckets=None, suspended=False):
        parameters = 'uid=%s&display-name=%s' % (uid, display_name)
        if email is not None:
            parameters += '&email=%s' % email
        if key_type is not None:
            parameters += '&key-type=%s' % key_type
        if access_key is not None:
            parameters += '&access-key=%s' % access_key
        if secret_key is not None:
            parameters += '&secret-key=%s' % secret_key
        if user_caps is not None:
            parameters += '&user-caps=%s' % user_caps
        parameters += '&generate-key=%s' % generate_key
        if max_buckets is not None:
            parameters += '&max-buckets=%s' % max_buckets
        parameters += '&suspended=%s' % suspended
        return self.request('put', '/%s/user?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def get_usage(self, uid=None, start=None, end=None, show_entries=False,
                  show_summary=False):
        parameters = ''
        if uid is not None:
            parameters += '&uid=%s' % uid
        if start is not None:
            parameters += '&start=%s' % start
        if end is not None:
            parameters += '&end=%s' % end
        parameters += '&show-entries=%s' % show_entries
        parameters += '&show-summary=%s' % show_summary
        return self.request('get', '/%s/usage?format=%s%s' %
                            (self._admin, self._response, parameters))

    def trim_usage(self, uid=None, start=None, end=None, remove_all=False):
        parameters = ''
        if uid is not None:
            parameters += '&uid=%s' % uid
        if start is not None:
            parameters += '&start=%s' % start
        if end is not None:
            parameters += '&end=%s' % end
        parameters += '&remove-all=%s' % remove_all
        return self.request('delete', '/%s/usage?format=%s%s' %
                            (self._admin, self._response, parameters))

    def modify_user(self, uid, display_name=None, email=None, key_type='s3',
                    access_key=None, secret_key=None, user_caps=None,
                    generate_key=True, max_buckets=None, suspended=False):
        parameters = 'uid=%s' % uid
        if display_name is not None:
            parameters += '&display-name=%s' % display_name
        if email is not None:
            parameters += '&email=%s' % email
        if key_type is not None:
            parameters += '&key-type=%s' % key_type
        if access_key is not None:
            parameters += '&access-key=%s' % access_key
        if secret_key is not None:
            parameters += '&secret-key=%s' % secret_key
        if user_caps is not None:
            parameters += '&user-caps=%s' % user_caps
        parameters += '&generate-key=%s' % generate_key
        if max_buckets is not None:
            parameters += '&max-buckets=%s' % max_buckets
        parameters += '&suspended=%s' % suspended
        return self.request('post', '/%s/user?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def get_quota(self, uid, quota_type):
        if quota_type not in ['user', 'bucket']:
            raise InvalidQuotaType
        parameters = 'uid=%s&quota-type=%s' % (uid, quota_type)
        return self.request('get', '/%s/user?quota&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def get_user_quota(self, uid):
        return self.get_quota(uid=uid, quota_type='user')

    def get_user_bucket_quota(self, uid):
        '''Return the quota set on every bucket owned/created by a user'''
        return self.get_quota(uid=uid, quota_type='bucket')

    def set_quota(self, uid, quota_type, max_size_kb=None, max_objects=None,
                  enabled=None):
        if quota_type not in ['user', 'bucket']:
            raise InvalidQuotaType
        parameters = 'uid=%s&quota-type=%s' % (uid, quota_type)
        if max_size_kb is not None:
            parameters += '&max-size-kb=%d' % max_size_kb
        if max_objects is not None:
            parameters += '&max-objects=%d' % max_objects
        if enabled is not None:
            parameters += '&enabled=%s' % str(enabled).lower()
        return self.request('put', '/%s/user?quota&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_user(self, uid, purge_data=False):
        parameters = 'uid=%s' % uid
        parameters += '&purge-data=%s' % purge_data
        return self.request('delete', '/%s/user?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def create_subuser(self, uid, subuser=None, secret_key=None,
                       access_key=None, key_type=None, access=None,
                       generate_secret=False):
        parameters = 'uid=%s' % uid
        if subuser is not None:
            parameters += '&subuser=%s' % subuser
        if secret_key is not None and access_key is not None:
            parameters += '&access-key=%s' % access_key
            parameters += '&secret-key=%s' % secret_key
        if key_type is not None and key_type.lower() in ['s3', 'swift']:
            parameters += '&key-type=%s' % key_type
        if access is not None:
            parameters += '&access=%s' % access
        if generate_secret:
            parameters += '&generate-secret=%s' % generate_secret
        return self.request('put', '/%s/user?subuser&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def modify_subuser(self, uid, subuser, secret=None, key_type='swift',
                       access=None, generate_secret=False):
        parameters = 'uid=%s&subuser=%s' % (uid, subuser)
        if secret is not None:
            parameters += '&secret=%s' % secret
        parameters += '&key-type=%s' % key_type
        if access is not None:
            parameters += '&access=%s' % access
        parameters += '&generate-secret=%s' % generate_secret
        return self.request('post', '/%s/user?subuser&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_subuser(self, uid, subuser, purge_keys=True):
        parameters = 'uid=%s&subuser=%s&purge-keys=%s' % (uid, subuser,
                                                          purge_keys)
        return self.request('delete', '/%s/user?subuser&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def create_key(self, uid, subuser=None, key_type='s3', access_key=None,
                   secret_key=None, generate_key=True):
        parameters = 'uid=%s' % uid
        if subuser is not None:
            parameters += '&subuser=%s' % subuser
        parameters += '&key-type=%s' % key_type
        if access_key is not None:
            parameters += '&access-key=%s' % access_key
        if secret_key is not None:
            parameters += '&secret-key=%s' % secret_key
        parameters += '&generate-key=%s' % generate_key
        return self.request('put', '/%s/user?key&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_key(self, access_key, key_type=None, uid=None, subuser=None):
        parameters = 'access-key=%s' % (access_key)
        if key_type is not None:
            parameters += '&key-type=%s' % key_type
        if uid is not None:
            parameters += '&uid=%s' % uid
        if subuser is not None:
            parameters += '&subuser=%s' % subuser
        return self.request('delete', '/%s/user?key&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def get_bucket(self, bucket=None, uid=None, stats=False):
        parameters = ''
        if bucket is not None:
            parameters += '&bucket=%s' % bucket
        if uid is not None:
            parameters += '&uid=%s' % uid
        parameters += '&stats=%s' % stats
        return self.request('get', '/%s/bucket?format=%s%s' %
                            (self._admin, self._response, parameters))

    def check_bucket_index(self, bucket, check_objects=False, fix=False):
        parameters = 'bucket=%s' % bucket
        parameters += '&check-objects=%s' % check_objects
        parameters += '&fix=%s' % fix
        return self.request('get', '/%s/bucket?index&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def create_bucket(self, bucket):
        return self.request('put', '/%s' % bucket)

    def remove_bucket(self, bucket, purge_objects=False):
        parameters = 'bucket=%s' % bucket
        parameters += '&purge-objects=%s' % purge_objects
        return self.request('delete', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def unlink_bucket(self, bucket, uid):
        parameters = 'bucket=%s&uid=%s' % (bucket, uid)
        return self.request('post', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def link_bucket(self, bucket, bucket_id, uid):
        parameters = 'bucket=%s&bucket-id=%s&uid=%s' % \
            (bucket, bucket_id, uid)
        return self.request('put', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_object(self, bucket, object_name):
        parameters = 'bucket=%s&object=%s' % (bucket, object_name)
        return self.request('delete', '/%s/bucket?object&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def get_policy(self, bucket, object_name=None):
        parameters = 'bucket=%s' % bucket
        if object_name is not None:
            parameters += '&object=%s' % object_name
        return self.request('get', '/%s/bucket?policy&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def add_capability(self, uid, user_caps):
        parameters = 'uid=%s&user-caps=%s' % (uid, user_caps)
        return self.request('put', '/%s/user?caps&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_capability(self, uid, user_caps):
        parameters = 'uid=%s&user-caps=%s' % (uid, user_caps)
        return self.request('delete', '/%s/user?caps&format=%s&%s' %
                            (self._admin, self._response, parameters))

    @staticmethod
    def parse_rados_datestring(s):
        return time.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")

    @staticmethod
    def gen_secret_key(size=40, chars=string.letters + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
