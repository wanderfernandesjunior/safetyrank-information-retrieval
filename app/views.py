import os
import re
import json
from flask import render_template, request, redirect, url_for, make_response, json, Response, abort
from app import db

IDIOMA_ATTRS = {'en': {'indice': 'alertas_english_indice',
                       'tabela': 'alertas_english',
                       'static_folder': 'alertas-english',
                       'stop_words_e_lematizador': 'inglês',
                       'mensagem_inicial': "<p class='text-success'><i class='fas fa-info-circle'></i> There are STR_TOTAL HSE Alerts in our folder.</p><p class='text-secondary'>See below 5 random examples.</p>",
                       'mensagem_erro': "<p class='text-danger'><i class='fas fa-exclamation-circle'></i> An error has occurred: STR_ERRO .</p>",
                       'mensagem_sem_resultados': "<p class='text-danger'><i class='fas fa-info-circle'></i> Your search did not found results.</p>",
                       'mensagem_sem_entrada': "<p class='text-danger'><i class='fas fa-info-circle'></i> Type some input for the algorithm.</p>",
                       'mensagem_com_resultados': "<p class='text-success'><i class='fas fa-info-circle'></i> Your search found STR_RESULTADOS result(s).</p>",
                       'template': 'index.html'}
                }

def index(idioma = "en"):
    if idioma not in IDIOMA_ATTRS.keys():
        abort(Response("Erro: Idioma não encontrado", status=404))

    indice = IDIOMA_ATTRS[idioma]['indice']
    tabela = IDIOMA_ATTRS[idioma]['tabela']
    static_folder = IDIOMA_ATTRS[idioma]['static_folder']
    stop_words_e_lematizador = IDIOMA_ATTRS[idioma]['stop_words_e_lematizador']
    template = IDIOMA_ATTRS[idioma]['template']
    mensagem_inicial = IDIOMA_ATTRS[idioma]['mensagem_inicial']
    mensagem_erro = IDIOMA_ATTRS[idioma]['mensagem_erro']
    mensagem_sem_resultados = IDIOMA_ATTRS[idioma]['mensagem_sem_resultados']
    mensagem_com_resultados = IDIOMA_ATTRS[idioma]['mensagem_com_resultados']

    dbcon = db.get_db()
    total = db.get_total(dbcon, tabela)

    try:
        #Se o metodo é GET então exibe página inicial com info gerais
        if request.method == 'GET':
            info = f"{mensagem_inicial}".replace("STR_TOTAL", str(total[0]))
            #Busca por resultados
            alertas = dbcon.execute(f"""
                SELECT nome_arquivo, conteudo
                FROM {indice}
                WHERE datadoc != ? and datadoc LIKE 'D:%'
                ORDER BY RANDOM()
                LIMIT 5;
                """, (db.NOT_AVAILABLE,)).fetchall()

            return render_template(template, alertas=alertas, total=total[0], info=info, idioma_attrs=IDIOMA_ATTRS[idioma])

        #Se o metodo é POST então busca o melhor alerta e retorna o resultado em formato JSON ou PDF
        elif request.method == 'POST':

            #Recebe e trata a descricao que foi passada pela chamada API ou form web.
            if(request.headers['Content-Type']=='application/x-www-form-urlencoded'):
                descricao = request.form.get('descricao')
                if descricao == "":
                    erro = IDIOMA_ATTRS[idioma]['mensagem_sem_entrada']
                    return render_template(template, total=total[0], info=erro,idioma_attrs=IDIOMA_ATTRS[idioma])
            else:
                dados_entrada = request.get_json()
                descricao = dados_entrada['desc']

            descricao_tratada = re.sub('\"|\'|\_|\?|\.|\,|\!|\/|\;|\:|\)|\(|\-|\[|\]|\ +', ' ',descricao)
            descricao_tratada = re.sub(' +', ' ',descricao_tratada).strip()

            palavras = db.tokenizar(descricao_tratada)
            palavras = db.remover_stopwords(palavras, stop_words_e_lematizador)
            palavras_lematizado = db.lematizar(palavras, stop_words_e_lematizador)

            palavras = ' '.join(palavras)
            palavras_lematizado = ' OR '.join(palavras_lematizado)

            #Busca por resultados
            alertas = dbcon.execute(f"""
                SELECT nome_arquivo, conteudo, ROUND(bm25({indice}), 2) as indicador
                FROM {indice}
                WHERE {indice} MATCH ?
                ORDER BY bm25({indice})
                LIMIT 100;
                """, (palavras_lematizado,)).fetchall()

            if not alertas and request.headers['Content-Type']!='application/json':
                info = f"{mensagem_sem_resultados}"
                return render_template(template, alertas=alertas, total=total[0], info=info, idioma_attrs=IDIOMA_ATTRS[idioma])

            #Retorna JSON se foi chamado via API ou PDFs se chamado via form web.
            if(request.headers['Content-Type']=='application/x-www-form-urlencoded'):
                info = f"{mensagem_com_resultados}".replace("STR_RESULTADOS", str(len(alertas)))
                return render_template(template, descricao=descricao, alertas=alertas, total=total[0], info=info, palavras=palavras,idioma_attrs=IDIOMA_ATTRS[idioma])
            else:
                dados_saida = dict()
                for alerta in alertas[:1]:
                    #retorna em JSON somente o primeiro registro.
                    dados_saida['url'] = request.url_root + f'static/{static_folder}/' + alerta['nome_arquivo']
                    dados_saida['conteudo'] = alerta['conteudo']
                dados_saida = json.dumps(dados_saida,ensure_ascii = False)
                return Response(dados_saida,content_type="application/json; charset=utf-8")

        #Se for qualquer outra coisa exibe erro.
        else:
            return redirect(url_for('index'))

    except Exception as erro:
        if request.headers['Content-Type']=='application/json':
            dados_erro = dict()
            dados_erro['erro'] = str(erro)
            return Response(json.dumps(dados_erro),content_type="application/json; charset=utf-8",status=500)
        else:
            erro = f"{mensagem_erro}".replace("STR_ERRO", str(erro))
            return render_template(template, total=total[0], info=erro,idioma_attrs=IDIOMA_ATTRS[idioma])

    finally:
        dbcon = db.close_db()
