# Visual Code Trace Example

## Example: `let x = 5 + 3; console.log(x);`

This document shows EXACTLY what happens at every stage.

---

## Stage 1: Lexer (Character by Character)

```
Position: 0  → char: 'l'
  → reads "let" → checks keywords → Token(LET, 'let')

Position: 3  → char: ' '  
  → whitespace → skip

Position: 4  → char: 'x'
  → reads "x" → not a keyword → Token(IDENTIFIER, 'x')

Position: 5  → char: ' '
  → whitespace → skip

Position: 6  → char: '='
  → checks next: ' ' (not '=') → Token(ASSIGN)

Position: 7  → char: ' '
  → whitespace → skip

Position: 8  → char: '5'
  → reads "5" → Token(NUMBER, 5)

Position: 9  → char: ' '
  → whitespace → skip

Position: 10 → char: '+'
  → checks next: ' ' (not '+' or '=') → Token(PLUS)

Position: 11 → char: ' '
  → whitespace → skip

Position: 12 → char: '3'
  → reads "3" → Token(NUMBER, 3)

Position: 13 → char: ';'
  → Token(SEMICOLON)

Position: 14 → char: ' '
  → whitespace → skip

Position: 15 → char: 'c'
  → reads "console" → checks keywords → not found → Token(IDENTIFIER, 'console')

Position: 22 → char: '.'
  → Token(DOT)

Position: 23 → char: 'l'
  → reads "log" → checks keywords → not found → Token(IDENTIFIER, 'log')

Position: 26 → char: '('
  → Token(LPAREN)

Position: 27 → char: 'x'
  → Token(IDENTIFIER, 'x')

Position: 28 → char: ')'
  → Token(RPAREN)

Position: 29 → char: ';'
  → Token(SEMICOLON)

Position: 30 → END
  → Token(EOF)
```

**Result: 14 tokens**

---

## Stage 2: Parser (Token by Token)

```
Current token: LET
  → statement() sees LET
  → calls variable_declaration()
    → consumes LET
    → creates VariableDeclarator
      → id = identifier() → consumes IDENTIFIER("x") → Identifier("x")
      → sees ASSIGN, consumes it
      → init = assignment_expression()
        → calls conditional_expression()
          → calls logical_or_expression()
            → ... descends through precedence levels ...
              → calls primary_expression()
                → sees NUMBER(5) → Literal(5)
        → sees PLUS, consumes it
        → right side: primary_expression() → Literal(3)
        → creates BinaryExpression('+', Literal(5), Literal(3))
    → semicolon consumed
  → returns VariableDeclaration

Current token: IDENTIFIER("console")
  → statement() doesn't recognize it as keyword
  → calls expression_statement()
    → expression() → assignment_expression()
      → conditional_expression()
        → ... descends ...
          → primary_expression() sees IDENTIFIER("console")
            → returns Identifier("console")
          → sees DOT, consumes it
            → property = identifier() → Identifier("log")
            → creates MemberExpression(console, log, computed=False)
          → sees LPAREN
            → this is a call!
            → creates CallExpression(MemberExpression, [args])
            → args = argument_list()
              → expression() → Identifier("x")
            → consumes RPAREN
    → semicolon consumed
  → returns ExpressionStatement(CallExpression)
```

**Result: AST with 2 statements**

---

## Stage 3: Interpreter (Node by Node)

### Statement 1: VariableDeclaration
```
eval_VariableDeclaration(node):
  for each declarator:
    init = evaluate(declarator.init)
      → eval_BinaryExpression(BinaryExpression('+', Literal(5), Literal(3))):
        left = eval_Literal(Literal(5)) → JSValue('number', 5)
        right = eval_Literal(Literal(3)) → JSValue('number', 3)
        operator '+' → js_add(5, 3)
          → neither is string → JSValue('number', 8)
        return JSValue('number', 8)

    env.define('x', JSValue('number', 8), 'let')
      → self.variables['x'] = {'value': 8, 'kind': 'let'}

  return JSUndefined
```

### Statement 2: ExpressionStatement
```
eval_ExpressionStatement(node):
  evaluate(node.expression)
    → eval_CallExpression(CallExpression):
      callee = evaluate(MemberExpression):
        object = evaluate(Identifier("console")):
          → env.get('console') → JSObject (built-in)
        property = Identifier("log") → 'log'
        → obj.get('log') → JSNativeFunction('log', console_log)

      arguments = [evaluate(Identifier("x"))]:
        → env.get('x') → JSValue('number', 8)

      this_value = object = JSObject(console)

      js_call(JSNativeFunction('log'), [JSValue('number', 8)], JSObject(console)):
        → native_func([8], console)
        → " ".join(arg.to_string() for arg in [8])
        → "8"
        → print("8")

      return JSUndefined

  return JSUndefined
```

**Result: Output "8"**

---

## Memory State During Execution

