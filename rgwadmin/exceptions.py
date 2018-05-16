"""
rgwadmin.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the rgwadmin exceptions.

"""


class RGWAdminException(Exception):
    """There was a unlabeled exception that was raised during your request"""
    def __init__(self, code, raw=None):
        self.code = code
        self.raw = raw


class AccessDenied(RGWAdminException):
    """Access was denied for the request."""


class UserExists(RGWAdminException):
    """Attempt to create existing user."""


class InvalidAccessKey(RGWAdminException):
    """Invalid access key specified."""


class InvalidArgument(RGWAdminException):
    """Invalid argument specified."""


class InvalidKeyType(RGWAdminException):
    """Invalid key type specified."""


class InvalidSecretKey(RGWAdminException):
    """Invalid secret key specified."""


class KeyExists(RGWAdminException):
    """Provided access key exists and belongs to another user."""


class EmailExists(RGWAdminException):
    """Provided email address exists."""


class SubuserExists(RGWAdminException):
    """Specified subuser exists."""


class InvalidAccess(RGWAdminException):
    """Invalid subuser access specified."""


class IndexRepairFailed(RGWAdminException):
    """Bucket index repair failed."""


class BucketNotEmpty(RGWAdminException):
    """Attempted to delete non-empty bucket."""


class ObjectRemovalFailed(RGWAdminException):
    """Unable to remove objects."""


class BucketUnlinkFailed(RGWAdminException):
    """Unable to unlink bucket from specified user."""


class BucketLinkFailed(RGWAdminException):
    """Unable to link bucket to specified user."""


class NoSuchObject(RGWAdminException):
    """Specified object does not exist."""


class IncompleteBody(RGWAdminException):
    """Either bucket was not specified for a bucket policy request or bucket
       and object were not specified for an object policy request."""


class InvalidCap(RGWAdminException):
    """Attempt to grant invalid admin capability."""


class NoSuchCap(RGWAdminException):
    """User does not possess specified capability."""


class InternalError(RGWAdminException):
    """Internal server error."""


class NoSuchUser(RGWAdminException):
    """User does not exist."""


class NoSuchBucket(RGWAdminException):
    """Bucket does not exist."""


class NoSuchKey(RGWAdminException):
    """No such access key."""


class ServerDown(RGWAdminException):
    """The backing server is not available."""


class InvalidQuotaType(RGWAdminException):
    """You must specify either a 'user' or 'bucket' quota type"""


class BucketAlreadyExists(RGWAdminException):
    """The bucket already exists"""
