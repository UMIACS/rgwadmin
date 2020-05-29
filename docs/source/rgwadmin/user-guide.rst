User Guide
==========

Connecting
----------

To get started, you'll want to connect to your Ceph instance by instantiating
a :class:`~rgwadmin.rgw.RGWAdmin` object.

.. code-block:: python

   from rgwadmin import RGWAdmin

   rgw = RGWAdmin(
       access_key='MY_ACCESS_KEY',
       secret_key='MY_SECRET_KEY',
       server='ceph.example.com')

.. note::
   rgwadmin connects over https by default. To connect over http, pass
   ``secure=False, verify=False``

You can also use :func:`~rgwadmin.utils.get_environment_creds` to pull in
environment variables to form the connection.

.. code-block:: python

   from rgwadmin import RGWAdmin
   from rgwadmin.utils import get_environment_creds

   rgw = RGWAdmin(**get_environment_creds())

The environment variables that it is looking for are ``OBJ_ACCESS_KEY_ID``,
``OBJ_SECRET_ACCESS_KEY``, and ``OBJ_SERVER``.

For a full list of options that can be passed when establishing a connection,
see :func:`~rgwadmin.rgw.RGWAdmin`.

Connection Pooling
~~~~~~~~~~~~~~~~~~~~~~

The ``pool_connections`` option can be passed to enable a tcp connection to be
reused on every request.  There are performance improvements to be had by
enabling connection persistence.  By default this is disabled and a new connection
is formed every time.

The downside to enabling connection pooling is that there is no built-in connection
resumption capability in the library.  If you enable connection pooling you will
need to handle connection resets yourself.  Check your frontend loadbalancer to see
what sort of keepalive settings your rgw server is negotiating.


User Management
---------------

Creating Users
~~~~~~~~~~~~~~

Let's create a new user for ourselves with :func:`~rgwadmin.rgw.RGWAdmin.create_user`.
This will generate an access/secret keypair for the new user by default.

.. code-block:: python

   rgw.create_user(
       uid='liam',
       display_name='Liam Monahan',
       email='liam@umiacs.umd.edu',
       user_caps='usage=read, write; users=read',
       max_buckets=1000)

Get User Details
~~~~~~~~~~~~~~~~

We can fetch a user back by calling :func:`~rgwadmin.rgw.RGWAdmin.get_user`.

.. code-block:: python

   >>> rgw.get_user('liam', stats=True)
   {   'admin': 'false',
    'bucket_quota': {   'check_on_raw': False,
                        'enabled': False,
                        'max_objects': -1,
                        'max_size': -1,
                        'max_size_kb': 0},
    'caps': [],
    'default_placement': '',
    'default_storage_class': '',
    'display_name': 'Liam Monahan',
    'email': 'liam@umiacs.umd.edu',
    'keys': [   {   'access_key': '91C3KDI66JG9ILSJRU5S',
                    'secret_key': '********************',
                    'user': 'liam'}],
    'max_buckets': 1000,
    'mfa_ids': [],
    'op_mask': 'read, write, delete',
    'placement_tags': [],
    'stats': {   'num_objects': 6,
                 'size': 1163924507,
                 'size_actual': 1163931648,
                 'size_kb': 1136646,
                 'size_kb_actual': 1136652,
                 'size_kb_utilized': 0,
                 'size_utilized': 0},
    'subusers': [],
    'suspended': 0,
    'swift_keys': [],
    'system': 'false',
    'temp_url_keys': [],
    'tenant': '',
    'type': 'rgw',
    'user_id': 'liam',
    'user_quota': {   'check_on_raw': False,
                      'enabled': True,
                      'max_objects': -1,
                      'max_size': 1168400384,
                      'max_size_kb': 1141016}}

Modifying Users
~~~~~~~~~~~~~~~

Most attributes about a user can be modified later.

For example, let's suspend our example user:

.. code-block:: python

   rgw.modify_user(uid='liam', suspended=True)

All of the modifications are idempotent.  See
:func:`~rgwadmin.rgw.RGWAdmin.modify_user` for a list of kwargs that
the function accepts. 

Listing Users
~~~~~~~~~~~~~

