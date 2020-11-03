#!/usr/bin/python3
from socket import *
import sys
import struct
from auxialiry import *

msg_lst = ["Move accepted",
           "Illegal move",
           "You win!",
           "Server win!",
           "error",
           "Disconnected from server",
           "Failed to connect to server"]


# This function performs nim game with the server.
def play():
    hostname, port_num = parse_args()

    if hostname is None and port_num is None:
        # We received too many arguments, so we terminate.
        print("Too many arguments. Please enter up to 2 arguments.")
        return

    client_sock = create_connection(hostname, port_num)

    if client_sock is None:
        print(msg_lst[6])
        return

    bytes_object = my_recv(struct.calcsize(">iiii"), client_sock)  # get heap sizes from server
    if bytes_object is None:
        print(msg_lst[5])
        client_sock.close()
        return
    heap_sizes = [0, 0, 0]
    flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)

    if flag == 6:
        current_heap_size(heap_sizes)  # print heaps to client

    while True:

        input_arr = input("Your turn:\n").split()
        ret = None
        if len(input_arr) == 0:
            # an illegal move has been sent to server
            ret = my_sendall(client_sock, struct.pack(">ici", 0, '0'.encode("ascii"), 0))
        elif input_arr[0] == 'Q':
            # if 'Q' is received as the first argument,
            # then we terminate even if there are more arguments afterwards
            my_sendall(client_sock, struct.pack(">ici", 2, '0'.encode("ascii"), 0))  # if there is an error,
            # we ignore it because user has requested to quit
            break
        elif len(input_arr) == 2 and input_arr[0] in {'A', 'B', 'C'} and input_arr[1].isnumeric():
            # a legal move has been sent to server
            ret = my_sendall(client_sock, struct.pack(">ici", 1, input_arr[0].encode("ascii"), int(input_arr[1])))
        else:
            # an illegal move has been sent to server
            ret = my_sendall(client_sock, struct.pack(">ici", 0, '0'.encode("ascii"), 0))

        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            print(msg_lst[5])
            break  # we need to terminate the program because we are not connected to the server anymore

        bytes_object = my_recv(struct.calcsize(">iiii"), client_sock)  # get Move accepted or Illegal move

        if bytes_object is None:
            print(msg_lst[5])
            break
        flag = struct.unpack(">iiii", bytes_object)[0]
        print(msg_lst[flag])

        bytes_object = my_recv(struct.calcsize(">iiii"), client_sock)  # get heap sizes from server
        if bytes_object is None:
            print(msg_lst[5])
            break
        flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)

        if flag == 6:
            current_heap_size(heap_sizes)  # print heaps to client

        bytes_object = my_recv(struct.calcsize(">iiii"), client_sock)  # get You win or Server win or continue playing
        if bytes_object is None:
            print(msg_lst[5])
            break
        flag = struct.unpack(">iiii", bytes_object)[0]

        if flag == 4:  # we need to continue
            continue
        else:
            print(msg_lst[flag])  # print winner
            break

    client_sock.close()


# This function parses the command line arguments.
# It returns (None, None) if there are too many arguments.
# Otherwise, it returns (hostname, port_num)
def parse_args():
    hostname = HOST
    port_num = PORT

    if len(sys.argv) > 1:
        hostname = sys.argv[1]

        if len(sys.argv) > 2:
            port_num = int(sys.argv[2])

        if len(sys.argv) > 3:
            return None, None

    return hostname, port_num


# This function connects to server whose hostname is hostname and through port number port_num.
# If there is OSError, it prints a matching message.
def create_connection(hostname, port_num):
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((hostname, port_num))
        return client_sock
    except OSError as my_error:
        return None


# this function prints the current heaps sizes
def current_heap_size(heap_sizes):
    print("Heap A: " + str(heap_sizes[0]) + "\n")
    print("Heap B: " + str(heap_sizes[1]) + "\n")
    print("Heap C: " + str(heap_sizes[2]) + "\n")


play()  # starting to play
