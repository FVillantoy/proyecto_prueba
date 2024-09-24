import re
import os

# Definimos los tipos de tokens
token_specification = [
    ('NUMBER_FLOAT',   r'\d+\.\d+'),   # Números decimales
    ('NUMBER_INT',     r'\d+'),        # Números enteros
    ('STRING',         r'"[^"]*"'),    # Cadenas de texto
    ('CHAR',           r"'[^']'"),     # Caracteres
    ('ASSIGN',         r'='),          # Asignación
    ('STMT_END',       r';'),          # Fin de una instrucción
    ('ID',             r'[A-Za-z_]\w*'),# Identificadores
    ('OP',             r'[+\-*/]'),    # Operadores aritméticos
    ('OP_REL',         r'[<>!=]=?|=='),# Operadores relacionales
    ('NEWLINE',        r'\n'),         # Líneas nuevas
    ('SKIP',           r'[ \t]+'),     # Espacios y tabulaciones
    ('COMMENT',        r'//.*'),       # Comentarios
    ('BEGIN',          r'BEGIN'),      # Palabras clave
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
]
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

directorio_actual = os.path.dirname(__file__)
directorio_padre = os.path.abspath(os.path.join(directorio_actual, os.pardir))
ruta_archivo = os.path.join(directorio_padre, 'codigo.txt')
with open(ruta_archivo, 'r') as archivo:
    contenido = archivo.read()

tokens = tokenize(contenido)
for token in tokens:
    print(token)
