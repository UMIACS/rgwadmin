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
