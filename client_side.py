#!/usr/bin/python3
from socket import *
import sys

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 6444  # Port to listen on


def play():

    hostname, port_num = parse_args()

    client_soc = create_connection(hostname, port_num)

    bytes_object = client_soc.recv(??) # get heap sizes from server

    string = bytes_object.decode()

    current_heap_size(nim_array)  # print heaps to client

    get_input()

    while sfds


def get_input():

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
    client_soc = socket(AF_INET, SOCK_STREAM)
    client_soc.connect((hostname, port_num))

    return client_soc


def my_sendall(sock, data):
    #add errors
    if len(data) == 0:
        return None
    ret = sock.send(data)
    return my_sendall(sock, data[ret:])

