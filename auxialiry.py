#!/usr/bin/python3

# Definition of the protocol - encoding of messages:
# 0- Move accepted
# 1- Illegal move
# 2-You win!
# 3-Server win!
# 4-error
# 5-Disconnected from server
# 6 - Heap A: #
#     Heap B: #
#     Heap C: #


# constants:
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)

PORT = 6444  # Port to listen on


def my_sendall(sock, data):
    if len(data) == 0:
        return None
    try:
        ret = sock.send(data)
        return my_sendall(sock, data[ret:])
    except OSError as error:
        return error.errno
