from hypothesis import given
from hypothesis.strategies import (
    binary,
    booleans,
    characters,
    composite,
    from_regex,
    integers,
    lists,
    one_of,
    sampled_from,
    text,
)
import reprshed
import pytest

from macaddress import *


@composite
def _addresses(draw, random_formats=0):
    Class = draw(_address_classes(random_formats))
    address_as_an_integer = draw(_address_integers(Class.size))
    return Class(address_as_an_integer)


@composite
def _addresses_with_several_random_formats(draw):
    random_formats = draw(integers(min_value=2, max_value=8))
    return draw(_addresses(random_formats=random_formats))


@composite
def _address_classes_and_invalid_integers(draw):
    Class = draw(_address_classes())
    invalid_integer = draw(one_of(
        integers(max_value=-1),
        integers(min_value=(1 << Class.size)),
    ))
    return (Class, invalid_integer)


@composite
def _address_classes_and_invalid_bytes(draw):
    Class = draw(_address_classes())
    size_in_bytes = (Class.size + 7) >> 3
    invalid_byte_string = draw(one_of(
        binary(max_size=size_in_bytes-1),
        binary(min_size=size_in_bytes+1),
    ))
    return (Class, invalid_byte_string)


@composite
def _address_classes_and_invalid_strings(draw):
    Class = draw(_address_classes())
    size_in_nibbles = (Class.size + 3) >> 2
    invalid_string = draw(one_of(
        text(characters(), max_size=size_in_nibbles-1),
        text(characters(), min_size=size_in_nibbles+1),
        from_regex('[^0-9A-Fa-f]'),
    ))
    return (Class, invalid_string)


@composite
def _lists_of_distinctly_formatted_addresses(draw):
    return draw(lists(
        _addresses(random_formats=1),
        min_size=2,
        max_size=8,
        unique_by=lambda address: address.formats[0],
    ))


@composite
def _lists_of_distinctly_sized_addresses(draw):
    return draw(lists(
        _addresses(),
        min_size=2,
        max_size=8,
        unique_by=lambda address: (address.size + 7) >> 3,
    ))


@composite
def _address_classes(draw, random_formats=0):
    address_sizes = integers(min_value=1, max_value=64)
    size_in_bits = draw(address_sizes)
    size_in_nibbles = (size_in_bits + 3) >> 2

    if random_formats > 0:
        format_strings = draw(lists(
            _address_format_strings(size_in_nibbles),
            min_size=random_formats,
            max_size=random_formats,
        ))
    else:
        format_string = 'x' * size_in_nibbles
        format_strings = (format_string,)

    class_should_be_slotted = draw(booleans())

    class Class(HWAddress):
        __slots__ = ()
        size = size_in_bits
        formats = format_strings
        def __repr__(self):
            return reprshed.impure(
                self,
                size=type(self).size,
                formats=type(self).formats,
                slots=class_should_be_slotted,
                address=self._address,
            )

    if not class_should_be_slotted:
        # Subclassing again without defining __slots__ is effectively
        # like "removing" slots from the class we just made.
        class Class(Class):
            pass

    return Class


def _address_integers(size_in_bits):
    return integers(min_value=0, max_value=((1 << size_in_bits) - 1))


_address_format_characters = sampled_from('x-:.')


@composite
def _address_format_strings(draw, size_in_nibbles):
    characters = []
    while size_in_nibbles:
        character = draw(_address_format_characters)
        if character == 'x':
            size_in_nibbles -= 1
        characters.append(character)
    return ''.join(characters)


@given(_addresses())
def test_int(address):
    Class = type(address)
    assert Class(int(address)) == address


@given(_address_classes_and_invalid_integers())
def test_int_value_error(Class_and_integer):
    Class, integer = Class_and_integer
    with pytest.raises(ValueError):
        Class(integer)


@given(_addresses())
def test_bytes(address):
    Class = type(address)
    assert Class(bytes(address)) == address


