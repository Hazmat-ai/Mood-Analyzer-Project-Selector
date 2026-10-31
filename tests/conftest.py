import pytest
from app import create_app

@pytest.fixture
def application(tmp_path):
    dist = tmp_path / 'dist'
    dist.mkdir()
    (dist / 'index.html').write_text('<h1>Project studio</h1>')
    return create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.sqlite'),'FRONTEND_DIST':str(dist),'RATE_LIMIT':10000})

@pytest.fixture
def client(application):
    return application.test_client()
