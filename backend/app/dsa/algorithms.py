"""
Dynamic Programming, Backtracking, and Branch & Bound algorithms.
Used internally for optimization tasks in the fraud detection system.
"""


# ===================== DYNAMIC PROGRAMMING =====================

def knapsack_01(weights, values, capacity):
    """
    0/1 Knapsack - used for resource allocation in investigation prioritization.
    Returns maximum value and selected items.
    """
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if weights[i - 1] <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - weights[i - 1]] + values[i - 1])

    # Backtrack to find selected items
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(i - 1)
            w -= weights[i - 1]

    return dp[n][capacity], selected


def longest_common_subsequence(s1, s2):
    """
    LCS - used for pattern matching in transaction sequences.
    Returns length and the LCS string.
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Reconstruct LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return dp[m][n], "".join(reversed(lcs))


def matrix_chain_multiplication(dims):
    """
    Matrix Chain Multiplication - used for optimizing sequential operations.
    Returns minimum multiplications and optimal parenthesization.
    """
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float("inf")
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k

    return dp[0][n - 1], split


def resource_allocation(resources, tasks, values):
    """
    Resource allocation using DP - for allocating analyst time to cases.
    resources: total available resources
    tasks: list of resource requirements per task
    values: list of value/priority per task
    """
    return knapsack_01(tasks, values, resources)


# ===================== BACKTRACKING =====================

def graph_coloring(adj_matrix, num_colors):
    """
    Graph coloring - used for conflict-free scheduling of investigations.
    Returns color assignment or None if not possible.
    """
    n = len(adj_matrix)
    colors = [0] * n

    def is_safe(node, color):
        for i in range(n):
            if adj_matrix[node][i] and colors[i] == color:
                return False
        return True

    def solve(node):
        if node == n:
            return True
        for color in range(1, num_colors + 1):
            if is_safe(node, color):
                colors[node] = color
                if solve(node + 1):
                    return True
                colors[node] = 0
        return False

    if solve(0):
        return colors
    return None


def n_queen(n):
    """
    N-Queen - used as optimization utility for non-conflicting assignments.
    Returns one valid placement or None.
    """
    board = [[0] * n for _ in range(n)]

    def is_safe(row, col):
        for i in range(col):
            if board[row][i]:
                return False
        for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
            if board[i][j]:
                return False
        for i, j in zip(range(row, n), range(col, -1, -1)):
            if board[i][j]:
                return False
        return True

    def solve(col):
        if col >= n:
            return True
        for i in range(n):
            if is_safe(i, col):
                board[i][col] = 1
                if solve(col + 1):
                    return True
                board[i][col] = 0
        return False

    if solve(0):
        return board
    return None


def hamiltonian_cycle(adj_matrix):
    """
    Hamiltonian cycle detection - used to find complete traversal paths in network.
    Returns path or None.
    """
    n = len(adj_matrix)
    path = [-1] * n
    path[0] = 0

    def is_safe(v, pos):
        if not adj_matrix[path[pos - 1]][v]:
            return False
        if v in path[:pos]:
            return False
        return True

    def solve(pos):
        if pos == n:
            return bool(adj_matrix[path[pos - 1]][path[0]])
        for v in range(1, n):
            if is_safe(v, pos):
                path[pos] = v
                if solve(pos + 1):
                    return True
                path[pos] = -1
        return False

    if solve(1):
        return path
    return None


def sum_of_subsets(numbers, target):
    """
    Sum of subsets - used for finding transaction combinations matching totals.
    Returns all subsets that sum to target.
    """
    result = []

    def backtrack(start, current_sum, subset):
        if current_sum == target:
            result.append(subset[:])
            return
        if current_sum > target:
            return
        for i in range(start, len(numbers)):
            subset.append(numbers[i])
            backtrack(i + 1, current_sum + numbers[i], subset)
            subset.pop()

    backtrack(0, 0, [])
    return result


# ===================== BRANCH AND BOUND =====================

def tsp_branch_and_bound(dist_matrix):
    """
    TSP using Branch and Bound - used for optimal route planning in investigations.
    Returns minimum cost and path.
    """
    import heapq

    n = len(dist_matrix)
    if n <= 1:
        return 0, [0]

    min_cost = float("inf")
    best_path = []

    # Priority queue: (lower_bound, cost_so_far, current_node, visited_set, path)
    initial_bound = _tsp_bound(dist_matrix, 0, frozenset([0]), n)
    pq = [(initial_bound, 0, 0, frozenset([0]), [0])]

    iterations = 0
    max_iterations = min(100000, 2 ** min(n, 15))

    while pq and iterations < max_iterations:
        iterations += 1
        bound, cost, node, visited, path = heapq.heappop(pq)

        if bound >= min_cost:
            continue

        if len(visited) == n:
            total = cost + dist_matrix[node][0]
            if total < min_cost:
                min_cost = total
                best_path = path + [0]
            continue

        for next_node in range(n):
            if next_node not in visited:
                new_cost = cost + dist_matrix[node][next_node]
                new_visited = visited | {next_node}
                new_bound = _tsp_bound(dist_matrix, new_cost, new_visited, n)
                if new_bound < min_cost:
                    heapq.heappush(pq, (new_bound, new_cost, next_node,
                                        new_visited, path + [next_node]))

    return min_cost, best_path


def _tsp_bound(dist_matrix, cost_so_far, visited, n):
    """Lower bound estimation for TSP."""
    bound = cost_so_far
    for i in range(n):
        if i not in visited:
            min_edge = float("inf")
            for j in range(n):
                if i != j and dist_matrix[i][j] > 0:
                    min_edge = min(min_edge, dist_matrix[i][j])
            if min_edge < float("inf"):
                bound += min_edge
    return bound
