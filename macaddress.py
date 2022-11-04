# SPDX-License-Identifier: 0BSD
# Copyright 2021 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""Like ``ipaddress``, but for hardware identifiers such as MAC addresses."""

__all__ = (
    'HWAddress',
    'OUI',
    'CDI32', 'CDI40',
    'MAC',
    'EUI48', 'EUI60', 'EUI64',
    'parse',
)
__version__ = '2.0.2'


from functools import total_ordering as _total_ordering


_HEX_DIGITS = "0123456789ABCDEFabcdef"


def _name(obj):
    return type(obj).__name__


def _class_names_in_proper_english(classes):
    class_names = [cls.__name__ for cls in classes]
    number_of_classes = len(classes)
    if number_of_classes < 2:
        return class_names[0]
    elif number_of_classes == 2:
        return ' or '.join(class_names)
    else:
        class_names[-1] = 'or ' + class_names[-1]
        return ', '.join(class_names)


def _type_error(value, *classes):
    class_names = _class_names_in_proper_english(classes)
    return TypeError(repr(value) + ' has wrong type for ' + class_names)


def _value_error(value, error, *classes):
    class_names = _class_names_in_proper_english(classes)
    return ValueError(repr(value) + ' ' + error + ' ' + class_names)


@_total_ordering
class HWAddress:
    """Base class for hardware addresses.

    Can be subclassed to create new address types
    by just defining a couple class attribures.

    Attributes:
        size: An integer defined by each subclass to specify the size
            (in bits) of the hardware address.
        formats: A sequence of format strings defined by each subclass
            to specify what formats the class can parse. The first
            format string is also used for ``repr`` and ``str`` output.
            Each "x" in each format string stands for one hexadecimal
            digit. All other characters are literal. For example, for
            MAC addresses, the format strings are "xx-xx-xx-xx-xx-xx",
            "xx:xx:xx:xx:xx:xx", "xxxx.xxxx.xxxx", and "xxxxxxxxxxxx".
    """

    __slots__ = ('_address', '__weakref__')

    formats = ()

    def __init__(self, address):
        """Initialize the hardware address object with the address given.

        Arguments:
            address: An ``int``, ``bytes``, or ``str`` representation of
                the address, or another instance of an address which is
                either the same class, a subclass, or a superclass. If a
                string, the ``formats`` attribute of the class is used
                to parse it. If a byte string, it is read in big-endian.
                If an integer, its value bytes in big-endian are used as
                the address bytes.

        Raises:
            TypeError: If ``address`` is not one of the valid types.
            ValueError: If ``address`` is a string but does not match
                one of the formats, if ``address`` is a byte string
                but does not match the size, or if ``address`` is an
                integer with a value that is negative or too big.
        """
        if isinstance(address, int):
            overflow = 1 << type(self).size
            if address >= overflow:
                raise _value_error(address, 'is too big for', type(self))
            if address < 0:
                raise ValueError('hardware address cannot be negative')
            self._address = address
        elif isinstance(address, bytes):
            length = len(address)
            size_in_bytes = (type(self).size + 7) >> 3
            if length != size_in_bytes:
                raise _value_error(address, 'has wrong length for', type(self))
            offset = (8 - type(self).size) & 7
            self._address = int.from_bytes(address, 'big') >> offset
        elif isinstance(address, str) and len(type(self).formats):
            self._address, _ = _parse(address, type(self))
        # Subclass being "cast" to superclass:
        elif isinstance(address, type(self)):
            self._address = int(address)
        # Superclass being "cast" to subclass:
        elif (isinstance(address, HWAddress)
        and   isinstance(self, type(address))):
            self._address = int(address)
        else:
            raise _type_error(address, type(self))

    def __repr__(self):
        """Represent the hardware address as an unambiguous string."""
        try:
            address = repr(str(self))
        except TypeError:
            address = _hex(int(self), type(self).size)
        return _name(self) + '(' + address + ')'

    def __str__(self):
        """Get the canonical human-readable string of this hardware address."""
        formats = type(self).formats
        if not len(formats):
            raise TypeError(_name(self) + ' has no string format')
        result = []
        offset = (4 - type(self).size) & 3
        unconsumed_address_value = int(self) << offset
        for character in reversed(formats[0]):
            if character == 'x':
                nibble = unconsumed_address_value & 0xf
                result.append(_HEX_DIGITS[nibble])
                unconsumed_address_value >>= 4
            else:
                result.append(character)
        return ''.join(reversed(result))

    def __bytes__(self):
        """Get the big-endian byte string of this hardware address."""
        offset = (8 - type(self).size) & 7
        size_in_bytes = (type(self).size + 7) >> 3
        return (int(self) << offset).to_bytes(size_in_bytes, 'big')

    def __int__(self):
        """Get the raw integer value of this hardware address."""
        return self._address

    def __eq__(self, other):
        """Check if this hardware address is equal to another.

        Hardware addresses are equal if they are instances of the
        same class, and their raw bit strings are the same.
        """
        if not isinstance(other, HWAddress):
            return NotImplemented
        return type(self) == type(other) and int(self) == int(other)

    def __lt__(self, other):
        """Check if this hardware address is before another.

        Hardware addresses are sorted by their raw bit strings,
        regardless of the exact hardware address class or size.

        For example: ``OUI('00-00-00') < CDI32('00-00-00-00')``,
        and they both are less than ``OUI('00-00-01')``.

        This order intuitively groups address prefixes like OUIs
        with (and just in front of) addresses like MAC addresses
        which have that prefix when sorting a list of them.
        """
        if not isinstance(other, HWAddress):
            return NotImplemented
        class1 = type(self)
        class2 = type(other)
        size1 = class1.size
        size2 = class2.size
        bits1 = int(self)
        bits2 = int(other)
        if size1 > size2:
            bits2 <<= size1 - size2
        else:
            bits1 <<= size2 - size1
        return (bits1, size1, id(class1)) < (bits2, size2, id(class2))

    def __hash__(self):
        """Get the hash of this hardware address."""
        return hash((type(self), int(self)))


