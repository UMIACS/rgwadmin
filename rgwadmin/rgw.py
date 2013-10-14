import time
import json
from StringIO import StringIO
import requests
import logging
import string
import random
from awsauth import S3Auth

from .exceptions import (
    RGWAdminException, AccessDenied, UserExists,
    InvalidAccessKey, InvalidSecretKey, InvalidKeyType,
    KeyExists, EmailExists, SubuserExists, InvalidAccess,
    IndexRepairFailed, BucketNotEmpty, ObjectRemovalFailed,
    BucketUnlinkFailed, BucketLinkFailed, NoSuchObject,
    IncompleteBody, InvalidCap, NoSuchCap,
    InternalError, NoSuchUser, NoSuchBucket, NoSuchKey
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
        ## ssl support
        self._ca_bundle = ca_bundle
        self._verify = verify
        if secure:
            self._protocol = 'https'
        else:
            self._protocol = 'http'
        self._response = response

    def request(self, method, request, data=None):
        url = '%s://%s%s' % (self._protocol,
                             self._server,
                             request)
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
            r = m(url, auth=S3Auth(self._access_key,
                  self._secret_key, self._server),
                  verify=verify)
        except Exception as e:
            log.exception(e)
            return None
        try:
            j = json.load(StringIO(r.content))
        except ValueError as e:
            log.info(e)
            j = None
        if r.status_code == requests.codes.ok:
            return j
        else:
            log.error(j)
            code = str(j['Code'])
            if code == 'AccessDenied':
                raise AccessDenied
            if code == 'UserExists':
                raise UserExists
            if code == 'InvalidAccessKey':
                raise InvalidAccessKey
            if code == 'InvalidKeyType':
                raise InvalidKeyType
            if code == 'InvalidSecretKey':
                raise InvalidSecretKey
            if code == 'KeyExists':
                raise KeyExists
            if code == 'EmailExists':
                raise EmailExists
            if code == 'SubuserExists':
                raise SubuserExists
            if code == 'InvalidAccess':
                raise InvalidAccess
            if code == 'IndexRepairFailed':
                raise IndexRepairFailed
            if code == 'BucketNotEmpty':
                raise BucketNotEmpty
            if code == 'ObjectRemovalFailed':
                raise ObjectRemovalFailed
            if code == 'BucketUnlinkFailed':
                raise BucketUnlinkFailed
            if code == 'BucketLinkFailed':
                raise BucketLinkFailed
            if code == 'NoSuchObject':
                raise NoSuchObject
            if code == 'IncompleteBody':
                raise IncompleteBody
            if code == 'InvalidCap':
                raise InvalidCap
            if code == 'NoSuchCap':
                raise NoSuchCap
            if code == 'InternalError':
                raise InternalError
            if code == 'NoSuchUser':
                raise NoSuchUser
            if code == 'NoSuchBucket':
                raise NoSuchBucket
            if code == 'NoSuchKey':
                raise NoSuchKey
            raise RGWAdminException

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

    def remove_user(self, uid, purge_data=False):
        parameters = 'uid=%s' % uid
        parameters += '&purge-data=%s' % purge_data
        return self.request('delete', '/%s/user?format%s&%s' %
                            (self._admin, self._response, parameters))

    def create_subuser(self, uid, subuser=None, secret_key=None,
                       key_type='s3', access=None, generate_secret=False):
        parameters = 'uid=%s' % uid
        if subuser is not None:
            parameters += '&subuser=%s' % subuser
        if secret_key is not None:
            parameters += '&secret-key=%s' % secret_key
        parameters += '&key-type=%s' % key_type
        if access is not None:
            parameters += '&access=%s' % access
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

    def remove_key(self, access_key, key_type, uid=None, subuser=None):
        parameters = 'access-key=%s&key-type=%s' % (access_key, key_type)
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
        return self.request('delete', '/%s/bucket&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def unlink_bucket(self, bucket, uid):
        parameters = 'bucket=%s&uid=%s' % (bucket, uid)
        return self.request('post', '/%s/bucket&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def link_bucket(self, bucket, uid):
        parameters = 'bucket=%s&uid=%s' % (bucket, uid)
        return self.request('put', '/%s/bucket&format=%s&%s' %
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
        return self.request('delete', '/%s/user?caps&format=%s&%s' %
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
