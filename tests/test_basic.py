import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:postgres@localhost:5432/webapp1_test'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_create_user():
    app = create_app()
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            name='Test User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        assert User.query.filter_by(username='testuser').first() is not None 