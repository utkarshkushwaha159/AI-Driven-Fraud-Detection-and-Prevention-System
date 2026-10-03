"""
Tree data structures for fraud detection system.
Includes BST, AVL Tree, Red-Black Tree, B-Tree, B+ Tree, Binary Heap,
and Threaded Binary Tree implementations.
Used internally for efficient data indexing and priority management.
"""


class TreeNode:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class BST:
    """Binary Search Tree for ordered data lookups."""

    def __init__(self):
        self.root = None
        self.size = 0

    def insert(self, key, value=None):
        self.root = self._insert(self.root, key, value)
        self.size += 1

    def _insert(self, node, key, value):
        if node is None:
            return TreeNode(key, value)
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            node.value = value
            self.size -= 1
        return node

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        if node is None:
            return None
        if key == node.key:
            return node.value
        elif key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

    def preorder(self):
        result = []
        self._preorder(self.root, result)
        return result

    def _preorder(self, node, result):
        if node:
            result.append((node.key, node.value))
            self._preorder(node.left, result)
            self._preorder(node.right, result)

    def postorder(self):
        result = []
        self._postorder(self.root, result)
        return result

    def _postorder(self, node, result):
        if node:
            self._postorder(node.left, result)
            self._postorder(node.right, result)
            result.append((node.key, node.value))

    def range_query(self, low, high):
        """Get all entries with keys in [low, high]."""
        result = []
        self._range_query(self.root, low, high, result)
        return result

    def _range_query(self, node, low, high, result):
        if node is None:
            return
        if low < node.key:
            self._range_query(node.left, low, high, result)
        if low <= node.key <= high:
            result.append((node.key, node.value))
        if node.key < high:
            self._range_query(node.right, low, high, result)

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, node, key):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            self.size -= 1
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            successor = self._min_node(node.right)
            node.key = successor.key
            node.value = successor.value
            node.right = self._delete(node.right, successor.key)
            self.size += 1
        return node

    def _min_node(self, node):
        while node.left:
            node = node.left
        return node


class AVLNode:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1


class AVLTree:
    """Self-balancing AVL Tree for efficient sorted data access."""

    def __init__(self):
        self.root = None
        self.size = 0

    def _height(self, node):
        return node.height if node else 0

    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    def _update_height(self, node):
        if node:
            node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _rotate_right(self, y):
        x = y.left
        t = x.right
        x.right = y
        y.left = t
        self._update_height(y)
        self._update_height(x)
        return x

    def _rotate_left(self, x):
        y = x.right
        t = y.left
        y.left = x
        x.right = t
        self._update_height(x)
        self._update_height(y)
        return y

    def insert(self, key, value=None):
        self.root = self._insert(self.root, key, value)
        self.size += 1

    def _insert(self, node, key, value):
        if not node:
            return AVLNode(key, value)
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            node.value = value
            self.size -= 1
            return node

        self._update_height(node)
        bf = self._balance_factor(node)

        if bf > 1 and key < node.left.key:
            return self._rotate_right(node)
        if bf < -1 and key > node.right.key:
            return self._rotate_left(node)
        if bf > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if bf < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def search(self, key):
        node = self.root
        while node:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

    def range_query(self, low, high):
        result = []
        self._range_query(self.root, low, high, result)
        return result

    def _range_query(self, node, low, high, result):
        if node is None:
            return
        if low < node.key:
            self._range_query(node.left, low, high, result)
        if low <= node.key <= high:
            result.append((node.key, node.value))
        if node.key < high:
            self._range_query(node.right, low, high, result)


