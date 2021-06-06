hwaddress
=========

A module for handling hardware identifiers like MAC addresses.

This module makes it easy to:

1. check if a string represents a valid MAC address, or a similar
   hardware identifier like an EUI-64, OUI, etc,

2. convert between string and binary forms of MAC addresses and
   other hardware identifiers,

and so on.

Heavily inspired by the ``ipaddress`` module, but not yet quite
as featureful.


Versioning
----------

This library's version numbers follow the `SemVer 2.0.0
specification <https://semver.org/spec/v2.0.0.html>`_.


Installation
------------

::

    pip install hwaddress


Usage
-----

Import:

.. code:: python

    import hwaddress

Several classes are provided to parse common hardware addresses
(``MAC``/``EUI48``, ``EUI64``, ``OUI``, etc), as well as
several less common ones (``EUI60``, ``CDI32``, etc). They each
support several common formats.

For example, the ``EUI48`` and ``MAC`` classes support the
following formats:

.. code:: python

    >>> hwaddress.MAC('01-23-45-67-89-ab')
    MAC('01-23-45-67-89-AB')
    >>> hwaddress.MAC('01:23:45:67:89:ab')
    MAC('01-23-45-67-89-AB')
    >>> hwaddress.MAC('0123.4567.89ab')
    MAC('01-23-45-67-89-AB')
    >>> hwaddress.MAC('0123456789ab')
    MAC('01-23-45-67-89-AB')

You can inspect what formats a hardware address class supports
by looking at its ``formats`` attribute:

.. code:: python

    >>> hwaddress.OUI.formats
    ('xx-xx-xx', 'xx:xx:xx', 'xxxxxx')

The first format listed in ``formats`` is also the one used
when stringifying (``str``) or representing (``repr``) the
object.

Most classes supplied by this module have the ``oui``
attribute, which just returns their first three bytes as
an OUI object:

.. code:: python

    >>> hwaddress.EUI48('01:02:03:04:05:06').oui
    OUI('01-02-03')

All ``hwaddress`` classes support equality comparisons:

.. code:: python

    >>> hwaddress.OUI('01-02-03') == hwaddress.OUI('01:02:03')
    True
    >>> hwaddress.OUI('01-02-03') == hwaddress.OUI('ff-ee-dd')
    False
    >>> hwaddress.OUI('01-02-03') == hwaddress.CDI32('01-02-03-04')
    False
    >>> hwaddress.OUI('01-02-03') == hwaddress.CDI32('01-02-03-04').oui
    True

All ``hwaddress`` classes can be initialized with raw bytes
or raw integers representing their value instead of strings:

.. code:: python

    >>> hwaddress.MAC(b'abcdef')
    MAC('61-62-63-64-65-66')
    >>> hwaddress.MAC(0x010203ffeedd)
    MAC('01-02-03-FF-EE-DD')
    >>> hwaddress.MAC(1)
    MAC('00-00-00-00-00-01')
    >>> hwaddress.OUI(b'abc')
    OUI('61-62-63')
    >>> hwaddress.OUI(0x010203)
    OUI('01-02-03')
    >>> hwaddress.OUI(1)
    OUI('00-00-01')

If any of the values passed to the constructors are invalid,
the constructors raise a ``TypeError`` or a ``ValueError``
as appropriate.

All ``hwaddress`` classes also support total ordering. The
comparisons are intended to intuitively put identifiers
that start with the same bits next to each other sorting:

.. code:: python

    >>> some_hw_identifiers = [
    ...     MAC('ff-ee-dd-01-02-03'),
    ...     MAC('ff-ee-00-99-88-77'),
    ...     MAC('ff-ee-dd-01-02-04'),
    ...     OUI('ff-ee-dd'),
    ... ]
    >>> for x in sorted(some_hw_identifiers):
    ...     print(x)
    ff-ee-00-01-02-03
    ff-ee-dd
    ff-ee-dd-01-02-03
    ff-ee-dd-01-02-04
