import time
import json
from io import StringIO
import logging
import string
import random

from typing import Optional, Dict
from typing import ClassVar, Union

import requests
from requests_aws4auth import AWS4Auth

from urllib.parse import quote
from .exceptions import (
    RGWAdminException, AccessDenied, UserAlreadyExists,
    InvalidAccessKey, InvalidSecretKey, InvalidKeyType,
    KeyExists, EmailExists, SubuserExists, InvalidAccess,
    IndexRepairFailed, BucketNotEmpty, ObjectRemovalFailed,
    BucketUnlinkFailed, BucketLinkFailed, NoSuchObject,
    IncompleteBody, InvalidCap, NoSuchCap,
    InternalError, NoSuchUser, NoSuchBucket, NoSuchKey,
    ServerDown, InvalidQuotaType, InvalidArgument, BucketAlreadyExists
)

log = logging.getLogger(__name__)
LETTERS = string.ascii_letters


class RGWAdmin:
    _access_key: str
    _secret_key: str
    _server: str
    _admin: str
    _response: str
    _ca_bundle: str
    _verify: bool
    _protocol: str
    _timeout: int

    connection: ClassVar['RGWAdmin']

    metadata_types = ['user', 'bucket', 'bucket.instance']

    def __init__(self, access_key, secret_key, server,
                 admin='admin', response='json', ca_bundle=None,
                 secure=True, verify=True, timeout=None, pool_connections=False):
        self._access_key = access_key
        self._secret_key = secret_key
        self._server = server
        self._admin = admin
        self._response = response
        self._session = None

        # ssl support
        self._ca_bundle = ca_bundle
        self._verify = verify
        if secure:
            self._protocol = 'https'
        else:
            self._protocol = 'http'

        self._timeout = timeout

        if pool_connections:
            self._session = requests.Session()

    @classmethod
    def connect(cls, **kwargs):
        """Establish a new connection to RGWAdmin

        Only one connection can be active in any single process
        """
        cls.set_connection(RGWAdmin(**kwargs))

    @classmethod
    def set_connection(cls, connection: 'RGWAdmin'):
        """Set a connection for the RGWAdmin session to use."""
        cls.connection = connection

    @classmethod
    def get_connection(cls) -> 'RGWAdmin':
        """Return the RGWAdmin connection that was set"""
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

    def get_base_url(self) -> str:
        '''Return a base URL.  I.e. https://ceph.server'''
        return '%s://%s' % (self._protocol, self._server)

    def _load_request(self, r):
        '''Load the request given as JSON handling exceptions if necessary'''
        try:
            j = r.json()
        except ValueError:
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
                code = str(j.get('Code', 'InternalError'))
            else:
                raise ServerDown(None)
            for e in [AccessDenied, UserAlreadyExists, InvalidAccessKey,
                      InvalidKeyType, InvalidSecretKey, KeyExists, EmailExists,
                      SubuserExists, InvalidAccess, InvalidArgument,
                      IndexRepairFailed, BucketNotEmpty, ObjectRemovalFailed,
                      BucketUnlinkFailed, BucketLinkFailed, NoSuchObject,
                      InvalidCap, NoSuchCap, NoSuchUser, NoSuchBucket,
                      NoSuchKey, IncompleteBody, BucketAlreadyExists,
                      InternalError]:
                if code == e.__name__:
                    raise e(j)
            raise RGWAdminException(code, raw=j)

    def request(self, method, request, headers: Optional[Dict] = None, data=None):
        url = '%s%s' % (self.get_base_url(), request)
        # add host request header
        if headers:
            headers['host'] = self._server
        else:
            headers = {'host': self._server}
        
        log.debug('URL: %s' % url)
        log.debug('Access Key: %s' % self._access_key)
        log.debug('Verify: %s  CA Bundle: %s' % (self._verify,
                                                 self._ca_bundle))
        try:
            if self._session:
                # use connection pool
                m = getattr(self._session, method.lower())
            else:
                # do not use connection pool
                m = getattr(requests, method.lower())
            verify: Union[bool, str, None] = None
            if self._ca_bundle:
                verify = self._ca_bundle
            else:
                verify = self._verify
            auth = AWS4Auth(self._access_key, self._secret_key, 'nowhere', 's3')
            r = m(url, headers=headers, auth=auth, verify=verify, data=data,
                  timeout=self._timeout)
        except Exception as e:
            raise e
        return self._load_request(r)

    def _request_metadata(self, method, metadata_type, params=None,
                          headers=None, data=None):
        if metadata_type not in self.metadata_types:
            raise Exception("Bad metadata_type")

        if params is None:
            params = {}
        params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        request = '/%s/metadata/%s?%s' % (self._admin, metadata_type, params)
        return self.request(
            method=method,
            request=request,
            headers=headers,
            data=data
        )

    def get_metadata(self, metadata_type, key=None, max_entries=None,
                     marker=None, headers=None):
        ''' Returns a JSON object representation of the metadata '''
        params = {'format': self._response}
        if key is not None:
            params['key'] = key
        if marker is not None:
            params['marker'] = quote(marker)
        if max_entries is not None:
            params['max-entries'] = max_entries
        return self._request_metadata(
            method='get',
            metadata_type=metadata_type,
            params=params,
            headers=headers,
        )

    def put_metadata(self, metadata_type, key, json_string):
        return self._request_metadata(
            method='put',
            metadata_type=metadata_type,
            params={'key': key},
            headers={'Content-Type': 'application/json'},
            data=json_string)

    # Alias for compatability:
    set_metadata = put_metadata

    def delete_metadata(self, metadata_type, key):
        return self._request_metadata(
            method='delete',
            metadata_type=metadata_type,
            params={'key': key},
        )

    def lock_metadata(self, metadata_type, key, lock_id, length):
        params = {
            'lock': 'lock',
            'key': key,
            'lock_id': lock_id,
            'length': int(length),
        }
        return self._request_metadata(
            method='post',
            metadata_type=metadata_type,
            params=params,
        )

    def unlock_metadata(self, metadata_type: str, key, lock_id):
        params = {
            'unlock': 'unlock',
            'key': key,
            'lock_id': lock_id,
        }
        return self._request_metadata(
            method='post',
            metadata_type=metadata_type,
            params=params,
        )

    def get_user(self, uid: Optional[str] = None, access_key: Optional[str] = None, stats=False,
                 sync=False):
        if uid is not None and access_key is not None:
            raise ValueError('Only one of uid and access_key is allowed')
        parameters = ''
        if uid is not None:
            parameters += '&uid=%s' % uid
        if access_key is not None:
            parameters += '&access-key=%s' % access_key
        parameters += '&stats=%s&sync=%s' % (stats, sync)
        return self.request('get', '/%s/user?format=%s%s' %
                            (self._admin, self._response, parameters))

    def get_users(self):
        return self.get_metadata(metadata_type='user')

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
                    generate_key=False, max_buckets=None, suspended=None, placement_tags=None):
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
        if suspended is not None:
            parameters += '&suspended=%s' % suspended
        if placement_tags is not None:
            parameters += '&placement-tags=%s' % placement_tags
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

    @staticmethod
    def _quota(max_size_kb=None, max_objects=None, enabled=None):
        quota = ''
        if max_size_kb is not None:
            quota += '&max-size-kb=%d' % max_size_kb
        if max_objects is not None:
            quota += '&max-objects=%d' % max_objects
        if enabled is not None:
            quota += '&enabled=%s' % str(enabled).lower()
        return quota

    def set_user_quota(self, uid, quota_type, max_size_kb=None,
                       max_objects=None, enabled=None):
        '''
        Set quotas on users and buckets owned by users

        If `quota_type` is user, then the quota applies to the user.  If
        `quota_type` is bucket, then the quota applies to buckets owned by
        the specified uid.

        If you want to set a quota on an individual bucket, then use
        set_bucket_quota() instead.
        '''
        if quota_type not in ['user', 'bucket']:
            raise InvalidQuotaType
        quota = self._quota(max_size_kb=max_size_kb, max_objects=max_objects,
                            enabled=enabled)
        parameters = 'uid=%s&quota-type=%s%s' % (uid, quota_type, quota)
        return self.request('put', '/%s/user?quota&format=%s&%s' %
                            (self._admin, self._response, parameters))

    def set_bucket_quota(self, uid, bucket, max_size_kb=None,
                         max_objects=None, enabled=None):
        '''Set the quota on an individual bucket'''
        quota = self._quota(max_size_kb=max_size_kb, max_objects=max_objects,
                            enabled=enabled)
        parameters = 'uid=%s&bucket=%s%s' % (uid, bucket, quota)
        return self.request('put', '/%s/bucket?quota&format=%s&%s' %
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
        parameters += '&generate-secret=%s' % generate_secret
        return self.request('put', '/%s/user?format=%s&%s' %
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
        return self.request('post', '/%s/user?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_subuser(self, uid, subuser, purge_keys=True):
        parameters = 'uid=%s&subuser=%s&purge-keys=%s' % (uid, subuser,
                                                          purge_keys)
        return self.request('delete', '/%s/user?format=%s&%s' %
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

    def get_buckets(self):
        '''Returns a list of all buckets in the radosgw'''
        return self.get_metadata(metadata_type='bucket')

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

    def remove_bucket(self, bucket, purge_objects=False):
        parameters = 'bucket=%s' % bucket
        parameters += '&purge-objects=%s' % purge_objects
        return self.request('delete', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def unlink_bucket(self, bucket, uid):
        parameters = 'bucket=%s&uid=%s' % (bucket, uid)
        return self.request('post', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def link_bucket(self, bucket, uid, bucket_id=None, new_bucket_name=None):
        parameters = 'bucket=%s' % bucket
        parameters += '&uid=%s' % uid
        if bucket_id is not None:
            parameters += '&bucket-id=%s' % bucket_id
        if new_bucket_name is not None:
            parameters += '&new-bucket-name=%s' % new_bucket_name
        return self.request('put', '/%s/bucket?format=%s&%s' %
                            (self._admin, self._response, parameters))

    def remove_object(self, bucket, object_name):
        parameters = 'bucket=%s&object=%s' % (bucket, object_name)
        return self.request('delete', '/%s/bucket?format=%s&%s' %
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

    def get_bucket_instances(self):
        '''Returns a list of all bucket instances in the radosgw'''
        return self.get_metadata(metadata_type='bucket.instance')

    @staticmethod
    def parse_rados_datestring(s):
        return time.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def gen_secret_key(size=40, chars=LETTERS + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
