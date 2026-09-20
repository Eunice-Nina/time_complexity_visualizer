"""
Algorithms to be timed by the visualizer.
Each function takes a single integer n (input size) and does work
proportional to that size, using a worst-case input where relevant
so the measured time reflects the algorithm's real complexity.
"""


def linear_search(n):
    arr = list(range(n))
    target = -1  # guarantees a full worst-case scan
    for x in arr:
        if x == target:
            return True
    return False


def binary_search(n):
    arr = list(range(n))
    target = -1  # guarantees the search runs to completion (not found)
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return True
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return False


def bubble_sort(n):
    arr = list(range(n, 0, -1))  # reverse-sorted = worst case for bubble sort
    for i in range(len(arr)):
        for j in range(0, len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def nested_loops(n):
    total = 0
    for i in range(n):
        for j in range(n):
            total += 1
    return total


# --- Bonus algorithms (extra credit per the activity) ---

def insertion_sort(n):
    arr = list(range(n, 0, -1))  # reverse-sorted = worst case
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


def merge_sort(n):
    arr = list(range(n, 0, -1))

    def _merge_sort(a):
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        left = _merge_sort(a[:mid])
        right = _merge_sort(a[mid:])
        return _merge(left, right)

    def _merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    return _merge_sort(arr)


def factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


ALGORITHMS = {
    "linear_search": linear_search,
    "binary_search": binary_search,
    "bubble_sort": bubble_sort,
    "nested_loops": nested_loops,
    "insertion_sort": insertion_sort,
    "merge_sort": merge_sort,
    "factorial": factorial,
}