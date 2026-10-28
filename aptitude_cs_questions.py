# aptitude_cs_questions.py
"""
Comprehensive Question Bank for Aptitude Preparation and CS Fundamentals MCQs.
Provides placement-oriented, beginner to intermediate level questions with clear explanations.
"""

APTITUDE_QUESTIONS = [
    # ---------------- QUANTITATIVE APTITUDE ----------------
    {
        "id": "quant_1",
        "category": "Quantitative",
        "topic": "Percentage",
        "difficulty": "Easy",
        "question": "If 20% of a number is 50, what is 60% of that number?",
        "options": ["100", "150", "200", "250"],
        "correct": 1, # Index 1 -> "150"
        "explanation": "Let the number be X. 0.20 * X = 50 => X = 250. 60% of 250 = 0.60 * 250 = 150."
    },
    {
        "id": "quant_2",
        "category": "Quantitative",
        "topic": "Percentage",
        "difficulty": "Medium",
        "question": "A student multiplies a number by 3/5 instead of 5/3. What is the percentage error in the calculation?",
        "options": ["34%", "44%", "64%", "74%"],
        "correct": 2,
        "explanation": "Let the number be 15 (LCM of 3 and 5). Correct value = 15 * (5/3) = 25. Incorrect value = 15 * (3/5) = 9. Error = 25 - 9 = 16. % Error = (16/25) * 100 = 64%."
    },
    {
        "id": "quant_3",
        "category": "Quantitative",
        "topic": "Profit and Loss",
        "difficulty": "Easy",
        "question": "An item bought for $80 is sold for $100. What is the profit percentage?",
        "options": ["20%", "25%", "30%", "15%"],
        "correct": 1,
        "explanation": "Profit = Selling Price - Cost Price = 100 - 80 = 20. Profit % = (20 / 80) * 100 = 25%."
    },
    {
        "id": "quant_4",
        "category": "Quantitative",
        "topic": "Profit and Loss",
        "difficulty": "Medium",
        "question": "By selling an article for $720, a shopkeeper incurs a loss of 10%. At what price must he sell it to gain 20%?",
        "options": ["$800", "$900", "$960", "$1000"],
        "correct": 2,
        "explanation": "Selling Price = 90% of Cost Price = 720 => Cost Price = 720 / 0.9 = 800. For 20% gain, SP = 800 * 1.20 = $960."
    },
    {
        "id": "quant_5",
        "category": "Quantitative",
        "topic": "Ratio and Proportion",
        "difficulty": "Easy",
        "question": "If A : B = 2 : 3 and B : C = 4 : 5, find A : B : C.",
        "options": ["8 : 12 : 15", "6 : 9 : 10", "2 : 4 : 5", "8 : 10 : 15"],
        "correct": 0,
        "explanation": "Multiply A:B by 4 -> 8:12. Multiply B:C by 3 -> 12:15. So A : B : C = 8 : 12 : 15."
    },
    {
        "id": "quant_6",
        "category": "Quantitative",
        "topic": "Average",
        "difficulty": "Easy",
        "question": "Find the average of the first 5 prime numbers.",
        "options": ["5.2", "5.6", "6.0", "6.2"],
        "correct": 1,
        "explanation": "First 5 prime numbers are 2, 3, 5, 7, 11. Sum = 28. Average = 28 / 5 = 5.6."
    },
    {
        "id": "quant_7",
        "category": "Quantitative",
        "topic": "Time and Work",
        "difficulty": "Medium",
        "question": "A can complete a task in 10 days, and B can complete it in 15 days. How many days will they take working together?",
        "options": ["5 days", "6 days", "7 days", "8 days"],
        "correct": 1,
        "explanation": "A's 1-day work = 1/10. B's 1-day work = 1/15. Combined 1-day work = 1/10 + 1/15 = 5/30 = 1/6. Total time = 6 days."
    },
    {
        "id": "quant_8",
        "category": "Quantitative",
        "topic": "Time, Speed and Distance",
        "difficulty": "Medium",
        "question": "A train traveling at 60 km/h crosses a pole in 9 seconds. What is the length of the train?",
        "options": ["120 meters", "150 meters", "180 meters", "200 meters"],
        "correct": 1,
        "explanation": "Speed in m/s = 60 * (5/18) = 50/3 m/s. Length = Speed * Time = (50/3) * 9 = 150 meters."
    },
    {
        "id": "quant_9",
        "category": "Quantitative",
        "topic": "Simple Interest",
        "difficulty": "Easy",
        "question": "Calculate the simple interest on $2000 at an annual interest rate of 5% for 3 years.",
        "options": ["$250", "$300", "$350", "$400"],
        "correct": 1,
        "explanation": "Simple Interest = (P * R * T) / 100 = (2000 * 5 * 3) / 100 = $300."
    },
    {
        "id": "quant_10",
        "category": "Quantitative",
        "topic": "Compound Interest",
        "difficulty": "Medium",
        "question": "What is the compound interest on $10,000 at 10% per annum for 2 years compounded annually?",
        "options": ["$2,000", "$2,100", "$2,200", "$2,500"],
        "correct": 1,
        "explanation": "Amount = P * (1 + R/100)^T = 10000 * (1.1)^2 = 12,100. Interest = Amount - Principal = 12,100 - 10,000 = $2,100."
    },
    {
        "id": "quant_11",
        "category": "Quantitative",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "Which of the following numbers is divisible by 9?",
        "options": ["2457", "3581", "4193", "5214"],
        "correct": 0,
        "explanation": "A number is divisible by 9 if the sum of its digits is divisible by 9. Sum for 2457 = 2+4+5+7 = 18 (divisible by 9)."
    },
    {
        "id": "quant_12",
        "category": "Quantitative",
        "topic": "Probability",
        "difficulty": "Medium",
        "question": "What is the probability of rolling a sum of 7 with two standard 6-sided dice?",
        "options": ["1/6", "1/12", "5/36", "1/36"],
        "correct": 0,
        "explanation": "Pairs giving sum 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) -> 6 outcomes out of 36. Probability = 6/36 = 1/6."
    },

    # ---------------- LOGICAL REASONING ----------------
    {
        "id": "log_1",
        "category": "Logical Reasoning",
        "topic": "Number/Alphabet Series",
        "difficulty": "Easy",
        "question": "Find the next number in the series: 2, 6, 12, 20, 30, ?",
        "options": ["36", "40", "42", "44"],
        "correct": 2,
        "explanation": "Differences are +4, +6, +8, +10. Next difference is +12. 30 + 12 = 42."
    },
    {
        "id": "log_2",
        "category": "Logical Reasoning",
        "topic": "Coding-Decoding",
        "difficulty": "Easy",
        "question": "If 'COMPUTER' is coded as 'RFUVQNPC', how is 'MEDICINE' coded?",
        "options": ["EOJDJEFM", "EOJDEJFM", "MFEJDJOE", "EOJDJFME"],
        "correct": 0,
        "explanation": "Reverse the letters and add +1 to each letter. Reverse of MEDICINE is ENICIDEM. Shift +1: E->F, N->O... matches EOJDJEFM."
    },
    {
        "id": "log_3",
        "category": "Logical Reasoning",
        "topic": "Blood Relations",
        "difficulty": "Medium",
        "question": "Pointing to a photograph, a man said, 'I have no brother or sister, but that man's father is my father's son.' Whose photograph was it?",
        "options": ["His own", "His son's", "His father's", "His nephew's"],
        "correct": 1,
        "explanation": "'My father's son' = the man himself (since he has no brother). 'That man's father is me' => It is his son's photograph."
    },
    {
        "id": "log_4",
        "category": "Logical Reasoning",
        "topic": "Direction Sense",
        "difficulty": "Easy",
        "question": "Rahul walks 5 km North, turns right and walks 3 km, then turns right again and walks 5 km. How far is he from his starting point?",
        "options": ["3 km", "5 km", "8 km", "13 km"],
        "correct": 0,
        "explanation": "Going North 5 km and South 5 km cancels out vertical displacement. Horizontal shift is 3 km East. Distance = 3 km."
    },
    {
        "id": "log_5",
        "category": "Logical Reasoning",
        "topic": "Syllogism",
        "difficulty": "Medium",
        "question": "Statements: All cats are dogs. All dogs are birds.\nConclusion I: All cats are birds.\nConclusion II: All birds are cats.",
        "options": ["Only I follows", "Only II follows", "Both I & II follow", "Neither follows"],
        "correct": 0,
        "explanation": "Cats ⊂ Dogs ⊂ Birds. Therefore, All cats are birds (I is True). All birds are cats is not necessarily true."
    },
    {
        "id": "log_6",
        "category": "Logical Reasoning",
        "topic": "Seating Arrangement",
        "difficulty": "Medium",
        "question": "A, B, C, D, E are sitting in a row facing North. C is to the immediate right of D. B is at an extreme end and E is next to B. A is to the left of C. Who is sitting in the middle?",
        "options": ["A", "C", "D", "E"],
        "correct": 1,
        "explanation": "Order from left to right: E, B, A, C, D or B, E, A, C, D. In both arrangements with C right of D, C sits in the middle."
    },

    # ---------------- VERBAL ABILITY ----------------
    {
        "id": "verb_1",
        "category": "Verbal Ability",
        "topic": "Grammar",
        "difficulty": "Easy",
        "question": "Choose the correct sentence:",
        "options": [
            "Neither of the answers are correct.",
            "Neither of the answers is correct.",
            "Neither of answers were correct.",
            "Neither of the answer is correct."
        ],
        "correct": 1,
        "explanation": "'Neither' is a singular pronoun and takes a singular verb 'is'."
    },
    {
        "id": "verb_2",
        "category": "Verbal Ability",
        "topic": "Vocabulary",
        "difficulty": "Easy",
        "question": "Find the synonym of 'CANDID':",
        "options": ["Frank", "Secretive", "Deceptive", "Arrogant"],
        "correct": 0,
        "explanation": "'CANDID' means truthful, straightforward, or frank."
    },
    {
        "id": "verb_3",
        "category": "Verbal Ability",
        "topic": "Sentence Correction",
        "difficulty": "Medium",
        "question": "Identify the error in: 'He is superior than me in technical knowledge.'",
        "options": ["superior than", "in technical", "He is", "No error"],
        "correct": 0,
        "explanation": "Latin comparative adjectives like 'superior', 'inferior', 'prior' take 'to' instead of 'than'. Correct: 'superior to me'."
    },
    {
        "id": "verb_4",
        "category": "Verbal Ability",
        "topic": "Reading Comprehension",
        "difficulty": "Medium",
        "question": "Passage: 'Artificial Intelligence is rapidly reshaping industries by automating repetitive tasks, allowing humans to focus on creative problem solving.' What is the main idea?",
        "options": [
            "AI will replace all human workers completely.",
            "AI automates tasks so humans can focus on creative tasks.",
            "Repetitive tasks are unnecessary in industry.",
            "Creative problem solving is no longer valued."
        ],
        "correct": 1,
        "explanation": "The passage explicitly states AI automates repetitive tasks to allow human focus on creative problem solving."
    }
]


