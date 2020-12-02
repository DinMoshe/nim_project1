#!/usr/bin/python3
from socket import *
from queue import Queue
from select import select
import sys
from auxialiry import *
import signal
from optimal_nim_strategy import nim_optimal_strategy

TO_STOP = False
recv_dict = dict()
send_dict = dict()
heap_dict = dict()
how_much_to_send_dict = dict()  # saves the remainder of the bytes to be sent per client
started_playing_dict = dict()
playing_sockets = list()
is_active_dict = dict()
to_write = list()
to_read = list()


def handler(signum, frame):
    global TO_STOP
    TO_STOP = True


# This method pops the first client in the queue and activates it if the queue is not empty
def wake_up_client(wait_queue):
    if wait_queue.empty():
        return
    conn_sock = wait_queue.get()
    is_active_dict[conn_sock] = True
    playing_sockets.append(conn_sock)
    send_dict[conn_sock] += struct.pack(">iiii", 9, 0, 0, 0)


# This function accepts one new client at a time. It always runs in the background.
def accept_clients():
    nim_array_saved, port_num, num_players, wait_list_size, optimal_strategy = parse_args()  # nim_array = [#A, #B, #C]

    if nim_array_saved is None and port_num is None and num_players is None and wait_list_size is None:
        print("The format of the arguments is illegal. "
              "Please run the server again with correct arguments.")
        return

    # Initializing the queue
    wait_queue = Queue(maxsize=wait_list_size)

    with start_listening(port_num, wait_list_size) as listening_socket:
        if listening_socket is None:
            return

        to_read.append(listening_socket)

        while True:  # this while loop is for new connections

            if TO_STOP:
                for conn_sock in playing_sockets:
                    release_socket(conn_sock)
                return

            readable, writeable, nothing = select(to_read, to_write, [], TIMEOUT)

            for s in writeable:

                if how_much_to_send_dict[s] == 0 and len(send_dict[s]) > 0:
                    how_much_to_send_dict[s] = SERVER_MSG_SIZE

                num_bytes_to_send = how_much_to_send_dict[s]

                if num_bytes_to_send > 0:
                    msg = send_dict[s][:num_bytes_to_send]

                    try:
                        ret = s.send(msg)
                        send_dict[s] = send_dict[s][ret:]
                        how_much_to_send_dict[s] = num_bytes_to_send - ret
                    except OSError as my_error:
                        ret_except = my_error.errno
                        if ret_except == errno.EPIPE or ret_except == errno.ECONNRESET:
                            # we need to deactivate the client because we are not connected to him anymore
                            release_socket(s)
                            wake_up_client(wait_queue)

            for s in readable:
                if s is listening_socket:
                    nim_array = [item for item in nim_array_saved]  # when the game is restarted,
                    # we use the heap sizes retrieved from the command line arguments.

                    conn_sock, client_address = create_connection(listening_socket)

                    if conn_sock is None and client_address is None:
                        continue

                    num_sockets = len(playing_sockets)
                    how_much_to_send_dict[conn_sock] = SERVER_MSG_SIZE
                    send_dict[conn_sock] = b""
                    started_playing_dict[conn_sock] = False
                    to_write.append(conn_sock)
                    if num_sockets == num_players:
                        # too many clients
                        is_active_dict[conn_sock] = False
                        if wait_queue.full() or wait_list_size == 0:
                            send_dict[conn_sock] += struct.pack(">iiii", 7, 0, 0, 0)
                        else:
                            send_dict[conn_sock] += struct.pack(">iiii", 8, 0, 0, 0)
                            to_read.append(conn_sock)
                            recv_dict[conn_sock] = b""
                            wait_queue.put(conn_sock)
                            heap_dict[conn_sock] = nim_array
                    else:
                        is_active_dict[conn_sock] = True
                        to_read.append(conn_sock)
                        send_dict[conn_sock] += struct.pack(">iiii", 9, 0, 0, 0)
                        heap_dict[conn_sock] = nim_array
                        recv_dict[conn_sock] = b""
                        playing_sockets.append(conn_sock)

                else:
                    try:
                        bytes_object = s.recv(CLIENT_MSG_SIZE)
                        if bytes_object == 0 or len(bytes_object) == 0:  # connection terminated
                            release_socket(s)
                            wake_up_client(wait_queue)
                            continue
                        recv_dict[s] += bytes_object
                    except OSError as my_error:
                        if my_error.errno == errno.ECONNREFUSED:  # connection terminated
                            release_socket(s)
                            wake_up_client(wait_queue)
                            continue
                    # maybe transfer check if the message is fully received here

            for conn_sock in playing_sockets:
                if not is_active_dict[conn_sock]:
                    #  socket has been deactivated due to win
                    if send_dict[conn_sock] == b"":
                        release_socket(conn_sock)
                        wake_up_client(wait_queue)

                    continue

                nim_array = heap_dict[conn_sock]
                if not started_playing_dict[conn_sock]:
                    send_dict[conn_sock] += struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2])
                    started_playing_dict[conn_sock] = True

                if len(recv_dict[conn_sock]) >= CLIENT_MSG_SIZE:
                    bytes_object = recv_dict[conn_sock][:CLIENT_MSG_SIZE]  # get a move from client

                    recv_dict[conn_sock] = recv_dict[conn_sock][CLIENT_MSG_SIZE:]

                    flag, heap, num_to_dec = struct.unpack(">ici", bytes_object)

                    heap = heap.decode("ascii")

                    if flag == 1 and is_legal_move(nim_array, heap, num_to_dec):
                        client_move(nim_array, ord(heap) - ord('A'), num_to_dec)
                        send_dict[conn_sock] += struct.pack(">iiii", 0, 0, 0, 0)  # send Move accepted
                    else:
                        if flag == 2:
                            release_socket(conn_sock)
                            wake_up_client(wait_queue)
                            continue
                        # flag == 0
                        send_dict[conn_sock] += struct.pack(">iiii", 1, 0, 0, 0)  # send Illegal move

                    if optimal_strategy:
                        ret_strategy = nim_optimal_strategy(nim_array) # server plays
                    else:
                        ret_strategy = nim_strategy(nim_array)  # server plays

                    # send heap sizes:
                    send_dict[conn_sock] += struct.pack(">iiii", 6, nim_array[0], nim_array[1], nim_array[2])

                    # send You win or server wins or continue playing
                    send_dict[conn_sock] += struct.pack(">iiii", ret_strategy + 2, 0, 0, 0)
                    # if client wins: ret_strategy + 2 == 2 (You win)
                    # if server wins: ret_strategy + 2 == 3 (Server win)
                    # if nobody wins: ret_strategy + 2 == 4 (continue playing)

                    if ret_strategy == 1 or ret_strategy == 0:
                        is_active_dict[conn_sock] = False


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
    if len(sys.argv) < 6 or len(sys.argv) > 8:
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

    if len(sys.argv) >= 7:  # we received port
        if not sys.argv[6].isnumeric():
            return None, None, None, None
        port_num = int(sys.argv[6])
    else:
        port_num = PORT

    optimal_strategy = False
    if len(sys.argv) == 8:  # we received optimal strategy flag
        optimal_strategy = True

    return nim_array, port_num, num_players, wait_list_size, optimal_strategy


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
    is_active_dict.pop(conn_sock)
    how_much_to_send_dict.pop(conn_sock)
    started_playing_dict.pop(conn_sock)
    playing_sockets.remove(conn_sock)
    to_read.remove(conn_sock)
    to_write.remove(conn_sock)
    conn_sock.close()


signal.signal(signal.SIGINT, handler)
accept_clients()  # starting to accept clients and play with them
