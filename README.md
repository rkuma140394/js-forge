# JS Forge - JavaScript Interpreter

**Thunder Hackathon 2.0 Submission**  
**Build Your Own JavaScript**

A complete JavaScript interpreter written from scratch in Python. No external dependencies, no transpilers, no shortcuts — just pure Python implementing a full lexer, parser, and execution engine for JavaScript.

## 🚀 Features

### Core Language Support
- ✅ Variable declarations (`let`, `const`, `var`)
- ✅ Primitive types (`number`, `string`, `boolean`, `null`, `undefined`)
- ✅ Objects and Arrays
- ✅ All operators (`+`, `-`, `*`, `/`, `%`, `**`, `===`, `==`, `!==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`, `&`, `|`, `^`, `~`, `<<`, `>>`, `>>>`)
- ✅ Compound assignment (`+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`)
- ✅ Increment/Decrement (`++`, `--`)
- ✅ Conditional statements (`if`, `else if`, `else`, `switch`, `case`, `default`)
- ✅ Loops (`for`, `while`, `do...while`, `for...of`, `for...in`)
- ✅ Functions (declarations, expressions, arrow functions)
- ✅ Callbacks and closures
- ✅ `return`, `break`, `continue`
- ✅ `try`, `catch`, `finally`, `throw`
- ✅ `typeof`, `void`, `delete`, `in`, `instanceof`
- ✅ `new` operator and constructors
- ✅ Classes (basic support)
- ✅ Spread operator (`...`) and rest parameters
- ✅ Template literals
- ✅ Ternary operator (`? :`)
- ✅ Short-circuit evaluation (`&&`, `||`)

### Array Methods
`push()`, `pop()`, `shift()`, `unshift()`, `slice()`, `splice()`, `concat()`, `includes()`, `indexOf()`, `sort()`, `reverse()`, `join()`, `map()`, `filter()`, `reduce()`, `find()`, `some()`, `every()`, `forEach()`

### String Methods
`replace()`, `replaceAll()`, `substring()`, `slice()`, `split()`, `trim()`, `toUpperCase()`, `toLowerCase()`, `includes()`, `startsWith()`, `endsWith()`, `indexOf()`, `charAt()`, `charCodeAt()`, `length`

### Built-in Objects
- **`console`**: `log()`, `error()`, `warn()`, `info()`
- **`Math`**: `floor()`, `ceil()`, `round()`, `random()`, `max()`, `min()`, `abs()`, `pow()`, `sqrt()`, `sin()`, `cos()`, `tan()`, `log()`, `exp()`, `trunc()`, `sign()`, plus constants (`PI`, `E`, etc.)
- **`Date`**: Constructor, `now()`, `getTime()`, `getFullYear()`, `getMonth()`, `getDate()`, `getDay()`, `getHours()`, `getMinutes()`, `getSeconds()`, `toString()`
- **`Array`**: Constructor, `isArray()`
- **`String`**: Constructor
- **`Object`**: `keys()`, `values()`, `entries()`, `assign()`

## 📁 Project Structure

```
js-forge/
├── main.py           # Entry point & CLI
├── lexer.py          # Tokenizer (lexer)
├── parser.py         # Recursive descent parser (AST builder)
├── interpreter.py    # Execution engine & built-ins
├── tests/            # Test cases
│   ├── test1.js      # Odd/Even Checker
│   ├── test2.js      # Triangle Pattern
│   ├── test3.js      # Armstrong Number
│   ├── test4.js      # Array Reverse
│   └── test5.js      # String Palindrome
└── README.md         # This file
```

## 🛠️ How to Run

### Requirements
- Python 3.8+
- No external dependencies required!

### Run a JavaScript file
```bash
python main.py tests/test1.js
```

### Execute code directly
```bash
python main.py -c "console.log('Hello, World!');"
```

### Interactive REPL
```bash
python main.py -i
```

### Run all test cases
```bash
python main.py --test
```

## 🏆 Hackathon Test Cases

| Test Case | Status | Points |
|-----------|--------|--------|
| TC-1: Odd/Even Checker | ✅ Pass | 20 |
| TC-2: Triangle Pattern | ✅ Pass | 20 |
| TC-3: Armstrong Number | ✅ Pass | 20 |
| TC-4: Array Reverse | ✅ Pass | 20 |
| TC-5: String Palindrome | ✅ Pass | 20 |
| **TOTAL** | **100/100** | **100** |

## 🎯 Innovation Highlights

1. **Pure Python Implementation**: Zero dependencies, works on any system with Python 3.8+
2. **Full Lexer + Parser**: Custom recursive descent parser with proper operator precedence
3. **JS Semantics**: Accurate type coercion, truthiness, `===` vs `==`, `undefined` vs `null`
4. **Prototype Chain**: Object and Array prototype method resolution
5. **REPL Mode**: Interactive environment for testing code snippets
6. **Error Handling**: Line/column accurate error messages with try/catch support
7. **Comprehensive Built-ins**: Extensive Math, Date, Array, String, and Object support

## 📜 License

Built for Thunder Hackathon 2.0. All code is original work.

---
**Author**: [Your Name]  
**GitHub**: [Your GitHub Repo Link]  
**X Post**: [Your X Post Link]