CS_MCQ_QUESTIONS = [
    # ---------------- DATA STRUCTURES & ALGORITHMS (DSA) ----------------
    {
        "id": "dsa_1",
        "subject": "DSA",
        "topic": "Time Complexity",
        "difficulty": "Easy",
        "question": "What is the average time complexity of searching an element in a balanced Binary Search Tree (BST)?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
        "correct": 2,
        "explanation": "In a balanced BST, the height is log(n), so search time complexity is O(log n)."
    },
    {
        "id": "dsa_2",
        "subject": "DSA",
        "topic": "Sorting",
        "difficulty": "Medium",
        "question": "Which sorting algorithm has a worst-case time complexity of O(n^2) but an average-case of O(n log n)?",
        "options": ["Merge Sort", "Quick Sort", "Heap Sort", "Bubble Sort"],
        "correct": 1,
        "explanation": "Quick Sort has worst-case O(n^2) when pivot selection is poor, but average-case O(n log n)."
    },
    {
        "id": "dsa_3",
        "subject": "DSA",
        "topic": "Stacks & Queues",
        "difficulty": "Easy",
        "question": "Which data structure operates on a Last In, First Out (LIFO) basis?",
        "options": ["Queue", "Stack", "Array", "Linked List"],
        "correct": 1,
        "explanation": "A Stack follows LIFO (Last In First Out), while Queue follows FIFO (First In First Out)."
    },

    # ---------------- OBJECT-ORIENTED PROGRAMMING (OOP) ----------------
    {
        "id": "oop_1",
        "subject": "OOP",
        "topic": "Polymorphism",
        "difficulty": "Easy",
        "question": "Which concept allows a function or method to operate in different ways based on the input parameters?",
        "options": ["Encapsulation", "Inheritance", "Polymorphism", "Abstraction"],
        "correct": 2,
        "explanation": "Polymorphism (specifically Method Overloading) allows the same function name to behave differently."
    },
    {
        "id": "oop_2",
        "subject": "OOP",
        "topic": "Encapsulation",
        "difficulty": "Medium",
        "question": "How is Encapsulation primarily achieved in programming languages like Java or C++?",
        "options": [
            "By making all class variables public",
            "By binding data and functions into a single unit and using private access specifiers",
            "By creating derived classes",
            "By using virtual functions"
        ],
        "correct": 1,
        "explanation": "Encapsulation wraps data and methods together while hiding internal state via private attributes and public getters/setters."
    },

    # ---------------- DATABASE MANAGEMENT SYSTEMS (DBMS) ----------------
    {
        "id": "dbms_1",
        "subject": "DBMS",
        "topic": "ACID Properties",
        "difficulty": "Easy",
        "question": "In ACID properties of database transactions, what does 'A' stand for?",
        "options": ["Availability", "Atomicity", "Accuracy", "Authentication"],
        "correct": 1,
        "explanation": "ACID stands for Atomicity, Consistency, Isolation, Durability. Atomicity ensures all-or-nothing execution."
    },
    {
        "id": "dbms_2",
        "subject": "DBMS",
        "topic": "Normalization",
        "difficulty": "Medium",
        "question": "Which normal form eliminates partial functional dependency on a composite primary key?",
        "options": ["1NF", "2NF", "3NF", "BCNF"],
        "correct": 1,
        "explanation": "2NF (Second Normal Form) requires 1NF and eliminates partial dependencies."
    },

    # ---------------- SQL ----------------
    {
        "id": "sql_1",
        "subject": "SQL",
        "topic": "Joins",
        "difficulty": "Easy",
        "question": "Which SQL JOIN returns all records when there is a match in either the left or right table?",
        "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"],
        "correct": 3,
        "explanation": "FULL OUTER JOIN returns all rows from both tables, filling NULLs where matches do not exist."
    },
    {
        "id": "sql_2",
        "subject": "SQL",
        "topic": "Aggregation",
        "difficulty": "Medium",
        "question": "Which SQL clause is used to filter group results after a GROUP BY clause?",
        "options": ["WHERE", "HAVING", "ORDER BY", "FILTER"],
        "correct": 1,
        "explanation": "HAVING filters aggregated records created by GROUP BY, whereas WHERE filters individual rows before grouping."
    },

    # ---------------- OPERATING SYSTEMS (OS) ----------------
    {
        "id": "os_1",
        "subject": "Operating Systems",
        "topic": "Deadlocks",
        "difficulty": "Medium",
        "question": "Which of the following is NOT one of Coffman's four necessary conditions for a deadlock?",
        "options": ["Mutual Exclusion", "Hold and Wait", "Preemption Allowed", "Circular Wait"],
        "correct": 2,
        "explanation": "Deadlock requires No Preemption. If preemption is allowed, deadlocks can be prevented."
    },
    {
        "id": "os_2",
        "subject": "Operating Systems",
        "topic": "Memory Management",
        "difficulty": "Easy",
        "question": "What is Virtual Memory?",
        "options": [
            "Extremely fast CPU cache memory",
            "A memory management technique that gives an illusion of a large main memory using secondary storage",
            "ROM used during system boot",
            "RAM installed in virtual machines"
        ],
        "correct": 1,
        "explanation": "Virtual Memory allows execution of processes larger than physical RAM by paging data to secondary disk storage."
    },

    # ---------------- COMPUTER NETWORKS ----------------
    {
        "id": "cn_1",
        "subject": "Computer Networks",
        "topic": "OSI Model",
        "difficulty": "Easy",
        "question": "Which layer of the OSI model is responsible for end-to-end communication, error recovery, and flow control?",
        "options": ["Network Layer", "Transport Layer", "Data Link Layer", "Session Layer"],
        "correct": 1,
        "explanation": "The Transport Layer (Layer 4, e.g. TCP) handles segment flow control, error recovery, and port addressing."
    },
    {
        "id": "cn_2",
        "subject": "Computer Networks",
        "topic": "Protocols",
        "difficulty": "Medium",
        "question": "On which port does HTTPS operate by default?",
        "options": ["80", "21", "443", "8080"],
        "correct": 2,
        "explanation": "HTTP defaults to port 80, whereas secure HTTPS operates on port 443."
    },

    # ---------------- PYTHON ----------------
    {
        "id": "py_1",
        "subject": "Python",
        "topic": "Data Types",
        "difficulty": "Easy",
        "question": "Which of the following Python data structures is IMMUTABLE?",
        "options": ["List", "Dictionary", "Set", "Tuple"],
        "correct": 3,
        "explanation": "Tuples are immutable sequences in Python; their elements cannot be changed after creation."
    },
    {
        "id": "py_2",
        "subject": "Python",
        "topic": "Memory Management",
        "difficulty": "Medium",
        "question": "What does the `is` operator compare in Python?",
        "options": [
            "Object values/content equality",
            "Memory reference / object identity",
            "Data types only",
            "String lengths"
        ],
        "correct": 1,
        "explanation": "`==` checks value equality, whereas `is` checks whether two variables point to the exact same object in memory (`id(a) == id(b)`)."
    },

    # ---------------- C++ ----------------
    {
        "id": "cpp_1",
        "subject": "C++",
        "topic": "Pointers & Memory",
        "difficulty": "Easy",
        "question": "Which operator is used to deallocate memory allocated with `new` in C++?",
        "options": ["free()", "delete", "remove", "destruct"],
        "correct": 1,
        "explanation": "`delete` (or `delete[]` for arrays) is used in C++ to free dynamically allocated heap memory created with `new`."
    },
    {
        "id": "cpp_2",
        "subject": "C++",
        "topic": "OOP Concepts",
        "difficulty": "Medium",
        "question": "What is a virtual function in C++?",
        "options": [
            "A function defined in a header file",
            "A member function declared in a base class and overridden in a derived class for runtime polymorphism",
            "A function with no body",
            "A private helper function"
        ],
        "correct": 1,
        "explanation": "Virtual functions enable dynamic (runtime) dispatch/polymorphism in C++ when called through base class pointers."
    },

    # ---------------- MORE DATA STRUCTURES & ALGORITHMS ----------------
    {
        "id": "dsa_4",
        "subject": "DSA",
        "topic": "Hash Tables",
        "difficulty": "Easy",
        "question": "What is the average time complexity for insertion, deletion, and lookup in a Hash Table?",
        "options": ["O(log n)", "O(1)", "O(n)", "O(n log n)"],
        "correct": 1,
        "explanation": "Hash Tables achieve O(1) average time complexity through hash mapping, with O(n) worst-case under severe hash collisions."
    },
    {
        "id": "dsa_5",
        "subject": "DSA",
        "topic": "Graphs",
        "difficulty": "Medium",
        "question": "Which algorithm is commonly used to find the shortest path in a weighted graph with non-negative edge weights?",
        "options": ["Dijkstra's Algorithm", "Kruskal's Algorithm", "Prim's Algorithm", "Tarjan's Algorithm"],
        "correct": 0,
        "explanation": "Dijkstra's algorithm finds single-source shortest paths in graphs with non-negative edge weights in O(V^2) or O(E + V log V) with a priority queue."
    },
    {
        "id": "dsa_6",
        "subject": "DSA",
        "topic": "Trees",
        "difficulty": "Medium",
        "question": "In which tree traversal is the root node visited after both left and right subtrees?",
        "options": ["Pre-order", "In-order", "Post-order", "Level-order"],
        "correct": 2,
        "explanation": "Post-order traversal follows: Left Subtree -> Right Subtree -> Root node."
    },
    {
        "id": "dsa_7",
        "subject": "DSA",
        "topic": "Sorting",
        "difficulty": "Hard",
        "question": "What is the worst-case space complexity of standard Merge Sort on an array of size n?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
        "correct": 2,
        "explanation": "Standard Merge Sort requires O(n) auxiliary space to store temporary arrays during the merge phase."
    },

    # ---------------- MORE DATABASE MANAGEMENT SYSTEMS (DBMS) ----------------
    {
        "id": "dbms_3",
        "subject": "DBMS",
        "topic": "Transactions",
        "difficulty": "Medium",
        "question": "What isolation level prevents Dirty Reads, Non-repeatable Reads, and Phantom Reads?",
        "options": ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"],
        "correct": 3,
        "explanation": "Serializable is the highest transaction isolation level and prevents dirty reads, non-repeatable reads, and phantom reads."
    },
    {
        "id": "dbms_4",
        "subject": "DBMS",
        "topic": "Indexing",
        "difficulty": "Medium",
        "question": "Which data structure is most widely used for indexing in relational database engines like MySQL and PostgreSQL?",
        "options": ["B+ Tree", "AVL Tree", "Red-Black Tree", "Binary Heap"],
        "correct": 0,
        "explanation": "B+ Trees keep all records in leaf nodes connected as a linked list, making range queries and sequential disk reads extremely efficient."
    },
    {
        "id": "dbms_5",
        "subject": "DBMS",
        "topic": "Keys",
        "difficulty": "Easy",
        "question": "What is a Foreign Key in a relational database?",
        "options": [
            "A key that uniquely identifies a row in its own table",
            "A column or set of columns in one table referencing the Primary Key of another table",
            "An index that cannot contain NULL values",
            "A key used for encrypting database tables"
        ],
        "correct": 1,
        "explanation": "A Foreign Key establishes referential integrity between two tables by matching the primary key of the referenced table."
    },
    {
        "id": "dbms_6",
        "subject": "DBMS",
        "topic": "Concurrency Control",
        "difficulty": "Hard",
        "question": "In the Two-Phase Locking (2PL) protocol, when does the shrinking phase begin?",
        "options": [
            "When the first lock is acquired",
            "When the first lock is released",
            "When the transaction commits",
            "When a deadlock is detected"
        ],
        "correct": 1,
        "explanation": "In 2PL, the growing phase acquires locks without releasing any. As soon as the first lock is released, the shrinking phase begins."
    },

    # ---------------- MORE OPERATING SYSTEMS (OS) ----------------
    {
        "id": "os_3",
        "subject": "Operating Systems",
        "topic": "CPU Scheduling",
        "difficulty": "Easy",
        "question": "Which CPU scheduling algorithm gives each process a small fixed unit of CPU time (time slice/quantum)?",
        "options": ["First-Come, First-Served", "Shortest Job First", "Round Robin", "Priority Scheduling"],
        "correct": 2,
        "explanation": "Round Robin scheduling assigns a fixed time quantum cyclically to all ready processes to ensure fair preemption."
    },
    {
        "id": "os_4",
        "subject": "Operating Systems",
        "topic": "Synchronization",
        "difficulty": "Medium",
        "question": "What is the difference between a Binary Semaphore and a Mutex?",
        "options": [
            "Binary Semaphore has an integer value, Mutex is a floating point",
            "A Mutex can only be unlocked by the thread that locked it (ownership), whereas a Semaphore can be signaled by any thread",
            "There is no difference; they are exact synonyms",
            "Semaphores are implemented in hardware only"
        ],
        "correct": 1,
        "explanation": "A Mutex includes ownership semantics: only the thread that acquired the mutex can release it. A semaphore is a signaling mechanism without ownership."
    },
    {
        "id": "os_5",
        "subject": "Operating Systems",
        "topic": "Memory Management",
        "difficulty": "Medium",
        "question": "What phenomenon occurs when excessive paging causes the system to spend more time paging than executing processes?",
        "options": ["Fragmentation", "Pipelining", "Thrashing", "Starvation"],
        "correct": 2,
        "explanation": "Thrashing occurs when total memory requirements exceed physical RAM, causing the OS to continuously swap pages between RAM and disk."
    },
    {
        "id": "os_6",
        "subject": "Operating Systems",
        "topic": "Processes & Threads",
        "difficulty": "Easy",
        "question": "Which memory segment is shared among multiple threads within the same process?",
        "options": ["Stack", "Registers", "Heap and Data Segment", "Program Counter"],
        "correct": 2,
        "explanation": "Threads in the same process share Heap, Global variables, Code, and open file descriptors, but maintain separate Stacks and Registers."
    },

    # ---------------- MORE COMPUTER NETWORKS ----------------
    {
        "id": "cn_3",
        "subject": "Computer Networks",
        "topic": "TCP vs UDP",
        "difficulty": "Easy",
        "question": "Which protocol provides connection-oriented, reliable, and ordered byte-stream delivery?",
        "options": ["UDP", "IP", "TCP", "ICMP"],
        "correct": 2,
        "explanation": "TCP (Transmission Control Protocol) guarantees reliability, sequencing, and flow control using sequence numbers and ACKs."
    },
    {
        "id": "cn_4",
        "subject": "Computer Networks",
        "topic": "DNS",
        "difficulty": "Easy",
        "question": "What is the primary function of the Domain Name System (DNS)?",
        "options": [
            "Encrypt network traffic across routers",
            "Translate human-readable domain names into IP addresses",
            "Assign dynamic IP addresses to home devices",
            "Prevent Distributed Denial of Service attacks"
        ],
        "correct": 1,
        "explanation": "DNS acts as the internet's phonebook, translating domain names like google.com into IP addresses like 142.250.190.46."
    },
    {
        "id": "cn_5",
        "subject": "Computer Networks",
        "topic": "Handshake",
        "difficulty": "Medium",
        "question": "What is the sequence of packets exchanged in the TCP Three-Way Handshake?",
        "options": ["SYN -> SYN-ACK -> ACK", "ACK -> SYN -> FIN", "SYN -> ACK -> DATA", "HELLO -> ACK -> CONNECT"],
        "correct": 0,
        "explanation": "TCP connection establishment sequence is: 1) Client sends SYN, 2) Server responds with SYN-ACK, 3) Client sends ACK."
    },
    {
        "id": "cn_6",
        "subject": "Computer Networks",
        "topic": "IP Addressing",
        "difficulty": "Medium",
        "question": "How many bits are in an IPv4 address versus an IPv6 address?",
        "options": ["32 bits vs 128 bits", "64 bits vs 256 bits", "16 bits vs 64 bits", "32 bits vs 64 bits"],
        "correct": 0,
        "explanation": "IPv4 uses 32-bit addresses (e.g. 192.168.1.1), while IPv6 uses 128-bit addresses (e.g. 2001:0db8::)."
    },

    # ---------------- MORE OBJECT-ORIENTED PROGRAMMING (OOP) ----------------
    {
        "id": "oop_3",
        "subject": "OOP",
        "topic": "Inheritance",
        "difficulty": "Easy",
        "question": "What is the primary benefit of Inheritance in Object-Oriented Programming?",
        "options": ["Code reusability and establishing hierarchical relationships", "Hiding implementation details", "Faster execution speed than procedural code", "Preventing class instantiation"],
        "correct": 0,
        "explanation": "Inheritance allows child classes to inherit attributes and behaviors from parent classes, promoting code reusability."
    },
    {
        "id": "oop_4",
        "subject": "OOP",
        "topic": "Abstraction",
        "difficulty": "Medium",
        "question": "What distinguishes an Abstract Class from an Interface in languages like Java?",
        "options": [
            "An interface cannot have any variables",
            "An abstract class can provide default method implementations and state (instance variables), while pure interfaces declare method signatures",
            "Interfaces can be instantiated directly with `new`",
            "Abstract classes cannot have constructors"
        ],
        "correct": 1,
        "explanation": "Abstract classes can hold state (member variables) and concrete method implementations; interfaces primarily define contracts."
    },
    {
        "id": "oop_5",
        "subject": "OOP",
        "topic": "Design Principles",
        "difficulty": "Medium",
        "question": "In the SOLID design principles, what does 'O' stand for?",
        "options": ["Object-oriented Principle", "Open/Closed Principle", "Orderly Dependency Principle", "Optimization Principle"],
        "correct": 1,
        "explanation": "Open/Closed Principle states software entities should be open for extension, but closed for modification."
    },

    # ---------------- COMPUTER FUNDAMENTALS ----------------
    {
        "id": "cf_1",
        "subject": "Computer Fundamentals",
        "topic": "Architecture",
        "difficulty": "Easy",
        "question": "Which architecture stores both program instructions and data in the same unified memory space?",
        "options": ["Harvard Architecture", "Von Neumann Architecture", "RISC Architecture", "CISC Architecture"],
        "correct": 1,
        "explanation": "The Von Neumann architecture features a shared memory system holding both instructions and data."
    },
    {
        "id": "cf_2",
        "subject": "Computer Fundamentals",
        "topic": "Memory Hierarchy",
        "difficulty": "Easy",
        "question": "Which level of the computer memory hierarchy is the fastest and closest to the CPU core?",
        "options": ["L3 Cache", "RAM", "CPU Registers", "L1 Cache"],
        "correct": 2,
        "explanation": "CPU Registers are inside the processor execution units and provide the fastest access times (sub-nanosecond)."
    },
    {
        "id": "cf_3",
        "subject": "Computer Fundamentals",
        "topic": "Compilers & Interpreters",
        "difficulty": "Medium",
        "question": "What is the primary difference between a Compiler and an Interpreter?",
        "options": [
            "A compiler translates high-level code line-by-line during runtime, while an interpreter translates all code beforehand",
            "A compiler translates the entire source code into machine/bytecode before execution, whereas an interpreter executes instructions line-by-line",
            "Compilers are only used for Python and interpreters for C++",
            "There is no difference"
        ],
        "correct": 1,
        "explanation": "Compilers generate an executable or intermediate bytecode ahead of time, while interpreters execute instructions dynamically at runtime."
    },
    {
        "id": "cf_4",
        "subject": "Computer Fundamentals",
        "topic": "Number Systems",
        "difficulty": "Easy",
        "question": "What is the decimal equivalent of the binary number `1101`?",
        "options": ["11", "12", "13", "14"],
        "correct": 2,
        "explanation": "1*2^3 + 1*2^2 + 0*2^1 + 1*2^0 = 8 + 4 + 0 + 1 = 13."
    }
]

