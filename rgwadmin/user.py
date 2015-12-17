import logging
from qav.listpack import ListPack
from copy import copy
from .utils import random_password
from .rgw import RGWAdmin
from .exceptions import NoSuchKey

log = logging.getLogger(__name__)


class RGWCap(object):
    def __init__(self, type, perm):
        self.type = type
        self.perm = perm

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.type))


class RGWKey(object):
    def __init__(self, user, access_key, secret_key):
        self.user = user
        self.access_key = access_key
        self.secret_key = secret_key

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.user))

    @staticmethod
    def generate(user, access_size=20, secret_size=40):
        access_key = random_password(size=access_size)
        secret_key = random_password(size=secret_size)
        return RGWKey(user, access_key, secret_key)


class RGWSubuser(object):
    def __init__(self, id, permissions):
        self.id = id
        self.permissions = permissions

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.id))


class RGWSwiftKey(object):
    def __init__(self, user, secret_key):
        self.user = user
        self.secret_key = secret_key

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.user))

    @staticmethod
    def generate(user, secret_size=40):
        secret_key = random_password(size=secret_size)
        return RGWSwiftKey(user, secret_key)


class RGWUser(object):
    attributes = ['user_id', 'display_name', 'email', 'caps', 'keys',
                  'max_buckets', 'suspended', 'swift_keys', 'subusers']
    subclasses = [RGWCap, RGWKey, RGWSubuser, RGWSwiftKey]
    """Representation of a RadosGW User"""
    def __init__(self, user_id, display_name, email=None, caps=None,
                 keys=None, max_buckets=1000, suspended=0, swift_keys=None,
                 subusers=None):
        self.user_id = user_id
        self.display_name = display_name
        self.email = email
        if caps is [] or caps is None:
            self.caps = []
        else:
            self.caps = caps
        if keys is [] or keys is None:
            self.keys = []
        else:
            self.keys = keys
        self.max_buckets = max_buckets
        self.suspended = suspended
        if swift_keys is [] or swift_keys is None:
            self.swift_keys = []
        else:
            self.swift_keys = swift_keys
        if subusers is [] or subusers is None:
            self.subusers = []
        else:
            self.subusers = subusers

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.user_id))

    def __str__(self):
        print ListPack(map(lambda x: (x, self.x), self.attributes))

    def diff(self):
        d = {}
        current = self.to_hash()
        try:
            existing = RGWUser.fetch(self.user_id).to_hash()
        except NoSuchKey:
            return current
        for k in current.keys():
            if k in existing.keys():
                if current[k] != existing[k]:
                    d[k] = (existing[k], current[k])
        return d

    def save(self):
        rgw = RGWAdmin.get_connection()
        try:
            RGWUser.fetch(self.user_id)
            rgw.modify_user(self.user_id, **self.to_hash(subclasses=False))
        except NoSuchKey:
            rgw.create_user(self.to_hash(subclasses=False))

    @classmethod
    def list(cls):
        rgw = RGWAdmin.get_connection()
        return map(lambda x: cls._parse_user(rgw.get_user(x)), rgw.get_users())

    @classmethod
    def fetch(cls, user):
        rgw = RGWAdmin.get_connection()
        return cls._parse_user(rgw.get_user(user))

    @classmethod
    def _parse_user(cls, rgw_user):
        # we expect to be passed a dict
        if type(rgw_user) is not dict:
            print 'no dict'
            return None
        # check to make sure we have all the correct keys
        if not set(map(lambda x: unicode(x), cls.attributes)) <= \
                set(rgw_user.keys()):
            return None
        log.info('Parsing RGWUser %s' % rgw_user)
        # load keys into RGWKey objects
        keys = map(lambda x: RGWKey(**x), rgw_user['keys'])
        # load caps into RGWCap objects
        caps = map(lambda x: RGWCap(**x), rgw_user['caps'])
        # load subusers into RGWSubuser objects
        subusers = map(lambda x: RGWSubuser(**x), rgw_user['subusers'])
        # load swift_keys into RGWSwiftKey objects
        swift_keys = map(lambda x: RGWSwiftKey(**x), rgw_user['swift_keys'])
        rgw_user['keys'] = keys
        rgw_user['caps'] = caps
        rgw_user['subusers'] = subusers
        rgw_user['swift_keys'] = swift_keys
        return RGWUser(**rgw_user)

    def to_hash(self, subclasses=True):
        '''Return the hash representation of the object'''
        rgw_user = copy(self.__dict__)
        for attr in rgw_user.keys():
            if type(rgw_user[attr]) is list and subclasses:
                attr_list = []
                for x in rgw_user[attr]:
                    if type(x) in self.subclasses:
                        attr_list.append(x.__dict__)
                rgw_user[attr] = attr_list
        return rgw_user
