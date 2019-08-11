/* TABELAS DE ALERTAS EM INGLES*/
DROP TABLE IF EXISTS alertas_english;
DROP TABLE IF EXISTS alertas_english_indice;

CREATE TABLE alertas_english(
  nome_arquivo TEXT NOT NULL PRIMARY KEY,
  conteudo TEXT NOT NULL,
  palavras TEXT NOT NULL,
  palavras_lematizado TEXT NOT NULL,
  datadoc TEXT
);

CREATE VIRTUAL TABLE alertas_english_indice USING fts5(
  nome_arquivo UNINDEXED,
  conteudo,
  palavras,
  palavras_lematizado UNINDEXED,
  datadoc UNINDEXED
);

CREATE TRIGGER novo_alerta_english AFTER INSERT ON alertas_english BEGIN
  INSERT INTO alertas_english_indice (
    nome_arquivo,
    conteudo,
    palavras,
    palavras_lematizado,
    datadoc
  )
  VALUES(
    new.nome_arquivo,
    new.conteudo,
    new.palavras,
    new.palavras_lematizado,
    new.datadoc
  );
END;
