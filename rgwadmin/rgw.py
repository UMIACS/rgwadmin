import sys
import json
from StringIO import StringIO
import requests
import logging
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

    def __init__(self, access_key, secret_key, server, secure=False,
                 response='json'):
        self._access_key = access_key
        self._secret_key = secret_key
        self._server = server
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
        log.debug('Secret Key: %s' % self._secret_key)
        try:
            m = getattr(requests, method.lower())
            r = m(url, auth=S3Auth(self._access_key,
                     self._secret_key, self._server))
        except Exception as e:
            log.exception(e)
            sys.exit(1)
        j = json.load(StringIO(r.content)) 
        if r.status_code == requests.codes.ok:
            return j
        else:
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

    def get_user(self, user):
        return self.request('get', '/admin/user?format=%s&uid=%s' %
                            (self._response, user))

    def get_users(self):
        return self.request('get', '/admin/metadata/user?format=%s' %
                            self._response) 

    def create_user(self, user, display_name, email=None, key_type=None,
                   access_key=None, secret_key=None, user_caps=None,
                   generate_key=True, max_buckets=None, suspended=False):
        parameters = 'uid=%s&display-name=%s' % (user, display_name)
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
        return self.request('put', '/admin/user?format=%s&%s' % 
                            (self._response, parameters))
