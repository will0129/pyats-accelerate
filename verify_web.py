import unittest
from netsnap.web import create_app, db, models

class WebTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config={
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Default user is created by create_app if not exists, but we used in-memory DB so it won't exist.
            # create_app only checks on init. We might need to manually trigger or just rely on create_app logic.
            # create_app logic is inside create_app() but after init_app.
            # Let's ensure default user exists.
            if not models.User.query.filter_by(username='pyats').first():
                 u = models.User(username='pyats', role='admin', must_change_password=True)
                 u.set_password('pyats123')
                 db.session.add(u)
                 db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('pyats', 'pyats123')
        assert b'Change Password' in rv.data or b'Dashboard' in rv.data
        rv = self.logout()
        assert b'Sign In' in rv.data
        rv = self.login('pyats', 'wrong')
        assert b'Invalid username or password' in rv.data

    def test_force_password_change(self):
        rv = self.login('pyats', 'pyats123')
        # Should redirect to change password
        assert b'Change Password' in rv.data
        assert b'Current Password' in rv.data

if __name__ == '__main__':
    unittest.main()
