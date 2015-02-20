# -*- coding: utf-8 -*-

from contextlib import closing
import jinja2
import markdown
import psycopg2
import os
import logging
import datetime
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from waitress import serve
from pyramid.events import NewRequest, subscriber
from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError, HTTPForbidden
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('journal', 'templates'))

here = os.path.dirname(os.path.abspath(__file__))

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    text TEXT NOT NULL,
    created TIMESTAMP NOT NULL
)
"""

INSERT_ENTRY = """
INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
"""

DB_ENTRIES_LIST = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""

SELECT_ID = """
SELECT * FROM entries WHERE id=%s
"""

READ_ENTRY = """
SELECT id, title, text, created FROM entries WHERE id = %s
"""

UPDATE_ENTRY = """
UPDATE entries SET (title, text) = (%s, %s) WHERE id=%s
"""

NEW_ENTRY = """
SELECT * FROM entries ORDER BY created DESC LIMIT 1
"""

logging.basicConfig()
log = logging.getLogger(__file__)


def connect_db(settings):
    """Return a connection to the configured database"""
    return psycopg2.connect(settings['db'])


def init_db():
    """Create database dables defined by DB_SCHEMA

    Warning: This function will not update existing table definitions
    """
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=learning_journal user=nbeck'
    )
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


@subscriber(NewRequest)
def open_connection(event):
    request = event.request
    settings = request.registry.settings
    request.db = connect_db(settings)
    request.add_finished_callback(close_connection)


def close_connection(request):
    """close the database connection for this request

    If there has been an error in the processing of the request, abort any
    open transactions.
    """
    db = getattr(request, 'db', None)
    if db is not None:
        if request.exception is not None:
            db.rollback()
        else:
            db.commit()
        request.db.close()


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=learning_journal user=nbeck'
    )
    # secret value for session signing:
    settings['auth.username'] = os.environ.get('ADMIN_USERNAME', 'admin')
    manager = BCRYPTPasswordManager()
    settings['auth.password'] = os.environ.get(
        'AUTH_PASSWORD', manager.encode('secret')
    )
    secret = os.environ.get('JOURNAL_SESSION_SECRET', 'itsaseekrit')
    session_factory = SignedCookieSessionFactory(secret)
    # add a secret value for auth tkt signing
    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', 'anotherseekrit')
    # configuration setup
    config = Configurator(
        settings=settings,
        session_factory=session_factory,
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=auth_secret,
            hashalg='sha512'
        ),
        authorization_policy=ACLAuthorizationPolicy(),
    )
    jinja2.filters.FILTERS['markdown'] = markd
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.add_route('home', '/')
    config.add_route('add', '/add')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('detail', '/detail/{id}')
    config.add_route('edit', '/edit')
    config.scan()
    app = config.make_wsgi_app()
    return app


def markd(input):
    return markdown.markdown(input, extension=["CodeHilite"])


def write_entry(request):
    """write a single entry to the database"""
    title = request.params.get('title', None)
    text = request.params.get('text', None)
    created = datetime.datetime.utcnow()
    request.db.cursor().execute(INSERT_ENTRY, [title, text, created])


@view_config(route_name='home', renderer='templates/list.jinja2')
def read_entries(request):
    """return a list of all entries as dicts"""
    cursor = request.db.cursor()
    cursor.execute(DB_ENTRIES_LIST)
    keys = ('id', 'title', 'text', 'created')
    entries = [dict(zip(keys, row)) for row in cursor.fetchall()]
    for entry in entries:
        entry['text'] = markdown.markdown(entry['text'], extensions=['codehilite', 'fenced_code'])
    return {'entries': entries}


@view_config(route_name='detail', renderer='templates/detail.jinja2')
def detail_entry(request):
    """return a single entry"""
    cursor = request.db.cursor()
    cursor.execute(SELECT_ID, (request.matchdict['id'], ))
    keys = ('id', 'title', 'text', 'created')
    row = cursor.fetchone()
    entry = dict(zip(keys, row))
    entry['text'] = markdown.markdown(
        entry['text'], extensions=['codehilite', 'fenced_code'])
    return {'entry': entry}


def update_entry(request):
    id = request.params.get('id')
    title = request.params.get('title')
    text = request.params.get('text')
    request.db.cursor().execute(UPDATE_ENTRY, [title, text, id])


@view_config(route_name='edit', renderer='json')
def editview_entry(request):
    if request.authenticated_userid:
        if request.method == 'GET':
            cursor = request.db.cursor()
            cursor.execute(SELECT_ID, (request.params.get('id', None), ))
            keys = ('id', 'title', 'text', 'created')
            row = cursor.fetchone()
            entry = dict(zip(keys, row))
            entry['created'] = entry['created'].strftime('%b %d, %Y')

            return entry

        elif request.method == 'POST':
            try:
                update_entry(request)
            except psycopg2.Error:
                # this will catch any errors generated by the database
                return HTTPInternalServerError()

            cursor = request.db.cursor()
            cursor.execute(READ_ENTRY, (request.params.get('id', None), ))
            keys = ('id', 'title', 'text', 'created')
            # import pdb; pdb.set_trace()
            row = cursor.fetchone()
            entry = dict(zip(keys, row))

            entry['text'] = markdown.markdown(
                entry['text'], extensions=['codehilite', 'fenced_code'])
            entry['created'] = entry['created'].strftime('%b %d, %Y')
            return entry
    else:
        return HTTPForbidden()


@view_config(route_name='add', renderer='json', request_method="POST")
def add_entry(request):
    if request.authenticated_userid:
        try:
            write_entry(request)
        except psycopg2.Error:
            # this will catch any errors generated by the database
            return HTTPInternalServerError()

        cursor = request.db.cursor()
        cursor.execute(NEW_ENTRY)
        keys = ('id', 'title', 'text', 'created')
        row = cursor.fetchone()
        entry = dict(zip(keys, row))
        entry['text'] = markdown.markdown(entry['text'], extensions=['codehilite', 'fenced_code'])
        entry['created'] = entry['created'].strftime('%b.%d.%Y')
        return entry
    else:
        return HTTPForbidden()
    # return HTTPFound(request.route_url('home'))


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    settings = request.registry.settings
    manager = BCRYPTPasswordManager()
    if username == settings.get('auth.username', ''):
        hashed = settings.get('auth.password', '')
        return manager.check(hashed, password)


@view_config(route_name='login', renderer="templates/login.jinja2")
def login(request):
    """authenticate a user by username/password"""
    username = request.params.get('username', '')
    error = ''
    if request.method == 'POST':
        error = "Login Failed"
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)

    return {'error': error, 'username': username}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
