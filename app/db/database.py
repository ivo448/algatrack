import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app, g
import click

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            current_app.config['POSTGRES_URI'],
            cursor_factory=RealDictCursor
        )
        g.db.autocommit = True 
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Crea las tablas en Postgres"""
    db = get_db()
    with db.cursor() as cursor:
        with current_app.open_resource('db/schema_postgres.sql') as f:
            cursor.execute(f.read().decode('utf8')) 

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Base de datos PostgreSQL inicializada.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)