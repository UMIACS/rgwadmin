# RadosGWAdmin

This is a Python library to allow access to the Ceph Object Storage Admin API.

http://docs.ceph.com/docs/master/radosgw/adminops/

## Example Usage

```python
from rgwadmin import RGWAdmin

rgw = RGWAdmin(access_key='XXX', secret_key='XXX', server='obj.example.com')
rgw.create_user(
    uid='liam',
    display_name='Liam Monahan',
    email='liam@umiacs.umd.edu',
    user_caps='usage=read, write; users=read',
    max_buckets=1000)
rgw.set_quota(
    uid='liam',
    quota_type='user',
    max_size_kb=1024*1024,
    enabled=True)
rgw.remove_user(uid='liam', purge_data=True)
```

## Requirements

rgwadmin requires the following Python packages:

 * [requests](http://python-requests.org/)
 * [requests-aws](https://github.com/tax/python-requests-aws)

Additionally, you need to have a [Ceph](http://www.ceph.org) Object Storage instance with a user that has appropriate caps (capabilities) on the parts of the API that you want to access.  See the [Ceph Object Storage](http://docs.ceph.com/docs/master/radosgw/) page for more information.

## Installation

```pip install rgwadmin```
