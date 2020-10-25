#!/usr/bin/python3
from socket import *
import sys
import errno


def play():
    nim_array, port_num = parse_args()  # nim_array = [#A, #B, #C]

    listening_socket = start_listening(port_num)

    while True:

        conn_sock, client_address = create_connection(listening_socket)

        heap_sizes = str(nim_array[0]) + " " + str(nim_array[1]) + " " + str(nim_array[2])

        my_sendall(conn_sock, heap_sizes.encode())

        while True:

            bytes_object = conn_sock.recv(15)  # get move from client

            input_arr = bytes_object.decode().split()  # first elem = which heap, 2nd elem = number to decrease

            if is_legal_move(nim_array, input_arr):
                client_move(nim_array, ord(input_arr[0]) - ord('A'), input_arr[1])
                my_sendall(conn_sock, "Move accepted\n".encode())
            else:
                my_sendall(conn_sock, "Illegal move\n".encode())

            ret = nim_strategy(nim_array)

            heap_sizes = str(nim_array[0]) + " " + str(nim_array[1]) + " " + str(nim_array[2])

            my_sendall(conn_sock, heap_sizes.encode())

            if ret == 1:
                my_sendall(conn_sock, "You win!".encode())
                break
            elif ret == 0:
                my_sendall(conn_sock, "Server win!".encode())
                break

        conn_sock.close()


def is_legal_move(nim_array, input_arr):
    if input_arr[0] == 'A':
        if nim_array[0] < input_arr[1]:
            print("error")
            return False
        else:
            return True
    elif input_arr[0] == 'B':
        if nim_array[1] < input_arr[1]:
            print("error")
            return False
        else:
            return True
    elif input_arr[0] == 'C':
        if nim_array[2] < input_arr[1]:
            print("error")
            return False
        else:
            return True
    else:
        print("error")
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
    listening_socket = socket(AF_INET, SOCK_STREAM)

    listening_socket.bind(('', port_num))

    listening_socket.listen(5)  # Socket becomes listening

    return listening_socket


def create_connection(listening_socket):
    (conn_sock, client_address) = listening_socket.accept()

    return conn_sock, client_address


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