def _hex(integer, bits):
    # Like the built-in function ``hex`` but pads the
    # output to ``bits`` worth of hex characters.
    #
    # Examples:
    #     (integer=5,      bits=32) -> '0x00000005'
    #     (integer=0x1234, bits=32) -> '0x00001234'
    #     (integer=0x1234, bits=16) -> '0x1234'
    return '0x' + hex((1 << (bits+3)) | integer)[3:]


class OUI(HWAddress):
    """Organizationally Unique Identifier."""

    __slots__ = ()

    size = 24

    formats = (
        'xx-xx-xx',
        'xx:xx:xx',
        'xxxxxx',
    )


class _StartsWithOUI(HWAddress):
    __slots__ = ()

    @property
    def oui(self):
        """Get the OUI part of this hardware address."""
        return OUI(int(self) >> (type(self).size - OUI.size))


class CDI32(_StartsWithOUI):
    """32-bit Context Dependent Identifier (CDI-32)."""

    __slots__ = ()

    size = 32

    formats = (
        'xx-xx-xx-xx',
        'xx:xx:xx:xx',
        'xxxxxxxx',
    )


class CDI40(_StartsWithOUI):
    """40-bit Context Dependent Identifier (CDI-40)."""

    __slots__ = ()

    size = 40

    formats = (
        'xx-xx-xx-xx-xx',
        'xx:xx:xx:xx:xx',
        'xxxxxxxxxx',
    )


class EUI48(_StartsWithOUI):
    """48-Bit Extended Unique Identifier (EUI-48).

    EUI-48 is also the modern official name for what
    many people are used to calling a "MAC address".
    """

    __slots__ = ()

    size = 48

    formats = (
        'xx-xx-xx-xx-xx-xx',
        'xx:xx:xx:xx:xx:xx',
        'xxxx.xxxx.xxxx',
        'xxxxxxxxxxxx',
    )


MAC = EUI48


class EUI60(_StartsWithOUI):
    """60-Bit Extended Unique Identifier (EUI-60)."""

    __slots__ = ()

    size = 60

    formats = (
        'x.x.x.x.x.x.x.x.x.x.x.x.x.x.x',
        'xx-xx-xx.x.x.x.x.x.x.x.x.x',
        'xxxxxxxxxxxxxxx',
    )


class EUI64(_StartsWithOUI):
    """64-Bit Extended Unique Identifier (EUI-64)."""

    __slots__ = ()

    size = 64

    formats = (
        'xx-xx-xx-xx-xx-xx-xx-xx',
        'xx:xx:xx:xx:xx:xx:xx:xx',
        'xxxx.xxxx.xxxx.xxxx',
        'xxxxxxxxxxxxxxxx',
    )


def parse(value, *classes):
    """Try parsing a value as several hardware address classes at once.

    This lets you just write

        address = macaddress.parse(user_input, EUI64, EUI48, ...)

    instead of all of this:

        try:
            address = macaddress.EUI64(user_input)
        except ValueError:
            try:
                address = macaddress.EUI48(user_input)
            except ValueError:
                ...

    Arguments:
        value: The value to parse as a hardware address. Either a
            string, byte string, or an instance of one of the classes.
        *classes: HWAddress subclasses to try to parse the string as.
            If the input address could parse as more than one of the
            classes, it is parsed as the first one.

    Returns:
        HWAddress: The parsed hardware address if the value argument
            was a string or byte string, or the value argument itself
            if it was already an instance of one of the classes.

    Raises:
        TypeError: If the value is not one of the valid types,
            or if no classes were passed in.
        ValueError: If the value could not be parsed as any
            of the given classes.
    """
    if not classes:
        raise TypeError('parse() requires at least one class argument')
    if isinstance(value, str):
        address, cls = _parse(value, *classes)
        return cls(address)
    elif isinstance(value, bytes):
        max_size = len(value) * 8
        min_size = max_size - 7
        for cls in classes:
            if min_size <= cls.size <= max_size:
                return cls(value)
        raise _value_error(value, 'has wrong length for', *classes)
    elif isinstance(value, classes):
        return value
    raise _type_error(value, *classes)


def _parse(string, *classes):
    length = len(string)
    if length < 1:
        raise ValueError('hardware address cannot be an empty string')
    candidates = {}
    for cls in classes:
        for format_ in cls.formats:
            if len(format_) == length:
                candidates.setdefault(format_, cls)
    candidates = sorted(candidates.items())
    address = 0
    start = 0
    end = len(candidates)
    for index in range(length):
        character = string[index]
        if character in _HEX_DIGITS:
            address <<= 4
            address += int(character, 16)
            character = 'x'
        elif character == 'x':
            character = ''
        while start < end and candidates[start][0][index] < character:
            start += 1
        while start < end and candidates[end - 1][0][index] > character:
            end -= 1
        if start >= end:
            raise _value_error(string, 'cannot be parsed as', *classes)
    _, cls = candidates[start]
    offset = (4 - cls.size) & 3
    address >>= offset
    return address, cls
