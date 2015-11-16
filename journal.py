# -*- coding: utf-8 -*-

# from contextlib import closing
import markdown
import psycopg2
import os
import logging
import datetime
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from waitress import serve
# from pyramid.events import NewRequest, subscriber
from pyramid.httpexceptions import HTTPFound, \
    HTTPInternalServerError, HTTPForbidden
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
from jinja2 import Environment, PackageLoader
import sqlalchemy as sa
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)


env = Environment(loader=PackageLoader('journal', 'templates'))

here = os.path.dirname(os.path.abspath(__file__))

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Entry(Base):
    __tablename__ = 'entries'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(127), nullable=False)
    text = sa.Column(sa.UnicodeText, nullable=False)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    def __repr__(self):
        return u"{}: {}".format(self.__class__.__name__, self.title)

    @classmethod
    def all(cls):
        return DBSession.query(cls).order_by(cls.created.desc()).all()

    @classmethod
    def by_id(cls, id):
        return DBSession.query(cls).filter(cls.id == id).one()

    @classmethod
    def from_request(cls, request):
        title = request.params.get('title', None)
        text = request.params.get('text', None)
        created = datetime.datetime.utcnow()
        new_entry = cls(title=title, text=text, created=created)
        DBSession.add(new_entry)

    @classmethod
    def desc_new(cls):
        return DBSession.query(cls).order_by(cls.created.desc()).first()

    def json_detail(self):
        '''Displays a JSON object for detailed view'''
        return {'title': self.title,
                'text': self.render_markdown(),
                'created': self.created.strftime('%b %d, %Y'),
                'id': self.id}

    def json_edit(self):
        '''Does not show HTML during editing'''
        return {'title': self.title,
                'text': self.text,
                'created': self.created.strftime('%b %d, %Y'),
                'id': self.id}

    def editing(self, request):
        '''Allows for updating both the entry text, as well as the title'''
        self.title = request.params.get('title', None)
        self.text = request.params.get('text', None)

    def render_markdown(self):
        '''Used to put markdown on text within my template'''
        return markdown.markdown(
            self.text, extensions=['codehilite', 'fenced_code'])


logging.basicConfig()
log = logging.getLogger(__file__)


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['sqlalchemy.url'] = os.environ.get(
        'DATABASE_URL', 'postgresql://nbeck:@localhost:5432/learning_journal'
    )
    engine = sa.engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    settings['auth.username'] = os.environ.get('AUTH_USERNAME', 'admin')
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
            hashalg='sha512',
            debug=True
        ),
        authorization_policy=ACLAuthorizationPolicy(),
    )
    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.add_route('add', '/add')
    config.add_route('detail', '/detail/{id}')
    config.add_route('edit', '/edit')
    config.add_route('list', '/')
    config.scan()
    app = config.make_wsgi_app()
    return app


def markd(input):
    return markdown.markdown(input, extension=["CodeHilite"])


@view_config(route_name='list', renderer='templates/list.jinja2')
def read_entries(request):
    """return a list of all entries as dicts"""
    entries = Entry.all()
    return {'entries': entries}


@view_config(route_name='detail', renderer='templates/detail.jinja2')
def detail_entry(request):
    """return a single entry by its id"""
    entry = Entry.by_id(request.matchdict['id'])
    return {'entry': entry}


@view_config(route_name='edit', renderer='json')
def edit_entry(request):
    """gets posts by id and allows for editing"""
    if request.authenticated_userid:
        entry = Entry.by_id(request.params.get('id', None))
        if request.method == 'GET':
            return entry.json_edit()

        elif request.method == 'POST':
            try:
                entry.editing(request)
            except psycopg2.Error:
                # this will catch any errors generated by the database
                return HTTPInternalServerError()
            return entry.json_detail()
    else:
        return HTTPForbidden()


@view_config(route_name='add', renderer='json', request_method="POST")
def add_entry(request):
    try:
        Entry.from_request(request)
    except psycopg2.Error:
        # this will catch any errors generated by the database
        return HTTPInternalServerError()
    entry = Entry.desc_new()
    return entry.json_detail()


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
