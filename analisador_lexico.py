#Analisador léxico com dois buffers
#Autor: Alessandro Vagner Lyra Rodrigues
#Feito como trabalho da disciplina de Compiladores
#Data: 12/09/2026
#Testado com Python versão 3.12.3

#Lê um código em java e retorna tokens, além de construir uma tabela de símbolos com os identificadores

import re

eof = '\0'


class LeitorBuffer:
    def __init__(self, arquivo, buffer_size):
        self.buffer_size = buffer_size
        self.buffer1 = [''] * (buffer_size + 1)
        self.buffer2 = [''] * (buffer_size + 1)
        self.buffer_atual = 1
        self.begin_pointer = 0
        self.forward_pointer = 0
        self.is_eof = False

        self.file = open(arquivo, "r", encoding="utf-8")

        self.ler_codigo()


    def ler_codigo(self):
        buffer = self.buffer1 if self.buffer_atual == 1 else self.buffer2
        dados = self.file.read(self.buffer_size)
        if not dados:
            self.is_eof = True
            #print(self.buffer1)
            #print(self.buffer2)
            return True
        #print(dados)
        for i in range(len(dados)):
            buffer[i] = dados[i]
        buffer[len(dados)] = eof
        #print(buffer)


    def ler_caractere(self):
        buffer = self.buffer1 if self.buffer_atual == 1 else self.buffer2
        char = buffer[self.forward_pointer]

        #Alternar buffers
        if char == eof:
            #if self.forward_pointer < self.buffer_size and self.buffer_atual[self.forward_pointer] == eof:
                #self.is_eof = True
                #return eof
            if self.buffer_atual == 1:
                self.buffer_atual = 2
                self.forward_pointer = 0
                self.ler_codigo()
            else:
                self.buffer_atual = 1
                self.forward_pointer = 0
                self.ler_codigo()
            buffer = self.buffer1 if self.buffer_atual == 1 else self.buffer2
            char = buffer[self.forward_pointer]

        self.forward_pointer += 1
        return char

    def update_begin_pointer(self):
        self.begin_pointer = self.forward_pointer
        return self.begin_pointer

    def __del__(self):
        self.file.close() #Garantir que o arquivo seja fechado ao fim do programa


