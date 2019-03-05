def create_bucket(rgw, bucket=None):
    """
    This is a helper function for tests to create buckets so they can assert changes
    on the gateway based on the bucket's existence.

    NOTE: The PUT /:bucket endpoint is not part of the Admin Ops API, and therefore
    is not included in the rgw class.  The response format does not match other
    Admin Operations, and it is largely incompatible with the rgw class.
    """
    return rgw.request('put', '/%s' % bucket)
