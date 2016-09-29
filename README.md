# RadosGWAdmin

This is a Python library to allow access to the Ceph Object Storage Admin API.

http://docs.ceph.com/docs/master/radosgw/adminops/


## API Example Usage

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

## User Example Usage
```python
from rgwadmin import RGWAdmin, RGWUser

RGWAdmin.connect(access_key='XXX', secret_key='XXX', server='obj.example.com')
u = RGWUser.create(user_id='test', display_name='Test User')
u.user_quota.size = 1024 * 1024  # in bytes
u.user_quota.enabled = True
u.save()
u.delete()
```

## Requirements

rgwadmin requires the following Python packages:

 * [requests](http://python-requests.org/)
 * [requests-aws](https://github.com/tax/python-requests-aws)

 If you are running python < 2.7 you will need a backport of collections
 ordereddict.
 * [ordereddict](https://pypi.python.org/pypi/ordereddict)

Additionally, you need to have a [Ceph](http://www.ceph.org) Object Storage
instance with a user that has appropriate caps (capabilities) on the parts of
the API that you want to access.  See the
[Ceph Object Storage](http://docs.ceph.com/docs/master/radosgw/) page for more
information.

### Compatibility
The API for different versions of Ceph RadosGW has changed over time.  While we
endeavor to be compatible with as many versions of Ceph RadosGW there will be
some issues that crop up over time.  We only consider the LTS versions but
these are what we have tested on.

* 1.0.5 <= Firefly
* 1.0.6 > Firefly/Hammer
* 1.1 > Hammer
* 1.1.5 > Jewel

## Installation

```pip install rgwadmin```


## License

    rgwadmin - a Python interface to the Rados Gateway Admin API
    Copyright (C) 2015  UMIACS

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

    Email:
        github@umiacs.umd.edu