### After Statement 1:
```
Environment (global):
  x → {'value': JSValue('number', 8), 'kind': 'let'}
  console → {'value': JSObject(console), 'kind': 'var'}
  Math → {'value': JSObject(Math), 'kind': 'var'}
  Date → {'value': JSNativeFunction(Date), 'kind': 'var'}
  Array → {'value': JSNativeFunction(Array), 'kind': 'var'}
  ...
```

### During Statement 2:
```
Call stack:
  [TOP] eval_CallExpression(console.log)
        → js_call(native_func, [8], console)
        → native_func executes
  [BOTTOM] eval_Program
```

---

## Key Insight: How `console.log` Works

```
console.log(x)
  │
  ├─ console → JSObject (from _setup_globals)
  │   └─ properties: {'log': JSNativeFunction}
  │
  ├─ .log → MemberExpression looks up 'log' in console
  │   └─ returns JSNativeFunction('log', console_log)
  │
  ├─ (x) → CallExpression evaluates argument
  │   └─ x → env.get('x') → JSValue('number', 8)
  │
  └─ js_call() → native_func([8], console)
     └─ console_log([8], console):
        └─ print(" ".join(["8"])) → print("8")
```

---

## How Array Methods Work (Prototype Chain)

```javascript
let arr = [1, 2, 3];
arr.push(4);
```

```
1. env.get('arr') → JSArray
   elements: [1, 2, 3]
   prototype: array_proto (JSObject with push, pop, map, etc.)

2. arr.push → eval_MemberExpression:
   arr.get('push'):
     → 'push' not in elements (not a number)
     → 'push' not in arr.properties
     → arr.prototype.get('push') → JSNativeFunction('push', array_push)

   Returns JSNativeFunction('push')

3. arr.push(4) → eval_CallExpression:
   js_call(push_func, [JSValue('number', 4)], arr):
     → array_push([4], arr):
        → arr.elements.append(4)
        → arr.elements = [1, 2, 3, 4]
        → arr.properties['length'] = 4
        → return JSValue('number', 4)
```

---

## How Closures Work

```javascript
function makeAdder(x) {
    return function(y) {
        return x + y;
    };
}
let add5 = makeAdder(5);
console.log(add5(3));
```

```
1. eval_FunctionDeclaration('makeAdder'):
   → JSFunction('makeAdder', ['x'], body, closure=global_env)
   → env.define('makeAdder', func, 'var')

2. eval_VariableDeclaration('add5'):
   → init = eval_CallExpression(makeAdder(5)):
     → js_call(makeAdder_func, [5], undefined):
       → env = Environment(global_env)  // closure captures global
       → env.define('x', 5, 'var')
       → evaluate(return statement):
         → return JSFunction(null, ['y'], body, closure=env)
         → this closure captures env (which has x=5)
   → env.define('add5', returned_func, 'let')

3. eval_CallExpression(add5(3)):
   → js_call(add5_func, [3], undefined):
     → env = Environment(add5_func.closure)  // closure has x=5!
     → env.define('y', 3, 'var')
     → evaluate body:
       → x + y → env.get('x') → 5 (from closure!)
               → env.get('y') → 3
               → 5 + 3 = 8
     → return 8
```

**The magic:** The inner function's `closure` points to the environment where it was created, which still has `x=5` even after `makeAdder` returns.

---

## How `this` Works

```javascript
let obj = {
    name: "Alice",
    greet: function() {
        console.log("Hello " + this.name);
    }
};
obj.greet();
```

```
1. obj.greet → MemberExpression:
   object = obj (JSObject)
   property = 'greet' → JSFunction

2. obj.greet() → CallExpression:
   this_value = obj (the object before the dot)

3. js_call(greet_func, [], obj):
   → this_binding = obj
   → evaluate body:
     → this.name → obj.get('name') → "Alice"
     → "Hello " + "Alice" → "Hello Alice"
```

**Arrow functions are different:**
```javascript
let obj = {
    name: "Alice",
    greet: () => {
        console.log("Hello " + this.name);
    }
};
```
Arrow functions capture `this` from where they were defined (bound_this), not from the call site.

---

## Summary Table

| Stage | Input | Output | Key Operation |
|-------|-------|--------|---------------|
| Lexer | Raw text | Token list | Pattern matching on characters |
| Parser | Token list | AST tree | Recursive descent by precedence |
| Interpreter | AST tree | Side effects | Tree traversal with environment |

---

## Call Stack Visualization

```javascript
function foo() {
    let a = 1;
    bar(a);
}
function bar(x) {
    console.log(x);
}
foo();
```

```
Execution flow:

[Global Env]
  foo → JSFunction
  bar → JSFunction

Call foo():
  [Env 1: foo's scope, parent=Global]
    a → 1

  Call bar(a):
    [Env 2: bar's scope, parent=Global]
      x → 1 (copied from a)

    console.log(x):
      [Env 3: console.log's scope, parent=Global]
        (native, no JS env)

    Return from bar → Env 2 destroyed

  Return from foo → Env 1 destroyed

[Back to Global Env only]
```
