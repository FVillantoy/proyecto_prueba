import os
import re

# Definimos los tipos de tokens
token_specification = [
    ('NUMBER_FLOAT',   r'\d+\.\d+'),    # Números decimales
    ('NUMBER_INT',     r'\d+'),         # Números enteros
    ('STRING',         r'"[^"]*"'),     # Cadenas de texto
    ('CHAR',           r"'[^']'"),      # Caracteres
    ('ASSIGN',         r'='),           # Asignación
    ('STMT_END',       r';'),           # Fin de una instrucción
    ('ID',             r'[A-Za-z_]\w*'),# Identificadores
    ('OP',             r'[+\-*/]'),     # Operadores aritméticos
    ('OP_REL',         r'[<>!=]=?|=='), # Operadores relacionales
    ('NEWLINE',        r'\n'),          # Líneas nuevas
    ('SKIP',           r'[ \t]+'),      # Espacios y tabulaciones
    ('COMMENT',        r'//.*'),        # Comentarios
    ('BEGIN',          r'BEGIN'),       # Palabras clave
    ('END',            r'END'),
    ('IF',             r'IF'),
    ('THEN',           r'THEN'),
    ('ELSE',           r'ELSE'),
    ('WHILE',          r'WHILE'),
    ('DO',             r'DO'),
    ('FOR',            r'FOR'),
    ('TO',             r'TO'),
    ('VAR',            r'VAR'),
    ('PRINT',          r'PRINT'),
    ('CALL',           r'CALL'),
    ('LPAREN',         r'\('),          # Paréntesis de apertura
    ('RPAREN',         r'\)'),          # Paréntesis de cierre
    ('COMMA',          r',')            # Coma
]

