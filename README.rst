macaddress
==========

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

    pip install macaddress


Usage
-----

Import:

.. code:: python

    import macaddress

Classes are provided for common hardware identifier
types (``MAC``/``EUI48``, ``EUI64``, ``OUI``, and
so on), as well as several less common ones. Others
might be added later. You can define ones that you
need in your code with just a few lines of code.


Parse or Validate String
~~~~~~~~~~~~~~~~~~~~~~~~

When only one address type is valid:
````````````````````````````````````

All provided classes support the standard and common formats.
For example, the ``EUI48`` and ``MAC`` classes support the
following formats:

.. code:: python

    >>> macaddress.MAC('01-23-45-67-89-ab')
    MAC('01-23-45-67-89-AB')
    >>> macaddress.MAC('01:23:45:67:89:ab')
    MAC('01-23-45-67-89-AB')
    >>> macaddress.MAC('0123.4567.89ab')
    MAC('01-23-45-67-89-AB')
    >>> macaddress.MAC('0123456789ab')
    MAC('01-23-45-67-89-AB')

You can inspect what formats a hardware address class supports
by looking at its ``formats`` attribute:

.. code:: python

    >>> macaddress.OUI.formats
    ('xx-xx-xx', 'xx:xx:xx', 'xxxxxx')

Each ``x`` in the format string matches one hexadecimal
"digit", and all other characters are matched literally.

If the string does not match one of the formats, a
``ValueError`` is raised:

.. code:: python

    >>> try:
    ...     macaddress.MAC('foo bar')
    ... except ValueError as error:
    ...     print(error)
    ... 
    'foo bar' cannot be parsed as MAC

If you need to parse in a format that isn't supported,
you can define a subclass and add the format:

.. code:: python

    >>> class MACAllowsTrailingDelimiters(macaddress.MAC):
    ...     formats = macaddress.MAC.formats + (
    ...         'xx-xx-xx-xx-xx-xx-',
    ...         'xx:xx:xx:xx:xx:xx:',
    ...         'xxxx.xxxx.xxxx.',
    ...     )
    ... 
    >>> MACAllowsTrailingDelimiters('01-02-03-04-05-06-')
    MACAllowsTrailingDelimiters('01-02-03-04-05-06')

When multiple address types are valid:
``````````````````````````````````````

There is also a ``parse`` function for when you have a string
which might be one of several classes:

.. code:: python

    >>> from macaddress import EUI48, EUI64, MAC, OUI

    >>> macaddress.parse('01:02:03', OUI, MAC)
    OUI('01-02-03')
    >>> macaddress.parse('01:02:03:04:05:06', OUI, MAC, EUI64)
    MAC('01-02-03-04-05-06')
    >>> macaddress.parse('010203040506', EUI64, EUI48)
    EUI48('01-02-03-04-05-06')
    >>> macaddress.parse('0102030405060708', EUI64, EUI48, OUI, MAC)
    EUI64('01-02-03-04-05-06-07-08')

If the input string cannot be parsed as any of
the given classes, a ``ValueError`` is raised:

.. code:: python

    >>> try:
    ...     macaddress.parse('01:23', MAC, OUI)
    ... except ValueError as error:
    ...     print(error)
    ... 
    '01:23' cannot be parsed as MAC or OUI
    >>> try:
    ...     macaddress.parse('01:23', MAC, OUI, EUI64)
    ... except ValueError as error:
    ...     print(error)
    ... 
    '01:23' cannot be parsed as MAC, OUI, or EUI64

Note that the message of the ``ValueError`` tries to be helpful
for developers, but it is not localized, nor is its exact text
part of the official public interface covered by SemVer.


Parse from Bytes
~~~~~~~~~~~~~~~~

All ``macaddress`` classes can be constructed from raw bytes:

.. code:: python

    >>> macaddress.MAC(b'abcdef')
    MAC('61-62-63-64-65-66')
    >>> macaddress.OUI(b'abc')
    OUI('61-62-63')

If the byte string is the wrong size, a ``ValueError`` is raised:

