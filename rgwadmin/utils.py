import os
import string
import random


def random_password(size=40, chars=None):
    '''Return a random password string.

    The default length is 32 characters.  Different character classes can be
    passed in, but the default draws from ASCII uppercase, lowercase, and
    digits.

    Uses the SystemRamdom to ensure you get a trustworty entropy pool.
    '''
    if chars is None:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    random_chars = random.SystemRandom().choice
    return ''.join(random_chars(chars) for _ in range(size))


def get_environment_creds():
    secure = os.environ.get('OBJ_SERVER_SECURE', True)
    if secure is not True and secure == 'false':
        secure = False
    verify = os.environ.get('OBJ_SERVER_VERIFY', True)
    if verify is not True and verify == 'false':
        verify = False
    return {'access_key': os.environ['OBJ_ACCESS_KEY_ID'],
            'secret_key': os.environ['OBJ_SECRET_ACCESS_KEY'],
            'server': os.environ['OBJ_SERVER'],
            'port': os.environ.get('OBJ_SERVER_PORT', 443),
            'secure': secure,
            'verify': verify}


def id_generator(size=6, chars=None):
    if chars is None:
        chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    letter = random.choice(string.ascii_lowercase)
    return letter + ''.join(random.choice(chars) for x in range(size))