# Compilar la expresión regular
token_re = re.compile('|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification))

def tokenize(contenido):
    line_num = 1
    line_start = 0
    tokens = []
    for mo in token_re.finditer(contenido):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NUMBER_FLOAT':
            value = float(value)
        elif kind == 'NUMBER_INT':
            value = int(value)
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'ID' and value in {'BEGIN', 'END', 'IF', 'THEN', 'ELSE', 'WHILE', 'DO', 'FOR', 'TO', 'VAR', 'PRINT', 'CALL'}:
            kind = value  # Cambiar el tipo de token a la palabra clave encontrada
        tokens.append((kind, value, line_num, column))
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def consume(self, expected_type):
        if self.pos < len(self.tokens):
            token_type, token_value, line, column = self.tokens[self.pos]
            if token_type == expected_type:
                self.pos += 1
                return token_value
        raise SyntaxError(f"Expected {expected_type} at position {self.pos}")

    def parse(self):
        return self.programa()

    def programa(self):
        self.consume('BEGIN')
        instrucciones = self.instrucciones()
        self.consume('END')
        return ('programa', instrucciones)

    def instrucciones(self):
        instrucciones = []
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] not in {'END', 'ELSE'}:
            instrucciones.append(self.instruccion())
        return instrucciones

    def instruccion(self):
        token_type = self.tokens[self.pos][0]
        if token_type == 'VAR':
            return self.declaracion()
        elif token_type == 'ID':
            return self.asignacion()
        elif token_type == 'IF':
            return self.condicional()
        elif token_type == 'WHILE' or token_type == 'FOR':
            return self.bucle()
        elif token_type == 'PRINT':
            return self.impresion()
        elif token_type == 'CALL':
            return self.llamada_funcion()
        else:
            raise SyntaxError(f"Unexpected token {token_type} at position {self.pos}")

    def declaracion(self):
        self.consume('VAR')
        id = self.consume('ID')
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'ASSIGN':
            self.consume('ASSIGN')
            expresion = self.expresion()
            self.consume('STMT_END')
            return ('declaracion', id, expresion)
        else:
            self.consume('STMT_END')
            return ('declaracion', id)

    def asignacion(self):
        id = self.consume('ID')
        self.consume('ASSIGN')
        expresion = self.expresion()
        self.consume('STMT_END')
        return ('asignacion', id, expresion)

    def condicional(self):
        self.consume('IF')
        condicion = self.condicion()
        self.consume('THEN')
        instrucciones_then = self.instrucciones()
        instrucciones_else = []
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'ELSE':
            self.consume('ELSE')
            instrucciones_else = self.instrucciones()
        self.consume('END')
        return ('condicional', condicion, instrucciones_then, instrucciones_else)

    def bucle(self):
        token_type = self.tokens[self.pos][0]
        if token_type == 'WHILE':
            self.consume('WHILE')
            condicion = self.condicion()
            self.consume('DO')
            instrucciones = self.instrucciones()
            self.consume('END')
            return ('bucle_while', condicion, instrucciones)
        elif token_type == 'FOR':
            self.consume('FOR')
            id = self.consume('ID')
            self.consume('ASSIGN')
            inicio = self.expresion()
            self.consume('TO')
            fin = self.expresion()
            self.consume('DO')
            instrucciones = self.instrucciones()
            self.consume('END')
            return ('bucle_for', id, inicio, fin, instrucciones)

    def impresion(self):
        self.consume('PRINT')
        expresion = self.expresion()
        self.consume('STMT_END')
        return ('impresion', expresion)

    def llamada_funcion(self):
        self.consume('CALL')
        id = self.consume('ID')
        self.consume('LPAREN')
        if self.tokens[self.pos][0] != 'RPAREN':
            argumentos = self.argumentos()
        else:
            argumentos = []
        self.consume('RPAREN')
        self.consume('STMT_END')
        return ('llamada_funcion', id, argumentos)

    def argumentos(self):
        argumentos = [self.expresion()]
        while self.tokens[self.pos][0] == 'COMMA':
            self.consume('COMMA')
            argumentos.append(self.expresion())
        return argumentos

    def expresion(self):
        termino = self.termino()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'OP':
            operador = self.consume('OP')
            termino_derecho = self.termino()
            termino = ('expresion', termino, operador, termino_derecho)
        return termino

    def termino(self):
        token_type = self.tokens[self.pos][0]
        if token_type == 'ID':
            return self.consume('ID')
        elif token_type == 'NUMBER_INT':
            return self.consume('NUMBER_INT')
        elif token_type == 'NUMBER_FLOAT':
            return self.consume('NUMBER_FLOAT')
        elif token_type == 'STRING':
            return self.consume('STRING')
        elif token_type == 'CHAR':
            return self.consume('CHAR')
        else:
            raise SyntaxError(f"Unexpected token {token_type} at position {self.pos}")

    def condicion(self):
        expresion_izq = self.expresion()
        operador = self.consume('OP_REL')
        expresion_der = self.expresion()
        return ('condicion', expresion_izq, operador, expresion_der)


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}

    def analyze(self, ast):
        self.visit(ast)

    def visit(self, node):
        if isinstance(node, tuple):
            method_name = 'visit_' + node[0]
            visitor = getattr(self, method_name, self.generic_visit)
            visitor(node)
        else:
            self.generic_visit(node)

    def generic_visit(self, node):
        if isinstance(node, tuple):
            for elem in node:
                if isinstance(elem, tuple):
                    self.visit(elem)
                else:
                    self.generic_visit(elem)
        elif isinstance(node, list):
            for item in node:
                self.visit(item)

    def visit_programa(self, node):
        _, instrucciones = node
        for instruccion in instrucciones:
            self.visit(instruccion)

    def visit_declaracion(self, node):
        _, id, *expresion = node
        if id in self.symbol_table:
            raise SemanticError(f"Variable '{id}' ya declarada.")
        if expresion:
            self.visit(expresion[0])
            self.symbol_table[id] = expresion[0]
        else:
            self.symbol_table[id] = None

    def visit_asignacion(self, node):
        _, id, expresion = node
        if id not in self.symbol_table:
            raise SemanticError(f"Variable '{id}' no declarada.")
        self.visit(expresion)
        self.symbol_table[id] = expresion

    def visit_condicional(self, node):
        _, condicion, instrucciones_then, instrucciones_else = node
        self.visit(condicion)
        for instruccion in instrucciones_then:
            self.visit(instruccion)
        for instruccion in instrucciones_else:
            self.visit(instruccion)

    def visit_bucle_while(self, node):
        _, condicion, instrucciones = node
        self.visit(condicion)
        for instruccion in instrucciones:
            self.visit(instruccion)

    def visit_bucle_for(self, node):
        _, id, inicio, fin, instrucciones = node
        self.symbol_table[id] = inicio  # Declarar la variable del bucle FOR
        self.visit(inicio)
        self.visit(fin)
        for instruccion in instrucciones:
            self.visit(instruccion)

    def visit_impresion(self, node):
        _, expresion = node
        self.visit(expresion)

    def visit_llamada_funcion(self, node):
        _, id, argumentos = node
        for argumento in argumentos:
            self.visit(argumento)

    def visit_expresion(self, node):
        _, izquierda, operador, derecha = node
        self.visit(izquierda)
        self.visit(derecha)

    def visit_condicion(self, node):
        _, izquierda, operador, derecha = node
        self.visit(izquierda)
        self.visit(derecha)

class SemanticError(Exception):
    pass

