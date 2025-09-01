# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: test_continue_tutorial.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:44+02:00
# === CUBIST STAMP END ===

import unittest


def sorting_algorithm(x):
    n = len(x)
    for i in range(n):
        for j in range(n - 1):
            if x[j] > x[j + 1]:
                # Swap elements if they are in the wrong order
                x[j], x[j + 1] = x[j + 1], x[j]
    return x


def sorting_algorithm2(x):
    for i in range(len(x)):
        for j in range(len(x) - 1):
            if x[j] > x[j + 1]:
                x[j], x[j + 1] = x[j + 1], x[j]
    return x


class TestSortingAlgorithms(unittest.TestCase):
    def test_sorting_algorithm_sorted(self):
        self.assertEqual(sorting_algorithm([1, 2, 3]), [1, 2, 3])

    def test_sorting_algorithm_reverse(self):
        self.assertEqual(sorting_algorithm([3, 2, 1]), [1, 2, 3])

    def test_sorting_algorithm_duplicates(self):
        self.assertEqual(sorting_algorithm([3, 1, 2, 1]), [1, 1, 2, 3])

    def test_sorting_algorithm_empty(self):
        self.assertEqual(sorting_algorithm([]), [])

    def test_sorting_algorithm_single(self):
        self.assertEqual(sorting_algorithm([42]), [42])

    def test_sorting_algorithm2_sorted(self):
        self.assertEqual(sorting_algorithm2([1, 2, 3]), [1, 2, 3])

    def test_sorting_algorithm2_reverse(self):
        self.assertEqual(sorting_algorithm2([3, 2, 1]), [1, 2, 3])

    def test_sorting_algorithm2_duplicates(self):
        self.assertEqual(sorting_algorithm2([3, 1, 2, 1]), [1, 1, 2, 3])

    def test_sorting_algorithm2_empty(self):
        self.assertEqual(sorting_algorithm2([]), [])

    def test_sorting_algorithm2_single(self):
        self.assertEqual(sorting_algorithm2([42]), [42])


if __name__ == "__main__":
    unittest.main()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:44+02:00
# === CUBIST FOOTER STAMP END ===
