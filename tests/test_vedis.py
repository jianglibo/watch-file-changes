import pytest
import wfc
from wfc.dir_watcher import my_vedis


# @pytest.fixture
# def client():
    # app = init.create_app()
    # app.config['TESTING'] = True
    # client = app.test_client()

    # with app.app_context():
    #     init_db()

    # yield client

    # os.close(db_fd)
    # os.unlink(flaskr.app.config['DATABASE'])


def test_open_vedis():
    app = wfc.create_app()
    assert app.config['ENV'] == 'production'
    assert app.config[my_vedis.VEDIS_DB]