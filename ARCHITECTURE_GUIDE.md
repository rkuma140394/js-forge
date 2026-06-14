# JS Forge - Complete Code Architecture Guide

## Table of Contents
1. [Big Picture: How a JS Interpreter Works](#1-big-picture)
2. [File-by-File Breakdown](#2-file-breakdown)
3. [Data Flow: From Source to Output](#3-data-flow)
4. [Step-by-Step Example Trace](#4-example-trace)
5. [Key Design Decisions](#5-design-decisions)
6. [Class Hierarchy](#6-class-hierarchy)
7. [Common Patterns](#7-common-patterns)
8. [How to Add New Features](#8-adding-features)

---

## 1. Big Picture: How a JS Interpreter Works

A JavaScript interpreter has 3 main stages, just like a compiler:

```
SOURCE CODE → [LEXER] → TOKENS → [PARSER] → AST → [INTERPRETER] → OUTPUT
```

### Stage 1: Lexer (Tokenizer)
**Job:** Break raw text into meaningful chunks called "tokens"

```javascript
let x = 5 + 3;
```

Becomes:
```
[LET, IDENTIFIER("x"), ASSIGN, NUMBER(5), PLUS, NUMBER(3), SEMICOLON]
```

Think of it like cutting a sentence into words.

### Stage 2: Parser
**Job:** Build a tree structure (AST) that shows the relationships between tokens

The same code becomes a tree:
```
Program
└── VariableDeclaration (let)
    └── VariableDeclarator
        ├── id: Identifier("x")
        └── init: BinaryExpression(+)
            ├── left: Literal(5)
            └── right: Literal(3)
```

Think of it like diagramming a sentence in grammar class.

### Stage 3: Interpreter
**Job:** Walk the tree and actually DO what the code says

It creates variables, runs loops, calls functions, and prints output.

---

## 2. File-by-File Breakdown

### `lexer.py` — The Tokenizer

**Core Classes:**
- `TokenType` (Enum) — All possible token types (LET, NUMBER, PLUS, etc.)
- `Token` (dataclass) — A single token with type, value, line, column
- `Lexer` — The main tokenizer engine

**Key Method:** `scan_token()`
- Looks at current character
- Decides what token it is
- Advances past it
- Handles multi-character tokens (===, ++, =>)
- Handles strings with escape sequences
- Skips whitespace and comments

**How it works:**
1. Start at position 0
2. Skip whitespace/comments
3. Look at current char:
   - `l` → might be `let`, read full word, check keywords dict
   - `"` → read string until closing quote
   - `5` → read number (handle decimals, exponents)
   - `+` → check if next is `+` (++) or `=` (+=)
4. Add token to list
5. Repeat until end of file
6. Add EOF token

---

### `parser.py` — The AST Builder

**Core Classes:**
- `Program`, `VariableDeclaration`, `IfStatement`, `BinaryExpression`, etc.
- All are dataclasses that represent tree nodes

**Key Method:** `parse()` (entry point)
**Key Pattern:** Recursive descent parsing

**How it works:**
The parser has methods for each grammar rule, organized by precedence:

```
expression() → assignment_expression()
assignment_expression() → conditional_expression()
conditional_expression() → logical_or_expression()
logical_or_expression() → logical_and_expression()
logical_and_expression() → equality_expression()
...continues down...
primary_expression() → literals, identifiers, parenthesized expressions
```

**Why this structure?** 
Each level handles operators of a specific precedence. Lower methods = lower precedence (evaluated last). Higher methods = higher precedence (evaluated first).

Example: `a + b * c`
- `*` is in `multiplicative_expression()` (higher precedence)
- `+` is in `additive_expression()` (lower precedence)
- The tree becomes: `(a + (b * c))` not `((a + b) * c)`

**Statement parsing:**
```
statement() checks the current token:
- IF → parse if_statement()
- FOR → parse for_statement()
- LET/CONST → parse variable_declaration()
- FUNCTION → parse function_declaration()
- { → parse block_statement()
- otherwise → parse expression_statement()
```

---

### `interpreter.py` — The Execution Engine

**Core Classes:**

#### `JSValue` — Base class for ALL JavaScript values
```python
class JSValue:
    type: str      # 'number', 'string', 'boolean', 'undefined', 'null', 'function', 'object'
    value: any     # The actual Python value
    properties: dict  # For objects/functions
    callable: bool    # Can it be called?
    constructor: bool # Can it be used with `new`?
```

Special instances:
- `JSUndefined` — the undefined value
- `JSNull` — the null value
- `JSTrue` / `JSFalse` — boolean singletons

#### `JSObject` — JavaScript objects
```python
class JSObject(JSValue):
    properties: dict
    prototype: JSObject  # Prototype chain for method lookup

    def get(key):  # Looks up key, falls back to prototype
    def set(key, value):  # Sets property
```

#### `JSArray` — JavaScript arrays
```python
class JSArray(JSValue):
    elements: list       # The actual array data
    properties: dict      # 'length' and methods
    prototype: JSObject  # Array.prototype for methods like push, map, etc.

    def get(key):
        # If key is a number, return element
        # If key is 'length', return len(elements)
        # Otherwise, check properties, then prototype
```

#### `JSFunction` — User-defined functions
```python
class JSFunction(JSValue):
    params: list         # Parameter names
    body: ASTNode        # The function body (AST)
    closure: Environment # Captured variables (for closures!)
    arrow: bool          # Is it an arrow function?
    bound_this: JSValue  # `this` binding for arrow functions
```

#### `JSNativeFunction` — Built-in functions (console.log, Math.floor, etc.)
```python
class JSNativeFunction(JSValue):
    native_func: callable  # A Python function that implements the JS behavior
```

#### `Environment` — Variable scope
```python
class Environment:
    variables: dict       # name → {value, kind}
    parent: Environment   # Outer scope (for closures)

    def define(name, value, kind):  # Create variable
    def get(name):                   # Read variable (walks up chain)
    def set(name, value):            # Update variable (walks up chain)
```

**How it works:**
The interpreter uses **visitor pattern** — each AST node type has a corresponding `eval_*` method.

```python
def evaluate(self, node):
    method_name = f'eval_{type(node).__name__}'
    method = getattr(self, method_name)
    return method(node)
```

Example: `eval_BinaryExpression` handles `+`, `-`, `*`, `/`, `===`, etc.

---

## 3. Data Flow: From Source to Output

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCE: let x = 5 + 3; console.log(x);                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEXER                                                      │
│  Input: "let x = 5 + 3; console.log(x);"                   │
│  Output: [LET, ID("x"), ASSIGN, NUM(5), PLUS, NUM(3),     │
│           SEMI, ID("console"), DOT, ID("log"), LPAREN,     │
│           ID("x"), RPAREN, SEMI, EOF]                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PARSER                                                     │
│  Builds tree:                                               │
│  Program                                                    │
│  ├── VariableDeclaration(let)                               │
│  │   └── VariableDeclarator                                 │
│  │       ├── id: Identifier("x")                           │
│  │       └── init: BinaryExpression(+)                      │
│  │           ├── left: Literal(5)                            │
│  │           └── right: Literal(3)                          │
│  └── ExpressionStatement                                    │
│      └── CallExpression                                     │
│          ├── callee: MemberExpression                     │
│          │   ├── object: Identifier("console")             │
│          │   └── property: Identifier("log")               │
│          └── arguments: [Identifier("x")]                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  INTERPRETER                                                │
│  1. eval_VariableDeclaration:                               │
│     - env.define("x", JSValue('number', 8), 'let')          │
│                                                             │
│  2. eval_CallExpression:                                    │
│     - eval callee: looks up "console.log" → JSNativeFunction │
│     - eval arguments: looks up "x" → JSValue('number', 8)  │
│     - js_call(native_func, [8], console_obj)               │
│     - native_func prints "8"                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: 8                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Step-by-Step Example Trace

Let's trace: `let arr = [1, 2, 3]; console.log(arr.reverse().join("-"));`

### Step 1: Lexer
```
LET | 'let'
IDENTIFIER | 'arr'
ASSIGN | '='
LBRACKET | '['
NUMBER | 1
COMMA | ','
NUMBER | 2
COMMA | ','
NUMBER | 3
RBRACKET | ']'
SEMICOLON | ';'
IDENTIFIER | 'console'
DOT | '.'
IDENTIFIER | 'log'
LPAREN | '('
IDENTIFIER | 'arr'
DOT | '.'
IDENTIFIER | 'reverse'
LPAREN | '('
RPAREN | ')'
DOT | '.'
IDENTIFIER | 'join'
LPAREN | '('
STRING | '-'
RPAREN | ')'
RPAREN | ')'
SEMICOLON | ';'
EOF
```

### Step 2: Parser
```
Program
├── VariableDeclaration(let)
│   └── VariableDeclarator
│       ├── id: Identifier("arr")
│       └── init: ArrayExpression
│           └── elements: [Literal(1), Literal(2), Literal(3)]
│
└── ExpressionStatement
    └── CallExpression
        ├── callee: MemberExpression
        │   ├── object: Identifier("console")
        │   └── property: Identifier("log")
        │
        └── arguments: [CallExpression]
            ├── callee: MemberExpression
            │   ├── object: CallExpression
            │   │   ├── callee: MemberExpression
            │   │   │   ├── object: Identifier("arr")
            │   │   │   └── property: Identifier("reverse")
            │   │   └── arguments: []
            │   └── property: Identifier("join")
            └── arguments: [Literal("-")]
```

### Step 3: Interpreter

**Statement 1:** `let arr = [1, 2, 3];`
1. `eval_VariableDeclaration` → `eval_ArrayExpression`
2. Creates `JSArray([JSValue('number',1), JSValue('number',2), JSValue('number',3)])`
3. Sets `arr.prototype = array_proto` (has reverse, join, etc.)
4. `env.define('arr', js_array, 'let')`

**Statement 2:** `console.log(arr.reverse().join("-"));`
1. `eval_CallExpression` for `console.log(...)`
2. Eval callee: `console.log` → `JSNativeFunction`
3. Eval argument: `arr.reverse().join("-")`

   **3a.** `eval_CallExpression` for `arr.reverse()`
   - Eval callee: `arr.reverse` → `MemberExpression`
     - `arr` → `JSArray` from env
     - `.reverse` → looks up in array_proto → `JSNativeFunction`
   - `js_call(reverse_func, [], arr)`
   - `reverse_func` calls `array_reverse(args=[], this=arr)`
   - `arr.elements.reverse()` → `[3, 2, 1]`
   - Returns `arr` (the same array, now reversed)

   **3b.** `eval_CallExpression` for `.join("-")`
   - Eval callee: `result_of_reverse.join` → `MemberExpression`
     - `result_of_reverse` is `arr` (JSArray)
     - `.join` → looks up in array_proto → `JSNativeFunction`
   - Eval argument: `"-"` → `JSValue('string', '-')`
   - `js_call(join_func, ['-'], arr)`
   - `join_func` calls `array_join(args=['-'], this=arr)`
   - `"-".join(["3", "2", "1"])` → `"3-2-1"`
   - Returns `JSValue('string', '3-2-1')`

4. `js_call(console.log, ['3-2-1'], console)`
5. Prints: `3-2-1`

---

## 5. Key Design Decisions

### Why Recursive Descent Parser?
- **Simple to understand** — each grammar rule = one method
- **Easy to debug** — clear call stack
- **Sufficient for JS subset** — no need for complex LR parser

### Why Visitor Pattern for Interpreter?
- **Extensible** — add new node type = add one method
- **Clean** — no giant switch statement
- **Type-safe** — each eval_* method handles one node type

### Why Separate JSValue Types?
- **Accurate JS semantics** — `typeof null === 'object'` is handled
- **Type coercion** — `5 + "3"` → `"53"` (string wins)
- **Prototype chain** — `arr.map()` works via prototype lookup

### Why Environment Chain?
- **Closures** — inner functions can access outer variables
- **Scope** — `let` in block creates new scope
- **Hoisting** — `var` goes to function scope

---

## 6. Class Hierarchy

```
JSValue (base)
├── JSValue('number', 42)
├── JSValue('string', "hello")
├── JSValue('boolean', True)
├── JSValue('undefined', None)
├── JSValue('null', None)
├── JSFunction
│   └── User-defined functions + arrow functions
├── JSNativeFunction
│   └── Built-ins (console.log, Math.floor, etc.)
├── JSObject
│   └── Plain objects, Math, Date, console
└── JSArray (extends JSObject)
    └── Arrays with numeric index access
```

---

## 7. Common Patterns

### Pattern 1: Evaluating Binary Operators
```python
def eval_BinaryExpression(self, node):
    left = self.evaluate(node.left)   # Recursively eval left side

    # Short-circuit for && and ||
    if node.operator == '&&':
        if not left.is_truthy(): return left
        return self.evaluate(node.right)

    right = self.evaluate(node.right)  # Recursively eval right side

    # Apply operator
    if node.operator == '+':
        return js_add(left, right)     # String concatenation or numeric add
    elif node.operator == '-':
        return JSValue('number', left.to_number() - right.to_number())
    # ... etc
```

### Pattern 2: Function Calls
```python
def js_call(func, args, this):
    if isinstance(func, JSNativeFunction):
        return func.native_func(args, this)  # Direct Python call

    if isinstance(func, JSFunction):
        env = Environment(func.closure)     # Create new scope
        for i, param in enumerate(func.params):
            env.define(param, args[i] if i < len(args) else JSUndefined, 'var')

        interpreter = Interpreter()
        interpreter.env = env
        interpreter.this_value = this if not func.arrow else func.bound_this

        try:
            result = interpreter.evaluate(func.body)
        except JSReturn as ret:
            return ret.value

        # Arrow functions with expression body return the expression
        if func.arrow and type(func.body).__name__ != 'BlockStatement':
            return result
        return JSUndefined
```

### Pattern 3: Variable Lookup
```python
def get(self, name):
    if name in self.variables:
        return self.variables[name]['value']
    if self.parent:
        return self.parent.get(name)  # Walk up the chain
    return JSUndefined  # Not found = undefined in JS
```

### Pattern 4: Prototype Chain Lookup
```python
def get(self, key):
    if key in self.properties:
        return self.properties[key]
    if self.prototype and hasattr(self.prototype, 'get'):
        return self.prototype.get(key)  # Fall back to prototype
    return JSUndefined
```

---

## 8. How to Add New Features

### Adding a new Array method (e.g., `flat()`)

**Step 1:** Add to `create_array_prototype()` in `interpreter.py`:
```python
def array_flat(args, this):
    if not isinstance(this, JSArray):
        return this
    result = []
    for el in this.elements:
        if isinstance(el, JSArray):
            result.extend(el.elements)
        else:
            result.append(el)
    return JSArray(result)

proto.properties['flat'] = JSNativeFunction('flat', array_flat)
```

**Step 2:** Test it:
```javascript
let arr = [1, [2, 3], 4];
console.log(arr.flat().join(", "));
// Expected: 1, 2, 3, 4
```

### Adding a new operator (e.g., `??` nullish coalescing)

**Step 1:** Add token type in `lexer.py`:
```python
NULLISH_COALESCING = auto()  # ??
```

**Step 2:** Add lexer rule:
```python
elif c == '?':
    if self.match('?'): self.add_token(TokenType.NULLISH_COALESCING)
    else: self.add_token(TokenType.QUESTION)
```

**Step 3:** Add parser precedence (between `||` and `??`):
```python
def nullish_expression(self):
    expr = self.logical_or_expression()
    while self.match(TokenType.NULLISH_COALESCING):
        right = self.logical_or_expression()
        # JS semantics: null/undefined → right, otherwise → left
        expr = ConditionalExpression(
            test=BinaryExpression('===', left, JSNull), ...)
    return expr
```

**Step 4:** Add interpreter logic:
```python
def eval_BinaryExpression(self, node):
    # ... existing code ...
    elif node.operator == '??':
        left = self.evaluate(node.left)
        if left.type == 'null' or left.type == 'undefined':
            return self.evaluate(node.right)
        return left
```

---

## Quick Reference: File Map

| File | Lines | Purpose | Key Classes |
|------|-------|---------|-------------|
| `lexer.py` | ~300 | Tokenize source | Token, TokenType, Lexer |
| `parser.py` | ~1100 | Build AST | Program, BinaryExpression, IfStatement, etc. |
| `interpreter.py` | ~1600 | Execute AST | JSValue, JSArray, JSFunction, Environment, Interpreter |
| `main.py` | ~200 | CLI entry | argparse, test runner, REPL |
| `debug.py` | ~200 | Debug toolkit | debug_tokens, debug_ast, debug_execution |

---

## Debugging Tips

1. **Use `debug.py`** — `python debug.py -t 1` shows everything
2. **Add print statements** in `eval_*` methods to trace execution
3. **Check tokens first** — if parsing fails, tokens are usually wrong
4. **Check AST second** — if execution is wrong, AST might be malformed
5. **Use the REPL** — `python main.py -i` for quick experiments

---

**Built for Thunder Hackathon 2.0**  
**Architecture:** Lexer → Parser → Interpreter (3-stage pipeline)  
**Language:** Pure Python 3, zero dependencies  
**Lines of Code:** ~3,400 total
