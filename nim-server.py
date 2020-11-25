#!/usr/bin/python3
from socket import *
from queue import Queue
from select import select
import sys
import struct
from auxialiry import *

TIMEOUT = 10
recv_dict = dict()
send_dict = dict()
heap_dict = dict()
is_active_sock_dict = dict()
how_much_to_read_dict = dict()


def num_is_active():
    i = 0
    for soc in is_active_sock_dict.keys():
        if is_active_sock_dict[soc]:
            i += 1
    return i


# This function performs nim game with the client connected through conn_sock.
def play(nim_array, conn_sock):
    while True:  # this while loop is for the moves from the client

        bytes_object = my_recv(struct.calcsize(">ici"), conn_sock)  # get a move from client

        if bytes_object is None:  # client has disconnected, so we continue to other clients
            return
        flag, heap, num_to_dec = struct.unpack(">ici", bytes_object)

        heap = heap.decode("ascii")

        if flag == 1 and is_legal_move(nim_array, heap, num_to_dec):
            client_move(nim_array, ord(heap) - ord('A'), num_to_dec)
            ret = my_sendall(conn_sock, struct.pack(">iiii", 0, 0, 0, 0))  # send Move accepted
        else:
            if flag == 2:
                return
            ret = my_sendall(conn_sock, struct.pack(">iiii", 1, 0, 0, 0))  # send Illegal move

        # checking if the client has disconnected:
        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            return  # we need to stop this game and start accepting other clients

        ret_strategy = nim_strategy(nim_array)  # server plays

        # send heap sizes:
        ret_send_heaps = my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))

        # checking if the client has disconnected:
        if ret_send_heaps == errno.EPIPE or ret_send_heaps == errno.ECONNRESET:
            return  # we need to stop this game and start accepting other clients

        # send You win or server wins or continue playing
        ret = my_sendall(conn_sock, struct.pack(">iiii", ret_strategy + 2, 0, 0, 0))
        # if client wins: ret_strategy + 2 == 2 (You win)
        # if server wins: ret_strategy + 2 == 3 (Server win)
        # if nobody wins: ret_strategy + 2 == 4 (continue playing)

        # checking if the client has disconnected:
        if ret == errno.EPIPE or ret == errno.ECONNRESET:
            return

        if ret_strategy == 1 or ret_strategy == 0:
            return  # we need to stop this game and start accepting other clients


