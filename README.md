# RadosGWAdmin

This is a Python library to allow access to the Ceph Object Storage admin API.

http://ceph.com/docs/master/radosgw/adminops/

## Requirements
The following python modules are a required to run radosgw-admin.

 * [requests](http://python-requests.org/)
 * [requests-aws](https://github.com/tax/python-requests-aws)

Both of these can be installed via simple pip command.

    pip install requests-aws

Additionally you need to have a [Ceph](http://www.ceph.org) Ceph Object Storage instance with a user that has appropriate caps (capabilties) on the parts of the API that you want to access.  See the [Ceph Object Storage](http://ceph.com/docs/master/radosgw/) page for more information.
