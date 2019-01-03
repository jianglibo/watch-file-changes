import pytest
import wfc
import my_vedis
from flask import Response
import json


@pytest.fixture
def client():
    app = wfc.create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


def test_open_vedis():
    app = wfc.create_app()
    assert app.config['ENV'] == 'testing'

def test_get_modified(client):
    rv: Response = client.get('/vedis/list-created')
    r = json.loads(rv.get_data(as_text=True))

    assert r['values'] == []