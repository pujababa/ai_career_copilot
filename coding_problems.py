# coding_problems.py
"""
Starter Question Bank for Placement-Oriented Coding Assessment.
Contains Easy and Medium Python problems across core topics:
Arrays, Strings, Searching, Sorting, Hashing, Two Pointers, Stack, Queue, Linked List.
"""

CODING_PROBLEMS = [
    {
        "id": "two_sum",
        "title": "Two Sum",
        "topic": "Arrays",
        "difficulty": "Easy",
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "input_format": "Line 1: Space-separated integers representing nums.\nLine 2: Integer target.",
        "output_format": "List of two indices [i, j].",
        "constraints": "2 <= len(nums) <= 10^4, -10^9 <= nums[i] <= 10^9",
        "examples": [
            {
                "input": "2 7 11 15\n9",
                "output": "[0, 1]",
                "explanation": "Because nums[0] + nums[1] == 2 + 7 == 9, we return [0, 1]."
            },
            {
                "input": "3 2 4\n6",
                "output": "[1, 2]",
                "explanation": "nums[1] + nums[2] == 2 + 4 == 6, we return [1, 2]."
            }
        ],
        "initial_code": "def two_sum(nums, target):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ([2, 7, 11, 15], 9), "expected": [0, 1]},
            {"input": ([3, 2, 4], 6), "expected": [1, 2]},
            {"input": ([3, 3], 6), "expected": [0, 1]},
            {"input": ([1, 5, 8, 3, 9], 12), "expected": [3, 4]},
            {"input": ([-1, -2, -3, -4, -5], -8), "expected": [2, 4]}
        ]
    },
    {
        "id": "valid_palindrome",
        "title": "Valid Palindrome",
        "topic": "Strings",
        "difficulty": "Easy",
        "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Return `True` if it is a palindrome, or `False` otherwise.",
        "input_format": "String s.",
        "output_format": "Boolean True or False.",
        "constraints": "1 <= s.length <= 2 * 10^5",
        "examples": [
            {
                "input": "A man, a plan, a canal: Panama",
                "output": "True",
                "explanation": "\"amanaplanacanalpanama\" is a palindrome."
            },
            {
                "input": "race a car",
                "output": "False",
                "explanation": "\"raceacar\" is not a palindrome."
            }
        ],
        "initial_code": "def is_palindrome(s):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ("A man, a plan, a canal: Panama",), "expected": True},
            {"input": ("race a car",), "expected": False},
            {"input": (" ",), "expected": True},
            {"input": ("No 'x' in Nixon",), "expected": True},
            {"input": ("hello world",), "expected": False}
        ]
    },
    {
        "id": "binary_search",
        "title": "Binary Search",
        "topic": "Searching",
        "difficulty": "Easy",
        "description": "Given an array of integers `nums` sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, return its index. Otherwise, return -1.",
        "input_format": "Line 1: Sorted space-separated integers.\nLine 2: Target integer.",
        "output_format": "Integer index or -1.",
        "constraints": "1 <= nums.length <= 10^4",
        "examples": [
            {
                "input": "-1 0 3 5 9 12\n9",
                "output": "4",
                "explanation": "9 exists in nums and its index is 4."
            }
        ],
        "initial_code": "def binary_search(nums, target):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ([-1, 0, 3, 5, 9, 12], 9), "expected": 4},
            {"input": ([-1, 0, 3, 5, 9, 12], 2), "expected": -1},
            {"input": ([5], 5), "expected": 0},
            {"input": ([2, 4, 6, 8, 10], 10), "expected": 4},
            {"input": ([1, 3, 5, 7, 9], 1), "expected": 0}
        ]
    },
    {
        "id": "reverse_string",
        "title": "Reverse String",
        "topic": "Two Pointers",
        "difficulty": "Easy",
        "description": "Write a function that reverses a string given as a list of characters `s`. Return the reversed list.",
        "input_format": "List of characters.",
        "output_format": "Reversed list of characters.",
        "constraints": "1 <= s.length <= 10^5",
        "examples": [
            {
                "input": "[\"h\",\"e\",\"l\",\"l\",\"o\"]",
                "output": "[\"o\",\"l\",\"l\",\"e\",\"h\"]"
            }
        ],
        "initial_code": "def reverse_string(s):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": (["h", "e", "l", "l", "o"],), "expected": ["o", "l", "l", "e", "h"]},
            {"input": (["H", "a", "n", "n", "a", "h"],), "expected": ["h", "a", "n", "n", "a", "H"]},
            {"input": (["a"],), "expected": ["a"]}
        ]
    },
    {
        "id": "valid_parentheses",
        "title": "Valid Parentheses",
        "topic": "Stack",
        "difficulty": "Easy",
        "description": "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Open brackets must be closed by the same type of brackets and in the correct order.",
        "input_format": "String s.",
        "output_format": "Boolean True or False.",
        "constraints": "1 <= s.length <= 10^4",
        "examples": [
            {
                "input": "()[]{}",
                "output": "True"
            },
            {
                "input": "(]",
                "output": "False"
            }
        ],
        "initial_code": "def is_valid_parentheses(s):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ("()",), "expected": True},
            {"input": ("()[]{}",), "expected": True},
            {"input": ("(]",), "expected": False},
            {"input": ("([)]",), "expected": False},
            {"input": ("{[]}",), "expected": True}
        ]
    },
    {
        "id": "max_subarray",
        "title": "Maximum Subarray (Kadane's Algorithm)",
        "topic": "Arrays",
        "difficulty": "Medium",
        "description": "Given an integer array `nums`, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
        "input_format": "Space-separated integers.",
        "output_format": "Integer sum.",
        "constraints": "1 <= nums.length <= 10^5",
        "examples": [
            {
                "input": "-2 1 -3 4 -1 2 1 -5 4",
                "output": "6",
                "explanation": "[4, -1, 2, 1] has the largest sum = 6."
            }
        ],
        "initial_code": "def max_subarray(nums):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ([-2, 1, -3, 4, -1, 2, 1, -5, 4],), "expected": 6},
            {"input": ([1],), "expected": 1},
            {"input": ([5, 4, -1, 7, 8],), "expected": 23},
            {"input": ([-1, -2, -3],), "expected": -1}
        ]
    },
    {
        "id": "first_non_repeating",
        "title": "First Non-Repeating Character",
        "topic": "Hashing",
        "difficulty": "Medium",
        "description": "Given a string `s`, find the first non-repeating character in it and return its index. If it does not exist, return -1.",
        "input_format": "String s.",
        "output_format": "Integer index.",
        "constraints": "1 <= s.length <= 10^5",
        "examples": [
            {
                "input": "leetcode",
                "output": "0"
            },
            {
                "input": "loveleetcode",
                "output": "2"
            }
        ],
        "initial_code": "def first_uniq_char(s):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ("leetcode",), "expected": 0},
            {"input": ("loveleetcode",), "expected": 2},
            {"input": ("aabb",), "expected": -1},
            {"input": ("z",), "expected": 0}
        ]
    },
    {
        "id": "queue_using_stacks",
        "title": "Implement Queue using Stacks",
        "topic": "Queue",
        "difficulty": "Medium",
        "description": "Implement a first in first out (FIFO) queue using python lists. Provide a function `process_operations(ops)` that takes a list of operations: 'push X', 'pop', 'peek', 'empty' and returns the list of outputs for 'pop', 'peek', 'empty'.",
        "input_format": "List of string commands.",
        "output_format": "List of return values.",
        "constraints": "Operations <= 100",
        "examples": [
            {
                "input": "['push 1', 'push 2', 'peek', 'pop', 'empty']",
                "output": "[1, 1, False]"
            }
        ],
        "initial_code": "def process_queue_ops(ops):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {
                "input": (["push 1", "push 2", "peek", "pop", "empty"],),
                "expected": [1, 1, False]
            },
            {
                "input": (["push 10", "pop", "empty"],),
                "expected": [10, True]
            }
        ]
    },
    {
        "id": "merge_sorted_arrays",
        "title": "Merge Sorted Arrays",
        "topic": "Sorting",
        "difficulty": "Easy",
        "description": "Given two sorted integer arrays `arr1` and `arr2`, merge them into a single sorted array and return it.",
        "input_format": "Two lists of integers.",
        "output_format": "Merged sorted list.",
        "constraints": "0 <= arr1.length, arr2.length <= 10^4",
        "examples": [
            {
                "input": "[1, 3, 5], [2, 4, 6]",
                "output": "[1, 2, 3, 4, 5, 6]"
            }
        ],
        "initial_code": "def merge_sorted(arr1, arr2):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ([1, 3, 5], [2, 4, 6]), "expected": [1, 2, 3, 4, 5, 6]},
            {"input": ([], [1, 2]), "expected": [1, 2]},
            {"input": ([5, 10], [1, 2, 3]), "expected": [1, 2, 3, 5, 10]}
        ]
    },
    {
        "id": "reverse_linked_list",
        "title": "Reverse Linked List Representation",
        "topic": "Linked List",
        "difficulty": "Easy",
        "description": "Given an array `head` representing values of a singly linked list, return an array representing the reversed linked list.",
        "input_format": "List of integers.",
        "output_format": "Reversed list of integers.",
        "constraints": "0 <= head.length <= 5000",
        "examples": [
            {
                "input": "[1, 2, 3, 4, 5]",
                "output": "[5, 4, 3, 2, 1]"
            }
        ],
        "initial_code": "def reverse_list(head):\n    # Write your Python code here\n    pass\n",
        "test_cases": [
            {"input": ([1, 2, 3, 4, 5],), "expected": [5, 4, 3, 2, 1]},
            {"input": ([1, 2],), "expected": [2, 1]},
            {"input": ([],), "expected": []}
        ]
    }
]
