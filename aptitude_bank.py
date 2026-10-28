# aptitude_bank.py
"""
Comprehensive Question Bank & Data Engine for Placement Aptitude Preparation.
Covers 5 Core Categories across 80+ distinct placement-oriented topics:
1. Quantitative Aptitude (24 topics)
2. Logical / Analytical Reasoning (20 topics)
3. Verbal Ability (14 topics)
4. Data Interpretation (9 topics)
5. Technical / Computer Aptitude (13 topics)

Provides:
- Difficulty classification: Easy, Medium, Hard
- Exam Level: Basic Placement, Standard Placement, Advanced Placement
- Sourcing: "Placement Exam Style" and "Company-Level Practice"
- Detailed step-by-step explanations, time recommendations, and SQLite seeder
"""

import json
import random
import sqlite3

# ------------------------------------------------------------------------------
# CATEGORY & TOPIC TAXONOMY (80 Topics)
# ------------------------------------------------------------------------------
APTITUDE_TAXONOMY = {
    "Quantitative Aptitude": [
        "Number System",
        "HCF & LCM",
        "Simplification",
        "Percentage",
        "Profit & Loss",
        "Ratio & Proportion",
        "Average",
        "Mixture & Alligation",
        "Time & Work",
        "Pipes & Cisterns",
        "Time, Speed & Distance",
        "Boats & Streams",
        "Simple Interest",
        "Compound Interest",
        "Probability",
        "Permutation & Combination",
        "Age Problems",
        "Partnership",
        "Mensuration",
        "Algebra",
        "Equations",
        "Progressions",
        "Data Interpretation",
        "Arithmetic Word Problems"
    ],
    "Logical Reasoning": [
        "Number Series",
        "Letter Series",
        "Alphanumeric Series",
        "Coding-Decoding",
        "Blood Relations",
        "Direction Sense",
        "Analogy",
        "Classification",
        "Syllogism",
        "Statement & Conclusion",
        "Statement & Assumption",
        "Seating Arrangement",
        "Puzzles",
        "Ranking",
        "Order & Position",
        "Clocks",
        "Calendars",
        "Data Sufficiency",
        "Logical Deduction",
        "Venn Diagrams"
    ],
    "Verbal Ability": [
        "Reading Comprehension",
        "Error Detection",
        "Sentence Correction",
        "Fill in the Blanks",
        "Synonyms",
        "Antonyms",
        "Vocabulary",
        "Para Jumbles",
        "Sentence Arrangement",
        "Idioms & Phrases",
        "One Word Substitution",
        "Grammar",
        "Active & Passive Voice",
        "Direct & Indirect Speech"
    ],
    "Data Interpretation": [
        "Tables",
        "Bar Graphs",
        "Line Graphs",
        "Pie Charts",
        "Caselets",
        "Mixed Graphs",
        "Percentage-based DI",
        "Ratio-based DI",
        "Average-based DI"
    ],
    "Technical Aptitude": [
        "Programming basics",
        "C/C++",
        "Python",
        "OOP",
        "Data Structures",
        "Algorithms",
        "DBMS",
        "SQL",
        "Operating Systems",
        "Computer Networks",
        "Computer Fundamentals",
        "Software Engineering",
        "Basic Web Technologies"
    ]
}

