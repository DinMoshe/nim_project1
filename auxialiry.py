#!/usr/bin/python3

import errno
import struct

# Definition of the protocol - encoding of messages from server to client:
# 0- Move accepted
# 1- Illegal move
# 2-You win!
# 3-Server win!
# 4-continue playing
# 6 - Heap A: #
#     Heap B: #
#     Heap C: #
# 7 - You are rejected by the server.
# 8 - Waiting to play against the server.
# 9 - Now you are playing against the server!

# encoding of messages from client to server:
# 0 - illegal move (parsing-wise) is sent to server
# 1 - legal move (parsing-wise) is sent to server
# 2 - user sent quit request


# constants:
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)

PORT = 6444  # Port to listen on

SERVER_MSG_SIZE = struct.calcsize(">iiii")
CLIENT_MSG_SIZE = struct.calcsize(">ici")
TIMEOUT = 10


def my_sendall(sock, data):
    if len(data) == 0:
        return None
    try:
        ret = sock.send(data)
        return my_sendall(sock, data[ret:])
    except OSError as error:
        return error.errno


# this function receives exactly num_bytes through sock if the connection is established
# otherwise it returns None
def my_recv(num_bytes, sock):
    bytes_object = None
    try:
        bytes_object = sock.recv(num_bytes)
        if bytes_object == 0:  # connection terminated
            return None
    except OSError as my_error:
        if my_error.errno == errno.ECONNREFUSED:  # connection terminated
            return None
    if bytes_object is None:
        return None
    byte_array = bytearray(bytes_object)
    num_bytes -= len(bytes_object)
    while num_bytes > 0:
        try:
            bytes_object = sock.recv(num_bytes)
            if bytes_object == 0:  # connection terminated
                return None
        except OSError as my_error:
            if my_error.errno == errno.ECONNREFUSED:  # connection terminated
                return None
        byte_array.extend(bytearray(bytes_object))
        num_bytes -= len(bytes_object)

    return bytes(byte_array)
