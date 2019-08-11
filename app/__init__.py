import os
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory
from app import db, views

def create_app(test_config=None):
    """Cria e configura uma instancia da aplicação Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='wfernandesjunior',
        # armazena a base de dados na pasta instance
        DATABASE=os.path.join(app.instance_path, 'alertas.sqlite'),
    )

    # garante que a pasta instance existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # registra os comando de banco de dados (flask init-db) e inicializa a conexão
    db.init_app(app)

    # registra as URLs das paginas
    app.add_url_rule('/', view_func=views.index, methods=["GET", "POST"])

    return app