# This function accepts one new client at a time. It always runs in the background.
def accept_clients():
    nim_array_saved, port_num, num_players, wait_list_size = parse_args()  # nim_array = [#A, #B, #C]

    if nim_array_saved is None and port_num is None and num_players is None and wait_list_size is None:
        print("The format of the arguments is illegal. "
              "Please run the server again with correct arguments.")
        return

    # Initializing the queue
    wait_queue = Queue(maxsize=wait_list_size)

    listening_socket = start_listening(port_num)

    if listening_socket is None:
        return

    to_write = []
    to_read = [listening_socket]

    while True:  # this while loop is for new connections

        readable, writeable = select(__rlist=to_read, __wlist=to_write, __xlist=[], __timeout=TIMEOUT)

        msg = b""
        for s in writeable:
            ret = s.send(msg)
            send_dict[s] += msg[:ret]

        for s in readable:
            if s is listening_socket:
                nim_array = [item for item in nim_array_saved]  # when the game is restarted,
                # we use the heap sizes retrieved from the command line arguments.

                conn_sock, client_address = create_connection(listening_socket)
                if conn_sock is None and client_address is None:
                    # ???
                    continue

                num_sockets = num_is_active()
                send_dict[conn_sock] = b""
                to_write.append(conn_sock)
                if num_sockets == num_players:
                    # too many clients
                    is_active_sock_dict[conn_sock] = False
                    if wait_queue.full():
                        send_dict[conn_sock] += struct.pack(">iiii", 7, 0, 0, 0)
                    else:
                        send_dict[conn_sock] += struct.pack(">iiii", 8, 0, 0, 0)
                        to_read.append(conn_sock)
                        recv_dict[conn_sock] = b""
                else:
                    to_read.append(conn_sock)
                    send_dict[conn_sock] += struct.pack(">iiii", 9, 0, 0, 0)
                    heap_dict[conn_sock] = nim_array
                    recv_dict[conn_sock] = b""
                    is_active_sock_dict[conn_sock] = True

            else:
                pass

        for conn_sock in is_active_sock_dict.keys():
            if not is_active_sock_dict[conn_sock]:
                continue
            nim_array = heap_dict[conn_sock]
            send_dict[conn_sock] += struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2])
            # ret = my_sendall(conn_sock, struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2]))
            # if ret == errno.EPIPE or ret == errno.ECONNRESET:
            #     conn_sock.close()
            #     continue

            if len(recv_dict[conn_sock]) == struct.calcsize(">ici"):
                bytes_object = recv_dict[conn_sock]  # get a move from client

                # if bytes_object is None:  # client has disconnected, so we continue to other clients
                #     continue
                flag, heap, num_to_dec = struct.unpack(">ici", bytes_object)

                heap = heap.decode("ascii")

                if flag == 1 and is_legal_move(nim_array, heap, num_to_dec):
                    client_move(nim_array, ord(heap) - ord('A'), num_to_dec)
                    send_dict[conn_sock] += struct.pack(">iiii", 0, 0, 0, 0)  # send Move accepted
                else:
                    if flag == 2:
                        is_active_sock_dict[conn_sock] = False
                        continue

                    send_dict[conn_sock] += struct.pack(">iiii", 1, 0, 0, 0)  # send Illegal move

                # # checking if the client has disconnected:
                # if ret == errno.EPIPE or ret == errno.ECONNRESET:
                #     return  # we need to stop this game and start accepting other clients

                ret_strategy = nim_strategy(nim_array)  # server plays

                # send heap sizes:
                send_dict[conn_sock] += struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2])

                # # checking if the client has disconnected:
                # if ret_send_heaps == errno.EPIPE or ret_send_heaps == errno.ECONNRESET:
                #     return  # we need to stop this game and start accepting other clients

                # send You win or server wins or continue playing
                send_dict[conn_sock] += struct.pack(">iiii", ret_strategy + 2, 0, 0, 0)
                # if client wins: ret_strategy + 2 == 2 (You win)
                # if server wins: ret_strategy + 2 == 3 (Server win)
                # if nobody wins: ret_strategy + 2 == 4 (continue playing)

                # # checking if the client has disconnected:
                # if ret == errno.EPIPE or ret == errno.ECONNRESET:
                #     return

                if ret_strategy == 1 or ret_strategy == 0:
                    is_active_sock_dict[conn_sock] = False

        # conn_sock.close()

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
# It return (None, None, None, None) if the format of the arguments is illegal.
# Otherwise, it returns (nim_array, port_num, num_players, wait_list_size)
def parse_args():
    if len(sys.argv) < 6 or len(sys.argv) > 7:
        return None, None, None, None

    nim_array = [num for num in sys.argv[1:4]]

    for item in nim_array:
        if not item.isnumeric() or (int(item) < 1 or int(item) > 1000):
            return None, None, None, None

    nim_array = [int(num) for num in nim_array]

    if not (sys.argv[4].isnumeric() and sys.argv[5].isnumeric()):
        return None, None, None, None

    num_players = int(sys.argv[4])

    wait_list_size = int(sys.argv[5])

    if num_players < 0 or wait_list_size < 0:
        return None, None, None, None

    if len(sys.argv) == 7:  # we received port
        if not sys.argv[6].isnumeric():
            return None, None, None, None
        port_num = int(sys.argv[4])
    else:
        port_num = PORT
    return nim_array, port_num, num_players, wait_list_size


# This function creates a listening socket.
# It tries until it succeeds in creating such a socket.
# In case the port is unavailable, we return None and terminate.
def start_listening(port_num, wait_list_size):
    try:
        listening_socket = socket(AF_INET, SOCK_STREAM)

        listening_socket.bind(('', port_num))

        listening_socket.listen(10*wait_list_size)  # Socket becomes listening

        return listening_socket

    except OSError as my_error:
        if my_error.errno == errno.EADDRINUSE:
            return None


# This function creates a connection between the server and a client.
# It tries until it succeeds in creating such a connection.
def create_connection(listening_socket):
    try:
        (conn_sock, client_address) = listening_socket.accept()
        return conn_sock, client_address
    except OSError as my_error:
        return None, None


# This function performs one server move.
# It returns 0 if client wins, 1 if the server wins and 2 otherwise.
def nim_strategy(nim_array):
    max_index = nim_array.index(max(nim_array))
    if nim_array[max_index] == 0:
        # all heaps are empty, so the client won
        return 0
    else:
        nim_array[max_index] = nim_array[max_index] - 1
        if max(nim_array) == 0:
            # all heaps are empty after server played, so the server won
            return 1
    return 2


def release_socket(conn_sock):
    send_dict.pop(conn_sock)
    recv_dict.pop(conn_sock)
    heap_dict.pop(conn_sock)
    is_active_sock_dict.pop(conn_sock)
    how_much_to_read_dict.pop(conn_sock)
    conn_sock.close()


accept_clients()  # starting to accept clients and play with them