class MaxHeap:
    """Max Heap for priority-based processing (alerts, risk scores)."""

    def __init__(self):
        self.heap = []

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, priority, item):
        self.heap.append((priority, item))
        self._heapify_up(len(self.heap) - 1)

    def _heapify_up(self, i):
        while i > 0 and self.heap[self._parent(i)][0] < self.heap[i][0]:
            self._swap(i, self._parent(i))
            i = self._parent(i)

    def extract_max(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        max_item = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return max_item

    def _heapify_down(self, i):
        n = len(self.heap)
        largest = i
        left = self._left(i)
        right = self._right(i)

        if left < n and self.heap[left][0] > self.heap[largest][0]:
            largest = left
        if right < n and self.heap[right][0] > self.heap[largest][0]:
            largest = right
        if largest != i:
            self._swap(i, largest)
            self._heapify_down(largest)

    def peek(self):
        return self.heap[0] if self.heap else None

    def size(self):
        return len(self.heap)

    def is_empty(self):
        return len(self.heap) == 0

    def get_top_n(self, n):
        """Get top N items without removing them."""
        import heapq
        temp = [(-p, item) for p, item in self.heap]
        heapq.heapify(temp)
        result = []
        for _ in range(min(n, len(temp))):
            p, item = heapq.heappop(temp)
            result.append((-p, item))
        return result


def heap_sort(arr):
    """Heap sort implementation."""
    n = len(arr)
    result = arr.copy()

    def heapify(arr, n, i):
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        if left < n and arr[left] > arr[largest]:
            largest = left
        if right < n and arr[right] > arr[largest]:
            largest = right
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(result, n, i)
    for i in range(n - 1, 0, -1):
        result[0], result[i] = result[i], result[0]
        heapify(result, i, 0)
    return result


class ThreadedBinaryTreeNode:
    """Node for threaded binary tree."""
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.left_thread = False
        self.right_thread = False


class ThreadedBinaryTree:
    """Threaded Binary Tree for efficient inorder traversal without stack."""

    def __init__(self):
        self.root = None

    def insert(self, key, value=None):
        node = ThreadedBinaryTreeNode(key, value)
        if self.root is None:
            self.root = node
            return

        current = self.root
        while True:
            if key < current.key:
                if current.left_thread or current.left is None:
                    node.left = current.left
                    node.left_thread = current.left_thread
                    node.right = current
                    node.right_thread = True
                    current.left = node
                    current.left_thread = False
                    return
                current = current.left
            else:
                if current.right_thread or current.right is None:
                    node.right = current.right
                    node.right_thread = current.right_thread
                    node.left = current
                    node.left_thread = True
                    current.right = node
                    current.right_thread = False
                    return
                current = current.right

    def inorder(self):
        """Inorder traversal using threads (no recursion/stack needed)."""
        result = []
        current = self._leftmost(self.root)
        while current:
            result.append((current.key, current.value))
            if current.right_thread:
                current = current.right
            else:
                current = self._leftmost(current.right)
        return result

    def _leftmost(self, node):
        if node is None:
            return None
        while node.left and not node.left_thread:
            node = node.left
        return node


class RBColor:
    RED = True
    BLACK = False


class RBNode:
    def __init__(self, key, value=None, color=RBColor.RED):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.parent = None
        self.color = color


class RedBlackTree:
    """Red-Black Tree for balanced indexing."""

    def __init__(self):
        self.nil = RBNode(None, color=RBColor.BLACK)
        self.root = self.nil

    def insert(self, key, value=None):
        node = RBNode(key, value)
        node.left = self.nil
        node.right = self.nil

        parent = None
        current = self.root

        while current != self.nil:
            parent = current
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                current.value = value
                return

        node.parent = parent
        if parent is None:
            self.root = node
        elif key < parent.key:
            parent.left = node
        else:
            parent.right = node

        self._fix_insert(node)

    def _fix_insert(self, z):
        while z.parent and z.parent.color == RBColor.RED:
            if z.parent.parent is None:
                break
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == RBColor.RED:
                    z.parent.color = RBColor.BLACK
                    y.color = RBColor.BLACK
                    z.parent.parent.color = RBColor.RED
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        z = z.parent
                        self._rotate_left(z)
                    z.parent.color = RBColor.BLACK
                    z.parent.parent.color = RBColor.RED
                    self._rotate_right(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y.color == RBColor.RED:
                    z.parent.color = RBColor.BLACK
                    y.color = RBColor.BLACK
                    z.parent.parent.color = RBColor.RED
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._rotate_right(z)
                    z.parent.color = RBColor.BLACK
                    z.parent.parent.color = RBColor.RED
                    self._rotate_left(z.parent.parent)
        self.root.color = RBColor.BLACK

    def _rotate_left(self, x):
        y = x.right
        x.right = y.left
        if y.left != self.nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, y):
        x = y.left
        y.left = x.right
        if x.right != self.nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is None:
            self.root = x
        elif y == y.parent.left:
            y.parent.left = x
        else:
            y.parent.right = x
        x.right = y
        y.parent = x

    def search(self, key):
        node = self.root
        while node != self.nil:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node != self.nil:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)


