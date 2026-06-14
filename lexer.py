"""
JS Forge - JavaScript Interpreter Lexer
Thunder Hackathon 2.0 Submission
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    UNDEFINED = auto()

    # Identifiers
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    CONST = auto()
    VAR = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    DO = auto()
    FUNCTION = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    NEW = auto()
    THIS = auto()
    TYPEOF = auto()
    VOID = auto()
    CLASS = auto()
    EXTENDS = auto()
    SUPER = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT_KW = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    THROW = auto()
    IMPORT = auto()
    EXPORT = auto()
    ASYNC = auto()
    AWAIT = auto()
    YIELD = auto()
    IN = auto()
    INSTANCEOF = auto()
    OF = auto()
    DELETE = auto()

    # Operators
    ASSIGN = auto()           # =
    PLUS = auto()             # +
    MINUS = auto()            # -
    MULTIPLY = auto()         # *
    DIVIDE = auto()           # /
    MODULO = auto()           # %
    POWER = auto()            # **
    INCREMENT = auto()        # ++
    DECREMENT = auto()        # --

    EQ = auto()               # ==
    STRICT_EQ = auto()        # ===
    NOT_EQ = auto()           # !=
    STRICT_NOT_EQ = auto()    # !==
    LT = auto()               # <
    GT = auto()               # >
    LTE = auto()              # <=
    GTE = auto()              # >=

    LOGICAL_AND = auto()      # &&
    LOGICAL_OR = auto()       # ||
    LOGICAL_NOT = auto()      # !

    BITWISE_AND = auto()      # &
    BITWISE_OR = auto()       # |
    BITWISE_XOR = auto()      # ^
    BITWISE_NOT = auto()      # ~
    LSHIFT = auto()           # <<
    RSHIFT = auto()           # >>
    URSHIFT = auto()          # >>>

    PLUS_ASSIGN = auto()      # +=
    MINUS_ASSIGN = auto()     # -=
    MUL_ASSIGN = auto()       # *=
    DIV_ASSIGN = auto()       # /=
    MOD_ASSIGN = auto()       # %=
    AND_ASSIGN = auto()       # &=
    OR_ASSIGN = auto()        # |=
    XOR_ASSIGN = auto()       # ^=

    # Symbols
    SEMICOLON = auto()        # ;
    COMMA = auto()            # ,
    DOT = auto()              # .
    COLON = auto()            # :
    QUESTION = auto()         # ?

    LPAREN = auto()           # (
    RPAREN = auto()           # )
    LBRACE = auto()           # {
    RBRACE = auto()           # }
    LBRACKET = auto()         # [
    RBRACKET = auto()         # ]

    ARROW = auto()            # =>
    SPREAD = auto()           # ...

    TEMPLATE_LITERAL = auto() # `...`
    TEMPLATE_EXPR = auto()    # ${

    EOF = auto()
    NEWLINE = auto()

@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int
    raw: str = ""

class LexerError(Exception):
    pass

class Lexer:
    KEYWORDS = {
        'let': TokenType.LET,
        'const': TokenType.CONST,
        'var': TokenType.VAR,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'for': TokenType.FOR,
        'while': TokenType.WHILE,
        'do': TokenType.DO,
        'function': TokenType.FUNCTION,
        'return': TokenType.RETURN,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'null': TokenType.NULL,
        'undefined': TokenType.UNDEFINED,
        'new': TokenType.NEW,
        'this': TokenType.THIS,
        'typeof': TokenType.TYPEOF,
        'void': TokenType.VOID,
        'class': TokenType.CLASS,
        'extends': TokenType.EXTENDS,
        'super': TokenType.SUPER,
        'switch': TokenType.SWITCH,
        'case': TokenType.CASE,
        'default': TokenType.DEFAULT_KW,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'try': TokenType.TRY,
        'catch': TokenType.CATCH,
        'finally': TokenType.FINALLY,
        'throw': TokenType.THROW,
        'import': TokenType.IMPORT,
        'export': TokenType.EXPORT,
        'async': TokenType.ASYNC,
        'await': TokenType.AWAIT,
        'yield': TokenType.YIELD,
        'in': TokenType.IN,
        'instanceof': TokenType.INSTANCEOF,
        'of': TokenType.OF,
        'delete': TokenType.DELETE,
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_column = 1

    def error(self, msg: str):
        raise LexerError(f"[{self.line}:{self.column}] {msg}")

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def peek(self, offset: int = 0) -> str:
        pos = self.current + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def add_token(self, type: TokenType, value=None):
        raw = self.source[self.start:self.current]
        self.tokens.append(Token(type, value, self.line, self.start_column, raw))

    def skip_whitespace(self):
        while True:
            c = self.peek()
            if c in ' \t\r':
                self.advance()
            elif c == '\n':
                self.advance()
            elif c == '/' and self.peek(1) == '/':
                # Single-line comment
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            elif c == '/' and self.peek(1) == '*':
                # Multi-line comment
                self.advance()  # /
                self.advance()  # *
                while not (self.peek() == '*' and self.peek(1) == '/') and not self.is_at_end():
                    self.advance()
                if not self.is_at_end():
                    self.advance()  # *
                    self.advance()  # /
            else:
                break

    def read_string(self, quote: str):
        # Opening quote already consumed by scan_token
        value = ""
        while self.peek() != quote and not self.is_at_end():
            if self.peek() == '\\':
                self.advance()
                escape = self.advance()
                if escape == 'n': value += '\n'
                elif escape == 't': value += '\t'
                elif escape == 'r': value += '\r'
                elif escape == '\\': value += '\\'
                elif escape == '"': value += '"'
                elif escape == "'": value += "'"
                elif escape == 'b': value += '\b'
                elif escape == 'f': value += '\f'
                elif escape == 'v': value += '\v'
                elif escape == '0': value += '\0'
                elif escape == 'x':
                    # Hex escape
                    hex_chars = self.advance() + self.advance()
                    value += chr(int(hex_chars, 16))
                elif escape == 'u':
                    # Unicode escape
                    if self.peek() == '{':
                        self.advance()
                        hex_chars = ""
                        while self.peek() != '}':
                            hex_chars += self.advance()
                        self.advance()  # }
                        value += chr(int(hex_chars, 16))
                    else:
                        hex_chars = "".join(self.advance() for _ in range(4))
                        value += chr(int(hex_chars, 16))
                else:
                    value += escape
            else:
                value += self.advance()

        if self.is_at_end():
            self.error("Unterminated string")

        self.advance()  # consume closing quote
        self.add_token(TokenType.STRING, value)

    def read_template_literal(self):
        # Opening ` already consumed by scan_token
        value = ""
        while self.peek() != '`' and not self.is_at_end():
            if self.peek() == '$' and self.peek(1) == '{':
                # Template expression
                if value:
                    self.add_token(TokenType.TEMPLATE_LITERAL, value)
                    value = ""
                self.advance()  # $
                self.advance()  # {
                self.add_token(TokenType.TEMPLATE_EXPR, "${")
                # Parse expression inside - we handle this at parser level
                # For now, just return, parser will handle nested expressions
                return
            elif self.peek() == '\\':
                self.advance()
                escape = self.advance()
                if escape == 'n': value += '\n'
                elif escape == 't': value += '\t'
                else: value += escape
            else:
                value += self.advance()

        if self.is_at_end():
            self.error("Unterminated template literal")

        self.advance()  # consume `
        if value:
            self.add_token(TokenType.TEMPLATE_LITERAL, value)

    def read_number(self):
        while self.peek().isdigit():
            self.advance()

        if self.peek() == '.' and self.peek(1).isdigit():
            self.advance()  # .
            while self.peek().isdigit():
                self.advance()

        if self.peek() in 'eE':
            self.advance()
            if self.peek() in '+-':
                self.advance()
            while self.peek().isdigit():
                self.advance()

        num_str = self.source[self.start:self.current]
        if '.' in num_str or 'e' in num_str.lower():
            self.add_token(TokenType.NUMBER, float(num_str))
        else:
            self.add_token(TokenType.NUMBER, int(num_str))

    def read_identifier(self):
        while self.peek().isalnum() or self.peek() in '_$':
            self.advance()

        text = self.source[self.start:self.current]
        token_type = self.KEYWORDS.get(text, TokenType.IDENTIFIER)

        if token_type == TokenType.TRUE:
            self.add_token(TokenType.BOOLEAN, True)
        elif token_type == TokenType.FALSE:
            self.add_token(TokenType.BOOLEAN, False)
        elif token_type == TokenType.NULL:
            self.add_token(TokenType.NULL, None)
        elif token_type == TokenType.UNDEFINED:
            self.add_token(TokenType.UNDEFINED, None)
        else:
            self.add_token(token_type, text)

    def scan_token(self):
        self.start = self.current
        self.start_column = self.column

        c = self.advance()

        if c == '(': self.add_token(TokenType.LPAREN)
        elif c == ')': self.add_token(TokenType.RPAREN)
        elif c == '{': self.add_token(TokenType.LBRACE)
        elif c == '}': self.add_token(TokenType.RBRACE)
        elif c == '[': self.add_token(TokenType.LBRACKET)
        elif c == ']': self.add_token(TokenType.RBRACKET)
        elif c == ';': self.add_token(TokenType.SEMICOLON)
        elif c == ',': self.add_token(TokenType.COMMA)
        elif c == ':': self.add_token(TokenType.COLON)
        elif c == '?': self.add_token(TokenType.QUESTION)

        elif c == '+':
            if self.match('='): self.add_token(TokenType.PLUS_ASSIGN)
            elif self.match('+'): self.add_token(TokenType.INCREMENT)
            else: self.add_token(TokenType.PLUS)

        elif c == '-':
            if self.match('='): self.add_token(TokenType.MINUS_ASSIGN)
            elif self.match('-'): self.add_token(TokenType.DECREMENT)
            else: self.add_token(TokenType.MINUS)

        elif c == '*':
            if self.match('='): self.add_token(TokenType.MUL_ASSIGN)
            elif self.match('*'): self.add_token(TokenType.POWER)
            else: self.add_token(TokenType.MULTIPLY)

        elif c == '/':
            if self.match('='): self.add_token(TokenType.DIV_ASSIGN)
            else: self.add_token(TokenType.DIVIDE)

        elif c == '%':
            if self.match('='): self.add_token(TokenType.MOD_ASSIGN)
            else: self.add_token(TokenType.MODULO)

        elif c == '=':
            if self.match('='):
                if self.match('='): self.add_token(TokenType.STRICT_EQ)
                else: self.add_token(TokenType.EQ)
            elif self.match('>'): self.add_token(TokenType.ARROW)
            else: self.add_token(TokenType.ASSIGN)

        elif c == '!':
            if self.match('='):
                if self.match('='): self.add_token(TokenType.STRICT_NOT_EQ)
                else: self.add_token(TokenType.NOT_EQ)
            else: self.add_token(TokenType.LOGICAL_NOT)

        elif c == '<':
            if self.match('='): self.add_token(TokenType.LTE)
            elif self.match('<'):
                if self.match('='): self.add_token(TokenType.AND_ASSIGN)  # <<=
                else: self.add_token(TokenType.LSHIFT)
            else: self.add_token(TokenType.LT)

        elif c == '>':
            if self.match('='): self.add_token(TokenType.GTE)
            elif self.match('>'):
                if self.match('='): self.add_token(TokenType.OR_ASSIGN)  # >>=
                elif self.match('>'):
                    if self.match('='): self.add_token(TokenType.XOR_ASSIGN)  # >>>=
                    else: self.add_token(TokenType.URSHIFT)
                else: self.add_token(TokenType.RSHIFT)
            else: self.add_token(TokenType.GT)

        elif c == '&':
            if self.match('&'): self.add_token(TokenType.LOGICAL_AND)
            elif self.match('='): self.add_token(TokenType.AND_ASSIGN)
            else: self.add_token(TokenType.BITWISE_AND)

        elif c == '|':
            if self.match('|'): self.add_token(TokenType.LOGICAL_OR)
            elif self.match('='): self.add_token(TokenType.OR_ASSIGN)
            else: self.add_token(TokenType.BITWISE_OR)

        elif c == '^':
            if self.match('='): self.add_token(TokenType.XOR_ASSIGN)
            else: self.add_token(TokenType.BITWISE_XOR)

        elif c == '~': self.add_token(TokenType.BITWISE_NOT)

        elif c == '.':
            if self.peek().isdigit():
                # Decimal number starting with .
                while self.peek().isdigit():
                    self.advance()
                num_str = self.source[self.start:self.current]
                self.add_token(TokenType.NUMBER, float(num_str))
            elif self.match('.') and self.match('.'):
                self.add_token(TokenType.SPREAD)
            else:
                self.add_token(TokenType.DOT)

        elif c == '"' or c == "'":
            self.read_string(c)

        elif c == '`':
            self.read_template_literal()

        elif c.isdigit():
            self.read_number()

        elif c.isalpha() or c in '_$':
            self.read_identifier()

        elif c == '\n':
            pass  # skip newlines (handled in whitespace)

        else:
            self.error(f"Unexpected character: '{c}'")

    def tokenize(self) -> List[Token]:
        while not self.is_at_end():
            self.skip_whitespace()
            if not self.is_at_end():
                self.scan_token()

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column, "EOF"))
        return self.tokens
