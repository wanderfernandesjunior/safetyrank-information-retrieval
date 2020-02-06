import os, io, sqlite3, PyPDF2, click, re, string, nltk
from flask import current_app, g
from flask.cli import with_appcontext
from wand.image import Image, Color
from pdfminer import (layout as pdfminer_layout, high_level as pdfminer_high_level)

NOT_AVAILABLE = 'NOT AVAILABLE'

def get_db():
    """Conecta com o banco de dados da aplicação. A conexão
    é única para cada requisição e será recusada se chamada
    novamente.
    """
    if 'dbcon' not in g:
        g.dbcon = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.dbcon.row_factory = sqlite3.Row

    return g.dbcon

def close_db(e=None):
    """Se estiver conectado ao banco de dados, fecha a conexão."""
    dbcon = g.pop('dbcon', None)

    if dbcon is not None:
        dbcon.close()

def converte_pdf_para_texto(pdf_filename):
    # https://stackoverflow.com/a/46695574/334872
    output = io.StringIO()
    # Utilizando configurações padrão
    laparams = pdfminer_layout.LAParams()

    with open(pdf_filename, "rb") as pdffile:
        pdfminer_high_level.extract_text_to_fp(pdffile, output,
                                               laparams=laparams)

    return output.getvalue()

def insert_file_into_db(dbcon, diretorio, nome_arquivo, tabela, idioma):
    # Lê conteúdo do arquivo
    pdfReader = PyPDF2.PdfFileReader(f"{diretorio}{nome_arquivo}", strict=False)
    if pdfReader.isEncrypted:
        pdfReader.decrypt('')

    try: # tenta primeiro ler com pdfminer.six
        conteudo = converte_pdf_para_texto(f"{diretorio}{nome_arquivo}")
    except: # fallback para PyPDF2
        conteudo=''
        for numPage in range(pdfReader.numPages):
            pageObj = pdfReader.getPage(numPage)
            conteudoParcial = pageObj.extractText()
            conteudoParcial = conteudoParcial.replace('\n','')
            conteudoParcial = conteudoParcial.strip()
            conteudoParcial = re.sub(' +', ' ',conteudoParcial)
            conteudo += ' ' + conteudoParcial

    dst_pdf = PyPDF2.PdfFileWriter()
    dst_pdf.addPage(pdfReader.getPage(0))

    pdf_bytes = io.BytesIO()
    dst_pdf.write(pdf_bytes)
    pdf_bytes.seek(0)

    # Faz um PNG a partir da primeira pagina PDF.
    try:
        with Image(file=pdf_bytes, resolution=72) as imagem:
            pagina = imagem.sequence[0]
            with Image(image=pagina) as imagem:
                imagem.resize(width=157, height=217)
                imagem.format = 'png'
                imagem.background_color = Color('white')
                imagem.alpha_channel = 'remove'
                imagem.convert('png')
                imagem.save(filename=f'{diretorio}{nome_arquivo}.png')
    except Exception as e:
        print(f"Erro: {e}")

    if pdfReader.documentInfo and '/CreationDate' in pdfReader.documentInfo:
        datadoc = pdfReader.documentInfo.get("/CreationDate", NOT_AVAILABLE)
        datadoc = datadoc.replace("'", "")
    else:
        datadoc = NOT_AVAILABLE

    palavras = tokenizar(conteudo)
    palavras = remover_stopwords(palavras, "inglês")
    palavras_lematizado = lematizar(palavras, "inglês")
    palavras = ' '.join(palavras)
    palavras_lematizado = ' '.join(palavras_lematizado)

    dbcon.execute("""
    INSERT INTO alertas_english (nome_arquivo, conteudo, palavras, palavras_lematizado, datadoc)
    VALUES (?,?,?,?,?)
    """, (nome_arquivo, conteudo, palavras, palavras_lematizado, datadoc))

    dbcon.commit()

    # Salva em TXT
    arquivo_txt = open(f"{diretorio}{nome_arquivo}.txt","w")
    arquivo_txt.write(conteudo)
    arquivo_txt.close() 

    print(nome_arquivo, "foi inserido.")