We can get a list of all users with :func:`~rgwadmin.rgw.RGWAdmin.get_users`.

.. code-block:: python

   >>> rgw.get_users()
   ['liam', 'bob', 'alice']

Removing Users
~~~~~~~~~~~~~~

Delete a user from rgw.  The operation will fail if the user owns data and
``purge_data`` is not set to ``True``.

.. code-block:: python

   rgw.remove_user(uid='liam', purge_data=True)

Add A User Capability
~~~~~~~~~~~~~~~~~~~~~

Add an administrative capability to a specified user.

.. code-block:: python

   >>> rgw.add_capability(
       uid='liam',
       user_caps='usage=read,write;user=write'
   )
   [{'type': 'usage', 'perm': '*'}]

This will return a dict of the user's full set of capabilities.

Remove A User Capability
~~~~~~~~~~~~~~~~~~~~~~~~

Remove an administrative capability from a specified user.

.. code-block:: python

   >>> rgw.remove_capability(
       uid='liam',
       user_caps='usage=read,write;user=write'
   )
   [{'type': 'usage', 'perm': '*'}]

Similarly to adding caps, this call will also return the user's new set of capabilities
as they are after the operation has completed.

Bandwidth Usage
-----

Request bandwidth usage information.

.. note::

   This feature is disabled by default.  It can be enabled by setting
   ``rgw enable usage log = true`` in the appropriate section of ``ceph.conf``.

Trim Usage
~~~~~~~~~~

Remove usage information. With no dates specified, removes all usage information.
More info here: :func:`~rgwadmin.rgw.RGWAdmin.trim_usage`.

.. code-block:: python

   rgw.trim_usage(uid='liam')


Subusers
--------

Subusers can be managed using key types of either S3 or Swift.

Creating Subusers
~~~~~~~~~~~~~~~~~

Let's say that we have a ``webadmin`` user and we want to create a subuser
for liam to have FULL_CONTROL.

.. code-block:: python

   rgw.create_subuser(
       uid='webadmin',
       subuser='liam',
       access='full',
       key_type='s3',
       generate_secret=True,
   )

See the full documentation for :func:`~rgwadmin.rgw.RGWAdmin.create_subuser`. 

Modifying Subusers
~~~~~~~~~~~~~~~~~~

The level of access granted to a subuser can be changed after they are created
with :func:`~rgwadmin.rgw.RGWAdmin.modify_subuser`.
The secret key can be regerated here, too.

.. code-block:: python

   rgw.modify_subuser(
       uid='webadmin',
       subuser='liam',
       access='read',
   )

Removing Subusers
~~~~~~~~~~~~~~~~~

We can remove a subuser by calling  :func:`~rgwadmin.rgw.RGWAdmin.remove_subuser`.

.. note::
   By default this will purge keys.  This is usually what you want.

.. code-block:: python

   rgw.remove_subuser(
       uid='webadmin',
       subuser='liam',
   )


Keys
----

Create Key
~~~~~~~~~~

To create a key on a user:

.. code-block:: python

   rgw.create_key(
       uid='liam',
       key_type='s3',
       generate_key=True)

If you are creating a key for a subuser, you will need to pass in the subuser.

.. code-block:: python

   rgw.create_key(
       uid='webadmin',
       subuser='liam',
       key_type='s3',
       generate_key=True)

.. note::

   The function :func:`~rgwadmin.rgw.RGWAdmin.gen_secret_key` can help generate
   a random string of characters that can be used as a SECRET_KEY.

Remove Key
~~~~~~~~~~

To remove a key using :func:`~rgwadmin.rgw.RGWAdmin.remove_key` it is required
to provide the access-key.  If you are removing a swift key, it is also
necessary to pass the ``key_type='swift'``

.. code-block:: python

   rgw.remove_key(access_key='81C3KDI66FG9ILSJRU5S')

More details in the API docs: https://docs.ceph.com/docs/master/radosgw/adminops/#remove-key


Buckets and Objects
-----------------

List Buckets
~~~~~~~~~~~~

A list of all buckets can be returned with :func:`~rgwadmin.rgw.RGWAdmin.get_buckets`.

