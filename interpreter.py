"""
JS Forge - JavaScript Interpreter Execution Engine
Thunder Hackathon 2.0 Submission
"""

import math
import random
import time
import sys
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from parser import (
    ASTNode, Program, ExpressionStatement, BlockStatement, VariableDeclaration,
    VariableDeclarator, FunctionDeclaration, FunctionExpression, ArrowFunctionExpression,
    IfStatement, ForStatement, ForOfStatement, ForInStatement, WhileStatement, DoWhileStatement,
    ReturnStatement, BreakStatement, ContinueStatement, SwitchStatement, SwitchCase,
    TryStatement, CatchClause, ThrowStatement, ClassDeclaration, ClassBody, MethodDefinition,
    BinaryExpression, UnaryExpression, UpdateExpression, AssignmentExpression,
    LogicalExpression, ConditionalExpression, CallExpression, MemberExpression,
    ArrayExpression, ObjectExpression, Property, SpreadElement, SequenceExpression,
    Identifier, Literal, TemplateLiteral, TemplateElement, ThisExpression, NewExpression,
    Super, EmptyStatement, AwaitExpression, YieldExpression
)
from lexer import TokenType

# ==================== JS VALUE SYSTEM ====================

class JSValue:
    def __init__(self, type_: str, value: Any, prototype: Optional['JSObject'] = None):
        self.type = type_
        self.value = value
        self.prototype = prototype
        self.properties: Dict[str, Any] = {}
        self.callable = False
        self.constructor = False

    def __repr__(self):
        if self.type == 'string':
            return f'"{self.value}"'
        if self.type == 'undefined':
            return 'undefined'
        if self.type == 'null':
            return 'null'
        if self.type == 'function':
            return f'[Function]'
        if self.type == 'object':
            return f'[Object]'
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, JSValue):
            return self.value == other.value and self.type == other.type
        return self.value == other

    def __hash__(self):
        if self.type == 'object':
            return id(self)
        return hash(self.value)

    def is_truthy(self) -> bool:
        if self.type == 'boolean':
            return self.value
        if self.type == 'number':
            return self.value != 0 and not math.isnan(self.value)
        if self.type == 'string':
            return len(self.value) > 0
        if self.type == 'undefined' or self.type == 'null':
            return False
        return True

    def to_string(self) -> str:
        if self.type == 'undefined': return 'undefined'
        if self.type == 'null': return 'null'
        if self.type == 'boolean': return 'true' if self.value else 'false'
        if self.type == 'number':
            if math.isnan(self.value): return 'NaN'
            if math.isinf(self.value): return 'Infinity' if self.value > 0 else '-Infinity'
            if isinstance(self.value, float) and self.value == int(self.value):
                return str(int(self.value))
            return str(self.value)
        if self.type == 'string': return self.value
        if self.type == 'function': return '[Function]'
        if self.type == 'object': return '[object Object]'
        return str(self.value)

    def to_number(self) -> float:
        if self.type == 'number': return self.value
        if self.type == 'undefined': return float('nan')
        if self.type == 'null': return 0
        if self.type == 'boolean': return 1 if self.value else 0
        if self.type == 'string':
            s = self.value.strip()
            if s == '':
                return 0
            try:
                return float(s)
            except ValueError:
                return float('nan')
        return float('nan')

class JSObject(JSValue):
    def __init__(self, properties: Dict[str, Any] = None, prototype: Optional['JSObject'] = None):
        super().__init__('object', None, prototype)
        self.properties = properties or {}

    def get(self, key: str) -> JSValue:
        if key in self.properties:
            return self.properties[key]
        if self.prototype and hasattr(self.prototype, 'get'):
            return self.prototype.get(key)
        return JSUndefined

    def set(self, key: str, value: JSValue):
        self.properties[key] = value

    def has(self, key: str) -> bool:
        return key in self.properties

class JSArray(JSValue):
    def __init__(self, elements: List[JSValue] = None):
        super().__init__('object', None)
        self.elements = elements or []
        self.properties = {'length': JSValue('number', len(self.elements))}

    def get(self, key: str) -> JSValue:
        if key == 'length':
            return JSValue('number', len(self.elements))
        if key.isdigit():
            idx = int(key)
            if 0 <= idx < len(self.elements):
                return self.elements[idx]
            return JSUndefined
        if key in self.properties:
            return self.properties[key]
        # Check prototype chain for array methods
        if self.prototype and hasattr(self.prototype, 'get'):
            return self.prototype.get(key)
        return JSUndefined

    def set(self, key: str, value: JSValue):
        if key.isdigit():
            idx = int(key)
            while len(self.elements) <= idx:
                self.elements.append(JSUndefined)
            self.elements[idx] = value
            self.properties['length'] = JSValue('number', len(self.elements))
        else:
            self.properties[key] = value

    def has(self, key: str) -> bool:
        if key.isdigit():
            return int(key) < len(self.elements)
        return key in self.properties

class JSFunction(JSValue):
    def __init__(self, name: str, params: List[str], body: ASTNode, closure: 'Environment',
                 arrow: bool = False, async_: bool = False, generator: bool = False,
                 bound_this: Optional[JSValue] = None):
        super().__init__('function', name)
        self.params = params
        self.body = body
        self.closure = closure
        self.arrow = arrow
        self.async_ = async_
        self.generator = generator
        self.bound_this = bound_this
        self.callable = True
        self.constructor = not arrow and not async_ and not generator
        self.properties = {}
        self.prototype = None

class JSNativeFunction(JSValue):
    def __init__(self, name: str, func: Callable, constructor: bool = False):
        super().__init__('function', name)
        self.native_func = func
        self.callable = True
        self.constructor = constructor
        self.properties = {}

# Special values
JSUndefined = JSValue('undefined', None)
JSNull = JSValue('null', None)
JSTrue = JSValue('boolean', True)
JSFalse = JSValue('boolean', False)
JSNaN = JSValue('number', float('nan'))
JSInfinity = JSValue('number', float('inf'))
JSNegInfinity = JSValue('number', float('-inf'))

# ==================== ENVIRONMENT ====================

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.variables: Dict[str, Dict[str, Any]] = {}
        self.parent = parent

    def define(self, name: str, value: JSValue, kind: str = 'var'):
        self.variables[name] = {'value': value, 'kind': kind}

    def get(self, name: str) -> JSValue:
        if name in self.variables:
            return self.variables[name]['value']
        if self.parent:
            return self.parent.get(name)
        return JSUndefined

    def set(self, name: str, value: JSValue) -> JSValue:
        if name in self.variables:
            if self.variables[name]['kind'] == 'const':
                raise JSError(f"Assignment to constant variable '{name}'")
            self.variables[name]['value'] = value
            return value
        if self.parent:
            return self.parent.set(name, value)
        # Implicit global
        self.variables[name] = {'value': value, 'kind': 'var'}
        return value

    def has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

