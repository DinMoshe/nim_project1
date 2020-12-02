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
TIMEOUT = 0.5

