#!/usr/bin/python3
from socket import *
import sys
import struct
import errno

# encoding of messages:
# 0- Move accepted
# 1- Illegal move
# 2-You win!
# 3-Server win!
# 4-error
# 5-Disconnected from server
# 6 - Heap A: #
#     Heap B: #
#     Heap C: #


def play():
    nim_array, port_num = parse_args()  # nim_array = [#A, #B, #C]

    listening_socket = start_listening(port_num)

    while True:

        conn_sock, client_address = create_connection(listening_socket)

        my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))

        while True:

            bytes_object = conn_sock.recv(9)  # get move from client

            flag, heap, num_to_dec = struct.unpack(">ici", bytes_object)

            if flag == 1 and is_legal_move(nim_array, heap, num_to_dec):
                client_move(nim_array, ord(heap) - ord('A'), num_to_dec)
                my_sendall(conn_sock, struct.pack(">iiii", 0, 0, 0, 0))
            else:
                my_sendall(conn_sock, struct.pack(">iiii",  1, 0, 0, 0))

            ret = nim_strategy(nim_array)

            my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))

            if ret == 1:
                my_sendall(conn_sock , struct.pack(">iiii",  2, 0, 0, 0))
                break
            elif ret == 0:
                my_sendall(conn_sock, struct.pack(">iiii",  3, 0, 0, 0))
                break

        conn_sock.close()


def is_legal_move(nim_array, heap, num_to_dec):
    if num_to_dec <= 0:
        return False
    if heap == 'A':
        if nim_array[0] < num_to_dec:
            return False
        else:
            return True
    elif heap == 'B':
        if nim_array[1] < num_to_dec:
            return False
        else:
            return True
    elif heap == 'C':
        if nim_array[2] < num_to_dec:
            return False
        else:
            return True
    else:
        return False


def client_move(nim_array, index, num_to_decrease):
    nim_array[index] -= num_to_decrease


def parse_args():
    nim_array = [int(num) for num in sys.argv[1:4]]
    if len(sys.argv) == 5:
        port_num = int(sys.argv[5])
    else:
        port_num = 6444
    return nim_array, port_num


def start_listening(port_num):
    while True:
        try:
            listening_socket = socket(AF_INET, SOCK_STREAM)

            listening_socket.bind(('', port_num))

            listening_socket.listen(5)  # Socket becomes listening

            return listening_socket

        except OSError as error:
            print(error.strerror)


def create_connection(listening_socket):
    while True:
        try:
            (conn_sock, client_address) = listening_socket.accept()
            return conn_sock, client_address
        except OSError as error:
                print(error.strerror)


# This function performs one server move.
# It returns 1 if client wins, 0 if the server wins and 2 otherwise.
def nim_strategy(nim_array):
    max_index = nim_array.index(max(nim_array))
    if nim_array[max_index] == 0:
        # all heaps are empty, so the client won
        return 1
    else:
        nim_array[max_index] = nim_array[max_index] - 1
        if max(nim_array) == 0:
            # all heaps are empty after server played, so the server won
            return 0
    return 2


def my_sendall(sock, data):
    # add errors
    if len(data) == 0:
        return None
    ret = sock.send(data)
    return my_sendall(sock, data[ret:])