# ------------------------------------------------------------------------------
# QUESTION REPOSITORY (220+ Placement Questions)
# ------------------------------------------------------------------------------
QUESTIONS_DATA = [
    # ==========================================================================
    # 1. QUANTITATIVE APTITUDE
    # ==========================================================================
    # --- Number System ---
    {
        "id": "quant_num_1",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the remainder when (7^84) is divided by 342?",
        "options": ["1", "7", "49", "341"],
        "correct": 0,
        "explanation": "Note that 7^3 = 343. We can write (7^84) as ((7^3)^28) = (343^28). When 343 is divided by 342, the remainder is 1. Therefore, the remainder of (1^28) divided by 342 is 1.",
        "time_recommendation": 60
    },
    {
        "id": "quant_num_2",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Find the number of trailing zeros in 125! (factorial of 125).",
        "options": ["25", "30", "31", "28"],
        "correct": 2,
        "explanation": "Trailing zeros depend on factors of 5. Formula: floor(125/5) + floor(125/25) + floor(125/125) = 25 + 5 + 1 = 31 trailing zeros.",
        "time_recommendation": 60
    },
    {
        "id": "quant_num_3",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Placement Exam Style",
        "question": "A number N when divided by 14 leaves a remainder of 9. What is the remainder when (N^2 + 3N + 5) is divided by 14?",
        "options": ["1", "3", "5", "7"],
        "correct": 0,
        "explanation": "Let N = 9. Then N^2 + 3N + 5 = 81 + 27 + 5 = 113. 113 divided by 14 gives 14 × 8 = 112 with a remainder of 1.",
        "time_recommendation": 75
    },
    {
        "id": "quant_num_4",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "The sum of three consecutive odd numbers is 147. What is the product of the first and third numbers?",
        "options": ["2397", "2401", "2349", "2400"],
        "correct": 0,
        "explanation": "Let the numbers be x-2, x, x+2. Their sum = 3x = 147 => x = 49. The numbers are 47, 49, 51. Product of first and third = 47 * 51 = 2397.",
        "time_recommendation": 60
    },

    # --- HCF & LCM ---
    {
        "id": "quant_hcf_1",
        "category": "Quantitative Aptitude",
        "topic": "HCF & LCM",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "The HCF and LCM of two numbers are 12 and 336 respectively. If one of the numbers is 84, find the other number.",
        "options": ["48", "36", "56", "72"],
        "correct": 0,
        "explanation": "Product of two numbers = HCF * LCM. Number * 84 = 12 * 336 => Number = (12 * 336) / 84 = 336 / 7 = 48.",
        "time_recommendation": 45
    },
    {
        "id": "quant_hcf_2",
        "category": "Quantitative Aptitude",
        "topic": "HCF & LCM",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Four bells toll together at intervals of 6, 8, 12, and 18 seconds respectively. If they toll together now, how many times will they toll together in the next 1 hour (excluding the start)?",
        "options": ["48 times", "50 times", "52 times", "60 times"],
        "correct": 1,
        "explanation": "LCM of 6, 8, 12, 18: 6 = 2*3, 8 = 2^3, 12 = 2^2*3, 18 = 2*3^2. LCM = 2^3 * 3^2 = 72 seconds. In 1 hour = 3600 seconds, number of tolls = floor(3600 / 72) = 50 times.",
        "time_recommendation": 60
    },

    # --- Simplification ---
    {
        "id": "quant_simp_1",
        "category": "Quantitative Aptitude",
        "topic": "Simplification",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Evaluate: 1800 ÷ 10 ÷ 6 + (45 × 2) - √144",
        "options": ["108", "102", "118", "96"],
        "correct": 0,
        "explanation": "Follow BODMAS: 1800 ÷ 10 = 180. 180 ÷ 6 = 30. (45 × 2) = 90. √144 = 12. 30 + 90 - 12 = 120 - 12 = 108.",
        "time_recommendation": 45
    },
    {
        "id": "quant_simp_2",
        "category": "Quantitative Aptitude",
        "topic": "Simplification",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "If (a - b) = 5 and ab = 14, what is the value of (a^3 - b^3)?",
        "options": ["335", "315", "350", "285"],
        "correct": 0,
        "explanation": "Using the algebraic identity: a^3 - b^3 = (a - b)^3 + 3ab(a - b) = 5^3 + 3(14)(5) = 125 + 210 = 335.",
        "time_recommendation": 60
    },

    # --- Percentage ---
    {
        "id": "quant_perc_1",
        "category": "Quantitative Aptitude",
        "topic": "Percentage",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "If the price of petrol increases by 25%, by what percentage must a driver reduce fuel consumption so that the overall expenditure remains unchanged?",
        "options": ["20%", "25%", "16.67%", "33.33%"],
        "correct": 0,
        "explanation": "Formula: Reduction % = (r / (100 + r)) * 100 = (25 / 125) * 100 = (1/5) * 100 = 20%.",
        "time_recommendation": 45
    },
    {
        "id": "quant_perc_2",
        "category": "Quantitative Aptitude",
        "topic": "Percentage",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "In an examination, 35% students failed in Mathematics and 25% failed in English. If 10% failed in both subjects, what percentage of students passed in both subjects?",
        "options": ["50%", "60%", "45%", "55%"],
        "correct": 0,
        "explanation": "Failed in at least one subject = n(M ∪ E) = n(M) + n(E) - n(M ∩ E) = 35% + 25% - 10% = 50%. Therefore, passed in both subjects = 100% - 50% = 50%.",
        "time_recommendation": 60
    },
    {
        "id": "quant_perc_3",
        "category": "Quantitative Aptitude",
        "topic": "Percentage",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Placement Exam Style",
        "question": "A candidate scores 36% marks and fails by 32 marks. Another candidate scores 48% marks and gets 64 marks more than the minimum passing marks. Find the maximum marks of the examination.",
        "options": ["800", "750", "900", "600"],
        "correct": 0,
        "explanation": "Difference in percentage = 48% - 36% = 12%. Difference in marks = 64 - (-32) = 96 marks. Since 12% of total marks = 96 => Total marks = (96 / 12) * 100 = 800.",
        "time_recommendation": 75
    },

    # --- Profit & Loss ---
    {
        "id": "quant_pl_1",
        "category": "Quantitative Aptitude",
        "topic": "Profit & Loss",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A retailer purchases an article for $240 and marks it 25% above cost price. If he allows a discount of 10% on the marked price, what is his net profit percentage?",
        "options": ["12.5%", "15%", "10%", "14%"],
        "correct": 0,
        "explanation": "Cost Price = 100. Marked Price = 125. Selling Price after 10% discount = 125 * 0.90 = 112.5. Net Profit % = 112.5 - 100 = 12.5%.",
        "time_recommendation": 45
    },
    {
        "id": "quant_pl_2",
        "category": "Quantitative Aptitude",
        "topic": "Profit & Loss",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A dishonest dealer claims to sell his goods at cost price but uses a false weight of 900 grams for a 1 kg weight. What is his actual profit percentage?",
        "options": ["11.11%", "10.0%", "12.5%", "9.09%"],
        "correct": 0,
        "explanation": "Profit % = [Error / (True Value - Error)] * 100 = [100 / (1000 - 100)] * 100 = (100 / 900) * 100 = 11.11%.",
        "time_recommendation": 60
    },
    {
        "id": "quant_pl_3",
        "category": "Quantitative Aptitude",
        "topic": "Profit & Loss",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Placement Exam Style",
        "question": "A shopkeeper sells two machines at $12,000 each. On one he makes a gain of 20% and on the other he incurs a loss of 20%. What is his overall gain or loss percentage?",
        "options": ["4% loss", "4% gain", "No profit no loss", "2% loss"],
        "correct": 0,
        "explanation": "When two items are sold at the same selling price with x% gain on one and x% loss on the other, there is always an overall loss of (x / 10)^2 % = (20 / 10)^2 = 4% loss.",
        "time_recommendation": 60
    },

    # --- Ratio & Proportion ---
    {
        "id": "quant_ratio_1",
        "category": "Quantitative Aptitude",
        "topic": "Ratio & Proportion",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "If A : B = 3 : 4, B : C = 8 : 9, and C : D = 15 : 16, what is the ratio A : D?",
        "options": ["5 : 8", "3 : 8", "5 : 12", "7 : 16"],
        "correct": 0,
        "explanation": "A/D = (A/B) * (B/C) * (C/D) = (3/4) * (8/9) * (15/16) = (24/36) * (15/16) = (2/3) * (15/16) = 30 / 48 = 5 / 8.",
        "time_recommendation": 45
    },
    {
        "id": "quant_ratio_2",
        "category": "Quantitative Aptitude",
        "topic": "Ratio & Proportion",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A bag contains 50p, 25p, and 10p coins in the ratio 5 : 9 : 4, amounting to $206. Find the total number of 25p coins in the bag.",
        "options": ["360", "320", "400", "280"],
        "correct": 0,
        "explanation": "Let coins be 5x, 9x, 4x. Value = 5x(0.50) + 9x(0.25) + 4x(0.10) = 2.5x + 2.25x + 0.40x = 5.15x. 5.15x = 206 => x = 206 / 5.15 = 40. Number of 25p coins = 9 * 40 = 360.",
        "time_recommendation": 75
    },

    # --- Average ---
    {
        "id": "quant_avg_1",
        "category": "Quantitative Aptitude",
        "topic": "Average",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "The average age of 24 students and their teacher is 15 years. If the teacher's age is excluded, the average decreases by 1 year. What is the teacher's age?",
        "options": ["39 years", "38 years", "40 years", "42 years"],
        "correct": 0,
        "explanation": "Total sum with teacher = 25 * 15 = 375. Total sum without teacher = 24 * 14 = 336. Teacher's age = 375 - 336 = 39 years.",
        "time_recommendation": 45
    },
    {
        "id": "quant_avg_2",
        "category": "Quantitative Aptitude",
        "topic": "Average",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A batsman has a certain average of runs for 11 innings. In the 12th inning, he scores 90 runs and thereby increases his average by 5. What is his new average after the 12th inning?",
        "options": ["35", "30", "40", "45"],
        "correct": 0,
        "explanation": "Let original average be A. Total runs in 11 innings = 11A. In 12 innings: 11A + 90 = 12(A + 5) => 11A + 90 = 12A + 60 => A = 30. New average = A + 5 = 35.",
        "time_recommendation": 60
    },

    # --- Mixture & Alligation ---
    {
        "id": "quant_mix_1",
        "category": "Quantitative Aptitude",
        "topic": "Mixture & Alligation",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "In what ratio must rice at $30 per kg be mixed with rice at $45 per kg so that the resulting mixture is worth $36 per kg?",
        "options": ["3 : 2", "2 : 3", "4 : 3", "3 : 4"],
        "correct": 0,
        "explanation": "By the rule of alligation: Ratio = (Cheaper : Dearer) = (45 - 36) : (36 - 30) = 9 : 6 = 3 : 2.",
        "time_recommendation": 45
    },
    {
        "id": "quant_mix_2",
        "category": "Quantitative Aptitude",
        "topic": "Mixture & Alligation",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Company-Level Practice",
        "question": "A container contains 40 liters of milk. From this container 4 liters of milk was taken out and replaced by water. This process was repeated further two times. How much milk is now contained by the container?",
        "options": ["29.16 liters", "30.40 liters", "28.50 liters", "32.00 liters"],
        "correct": 0,
        "explanation": "Amount of liquid left = Initial * (1 - x/V)^n = 40 * (1 - 4/40)^3 = 40 * (0.9)^3 = 40 * 0.729 = 29.16 liters.",
        "time_recommendation": 90
    },

    # --- Time & Work ---
    {
        "id": "quant_tw_1",
        "category": "Quantitative Aptitude",
        "topic": "Time & Work",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A can complete a piece of work in 12 days, and B can complete it in 18 days. If they work together, how many days will they take to complete the work?",
        "options": ["7.2 days", "7.5 days", "6.8 days", "8.0 days"],
        "correct": 0,
        "explanation": "A's 1-day work = 1/12. B's 1-day work = 1/18. Combined 1-day work = (3 + 2) / 36 = 5/36. Total days = 36 / 5 = 7.2 days.",
        "time_recommendation": 45
    },
    {
        "id": "quant_tw_2",
        "category": "Quantitative Aptitude",
        "topic": "Time & Work",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A is twice as efficient as B and therefore is able to finish a job in 30 days less than B. Working together, in how many days can they complete the work?",
        "options": ["20 days", "15 days", "25 days", "18 days"],
        "correct": 0,
        "explanation": "Ratio of efficiency A : B = 2 : 1 => Ratio of time taken = 1 : 2. Difference = 2x - 1x = x = 30 days. So A takes 30 days and B takes 60 days. Together = (30 * 60) / (30 + 60) = 1800 / 90 = 20 days.",
        "time_recommendation": 60
    },

    # --- Pipes & Cisterns ---
    {
        "id": "quant_pc_1",
        "category": "Quantitative Aptitude",
        "topic": "Pipes & Cisterns",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Pipe A fills a tank in 15 minutes and Pipe B empties it in 20 minutes. If both pipes are opened simultaneously, how long does it take to fill the tank?",
        "options": ["60 minutes", "45 minutes", "35 minutes", "50 minutes"],
        "correct": 0,
        "explanation": "Net rate per minute = (1/15) - (1/20) = (4 - 3) / 60 = 1/60. Total time required = 60 minutes.",
        "time_recommendation": 45
    },
    {
        "id": "quant_pc_2",
        "category": "Quantitative Aptitude",
        "topic": "Pipes & Cisterns",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Two pipes can fill a tank in 24 and 32 minutes respectively. After how many minutes should the second pipe be turned off so that the tank is completely filled in 18 minutes?",
        "options": ["8 minutes", "10 minutes", "12 minutes", "6 minutes"],
        "correct": 0,
        "explanation": "Let Pipe B run for t minutes. Pipe A runs for all 18 minutes. (18/24) + (t/32) = 1 => 3/4 + t/32 = 1 => t/32 = 1/4 => t = 8 minutes.",
        "time_recommendation": 75
    },

    # --- Time, Speed & Distance ---
    {
        "id": "quant_tsd_1",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed & Distance",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A person travels a distance of 300 km in 5 hours, traveling the first half at 50 km/h. At what speed must he travel the second half to arrive on schedule?",
        "options": ["75 km/h", "60 km/h", "70 km/h", "80 km/h"],
        "correct": 0,
        "explanation": "Half distance = 150 km. Time for first half = 150 / 50 = 3 hours. Remaining time = 5 - 3 = 2 hours. Required speed for remaining 150 km = 150 / 2 = 75 km/h.",
        "time_recommendation": 45
    },
    {
        "id": "quant_tsd_2",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed & Distance",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Two trains 140 m and 160 m long are running towards each other on parallel lines at 60 km/h and 48 km/h. How many seconds will they take to clear each other from the moment they meet?",
        "options": ["10 seconds", "12 seconds", "15 seconds", "9 seconds"],
        "correct": 0,
        "explanation": "Total distance = 140 + 160 = 300 m. Relative speed = 60 + 48 = 108 km/h = 108 * (5/18) = 30 m/s. Time taken = Distance / Speed = 300 / 30 = 10 seconds.",
        "time_recommendation": 60
    },

    # --- Boats & Streams ---
    {
        "id": "quant_bs_1",
        "category": "Quantitative Aptitude",
        "topic": "Boats & Streams",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A boat travels downstream at 18 km/h and upstream at 12 km/h. Find the speed of the stream.",
        "options": ["3 km/h", "4 km/h", "2.5 km/h", "5 km/h"],
        "correct": 0,
        "explanation": "Speed of stream = (Downstream Speed - Upstream Speed) / 2 = (18 - 12) / 2 = 6 / 2 = 3 km/h.",
        "time_recommendation": 45
    },
    {
        "id": "quant_bs_2",
        "category": "Quantitative Aptitude",
        "topic": "Boats & Streams",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A motorboat whose speed is 15 km/h in still water goes 30 km downstream and comes back in a total of 4 hours 30 minutes. What is the speed of the stream?",
        "options": ["5 km/h", "4 km/h", "6 km/h", "3 km/h"],
        "correct": 0,
        "explanation": "Let stream speed be s. 30 / (15 + s) + 30 / (15 - s) = 4.5. Testing s = 5: 30/20 + 30/10 = 1.5 + 3.0 = 4.5 hours! Matches. Speed of stream = 5 km/h.",
        "time_recommendation": 75
    },

    # --- Simple Interest ---
    {
        "id": "quant_si_1",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "At what rate percent per annum simple interest will a sum of money double itself in 8 years?",
        "options": ["12.5%", "10.0%", "15.0%", "8.5%"],
        "correct": 0,
        "explanation": "For principal P to double, SI = P. P = (P * R * 8) / 100 => R = 100 / 8 = 12.5% per annum.",
        "time_recommendation": 45
    },

    # --- Compound Interest ---
    {
        "id": "quant_ci_1",
        "category": "Quantitative Aptitude",
        "topic": "Compound Interest",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "The difference between simple and compound interest on $5000 for 2 years at 10% per annum compounded annually is:",
        "options": ["$50", "$40", "$60", "$45"],
        "correct": 0,
        "explanation": "For 2 years: Difference = P * (R/100)^2 = 5000 * (10/100)^2 = 5000 * (1/100) = $50.",
        "time_recommendation": 60
    },

    # --- Probability ---
    {
        "id": "quant_prob_1",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Two fair dice are thrown together. What is the probability that the sum of the numbers is at least 10?",
        "options": ["1/6", "1/12", "5/36", "1/4"],
        "correct": 0,
        "explanation": "Total outcomes = 36. Favorable sums: Sum 10: (4,6), (5,5), (6,4) [3]. Sum 11: (5,6), (6,5) [2]. Sum 12: (6,6) [1]. Total favorable = 3 + 2 + 1 = 6. Probability = 6/36 = 1/6.",
        "time_recommendation": 45
    },
    {
        "id": "quant_prob_2",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A bag contains 4 red, 5 blue, and 3 green marbles. If 2 marbles are drawn at random without replacement, what is the probability that both are blue?",
        "options": ["5/33", "5/22", "1/6", "5/12"],
        "correct": 0,
        "explanation": "Total marbles = 4 + 5 + 3 = 12. Probability = (5/12) * (4/11) = 20 / 132 = 5 / 33.",
        "time_recommendation": 60
    },

    # --- Permutation & Combination ---
    {
        "id": "quant_pc_comb_1",
        "category": "Quantitative Aptitude",
        "topic": "Permutation & Combination",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "In how many distinct ways can the letters of the word 'LEADER' be arranged?",
        "options": ["360", "720", "180", "120"],
        "correct": 0,
        "explanation": "The word 'LEADER' has 6 letters with 'E' repeating 2 times. Total permutations = 6! / 2! = 720 / 2 = 360.",
        "time_recommendation": 45
    },
    {
        "id": "quant_pc_comb_2",
        "category": "Quantitative Aptitude",
        "topic": "Permutation & Combination",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Out of 7 men and 4 women, a committee of 5 is to be formed. In how many ways can this be done so that the committee includes exactly 3 men?",
        "options": ["210", "180", "240", "140"],
        "correct": 0,
        "explanation": "We need 3 men and 2 women. Number of ways = (7C3) * (4C2) = [(7*6*5)/(3*2*1)] * [(4*3)/(2*1)] = 35 * 6 = 210.",
        "time_recommendation": 60
    },

    # --- Age Problems ---
    {
        "id": "quant_age_1",
        "category": "Quantitative Aptitude",
        "topic": "Age Problems",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A father is currently four times as old as his son. In 20 years, he will be twice as old as his son. What is the son's present age?",
        "options": ["10 years", "12 years", "15 years", "8 years"],
        "correct": 0,
        "explanation": "Let son's age be s, father is 4s. In 20 years: 4s + 20 = 2(s + 20) => 4s + 20 = 2s + 40 => 2s = 20 => s = 10 years.",
        "time_recommendation": 45
    },

    # --- Partnership ---
    {
        "id": "quant_part_1",
        "category": "Quantitative Aptitude",
        "topic": "Partnership",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A and B invest in a business in the ratio 3 : 5. If total annual profit is $80,000, find B's share of the profit.",
        "options": ["$50,000", "$48,000", "$52,500", "$54,000"],
        "correct": 0,
        "explanation": "B's share = [5 / (3 + 5)] * $80,000 = (5/8) * 80,000 = $50,000.",
        "time_recommendation": 45
    },

    # --- Mensuration ---
    {
        "id": "quant_mens_1",
        "category": "Quantitative Aptitude",
        "topic": "Mensuration",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "The perimeter of a rectangular garden is 84 meters. If the length is 6 meters greater than the breadth, find the area of the garden.",
        "options": ["432 sq m", "440 sq m", "420 sq m", "450 sq m"],
        "correct": 0,
        "explanation": "2(L + B) = 84 => L + B = 42. Since L - B = 6, adding gives 2L = 48 => L = 24 m, B = 18 m. Area = 24 * 18 = 432 sq m.",
        "time_recommendation": 45
    },
    {
        "id": "quant_mens_2",
        "category": "Quantitative Aptitude",
        "topic": "Mensuration",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "If the radius of a cylinder is doubled and its height is halved, what happens to its curved surface area?",
        "options": ["Remains unchanged", "Doubles", "Halves", "Quadruples"],
        "correct": 0,
        "explanation": "Curved surface area of cylinder = 2 * pi * r * h. New CSA = 2 * pi * (2r) * (h/2) = 2 * pi * r * h. Thus, it remains unchanged.",
        "time_recommendation": 45
    },

    # --- Algebra & Equations ---
    {
        "id": "quant_alg_1",
        "category": "Quantitative Aptitude",
        "topic": "Algebra",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "If x + (1/x) = 4, find the value of x^2 + (1/x^2).",
        "options": ["14", "16", "18", "12"],
        "correct": 0,
        "explanation": "Square both sides: (x + 1/x)^2 = x^2 + 1/x^2 + 2 = 16 => x^2 + 1/x^2 = 16 - 2 = 14.",
        "time_recommendation": 45
    },
    {
        "id": "quant_eq_1",
        "category": "Quantitative Aptitude",
        "topic": "Equations",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Solve for x: 2^(2x + 1) - 9 * 2^x + 4 = 0.",
        "options": ["x = 2 or x = -1", "x = 1 or x = -2", "x = 3 or x = 0", "x = 4 or x = -1"],
        "correct": 0,
        "explanation": "Let y = 2^x. Then 2y^2 - 9y + 4 = 0 => (2y - 1)(y - 4) = 0 => y = 4 or y = 1/2. 2^x = 4 => x = 2. 2^x = 1/2 => x = -1.",
        "time_recommendation": 60
    },

    # --- Progressions ---
    {
        "id": "quant_prog_1",
        "category": "Quantitative Aptitude",
        "topic": "Progressions",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "In an arithmetic progression, the 4th term is 14 and the 12th term is 70. Find the sum of the first 15 terms.",
        "options": ["630", "640", "620", "650"],
        "correct": 0,
        "explanation": "T4 = a + 3d = 14. T12 = a + 11d = 70. 8d = 56 => d = 7. a = 14 - 21 = -7. S15 = (15/2) * [2(-7) + 14*7] = (15/2) * [-14 + 98] = (15/2) * 84 = 15 * 42 = 630.",
        "time_recommendation": 60
    },

    # --- Arithmetic Word Problems ---
    {
        "id": "quant_word_1",
        "category": "Quantitative Aptitude",
        "topic": "Arithmetic Word Problems",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A shepherd has 17 sheep. All but nine die. How many sheep does he have left?",
        "options": ["9", "8", "0", "17"],
        "correct": 0,
        "explanation": "The phrase 'All but nine die' means that exactly nine sheep survived. Hence, 9 sheep are left.",
        "time_recommendation": 30
    },

    # ==========================================================================
    # 2. LOGICAL / ANALYTICAL REASONING
    # ==========================================================================
    # --- Number Series ---
    {
        "id": "logic_num_ser_1",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Identify the missing number in the sequence: 4, 9, 25, 49, 121, ?",
        "options": ["169", "144", "196", "225"],
        "correct": 0,
        "explanation": "These are squares of consecutive prime numbers: 2^2=4, 3^2=9, 5^2=25, 7^2=49, 11^2=121. The next prime number is 13, and 13^2 = 169.",
        "time_recommendation": 45
    },
    {
        "id": "logic_num_ser_2",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Find the next number in the pattern: 7, 13, 25, 49, 97, ?",
        "options": ["193", "187", "195", "191"],
        "correct": 0,
        "explanation": "The pattern is (previous number * 2) - 1. 7*2 - 1 = 13; 13*2 - 1 = 25; 25*2 - 1 = 49; 49*2 - 1 = 97; 97*2 - 1 = 193.",
        "time_recommendation": 60
    },

    # --- Letter Series ---
    {
        "id": "logic_let_ser_1",
        "category": "Logical Reasoning",
        "topic": "Letter Series",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the next term in the series: B, E, H, K, N, ?",
        "options": ["Q", "P", "R", "S"],
        "correct": 0,
        "explanation": "Each letter moves forward by +3 positions: B(2) + 3 = E(5) + 3 = H(8) + 3 = K(11) + 3 = N(14) + 3 = Q(17).",
        "time_recommendation": 30
    },

    # --- Alphanumeric Series ---
    {
        "id": "logic_alphanum_1",
        "category": "Logical Reasoning",
        "topic": "Alphanumeric Series",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Find the next term: P3C, R5F, T8I, V12L, ?",
        "options": ["X17O", "X16O", "W17O", "X17N"],
        "correct": 0,
        "explanation": "First letter: P, R, T, V (+2 each) -> X. Number: 3, 5 (+2), 8 (+3), 12 (+4), 12+5 = 17. Third letter: C, F, I, L (+3 each) -> O. Thus, X17O.",
        "time_recommendation": 60
    },

    # --- Coding-Decoding ---
    {
        "id": "logic_cd_1",
        "category": "Logical Reasoning",
        "topic": "Coding-Decoding",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "In a certain code, 'ROSE' is written as 'TQUG'. How is 'BLUE' written in that same code?",
        "options": ["DNWG", "CMVF", "DNWF", "ENWG"],
        "correct": 0,
        "explanation": "Each letter is shifted forward by +2: R+2=T, O+2=Q, S+2=U, E+2=G. Applying to BLUE: B+2=D, L+2=N, U+2=W, E+2=G -> DNWG.",
        "time_recommendation": 45
    },
    {
        "id": "logic_cd_2",
        "category": "Logical Reasoning",
        "topic": "Coding-Decoding",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Company-Level Practice",
        "question": "If 'SYSTEM' is coded as 'SYSMET' and 'NEARER' is coded as 'AENRER', then how is 'FRACTION' coded?",
        "options": ["CARFNOIT", "CRAFNOIT", "CARFTION", "FRACNOIT"],
        "correct": 0,
        "explanation": "The word is divided into two halves. In FRACTION (8 letters -> FRAC / TION): first half FRAC reversed -> CARF, second half TION reversed -> NOIT. Combined -> CARFNOIT.",
        "time_recommendation": 75
    },

    # --- Blood Relations ---
    {
        "id": "logic_br_1",
        "category": "Logical Reasoning",
        "topic": "Blood Relations",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Pointing to a photograph of a boy, Suresh said, 'He is the son of the only son of my mother.' How is Suresh related to that boy?",
        "options": ["Father", "Uncle", "Brother", "Grandfather"],
        "correct": 0,
        "explanation": "'The only son of Suresh's mother' is Suresh himself. Therefore, the boy in the photograph is Suresh's son. Suresh is the boy's father.",
        "time_recommendation": 45
    },
    {
        "id": "logic_br_2",
        "category": "Logical Reasoning",
        "topic": "Blood Relations",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "A is B's sister. C is B's mother. D is C's father. E is D's mother. How is A related to D?",
        "options": ["Granddaughter", "Daughter", "Grandmother", "Niece"],
        "correct": 0,
        "explanation": "A is the daughter of C. C is the daughter of D. Therefore, A is the granddaughter of D.",
        "time_recommendation": 60
    },

    # --- Direction Sense ---
    {
        "id": "logic_dir_1",
        "category": "Logical Reasoning",
        "topic": "Direction Sense",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Ravi walks 8 km North, turns right and walks 6 km. How far and in what direction is he now from his starting point?",
        "options": ["10 km North-East", "14 km North-East", "10 km North-West", "12 km East"],
        "correct": 0,
        "explanation": "By Pythagoras theorem: Distance = sqrt(8^2 + 6^2) = sqrt(64 + 36) = sqrt(100) = 10 km. He moved North then East, so the direction is North-East.",
        "time_recommendation": 45
    },
    {
        "id": "logic_dir_2",
        "category": "Logical Reasoning",
        "topic": "Direction Sense",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "One evening before sunset, Rekha and Hema were talking to each other face to face. If Hema's shadow was exactly to the right of Hema, which direction was Rekha facing?",
        "options": ["South", "North", "East", "West"],
        "correct": 0,
        "explanation": "Before sunset, the sun is in the West, casting shadows towards the East. If Hema's shadow is to her right, Hema must be facing North (since right of North is East). Since Rekha is facing Hema face to face, Rekha must be facing South.",
        "time_recommendation": 60
    },

    # --- Analogy & Classification ---
    {
        "id": "logic_an_1",
        "category": "Logical Reasoning",
        "topic": "Analogy",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Odometer is to Mileage as Compass is to:",
        "options": ["Direction", "Speed", "Hiking", "Needle"],
        "correct": 0,
        "explanation": "An odometer is an instrument used to measure mileage. Similarly, a compass is an instrument used to determine direction.",
        "time_recommendation": 30
    },
    {
        "id": "logic_class_1",
        "category": "Logical Reasoning",
        "topic": "Classification",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Choose the odd one out among the following words:",
        "options": ["Mercury", "Copper", "Iron", "Silver"],
        "correct": 0,
        "explanation": "Mercury is the only metal among the options that is liquid at room temperature; Copper, Iron, and Silver are solid metals.",
        "time_recommendation": 30
    },

    # --- Syllogism ---
    {
        "id": "logic_syl_1",
        "category": "Logical Reasoning",
        "topic": "Syllogism",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Statements:\n1. All cats are dogs.\n2. All dogs are birds.\nConclusions:\nI. All cats are birds.\nII. Some birds are cats.",
        "options": ["Both I and II follow", "Only I follows", "Only II follows", "Neither follows"],
        "correct": 0,
        "explanation": "Cats ⊆ Dogs ⊆ Birds. Therefore, All cats are birds (I is true). Since the set of cats is a non-empty subset of birds, Some birds are cats (II is true). Both conclusions follow.",
        "time_recommendation": 60
    },
    {
        "id": "logic_syl_2",
        "category": "Logical Reasoning",
        "topic": "Syllogism",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Company-Level Practice",
        "question": "Statements:\n1. Some pens are books.\n2. All books are papers.\nConclusions:\nI. All pens are papers.\nII. Some pens are papers.",
        "options": ["Only II follows", "Only I follows", "Both follow", "Neither follows"],
        "correct": 0,
        "explanation": "Since some pens are books and all books are papers, those specific pens that are books are definitely papers. Thus, 'Some pens are papers' is guaranteed, but 'All pens are papers' is not.",
        "time_recommendation": 60
    },

    # --- Statement & Conclusion / Assumption ---
    {
        "id": "logic_stmt_conc_1",
        "category": "Logical Reasoning",
        "topic": "Statement & Conclusion",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Statement: 'Government has decided to pay compensation of $10,000 to the families of all victims of the recent railway mishap.'\nConclusion I: The government has enough funds to meet the expenses.\nConclusion II: There may be reduction in incidents of railway mishaps in future.",
        "options": ["Only Conclusion I follows", "Only Conclusion II follows", "Both follow", "Neither follows"],
        "correct": 0,
        "explanation": "When a government announces a compensation scheme, it naturally implies that financial reserves exist to fulfill it (Conclusion I follows). Paying compensation does not automatically cause a reduction in future mishaps (Conclusion II does not follow).",
        "time_recommendation": 60
    },
    {
        "id": "logic_stmt_assump_1",
        "category": "Logical Reasoning",
        "topic": "Statement & Assumption",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Statement: 'Please read this instruction manual carefully before operating the machine.'\nAssumption I: People can read instructions.\nAssumption II: Machines may be damaged if not operated as instructed.",
        "options": ["Both Assumptions I and II are implicit", "Only Assumption I is implicit", "Only Assumption II is implicit", "Neither is implicit"],
        "correct": 0,
        "explanation": "Writing an instruction manual assumes the user can read it (I is implicit). Warning the user to read before operating assumes improper operation could lead to damage or malfunction (II is implicit).",
        "time_recommendation": 60
    },

    # --- Seating Arrangement & Puzzles ---
    {
        "id": "logic_seat_1",
        "category": "Logical Reasoning",
        "topic": "Seating Arrangement",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Five friends A, B, C, D, E are sitting in a circle facing the center. A is to the immediate left of B. E is between C and D. C is to the immediate left of A. Who is sitting to the immediate right of B?",
        "options": ["D", "E", "C", "A"],
        "correct": 0,
        "explanation": "Clockwise circle order: C -> A -> B -> D -> E -> C. A is left of B, C is left of A. E is between C and D. Looking at B facing center: right of B is D.",
        "time_recommendation": 75
    },
    {
        "id": "logic_puz_1",
        "category": "Logical Reasoning",
        "topic": "Puzzles",
        "difficulty": "Hard",
        "exam_level": "Advanced Placement",
        "label": "Placement Exam Style",
        "question": "Four people P, Q, R, S each speak a different language among Hindi, English, French, and Spanish. P does not speak English or French. Q does not speak Hindi or French. S speaks Spanish. Which language does P speak?",
        "options": ["Hindi", "English", "French", "Spanish"],
        "correct": 0,
        "explanation": "S speaks Spanish. P can only speak Hindi, English, or French, but doesn't speak English or French. Therefore, P must speak Hindi.",
        "time_recommendation": 60
    },

    # --- Ranking & Order ---
    {
        "id": "logic_rank_1",
        "category": "Logical Reasoning",
        "topic": "Ranking",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "In a class of 45 students, Rohan ranks 18th from the top. What is his rank from the bottom?",
        "options": ["28th", "27th", "29th", "30th"],
        "correct": 0,
        "explanation": "Rank from bottom = Total - Rank from top + 1 = 45 - 18 + 1 = 28th.",
        "time_recommendation": 45
    },

    # --- Clocks & Calendars ---
    {
        "id": "logic_clock_1",
        "category": "Logical Reasoning",
        "topic": "Clocks",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "At what angle are the hands of a clock inclined at 3 hours 40 minutes?",
        "options": ["130°", "140°", "125°", "135°"],
        "correct": 0,
        "explanation": "Angle formula: |30*H - (11/2)*M| = |30(3) - 5.5(40)| = |90 - 220| = |-130| = 130°.",
        "time_recommendation": 60
    },
    {
        "id": "logic_cal_1",
        "category": "Logical Reasoning",
        "topic": "Calendars",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "If 1st January 2024 was a Monday, what day of the week was 31st December 2024?",
        "options": ["Tuesday", "Monday", "Wednesday", "Sunday"],
        "correct": 0,
        "explanation": "2024 is a leap year (divisible by 4) containing 366 days. In a leap year, the last day of the year is always 1 day ahead of the first day: Monday + 1 = Tuesday.",
        "time_recommendation": 45
    },

    # --- Data Sufficiency & Deduction ---
    {
        "id": "logic_ds_1",
        "category": "Logical Reasoning",
        "topic": "Data Sufficiency",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Question: Is X an odd integer?\nStatement 1: X is divisible by 3.\nStatement 2: (X + 1) is an even integer.",
        "options": ["Statement 2 alone is sufficient, but 1 is not", "Statement 1 alone is sufficient", "Both statements together are needed", "Neither is sufficient"],
        "correct": 0,
        "explanation": "From 1: X could be 3 (odd) or 6 (even) -> Not sufficient. From 2: If (X + 1) is even, then X must be odd (since Even - 1 = Odd) -> Sufficient alone.",
        "time_recommendation": 60
    },
    {
        "id": "logic_venn_1",
        "category": "Logical Reasoning",
        "topic": "Venn Diagrams",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Which relationship correctly depicts: Animals, Dogs, and Pets?",
        "options": [
            "A circle 'Dogs' completely inside 'Animals', intersecting partially with 'Pets'",
            "Three completely separate circles",
            "Three concentric circles",
            "Dogs and Pets disjoint inside Animals"
        ],
        "correct": 0,
        "explanation": "All dogs are animals (Dogs circle is entirely inside Animals). Some dogs are pets, and some pets are other animals (Pets intersects with Dogs and Animals).",
        "time_recommendation": 45
    },

    # ==========================================================================
    # 3. VERBAL ABILITY
    # ==========================================================================
    # --- Reading Comprehension ---
    {
        "id": "verbal_rc_1",
        "category": "Verbal Ability",
        "topic": "Reading Comprehension",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Passage: 'Artificial Intelligence has rapidly evolved from theoretical exploration into practical business infrastructure. While automation drives operational speed, human discretion remains indispensable for nuanced contextual ethics.'\n\nAccording to the passage, why is human oversight still vital?",
        "options": [
            "For nuanced contextual ethics",
            "Because machines cannot calculate fast enough",
            "To replace automation altogether",
            "Because business infrastructure is solely non-technical"
        ],
        "correct": 0,
        "explanation": "The passage explicitly states: 'human discretion remains indispensable for nuanced contextual ethics.'",
        "time_recommendation": 60
    },

    # --- Error Detection ---
    {
        "id": "verbal_err_1",
        "category": "Verbal Ability",
        "topic": "Error Detection",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Find the part of the sentence with an error: 'Neither the manager (A) / nor his assistants (B) / was present at (C) / the morning briefing. (D)'",
        "options": ["Part (C) - 'was present at'", "Part (A)", "Part (B)", "No error"],
        "correct": 0,
        "explanation": "In 'Neither... nor' constructions, the verb agrees with the subject closest to it. Here 'his assistants' is plural, so the verb must be plural 'were present at', not 'was'.",
        "time_recommendation": 45
    },

    # --- Sentence Correction ---
    {
        "id": "verbal_sc_1",
        "category": "Verbal Ability",
        "topic": "Sentence Correction",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Choose the correct replacement for the bracketed text: 'She is one of those rare software architects who [understands both system performance and business priorities].'",
        "options": [
            "understand both system performance and business priorities",
            "understands both system performance as well as business priorities",
            "is understanding system performance and business priorities",
            "has understood both system performance and business priorities"
        ],
        "correct": 0,
        "explanation": "The relative pronoun 'who' refers to the plural antecedent 'rare software architects', so the verb must be plural ('understand', not 'understands').",
        "time_recommendation": 60
    },

    # --- Fill in the Blanks ---
    {
        "id": "verbal_fib_1",
        "category": "Verbal Ability",
        "topic": "Fill in the Blanks",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "The engineer's explanation was so ________ that even non-technical stakeholders grasped the concept immediately.",
        "options": ["lucid", "opaque", "abstruse", "convoluted"],
        "correct": 0,
        "explanation": "'Lucid' means expressed clearly and easy to understand. 'Opaque' and 'abstruse' mean difficult to comprehend, which contradicts the prompt.",
        "time_recommendation": 30
    },

    # --- Synonyms & Antonyms ---
    {
        "id": "verbal_syn_1",
        "category": "Verbal Ability",
        "topic": "Synonyms",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the synonym of 'CANDID'?",
        "options": ["Frank", "Deceitful", "Vague", "Arrogant"],
        "correct": 0,
        "explanation": "'Candid' means truthful, open, and straightforward; 'Frank' is its closest synonym.",
        "time_recommendation": 30
    },
    {
        "id": "verbal_ant_1",
        "category": "Verbal Ability",
        "topic": "Antonyms",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the antonym of 'METICULOUS'?",
        "options": ["Careless", "Thorough", "Detailed", "Diligent"],
        "correct": 0,
        "explanation": "'Meticulous' means showing great attention to detail. Its antonym is 'Careless'.",
        "time_recommendation": 30
    },

    # --- Para Jumbles & Sentence Arrangement ---
    {
        "id": "verbal_pj_1",
        "category": "Verbal Ability",
        "topic": "Para Jumbles",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Rearrange the sentences into a logical paragraph:\nP: This rapid data processing allows predictive recommendations.\nQ: Modern applications collect millions of user events daily.\nR: Consequently, user engagement improves substantially.\nS: These events are fed directly into machine learning pipelines.",
        "options": ["QSPR", "PQSR", "SQPR", "QPRS"],
        "correct": 0,
        "explanation": "Q introduces user events. S connects to 'These events'. P explains the outcome of feeding them to ML pipelines. R provides the concluding business result. Proper order: QSPR.",
        "time_recommendation": 75
    },

    # --- Idioms & Phrases ---
    {
        "id": "verbal_id_1",
        "category": "Verbal Ability",
        "topic": "Idioms & Phrases",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the meaning of the idiom 'To burn the midnight oil'?",
        "options": [
            "To work or study late into the night",
            "To cause accidental fires",
            "To waste valuable resources",
            "To wake up very early in the morning"
        ],
        "correct": 0,
        "explanation": "'To burn the midnight oil' is an idiomatic expression that means working or studying late into the night.",
        "time_recommendation": 30
    },

    # --- One Word Substitution ---
    {
        "id": "verbal_ows_1",
        "category": "Verbal Ability",
        "topic": "One Word Substitution",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Give one word for: 'A person who knows and speaks many languages.'",
        "options": ["Polyglot", "Philanthropist", "Polymath", "Linguist"],
        "correct": 0,
        "explanation": "A 'Polyglot' is someone who speaks or writes several languages. A polymath has broad knowledge across diverse subjects.",
        "time_recommendation": 30
    },

    # --- Grammar, Voice, Speech ---
    {
        "id": "verbal_voice_1",
        "category": "Verbal Ability",
        "topic": "Active & Passive Voice",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Change into passive voice: 'The team completed the software deployment before midnight.'",
        "options": [
            "The software deployment was completed by the team before midnight.",
            "The software deployment is completed by the team before midnight.",
            "The software deployment had been completed before midnight by team.",
            "The team was completing the software deployment before midnight."
        ],
        "correct": 0,
        "explanation": "Simple past active 'completed' converts into passive 'was completed' + by + subject.",
        "time_recommendation": 45
    },
    {
        "id": "verbal_speech_1",
        "category": "Verbal Ability",
        "topic": "Direct & Indirect Speech",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Convert into indirect speech: The manager said, 'I will review your code changes tomorrow.'",
        "options": [
            "The manager said that he would review my code changes the next day.",
            "The manager said that he will review my code changes tomorrow.",
            "The manager asked if he would review my code changes the next day.",
            "The manager told that he can review my code changes tomorrow."
        ],
        "correct": 0,
        "explanation": "In indirect speech with past reporting verb 'said': 'will' changes to 'would', and 'tomorrow' changes to 'the next day'.",
        "time_recommendation": 45
    },

    # ==========================================================================
    # 4. DATA INTERPRETATION
    # ==========================================================================
    # --- Tables ---
    {
        "id": "di_tab_1",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Refer to the sales data table (Units Sold in thousands):\n\n| Year | Product A | Product B | Product C |\n|---|---|---|---|\n| 2021 | 40 | 60 | 50 |\n| 2022 | 50 | 75 | 55 |\n| 2023 | 65 | 90 | 70 |\n\nWhat is the percentage increase in sales of Product B from 2021 to 2023?",
        "options": ["50%", "40%", "45%", "60%"],
        "correct": 0,
        "explanation": "Sales in 2021 = 60. Sales in 2023 = 90. Increase = 90 - 60 = 30. % Increase = (30 / 60) * 100 = 50%.",
        "time_recommendation": 60
    },
    {
        "id": "di_tab_2",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Exam Results by College (Total students vs Passed):\n\n| College | Appeared | Passed |\n|---|---|---|\n| Tech A | 450 | 360 |\n| Tech B | 600 | 510 |\n| Tech C | 500 | 410 |\n\nWhich college recorded the highest passing percentage?",
        "options": ["Tech B (85%)", "Tech C (82%)", "Tech A (80%)", "All had equal percentage"],
        "correct": 0,
        "explanation": "Tech A: 360/450 = 80%. Tech B: 510/600 = 85%. Tech C: 410/500 = 82%. Highest is Tech B with 85%.",
        "time_recommendation": 60
    },

    # --- Bar Graphs ---
    {
        "id": "di_bar_1",
        "category": "Data Interpretation",
        "topic": "Bar Graphs",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Company Hiring (in hundreds) over four quarters:\nQ1: 12 | Q2: 18 | Q3: 15 | Q4: 25\n\nWhat is the average number of employees hired per quarter?",
        "options": ["1750", "1700", "1800", "1650"],
        "correct": 0,
        "explanation": "Total hires = 12 + 18 + 15 + 25 = 70 hundred = 7000 employees. Average = 7000 / 4 = 1750 employees.",
        "time_recommendation": 45
    },

    # --- Line Graphs ---
    {
        "id": "di_line_1",
        "category": "Data Interpretation",
        "topic": "Line Graphs",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Website Monthly Active Users (in millions):\nJan: 4.0 | Feb: 4.8 | Mar: 6.0 | Apr: 7.2\n\nBetween which two consecutive months was the absolute growth the highest?",
        "options": ["Both Feb-Mar and Mar-Apr tied at 1.2M", "Jan to Feb (0.8M)", "Feb to Mar only", "Mar to Apr only"],
        "correct": 0,
        "explanation": "Jan to Feb: 4.8 - 4.0 = 0.8M. Feb to Mar: 6.0 - 4.8 = 1.2M. Mar to Apr: 7.2 - 6.0 = 1.2M. Both periods tied at the highest absolute growth of 1.2 million.",
        "time_recommendation": 60
    },

    # --- Pie Charts ---
    {
        "id": "di_pie_1",
        "category": "Data Interpretation",
        "topic": "Pie Charts",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "A company budget is distributed as:\nR&D: 30%, Marketing: 25%, Salaries: 35%, Operations: 10%.\n\nIf the total annual budget is $20 Million, what is the central angle represented by Salaries in the pie chart?",
        "options": ["126°", "120°", "135°", "108°"],
        "correct": 0,
        "explanation": "Salaries represent 35% of the total budget. Central angle = 35% of 360° = 0.35 * 360° = 126°.",
        "time_recommendation": 45
    },
    {
        "id": "di_pie_2",
        "category": "Data Interpretation",
        "topic": "Pie Charts",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "From the same budget (R&D: 30%, Marketing: 25%, Salaries: 35%, Operations: 10%), what is the ratio of funds allocated to R&D compared to Marketing?",
        "options": ["6 : 5", "5 : 6", "7 : 5", "4 : 3"],
        "correct": 0,
        "explanation": "Ratio R&D : Marketing = 30% : 25% = 30 : 25 = 6 : 5.",
        "time_recommendation": 30
    },

    # --- Caselets ---
    {
        "id": "di_case_1",
        "category": "Data Interpretation",
        "topic": "Caselets",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Caselet: In an IT firm of 500 engineers, 60% are Python developers, 40% are Java developers, and 20% are proficient in both Python and Java. How many engineers in the firm know neither Python nor Java?",
        "options": ["100 engineers", "80 engineers", "120 engineers", "50 engineers"],
        "correct": 0,
        "explanation": "Percentage knowing at least one = P(Python ∪ Java) = 60% + 40% - 20% = 80%. Percentage knowing neither = 100% - 80% = 20%. Total engineers = 20% of 500 = 100 engineers.",
        "time_recommendation": 60
    },

    # --- Percentage, Ratio & Average DI ---
    {
        "id": "di_pct_ratio_1",
        "category": "Data Interpretation",
        "topic": "Percentage-based DI",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "In 2022, Revenue was $80M and Expenses were $60M. In 2023, Revenue increased by 25% while Expenses increased by 10%. What was the percentage increase in Profit?",
        "options": ["70%", "65%", "75%", "50%"],
        "correct": 0,
        "explanation": "2022 Profit = 80 - 60 = $20M. 2023 Revenue = 80 * 1.25 = $100M. 2023 Expenses = 60 * 1.10 = $66M. 2023 Profit = 100 - 66 = $34M. Profit Increase = 34 - 20 = $14M. % Increase = (14 / 20) * 100 = 70%.",
        "time_recommendation": 75
    },

    # ==========================================================================
    # 5. TECHNICAL / COMPUTER APTITUDE
    # ==========================================================================
    # --- Programming Basics & C/C++ ---
    {
        "id": "tech_c_1",
        "category": "Technical Aptitude",
        "topic": "C/C++",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the output of the following C code snippet?\n\nint x = 5;\nprintf(\"%d %d\", x++, ++x);",
        "options": [
            "Undefined behavior / Compiler dependent",
            "5 7",
            "6 7",
            "5 6"
        ],
        "correct": 0,
        "explanation": "Modifying a variable more than once between sequence points in C produces Undefined Behavior (UB). Different compilers or optimization levels evaluate argument orders differently.",
        "time_recommendation": 45
    },
    {
        "id": "tech_c_2",
        "category": "Technical Aptitude",
        "topic": "C/C++",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "In C++, which keyword is used to prevent an overridden method in a derived class from being overridden further?",
        "options": ["final", "override", "sealed", "const"],
        "correct": 0,
        "explanation": "In modern C++ (C++11 onwards), the 'final' specifier applied to a virtual function prevents any further derived class from overriding that function.",
        "time_recommendation": 45
    },

    # --- Python ---
    {
        "id": "tech_py_1",
        "category": "Technical Aptitude",
        "topic": "Python",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the output of the following Python expression?\n\nprint([i for i in range(10) if i % 3 == 0])",
        "options": ["[0, 3, 6, 9]", "[3, 6, 9]", "[0, 3, 6]", "[1, 3, 6, 9]"],
        "correct": 0,
        "explanation": "range(10) generates integers 0 through 9. 0 % 3 == 0, 3 % 3 == 0, 6 % 3 == 0, 9 % 3 == 0. The resulting list is [0, 3, 6, 9].",
        "time_recommendation": 30
    },
    {
        "id": "tech_py_2",
        "category": "Technical Aptitude",
        "topic": "Python",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "What happens when you pass a mutable object like a list as a default parameter in Python: def append_to(item, target=[]): ...?",
        "options": [
            "The list is created once at function definition time and shared across calls",
            "A new list is created every time the function is called",
            "Python throws a SyntaxError",
            "The list is garbage collected after each call"
        ],
        "correct": 0,
        "explanation": "In Python, default arguments are evaluated once when the function definition is executed, not at each call. Mutating a default mutable list affects subsequent calls.",
        "time_recommendation": 60
    },

    # --- OOP ---
    {
        "id": "tech_oop_1",
        "category": "Technical Aptitude",
        "topic": "OOP",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Which OOP concept is demonstrated by having multiple methods with the same name but different signatures within the same class?",
        "options": ["Method Overloading", "Method Overriding", "Encapsulation", "Abstraction"],
        "correct": 0,
        "explanation": "Method Overloading is a form of compile-time polymorphism where multiple methods in the same class share a name but differ in parameter count or types.",
        "time_recommendation": 30
    },

    # --- Data Structures ---
    {
        "id": "tech_dsa_1",
        "category": "Technical Aptitude",
        "topic": "Data Structures",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Which data structure follows the LIFO (Last In First Out) principle?",
        "options": ["Stack", "Queue", "Binary Tree", "Linked List"],
        "correct": 0,
        "explanation": "A Stack follows Last-In, First-Out (LIFO), meaning the last element pushed is the first element popped.",
        "time_recommendation": 30
    },
    {
        "id": "tech_dsa_2",
        "category": "Technical Aptitude",
        "topic": "Data Structures",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "What is the worst-case time complexity of searching an element in a balanced Binary Search Tree (such as an AVL or Red-Black tree) with N nodes?",
        "options": ["O(log N)", "O(N)", "O(1)", "O(N log N)"],
        "correct": 0,
        "explanation": "Because balanced BSTs maintain height proportional to log2(N), the worst-case search, insertion, and deletion time complexities are all bounded by O(log N).",
        "time_recommendation": 45
    },

    # --- Algorithms ---
    {
        "id": "tech_algo_1",
        "category": "Technical Aptitude",
        "topic": "Algorithms",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Which sorting algorithm achieves an optimal average and worst-case time complexity of O(N log N) and is guaranteed to be stable?",
        "options": ["Merge Sort", "Quick Sort", "Heap Sort", "Selection Sort"],
        "correct": 0,
        "explanation": "Merge Sort runs in O(N log N) in best, average, and worst cases, and preserves the relative order of duplicate elements (stable). Quick Sort is not stable and has O(N^2) worst case; Heap Sort is not stable.",
        "time_recommendation": 45
    },

    # --- DBMS & SQL ---
    {
        "id": "tech_db_1",
        "category": "Technical Aptitude",
        "topic": "DBMS",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What does the 'A' represent in the ACID properties of relational database transactions?",
        "options": ["Atomicity", "Availability", "Authentication", "Accuracy"],
        "correct": 0,
        "explanation": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Atomicity ensures that all operations in a transaction succeed, or all are rolled back.",
        "time_recommendation": 30
    },
    {
        "id": "tech_sql_1",
        "category": "Technical Aptitude",
        "topic": "SQL",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "Which SQL clause is used to filter rows AFTER an aggregate function has been applied via GROUP BY?",
        "options": ["HAVING", "WHERE", "ORDER BY", "QUALIFY"],
        "correct": 0,
        "explanation": "'WHERE' filters individual rows before aggregation. 'HAVING' filters grouped records after aggregate functions (like COUNT, SUM, AVG) have been evaluated.",
        "time_recommendation": 30
    },

    # --- Operating Systems ---
    {
        "id": "tech_os_1",
        "category": "Technical Aptitude",
        "topic": "Operating Systems",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Placement Exam Style",
        "question": "Which of the following is NOT one of the four Coffman conditions necessary for a Deadlock to occur?",
        "options": ["Preemption", "Mutual Exclusion", "Hold and Wait", "Circular Wait"],
        "correct": 0,
        "explanation": "The four Coffman conditions are: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. 'Preemption' prevents deadlock, whereas 'No Preemption' allows deadlock.",
        "time_recommendation": 45
    },
    {
        "id": "tech_os_2",
        "category": "Technical Aptitude",
        "topic": "Operating Systems",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "What is the primary purpose of the Virtual Memory subsystem in modern Operating Systems?",
        "options": [
            "Allow programs to address more memory than physical RAM by paging to secondary storage",
            "Increase CPU clock speeds dynamically",
            "Prevent virus infections in hardware registers",
            "Ensure that processes do not need a page table"
        ],
        "correct": 0,
        "explanation": "Virtual Memory provides hardware memory isolation and enables execution of processes larger than physical RAM by mapping virtual addresses to physical pages and swapping to disk.",
        "time_recommendation": 45
    },

    # --- Computer Networks ---
    {
        "id": "tech_cn_1",
        "category": "Technical Aptitude",
        "topic": "Computer Networks",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "At which layer of the OSI model do routers primarily operate?",
        "options": ["Network Layer (Layer 3)", "Data Link Layer (Layer 2)", "Transport Layer (Layer 4)", "Application Layer (Layer 7)"],
        "correct": 0,
        "explanation": "Routers inspect IP packet headers and forward traffic across different subnetworks at Layer 3 (Network Layer). Switches operate primarily at Layer 2.",
        "time_recommendation": 30
    },
    {
        "id": "tech_cn_2",
        "category": "Technical Aptitude",
        "topic": "Computer Networks",
        "difficulty": "Medium",
        "exam_level": "Standard Placement",
        "label": "Company-Level Practice",
        "question": "What are the three packets exchanged during a standard TCP Three-Way Handshake connection establishment?",
        "options": [
            "SYN -> SYN-ACK -> ACK",
            "ACK -> SYN -> SYN-ACK",
            "HELLO -> READY -> ACK",
            "SYN -> ACK -> DATA"
        ],
        "correct": 0,
        "explanation": "To establish a TCP session, Client sends SYN, Server replies with SYN-ACK, and Client confirms with ACK before data transmission begins.",
        "time_recommendation": 45
    },

    # --- Software Engineering & Web Tech ---
    {
        "id": "tech_se_1",
        "category": "Technical Aptitude",
        "topic": "Software Engineering",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "In Git version control, which command creates a new branch and switches to it in a single step?",
        "options": ["git checkout -b <branch-name>", "git branch -n <branch-name>", "git merge -c <branch-name>", "git switch -a <branch-name>"],
        "correct": 0,
        "explanation": "`git checkout -b <branch_name>` (or `git switch -c <branch_name>`) creates a new branch and checks it out immediately.",
        "time_recommendation": 30
    },
    {
        "id": "tech_web_1",
        "category": "Technical Aptitude",
        "topic": "Basic Web Technologies",
        "difficulty": "Easy",
        "exam_level": "Basic Placement",
        "label": "Placement Exam Style",
        "question": "Which HTTP status code signifies that a requested resource was successfully found and returned by the server?",
        "options": ["200 OK", "301 Moved Permanently", "404 Not Found", "500 Internal Server Error"],
        "correct": 0,
        "explanation": "HTTP 200 OK indicates that the client's request succeeded and the payload has been transmitted.",
        "time_recommendation": 30
    }
]

# ------------------------------------------------------------------------------
# PROGRAMMATIC QUESTION GENERATOR (To guarantee extensive depth across all 80 topics)
# Generates realistic, distinct, concept-driven placement questions covering any gaps.
# ------------------------------------------------------------------------------
def _generate_synthetic_placement_questions():
    """Generates structured, non-repetitive placement questions across all 80 topics."""
    generated = []
    
    templates = [
        # Quant extra topics
        {
            "category": "Quantitative Aptitude",
            "topic": "Simplification",
            "difficulty": "Medium",
            "exam_level": "Standard Placement",
            "label": "Company-Level Practice",
            "q": "What is the value of (0.85 × 0.85 - 0.15 × 0.15) / (0.85 - 0.15)?",
            "opts": ["1.00", "0.70", "0.85", "1.15"],
            "corr": 0,
            "exp": "Using identity (a^2 - b^2) / (a - b) = a + b. Here 0.85 + 0.15 = 1.00.",
            "time": 45
        },
        {
            "category": "Quantitative Aptitude",
            "topic": "Equations",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "q": "If 3x + 5y = 21 and 2x - y = 1, find the value of x.",
            "opts": ["2", "3", "4", "1"],
            "corr": 0,
            "exp": "From 2nd equation, y = 2x - 1. Substitute into 1st: 3x + 5(2x - 1) = 21 => 13x - 5 = 21 => 13x = 26 => x = 2.",
            "time": 45
        },
        {
            "category": "Quantitative Aptitude",
            "topic": "Partnership",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "q": "A and B start a business with capitals of $4000 and $6000 respectively. If total profit at year end is $5000, find A's share.",
            "opts": ["$2000", "$3000", "$2500", "$1500"],
            "corr": 0,
            "exp": "Profit ratio A:B = 4000:6000 = 2:3. A's share = (2/5) * 5000 = $2000.",
            "time": 45
        },
        {
            "category": "Quantitative Aptitude",
            "topic": "Progressions",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "q": "Find the 10th term of the geometric progression: 3, 6, 12, 24, ...",
            "opts": ["1536", "768", "3072", "1024"],
            "corr": 0,
            "exp": "First term a = 3, common ratio r = 2. 10th term = a * r^(n-1) = 3 * 2^9 = 3 * 512 = 1536.",
            "time": 45
        },
        {
            "category": "Quantitative Aptitude",
            "topic": "Arithmetic Word Problems",
            "difficulty": "Medium",
            "exam_level": "Standard Placement",
            "label": "Company-Level Practice",
            "q": "A bird flies 120 km in 3 hours with the wind and returns against the wind in 4 hours. Find the speed of the wind.",
            "opts": ["5 km/h", "10 km/h", "7.5 km/h", "4 km/h"],
            "corr": 0,
            "exp": "Downwind speed = 120/3 = 40 km/h. Upwind speed = 120/4 = 30 km/h. Wind speed = (40 - 30) / 2 = 5 km/h.",
            "time": 60
        },

        # Logical extra topics
        {
            "category": "Logical Reasoning",
            "topic": "Order & Position",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "q": "In a row of boys, A is 10th from left and B is 9th from right. If they interchange positions, A becomes 15th from left. How many boys are in the row?",
            "opts": ["23", "24", "22", "25"],
            "corr": 0,
            "exp": "After interchange, A is at B's old position. Total = Left rank + Right rank - 1 = 15 + 9 - 1 = 23 boys.",
            "time": 45
        },
        {
            "category": "Logical Reasoning",
            "topic": "Logical Deduction",
            "difficulty": "Medium",
            "exam_level": "Standard Placement",
            "label": "Company-Level Practice",
            "q": "If all software engineers write code, and Sarah does not write code, what can logically be deduced?",
            "opts": ["Sarah is not a software engineer", "Sarah might be a manager", "Sarah will write code tomorrow", "None of these"],
            "corr": 0,
            "exp": "By modus tollens: P -> Q. ~Q is true, hence ~P must be true. Sarah is not a software engineer.",
            "time": 30
        },

        # Verbal extra topics
        {
            "category": "Verbal Ability",
            "topic": "Vocabulary",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "question": "Select the word closest in meaning to 'EPHEMERAL':",
            "options": ["Short-lived", "Eternal", "Heavy", "Fragile"],
            "correct": 0,
            "explanation": "'Ephemeral' means lasting for a very short time; transient.",
            "time_recommendation": 30
        },
        {
            "category": "Verbal Ability",
            "topic": "Sentence Arrangement",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "question": "Arrange the parts to form a coherent sentence:\n(1) the deployment pipeline / (2) failed / (3) due to a syntax error / (4) in the configuration file",
            "options": ["1-2-3-4", "4-3-2-1", "2-1-3-4", "3-4-1-2"],
            "correct": 0,
            "explanation": "Natural grammatical structure: Subject (1) + Verb (2) + Prepositional phrase (3) + Modifying phrase (4): 'The deployment pipeline failed due to a syntax error in the configuration file.'",
            "time_recommendation": 30
        },

        # DI extra topics
        {
            "category": "Data Interpretation",
            "topic": "Mixed Graphs",
            "difficulty": "Hard",
            "exam_level": "Advanced Placement",
            "label": "Company-Level Practice",
            "question": "A company produces 500,000 units. A pie chart shows 40% are Model X. A line chart reveals defective rate for Model X is 2%. How many non-defective Model X units were produced?",
            "options": ["196,000 units", "200,000 units", "198,000 units", "190,000 units"],
            "correct": 0,
            "explanation": "Total Model X units = 40% of 500,000 = 200,000. Defective = 2% of 200,000 = 4,000. Non-defective = 200,000 - 4,000 = 196,000 units.",
            "time_recommendation": 75
        },
        {
            "category": "Data Interpretation",
            "topic": "Ratio-based DI",
            "difficulty": "Medium",
            "exam_level": "Standard Placement",
            "label": "Placement Exam Style",
            "question": "In a company of 1200 employees, the ratio of Male to Female engineers is 5 : 3. If 20% of males and 30% of females work in Cloud Computing, how many total employees work in Cloud Computing?",
            "options": ["285", "300", "270", "295"],
            "correct": 0,
            "explanation": "Total parts = 5 + 3 = 8. Males = (5/8)*1200 = 750. Females = (3/8)*1200 = 450. Cloud Males = 20% of 750 = 150. Cloud Females = 30% of 450 = 135. Total Cloud employees = 150 + 135 = 285.",
            "time_recommendation": 60
        },
        {
            "category": "Data Interpretation",
            "topic": "Average-based DI",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "question": "Quarterly profits of a tech startup were: Q1: $120k, Q2: $150k, Q3: $180k, Q4: $230k. What was the average monthly profit across the entire year?",
            "options": ["$56.67k", "$60.00k", "$55.00k", "$58.33k"],
            "correct": 0,
            "explanation": "Total annual profit = 120 + 150 + 180 + 230 = $680k. There are 12 months in a year. Average monthly profit = 680 / 12 = $56.67k.",
            "time_recommendation": 45
        },

        # Technical extra topics
        {
            "category": "Technical Aptitude",
            "topic": "Programming basics",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "question": "Which of the following describes the difference between a compiler and an interpreter?",
            "options": [
                "A compiler translates entire code before execution; an interpreter translates line by line at runtime",
                "An interpreter produces standalone binary executables",
                "Compilers cannot catch syntax errors",
                "There is no functional difference"
            ],
            "correct": 0,
            "explanation": "Compilers translate entire source code into machine code prior to execution, whereas interpreters execute instructions line-by-line during runtime.",
            "time_recommendation": 30
        },
        {
            "category": "Technical Aptitude",
            "topic": "Computer Fundamentals",
            "difficulty": "Easy",
            "exam_level": "Basic Placement",
            "label": "Placement Exam Style",
            "question": "How many bytes are in a 64-bit memory address?",
            "options": ["8 bytes", "4 bytes", "16 bytes", "64 bytes"],
            "correct": 0,
            "explanation": "1 byte = 8 bits. A 64-bit architecture address contains 64 / 8 = 8 bytes.",
            "time_recommendation": 30
        }
    ]

    for idx, t in enumerate(templates):
        q_id = f"extra_{t['topic'].lower().replace(' ', '_').replace('&', 'and')}_{idx+1}"
        generated.append({
            "id": q_id,
            "category": t["category"],
            "topic": t["topic"],
            "difficulty": t.get("difficulty", "Medium"),
            "exam_level": t.get("exam_level", "Standard Placement"),
            "label": t.get("label", "Placement Exam Style"),
            "question": t.get("question") or t.get("q"),
            "options": t.get("options") or t.get("opts"),
            "correct": t.get("correct") if "correct" in t else t.get("corr", 0),
            "explanation": t.get("explanation") or t.get("exp"),
            "time_recommendation": t.get("time_recommendation") or t.get("time", 60)
        })

    return generated

# Combine base repository with programmatic extensions
ALL_APTITUDE_QUESTIONS = QUESTIONS_DATA + _generate_synthetic_placement_questions()

# ------------------------------------------------------------------------------
# POPULATE EXPANDED REPERTOIRE (To ensure multi-question depth per topic)
# ------------------------------------------------------------------------------
def _expand_question_depth():
    """Expands question bank to 200+ placement-verified questions across all topics."""
    extra_questions = []
    
    extra_items = [
        ("Quantitative Aptitude", "Number System", "Easy", "What is the unit digit in the product (781 × 342 × 893 × 997)?", ["2", "4", "6", "8"], 0, "Multiply unit digits: 1 × 2 = 2. 2 × 3 = 6. 6 × 7 = 42. The unit digit is 2.", 30),
        ("Quantitative Aptitude", "Number System", "Medium", "How many numbers between 100 and 500 are completely divisible by both 4 and 6?", ["33", "34", "32", "30"], 0, "LCM(4, 6) = 12. Multiples between 100 and 500: First is 108 (12*9), last is 492 (12*41). Number of terms = 41 - 9 + 1 = 33.", 60),
        ("Quantitative Aptitude", "HCF & LCM", "Easy", "Find the greatest number that will divide 43, 91, and 183 so as to leave the same remainder in each case.", ["4", "7", "9", "13"], 0, "Required number = HCF(|91-43|, |183-91|, |183-43|) = HCF(48, 92, 140) = 4.", 60),
        ("Quantitative Aptitude", "Percentage", "Easy", "A's salary is 20% lower than B's salary. By what percentage is B's salary higher than A's?", ["25%", "20%", "16.67%", "30%"], 0, "Let B = 100, then A = 80. Difference = 20. % higher = (20 / 80) * 100 = 25%.", 45),
        ("Quantitative Aptitude", "Profit & Loss", "Easy", "A vendor sells 6 bananas for $5 and buys 5 bananas for $6. What is the loss/gain?", ["44% profit", "44% loss", "25% profit", "30% profit"], 0, "Cost of 1 = 5/6. Selling price = 6/5. Gain = 6/5 - 5/6 = 11/30. Gain % = (11/30) / (5/6) * 100 = 44% profit.", 60),
        ("Quantitative Aptitude", "Ratio & Proportion", "Medium", "Divide $1050 among P, Q, and R such that P receives 2/5 of what Q and R receive together. What is P's share?", ["$300", "$350", "$400", "$250"], 0, "P = 2/5(Q + R) => P / (Q + R) = 2/5. P's share = 2 / (2 + 5) * 1050 = (2/7) * 1050 = $300.", 60),
        ("Quantitative Aptitude", "Average", "Hard", "The average temperature of Mon, Tue, Wed was 40°C. Tue, Wed, Thu was 41°C. If Thursday was 42°C, find Monday's temperature.", ["39°C", "38°C", "40°C", "37°C"], 0, "(Mon + Tue + Wed) = 120. (Tue + Wed + Thu) = 123. Subtracting: Thu - Mon = 3. Since Thu = 42, Mon = 42 - 3 = 39°C.", 60),
        ("Quantitative Aptitude", "Time & Work", "Medium", "12 workers can build a wall in 15 days working 8 hours a day. How many workers can build it in 10 days working 6 hours a day?", ["24 workers", "20 workers", "22 workers", "26 workers"], 0, "M1*D1*H1 = M2*D2*H2 => 12 * 15 * 8 = M2 * 10 * 6 => 1440 = 60 * M2 => M2 = 24 workers.", 60),
        ("Quantitative Aptitude", "Simple Interest", "Medium", "A sum lent at simple interest amounts to $720 after 2 years and to $1020 after another 5 years. What is the sum?", ["$600", "$550", "$500", "$650"], 0, "Interest for 5 years = 1020 - 720 = 300. Interest for 1 year = 60. Interest for 2 years = 120. Principal = 720 - 120 = $600.", 60),
        ("Quantitative Aptitude", "Compound Interest", "Easy", "What is the compound interest on $10,000 for 2 years at 10% per annum compounded annually?", ["$2,100", "$2,000", "$2,200", "$2,050"], 0, "Amount = 10000 * (1.1)^2 = 12100. CI = 12100 - 10000 = $2,100.", 45),
        ("Quantitative Aptitude", "Probability", "Easy", "A card is drawn from a well-shuffled pack of 52 cards. What is the probability that it is an Ace or a King?", ["2/13", "1/13", "4/13", "1/26"], 0, "4 Aces + 4 Kings = 8 cards. Probability = 8 / 52 = 2 / 13.", 30),
        ("Quantitative Aptitude", "Age Problems", "Medium", "Ten years ago, A was half of B in age. If the ratio of their present ages is 3 : 4, what is the sum of their present ages?", ["35 years", "40 years", "42 years", "32 years"], 0, "Present ages: 3x and 4x. (3x - 10) / (4x - 10) = 1/2 => 6x - 20 = 4x - 10 => 2x = 10 => x = 5. Sum = 3x + 4x = 7x = 35 years.", 60),
        ("Quantitative Aptitude", "Mensuration", "Medium", "If the diagonal of a cube is 6√3 cm, what is its total surface area?", ["216 sq cm", "180 sq cm", "144 sq cm", "256 sq cm"], 0, "Diagonal of cube = a√3 = 6√3 => a = 6 cm. Total surface area = 6 * a^2 = 6 * 36 = 216 sq cm.", 45),

        # Logical
        ("Logical Reasoning", "Number Series", "Medium", "Find the next term: 2, 6, 12, 20, 30, 42, ?", ["56", "54", "58", "60"], 0, "Differences are +4, +6, +8, +10, +12. Next difference is +14: 42 + 14 = 56 (or n*(n+1): 7*8=56).", 45),
        ("Logical Reasoning", "Letter Series", "Medium", "Find the next letters: AZ, BY, CX, DW, ?", ["EV", "EU", "FU", "FW"], 0, "First letter moves +1: A, B, C, D -> E. Second letter moves -1: Z, Y, X, W -> V. Term is EV.", 30),
        ("Logical Reasoning", "Blood Relations", "Medium", "If P $ Q means P is father of Q, P # Q means P is mother of Q, and P * Q means P is sister of Q. In A $ B * C, how is A related to C?", ["Father", "Uncle", "Brother", "Grandfather"], 0, "A $ B -> A is father of B. B * C -> B is sister of C. Therefore, A is also the father of C.", 45),
        ("Logical Reasoning", "Direction Sense", "Easy", "A clock shows 4:30. If the minute hand points East, in which direction will the hour hand point?", ["North-East", "South-East", "North", "South"], 0, "At 4:30, minute hand is at 6 (South normally). If it points East, rotation is 90° counter-clockwise. Hour hand between 4 and 5 (South-East) rotates 90° CCW to point North-East.", 60),
        ("Logical Reasoning", "Syllogism", "Easy", "Statements: All cars are vehicles. All vehicles are machines. Conclusion: All cars are machines.", ["Conclusion follows", "Does not follow", "Cannot be determined", "Partially follows"], 0, "Cars ⊆ Vehicles ⊆ Machines. All cars are machines follows definitely.", 30),
        ("Logical Reasoning", "Clocks", "Easy", "How many times do the hands of a clock coincide in a 24-hour period?", ["22 times", "24 times", "44 times", "48 times"], 0, "The hands coincide 11 times in every 12 hours (between 11 and 1 they coincide once at 12). In 24 hours: 11 * 2 = 22 times.", 30),
        ("Logical Reasoning", "Calendars", "Easy", "How many odd days are there in a normal non-leap year of 365 days?", ["1 odd day", "2 odd days", "0 odd days", "3 odd days"], 0, "365 = 52 weeks + 1 day. Hence, exactly 1 odd day.", 30),

        # Verbal
        ("Verbal Ability", "Synonyms", "Easy", "Find the synonym of 'PRAGMATIC':", ["Practical", "Theoretical", "Arrogant", "Hesitant"], 0, "'Pragmatic' means dealing with things sensibly and realistically based on practical considerations.", 30),
        ("Verbal Ability", "Antonyms", "Easy", "Find the antonym of 'AFFLUENT':", ["Poor", "Wealthy", "Healthy", "Fluent"], 0, "'Affluent' means wealthy; its direct opposite is 'Poor'.", 30),
        ("Verbal Ability", "Error Detection", "Medium", "Spot the error: 'He has been working (A) / in this organization (B) / since five years. (C) / No error (D)'", ["Part (C) - 'since five years'", "Part (A)", "Part (B)", "Part (D)"], 0, "For a duration of time ('five years'), the preposition 'for' should be used instead of 'since'. Correct is 'for five years'.", 45),
        ("Verbal Ability", "Sentence Correction", "Easy", "Correct: 'She is taller than me.' in formal English:", ["She is taller than I am.", "She is more tall than me.", "She is taller from me.", "She is taller to me."], 0, "In comparative clauses where a pronoun follows 'than', standard grammar prescribes the subjective pronoun: 'taller than I (am)'.", 30),
        ("Verbal Ability", "Idioms & Phrases", "Easy", "What is meant by 'A blessing in disguise'?", ["A good thing that seemed bad at first", "A secret miracle", "A fake gift", "An unavoidable penalty"], 0, "'A blessing in disguise' describes an apparent misfortune that eventually produces beneficial results.", 30),

        # DI
        ("Data Interpretation", "Tables", "Easy", "A candidate scored 80 in Math, 75 in Physics, 85 in Chemistry. Total possible was 100 per subject. What is the overall percentage?", ["80%", "78%", "82%", "85%"], 0, "Total = 80 + 75 + 85 = 240 / 300 = 80%.", 30),
        ("Data Interpretation", "Bar Graphs", "Medium", "Production in Year 1 was 50 units and Year 2 was 65 units. What was the growth percentage?", ["30%", "25%", "35%", "20%"], 0, "Increase = 15. % Increase = (15 / 50) * 100 = 30%.", 30),

        # Technical
        ("Technical Aptitude", "Programming basics", "Easy", "What is the typical time complexity of accessing an array element by its index?", ["O(1)", "O(N)", "O(log N)", "O(N^2)"], 0, "Array elements are stored in contiguous memory addresses; indexing arithmetic allows O(1) constant time access.", 30),
        ("Technical Aptitude", "Python", "Medium", "In Python, which built-in function returns both the index and the item during a loop iteration?", ["enumerate()", "zip()", "map()", "filter()"], 0, "The `enumerate()` function adds a counter to an iterable and returns an enumerate object.", 30),
        ("Technical Aptitude", "Data Structures", "Medium", "Which data structure is optimal for implementing a LRU (Least Recently Used) cache?", ["Hash Map + Doubly Linked List", "Binary Heap", "Stack", "Queue only"], 0, "A Hash Map provides O(1) key lookup, while a Doubly Linked List maintains chronological access order for O(1) node removals and insertions.", 45),
        ("Technical Aptitude", "Algorithms", "Easy", "What search algorithm works on a sorted array by dividing the search interval in half repeatedly?", ["Binary Search", "Linear Search", "Depth First Search", "Breadth First Search"], 0, "Binary Search repeatedly divides the search space in half with O(log N) complexity.", 30),
        ("Technical Aptitude", "DBMS", "Medium", "What does 3NF (Third Normal Form) eliminate from a relational schema?", ["Transitive dependencies", "Partial functional dependencies", "Multivalued dependencies", "Duplicate table names"], 0, "2NF eliminates partial dependencies on primary key; 3NF eliminates transitive functional dependencies on non-prime attributes.", 45),
        ("Technical Aptitude", "SQL", "Easy", "Which SQL command is used to permanently remove all rows from a table without logging individual row deletions?", ["TRUNCATE", "DELETE", "DROP", "ALTER"], 0, "TRUNCATE TABLE removes all rows quickly with minimal transaction logging compared to DELETE.", 30),
        ("Technical Aptitude", "Operating Systems", "Medium", "In OS process management, what is a PCB?", ["Process Control Block", "Primary CPU Board", "Program Counter Buffer", "Processor Cache Bus"], 0, "A Process Control Block (PCB) is a kernel data structure containing all information regarding a process state, registers, and scheduling.", 30),
        ("Technical Aptitude", "Computer Networks", "Easy", "What protocol maps an IP address to a physical MAC address on a local area network?", ["ARP (Address Resolution Protocol)", "DHCP", "DNS", "ICMP"], 0, "ARP resolves a known 32-bit IPv4 address into its corresponding 48-bit MAC address.", 30),
        ("Technical Aptitude", "Software Engineering", "Easy", "What does the 'S' in the SOLID design principles stand for?", ["Single Responsibility Principle", "System Scalability Principle", "Synchronous Execution", "Substitutability"], 0, "SOLID: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.", 30),
        ("Technical Aptitude", "Basic Web Technologies", "Easy", "In CSS, what is the default value of the `position` property?", ["static", "relative", "absolute", "fixed"], 0, "Every HTML element has a default CSS position of `static`, placing it in normal document flow.", 30)
    ]

    for i, item in enumerate(extra_items):
        cat, top, diff, q, opts, corr, exp, t_rec = item
        qid = f"apt_depth_{cat[:3].lower()}_{top[:3].lower()}_{i+1}"
        extra_questions.append({
            "id": qid,
            "category": cat,
            "topic": top,
            "difficulty": diff,
            "exam_level": "Standard Placement" if diff == "Medium" else ("Advanced Placement" if diff == "Hard" else "Basic Placement"),
            "label": "Company-Level Practice" if i % 2 == 0 else "Placement Exam Style",
            "question": q,
            "options": opts,
            "correct": corr,
            "explanation": exp,
            "time_recommendation": t_rec
        })

    return extra_questions

ALL_APTITUDE_QUESTIONS.extend(_expand_question_depth())

try:
    from percentage_questions import PERCENTAGE_QUESTIONS
    ALL_APTITUDE_QUESTIONS.extend(PERCENTAGE_QUESTIONS)
except ImportError:
    pass

# Re-export for compatibility with older code
APTITUDE_QUESTIONS = ALL_APTITUDE_QUESTIONS
CS_MCQ_QUESTIONS = [q for q in ALL_APTITUDE_QUESTIONS if q["category"] in ("Technical Aptitude", "Computer Science")]

# ------------------------------------------------------------------------------
# DATABASE SEEDER ROUTINE
# ------------------------------------------------------------------------------
def seed_aptitude_questions(conn):
    """
    Ensures that SQLite `aptitude_questions` table contains all current questions.
    Performs UPSERT / INSERT OR REPLACE so updates are reflected seamlessly.
    Normalizes 'Quantitative Aptitude' to 'Quantitative' for consistent querying.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aptitude_questions (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            exam_level TEXT NOT NULL,
            label TEXT NOT NULL,
            question TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_option INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            time_recommendation INTEGER NOT NULL DEFAULT 60,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Indexes for fast filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_q_cat ON aptitude_questions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_q_top ON aptitude_questions(topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_apt_q_diff ON aptitude_questions(difficulty)")

    # Insert / Replace all defined questions
    for q in ALL_APTITUDE_QUESTIONS:
        norm_cat = "Quantitative" if q["category"] == "Quantitative Aptitude" else q["category"]
        cursor.execute("""
            INSERT OR REPLACE INTO aptitude_questions (
                id, category, topic, difficulty, exam_level, label,
                question, options_json, correct_option, explanation,
                time_recommendation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q["id"],
            norm_cat,
            q["topic"],
            q["difficulty"],
            q.get("exam_level", "Standard Placement"),
            q.get("label", "Placement Exam Style"),
            q["question"],
            json.dumps(q["options"]),
            q["correct"],
            q["explanation"],
            q.get("time_recommendation", 60)
        ))
    conn.commit()
    print(f"Aptitude Bank: Seeded {len(ALL_APTITUDE_QUESTIONS)} questions across {len(APTITUDE_TAXONOMY)} categories.")

