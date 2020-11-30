# This method checks if all heaps are empty.
# If they are, it returns True, otherwise it returns False
def is_empty(nim_array):
    max_heap = max(nim_array)

    if max_heap == 0:
        return True

    return False


# This function performs one optimal server move.
# It returns 0 if client wins, 1 if the server wins and 2 otherwise.
def nim_optimal_strategy(nim_array):
    if is_empty(nim_array):
        # all heaps are empty, so the client won
        return 0

    nim_sum = calc_nim_sum(nim_array)
    if nim_sum != 0:
        heap_to_remove = find_min_winning_heap(nim_array)
        removed_objects = nim_array[heap_to_remove] - (nim_array[heap_to_remove] ^ nim_sum)
    else:
        heap_to_remove = find_min_non_empty_heap(nim_array)
        removed_objects = 1
    update_heaps(nim_array, heap_to_remove, removed_objects)

    if is_empty(nim_array):
        # all heaps are empty after server played, so the server won
        return 1

    return 2


# The function finds the minimal i such that nim_array[i] > 0.
# It assumes !isEmpty(heaps, length)
def find_min_non_empty_heap(nim_array):
    i_min = len(nim_array) - 1
    for i in range(len(nim_array) - 2, -1, -1):
        if nim_array[i] > 0:
            i_min = i

    return i_min


# The function finds the minimal i such that nim_array[i]^nim_sum < nim_array[i].
def find_min_winning_heap(nim_array):
    i_min = len(nim_array) - 1
    nim_sum = calc_nim_sum(nim_array)
    for i in range(len(nim_array) - 2, -1, -1):
        if nim_array[i] ^ nim_sum < nim_array[i]:
            i_min = i

    return i_min


# The function calculates the nim sum of the heaps in the current turn.
def calc_nim_sum(nim_array):
    nim_sum = nim_array[0]
    for i in range(1, len(nim_array)):
        nim_sum ^= nim_array[i]

    return nim_sum


# The function updates the heaps according to the parameter received.
def update_heaps(nim_array, index, removed_objects):
    nim_array[index] -= removed_objects

