#!/usr/bin/env python3
"""
JS Forge - JavaScript Interpreter
Thunder Hackathon 2.0 Submission

A custom JavaScript interpreter written in Python from scratch.
Supports: variables, functions, arrays, objects, loops, conditionals,
operators, built-ins (Math, Date, console), and more.

Usage:
    python main.py <file.js>
    python main.py -c "js code here"
    python main.py -i          # Interactive REPL
    python main.py --test      # Run all test cases
"""

import sys
import os
import argparse

# Add project directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from interpreter import Interpreter, JSError, JSReturn, JSBreak, JSContinue

def run_js(source: str, filename: str = "<stdin>"):
    """Execute JavaScript source code and return output."""
    try:
        # Tokenize
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Parse
        parser = Parser(tokens)
        ast = parser.parse()

        # Execute
        interpreter = Interpreter()
        interpreter.run(ast)

    except LexerError as e:
        print(f"SyntaxError: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"SyntaxError: {e}", file=sys.stderr)
        sys.exit(1)
    except JSError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_repl():
    """Interactive Read-Eval-Print Loop."""
    print("JS Forge v1.0 - JavaScript Interpreter")
    print("Type .exit to quit, .help for commands\n")

    interpreter = Interpreter()

    while True:
        try:
            source = input("> ")
            if source.strip() == '.exit':
                break
            if source.strip() == '.help':
                print("Commands: .exit, .help, .clear")
                continue
            if source.strip() == '.clear':
                interpreter = Interpreter()
                print("Environment cleared.")
                continue
            if not source.strip():
                continue

            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()

            # For REPL, we preserve the environment
            for stmt in ast.body:
                result = interpreter.evaluate(stmt)
                if result is not None and result.type != 'undefined':
                    print(result.to_string())

        except (LexerError, ParseError, JSError) as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nUse .exit to quit")
        except EOFError:
            break

    print("\nGoodbye!")

def run_tests():
    """Run all 5 test cases and verify output."""
    tests = [
        {
            "name": "TC-1: Odd/Even Checker",
            "code": """let num = 7;
if (num % 2 === 0) {
    console.log(num + " is Even");
} else {
    console.log(num + " is Odd");
}""",
            "expected": ["7 is Odd"]
        },
        {
            "name": "TC-2: Triangle Pattern",
            "code": """for (let i = 1; i <= 5; i++) {
    let row = "";
    for (let j = 1; j <= i; j++) {
        row += "*";
    }
    console.log(row);
}""",
            "expected": ["*", "**", "***", "****", "*****"]
        },
        {
            "name": "TC-3: Armstrong Number",
            "code": """function isArmstrong(num) {
    let temp = num;
    let sum = 0;
    while (temp > 0) {
        let digit = temp % 10;
        sum += digit ** 3;
        temp = Math.floor(temp / 10);
    }
    return sum === num;
}
console.log(isArmstrong(153));
console.log(isArmstrong(123));""",
            "expected": ["true", "false"]
        },
        {
            "name": "TC-4: Array Reverse",
            "code": """let arr = [1, 2, 3, 4, 5];
let reversed = [...arr].reverse();
console.log("Original: " + arr.join(", "));
console.log("Reversed: " + reversed.join(", "));""",
            "expected": ["Original: 1, 2, 3, 4, 5", "Reversed: 5, 4, 3, 2, 1"]
        },
        {
            "name": "TC-5: String Palindrome",
            "code": """let str = "racecar";
let reversed = str.split("").reverse().join("");
if (str === reversed) {
    console.log(str + " is a Palindrome");
} else {
    console.log(str + " is not a Palindrome");
}""",
            "expected": ["racecar is a Palindrome"]
        }
    ]

    import io
    from contextlib import redirect_stdout

    passed = 0
    total = len(tests)

    print("=" * 60)
    print("JS FORGE - TEST SUITE")
    print("=" * 60)

    for i, test in enumerate(tests, 1):
        print(f"\n[Test {i}] {test['name']}")
        print("-" * 40)

        try:
            lexer = Lexer(test['code'])
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter = Interpreter()

            # Capture output
            f = io.StringIO()
            with redirect_stdout(f):
                interpreter.run(ast)
            output = f.getvalue().strip().split('\n') if f.getvalue().strip() else []

            expected = test['expected']

            if output == expected:
                print(f"✅ PASSED")
                passed += 1
            else:
                print(f"❌ FAILED")
                print(f"   Expected: {expected}")
                print(f"   Got:      {output}")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} tests passed ({passed * 20} points)")
    print("=" * 60)

    return passed == total

def main():
    parser = argparse.ArgumentParser(
        description="JS Forge - A JavaScript Interpreter in Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py program.js
  python main.py -c "console.log(1 + 2);"
  python main.py -i
  python main.py --test
        """
    )
    parser.add_argument('file', nargs='?', help='JavaScript file to execute')
    parser.add_argument('-c', '--code', help='Execute JavaScript code directly')
    parser.add_argument('-i', '--interactive', action='store_true', help='Start REPL')
    parser.add_argument('--test', action='store_true', help='Run test suite')

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.interactive:
        run_repl()
        return

    if args.code:
        run_js(args.code)
        return

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        with open(args.file, 'r') as f:
            source = f.read()
        run_js(source, args.file)
        return

    # No arguments - show help
    parser.print_help()

if __name__ == '__main__':
    main()
