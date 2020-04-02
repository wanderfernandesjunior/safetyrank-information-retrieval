![Logo](https://jcconcursos.uol.com.br/media/_versions/orgao/brasao-ifes_sm.png)
# Trabalho de IA
## Conceitos de recuperação de informação aplicados a documentos de alertas de segurança industriais obtidos da internet

Texto completo: [clique aqui](https://github.com/wanderfernandesjunior/trabalho-ia/blob/master/TextoCompleto.pdf)

Demo: [http://safetyrank.herokuapp.com/](http://safetyrank.herokuapp.com/)

## Resumo
Conforme Russell and Norvig, recuperação de informação é a tarefa de encontrar documentos relevantes e aplicáveis às necessidades dos usuários. Os melhores exemplos de uso são os buscadores da internet. Um sistema de recuperação de informação é caracterizado por quatro componentes:
1. Documentos: também chamado de corpus, é o conjunto de dados a ser analisado.
2. Consulta: também chamada de query, é a informação fornecida pelo usuário sobre o que necessita ser buscado no conjunto de documentos, e pode conter operadores lógicos tais como OR ou AND.
3. Resultados: subconjunto dos documentos que o sistema de recuperação de informações identificou como relevantes para a consulta de entrada.
4. Apresentação: é a exibição visual dos resultados ao usuário.

A maioria dos sistemas de recuperação de informação são baseados em estatísticas de contagem de palavras (bag of words). Uma função de ranqueamento recebe um documento
e uma consulta e retorna um indicador numérico, sendo que os documentos mais relevantes recebem indicadores com valores mais altos. A função de ranqueamento BM25 foi
desenvolvida no projeto Okapi na London’s City College e tem sido usado por mecanismos de busca, tais como o projeto open-source Lucene. Na função BM25, este indicador é
uma combinação linear dos indicadores de cada palavra que compõe a consulta e leva em consideração três fatores: o primeiro é a frequência com a qual uma palavra aparece em determinado documento (TF ou Term Frequency); o segundo é a frequência invertida dos documentos (IDF ou Inverse Documento Frequency), que representa a contagem relativa de documentos que contém determinada palavra; e o terceiro é o tamanho total de cada documento (Russell and Norvig 2016).
O objetivo deste trabalho é a aplicação de conceitos de recuperação de informação do Capítulo 22 do livro Artificial Intelligence: A Modern Approach a documentos de alertas de segurança industriais em formato PDF obtidos da internet.

Este projeto contempla as seguintes etapas:
- Obtenção de alertas de segurança industriais públicos em formato PDF a partir da internet.
- Extração de textos e tabulação em base de dados.
- Aplicação das técnicas de pré-processamento tokenização, remoção de stop words e lematização dos documentos.
- Elaboração de consulta para busca e ordenação nos respectivos documentos aplicando a técnica Okapi BM25
- Elaboração de uma interface para exibição dos documentos recuperados.
- Disponibilização de código fonte no GitHub e protótipo no Heroku.

Serão utilizados alertas de segurança industriais recentes e em inglês a serem obtidos das seguintes instituições: Center for Chemical Process Safety (CCPS), United States Coast Guard, Bureau of Safety and Environmental Enforcement (BSEE), National Offshore Petroleum Safety and Environmental Management Authority (NOPSEMA), International Association of Drilling Contractors (IADC) e Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP).

Para implantação das etapas de extração de textos, tabulação e pré-processamento será utilizada a linguagem de programação Python e a biblioteca NLTK (Natural Language Toolkit). O armazenamento será realizado no banco de dados SQLite, no qual será utilizada uma consulta a ser ordenada conforme a função BM25. A exibição dos resultados será realizada por meio de uma página web utilizando o framework Flask.

## Referências
Russell, S. J., and Norvig, P. 2016. Artificial intelligence: a modern approach. Malaysia; Pearson Education Limited,.
