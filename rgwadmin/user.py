import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import json
from .utils import random_password
from .rgw import RGWAdmin
from .exceptions import NoSuchKey

log = logging.getLogger(__name__)


class AttributeMixin(object):
    attrs = []

    def __str__(self):
        try:
            from qav.listpack import ListPack
        except:
            return str(self.to_tuples())
        return str(ListPack(self.to_tuples()))

    def to_tuples(self):
        return map(lambda x: (x, getattr(self, x)), self.attrs)

    def to_dict(self):
        return dict(self.to_tuples())


class RGWCap(AttributeMixin):
    attrs = ['type', 'perm']

    def __init__(self, type, perm):
        self.type = type
        self.perm = perm

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.type))


class RGWKey(AttributeMixin):
    attrs = ['user', 'access_key', 'secret_key']

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


class RGWSubuser(AttributeMixin):
    attrs = ['id', 'permissions']
    permission_list = ['read', 'write', 'readwrite', 'full']

    def __init__(self, id, permissions):
        self.id = id
        self.permissions = permissions

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.id))

    @property
    def permissions(self):
        return self._permissions

    @permissions.setter
    def permissions(self, value):
        if value in self.permission_list:
            self._permissions = value
        elif value == '<none>':
            self._permissions = None
        else:
            raise AttributeError


class RGWSwiftKey(AttributeMixin):
    attrs = ['user', 'secret_key']

    def __init__(self, user, secret_key):
        self.user = user
        self.secret_key = secret_key

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.user))

    @staticmethod
    def generate(user, secret_size=40):
        secret_key = random_password(size=secret_size)
        return RGWSwiftKey(user, secret_key)


class RGWQuota(AttributeMixin):
    attrs = ['enabled', 'max_objects', 'max_size_kb']
    defaults = OrderedDict([('enabled', False),
                            ('max_objects', -1),
                            ('max_size_kb', -1)])

    def __init__(self, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs[attr])

    def __repr__(self):
        return '%s %s/%s' % (self.enabled, self.max_objects,
                             self.string_size())

    def string_size(self):
        weights = ['KB', 'MB', 'GB', 'TB', 'PB']
        size = int(self.max_size_kb)
        weight = 0
        if size < 0:
            return size
        while True:
            if size < 1024 or weight == len(weights):
                return str('%s%s' % (size, weights[weight]))
            else:
                size = size / 1024
                weight += 1

    @classmethod
    def default(cls):
        return cls(**cls.defaults)

    @property
    def size(self):
        return int(self.max_size_kb) * 1000

    @size.setter
    def size(self, new_size):
        self.max_size_kb = int(new_size) / 1000


class RGWUser(AttributeMixin):
    attrs = ['user_id', 'display_name', 'email', 'caps', 'keys',
             'max_buckets', 'suspended', 'swift_keys', 'subusers',
             'placement_tags', 'auid', 'bucket_quota', 'user_quota',
             'default_placement', 'op_mask', 'temp_url_keys']
    sub_attrs = OrderedDict([('caps', RGWCap),
                             ('keys', RGWKey),
                             ('swift_keys', RGWSwiftKey),
                             ('subusers', RGWSubuser),
                             ('bucket_quota', RGWQuota),
                             ('user_quota', RGWQuota)])

    """Representation of a RadosGW User"""
    def __init__(self, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs[attr])

    def __repr__(self):
        return str('%s %s' % (self.__class__.__name__, self.user_id))

    @classmethod
    def create(cls, user_id, display_name, **kwargs):
        rgw = RGWAdmin.get_connection()
        rgw.create_user(uid=user_id,
                        display_name=display_name,
                        **kwargs)
        return cls.fetch(user_id)

    def diff(self):
        rgw = RGWAdmin.get_connection()
        d = {}
        current = self.to_dict()
        try:
            existing = rgw.get_metadata('user', self.user_id)['data']
        except NoSuchKey:
            logging.info('Unable to fetch the user %s.' % self.user_id)
            return current
        for k in current.keys():
            if k in existing.keys():
                if current[k] != existing[k]:
                    d[k] = (existing[k], current[k])
        return d

    def save(self):
        rgw = RGWAdmin.get_connection()
        try:
            existing = rgw.get_metadata('user', self.user_id)
        except NoSuchKey:
            # create a new user first before we save the full object
            rgw.create_user(user_id=self.user_id,
                            display_name=self.display_name)
        else:
            # only replace the data with our local object
            existing['data'] = self.to_dict()
            log.info('Saving %s' % existing)
            rgw.set_metadata('user', self.user_id, json.dumps(existing))

    def delete(self):
        rgw = RGWAdmin.get_connection()
        try:
            rgw.get_metadata('user', self.user_id)
        except NoSuchKey:
            logging.error('User %s does not exist yet aborting.' %
                          self.user_id)
            return False
        logging.info('Deleting user %s from %s' %
                     (self.user_id, rgw.get_base_url()))
        return rgw.remove_user(uid=self.user_id)

    @classmethod
    def list(cls):
        rgw = RGWAdmin.get_connection()
        return map(lambda x: cls._parse_user(rgw.get_user(x)), rgw.get_users())

    @classmethod
    def fetch(cls, user):
        rgw = RGWAdmin.get_connection()
        try:
            j = rgw.get_metadata('user', user)
        except NoSuchKey:
            return None
        else:
            return cls._parse_user(j['data'])

    @classmethod
    def _parse_user(cls, rgw_user):
        # we expect to be passed a dict
        if type(rgw_user) is not dict:
            print 'no dict'
            return None
        # check to make sure we have all the correct keys
        if not set(map(lambda x: unicode(x), cls.attrs)) <= \
                set(rgw_user.keys()):
            return None
        log.info('Parsing RGWUser %s' % rgw_user)
        for subattr in cls.sub_attrs.keys():
            log.info('Loading attribute %s with class %s' %
                     (subattr, cls.sub_attrs[subattr].__name__))
            if type(rgw_user[subattr]) is list:
                obj = map(lambda x: cls.sub_attrs[subattr](**x),
                          rgw_user[subattr])
            elif type(rgw_user[subattr]) is dict:
                obj = cls.sub_attrs[subattr](**rgw_user[subattr])
            else:
                obj = rgw_user[subattr]
            rgw_user[subattr] = obj
        return RGWUser(**rgw_user)

    def to_dict(self):
        '''Return the dict representation of the object'''
        d = {}
        for attr in self.attrs:
            if attr in self.sub_attrs.keys():
                if type(getattr(self, attr)) is list:
                    d[attr] = []
                    for o in getattr(self, attr):
                        d[attr].append(o.to_dict())
                else:
                    d[attr] = getattr(self, attr).to_dict()
            else:
                d[attr] = getattr(self, attr)
        return d