@given(_address_classes_and_invalid_bytes())
def test_bytes_value_error(Class_and_bytes):
    Class, byte_string = Class_and_bytes
    with pytest.raises(ValueError):
        Class(byte_string)


@given(_addresses(random_formats=1))
def test_str(address):
    Class = type(address)
    assert Class(str(address)) == address


@given(_address_classes_and_invalid_strings())
def test_str_value_error(Class_and_string):
    Class, string = Class_and_string
    with pytest.raises(ValueError):
        Class(string)


@given(_address_classes())
def test_str_x_literal_value_error(Class):
    size_in_nibbles = (Class.size + 3) >> 2
    with pytest.raises(ValueError):
        Class('x' * size_in_nibbles)


@given(_addresses_with_several_random_formats())
def test_str_alternatives(address):
    Class = type(address)
    formats = Class.formats
    for format in formats:
        # Override instance formats to make this format the only
        # format, because it will stringify using the first one.
        # Note: we have to overwrite `.formats` on the class
        # because it cannot be overwritten on the instance if
        # the class is slotted.
        Class.formats = (format,)
        # Format to string using the newly chosen format:
        formatted = str(address)
        # Restore the original formats for comparison, so that
        # the test verifies that the constructor parses each
        # alternate format whether or not it is the first one:
        Class.formats = formats
        assert Class(formatted) == address


@given(_addresses())
def test_copy_construction(address):
    Class = type(address)
    assert Class(address) == address


@given(_addresses(random_formats=1))
def test_parse_str(address):
    Class = type(address)
    assert parse(str(address), Class) == address


@given(_lists_of_distinctly_formatted_addresses())
def test_parse_str_alternatives(addresses):
    classes = [type(address) for address in addresses]
    for address in addresses:
        assert parse(str(address), *classes) == address


@given(_addresses())
def test_parse_bytes(address):
    Class = type(address)
    assert parse(bytes(address), Class) == address


@given(_lists_of_distinctly_sized_addresses())
def test_parse_bytes_alternatives(addresses):
    classes = [type(address) for address in addresses]
    for address in addresses:
        assert parse(bytes(address), *classes) == address


@given(_addresses())
def test_parse_passthrough(address):
    Class = type(address)
    assert parse(address, Class) == address


@given(_addresses())
def test_equality_with_subclass(address):
    Class = type(address)
    class Subclass(Class):
        pass
    assert Subclass(int(address)) != address


@given(_addresses(), _addresses())
def test_ordering(address1, address2):
    assert (address1 <  address2) == (_bits(address1) <  _bits(address2))
    assert (address1 <= address2) == (_bits(address1) <= _bits(address2))
    assert (address1 >  address2) == (_bits(address1) >  _bits(address2))
    assert (address1 >= address2) == (_bits(address1) >= _bits(address2))


def _bits(address):
    size = address.size
    address = int(address)
    bits = []
    while size:
        least_significant_bit = address & 1
        bits.append(least_significant_bit)
        address >>= 1
        size -= 1
    return ''.join(map(str, reversed(bits)))


@given(_addresses(), _addresses())
def test_hash(address1, address2):
    Class = type(address1)
    assert hash(Class(address1)) == hash(address1)
    if address1 == address2:
        assert hash(address1) == hash(address2)


def test_type_errors():
    class Dummy:
        pass
    for thing in (None, [], {}, object, object(), Dummy, Dummy()):
        with pytest.raises(TypeError):
            MAC(thing)
        with pytest.raises(TypeError):
            parse(thing, MAC, OUI)
        with pytest.raises(TypeError):
            parse(thing)


def test_equality_not_implemented():
    class Dummy:
        pass
    for thing in (None, [], {}, object, object(), Dummy, Dummy()):
        assert MAC(0).__eq__(thing) is NotImplemented
        assert MAC(0).__ne__(thing) is NotImplemented


def test_provided_classes():
    for Class in OUI, CDI32, CDI40, MAC, EUI48, EUI60, EUI64:
        for format in Class.formats:
            assert (Class.size + 3) >> 2 == sum(1 for x in format if x == 'x')
