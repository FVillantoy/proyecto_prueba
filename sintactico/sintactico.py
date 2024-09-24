import re
import os

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
