
from lettuce import before, after, step, world
from contextlib import closing
import os

from journal import connect_db
from journal import DB_SCHEMA
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid import testing

TEST_DSN = 'dbname=test_learning_journal user=nbeck'


@step('Given a posts detail page and I am logged in')
def authorized_edit_entry(step):
    response = world.app.get("/detail/1")
    assert response.status_code == 200
    world.authorized = True


@step('I am at the homepage')
def at_home(step):
    world.url = "http://127.0..0.0.1:5000/"


def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('secret'),
    }
