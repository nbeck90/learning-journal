# -*- coding: utf-8 -*-
from contextlib import closing
from pyramid import testing
import datetime
import os
from journal import INSERT_ENTRY
from journal import connect_db
from journal import DB_SCHEMA
from cryptacular.bcrypt import BCRYPTPasswordManager
from lettuce import world
from lettuce import step
from lettuce import before
from lettuce import after

TEST_DSN = 'dbname=test_learning_journal user=nbeck'


def init_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


def clear_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DROP TABLE entries")
        db.commit()


def clear_entries(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DELETE FROM entries")
        db.commit()


@before.all
def db():
    settings = {'db': TEST_DSN}
    init_db(settings)
    world.settings = settings


@before.all
def app():
    from journal import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    world.app = TestApp(app)


def run_query(db, query, params=(), get_results=True):
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    results = None
    if get_results:
        results = cursor.fetchall()
    return results


@before.all
def login():
    entry_data = {
        'username': 'admin',
        'password': 'secret',
    }
    world.app.post('/login', params=entry_data, status='3*')


@before.all
def entry():
    settings = world.settings
    now = datetime.datetime.utcnow()
    expected = ('New Title', 'New Test', now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@before.all
def entry_2():
    """Add an entry to the database"""
    settings = world.settings
    now = datetime.datetime.utcnow()
    expected = ('Markdown Test', '# Header1', now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@after.all
def cleanup(step):
    clear_db(world.settings)


@step('I am at the homepage')
def at_home(step):
    world.url = "http://127.0..0.0.1:5000/"


@step('I select a posts title or body')
def select_post(step):
    world.response = world.app.get('/detail/1')


@step('Then I am taken to a page with just the post I selected')
def detail_page(step):
    assert 'New Title' in world.response.body


@step('a posts entry detail with a title (.*)')
def get_entry(step, title):
    response = world.app.get('/detail/1')
    assert title in response.body


@step('I move to the edit page')
def edit_page(step):
    response = world.app.get('/edit/1')
    assert 'id="share_button"' in response.body


@step('I click the edit button')
def edit_button(step):
    entry_data = {
        'title': 'Edited Title Text',
        'text': 'Edited Post',
    }
    world.app.post('/edit/1', params=entry_data, status='3*')