# ==================== EXCEPTIONS ====================

class JSError(Exception):
    def __init__(self, message: str, value: JSValue = None):
        super().__init__(message)
        self.message = message
        self.value = value

class JSReturn(Exception):
    def __init__(self, value: JSValue):
        self.value = value

class JSBreak(Exception):
    pass

class JSContinue(Exception):
    pass

# ==================== BUILT-INS ====================

def create_console():
    console = JSObject()

    def console_log(args, this):
        output = " ".join(arg.to_string() for arg in args)
        print(output)
        return JSUndefined

    def console_error(args, this):
        output = " ".join(arg.to_string() for arg in args)
        print(output, file=sys.stderr)
        return JSUndefined

    console.properties['log'] = JSNativeFunction('log', console_log)
    console.properties['error'] = JSNativeFunction('error', console_error)
    console.properties['warn'] = JSNativeFunction('warn', console_log)
    console.properties['info'] = JSNativeFunction('info', console_log)
    return console

def create_math():
    math_obj = JSObject()

    math_obj.properties['PI'] = JSValue('number', math.pi)
    math_obj.properties['E'] = JSValue('number', math.e)
    math_obj.properties['LN2'] = JSValue('number', math.log(2))
    math_obj.properties['LN10'] = JSValue('number', math.log(10))
    math_obj.properties['LOG2E'] = JSValue('number', math.log(math.e, 2))
    math_obj.properties['LOG10E'] = JSValue('number', math.log10(math.e))
    math_obj.properties['SQRT1_2'] = JSValue('number', math.sqrt(0.5))
    math_obj.properties['SQRT2'] = JSValue('number', math.sqrt(2))

    def math_floor(args, this):
        if not args: return JSNaN
        return JSValue('number', math.floor(args[0].to_number()))

    def math_ceil(args, this):
        if not args: return JSNaN
        return JSValue('number', math.ceil(args[0].to_number()))

    def math_round(args, this):
        if not args: return JSNaN
        n = args[0].to_number()
        # JS round: round half up
        if n >= 0:
            return JSValue('number', int(n + 0.5))
        else:
            return JSValue('number', int(n - 0.5))

    def math_random(args, this):
        return JSValue('number', random.random())

    def math_max(args, this):
        if not args: return JSValue('number', float('-inf'))
        return JSValue('number', max(a.to_number() for a in args))

    def math_min(args, this):
        if not args: return JSValue('number', float('inf'))
        return JSValue('number', min(a.to_number() for a in args))

    def math_abs(args, this):
        if not args: return JSNaN
        return JSValue('number', abs(args[0].to_number()))

    def math_pow(args, this):
        if len(args) < 2: return JSNaN
        return JSValue('number', math.pow(args[0].to_number(), args[1].to_number()))

    def math_sqrt(args, this):
        if not args: return JSNaN
        return JSValue('number', math.sqrt(args[0].to_number()))

    def math_sin(args, this):
        if not args: return JSNaN
        return JSValue('number', math.sin(args[0].to_number()))

    def math_cos(args, this):
        if not args: return JSNaN
        return JSValue('number', math.cos(args[0].to_number()))

    def math_tan(args, this):
        if not args: return JSNaN
        return JSValue('number', math.tan(args[0].to_number()))

    def math_log(args, this):
        if not args: return JSNaN
        return JSValue('number', math.log(args[0].to_number()))

    def math_exp(args, this):
        if not args: return JSNaN
        return JSValue('number', math.exp(args[0].to_number()))

    def math_trunc(args, this):
        if not args: return JSNaN
        return JSValue('number', math.trunc(args[0].to_number()))

    def math_sign(args, this):
        if not args: return JSNaN
        n = args[0].to_number()
        if n > 0: return JSValue('number', 1)
        if n < 0: return JSValue('number', -1)
        if n == 0: return JSValue('number', 0)
        return JSNaN

    math_obj.properties['floor'] = JSNativeFunction('floor', math_floor)
    math_obj.properties['ceil'] = JSNativeFunction('ceil', math_ceil)
    math_obj.properties['round'] = JSNativeFunction('round', math_round)
    math_obj.properties['random'] = JSNativeFunction('random', math_random)
    math_obj.properties['max'] = JSNativeFunction('max', math_max)
    math_obj.properties['min'] = JSNativeFunction('min', math_min)
    math_obj.properties['abs'] = JSNativeFunction('abs', math_abs)
    math_obj.properties['pow'] = JSNativeFunction('pow', math_pow)
    math_obj.properties['sqrt'] = JSNativeFunction('sqrt', math_sqrt)
    math_obj.properties['sin'] = JSNativeFunction('sin', math_sin)
    math_obj.properties['cos'] = JSNativeFunction('cos', math_cos)
    math_obj.properties['tan'] = JSNativeFunction('tan', math_tan)
    math_obj.properties['log'] = JSNativeFunction('log', math_log)
    math_obj.properties['exp'] = JSNativeFunction('exp', math_exp)
    math_obj.properties['trunc'] = JSNativeFunction('trunc', math_trunc)
    math_obj.properties['sign'] = JSNativeFunction('sign', math_sign)

    return math_obj