.. code-block:: python

   >>> rgw.get_buckets()
   ['foo', 'bar', 'baz']

Get Bucket
~~~~~~~~~~

This can be used to return specific info on a bucket:

.. code-block:: python

   >>> rgw.get_bucket(bucket='liam-www')
   {'bucket': 'liam-www',
    'num_shards': 0,
    'tenant': '',
    'zonegroup': '29946069-33ce-49b7-b93d-de8c95a0c344',
    'placement_rule': 'default-placement',
    'explicit_placement': {'data_pool': '.rgw.buckets',
    'data_extra_pool': '',
    'index_pool': '.rgw.buckets.index'},
    'id': 'default.7519.1',
    'marker': 'default.7519.1',
    'index_type': 'Normal',
    'owner': 'liam',
    'ver': '0#6701',
    'master_ver': '0#0',
    'mtime': '2018-01-26 16:07:10.290779Z',
    'max_marker': '0#00000006690.7081727.5',
    'usage': {'rgw.main': {'size': 1091085,
      'size_actual': 1130496,
      'size_utilized': 1091085,
      'size_kb': 1066,
      'size_kb_actual': 1104,
      'size_kb_utilized': 1066,
      'num_objects': 18},
    'rgw.multimeta': {'size': 0,
      'size_actual': 0,
      'size_utilized': 0,
      'size_kb': 0,
      'size_kb_actual': 0,
      'size_kb_utilized': 0,
      'num_objects': 0}},
    'bucket_quota': {'enabled': False,
    'check_on_raw': False,
    'max_size': -1024,
    'max_size_kb': 0,
    'max_objects': -1}}

:func:`~rgwadmin.rgw.RGWAdmin.get_bucket` can also be used to return a
list of buckets for a given user:

.. code-block:: python

   >>> rgw.get_bucket(uid='liam')
   ['bucket1', 'bucket2', 'bucket3']

Check Bucket Index
~~~~~~~~~~~~~~~~~~

Check the index of an existing bucket.

.. note:: to check multipart object accounting with ``check_objects``, ``fix`` must be set to True.

This will return the status of the bucket index, if any.

.. code-block:: python

   >>> rgw.check_bucket_index(bucket='liampriv')
   []

Remove Bucket
~~~~~~~~~~~~~

Remove a bucket using :func:`~rgwadmin.rgw.RGWAdmin.remove_bucket`.  You must
pass purge_objects to delete a non-empty bucket.  If called on a non-empty bucket
when ``purge_data=False``, this will throw a :class:`~rgwadmin.exceptions.BucketNotEmpty`
exception. 

.. code-block:: python

   >>> rgw.remove_bucket(bucket='bucket1')
   BucketNotEmpty: {'Code': 'BucketNotEmpty',
                    'RequestId': 'tx0000000000000002a6446-005ed13a10-ad92-default',
                    'HostId': 'ad92-default-default'}

   >>> rgw.remove_bucket(bucket='bucket1', purge_data=True)


Unlink Bucket
~~~~~~~~~~~~~

Unlink a bucket from a specified user using :func:`~rgwadmin.rgw.RGWAdmin.unlink_bucket`.

.. code-block:: python

   rgw.unlink_bucket(bucket='launch-codes', uid='liam')

Link Bucket
~~~~~~~~~~~

Link the bucket to a new owner using :func:`~rgwadmin.rgw.RGWAdmin.link_bucket`.

.. code-block:: python

   # first you have to find the bucket id
   metadata = rgw.get_metadata(metadata_type='bucket', key=bucket)
   bucket_id = metadata['data']['bucket']['bucket_id']

   # then do the linking
   rgw.link_bucket(
       bucket=bucket,
       bucket_id=bucket_id,
       uid='newowner',
   )

Remove Object
~~~~~~~~~~~~~

Ceph Docs: https://docs.ceph.com/docs/master/radosgw/adminops/#remove-object

Objects can be removed from a bucket with :func:`~rgwadmin.rgw.RGWAdmin.remove_object`. 

.. code-block:: python

   rgw.remove_object(bucket='bkt1', object_name='index.html')