class BTreeNode:
    def __init__(self, t, leaf=True):
        self.t = t  # minimum degree
        self.keys = []
        self.values = []
        self.children = []
        self.leaf = leaf


class BTree:
    """B-Tree for disk-optimized data storage."""

    def __init__(self, t=3):
        self.t = t
        self.root = BTreeNode(t)

    def search(self, key, node=None):
        if node is None:
            node = self.root
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self.search(key, node.children[i])

    def insert(self, key, value=None):
        root = self.root
        if len(root.keys) == 2 * self.t - 1:
            new_root = BTreeNode(self.t, leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_nonfull(self.root, key, value)

    def _insert_nonfull(self, node, key, value):
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_nonfull(node.children[i], key, value)

    def _split_child(self, parent, i):
        t = self.t
        child = parent.children[i]
        new_node = BTreeNode(t, child.leaf)

        parent.keys.insert(i, child.keys[t - 1])
        parent.values.insert(i, child.values[t - 1])
        parent.children.insert(i + 1, new_node)

        new_node.keys = child.keys[t:]
        new_node.values = child.values[t:]
        child.keys = child.keys[:t - 1]
        child.values = child.values[:t - 1]

        if not child.leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]


class BPlusTreeNode:
    def __init__(self, t, leaf=True):
        self.t = t
        self.keys = []
        self.values = []  # only in leaf nodes
        self.children = []  # only in internal nodes
        self.leaf = leaf
        self.next = None  # linked list pointer for leaf nodes


class BPlusTree:
    """B+ Tree for range queries."""

    def __init__(self, t=3):
        self.t = t
        self.root = BPlusTreeNode(t)

    def search(self, key):
        node = self._find_leaf(key)
        for i, k in enumerate(node.keys):
            if k == key:
                return node.values[i]
        return None

    def _find_leaf(self, key):
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    def insert(self, key, value=None):
        leaf = self._find_leaf(key)

        # Insert into leaf
        i = 0
        while i < len(leaf.keys) and key > leaf.keys[i]:
            i += 1
        if i < len(leaf.keys) and leaf.keys[i] == key:
            leaf.values[i] = value
            return

        leaf.keys.insert(i, key)
        leaf.values.insert(i, value)

        if len(leaf.keys) > 2 * self.t - 1:
            self._split_leaf(leaf)

    def _split_leaf(self, leaf):
        t = self.t
        mid = len(leaf.keys) // 2

        new_leaf = BPlusTreeNode(t, leaf=True)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.values = leaf.values[mid:]
        new_leaf.next = leaf.next
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        leaf.next = new_leaf

        if leaf == self.root:
            new_root = BPlusTreeNode(t, leaf=False)
            new_root.keys = [new_leaf.keys[0]]
            new_root.children = [leaf, new_leaf]
            self.root = new_root

    def range_query(self, low, high):
        """Get all entries in [low, high] range."""
        result = []
        leaf = self._find_leaf(low)
        while leaf:
            for i, k in enumerate(leaf.keys):
                if k > high:
                    return result
                if k >= low:
                    result.append((k, leaf.values[i]))
            leaf = leaf.next
        return result