class CriadorDeTokens():
    def __init__(self, leitor_buffer):
        #Atributos gerais
        self.reader = leitor_buffer
        self.palavras_chave = ["if", "else", "switch", "case", "default", "for", "while", "do", "break",
                               "continue", "return", "class", "interface", "enum", "extends", 
                               "implements", "new", "this", "super", "instanceof", 
                               "boolean", "byte", "char", "short", "int", "long", "float", "double", "void", 
                               "abstract", "final", "static", "synchronized", "volatile",
                               "transient", "native", "strictfp", "try", "catch", "finally", 
                               "throw", "throws", "assert", "package", "import", 
                               "module", "requires", "export", "opens", "uses", "provides", "with", 
                               "record", "sealed", "permits", "non-sealed", "const", "goto", "public", "private", "protected"]

        self.literais_reservados = {"true": ("BOOL", "true"), "false": ("BOOL", "false"), "null": ("NULL", "")}
        self.operadores = ["==","!=", ">=", "<=","+", "-", "*", "/", "=", "<", ">", "|", "||", "&", "&&", "!", "+=", "*=", "-=", "/="]
        self.separadores = {";": ("SEMICOLON", ""), "(":("LPAREN", ""), ")":("RPAREN", ""), "[":("LBRACKET", ""), "]":("RBRACKET", ""), "{":("LBRACE", ""), "}":("RBRACE", "")}

        #Flags
        self.string_flag = False #True se uma string foi iniciada, False quando não há strings ou a string foi fechada
        self.comment_flag = False #True se estiver em um comentário de linha única
        self.multi_comment_flag = False #True se estiver em um bloco de comentário de múltiplas linhas

        #Contadores
        self.paren_count = 0
        self.bracket_count = 0
        self.brace_count = 0


    def criar_tokens(self):
        tokens = []
        lexema = []

        while True:
            char = self.reader.ler_caractere()
            #print(self.reader.is_eof)
            if char == eof and not lexema:
                break
            if char == eof:
                char = " "

            if self.reader.is_eof: #Fim do arquivo
                if (self.string_flag == True) or self.paren_count != 0 or self.bracket_count != 0  or self.brace_count != 0:
                    tokens.append(("ERROR", "")) #Strings, parênteses, colchetes ou chaves não fechados
                elif lexema:
                    lexema_string = "".join(lexema)
                    tokens.append(self.classificar_lexema(lexema_string)) #Tokenizar o último lexema
                    lexema = []
                    self.reader.update_begin_pointer()
                break

            if self.multi_comment_flag: #Ignorar comentários de linhas múltiplas
                if char == "*":
                    buffer = self.reader.buffer1 if self.reader.buffer_atual == 1 else self.reader.buffer2
                    if buffer[self.reader.forward_pointer] == "/": #Lookahead
                        self.multi_comment_flag = False
                        char = self.reader.ler_caractere()
                        char = self.reader.ler_caractere() #Mover o ponteiro do buffer
                    else:
                        continue
                else:
                    continue

            if self.comment_flag: #Ignorar comentários
                if char == "\n":
                    self.comment_flag = False
                else:
                    continue

            #print("".join(lexema))

            if char == "\"" or char == "\'": #Strings
                if self.string_flag == False:
                    self.string_flag = True
                    #print(self.string_flag)
                else:
                    self.string_flag = False
                    lexema.append(char) #Adicionar a aspa no fim da string
                    lexema_string = "".join(lexema)
                    tokens.append(("LITERAL_STRING", lexema_string))
                    lexema = []
                    self.reader.update_begin_pointer()
                    continue
            if self.string_flag == False:
                if char.isspace(): #Espaços em branco
                    if lexema:
                        lexema_string = "".join(lexema)
                        tokens.append(self.classificar_lexema(lexema_string))
                        lexema = []
                        self.reader.update_begin_pointer()
                elif char in self.separadores.keys(): #Separadores
                    if char == "(":
                        self.paren_count += 1
                    elif char == ")":
                        self.paren_count -= 1
                        if self.paren_count < 0:
                            tokens.append(("ERROR", "")) #Fechar um parêntese que nunca foi aberto

                    if char == "[":
                        self.bracket_count += 1
                    elif char == "]":
                        self.bracket_count -= 1
                        if self.bracket_count < 0:
                            tokens.append(("ERROR", "")) #Fechar um parêntese que nunca foi aberto

                    if char == "{":
                        self.brace_count += 1
                    elif char == "}":
                        self.brace_count -= 1
                        if self.brace_count < 0:
                            tokens.append(("ERROR", "")) #Fechar um parêntese que nunca foi aberto               
                    if lexema:
                        lexema_string = "".join(lexema)
                        tokens.append(self.classificar_lexema(lexema_string))
                        lexema = []
                        self.reader.update_begin_pointer()
                    if not (self.paren_count < 0 or self.brace_count < 0 or self.bracket_count < 0): #Evitar token RPAREN se houver um parêntese fechando outro que nunca foi aberto
                        tokens.append(self.separadores[char])

                elif char == ",": #Esse separador é um caso especial, já que pode ser um erro de digitação em um float
                    if lexema:
                        lexema_string = "".join(lexema)
                        if (not lexema_string.isdigit()) or self.paren_count > 0:
                            tokens.append(self.classificar_lexema(lexema_string))
                            tokens.append(("COMMA", ""))
                            lexema = []
                            self.reader.update_begin_pointer()
                        else:
                            lexema.append(char)

                elif char in self.operadores: #Operadores
                    if char == "/":
                        buffer = self.reader.buffer1 if self.reader.buffer_atual == 1 else self.reader.buffer2
                        if buffer[self.reader.forward_pointer] == "/": #Lookahead
                            if lexema:
                                lexema_string = "".join(lexema)
                                tokens.append(self.classificar_lexema(lexema_string))
                                lexema = []
                                self.reader.update_begin_pointer()
                            self.comment_flag = True
                            continue
                        elif buffer[self.reader.forward_pointer] == "*":
                            if lexema:
                                lexema_string = "".join(lexema)
                                tokens.append(self.classificar_lexema(lexema_string))
                                lexema = []
                                self.reader.update_begin_pointer()
                            self.multi_comment_flag = True
                            continue
                        else:
                            char2 = buffer[self.reader.forward_pointer] #Lookahead
                            op_string = char + char2
                            #print(op_string)
                            if op_string in self.operadores:
                                tokens.append(("OPERATOR", op_string))
                                if lexema:
                                    lexema_string = "".join(lexema)
                                    tokens.append(self.classificar_lexema(lexema_string))
                                    lexema = []
                                    self.reader.update_begin_pointer()
                                char = self.reader.ler_caractere() #Mover o ponteiro
                                continue
                    elif char in "=><|!+-*&":
                        buffer = self.reader.buffer1 if self.reader.buffer_atual == 1 else self.reader.buffer2
                        char2 = buffer[self.reader.forward_pointer] #Lookahead
                        op_string = char + char2
                        #print(char)
                        #print(char2)
                        if op_string in self.operadores:
                            tokens.append(("OPERATOR", op_string))
                            if lexema:
                                lexema_string = "".join(lexema)
                                tokens.append(self.classificar_lexema(lexema_string))
                                lexema = []
                                self.reader.update_begin_pointer()
                            char = self.reader.ler_caractere() #Mover o ponteiro
                            continue
                    if lexema:
                        lexema_string = "".join(lexema)
                        tokens.append(self.classificar_lexema(lexema_string))
                        lexema = []
                        self.reader.update_begin_pointer()
                    tokens.append(("OPERATOR", char))
                else:
                    lexema.append(char)
            else:
                lexema.append(char)

        #if self.string_flag == True:
            #tokens.append(("ERROR", ""))
            #return(("ERROR", ""))
        return tokens

    def classificar_lexema(self, lexema: str):
        if lexema in self.palavras_chave:
            return ("KEYWORD", lexema)
        elif lexema in self.literais_reservados.keys():
            return self.literais_reservados[lexema]
        else:
            if self.checar_erros(lexema) == False:
                return ("ERROR", "")
            try:
                int(lexema)
                return ("NUM_INT", lexema)
            except:
                try:
                    float(lexema)
                    return ("NUM_FLOAT", lexema)
                except:
                    return ("ID", lexema)

    def checar_erros(self, lexema: str):
        #Número int sem erros (para evitar falso positivo)
        if bool((re.match(r"^\d+$", lexema))):
            return True
        
        #Lexema começando com um número e terminando com texto
        if bool((re.match(r"^\d+[a-zA-Z0-9]+$", lexema))):
            return False

        #Float incorretamente digitado com vírgula ao invés de ponto
        if bool((re.match(r"^\d+,\d+$", lexema))):
            return False
        
        return True


