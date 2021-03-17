import serial
import time

LONG_OFFSET = 2147483647
baud = 57600


def read_to_bytearray(my_serial, size=4):
    data = bytearray(size)
    my_serial.readinto(data)
    return data


def read_long(my_serial):
    arr_string = read_hex(my_serial)
    result = int(arr_string, 16)
    if result > LONG_OFFSET:
        result -= 2 * LONG_OFFSET + 2
    return result


def read_char(my_serial):
    data = read_to_bytearray(my_serial, 1)
    my_serial.readinto(data)
    return data.decode("utf-8")


def read_binary(my_serial):
    data = read_to_bytearray(my_serial)
    my_serial.readinto(data)
    return '0b' + ''.join('{:08b}'.format(x) for x in data)


def read_hex(my_serial):
    data = read_to_bytearray(my_serial)
    my_serial.readinto(data)
    return '0x' + ''.join('{:02x}'.format(x) for x in data)


def write_string(my_serial, message):
    message.encode("utf-8")
    test_bytearray = bytearray()
    test_bytearray.extend(map(ord, message))
    return my_serial.write(test_bytearray)


def read_string(my_serial, length):
    result = ""
    data = read_to_bytearray(my_serial, length)
    for elem in data:
        result += chr(elem)
    return result, data


def init(my_serial):
    return read_char(my_serial)
