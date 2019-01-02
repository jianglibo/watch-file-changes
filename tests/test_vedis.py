import pytest
import wfc
from wfc.dir_watcher import my_vedis
from flask import Response
import json


@pytest.fixture
def client():
    app = wfc.create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # with app.app_context():
    #     init_db()

    yield client

    my_vedis.close_vedis(app)


def test_open_vedis():
    app = wfc.create_app()
    assert app.config['ENV'] == 'testing'
    assert app.config[my_vedis.VEDIS_DB]

def test_get_modified(client):
    rv: Response = client.get('/vedis/list-created')
    r = json.loads(rv.get_data(as_text=True))

    assert r['values'] == []