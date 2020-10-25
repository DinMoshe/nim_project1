#!/usr/bin/python3
from socket import *
import sys
import struct
import errno

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 6444  # Port to listen on
msg_lst = ["Move accepted\n",
           "Illegal move\n",
           "You win!\n",
           "Server win!\n",
           "error\n",
           "Disconnected from server\n"]


def play():
    hostname, port_num = parse_args()

    client_sock = create_connection(hostname, port_num)

    while True:
        try:
            bytes_object = client_sock.recv(16)  # get heap sizes from server
            if bytes_object == 0:
                print(msg_lst[5])
                break
            heap_sizes = [0, 0, 0]
            flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)
            if flag == 6:
                current_heap_size(heap_sizes)  # print heaps to client
        except OSError as error:
            if error.errno == errno.ECONNREFUSED:
                print(msg_lst[5])
            else:
                print(error.strerror)
            break

        try:
            bytes_object = client_sock.recv(16)  # get heap sizes from server
            if bytes_object == 0:
                print(msg_lst[5])
                break
            flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)
            print(msg_lst[flag])
        except OSError as error:
            if error.errno == errno.ECONNREFUSED:
                print(msg_lst[5])
            else:
                print(error.strerror)
            break

        input_arr = input("Your turn:\n").split()
        ret = None
        if input_arr[0] == 'Q':
            if len(input_arr) > 1:
                print("error")
            break
        elif len(input_arr) == 2 and input_arr[0] in {'A', 'B', 'C'} and input_arr[1].isnumeric():
            # a legal move has been sent to server
            ret = my_sendall(client_sock, struct.pack(">ici", 1, input_arr[0], int(input_arr[1])))
        else:
            # an illegal move has been sent to server
            ret = my_sendall(client_sock, struct.pack(">ici", 0, '0', '0'))

        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            print(msg_lst[5])
            break

        try:
            bytes_object = client_sock.recv(16)  # get heap sizes from server
            if bytes_object == 0:
                print(msg_lst[5])
                break
            flag, heap_sizes[0], heap_sizes[1], heap_sizes[2] = struct.unpack(">iiii", bytes_object)
            print(msg_lst[flag])
        except OSError as error:
            if error.errno == errno.ECONNREFUSED:
                print(msg_lst[5])
            else:
                print(error.strerror)
            break

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
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((hostname, port_num))
        return client_sock
    except OSError as error:
        print(error.strerror)


# this function prints the current heaps sizes
def current_heap_size(heap_sizes):
    print("Heap A:" + str(heap_sizes[0]) + "\n")
    print("Heap B:" + str(heap_sizes[1]) + "\n")
    print("Heap C:" + str(heap_sizes[2]) + "\n")


def my_sendall(sock, data):
    # add errors
    if len(data) == 0:
        return None
    try:
        ret = sock.send(data)
        return my_sendall(sock, data[ret:])
    except OSError as error:
        return error.errno

