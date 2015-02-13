# -*- coding: utf-8 -*-
from contextlib import closing
import datetime
import os
from journal import INSERT_ENTRY
from journal import connect_db
from journal import DB_SCHEMA
from lettuce import world
from lettuce import step
from lettuce import before
from lettuce import after

TEST_DSN = 'dbname=test_learning_journal user=nbeck'


def init_db(setup):
    with closing(connect_db(setup)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


def empty_db(setup):
    with closing(connect_db(setup)) as db:
        db.cursor().execute("DROP TABLE entries")
        db.commit()


def clear_entries(setup):
    with closing(connect_db(setup)) as db:
        db.cursor().execute("DELETE FROM entries")
        db.commit()


@before.all
def db():
    setup = {'db': TEST_DSN}
    init_db(setup)
    world.setup = setup


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
def entry1():
    setup = world.setup
    now = datetime.datetime.utcnow()
    expected = ('New Title', 'New Test', now)
    with closing(connect_db(setup)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@before.all
def entry2():
    """Add an entry to the database with a header"""
    setup = world.setup
    now = datetime.datetime.utcnow()
    expected = ('Markdown Test', '# Header1', now)
    with closing(connect_db(setup)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@before.all
def entry3():
    """Add an entry to the database with a header"""
    setup = world.setup
    now = datetime.datetime.utcnow()
    expected = ('Markdown Test', "```Inline code```", now)
    with closing(connect_db(setup)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@after.all
def cleanup(step):
    empty_db(world.setup)


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


@step('I click the edit button')
def edit_click(step):
    world.app.get('/detail/1')
    action = world.response.click("Edit")
    assert 'id="share_button"' in action.body


@step('I move to the edit page')
def edit_page(step):
    response = world.app.get('/edit/1')
    assert 'id="share_button"' in response.body


@step('a post that I have edited')
def edited_post(step):
    response = world.app.get('/edit/1')
    assert 'id="share_button"' in response.body


@step('I click the share button')
def button_exists(step):
    response = world.app.get('/edit/1')
    assert 'id="share_button"' in response.body


@step('I move to that posts detail page')
def click_share(step):
    response = world.app.get('/edit/1')
    edit_form = response.form
    sub = edit_form.submit
    select = sub("share_button", index=5)
    assert select.status_code == 302
    redirect = select.follow()
    assert 'class="edit_button"' in redirect.body


@step("a posts detail page with markdown written in it")
def at_detail(step):
    response = world.app.get('/detail/1')
    assert 'class="edit_button"' in response.body


@step('I see properly formatted/colored text')
def is_colored(step):
    response = world.app.get('/detail/3')
    assert '<code>Inline code</code>' in response.body


@step('I see properly formatted/rendered text')
def is_markd(step):
    response = world.app.get('/detail/2')
    assert '<h1>Header1</h1>' in response.body
