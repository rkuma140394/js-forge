"""
JS Forge - JavaScript Interpreter Parser
Thunder Hackathon 2.0 Submission
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from lexer import Token, TokenType, LexerError

# ==================== AST NODES ====================

@dataclass
class ASTNode:
    line: int = 0
    column: int = 0

@dataclass
class Program(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ExpressionStatement(ASTNode):
    expression: ASTNode = None

@dataclass
class BlockStatement(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class VariableDeclaration(ASTNode):
    kind: str = ""  # 'let', 'const', 'var'
    declarations: List[ASTNode] = field(default_factory=list)

@dataclass
class VariableDeclarator(ASTNode):
    id: ASTNode = None
    init: Optional[ASTNode] = None

@dataclass
class FunctionDeclaration(ASTNode):
    id: Optional[ASTNode] = None
    params: List[ASTNode] = field(default_factory=list)
    body: ASTNode = None
    async_: bool = False

@dataclass
class FunctionExpression(ASTNode):
    id: Optional[ASTNode] = None
    params: List[ASTNode] = field(default_factory=list)
    body: ASTNode = None
    async_: bool = False

@dataclass
class ArrowFunctionExpression(ASTNode):
    params: List[ASTNode] = field(default_factory=list)
    body: ASTNode = None
    async_: bool = False
    expression: bool = False  # true if body is expression, not block

@dataclass
class IfStatement(ASTNode):
    test: ASTNode = None
    consequent: ASTNode = None
    alternate: Optional[ASTNode] = None

@dataclass
class ForStatement(ASTNode):
    init: Optional[ASTNode] = None
    test: Optional[ASTNode] = None
    update: Optional[ASTNode] = None
    body: ASTNode = None

@dataclass
class ForOfStatement(ASTNode):
    left: ASTNode = None
    right: ASTNode = None
    body: ASTNode = None

@dataclass
class ForInStatement(ASTNode):
    left: ASTNode = None
    right: ASTNode = None
    body: ASTNode = None

@dataclass
class WhileStatement(ASTNode):
    test: ASTNode = None
    body: ASTNode = None

@dataclass
class DoWhileStatement(ASTNode):
    body: ASTNode = None
    test: ASTNode = None

@dataclass
class ReturnStatement(ASTNode):
    argument: Optional[ASTNode] = None

@dataclass
class BreakStatement(ASTNode):
    label: Optional[ASTNode] = None

@dataclass
class ContinueStatement(ASTNode):
    label: Optional[ASTNode] = None

@dataclass
class SwitchStatement(ASTNode):
    discriminant: ASTNode = None
    cases: List[ASTNode] = field(default_factory=list)

@dataclass
class SwitchCase(ASTNode):
    test: Optional[ASTNode] = None
    consequent: List[ASTNode] = field(default_factory=list)

@dataclass
class TryStatement(ASTNode):
    block: ASTNode = None
    handler: Optional[ASTNode] = None
    finalizer: Optional[ASTNode] = None

@dataclass
class CatchClause(ASTNode):
    param: Optional[ASTNode] = None
    body: ASTNode = None

@dataclass
class ThrowStatement(ASTNode):
    argument: ASTNode = None

@dataclass
class ClassDeclaration(ASTNode):
    id: ASTNode = None
    superClass: Optional[ASTNode] = None
    body: ASTNode = None

@dataclass
class ClassBody(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class MethodDefinition(ASTNode):
    key: ASTNode = None
    value: ASTNode = None
    kind: str = "method"  # 'method', 'get', 'set', 'constructor'
    static: bool = False

@dataclass
class BinaryExpression(ASTNode):
    operator: str = ""
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class UnaryExpression(ASTNode):
    operator: str = ""
    argument: ASTNode = None
    prefix: bool = True

@dataclass
class UpdateExpression(ASTNode):
    operator: str = ""
    argument: ASTNode = None
    prefix: bool = True

@dataclass
class AssignmentExpression(ASTNode):
    operator: str = ""
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class LogicalExpression(ASTNode):
    operator: str = ""
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class ConditionalExpression(ASTNode):
    test: ASTNode = None
    consequent: ASTNode = None
    alternate: ASTNode = None

@dataclass
class CallExpression(ASTNode):
    callee: ASTNode = None
    arguments: List[ASTNode] = field(default_factory=list)

@dataclass
class MemberExpression(ASTNode):
    object: ASTNode = None
    property: ASTNode = None
    computed: bool = False  # true for obj[prop], false for obj.prop

@dataclass
class ArrayExpression(ASTNode):
    elements: List[Optional[ASTNode]] = field(default_factory=list)

@dataclass
class ObjectExpression(ASTNode):
    properties: List[ASTNode] = field(default_factory=list)

@dataclass
class Property(ASTNode):
    key: ASTNode = None
    value: ASTNode = None
    kind: str = "init"  # 'init', 'get', 'set'
    method: bool = False
    shorthand: bool = False
    computed: bool = False

@dataclass
class SpreadElement(ASTNode):
    argument: ASTNode = None

@dataclass
class SequenceExpression(ASTNode):
    expressions: List[ASTNode] = field(default_factory=list)

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class Literal(ASTNode):
    value: Any = None
    raw: str = ""

@dataclass
class TemplateLiteral(ASTNode):
    quasis: List[ASTNode] = field(default_factory=list)
    expressions: List[ASTNode] = field(default_factory=list)

@dataclass
class TemplateElement(ASTNode):
    value: Dict[str, str] = field(default_factory=dict)
    tail: bool = False

@dataclass
class ThisExpression(ASTNode):
    pass

@dataclass
class NewExpression(ASTNode):
    callee: ASTNode = None
    arguments: List[ASTNode] = field(default_factory=list)

@dataclass
class Super(ASTNode):
    pass

@dataclass
class EmptyStatement(ASTNode):
    pass

@dataclass
class LabeledStatement(ASTNode):
    label: ASTNode = None
    body: ASTNode = None

@dataclass
class AwaitExpression(ASTNode):
    argument: ASTNode = None

@dataclass
class YieldExpression(ASTNode):
    argument: Optional[ASTNode] = None
    delegate: bool = False


# ==================== PARSER ====================

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def error(self, msg: str):
        token = self.peek()
        raise ParseError(f"[{token.line}:{token.column}] {msg}")

    def peek(self, offset: int = 0) -> Token:
        pos = self.current + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == type

    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def consume(self, type: TokenType, msg: str) -> Token:
        if self.check(type):
            return self.advance()
        self.error(msg)

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            if self.peek().type in {
                TokenType.FUNCTION, TokenType.LET, TokenType.CONST, TokenType.VAR,
                TokenType.FOR, TokenType.IF, TokenType.WHILE, TokenType.RETURN,
                TokenType.CLASS, TokenType.TRY, TokenType.THROW, TokenType.SWITCH
            }:
                return
            self.advance()

    # ============== PARSING ENTRY ==============

    def parse(self) -> Program:
        body = []
        while not self.is_at_end():
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        return Program(body=body, line=1, column=1)

    # ============== STATEMENTS ==============

    def statement(self) -> Optional[ASTNode]:
        if self.match(TokenType.SEMICOLON):
            return EmptyStatement(line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.LBRACE):
            return self.block_statement()

        if self.match(TokenType.IF):
            return self.if_statement()

        if self.match(TokenType.FOR):
            return self.for_statement()

        if self.match(TokenType.WHILE):
            return self.while_statement()

        if self.match(TokenType.DO):
            return self.do_while_statement()

        if self.match(TokenType.RETURN):
            return self.return_statement()

        if self.match(TokenType.BREAK):
            return self.break_statement()

        if self.match(TokenType.CONTINUE):
            return self.continue_statement()

        if self.match(TokenType.TRY):
            return self.try_statement()

        if self.match(TokenType.THROW):
            return self.throw_statement()

        if self.match(TokenType.SWITCH):
            return self.switch_statement()

        if self.match(TokenType.FUNCTION):
            return self.function_declaration()

        if self.match(TokenType.CLASS):
            return self.class_declaration()

        if self.match(TokenType.LET, TokenType.CONST, TokenType.VAR):
            return self.variable_declaration(self.previous().type)

        return self.expression_statement()

    def block_statement(self) -> BlockStatement:
        body = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return BlockStatement(body=body, line=self.previous().line, column=self.previous().column)

    def if_statement(self) -> IfStatement:
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        test = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after if condition")
        consequent = self.statement()
        alternate = None
        if self.match(TokenType.ELSE):
            alternate = self.statement()
        return IfStatement(test=test, consequent=consequent, alternate=alternate,
                          line=self.previous().line, column=self.previous().column)

    def for_statement(self) -> ASTNode:
        self.consume(TokenType.LPAREN, "Expected '(' after 'for'")

        # Check for for-of / for-in
        if self.check(TokenType.LET) or self.check(TokenType.CONST) or self.check(TokenType.VAR):
            # Look ahead to see if it's for-of or for-in
            save = self.current
            self.advance()  # let/const/var
            self.advance()  # identifier
            if self.check(TokenType.IN) or self.check(TokenType.OF):
                kind = self.tokens[save].type
                self.current = save
                return self.for_in_of_statement(kind)
            self.current = save
        elif self.check(TokenType.IDENTIFIER):
            save = self.current
            self.advance()  # identifier
            if self.check(TokenType.IN) or self.check(TokenType.OF):
                self.current = save
                return self.for_in_of_statement(None)
            self.current = save

        # Regular for loop
        init = None
        if self.match(TokenType.SEMICOLON):
            init = None
        elif self.match(TokenType.LET, TokenType.CONST, TokenType.VAR):
            init = self.variable_declaration(self.previous().type)
        else:
            init = self.expression()
            self.consume(TokenType.SEMICOLON, "Expected ';' after for loop init")

        test = None
        if not self.check(TokenType.SEMICOLON):
            test = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for loop condition")

        update = None
        if not self.check(TokenType.RPAREN):
            update = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after for loop clauses")

        body = self.statement()
        return ForStatement(init=init, test=test, update=update, body=body,
                           line=self.previous().line, column=self.previous().column)

    def for_in_of_statement(self, kind) -> ASTNode:
        if kind:
            self.advance()  # let/const/var

        left = self.identifier()
        if kind:
            left = VariableDeclaration(kind=self.token_type_to_kind(kind), 
                                       declarations=[VariableDeclarator(id=left)],
                                       line=left.line, column=left.column)

        is_of = self.match(TokenType.OF)
        if not is_of:
            self.consume(TokenType.IN, "Expected 'in' or 'of' in for loop")

        right = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after for loop clauses")
        body = self.statement()

        if is_of:
            return ForOfStatement(left=left, right=right, body=body,
                                 line=self.previous().line, column=self.previous().column)
        return ForInStatement(left=left, right=right, body=body,
                             line=self.previous().line, column=self.previous().column)

    def token_type_to_kind(self, type: TokenType) -> str:
        if type == TokenType.LET: return "let"
        if type == TokenType.CONST: return "const"
        if type == TokenType.VAR: return "var"
        return "var"

    def while_statement(self) -> WhileStatement:
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        test = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after while condition")
        body = self.statement()
        return WhileStatement(test=test, body=body,
                             line=self.previous().line, column=self.previous().column)

    def do_while_statement(self) -> DoWhileStatement:
        body = self.statement()
        self.consume(TokenType.WHILE, "Expected 'while' after do block")
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        test = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after while condition")
        self.consume(TokenType.SEMICOLON, "Expected ';' after do-while")
        return DoWhileStatement(body=body, test=test,
                               line=self.previous().line, column=self.previous().column)

    def return_statement(self) -> ReturnStatement:
        argument = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE):
            argument = self.expression()
        self.consume_semicolon()
        return ReturnStatement(argument=argument,
                              line=self.previous().line, column=self.previous().column)

    def break_statement(self) -> BreakStatement:
        label = None
        if self.check(TokenType.IDENTIFIER):
            label = self.identifier()
        self.consume_semicolon()
        return BreakStatement(label=label,
                             line=self.previous().line, column=self.previous().column)

    def continue_statement(self) -> ContinueStatement:
        label = None
        if self.check(TokenType.IDENTIFIER):
            label = self.identifier()
        self.consume_semicolon()
        return ContinueStatement(label=label,
                                line=self.previous().line, column=self.previous().column)

    def try_statement(self) -> TryStatement:
        self.consume(TokenType.LBRACE, "Expected '{' before try block")
        block = self.block_statement()
        handler = None
        if self.match(TokenType.CATCH):
            param = None
            if self.match(TokenType.LPAREN):
                param = self.identifier()
                self.consume(TokenType.RPAREN, "Expected ')' after catch parameter")
            self.consume(TokenType.LBRACE, "Expected '{' before catch block")
            body = self.block_statement()
            handler = CatchClause(param=param, body=body,
                                 line=self.previous().line, column=self.previous().column)

        finalizer = None
        if self.match(TokenType.FINALLY):
            self.consume(TokenType.LBRACE, "Expected '{' before finally block")
            finalizer = self.block_statement()

        return TryStatement(block=block, handler=handler, finalizer=finalizer,
                           line=self.previous().line, column=self.previous().column)

    def throw_statement(self) -> ThrowStatement:
        argument = self.expression()
        self.consume_semicolon()
        return ThrowStatement(argument=argument,
                             line=self.previous().line, column=self.previous().column)

    def switch_statement(self) -> SwitchStatement:
        self.consume(TokenType.LPAREN, "Expected '(' after 'switch'")
        discriminant = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after switch discriminant")
        self.consume(TokenType.LBRACE, "Expected '{' before switch cases")

        cases = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.match(TokenType.CASE):
                test = self.expression()
                self.consume(TokenType.COLON, "Expected ':' after case test")
                consequent = []
                while not self.check(TokenType.CASE) and not self.check(TokenType.DEFAULT_KW) and not self.check(TokenType.RBRACE):
                    stmt = self.statement()
                    if stmt:
                        consequent.append(stmt)
                cases.append(SwitchCase(test=test, consequent=consequent,
                                       line=self.previous().line, column=self.previous().column))
            elif self.match(TokenType.DEFAULT_KW):
                self.consume(TokenType.COLON, "Expected ':' after default")
                consequent = []
                while not self.check(TokenType.CASE) and not self.check(TokenType.DEFAULT_KW) and not self.check(TokenType.RBRACE):
                    stmt = self.statement()
                    if stmt:
                        consequent.append(stmt)
                cases.append(SwitchCase(test=None, consequent=consequent,
                                       line=self.previous().line, column=self.previous().column))
            else:
                self.error("Expected 'case' or 'default' in switch")

        self.consume(TokenType.RBRACE, "Expected '}' after switch cases")
        return SwitchStatement(discriminant=discriminant, cases=cases,
                              line=self.previous().line, column=self.previous().column)

    def function_declaration(self) -> FunctionDeclaration:
        id = None
        if self.check(TokenType.IDENTIFIER):
            id = self.identifier()

        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')' after function parameters")
        self.consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self.block_statement()
        return FunctionDeclaration(id=id, params=params, body=body,
                                  line=self.previous().line, column=self.previous().column)

    def class_declaration(self) -> ClassDeclaration:
        id = self.identifier()
        superClass = None
        if self.match(TokenType.EXTENDS):
            superClass = self.identifier()

        self.consume(TokenType.LBRACE, "Expected '{' before class body")
        body_nodes = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            static = self.match(TokenType.IDENTIFIER) and self.previous().value == 'static'
            if static and not self.check(TokenType.IDENTIFIER):
                self.error("Expected identifier after 'static'")

            if not static:
                # Put back if we consumed an identifier that wasn't 'static'
                pass  # Actually, we need to handle this better

            key = self.identifier() if self.check(TokenType.IDENTIFIER) else self.identifier()
            # Simplified class parsing - just methods
            if self.match(TokenType.LPAREN):
                params = self.parameter_list()
                self.consume(TokenType.RPAREN, "Expected ')' after method parameters")
                self.consume(TokenType.LBRACE, "Expected '{' before method body")
                method_body = self.block_statement()
                kind = "constructor" if key.name == "constructor" else "method"
                method = FunctionExpression(params=params, body=method_body,
                                           line=self.previous().line, column=self.previous().column)
                body_nodes.append(MethodDefinition(key=key, value=method, kind=kind, static=static,
                                                  line=self.previous().line, column=self.previous().column))

        self.consume(TokenType.RBRACE, "Expected '}' after class body")
        return ClassDeclaration(id=id, superClass=superClass, 
                               body=ClassBody(body=body_nodes),
                               line=self.previous().line, column=self.previous().column)

    def parameter_list(self) -> List[ASTNode]:
        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                if self.match(TokenType.SPREAD):
                    params.append(SpreadElement(argument=self.identifier(),
                                               line=self.previous().line, column=self.previous().column))
                    break
                else:
                    params.append(self.identifier())
                if not self.match(TokenType.COMMA):
                    break
        return params

    def variable_declaration(self, kind_type: TokenType) -> VariableDeclaration:
        kind = self.token_type_to_kind(kind_type)
        declarations = []
        while True:
            id = self.identifier()
            init = None
            if self.match(TokenType.ASSIGN):
                init = self.expression()
            declarations.append(VariableDeclarator(id=id, init=init,
                                                  line=id.line, column=id.column))
            if not self.match(TokenType.COMMA):
                break
        self.consume_semicolon()
        return VariableDeclaration(kind=kind, declarations=declarations,
                                  line=self.previous().line, column=self.previous().column)

    def expression_statement(self) -> ExpressionStatement:
        expr = self.expression()
        self.consume_semicolon()
        return ExpressionStatement(expression=expr,
                                line=self.previous().line, column=self.previous().column)

    def consume_semicolon(self):
        if not self.is_at_end() and not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            self.consume(TokenType.SEMICOLON, "Expected ';' after statement")

    # ============== EXPRESSIONS ==============

    def expression(self) -> ASTNode:
        return self.sequence_expression()

    def sequence_expression(self) -> ASTNode:
        expr = self.assignment_expression()
        if self.match(TokenType.COMMA):
            expressions = [expr]
            while True:
                expressions.append(self.assignment_expression())
                if not self.match(TokenType.COMMA):
                    break
            return SequenceExpression(expressions=expressions,
                                     line=self.previous().line, column=self.previous().column)
        return expr

    def assignment_expression(self) -> ASTNode:
        expr = self.conditional_expression()

        if self.match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                      TokenType.MUL_ASSIGN, TokenType.DIV_ASSIGN, TokenType.MOD_ASSIGN,
                      TokenType.AND_ASSIGN, TokenType.OR_ASSIGN, TokenType.XOR_ASSIGN):
            operator = self.previous().raw
            right = self.assignment_expression()
            return AssignmentExpression(operator=operator, left=expr, right=right,
                                       line=self.previous().line, column=self.previous().column)

        return expr

    def conditional_expression(self) -> ASTNode:
        expr = self.logical_or_expression()
        if self.match(TokenType.QUESTION):
            consequent = self.expression()
            self.consume(TokenType.COLON, "Expected ':' in ternary expression")
            alternate = self.conditional_expression()
            return ConditionalExpression(test=expr, consequent=consequent, alternate=alternate,
                                        line=self.previous().line, column=self.previous().column)
        return expr

    def logical_or_expression(self) -> ASTNode:
        expr = self.logical_and_expression()
        while self.match(TokenType.LOGICAL_OR):
            operator = self.previous().raw
            right = self.logical_and_expression()
            expr = LogicalExpression(operator=operator, left=expr, right=right,
                                    line=self.previous().line, column=self.previous().column)
        return expr

    def logical_and_expression(self) -> ASTNode:
        expr = self.bitwise_or_expression()
        while self.match(TokenType.LOGICAL_AND):
            operator = self.previous().raw
            right = self.bitwise_or_expression()
            expr = LogicalExpression(operator=operator, left=expr, right=right,
                                    line=self.previous().line, column=self.previous().column)
        return expr

    def bitwise_or_expression(self) -> ASTNode:
        expr = self.bitwise_xor_expression()
        while self.match(TokenType.BITWISE_OR):
            operator = self.previous().raw
            right = self.bitwise_xor_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def bitwise_xor_expression(self) -> ASTNode:
        expr = self.bitwise_and_expression()
        while self.match(TokenType.BITWISE_XOR):
            operator = self.previous().raw
            right = self.bitwise_and_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def bitwise_and_expression(self) -> ASTNode:
        expr = self.equality_expression()
        while self.match(TokenType.BITWISE_AND):
            operator = self.previous().raw
            right = self.equality_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def equality_expression(self) -> ASTNode:
        expr = self.relational_expression()
        while self.match(TokenType.EQ, TokenType.NOT_EQ, TokenType.STRICT_EQ, TokenType.STRICT_NOT_EQ):
            operator = self.previous().raw
            right = self.relational_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def relational_expression(self) -> ASTNode:
        expr = self.shift_expression()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE, TokenType.IN, TokenType.INSTANCEOF):
            operator = self.previous().raw
            right = self.shift_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def shift_expression(self) -> ASTNode:
        expr = self.additive_expression()
        while self.match(TokenType.LSHIFT, TokenType.RSHIFT, TokenType.URSHIFT):
            operator = self.previous().raw
            right = self.additive_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def additive_expression(self) -> ASTNode:
        expr = self.multiplicative_expression()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().raw
            right = self.multiplicative_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def multiplicative_expression(self) -> ASTNode:
        expr = self.exponentiation_expression()
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous().raw
            right = self.exponentiation_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def exponentiation_expression(self) -> ASTNode:
        expr = self.unary_expression()
        if self.match(TokenType.POWER):
            operator = self.previous().raw
            right = self.exponentiation_expression()
            expr = BinaryExpression(operator=operator, left=expr, right=right,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def unary_expression(self) -> ASTNode:
        if self.match(TokenType.LOGICAL_NOT, TokenType.MINUS, TokenType.PLUS,
                      TokenType.BITWISE_NOT, TokenType.TYPEOF, TokenType.VOID, TokenType.DELETE):
            operator = self.previous().raw
            argument = self.unary_expression()
            return UnaryExpression(operator=operator, argument=argument, prefix=True,
                                line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.previous().raw
            argument = self.unary_expression()
            return UpdateExpression(operator=operator, argument=argument, prefix=True,
                                   line=self.previous().line, column=self.previous().column)

        return self.update_expression()

    def update_expression(self) -> ASTNode:
        expr = self.call_expression()
        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.previous().raw
            return UpdateExpression(operator=operator, argument=expr, prefix=False,
                                   line=self.previous().line, column=self.previous().column)
        return expr

    def call_expression(self) -> ASTNode:
        expr = self.member_expression()
        while True:
            if self.match(TokenType.LPAREN):
                args = self.argument_list()
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpression(callee=expr, arguments=args,
                                   line=self.previous().line, column=self.previous().column)
            elif self.match(TokenType.DOT):
                property = self.identifier()
                expr = MemberExpression(object=expr, property=property, computed=False,
                                       line=self.previous().line, column=self.previous().column)
            elif self.match(TokenType.LBRACKET):
                property = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after property access")
                expr = MemberExpression(object=expr, property=property, computed=True,
                                       line=self.previous().line, column=self.previous().column)
            elif self.match(TokenType.TEMPLATE_LITERAL, TokenType.TEMPLATE_EXPR):
                # Template literal call (tagged template)
                pass
            else:
                break
        return expr

    def argument_list(self) -> List[ASTNode]:
        args = []
        if not self.check(TokenType.RPAREN):
            while True:
                if self.match(TokenType.SPREAD):
                    args.append(SpreadElement(argument=self.assignment_expression(),
                                             line=self.previous().line, column=self.previous().column))
                else:
                    args.append(self.assignment_expression())
                if not self.match(TokenType.COMMA):
                    break
        return args

    def member_expression(self) -> ASTNode:
        expr = self.primary_expression()
        while True:
            if self.match(TokenType.DOT):
                property = self.identifier()
                expr = MemberExpression(object=expr, property=property, computed=False,
                                       line=self.previous().line, column=self.previous().column)
            elif self.match(TokenType.LBRACKET):
                property = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after property access")
                expr = MemberExpression(object=expr, property=property, computed=True,
                                       line=self.previous().line, column=self.previous().column)
            else:
                break
        return expr

    def primary_expression(self) -> ASTNode:
        if self.match(TokenType.NUMBER):
            return Literal(value=self.previous().value, raw=self.previous().raw,
                          line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.STRING):
            return Literal(value=self.previous().value, raw=self.previous().raw,
                          line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.BOOLEAN):
            return Literal(value=self.previous().value, raw=str(self.previous().value).lower(),
                          line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.NULL):
            return Literal(value=None, raw="null",
                          line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.UNDEFINED):
            return Literal(value=None, raw="undefined",
                          line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.IDENTIFIER):
            # Check for arrow function: x => expr
            if self.check(TokenType.ARROW):
                params = [Identifier(name=self.previous().value,
                                    line=self.previous().line, column=self.previous().column)]
                return self.parse_arrow_function(params)
            return Identifier(name=self.previous().value,
                             line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.THIS):
            return ThisExpression(line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.SUPER):
            return Super(line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.LPAREN):
            # Check for arrow function: () => expr or (x, y) => expr
            if self.check(TokenType.RPAREN) and self.peek(1).type == TokenType.ARROW:
                self.advance()  # consume )
                return self.parse_arrow_function([])

            # Try to parse as arrow function params: (x, y) => expr
            save_pos = self.current
            params = []
            try:
                while True:
                    if self.check(TokenType.IDENTIFIER):
                        params.append(self.identifier())
                    else:
                        break
                    if not self.match(TokenType.COMMA):
                        break

                if self.match(TokenType.RPAREN) and self.check(TokenType.ARROW):
                    return self.parse_arrow_function(params)
            except ParseError:
                pass

            # Not an arrow function, restore and parse as regular expression
            self.current = save_pos
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        if self.match(TokenType.LBRACKET):
            return self.array_expression()

        if self.match(TokenType.LBRACE):
            return self.object_expression()

        if self.match(TokenType.FUNCTION):
            return self.function_expression()

        if self.match(TokenType.NEW):
            return self.new_expression()

        if self.match(TokenType.ASYNC):
            if self.match(TokenType.FUNCTION):
                return self.function_expression(async_=True)
            self.error("Unexpected 'async'")

        if self.match(TokenType.AWAIT):
            return AwaitExpression(argument=self.unary_expression(),
                                  line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.YIELD):
            argument = None
            delegate = False
            if self.match(TokenType.MULTIPLY):
                delegate = True
            if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE):
                argument = self.assignment_expression()
            return YieldExpression(argument=argument, delegate=delegate,
                                  line=self.previous().line, column=self.previous().column)

        if self.match(TokenType.TEMPLATE_LITERAL):
            return Literal(value=self.previous().value, raw=f"`{self.previous().value}`",
                          line=self.previous().line, column=self.previous().column)

        self.error(f"Unexpected token: {self.peek().raw}")

    def array_expression(self) -> ArrayExpression:
        elements = []
        if not self.check(TokenType.RBRACKET):
            while True:
                if self.match(TokenType.COMMA):
                    elements.append(None)
                elif self.match(TokenType.SPREAD):
                    elements.append(SpreadElement(argument=self.assignment_expression(),
                                                 line=self.previous().line, column=self.previous().column))
                else:
                    elements.append(self.assignment_expression())
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RBRACKET, "Expected ']' after array elements")
        return ArrayExpression(elements=elements,
                              line=self.previous().line, column=self.previous().column)

    def object_expression(self) -> ObjectExpression:
        properties = []
        if not self.check(TokenType.RBRACE):
            while True:
                if self.match(TokenType.SPREAD):
                    properties.append(SpreadElement(argument=self.assignment_expression(),
                                                   line=self.previous().line, column=self.previous().column))
                else:
                    key, computed = self.property_key()
                    if self.match(TokenType.COLON):
                        value = self.assignment_expression()
                        properties.append(Property(key=key, value=value, kind="init", computed=computed,
                                                  line=self.previous().line, column=self.previous().column))
                    elif self.match(TokenType.LPAREN):
                        # Method shorthand
                        params = self.parameter_list()
                        self.consume(TokenType.RPAREN, "Expected ')' after method parameters")
                        self.consume(TokenType.LBRACE, "Expected '{' before method body")
                        body = self.block_statement()
                        func = FunctionExpression(params=params, body=body,
                                                 line=self.previous().line, column=self.previous().column)
                        properties.append(Property(key=key, value=func, kind="init", method=True, computed=computed,
                                                  line=self.previous().line, column=self.previous().column))
                    elif isinstance(key, Identifier) and self.check(TokenType.COMMA) or self.check(TokenType.RBRACE):
                        # Shorthand property {a} -> {a: a}
                        properties.append(Property(key=key, value=key, kind="init", shorthand=True,
                                                  line=self.previous().line, column=self.previous().column))
                    else:
                        self.error("Expected ':' or '(' in object property")
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RBRACE, "Expected '}' after object properties")
        return ObjectExpression(properties=properties,
                               line=self.previous().line, column=self.previous().column)

    def property_key(self):
        computed = False
        if self.match(TokenType.LBRACKET):
            key = self.expression()
            self.consume(TokenType.RBRACKET, "Expected ']' after computed property key")
            computed = True
        elif self.match(TokenType.STRING):
            key = Literal(value=self.previous().value, raw=self.previous().raw,
                         line=self.previous().line, column=self.previous().column)
        elif self.match(TokenType.NUMBER):
            key = Literal(value=self.previous().value, raw=self.previous().raw,
                         line=self.previous().line, column=self.previous().column)
        elif self.match(TokenType.IDENTIFIER):
            key = Identifier(name=self.previous().value,
                            line=self.previous().line, column=self.previous().column)
        else:
            self.error("Expected property key")
        return key, computed

    def function_expression(self, async_: bool = False) -> FunctionExpression:
        id = None
        if self.check(TokenType.IDENTIFIER):
            id = self.identifier()
        self.consume(TokenType.LPAREN, "Expected '(' after function")
        params = self.parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')' after function parameters")
        self.consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self.block_statement()
        return FunctionExpression(id=id, params=params, body=body, async_=async_,
                                 line=self.previous().line, column=self.previous().column)

    def new_expression(self) -> NewExpression:
        callee = self.member_expression()
        args = []
        if self.match(TokenType.LPAREN):
            args = self.argument_list()
            self.consume(TokenType.RPAREN, "Expected ')' after new arguments")
        return NewExpression(callee=callee, arguments=args,
                            line=self.previous().line, column=self.previous().column)

    def identifier(self) -> Identifier:
        if not self.check(TokenType.IDENTIFIER):
            self.error(f"Expected identifier, got {self.peek().type.name}")
        token = self.advance()
        return Identifier(name=token.value,
                         line=token.line, column=token.column)

    def parse_arrow_function(self, params: List[ASTNode]) -> ArrowFunctionExpression:
        self.consume(TokenType.ARROW, "Expected '=>'")
        if self.match(TokenType.LBRACE):
            body = self.block_statement()
            return ArrowFunctionExpression(params=params, body=body, expression=False,
                                          line=self.previous().line, column=self.previous().column)
        else:
            body = self.assignment_expression()
            return ArrowFunctionExpression(params=params, body=body, expression=True,
                                          line=self.previous().line, column=self.previous().column)
