"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production 
#    python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1234567
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            response = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(response.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_unauthorized_message_add(self):
        """ Can a not-logged-in user add a message? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = -1    
            response = c.post("messages/new", data={"text": "Hello"})
            self.assertEqual(response.location, "http://localhost/")

    def test_show_message(self):
        """ Can a logged-in user view a message that exists? """

        m = Message(id=9999, text="yo yo yo", user_id=self.testuser_id)
        
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(9999)

            response = c.get(f'/messages/{m.id}')

            self.assertEqual(response.status_code, 200)
            self.assertIn(m.text, str(response.data))

    def test_show_invalid_message(self):
        """ Can anyone view a message that does not exist? """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.get('/messages/101010101')

            self.assertEqual(response.status_code, 404)

    def test_delete_message(self):

        m = Message(id=9999, text="a test message", user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/messages/9999/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            m = Message.query.get(9999)
            self.assertIsNone(m)

    def test_delete_unauthorized_message(self):
        """ Can a user delete another user's message """

        # A second user that will try to delete the message
        u = User.signup(username="evil-user",
                        email="evil@evil.com",
                        password="robotnik",
                        image_url=None)
        u.id = 66666

        #Message is owned by testuser
        m = Message(text="a test message", user_id=self.testuser_id)
        m.id = 77777
        db.session.add(m)
        db.session.add(u)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 66666

            response = c.post("/messages/77777/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

            m = Message.query.get(77777)
            self.assertIsNotNone(m)

    def test_delete_message_no_authentication(self):
        """ Can a logged-in user delete another user's message? """

        m = Message(id=1234, text="a test message", user_id=self.testuser_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            response = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)
