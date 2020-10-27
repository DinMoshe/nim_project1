#!/usr/bin/python3
from socket import *
import sys
import struct
import errno
from auxialiry import *


# This function performs nim game with the client connected through conn_sock.
def play(nim_array, conn_sock):
    while True:  # this while loop is for the moves from the client

        bytes_object = conn_sock.recv(struct.calcsize(">ici"))  # get a move from client

        flag, heap, num_to_dec = struct.unpack(">ici", bytes_object)

        if flag == 1 and is_legal_move(nim_array, heap, num_to_dec):
            client_move(nim_array, ord(heap) - ord('A'), num_to_dec)
            ret = my_sendall(conn_sock, struct.pack(">iiii", 0, 0, 0, 0))
        else:
            ret = my_sendall(conn_sock, struct.pack(">iiii", 1, 0, 0, 0))

        # checking if the client has disconnected:
        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            print("Client disconnected\n")
            return  # we need to stop this game and start accepting other clients

        ret_strategy = nim_strategy(nim_array)

        ret = my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))

        # checking if the client has disconnected:
        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            print("Client disconnected\n")
            return  # we need to stop this game and start accepting other clients

        if ret_strategy == 1:
            ret = my_sendall(conn_sock, struct.pack(">iiii", 2, 0, 0, 0))
            # checking if the client has disconnected:
            if ret == errno.EPIPE or ret == errno.ECONNRESET:
                print("Client disconnected\n")
            return  # we need to stop this game and start accepting other clients
        elif ret_strategy == 0:
            ret = my_sendall(conn_sock, struct.pack(">iiii", 3, 0, 0, 0))
            # checking if the client has disconnected:
            if ret == errno.EPIPE or ret == errno.ECONNRESET:
                print("Client disconnected\n")
            return  # we need to stop this game and start accepting other clients


# This function accepts one new client at a time. It always runs in the background.
def accept_clients():
    nim_array_saved, port_num = parse_args()  # nim_array = [#A, #B, #C]

    if nim_array_saved is None and port_num is None:
        print("The format of the arguments is illegal. "
              "Please run the server again with correct arguments.\n")
        return

    listening_socket = start_listening(port_num)

    while True:  # this while loop is for new connections

        nim_array = [item for item in nim_array_saved]  # when the game is restarted,
        # we use the heap sizes retrieved from the command line arguments.

        conn_sock, client_address = create_connection(listening_socket)

        ret = my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))

        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            print("Client disconnected\n")
            conn_sock.close()
            continue

        play(nim_array, conn_sock)

        conn_sock.close()

    listening_socket.close()


# This function checks and returns whether the client's move is legal
# We assume the client's move is well formatted.
def is_legal_move(nim_array, heap, num_to_dec):
    if num_to_dec <= 0:  # checking if we decrease at least one cube
        return False
    if heap == 'A':
        if nim_array[0] < num_to_dec:
            return False
    elif heap == 'B':
        if nim_array[1] < num_to_dec:
            return False
    elif heap == 'C':
        if nim_array[2] < num_to_dec:
            return False

    return True


# This function performs a client move
def client_move(nim_array, index, num_to_decrease):
    nim_array[index] -= num_to_decrease


# This function parses command line arguments.
# It return (None, None) if the format of the arguments is illegal.
# Otherwise, it returns (nim_array, port_num)
def parse_args():

    if len(sys.argv) < 4 or len(sys.argv) > 5:
        return None, None

    nim_array = [num for num in sys.argv[1:4]]

    for item in nim_array:
        if not item.isnumeric():
            return None, None

    nim_array = [int(num) for num in nim_array]

    if len(sys.argv) == 5:  # we received port
        if not sys.argv[5].isnumeric():
            return None, None
        port_num = int(sys.argv[5])
    else:
        port_num = PORT
    return nim_array, port_num


# This function creates a listening socket.
# It tries until it succeed in creating such a socket.
def start_listening(port_num):
    while True:
        try:
            listening_socket = socket(AF_INET, SOCK_STREAM)

            listening_socket.bind(('', port_num))

            listening_socket.listen(5)  # Socket becomes listening

            return listening_socket

        except OSError as my_error:
            print(my_error.strerror)


# This function creates a connection between the server and a client.
# It tries until it succeeds in creating such a connection.
def create_connection(listening_socket):
    while True:
        try:
            (conn_sock, client_address) = listening_socket.accept()
            return conn_sock, client_address
        except OSError as my_error:
            print(my_error.strerror)


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


accept_clients()  # starting to accept clients and play with them