class ASTToCTranslator:
    def __init__(self, ast):
        self.ast = ast
        self.indent_level = 0

    def translate(self):
        return self.translate_node(self.ast)

    def translate_node(self, node):
        if isinstance(node, tuple):
            node_type = node[0]
            if node_type == 'programa':
                return self.translate_programa(node)
            elif node_type == 'declaracion':
                return self.translate_declaracion(node)
            elif node_type == 'asignacion':
                return self.translate_asignacion(node)
            elif node_type == 'condicional':
                return self.translate_condicional(node)
            elif node_type == 'bucle_while':
                return self.translate_bucle_while(node)
            elif node_type == 'bucle_for':
                return self.translate_bucle_for(node)
            elif node_type == 'impresion':
                return self.translate_impresion(node)
            elif node_type == 'llamada_funcion':
                return self.translate_llamada_funcion(node)
            elif node_type == 'expresion':
                return self.translate_expresion(node)
            elif node_type == 'condicion':
                return self.translate_condicion(node)
            else:
                raise ValueError(f"Unknown node type: {node_type}")
        elif isinstance(node, (int, float)):
            return str(node)
        elif isinstance(node, str):
            return node
        else:
            raise TypeError(f"Unexpected node type: {type(node).__name__}, value: {node}")

    def indent(self):
        return '    ' * self.indent_level

    def translate_programa(self, node):
        instrucciones = node[1]
        code = "#include <stdio.h>\n\nint main() {\n"
        self.indent_level += 1
        for instr in instrucciones:
            code += self.indent() + self.translate_node(instr) + "\n"
        self.indent_level -= 1
        code += "    return 0;\n}\n"
        return code

    def translate_declaracion(self, node):
        id = node[1]
        if len(node) == 3:
            expr = self.translate_node(node[2])
            return f"int {id} = {expr};"
        else:
            return f"int {id};"

    def translate_asignacion(self, node):
        id = node[1]
        expr = self.translate_node(node[2])
        return f"{id} = {expr};"

    def translate_condicional(self, node):
        condicion = self.translate_node(node[1])
        instrucciones_then = node[2]
        instrucciones_else = node[3]
        code = f"if {condicion} {{\n"
        self.indent_level += 1
        for instr in instrucciones_then:
            code += self.indent() + self.translate_node(instr) + "\n"
        self.indent_level -= 1
        if instrucciones_else:
            code += self.indent() + "} else {\n"
            self.indent_level += 1
            for instr in instrucciones_else:
                code += self.indent() + self.translate_node(instr) + "\n"
            self.indent_level -= 1
        code += self.indent() + "}"
        return code

    def translate_bucle_while(self, node):
        condicion = self.translate_node(node[1])
        instrucciones = node[2]
        code = f"while {condicion} {{\n"
        self.indent_level += 1
        for instr in instrucciones:
            code += self.indent() + self.translate_node(instr) + "\n"
        self.indent_level -= 1
        code += self.indent() + "}"
        return code

    def translate_bucle_for(self, node):
        id = node[1]
        inicio = self.translate_node(node[2])
        fin = self.translate_node(node[3])
        instrucciones = node[4]
        code = f"for (int {id} = {inicio}; {id} <= {fin}; {id}++) {{\n"
        self.indent_level += 1
        for instr in instrucciones:
            code += self.indent() + self.translate_node(instr) + "\n"
        self.indent_level -= 1
        code += self.indent() + "}"
        return code

    def translate_impresion(self, node):
        expr = self.translate_node(node[1])
        return f"printf(\"%d\", {expr});"

    def translate_llamada_funcion(self, node):
        id = node[1]
        argumentos = node[2]
        args = ", ".join(self.translate_node(arg) for arg in argumentos)
        return f"{id}({args});"

    def translate_expresion(self, node):
        izq = self.translate_node(node[1])
        op = node[2]
        der = self.translate_node(node[3])
        return f"({izq} {op} {der})"

    def translate_condicion(self, node):
        izq = self.translate_node(node[1])
        op = node[2]
        der = self.translate_node(node[3])
        return f"({izq} {op} {der})"





# Cargar el archivo y analizar
directorio_actual = os.path.dirname(__file__)
directorio_padre = os.path.abspath(os.path.join(directorio_actual, os.pardir))
ruta_archivo = os.path.join(directorio_padre, 'codigo.txt')
with open(ruta_archivo, 'r') as archivo:
    contenido = archivo.read()

tokens = tokenize(contenido)
for token in tokens:
    print(token)

parser = Parser(tokens)
ast = parser.parse()
print(ast)

analyzer = SemanticAnalyzer()
analyzer.analyze(ast)
print("Análisis semántico completado sin errores.")

translator = ASTToCTranslator(ast)
codigo_c = translator.translate()
print(codigo_c)