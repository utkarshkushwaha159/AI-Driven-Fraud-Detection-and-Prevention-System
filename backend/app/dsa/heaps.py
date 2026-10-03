"""
Binomial and Fibonacci Heap implementations.
Used internally for efficient priority queue operations.
"""


class BinomialNode:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.degree = 0
        self.parent = None
        self.child = None
        self.sibling = None


class BinomialHeap:
    """Binomial Heap for efficient merge operations."""

    def __init__(self):
        self.head = None
        self._size = 0

    def is_empty(self):
        return self.head is None

    def insert(self, key, value=None):
        node = BinomialNode(key, value)
        h = BinomialHeap()
        h.head = node
        h._size = 1
        self._merge_heap(h)
        self._size += 1

    def find_min(self):
        if self.head is None:
            return None
        min_node = self.head
        current = self.head.sibling
        while current:
            if current.key < min_node.key:
                min_node = current
            current = current.sibling
        return (min_node.key, min_node.value)

    def extract_min(self):
        if self.head is None:
            return None

        # Find minimum
        min_node = self.head
        min_prev = None
        prev = None
        current = self.head
        while current:
            if current.key < min_node.key:
                min_node = current
                min_prev = prev
            prev = current
            current = current.sibling

        # Remove min_node from root list
        if min_prev:
            min_prev.sibling = min_node.sibling
        else:
            self.head = min_node.sibling

        # Reverse children and merge
        child = min_node.child
        h = BinomialHeap()
        prev = None
        while child:
            next_child = child.sibling
            child.sibling = prev
            child.parent = None
            prev = child
            child = next_child
        h.head = prev

        self._merge_heap(h)
        self._size -= 1
        return (min_node.key, min_node.value)

    def _merge_heap(self, other):
        """Merge another binomial heap into this one."""
        self.head = self._merge_root_lists(self.head, other.head)
        if self.head is None:
            return

        prev = None
        curr = self.head
        next_node = curr.sibling

        while next_node:
            if (curr.degree != next_node.degree or
                    (next_node.sibling and next_node.sibling.degree == curr.degree)):
                prev = curr
                curr = next_node
            elif curr.key <= next_node.key:
                curr.sibling = next_node.sibling
                self._link(next_node, curr)
            else:
                if prev:
                    prev.sibling = next_node
                else:
                    self.head = next_node
                self._link(curr, next_node)
                curr = next_node
            next_node = curr.sibling

    def _merge_root_lists(self, h1, h2):
        if h1 is None:
            return h2
        if h2 is None:
            return h1

        head = None
        tail = None
        while h1 and h2:
            if h1.degree <= h2.degree:
                node = h1
                h1 = h1.sibling
            else:
                node = h2
                h2 = h2.sibling
            node.sibling = None
            if head is None:
                head = node
                tail = node
            else:
                tail.sibling = node
                tail = node

        remaining = h1 or h2
        if tail:
            tail.sibling = remaining
        else:
            head = remaining
        return head

    def _link(self, child, parent):
        child.parent = parent
        child.sibling = parent.child
        parent.child = child
        parent.degree += 1

    def size(self):
        return self._size


class FibonacciNode:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.degree = 0
        self.parent = None
        self.child = None
        self.left = self
        self.right = self
        self.mark = False


class FibonacciHeap:
    """Fibonacci Heap for efficient decrease-key operations."""

    def __init__(self):
        self.min_node = None
        self._size = 0

    def is_empty(self):
        return self.min_node is None

    def insert(self, key, value=None):
        node = FibonacciNode(key, value)
        if self.min_node is None:
            self.min_node = node
        else:
            self._add_to_root_list(node)
            if node.key < self.min_node.key:
                self.min_node = node
        self._size += 1
        return node

    def find_min(self):
        if self.min_node:
            return (self.min_node.key, self.min_node.value)
        return None

    def extract_min(self):
        z = self.min_node
        if z is None:
            return None

        if z.child:
            child = z.child
            while True:
                next_child = child.right
                self._add_to_root_list(child)
                child.parent = None
                if next_child == z.child:
                    break
                child = next_child

        self._remove_from_root_list(z)
        if z == z.right:
            self.min_node = None
        else:
            self.min_node = z.right
            self._consolidate()

        self._size -= 1
        return (z.key, z.value)

    def decrease_key(self, node, new_key):
        if new_key > node.key:
            return
        node.key = new_key
        parent = node.parent
        if parent and node.key < parent.key:
            self._cut(node, parent)
            self._cascading_cut(parent)
        if node.key < self.min_node.key:
            self.min_node = node

    def _add_to_root_list(self, node):
        node.left = self.min_node
        node.right = self.min_node.right
        self.min_node.right.left = node
        self.min_node.right = node

    def _remove_from_root_list(self, node):
        node.left.right = node.right
        node.right.left = node.left

    def _cut(self, child, parent):
        if child.right == child:
            parent.child = None
        else:
            if parent.child == child:
                parent.child = child.right
            child.left.right = child.right
            child.right.left = child.left
        parent.degree -= 1
        self._add_to_root_list(child)
        child.parent = None
        child.mark = False

    def _cascading_cut(self, node):
        parent = node.parent
        if parent:
            if not node.mark:
                node.mark = True
            else:
                self._cut(node, parent)
                self._cascading_cut(parent)

    def _consolidate(self):
        import math
        max_degree = int(math.log2(self._size)) + 2 if self._size > 0 else 1
        degree_table = [None] * (max_degree + 1)

        nodes = []
        current = self.min_node
        if current:
            while True:
                nodes.append(current)
                current = current.right
                if current == self.min_node:
                    break

        for node in nodes:
            d = node.degree
            while d < len(degree_table) and degree_table[d]:
                other = degree_table[d]
                if node.key > other.key:
                    node, other = other, node
                self._link_nodes(other, node)
                degree_table[d] = None
                d += 1
            if d >= len(degree_table):
                degree_table.extend([None] * (d - len(degree_table) + 1))
            degree_table[d] = node

        self.min_node = None
        for node in degree_table:
            if node:
                if self.min_node is None:
                    node.left = node
                    node.right = node
                    self.min_node = node
                else:
                    self._add_to_root_list(node)
                    if node.key < self.min_node.key:
                        self.min_node = node

    def _link_nodes(self, child, parent):
        self._remove_from_root_list(child)
        child.left = child
        child.right = child
        if parent.child is None:
            parent.child = child
        else:
            child.right = parent.child.right
            child.left = parent.child
            parent.child.right.left = child
            parent.child.right = child
        child.parent = parent
        parent.degree += 1
        child.mark = False

    def size(self):
        return self._size