Get Bucket or Object Policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the policy of an object or bucket.

.. code-block:: python

   >>> rgw.get_policy(bucket='liampub')
   {'acl': {'acl_user_map': [{'user': 'liam', 'acl': 15}],
     'acl_group_map': [{'group': 1, 'acl': 1}],
     'grant_map': [{'id': '',
       'grant': {'type': {'type': 2},
        'id': '',
        'email': '',
        'permission': {'flags': 1},
        'name': '',
        'group': 1,
        'url_spec': ''}},
      {'id': 'liam',
       'grant': {'type': {'type': 0},
        'id': 'liam',
        'email': '',
        'permission': {'flags': 15},
        'name': 'Liam Monahan',
        'group': 0,
        'url_spec': ''}}]},
    'owner': {'id': 'liam', 'display_name': 'Liam Monahan'}}

And similarly for an object policy:

.. code-block:: python

   >>> rgw.get_policy(bucket='liampub', object_name='index.html')
   {'acl': {'acl_user_map': [{'user': 'liam', 'acl': 15}],
     'acl_group_map': [],
     'grant_map': [{'id': 'liam',
       'grant': {'type': {'type': 0},
        'id': 'liam',
        'email': '',
        'permission': {'flags': 15},
        'name': 'Liam Monahan',
        'group': 0,
        'url_spec': ''}}]},
    'owner': {'id': 'liam', 'display_name': 'Liam Monahan'}}

Quotas
------

There are two main types of quotas: user quotas and bucket quotas.  The API
allows you to work with both.

Set User Quota
~~~~~~~~~~~~~~

Maybe this user needs a 1GB quota.  Set a quota with
:func:`~rgwadmin.rgw.RGWAdmin.set_user_quota`.

.. code-block:: python

   rgw.set_user_quota(
       uid='liam',
       quota_type='user',
       max_size_kb=1024*1024,  # 1GB
       enabled=True,
   )

Set Bucket Quota
~~~~~~~~~~~~~~~~

Set the quota on an individual bucket:

.. code-block:: python

   rgw.set_bucket_quota(
       uid='liam',
       bucket='launch-codes',
       max_size_kb=1024*1024,  # 1GB
       enabled=True)

Get User Quota
~~~~~~~~~~~~~~

Return the quota set for the user.

.. code-block:: python

   >>> rgw.get_user_quota(uid='liam')
   {'check_on_raw': False,
    'enabled': True,
    'max_objects': -1,
    'max_size': 1168400384,
    'max_size_kb': 1141016}

This user has a size quota enabled.

Get User Bucket Quota
~~~~~~~~~~~~~~~~~~~~~

Return the quota set on every bucket owned/created by a user.  We can see
that our example user does not have this quota enabled.

.. code-block:: python

   >>> rgw.get_user_bucket_quota(uid='liam')
   {'check_on_raw': False,
    'enabled': False,
    'max_objects': -1,
    'max_size': -1,
    'max_size_kb': 0}

Get Quota
~~~~~~~~~

As a lower-level function you can get quotas and specify the quota type:

.. code-block:: python

   rgw.get_quota(uid='liam', quota_type='user')

Metadata Ops
--------

Get Metadata
~~~~~~~~~~~~

See :func:`~rgwadmin.rgw.RGWAdmin.get_metadata`

Put Metadata
~~~~~~~~~~~~

See :func:`~rgwadmin.rgw.RGWAdmin.put_metadata`

Delete Metadata
~~~~~~~~~~~~~~~

See :func:`~rgwadmin.rgw.RGWAdmin.delete_metadata`

Lock Metadata
~~~~~~~~~~~~

See :func:`~rgwadmin.rgw.RGWAdmin.lock_metadata`

Unlock Metadata
~~~~~~~~~~~~

See :func:`~rgwadmin.rgw.RGWAdmin.unlock_metadata`

Get Bucket Instances
~~~~~~~~~~~~~~~~~~~~

There is a convenience method called :func:`~rgwadmin.rgw.RGWAdmin.get_bucket_instances`
to get all the bucket instance metadata.

.. code-block:: python

   rgw.get_bucket_instances()
