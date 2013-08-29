import sys
import json
from StringIO import StringIO
import requests
import logging
from awsauth import S3Auth

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
        try:
            url = '%s://%s%s' % (self._protocol,
                                 self._server,
                                 request)
            log.debug('URL: %s' % url)
            log.debug('Access Key: %s' % self._access_key)
            log.debug('Secret Key: %s' % self._secret_key)
            m = getattr(requests, method.lower())
            return m(url, auth=S3Auth(self._access_key,
                     self._secret_key, self._server))
        except Exception as e:
            log.exception(e)
            sys.exit(1)

    def get_user(self, user):
        r = self.request('get', '/admin/user?format=%s&uid=%s' %
                         (self._response, user))
        return json.load(StringIO(r.content))

    def get_users(self):
        r = self.request('get', '/admin/metadata/user?format=%s' %
                         self._response) 
        return json.load(StringIO(r.content))

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
        r = self.request('put', '/admin/user?format=%s&%s' % 
                         (self._response, parameters))
        return json.load(StringIO(r.content)) 
