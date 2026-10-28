# coding_evaluator.py
"""
Safe Controlled Evaluation Architecture for Coding Assessment.

SECURITY ARCHITECTURE & DEFENSE IN DEPTH:
1. AST Static Security Audit: Uses Python's built-in `ast` module to scan submitted code prior to execution.
   Blocks any forbidden imports (os, sys, subprocess, socket, etc.) and dangerous builtins (eval, exec, open, __import__).
2. Namespace Isolation: Sanitizes __builtins__ dictionary to strictly safe algorithmic primitives.
   No file system, process control, or network I/O capabilities exist in the execution environment.
3. Size & Execution Safeguards: Rejects inputs larger than 10KB.
"""

import ast

# Safe built-in primitives allowed for algorithmic problem solving
SAFE_BUILTINS = {
    'abs': abs,
    'all': all,
    'any': any,
    'bool': bool,
    'dict': dict,
    'enumerate': enumerate,
    'float': float,
    'format': format,
    'int': int,
    'len': len,
    'list': list,
    'max': max,
    'min': min,
    'ord': ord,
    'chr': chr,
    'pow': pow,
    'range': range,
    'reversed': reversed,
    'round': round,
    'set': set,
    'slice': slice,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'zip': zip,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'Exception': Exception,
    'ValueError': ValueError,
    'TypeError': TypeError,
    'IndexError': IndexError,
    'KeyError': KeyError,
    'AttributeError': AttributeError,
    'True': True,
    'False': False,
    'None': None
}

FORBIDDEN_MODULES = {
    'os', 'sys', 'subprocess', 'shutil', 'socket', 'importlib', 
    'ctypes', 'multiprocessing', 'threading', 'signal', 'pty', 'builtins'
}

FORBIDDEN_NAMES = {
    'eval', 'exec', 'open', '__import__', 'globals', 'locals', 
    'compile', 'getattr', 'setattr', 'delattr', 'input', 'file'
}


def audit_code_ast(code):
    """
    Statically audits the submitted Python code AST for security compliance.
    Returns (is_safe, error_message).
    """
    if len(code) > 10000:
        return False, "Code size limit exceeded (Max 10,000 characters)."

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {e.msg} on line {e.lineno}"

    for node in ast.walk(tree):
        # 1. Check Import & ImportFrom
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in FORBIDDEN_MODULES:
                    return False, f"Security Violation: Import of module '{alias.name}' is strictly prohibited."
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_MODULES:
                return False, f"Security Violation: Import from module '{node.module}' is strictly prohibited."

        # 2. Check forbidden function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_NAMES:
                    return False, f"Security Violation: Call to restricted function '{node.func.id}()' is prohibited."

        # 3. Check forbidden attribute accesses (e.g. __subclasses__)
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith('__'):
                return False, f"Security Violation: Dunder attribute access '{node.attr}' is prohibited."

    return True, None


def evaluate_python_submission(code, problem_data):
    """
    Evaluates Python submission against problem test cases safely.
    
    Returns dict:
    {
        "status": "Passed" | "Failed" | "Syntax Error" | "Security Blocked",
        "score": int (0-100),
        "passed_tests": int,
        "total_tests": int,
        "classification": "Excellent" | "Good" | "Needs Improvement" | "Practice Required",
        "test_results": list of dicts,
        "error_message": str or None
    }
    """
    # Step 1: Security Audit
    is_safe, sec_error = audit_code_ast(code)
    if not is_safe:
        return {
            "status": "Security Blocked",
            "score": 0,
            "passed_tests": 0,
            "total_tests": len(problem_data.get("test_cases", [])),
            "classification": "Practice Required",
            "test_results": [],
            "error_message": sec_error
        }

    test_cases = problem_data.get("test_cases", [])
    total_tests = len(test_cases)
    if total_tests == 0:
        return {
            "status": "Failed",
            "score": 0,
            "passed_tests": 0,
            "total_tests": 0,
            "classification": "Practice Required",
            "test_results": [],
            "error_message": "No test cases specified for this problem."
        }

    # Step 2: Isolated Execution Scope
    exec_namespace = {"__builtins__": SAFE_BUILTINS}
    try:
        compiled_code = compile(code, "<submitted_code>", "exec")
        exec(compiled_code, exec_namespace)
    except Exception as e:
        return {
            "status": "Syntax Error",
            "score": 0,
            "passed_tests": 0,
            "total_tests": total_tests,
            "classification": "Practice Required",
            "test_results": [],
            "error_message": f"Execution/Compilation Error: {str(e)}"
        }

    # Step 3: Find Target Function
    target_func = None
    for name, obj in exec_namespace.items():
        if callable(obj) and not name.startswith('__'):
            target_func = obj
            break

    if not target_func:
        return {
            "status": "Failed",
            "score": 0,
            "passed_tests": 0,
            "total_tests": total_tests,
            "classification": "Practice Required",
            "test_results": [],
            "error_message": "No executable function found in your submitted code."
        }

    # Step 4: Run Test Cases
    passed_tests = 0
    test_results = []

    for idx, tc in enumerate(test_cases):
        args = tc.get("input", ())
        expected = tc.get("expected")

        try:
            # Handle single vs tuple arguments
            if isinstance(args, tuple):
                actual = target_func(*args)
            else:
                actual = target_func(args)

            is_passed = (actual == expected)
            if is_passed:
                passed_tests += 1

            test_results.append({
                "test_index": idx + 1,
                "input": str(args),
                "expected": str(expected),
                "actual": str(actual),
                "passed": is_passed,
                "error": None
            })
        except Exception as err:
            test_results.append({
                "test_index": idx + 1,
                "input": str(args),
                "expected": str(expected),
                "actual": "Runtime Exception",
                "passed": False,
                "error": str(err)
            })

    score = int(round((passed_tests / total_tests) * 100)) if total_tests > 0 else 0
    status = "Passed" if passed_tests == total_tests else "Failed"

    if score == 100:
        classification = "Excellent"
    elif score >= 80:
        classification = "Good"
    elif score >= 50:
        classification = "Needs Improvement"
    else:
        classification = "Practice Required"

    return {
        "status": status,
        "score": score,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "classification": classification,
        "test_results": test_results,
        "error_message": None
    }