def create_date():
    date_proto = JSObject()

    def date_constructor(args, this):
        if isinstance(this, JSValue) and this.type == 'object' and this.constructor:
            timestamp = time.time() * 1000
            if args:
                timestamp = args[0].to_number()
            this.value = timestamp
            return this
        return JSValue('string', time.strftime('%a %b %d %Y %H:%M:%S GMT%z'))

    def date_now(args, this):
        return JSValue('number', time.time() * 1000)

    def date_getTime(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', this.value)
        return JSNaN

    def date_getFullYear(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_year + 1900)
        return JSNaN

    def date_getMonth(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_mon)
        return JSNaN

    def date_getDate(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_mday)
        return JSNaN

    def date_getDay(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_wday)
        return JSNaN

    def date_getHours(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_hour)
        return JSNaN

    def date_getMinutes(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_min)
        return JSNaN

    def date_getSeconds(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('number', time.localtime(this.value / 1000).tm_sec)
        return JSNaN

    def date_toString(args, this):
        if hasattr(this, 'value') and this.value is not None:
            return JSValue('string', time.strftime('%a %b %d %Y %H:%M:%S GMT%z', time.localtime(this.value / 1000)))
        return JSValue('string', 'Invalid Date')

    date_proto.properties['getTime'] = JSNativeFunction('getTime', date_getTime)
    date_proto.properties['getFullYear'] = JSNativeFunction('getFullYear', date_getFullYear)
    date_proto.properties['getMonth'] = JSNativeFunction('getMonth', date_getMonth)
    date_proto.properties['getDate'] = JSNativeFunction('getDate', date_getDate)
    date_proto.properties['getDay'] = JSNativeFunction('getDay', date_getDay)
    date_proto.properties['getHours'] = JSNativeFunction('getHours', date_getHours)
    date_proto.properties['getMinutes'] = JSNativeFunction('getMinutes', date_getMinutes)
    date_proto.properties['getSeconds'] = JSNativeFunction('getSeconds', date_getSeconds)
    date_proto.properties['toString'] = JSNativeFunction('toString', date_toString)

    date_constructor = JSNativeFunction('Date', date_constructor, constructor=True)
    date_constructor.properties['now'] = JSNativeFunction('now', date_now)
    date_constructor.properties['prototype'] = date_proto

    return date_constructor

def create_array_prototype():
    proto = JSObject()

    def array_push(args, this):
        if not isinstance(this, JSArray):
            return JSValue('number', 0)
        for arg in args:
            this.elements.append(arg)
        this.properties['length'] = JSValue('number', len(this.elements))
        return JSValue('number', len(this.elements))

    def array_pop(args, this):
        if not isinstance(this, JSArray):
            return JSUndefined
        if not this.elements:
            return JSUndefined
        val = this.elements.pop()
        this.properties['length'] = JSValue('number', len(this.elements))
        return val

    def array_shift(args, this):
        if not isinstance(this, JSArray):
            return JSUndefined
        if not this.elements:
            return JSUndefined
        val = this.elements.pop(0)
        this.properties['length'] = JSValue('number', len(this.elements))
        return val

    def array_unshift(args, this):
        if not isinstance(this, JSArray):
            return JSValue('number', 0)
        for arg in reversed(args):
            this.elements.insert(0, arg)
        this.properties['length'] = JSValue('number', len(this.elements))
        return JSValue('number', len(this.elements))

    def array_slice(args, this):
        if not isinstance(this, JSArray):
            return JSArray()
        start = int(args[0].to_number()) if args else 0
        end = int(args[1].to_number()) if len(args) > 1 else len(this.elements)
        result = JSArray(this.elements[start:end])
        result.prototype = this.prototype
        return result

    def array_splice(args, this):
        if not isinstance(this, JSArray):
            return JSArray()
        start = int(args[0].to_number()) if args else 0
        delete_count = int(args[1].to_number()) if len(args) > 1 else (len(this.elements) - start)
        removed = this.elements[start:start + delete_count]
        insert = args[2:]
        this.elements = this.elements[:start] + insert + this.elements[start + delete_count:]
        this.properties['length'] = JSValue('number', len(this.elements))
        result = JSArray(removed)
        result.prototype = this.prototype
        return result

    def array_concat(args, this):
        if not isinstance(this, JSArray):
            return JSArray()
        result = JSArray(this.elements[:])
        for arg in args:
            if isinstance(arg, JSArray):
                result.elements.extend(arg.elements)
            else:
                result.elements.append(arg)
        result.properties['length'] = JSValue('number', len(result.elements))
        result.prototype = this.prototype
        return result

    def array_includes(args, this):
        if not isinstance(this, JSArray):
            return JSFalse
        if not args:
            return JSFalse
        search = args[0]
        for el in this.elements:
            if js_strict_equal(el, search).value:
                return JSTrue
        return JSFalse

    def array_indexOf(args, this):
        if not isinstance(this, JSArray):
            return JSValue('number', -1)
        if not args:
            return JSValue('number', -1)
        search = args[0]
        from_index = int(args[1].to_number()) if len(args) > 1 else 0
        for i in range(from_index, len(this.elements)):
            if js_strict_equal(this.elements[i], search).value:
                return JSValue('number', i)
        return JSValue('number', -1)

    def array_sort(args, this):
        if not isinstance(this, JSArray):
            return this
        if args and args[0].callable:
            compare_fn = args[0]
            from functools import cmp_to_key
            def py_compare(a, b):
                result = js_call(compare_fn, [a, b], JSUndefined)
                return int(result.to_number())
            this.elements.sort(key=cmp_to_key(py_compare))
        else:
            this.elements.sort(key=lambda x: x.to_string())
        return this

    def array_reverse(args, this):
        if not isinstance(this, JSArray):
            return this
        this.elements.reverse()
        return this

    def array_join(args, this):
        if not isinstance(this, JSArray):
            return JSValue('string', '')
        sep = args[0].to_string() if args else ','
        return JSValue('string', sep.join(el.to_string() for el in this.elements))

    def array_map(args, this):
        if not isinstance(this, JSArray):
            return JSArray()
        if not args or not args[0].callable:
            return JSArray()
        callback = args[0]
        result = []
        for i, el in enumerate(this.elements):
            val = js_call(callback, [el, JSValue('number', i), this], JSUndefined)
            result.append(val)
        arr = JSArray(result)
        arr.prototype = this.prototype
        return arr

    def array_filter(args, this):
        if not isinstance(this, JSArray):
            return JSArray()
        if not args or not args[0].callable:
            return JSArray()
        callback = args[0]
        result = []
        for i, el in enumerate(this.elements):
            val = js_call(callback, [el, JSValue('number', i), this], JSUndefined)
            if val.is_truthy():
                result.append(el)
        arr = JSArray(result)
        arr.prototype = this.prototype
        return arr

    def array_reduce(args, this):
        if not isinstance(this, JSArray):
            return JSUndefined
        if not args or not args[0].callable:
            return JSUndefined
        callback = args[0]
        arr = this.elements
        if len(args) > 1:
            acc = args[1]
            start_idx = 0
        else:
            if not arr:
                return JSUndefined
            acc = arr[0]
            start_idx = 1
        for i in range(start_idx, len(arr)):
            acc = js_call(callback, [acc, arr[i], JSValue('number', i), this], JSUndefined)
        return acc

    def array_find(args, this):
        if not isinstance(this, JSArray):
            return JSUndefined
        if not args or not args[0].callable:
            return JSUndefined
        callback = args[0]
        for i, el in enumerate(this.elements):
            val = js_call(callback, [el, JSValue('number', i), this], JSUndefined)
            if val.is_truthy():
                return el
        return JSUndefined

    def array_some(args, this):
        if not isinstance(this, JSArray):
            return JSFalse
        if not args or not args[0].callable:
            return JSFalse
        callback = args[0]
        for i, el in enumerate(this.elements):
            val = js_call(callback, [el, JSValue('number', i), this], JSUndefined)
            if val.is_truthy():
                return JSTrue
        return JSFalse

    def array_every(args, this):
        if not isinstance(this, JSArray):
            return JSTrue
        if not args or not args[0].callable:
            return JSTrue
        callback = args[0]
        for i, el in enumerate(this.elements):
            val = js_call(callback, [el, JSValue('number', i), this], JSUndefined)
            if not val.is_truthy():
                return JSFalse
        return JSTrue

    def array_forEach(args, this):
        if not isinstance(this, JSArray):
            return JSUndefined
        if not args or not args[0].callable:
            return JSUndefined
        callback = args[0]
        for i, el in enumerate(this.elements):
            js_call(callback, [el, JSValue('number', i), this], JSUndefined)
        return JSUndefined

    proto.properties['push'] = JSNativeFunction('push', array_push)
    proto.properties['pop'] = JSNativeFunction('pop', array_pop)
    proto.properties['shift'] = JSNativeFunction('shift', array_shift)
    proto.properties['unshift'] = JSNativeFunction('unshift', array_unshift)
    proto.properties['slice'] = JSNativeFunction('slice', array_slice)
    proto.properties['splice'] = JSNativeFunction('splice', array_splice)
    proto.properties['concat'] = JSNativeFunction('concat', array_concat)
    proto.properties['includes'] = JSNativeFunction('includes', array_includes)
    proto.properties['indexOf'] = JSNativeFunction('indexOf', array_indexOf)
    proto.properties['sort'] = JSNativeFunction('sort', array_sort)
    proto.properties['reverse'] = JSNativeFunction('reverse', array_reverse)
    proto.properties['join'] = JSNativeFunction('join', array_join)
    proto.properties['map'] = JSNativeFunction('map', array_map)
    proto.properties['filter'] = JSNativeFunction('filter', array_filter)
    proto.properties['reduce'] = JSNativeFunction('reduce', array_reduce)
    proto.properties['find'] = JSNativeFunction('find', array_find)
    proto.properties['some'] = JSNativeFunction('some', array_some)
    proto.properties['every'] = JSNativeFunction('every', array_every)
    proto.properties['forEach'] = JSNativeFunction('forEach', array_forEach)

    return proto

def create_string_prototype(array_proto=None):
    proto = JSObject()

    def string_replace(args, this):
        s = this.to_string()
        if not args:
            return JSValue('string', s)
        search = args[0].to_string()
        replacement = args[1].to_string() if len(args) > 1 else ''
        return JSValue('string', s.replace(search, replacement, 1))

    def string_replaceAll(args, this):
        s = this.to_string()
        if not args:
            return JSValue('string', s)
        search = args[0].to_string()
        replacement = args[1].to_string() if len(args) > 1 else ''
        return JSValue('string', s.replace(search, replacement))

    def string_substring(args, this):
        s = this.to_string()
        start = int(args[0].to_number()) if args else 0
        end = int(args[1].to_number()) if len(args) > 1 else len(s)
        return JSValue('string', s[start:end])

    def string_slice(args, this):
        s = this.to_string()
        start = int(args[0].to_number()) if args else 0
        end = int(args[1].to_number()) if len(args) > 1 else len(s)
        return JSValue('string', s[start:end])

    def string_split(args, this):
        s = this.to_string()
        sep = args[0].to_string() if args else None
        if sep == "" or sep is None:
            result = JSArray([JSValue('string', c) for c in s])
        else:
            result = JSArray([JSValue('string', x) for x in s.split(sep)])
        if array_proto:
            result.prototype = array_proto
        return result

    def string_trim(args, this):
        return JSValue('string', this.to_string().strip())

    def string_toUpperCase(args, this):
        return JSValue('string', this.to_string().upper())

    def string_toLowerCase(args, this):
        return JSValue('string', this.to_string().lower())

    def string_includes(args, this):
        s = this.to_string()
        search = args[0].to_string() if args else ''
        return JSValue('boolean', search in s)

    def string_startsWith(args, this):
        s = this.to_string()
        search = args[0].to_string() if args else ''
        return JSValue('boolean', s.startswith(search))

    def string_endsWith(args, this):
        s = this.to_string()
        search = args[0].to_string() if args else ''
        return JSValue('boolean', s.endswith(search))

    def string_indexOf(args, this):
        s = this.to_string()
        search = args[0].to_string() if args else ''
        from_idx = int(args[1].to_number()) if len(args) > 1 else 0
        return JSValue('number', s.find(search, from_idx))

    def string_charAt(args, this):
        s = this.to_string()
        idx = int(args[0].to_number()) if args else 0
        if 0 <= idx < len(s):
            return JSValue('string', s[idx])
        return JSValue('string', '')

    def string_charCodeAt(args, this):
        s = this.to_string()
        idx = int(args[0].to_number()) if args else 0
        if 0 <= idx < len(s):
            return JSValue('number', ord(s[idx]))
        return JSNaN

    def string_length(args, this):
        return JSValue('number', len(this.to_string()))

    proto.properties['replace'] = JSNativeFunction('replace', string_replace)
    proto.properties['replaceAll'] = JSNativeFunction('replaceAll', string_replaceAll)
    proto.properties['substring'] = JSNativeFunction('substring', string_substring)
    proto.properties['slice'] = JSNativeFunction('slice', string_slice)
    proto.properties['split'] = JSNativeFunction('split', string_split)
    proto.properties['trim'] = JSNativeFunction('trim', string_trim)
    proto.properties['toUpperCase'] = JSNativeFunction('toUpperCase', string_toUpperCase)
    proto.properties['toLowerCase'] = JSNativeFunction('toLowerCase', string_toLowerCase)
    proto.properties['includes'] = JSNativeFunction('includes', string_includes)
    proto.properties['startsWith'] = JSNativeFunction('startsWith', string_startsWith)
    proto.properties['endsWith'] = JSNativeFunction('endsWith', string_endsWith)
    proto.properties['indexOf'] = JSNativeFunction('indexOf', string_indexOf)
    proto.properties['charAt'] = JSNativeFunction('charAt', string_charAt)
    proto.properties['charCodeAt'] = JSNativeFunction('charCodeAt', string_charCodeAt)
    proto.properties['length'] = JSNativeFunction('length', string_length)

    return proto

def create_object(array_proto=None):
    obj = JSObject()

    def object_keys(args, this):
        if not args:
            return JSArray()
        target = args[0]
        if isinstance(target, JSArray):
            result = JSArray([JSValue('string', str(i)) for i in range(len(target.elements))])
        elif isinstance(target, JSObject):
            result = JSArray([JSValue('string', k) for k in target.properties.keys()])
        else:
            result = JSArray()
        if array_proto:
            result.prototype = array_proto
        return result

    def object_values(args, this):
        if not args:
            return JSArray()
        target = args[0]
        if isinstance(target, JSArray):
            result = JSArray(target.elements[:])
        elif isinstance(target, JSObject):
            result = JSArray(list(target.properties.values()))
        else:
            result = JSArray()
        if array_proto:
            result.prototype = array_proto
        return result

    def object_entries(args, this):
        if not args:
            return JSArray()
        target = args[0]
        result = []
        if isinstance(target, JSArray):
            for i, el in enumerate(target.elements):
                entry = JSArray([JSValue('string', str(i)), el])
                if array_proto:
                    entry.prototype = array_proto
                result.append(entry)
        elif isinstance(target, JSObject):
            for k, v in target.properties.items():
                entry = JSArray([JSValue('string', k), v])
                if array_proto:
                    entry.prototype = array_proto
                result.append(entry)
        arr = JSArray(result)
        if array_proto:
            arr.prototype = array_proto
        return arr

    def object_assign(args, this):
        if not args:
            return JSObject()
        target = args[0]
        if not isinstance(target, JSObject):
            target = JSObject()
        for source in args[1:]:
            if isinstance(source, JSObject):
                for k, v in source.properties.items():
                    target.properties[k] = v
        return target

    obj.properties['keys'] = JSNativeFunction('keys', object_keys)
    obj.properties['values'] = JSNativeFunction('values', object_values)
    obj.properties['entries'] = JSNativeFunction('entries', object_entries)
    obj.properties['assign'] = JSNativeFunction('assign', object_assign)

    return obj

def create_array_constructor(array_proto):
    def array_constructor(args, this):
        if isinstance(this, JSValue) and this.type == 'object' and this.constructor:
            if len(args) == 1 and args[0].type == 'number':
                arr = JSArray([JSUndefined] * int(args[0].to_number()))
                arr.prototype = array_proto
                return arr
            arr = JSArray(args)
            arr.prototype = array_proto
            return arr
        if len(args) == 1 and args[0].type == 'number':
            arr = JSArray([JSUndefined] * int(args[0].to_number()))
            arr.prototype = array_proto
            return arr
        arr = JSArray(args)
        arr.prototype = array_proto
        return arr

    def array_isArray(args, this):
        if not args:
            return JSFalse
        return JSValue('boolean', isinstance(args[0], JSArray))

    constructor = JSNativeFunction('Array', array_constructor, constructor=True)
    constructor.properties['isArray'] = JSNativeFunction('isArray', array_isArray)
    constructor.properties['prototype'] = array_proto
    return constructor

def create_string_constructor(string_proto):
    def string_constructor(args, this):
        if isinstance(this, JSValue) and this.type == 'object' and this.constructor:
            val = args[0].to_string() if args else ''
            this.value = val
            return this
        return JSValue('string', args[0].to_string() if args else '')

    constructor = JSNativeFunction('String', string_constructor, constructor=True)
    constructor.properties['prototype'] = string_proto
    return constructor

# ==================== JS OPERATIONS ====================

def js_strict_equal(a: JSValue, b: JSValue) -> JSValue:
    if a.type != b.type:
        return JSFalse
    if a.type == 'number':
        if math.isnan(a.value) or math.isnan(b.value):
            return JSFalse
        return JSValue('boolean', a.value == b.value)
    return JSValue('boolean', a.value == b.value)

def js_loose_equal(a: JSValue, b: JSValue) -> JSValue:
    if a.type == b.type:
        return js_strict_equal(a, b)
    if a.type == 'null' and b.type == 'undefined':
        return JSTrue
    if a.type == 'undefined' and b.type == 'null':
        return JSTrue
    if a.type == 'number' and b.type == 'string':
        return js_loose_equal(a, JSValue('number', b.to_number()))
    if a.type == 'string' and b.type == 'number':
        return js_loose_equal(JSValue('number', a.to_number()), b)
    if a.type == 'boolean':
        return js_loose_equal(JSValue('number', a.to_number()), b)
    if b.type == 'boolean':
        return js_loose_equal(a, JSValue('number', b.to_number()))
    if a.type == 'string' and b.type == 'boolean':
        return js_loose_equal(JSValue('number', a.to_number()), JSValue('number', b.to_number()))
    if a.type == 'boolean' and b.type == 'string':
        return js_loose_equal(JSValue('number', a.to_number()), JSValue('number', b.to_number()))
    return JSFalse

def js_add(a: JSValue, b: JSValue) -> JSValue:
    if a.type == 'string' or b.type == 'string':
        return JSValue('string', a.to_string() + b.to_string())
    return JSValue('number', a.to_number() + b.to_number())

def js_call(func: JSValue, args: List[JSValue], this: JSValue) -> JSValue:
    if not func.callable:
        raise JSError(f"{func.to_string()} is not a function")

    if isinstance(func, JSNativeFunction):
        return func.native_func(args, this)

    if isinstance(func, JSFunction):
        env = Environment(func.closure)

        # Bind parameters
        for i, param in enumerate(func.params):
            if i < len(args):
                env.define(param, args[i], 'var')
            else:
                env.define(param, JSUndefined, 'var')

        # Bind this
        if func.arrow:
            this_binding = func.bound_this if func.bound_this else this
        else:
            this_binding = this

        interpreter = Interpreter()
        interpreter.env = env
        interpreter.this_value = this_binding

        try:
            result = interpreter.evaluate(func.body)
        except JSReturn as ret:
            return ret.value

        # For arrow functions with expression body, return the expression result
        if func.arrow and not isinstance(func.body, BlockStatement):
            return result

        return JSUndefined

    return JSUndefined

def js_construct(constructor: JSValue, args: List[JSValue]) -> JSValue:
    if not constructor.constructor:
        raise JSError(f"{constructor.to_string()} is not a constructor")

    instance = JSObject()
    instance.constructor = True

    if isinstance(constructor, JSNativeFunction):
        result = constructor.native_func(args, instance)
        if result and result.type != 'undefined':
            return result
        return instance

    if isinstance(constructor, JSFunction):
        env = Environment(constructor.closure)
        for i, param in enumerate(constructor.params):
            if i < len(args):
                env.define(param, args[i], 'var')
            else:
                env.define(param, JSUndefined, 'var')

        interpreter = Interpreter()
        interpreter.env = env
        interpreter.this_value = instance

        try:
            interpreter.evaluate(constructor.body)
        except JSReturn as ret:
            if ret.value.type != 'undefined':
                return ret.value

        return instance

    return instance

# ==================== INTERPRETER ====================

class Interpreter:
    def __init__(self):
        self.env = Environment()
        self.this_value = JSUndefined
        self.output = []
        self.array_proto = create_array_prototype()
        self.string_proto = create_string_prototype(self.array_proto)
        self._setup_globals()

    def _setup_globals(self):
        self.env.define('console', create_console(), 'var')
        self.env.define('Math', create_math(), 'var')
        self.env.define('Date', create_date(), 'var')
        self.env.define('Object', create_object(self.array_proto), 'var')
        self.env.define('Array', create_array_constructor(self.array_proto), 'var')
        self.env.define('String', create_string_constructor(self.string_proto), 'var')

    def run(self, program: Program) -> List[str]:
        self.output = []
        for stmt in program.body:
            self.evaluate(stmt)
        return self.output

    def evaluate(self, node: ASTNode) -> JSValue:
        if node is None:
            return JSUndefined

        method_name = f'eval_{node.__class__.__name__}'
        method = getattr(self, method_name, self._eval_unknown)
        return method(node)

    def _eval_unknown(self, node: ASTNode) -> JSValue:
        raise JSError(f"Unknown node type: {type(node).__name__}")

    # ============== STATEMENT EVALUATORS ==============

    def eval_Program(self, node: Program) -> JSValue:
        result = JSUndefined
        for stmt in node.body:
            result = self.evaluate(stmt)
        return result

    def eval_ExpressionStatement(self, node: ExpressionStatement) -> JSValue:
        return self.evaluate(node.expression)

    def eval_BlockStatement(self, node: BlockStatement) -> JSValue:
        old_env = self.env
        self.env = Environment(old_env)
        result = JSUndefined
        try:
            for stmt in node.body:
                result = self.evaluate(stmt)
        finally:
            self.env = old_env
        return result

    def eval_VariableDeclaration(self, node: VariableDeclaration) -> JSValue:
        for decl in node.declarations:
            init = self.evaluate(decl.init) if decl.init else JSUndefined
            self.env.define(decl.id.name, init, node.kind)
        return JSUndefined

    def eval_FunctionDeclaration(self, node: FunctionDeclaration) -> JSValue:
        name = node.id.name if node.id else None
        params = [p.name for p in node.params]
        func = JSFunction(name, params, node.body, self.env, async_=node.async_)
        if name:
            self.env.define(name, func, 'var')
        return func

    def eval_IfStatement(self, node: IfStatement) -> JSValue:
        test = self.evaluate(node.test)
        if test.is_truthy():
            return self.evaluate(node.consequent)
        elif node.alternate:
            return self.evaluate(node.alternate)
        return JSUndefined

    def eval_ForStatement(self, node: ForStatement) -> JSValue:
        old_env = self.env
        self.env = Environment(old_env)
        result = JSUndefined
        try:
            if node.init:
                self.evaluate(node.init)
            while True:
                if node.test:
                    test = self.evaluate(node.test)
                    if not test.is_truthy():
                        break
                try:
                    result = self.evaluate(node.body)
                except JSBreak:
                    break
                except JSContinue:
                    pass
                if node.update:
                    self.evaluate(node.update)
        finally:
            self.env = old_env
        return result

    def eval_ForOfStatement(self, node: ForOfStatement) -> JSValue:
        iterable = self.evaluate(node.right)
        result = JSUndefined

        items = []
        if isinstance(iterable, JSArray):
            items = iterable.elements
        elif isinstance(iterable, JSValue) and iterable.type == 'string':
            items = [JSValue('string', c) for c in iterable.value]
        elif isinstance(iterable, JSObject) and 'length' in iterable.properties:
            length = int(iterable.properties['length'].to_number())
            for i in range(length):
                items.append(iterable.get(str(i)))

        old_env = self.env
        self.env = Environment(old_env)
        try:
            for item in items:
                if isinstance(node.left, VariableDeclaration):
                    for decl in node.left.declarations:
                        self.env.define(decl.id.name, item, node.left.kind)
                elif isinstance(node.left, Identifier):
                    self.env.set(node.left.name, item)
                try:
                    result = self.evaluate(node.body)
                except JSBreak:
                    break
                except JSContinue:
                    pass
        finally:
            self.env = old_env
        return result

    def eval_ForInStatement(self, node: ForInStatement) -> JSValue:
        obj = self.evaluate(node.right)
        result = JSUndefined

        keys = []
        if isinstance(obj, JSArray):
            keys = [str(i) for i in range(len(obj.elements))]
        elif isinstance(obj, JSObject):
            keys = list(obj.properties.keys())

        old_env = self.env
        self.env = Environment(old_env)
        try:
            for key in keys:
                if isinstance(node.left, VariableDeclaration):
                    for decl in node.left.declarations:
                        self.env.define(decl.id.name, JSValue('string', key), node.left.kind)
                elif isinstance(node.left, Identifier):
                    self.env.set(node.left.name, JSValue('string', key))
                try:
                    result = self.evaluate(node.body)
                except JSBreak:
                    break
                except JSContinue:
                    pass
        finally:
            self.env = old_env
        return result

    def eval_WhileStatement(self, node: WhileStatement) -> JSValue:
        result = JSUndefined
        while True:
            test = self.evaluate(node.test)
            if not test.is_truthy():
                break
            try:
                result = self.evaluate(node.body)
            except JSBreak:
                break
            except JSContinue:
                pass
        return result

    def eval_DoWhileStatement(self, node: DoWhileStatement) -> JSValue:
        result = JSUndefined
        while True:
            try:
                result = self.evaluate(node.body)
            except JSBreak:
                break
            except JSContinue:
                pass
            test = self.evaluate(node.test)
            if not test.is_truthy():
                break
        return result

    def eval_ReturnStatement(self, node: ReturnStatement) -> JSValue:
        value = self.evaluate(node.argument) if node.argument else JSUndefined
        raise JSReturn(value)

    def eval_BreakStatement(self, node: BreakStatement) -> JSValue:
        raise JSBreak()

    def eval_ContinueStatement(self, node: ContinueStatement) -> JSValue:
        raise JSContinue()

    def eval_SwitchStatement(self, node: SwitchStatement) -> JSValue:
        discriminant = self.evaluate(node.discriminant)
        matched = False
        result = JSUndefined

        for case in node.cases:
            if not matched:
                if case.test is None:
                    matched = True
                else:
                    test = self.evaluate(case.test)
                    if js_strict_equal(discriminant, test).value:
                        matched = True

            if matched:
                for stmt in case.consequent:
                    try:
                        result = self.evaluate(stmt)
                    except JSBreak:
                        return result
        return result

    def eval_TryStatement(self, node: TryStatement) -> JSValue:
        result = JSUndefined
        try:
            result = self.evaluate(node.block)
        except JSError as e:
            if node.handler:
                old_env = self.env
                self.env = Environment(old_env)
                try:
                    if node.handler.param:
                        error_val = e.value if e.value else JSValue('string', e.message)
                        self.env.define(node.handler.param.name, error_val, 'var')
                    result = self.evaluate(node.handler.body)
                finally:
                    self.env = old_env
            else:
                raise
        finally:
            if node.finalizer:
                self.evaluate(node.finalizer)
        return result

    def eval_ThrowStatement(self, node: ThrowStatement) -> JSValue:
        value = self.evaluate(node.argument)
        raise JSError("Thrown", value)

    def eval_ClassDeclaration(self, node: ClassDeclaration) -> JSValue:
        class_obj = JSObject()
        if node.superClass:
            super_class = self.env.get(node.superClass.name)
            class_obj.prototype = super_class

        for method in node.body.body:
            func = JSFunction(method.key.name, 
                             [p.name for p in method.value.params],
                             method.value.body, self.env)
            class_obj.properties[method.key.name] = func

        self.env.define(node.id.name, class_obj, 'var')
        return class_obj

    def eval_EmptyStatement(self, node: EmptyStatement) -> JSValue:
        return JSUndefined

    # ============== EXPRESSION EVALUATORS ==============

    def eval_BinaryExpression(self, node: BinaryExpression) -> JSValue:
        left = self.evaluate(node.left)

        if node.operator == '&&':
            if not left.is_truthy():
                return left
            return self.evaluate(node.right)

        if node.operator == '||':
            if left.is_truthy():
                return left
            return self.evaluate(node.right)

        right = self.evaluate(node.right)

        if node.operator == '+':
            return js_add(left, right)
        elif node.operator == '-':
            return JSValue('number', left.to_number() - right.to_number())
        elif node.operator == '*':
            return JSValue('number', left.to_number() * right.to_number())
        elif node.operator == '/':
            if right.to_number() == 0:
                if left.to_number() == 0:
                    return JSNaN
                return JSInfinity if left.to_number() > 0 else JSNegInfinity
            return JSValue('number', left.to_number() / right.to_number())
        elif node.operator == '%':
            return JSValue('number', left.to_number() % right.to_number())
        elif node.operator == '**':
            return JSValue('number', math.pow(left.to_number(), right.to_number()))
        elif node.operator == '===':
            return js_strict_equal(left, right)
        elif node.operator == '==':
            return js_loose_equal(left, right)
        elif node.operator == '!==':
            return JSValue('boolean', not js_strict_equal(left, right).value)
        elif node.operator == '!=':
            return JSValue('boolean', not js_loose_equal(left, right).value)
        elif node.operator == '<':
            return JSValue('boolean', left.to_number() < right.to_number())
        elif node.operator == '>':
            return JSValue('boolean', left.to_number() > right.to_number())
        elif node.operator == '<=':
            return JSValue('boolean', left.to_number() <= right.to_number())
        elif node.operator == '>=':
            return JSValue('boolean', left.to_number() >= right.to_number())
        elif node.operator == '&':
            return JSValue('number', int(left.to_number()) & int(right.to_number()))
        elif node.operator == '|':
            return JSValue('number', int(left.to_number()) | int(right.to_number()))
        elif node.operator == '^':
            return JSValue('number', int(left.to_number()) ^ int(right.to_number()))
        elif node.operator == '<<':
            return JSValue('number', int(left.to_number()) << int(right.to_number()))
        elif node.operator == '>>':
            return JSValue('number', int(left.to_number()) >> int(right.to_number()))
        elif node.operator == '>>>':
            return JSValue('number', int(left.to_number()) & 0xFFFFFFFF >> int(right.to_number()))
        elif node.operator == 'in':
            if isinstance(right, JSObject):
                return JSValue('boolean', right.has(left.to_string()))
            return JSFalse
        elif node.operator == 'instanceof':
            return JSFalse

        raise JSError(f"Unknown binary operator: {node.operator}")

    def eval_UnaryExpression(self, node: UnaryExpression) -> JSValue:
        argument = self.evaluate(node.argument)

        if node.operator == '!':
            return JSValue('boolean', not argument.is_truthy())
        elif node.operator == '-':
            return JSValue('number', -argument.to_number())
        elif node.operator == '+':
            return JSValue('number', argument.to_number())
        elif node.operator == '~':
            return JSValue('number', ~int(argument.to_number()))
        elif node.operator == 'typeof':
            if argument.type == 'undefined':
                return JSValue('string', 'undefined')
            if argument.type == 'null':
                return JSValue('string', 'object')
            if argument.type == 'function':
                return JSValue('string', 'function')
            return JSValue('string', argument.type)
        elif node.operator == 'void':
            return JSUndefined
        elif node.operator == 'delete':
            return JSTrue

        raise JSError(f"Unknown unary operator: {node.operator}")

    def eval_UpdateExpression(self, node: UpdateExpression) -> JSValue:
        if isinstance(node.argument, Identifier):
            current = self.env.get(node.argument.name)
            val = current.to_number()
            if node.operator == '++':
                new_val = val + 1
            elif node.operator == '--':
                new_val = val - 1
            else:
                raise JSError(f"Unknown update operator: {node.operator}")

            new_js_val = JSValue('number', new_val)
            self.env.set(node.argument.name, new_js_val)
            return JSValue('number', new_val if node.prefix else val)

        raise JSError("Invalid update expression")

    def eval_AssignmentExpression(self, node: AssignmentExpression) -> JSValue:
        right = self.evaluate(node.right)

        if isinstance(node.left, Identifier):
            if node.operator == '=':
                self.env.set(node.left.name, right)
                return right
            else:
                current = self.env.get(node.left.name)
                op = node.operator[:-1]
                if op == '+':
                    new_val = js_add(current, right)
                elif op == '-':
                    new_val = JSValue('number', current.to_number() - right.to_number())
                elif op == '*':
                    new_val = JSValue('number', current.to_number() * right.to_number())
                elif op == '/':
                    new_val = JSValue('number', current.to_number() / right.to_number())
                elif op == '%':
                    new_val = JSValue('number', current.to_number() % right.to_number())
                else:
                    raise JSError(f"Unknown assignment operator: {node.operator}")
                self.env.set(node.left.name, new_val)
                return new_val

        elif isinstance(node.left, MemberExpression):
            obj = self.evaluate(node.left.object)
            if node.left.computed:
                prop = self.evaluate(node.left.property).to_string()
            else:
                prop = node.left.property.name

            if node.operator == '=':
                if isinstance(obj, JSArray):
                    obj.set(prop, right)
                elif isinstance(obj, JSObject):
                    obj.set(prop, right)
                return right
            else:
                current = obj.get(prop) if hasattr(obj, 'get') else JSUndefined
                op = node.operator[:-1]
                if op == '+':
                    new_val = js_add(current, right)
                elif op == '-':
                    new_val = JSValue('number', current.to_number() - right.to_number())
                elif op == '*':
                    new_val = JSValue('number', current.to_number() * right.to_number())
                elif op == '/':
                    new_val = JSValue('number', current.to_number() / right.to_number())
                elif op == '%':
                    new_val = JSValue('number', current.to_number() % right.to_number())
                else:
                    raise JSError(f"Unknown assignment operator: {node.operator}")
                if isinstance(obj, JSArray):
                    obj.set(prop, new_val)
                elif isinstance(obj, JSObject):
                    obj.set(prop, new_val)
                return new_val

        raise JSError("Invalid assignment target")

    def eval_LogicalExpression(self, node: LogicalExpression) -> JSValue:
        left = self.evaluate(node.left)
        if node.operator == '&&':
            if not left.is_truthy():
                return left
            return self.evaluate(node.right)
        elif node.operator == '||':
            if left.is_truthy():
                return left
            return self.evaluate(node.right)
        raise JSError(f"Unknown logical operator: {node.operator}")

    def eval_ConditionalExpression(self, node: ConditionalExpression) -> JSValue:
        test = self.evaluate(node.test)
        if test.is_truthy():
            return self.evaluate(node.consequent)
        return self.evaluate(node.alternate)

    def eval_CallExpression(self, node: CallExpression) -> JSValue:
        callee = self.evaluate(node.callee)
        args = []
        for arg in node.arguments:
            if isinstance(arg, SpreadElement):
                spread_val = self.evaluate(arg.argument)
                if isinstance(spread_val, JSArray):
                    args.extend(spread_val.elements)
                else:
                    args.append(spread_val)
            else:
                args.append(self.evaluate(arg))

        this_value = JSUndefined
        if isinstance(node.callee, MemberExpression):
            this_value = self.evaluate(node.callee.object)

        return js_call(callee, args, this_value)

    def eval_MemberExpression(self, node: MemberExpression) -> JSValue:
        obj = self.evaluate(node.object)

        if node.computed:
            prop = self.evaluate(node.property).to_string()
        else:
            prop = node.property.name

        if isinstance(obj, JSArray):
            if prop == 'length':
                return JSValue('number', len(obj.elements))
            return obj.get(prop)
        elif isinstance(obj, JSObject):
            val = obj.get(prop)
            if val.callable and not isinstance(obj, JSNativeFunction):
                return val
            return val
        elif obj.type == 'string':
            if prop == 'length':
                return JSValue('number', len(obj.value))
            val = self.string_proto.get(prop)
            if val.callable:
                def bound_method(args, this):
                    return val.native_func(args, obj)
                return JSNativeFunction(prop, bound_method)
            return val
        elif obj.type == 'number':
            pass

        return JSUndefined

    def eval_ArrayExpression(self, node: ArrayExpression) -> JSValue:
        elements = []
        for el in node.elements:
            if el is None:
                elements.append(JSUndefined)
            elif isinstance(el, SpreadElement):
                spread_val = self.evaluate(el.argument)
                if isinstance(spread_val, JSArray):
                    elements.extend(spread_val.elements)
                else:
                    elements.append(spread_val)
            else:
                elements.append(self.evaluate(el))
        arr = JSArray(elements)
        arr.prototype = self.array_proto
        return arr

    def eval_ObjectExpression(self, node: ObjectExpression) -> JSValue:
        obj = JSObject()
        for prop in node.properties:
            if isinstance(prop, SpreadElement):
                spread_val = self.evaluate(prop.argument)
                if isinstance(spread_val, JSObject):
                    for k, v in spread_val.properties.items():
                        obj.properties[k] = v
            else:
                if prop.computed:
                    key = self.evaluate(prop.key).to_string()
                elif isinstance(prop.key, Identifier):
                    key = prop.key.name
                else:
                    key = str(self.evaluate(prop.key).value)

                if prop.shorthand:
                    value = self.env.get(key)
                else:
                    value = self.evaluate(prop.value)

                obj.properties[key] = value
        return obj

    def eval_SpreadElement(self, node: SpreadElement) -> JSValue:
        return self.evaluate(node.argument)

    def eval_SequenceExpression(self, node: SequenceExpression) -> JSValue:
        result = JSUndefined
        for expr in node.expressions:
            result = self.evaluate(expr)
        return result

    def eval_Identifier(self, node: Identifier) -> JSValue:
        return self.env.get(node.name)

    def eval_Literal(self, node: Literal) -> JSValue:
        if node.raw == 'null':
            return JSNull
        if node.raw == 'undefined':
            return JSUndefined
        if isinstance(node.value, bool):
            return JSValue('boolean', node.value)
        if isinstance(node.value, (int, float)):
            return JSValue('number', node.value)
        if isinstance(node.value, str):
            return JSValue('string', node.value)
        return JSValue('undefined', None)

    def eval_TemplateLiteral(self, node: TemplateLiteral) -> JSValue:
        result = ""
        for i, quasi in enumerate(node.quasis):
            result += quasi.value.get('raw', '')
            if i < len(node.expressions):
                expr_val = self.evaluate(node.expressions[i])
                result += expr_val.to_string()
        return JSValue('string', result)

    def eval_ThisExpression(self, node: ThisExpression) -> JSValue:
        return self.this_value

    def eval_NewExpression(self, node: NewExpression) -> JSValue:
        constructor = self.evaluate(node.callee)
        args = [self.evaluate(arg) for arg in node.arguments]
        return js_construct(constructor, args)

    def eval_FunctionExpression(self, node: FunctionExpression) -> JSValue:
        name = node.id.name if node.id else None
        params = [p.name for p in node.params]
        func = JSFunction(name, params, node.body, self.env, async_=node.async_)
        return func

    def eval_ArrowFunctionExpression(self, node: ArrowFunctionExpression) -> JSValue:
        params = [p.name for p in node.params]
        func = JSFunction(None, params, node.body, self.env, arrow=True, async_=node.async_)
        func.bound_this = self.this_value
        return func

    def eval_Super(self, node: Super) -> JSValue:
        return JSUndefined

    def eval_AwaitExpression(self, node: AwaitExpression) -> JSValue:
        return self.evaluate(node.argument)

    def eval_YieldExpression(self, node: YieldExpression) -> JSValue:
        return self.evaluate(node.argument) if node.argument else JSUndefined