.. code:: python

    >>> try:
    ...     macaddress.MAC(b'\x01\x02\x03')
    ... except ValueError as error:
    ...     print(error)
    ... 
    b'\x01\x02\x03' has wrong length for MAC


Parse from Integers
~~~~~~~~~~~~~~~~~~~

All ``macaddress`` classes can be constructed from raw integers:

.. code:: python

    >>> macaddress.MAC(0x010203ffeedd)
    MAC('01-02-03-FF-EE-DD')
    >>> macaddress.OUI(0x010203)
    OUI('01-02-03')

Note that the least-significant bit of the integer value maps
to the last bit in the address type, so the same integer has
a different meaning depending on the class you use it with:

.. code:: python

    >>> macaddress.MAC(1)
    MAC('00-00-00-00-00-01')
    >>> macaddress.OUI(1)
    OUI('00-00-01')

If the integer is too large for the hardware identifier class
that you're trying to construct, a ``ValueError`` is raised:

.. code:: python

    >>> try:
    ...     macaddress.OUI(1_000_000_000)
    ... except ValueError as error:
    ...     print(error)
    ... 
    1000000000 is too big for OUI


Get as String
~~~~~~~~~~~~~

.. code:: python

    >>> mac = macaddress.MAC('01-02-03-0A-0B-0C')
    >>> str(mac)
    '01-02-03-0A-0B-0C'
    >>> str(mac).replace('-', ':')
    '01:02:03:0A:0B:0C'
    >>> str(mac).replace('-', '')
    '0102030A0B0C'
    >>> str(mac).lower()
    '01-02-03-0a-0b-0c'


Get as Bytes
~~~~~~~~~~~~

.. code:: python

    >>> mac = macaddress.MAC('61-62-63-04-05-06')
    >>> bytes(mac)
    b'abc\x04\x05\x06'


Get as Integer
~~~~~~~~~~~~~~

.. code:: python

    >>> mac = macaddress.MAC('01-02-03-04-05-06')
    >>> int(mac)
    1108152157446
    >>> int(mac) == 0x010203040506
    True


Get the OUI
~~~~~~~~~~~

Most classes supplied by this module have the ``oui``
attribute, which returns their first three bytes as
an OUI object:

.. code:: python

    >>> macaddress.MAC('01:02:03:04:05:06').oui
    OUI('01-02-03')


Compare
~~~~~~~

Equality
````````

All ``macaddress`` classes support equality comparisons:

.. code:: python

    >>> macaddress.OUI('01-02-03') == macaddress.OUI('01:02:03')
    True
    >>> macaddress.OUI('01-02-03') == macaddress.OUI('ff-ee-dd')
    False
    >>> macaddress.OUI('01-02-03') != macaddress.CDI32('01-02-03-04')
    True
    >>> macaddress.OUI('01-02-03') != macaddress.CDI32('01-02-03-04').oui
    False

Ordering
````````

All ``macaddress`` classes support total
ordering. The comparisons are designed to
intuitively sort identifiers that start
with the same bits next to each other:

.. code:: python

    >>> some_values = [
    ...     MAC('ff-ee-dd-01-02-03'),
    ...     MAC('ff-ee-00-99-88-77'),
    ...     MAC('ff-ee-dd-01-02-04'),
    ...     OUI('ff-ee-dd'),
    ... ]
    >>> for x in sorted(some_values):
    ...     print(x)
    FF-EE-00-01-02-03
    FF-EE-DD
    FF-EE-DD-01-02-03
    FF-EE-DD-01-02-04


Define New Types
~~~~~~~~~~~~~~~~

If this library does not provide a hardware address
type that you need, you can easily define your own.

For example, this is all it takes to define
IP-over-InfiniBand link-layer addresses:

.. code:: python

    class InfiniBand(macaddress.HWAddress):
        size = 20 * 8  # size in bits; 20 octets

        formats = (
            'xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx-xx',
            'xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx',
            'xxxx.xxxx.xxxx.xxxx.xxxx.xxxx.xxxx.xxxx.xxxx.xxxx',
            'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            # or whatever formats you want to support
        )
        # All formats are tried when parsing from string,
        # and the first format is used when stringifying.