class AnalizadorLexico:
    def __init__(self, arquivo: str, buffer_size: int):
        self.criador_tokens = CriadorDeTokens(LeitorBuffer(arquivo, buffer_size))
        self.tokens_gerados = []
        self.tabela_simbolos = {}

    def obter_tokens(self):
        self.tokens_gerados = self.criador_tokens.criar_tokens()
        return self.tokens_gerados

    def construir_tabela_simbolos(self):
        id = 0
        for token in self.tokens_gerados:
            if token[0] == "ID":
                if token in self.tabela_simbolos.keys():
                    self.tabela_simbolos[token] += 1 #Incrementar a quantidade de ocorrências
                else:
                    self.tabela_simbolos[token] = 1 #Adicionar novo token a tabela de símbolos
        return self.tabela_simbolos

#Testes
print("=====Código Correto=====")
analisador = AnalizadorLexico("hello_world.java", 10)
print("Tokens gerados:")
print(analisador.obter_tokens())
print("\n")
print("Tabela de símbolos:")
print(analisador.construir_tabela_simbolos())

print("\n")

print("=====Código Errado=====")
analisador = AnalizadorLexico("codigo_errado.java", 10)
print("Tokens gerados:")
print(analisador.obter_tokens())
print("\n")
print("Tabela de símbolos:")
print(analisador.construir_tabela_simbolos())

#criador_tokens = CriadorDeTokens(LeitorBuffer("teste.txt", 10))
#print(criador_tokens.criar_tokens())