def init_db(diretorio, tabela, idioma):
    """Apaga dados existentes, cria novas tabelas e cadastra alertas de SMS."""
    dbcon = get_db()

    with current_app.open_resource('schema.sql') as f:
        dbcon.executescript(f.read().decode('utf8'))

    try:
        #Contador do total de alertas
        total = 0

        #Imprime resultado
        print("___________________INICIO____________________")
        print(f"IDIOMA: {idioma}")

        #Passa por todos os alertas da pasta static/alertas
        for nome_arquivo in os.listdir(diretorio):
            #Verifica se o arquivo é PDF e lê as informações do mesmo
            if nome_arquivo.endswith('.pdf'):
                insert_file_into_db(dbcon, diretorio, nome_arquivo, tabela, idioma)
                total += 1

        #Imprime resultado
        print("___________________RESUMO____________________")
        print(f"Total de alertas em {idioma}: {total}")
        print("_____________________________________________\n\n")

    except Exception as e:
        print(f"Ocorreu um erro ao inserir/atualizar o alerta {nome_arquivo} no banco de dados.")
        print(f"Erro: {e}")

def update_db(diretorio, tabela, idioma):
    """Atualiza tabelas com novos alertas de SMS, ignorando arquivos existentes."""
    dbcon = get_db()
    try:
        # Coleta alertas existentes no banco
        alertas_existentes = dbcon.execute(f'SELECT nome_arquivo FROM {tabela}') \
                                  .fetchall()
        alertas_existentes = [alerta['nome_arquivo'] for alerta in alertas_existentes]

        #Contador do total de alertas
        total = 0

        #Imprime resultado
        print("___________________INICIO____________________")
        print(f"IDIOMA: {idioma}")

        #Passa por todos os alertas da pasta static/alertas AINDA NÃO existentes no banco
        for nome_arquivo in os.listdir(diretorio):
            #Verifica se o arquivo é PDF e lê as informações do mesmo
            if nome_arquivo.endswith('.pdf') and nome_arquivo not in alertas_existentes:
                insert_file_into_db(dbcon, diretorio, nome_arquivo, tabela, idioma)
                total += 1

        #Imprime resultado
        print("___________________RESUMO____________________")
        print(f"Total de alertas em {idioma}: {total}")
        print("_____________________________________________\n\n")

    except Exception as e:
        print(f"Ocorreu um erro ao inserir/atualizar o alerta {nome_arquivo} no banco de dados.")
        print(f"Erro: {e}")
        print('A execução terminará agora.')

def get_total(dbcon, tabela):
    """Busca total de alertas de SMS"""
    query = f'SELECT COUNT(*) FROM {tabela};'
    total = dbcon.execute(query).fetchone()
    return total

def tokenizar(sentence):
    """Função que recebe texto como entrada e devolve lista
    de palavras.
    """
    sentence = sentence.lower()
    sentence = nltk.word_tokenize(sentence)
    return sentence

def remover_stopwords(sentence, idioma):
    """Função que recebe texto como entrada e devolve lista
    de palavras excluindo pontuacao, preposicoes, artigos,
    palavra com 1 letra, etc.
    """
    if idioma == "inglês":
        stopwords = nltk.corpus.stopwords.words('english')
        phrase = []
        for word in sentence:
            if word not in stopwords and word not in string.punctuation and len(word)>1:
                phrase.append(word)
        return phrase
    elif idioma == "espanhol":
        stopwords = nltk.corpus.stopwords.words('spanish')
        phrase = []
        for word in sentence:
            if word not in stopwords and word not in string.punctuation and len(word)>1:
                phrase.append(word)
        return phrase
    elif idioma == "português":
        stopwords = nltk.corpus.stopwords.words('portuguese')
        phrase = []
        for word in sentence:
            if word not in stopwords and word not in string.punctuation and len(word)>1:
                phrase.append(word)
        return phrase

def lematizar(sentence, idioma):
    """Função que recebe sentenças como entrada e devolve apos passar
    por removedor de sufixos.
    """
    if idioma == "inglês":
        stemmer = nltk.stem.SnowballStemmer('english')
        phrase = []
        for word in sentence:
            phrase.append(stemmer.stem(word.lower()))
        return phrase
    elif idioma == "espanhol":
        stemmer = nltk.stem.SnowballStemmer('spanish')
        phrase = []
        for word in sentence:
            phrase.append(stemmer.stem(word.lower()))
        return phrase
    elif idioma == "português":
        stemmer = nltk.stem.RSLPStemmer()
        phrase = []
        for word in sentence:
            phrase.append(stemmer.stem(word.lower()))
        return phrase

def init_app(app):
    """Registra funções de banco de dados no Flask app. Esta função é
    chamada pela application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Apaga dados existentes, cria novas tabelas e cadastra alertas de SMS."""

    init_db('./app/static/alertas-english/', "alertas_english", "inglês")

@click.command('update-db')
@with_appcontext
def update_db_command():
    """Atualiza tabelas com novos alertas de SMS, ignorando arquivos existentes."""

    update_db('./app/static/alertas-english/', "alertas_english", "inglês")
