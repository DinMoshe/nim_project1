#!/usr/bin/python3
from socket import *
import sys
import errno

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 6444  # Port to listen on


def play():

    hostname, port_num = parse_args()

    client_sock = create_connection(hostname, port_num)

    while True:
        bytes_object = client_sock.recv(15)  # get heap sizes from server

        heap_sizes = bytes_object.decode()

        nim_array = heap_sizes.split()

        current_heap_size(nim_array)  # print heaps to client

        input_arr = input("Your turn:\n").split()

        if input_arr[0] == 'Q':
            break

        if len(input_arr) != 2:
            print("error")
        else:
            if input_arr[0] not in {'A', 'B', 'C'}:
                print("Illegal move")
            else:
                if not input_arr[1].isnumeric():
                    print("Illegal move")
                else:
                    my_sendall(client_sock, " ".join(input_arr).encode())
                    bytes_object = client_sock.recv(14)  # message = "Move accepted" or "Illegal move"

    if len(input_arr) > 1:
        print("error")

    client_sock.close()


def get_input(client_sock):
    input_arr = input("Your turn:\n").split()


def parse_args():

    hostname = HOST
    port_num = PORT

    if len(sys.argv) > 1:
        hostname = sys.argv[1]

        if len(sys.argv) > 2:
            port_num = int(sys.argv[2])

        if len(sys.argv) > 3:
            print("error")

    return hostname, port_num


def create_connection(hostname, port_num):
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((hostname, port_num))

    return client_sock


# this function prints the current heaps sizes
def current_heap_size(nim_array):
    print("Heap A:" + str(nim_array[0]) + "\n")
    print("Heap B:" + str(nim_array[1]) + "\n")
    print("Heap C:" + str(nim_array[2]) + "\n")


def my_sendall(sock, data):
    # add errors
    if len(data) == 0:
        return None
    ret = sock.send(data)
    return my_sendall(sock, data[ret:])


play()
