#!/usr/bin/python3
from socket import *
from select import select
import sys
import struct
from auxialiry import *

msg_lst = ["Move accepted",
           "Illegal move",
           "You win!",
           "Server win!",
           "Disconnected from server",
           "Failed to connect to server",
           "You are rejected by the server.",
           "Waiting to play against the server.",
           "Now you are playing against the server!"]

RECEIVED_FIRST_MSG = False  # tells us if we received our first message


# This method checks what message was received.
# If we need to terminate, it returns False. Otherwise it returns True.
def parse_msg(bytes_object):
    global RECEIVED_FIRST_MSG

    heap_sizes = [0, 0, 0]
    flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)

    if flag in {0, 1, 2, 3, 7, 8, 9}:
        if flag in {7, 8, 9}:
            flag -= 1
        print(msg_lst[flag])

        if flag in {2, 3}:
            return False
        else:
            if flag == 4 and RECEIVED_FIRST_MSG:
                print("Your turn:")

    elif flag == 6:
        current_heap_size(heap_sizes)  # print heaps to client
        if not RECEIVED_FIRST_MSG: # this is the first message received so we need to ask the player to play
            print("Your turn:")

    RECEIVED_FIRST_MSG = True
    return True


def writeable_loop(writeable, to_send, remainder_bytes_to_send):
    for sock in writeable:
        if remainder_bytes_to_send == 0 and len(to_send) > 0:
            remainder_bytes_to_send = CLIENT_MSG_SIZE

        loop_condition = True

        num_bytes_to_send = remainder_bytes_to_send

        if num_bytes_to_send > 0:
            msg = to_send[:num_bytes_to_send]
            ret = 0
            ret_except = None
            try:
                ret = sock.send(msg)
            except OSError as my_error:
                ret_except = my_error.errno
            if ret_except == errno.EPIPE or ret_except == errno.ECONNRESET:
                print(msg_lst[4])
                loop_condition = False
                # we need to terminate the program because we are not connected to the server anymore
            else:
                to_send = to_send[ret:]
                remainder_bytes_to_send = num_bytes_to_send - ret

        return remainder_bytes_to_send, to_send, loop_condition


def readable_loop(readable, received_from_user, to_send, received_from_server):
    loop_condition = True
    for sock in readable:
        if sock is sys.stdin:
            # client has entered a move
            bytes_object = None
            try:
                bytes_object = sock.recv(4)
                if bytes_object == 0:  # connection terminated
                    loop_condition = False
                    break
            except OSError as my_error:
                if my_error.errno == errno.ECONNREFUSED:  # connection terminated
                    loop_condition = False
                    break

            index = bytes_object.find(b"/n")
            if index == -1:
                # no new line character
                received_from_user += struct.unpack(">" + str(len(bytes_object)) + "c", bytes_object)[0]
            else:
                user_msg = received_from_user + struct.unpack(">" + str(index) + "c", bytes_object[:index])[0]
                if index == len(bytes_object) - 1:
                    received_from_user = ""
                else:
                    received_from_user = struct.unpack(">" + str(len(bytes_object) - index - 1) + "c",
                                                       bytes_object[index + 1:])[0]

                input_arr = user_msg.split()

                if len(input_arr) == 0:
                    # an illegal move has been sent to server
                    to_send += struct.pack(">ici", 0, '0'.encode("ascii"), 0)
                elif input_arr[0] == 'Q':
                    # if 'Q' is received as the first argument,
                    # then we terminate even if there are more arguments afterwards
                    to_send += struct.pack(">ici", 2, '0'.encode("ascii"), 0)
                    loop_condition = False
                    break
                elif len(input_arr) == 2 and input_arr[0] in {'A', 'B', 'C'} and input_arr[1].isnumeric():
                    # a legal move has been sent to server
                    to_send += struct.pack(">ici", 1, input_arr[0].encode("ascii"), int(input_arr[1]))
                else:
                    # an illegal move has been sent to server
                    to_send += struct.pack(">ici", 0, '0'.encode("ascii"), 0)

                # if ret == errno.EPIPE or ret == errno.ECONNRESET:
                #    print(msg_lst[4])
                #    break  # we need to terminate the program because we are not connected to the server anymore
        else:
            # sock is client_sock
            bytes_object = None
            try:
                bytes_object = sock.recv(SERVER_MSG_SIZE)
                if bytes_object == 0:  # connection terminated
                    loop_condition = False
                    break
            except OSError as my_error:
                if my_error.errno == errno.ECONNREFUSED:  # connection terminated
                    loop_condition = False
                    break
            received_from_server += bytes_object
            if len(received_from_server) >= SERVER_MSG_SIZE:
                msg = received_from_server[:SERVER_MSG_SIZE]
                received_from_server = received_from_server[SERVER_MSG_SIZE:]
                if not parse_msg(msg):
                    loop_condition = False
                    break

        return received_from_user, to_send, received_from_server, loop_condition


# This function performs nim game with the server.
def play():
    hostname, port_num = parse_args()

    if hostname == 0 and port_num is None:
        # We received too many arguments, so we terminate.
        print("Too many arguments. Please enter up to 2 arguments.")
        return

    if hostname == 1 and port_num is None:
        # port is not a number
        print("The port entered is not a number. Please enter a legal port.")
        return

    client_sock = create_connection(hostname, port_num)

    if client_sock is None:
        print(msg_lst[5])  # Failed to connect to server
        return

    to_send = b""
    received_from_server = b""
    received_from_user = ""
    remainder_bytes_to_send = CLIENT_MSG_SIZE
    to_write = [client_sock]
    to_read = [client_sock, sys.stdin]
    loop_condition = True

    while loop_condition:
        readable, writeable = select(__rlist=to_read, __wlist=to_write, __xlist=[], __timeout=TIMEOUT)

        received_from_user, to_send, received_from_server, loop_condition = \
            readable_loop(readable, received_from_user, to_send, received_from_server)

        if not loop_condition:
            break

        # loop_condition == True
        remainder_bytes_to_send, to_send, loop_condition = writeable_loop(writeable, to_send, remainder_bytes_to_send)

    # flushing the remained messages before disconnecting
    while to_send != b"":
        readable, writeable = select(__rlist=to_read, __wlist=to_write, __xlist=[], __timeout=TIMEOUT)
        remainder_bytes_to_send, to_send, not_important = writeable_loop(writeable, to_send, remainder_bytes_to_send)

    client_sock.close()


# This function parses the command line arguments.
# It returns (1, None) if there are too many arguments.
# It returns (0, None) if port is not a number
# Otherwise, it returns (hostname, port_num)
def parse_args():
    hostname = HOST
    port_num = PORT

    if len(sys.argv) > 1:
        hostname = sys.argv[1]

        if len(sys.argv) > 2:
            if not sys.argv[2].isnumeric():
                return 1, None
            port_num = int(sys.argv[2])

        if len(sys.argv) > 3:
            return 0, None

    return hostname, port_num


# This function connects to server whose hostname is hostname and through port number port_num.
# If there is OSError, it prints a matching message and returns None.
def create_connection(hostname, port_num):
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((hostname, port_num))
        return client_sock
    except OSError as my_error:
        return None


# this function prints the current heaps sizes
def current_heap_size(heap_sizes):
    print("Heap A: " + str(heap_sizes[0]))
    print("Heap B: " + str(heap_sizes[1]))
    print("Heap C: " + str(heap_sizes[2]))


play()  # starting to play
