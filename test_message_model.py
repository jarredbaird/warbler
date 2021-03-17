"""Message model tests."""

# python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# connect to TEST DATABASE!! don't wanna mess up production
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# NOW connect to app.py
from app import app

# NOW we can do some DAMAGE!
db.create_all()

class MessageModelTestCase(TestCase):

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 1234567
        u = User.signup("tester", "butt@buttface.com", "password...original, right?", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        meh = super().tearDown()
        db.session.rollback()
        return meh
    
    def test_user_repr(self):
        m = Message(text="poop", user_id=1234567)
        db.session.add(m)
        db.session.commit()
        self.assertEqual(m.user, self.u)

    def test_text_len(self):
        m = Message(text=''.join(['a' for r in range(0,141)]), user_id=1234567)
        db.session.add(m)
        self.assertRaises(exc.DataError, db.session.commit)