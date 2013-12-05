Running zcp from a local checkout
===

If you have a local checkout of zcp and you've built the binaries without
installing them system-wide, importing MAPI modules will fail. To get around
this use:

$ fab zcp.load_local_zcp

This will do some magic on your system to make sure python can find MAPI and
that the zarafa client can initialize correctly. It assumes this layout:

checkout: ~/zcp
fakeroot: ~/fakeroot

For more info check fabfile.py
