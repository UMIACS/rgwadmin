Getting Started
===============

To get started, you'll want to connect to your Ceph instance by instantiating
a :class:`~rgwadmin.rgw.RGWAdmin` object.

.. code-block:: python

   from rgwadmin import RGWAdmin

   rgw = RGWAdmin(
       access_key='MY_ACCESS_KEY',
       secret_key='MY_SECRET_KEY',
       server='ceph.example.com')

Let's create a new user for ourselves with :func:`~rgwadmin.rgw.RGWAdmin.create_user`.

.. code-block:: python

   rgw.create_user(
       uid='liam',
       display_name='Liam Monahan',
       email='liam@umiacs.umd.edu',
       user_caps='usage=read, write; users=read',
       max_buckets=1000)

Maybe this user needs a 1GB quota.  Set a quota with
:func:`~rgwadmin.rgw.RGWAdmin.set_user_quota`.

.. code-block:: python

   rgw.set_user_quota(
       uid='liam',
       quota_type='user',
       max_size_kb=1024*1024,  # 1GB
       enabled=True)
