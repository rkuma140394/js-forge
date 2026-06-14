#!/usr/bin/env python3
"""
JS Forge - Hidden Test Suite Runner
Thunder Hackathon 2.0 - Extended Test Cases
"""

import sys
import os
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from interpreter import Interpreter, JSError

# ============== HIDDEN TEST CASES ==============

HIDDEN_TESTS = [
    {
        "name": "HT-1: Arrow Functions",
        "file": "tests/test6_arrow_functions.js",
        "expected": ["7", "25", "Hello"]
    },
    {
        "name": "HT-2: const vs let Scoping",
        "file": "tests/test7_const_let.js",
        "expected": ["30", "10", "20"]
    },
    {
        "name": "HT-3: Type Coercion (== vs ===)",
        "file": "tests/test8_type_coercion.js",
        "expected": ["true", "false", "true", "false", "true", "false", "true", "false"]
    },
    {
        "name": "HT-4: Array map/filter/reduce/find/some/every",
        "file": "tests/test9_array_methods.js",
        "expected": ["2, 4, 6, 8, 10", "2, 4", "15", "2", "true", "true"]
    },
    {
        "name": "HT-5: String Methods (trim/toUpperCase/toLowerCase/includes/startsWith/endsWith/indexOf/replace/substring)",
        "file": "tests/test10_string_methods.js",
        "expected": ["Hello World", "  HELLO WORLD  ", "  hello world  ", "true", "true", "true", "8", "  Hello Universe  ", "Hello"]
    },
    {
        "name": "HT-6: Objects & Object.keys/values",
        "file": "tests/test11_objects.js",
        "expected": ["Alice", "25", "26", "name, age", "Alice, 26"]
    },
    {
        "name": "HT-7: Spread Operator",
        "file": "tests/test12_spread.js",
        "expected": ["1, 2, 3, 4, 5", "a, b, c"]
    },
    {
        "name": "HT-8: Ternary Operator",
        "file": "tests/test13_ternary.js",
        "expected": ["B", "Odd"]
    },
    {
        "name": "HT-9: do-while Loop",
        "file": "tests/test14_dowhile.js",
        "expected": ["123"]
    },
    {
        "name": "HT-10: switch Statement",
        "file": "tests/test15_switch.js",
        "expected": ["Wednesday"]
    },
    {
        "name": "HT-11: typeof Operator",
        "file": "tests/test16_typeof.js",
        "expected": ["number", "string", "boolean", "undefined", "object", "object", "object", "function"]
    },
    {
        "name": "HT-12: Math Object (abs/pow/sqrt/max/min/ceil/floor/round/trunc/sign)",
        "file": "tests/test17_math.js",
        "expected": ["5", "8", "4", "5", "1", "5", "4", "5", "4", "-1"]
    },
    {
        "name": "HT-13: Callbacks & Closures",
        "file": "tests/test18_callbacks.js",
        "expected": ["12", "15", "6"]
    },
    {
        "name": "HT-14: Array push/pop/shift/unshift/includes",
        "file": "tests/test19_array_stack.js",
        "expected": ["1, 2, 3, 4", "1, 2, 3", "0, 1, 2, 3", "1, 2, 3", "true", "false"]
    },
    {
        "name": "HT-15: try-catch-finally",
        "file": "tests/test20_trycatch.js",
        "expected": ["No error", "Finally block", "Infinity"]
    },
    {
        "name": "HT-16: for-of Loop",
        "file": "tests/test21_forof.js",
        "expected": ["abc"]
    },
    {
        "name": "HT-17: Array slice & splice",
        "file": "tests/test22_slice_splice.js",
        "expected": ["2, 3, 4", "1, 2, 3, 4, 5", "3, 4", "1, 2, 5"]
    },
    {
        "name": "HT-18: String split("") and join",
        "file": "tests/test23_string_split_join.js",
        "expected": ["a-b-c", "hello, world, test"]
    },
    {
        "name": "HT-19: Nested Loops + break/continue",
        "file": "tests/test24_nested_loops.js",
        "expected": ["11 13 21 23 31 33"]
    },
    {
        "name": "HT-20: Function Expressions",
        "file": "tests/test25_func_expr.js",
        "expected": ["20", "5"]
    },
]

VISIBLE_TESTS = [
    {
        "name": "TC-1: Odd/Even Checker",
        "file": "tests/test1.js",
        "expected": ["7 is Odd"]
    },
    {
        "name": "TC-2: Triangle Pattern",
        "file": "tests/test2.js",
        "expected": ["*", "**", "***", "****", "*****"]
    },
    {
        "name": "TC-3: Armstrong Number",
        "file": "tests/test3.js",
        "expected": ["true", "false"]
    },
    {
        "name": "TC-4: Array Reverse",
        "file": "tests/test4.js",
        "expected": ["Original: 1, 2, 3, 4, 5", "Reversed: 5, 4, 3, 2, 1"]
    },
    {
        "name": "TC-5: String Palindrome",
        "file": "tests/test5.js",
        "expected": ["racecar is a Palindrome"]
    },
]

def run_single_test(test):
    """Run a single test and return (passed, output, error)"""
    try:
        with open(test["file"], "r") as f:
            source = f.read()

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()

        f = io.StringIO()
        with redirect_stdout(f):
            interpreter.run(ast)
        output = f.getvalue().strip().split("\n") if f.getvalue().strip() else []

        expected = test["expected"]
        if output == expected:
            return True, output, None
        else:
            return False, output, f"Expected: {expected}\nGot:      {output}"

    except Exception as e:
        return False, [], str(e)

def run_test_suite(tests, title):
    passed = 0
    total = len(tests)

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for test in tests:
        ok, output, error = run_single_test(test)
        status = "✅ PASSED" if ok else "❌ FAILED"
        print(f"\n{test['name']}")
        print("-" * 50)
        if ok:
            print(f"{status}")
            passed += 1
        else:
            print(f"{status}")
            if error:
                print(f"   {error}")

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{total} passed")
    print("=" * 70)
    return passed, total

def main():
    print("\n" + "🚀 " * 20)
    print("JS FORGE - COMPLETE TEST SUITE")
    print("🚀 " * 20)

    # Run visible tests
    v_passed, v_total = run_test_suite(VISIBLE_TESTS, "VISIBLE TEST CASES (Hackathon Official)")

    # Run hidden tests
    h_passed, h_total = run_test_suite(HIDDEN_TESTS, "HIDDEN TEST CASES (Extended Coverage)")

    # Grand total
    total_passed = v_passed + h_passed
    total_tests = v_total + h_total

    print("\n" + "🎯 " * 20)
    print(f"GRAND TOTAL: {total_passed}/{total_tests} tests passed")
    print(f"Visible: {v_passed}/{v_total} | Hidden: {h_passed}/{h_total}")
    print("🎯 " * 20)

    if total_passed == total_tests:
        print("\n🏆 PERFECT SCORE! ALL TESTS PASSING!")

    return total_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
