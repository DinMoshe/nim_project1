#!/usr/bin/python3
from socket import *
import sys


def play():
    nim_array, port_num = parse_args()  # nim_array = [#A, #B, #C]

    listening_socket = start_listening(port_num)

    while True:

        conn_sock, client_address = create_connection(listening_socket)



        while input_arr[0] != 'Q':
            if len(input_arr) != 2:
                print("error")

            if is_legal_move(nim_array, input_arr):
                client_move(nim_array, ord(input_arr[0]) - ord('A'), input_arr[1])
            else:
                print("error")

            nim_strategy(nim_array)

            current_heap_size(nim_array)

        close(conn_sock)

        if len(input_arr) > 1:
            print("error")


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


# this function performs one server move, and prints the winner if the game is complete
def nim_strategy(nim_array):
    max_index = nim_array.index(max(nim_array))
    if nim_array[max_index] == 0:
        print("You win!\n")
        return None
    else:
        nim_array[max_index] = nim_array[max_index] - 1
        if max(nim_array) == 0:
            print("Server win!\n")
    return nim_array


# this function prints the current heaps sizes
def current_heap_size(n_a, n_b, n_c):
    print("Heap A:" + str(nim_array[0]) + "\n")
    print("Heap B:" + str(nim_array[1]) + "\n")
    print("Heap C:" + str(nim_array[2]) + "\n")
