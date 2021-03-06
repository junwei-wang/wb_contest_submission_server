import time
import datetime
import sys
from enum import Enum, unique
from app import db
from app import login_manager
from passlib.hash import pbkdf2_sha256
from traceback import print_exc
from app import utils
from .whiteboxbreak import WhiteboxBreak
from .program import Program

class User(db.Model):

    #NBR_SECONDS_PER_DAY = 86400
    NBR_SECONDS_PER_DAY = 10

    _id = db.Column(db.Integer, primary_key=True)
    _email = db.Column(db.Text, nullable=False)
    _username = db.Column(db.String(64), index=True, unique=True)
    _password_hash = db.Column(db.String(256))
    _bananas = db.Column(db.BigInteger, default=None)
    _bananas_ranking = db.Column(db.BigInteger, default=None)
    _strawberries = db.Column(db.BigInteger, default=None)
    _strawberries_ranking = db.Column(db.BigInteger, default=None)
    programs = db.relationship('Program', backref='user')

    @property
    def bananas_ranking(self):
        return self._bananas_ranking

    @property
    def published_programs(self):
        return [p for p in self.programs if p.is_published]

    @property
    def strawberries_ranking(self):
        return self._strawberries_ranking

    @property
    def strawberries(self):
        return self._strawberries

    @property
    def bananas(self):
        return self._bananas

    @property
    def username(self):
        return self._username

    # The following properties are required by LoginManager

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self._id)

    def update_bananas(self, strawberries):
        if self._bananas is None or strawberries > self._bananas:
            self._bananas = strawberries
        User.refresh_all_banana_rankings()

    @staticmethod
    def refresh_all_banana_rankings():
        users = User.query.filter(User._bananas != None).order_by(User._bananas.desc()).all()
        if len(users) == 0:
            return
        users[0]._bananas_ranking = 1
        r = 1
        b = users[0]._bananas
        skipped = 0
        for user in users[1:]:
            if user._bananas < b:
                r += 1 + skipped
                skipped = 0
            else:
                skipped += 1
            user._bananas_ranking = r
            b = user._bananas

    @login_manager.user_loader
    def load_user(id):
        return User.query.filter(User._id==int(id)).first()

    def refresh_strawberries_count_and_rank(self):
        s = max([p.strawberries_peak for p in self.published_programs])
        if self._strawberries != s:
            self._strawberries = s
            User.refresh_all_strawberry_rankings()

    @staticmethod
    def refresh_all_strawberry_rankings():
        users = User.query.filter(User._strawberries != None).order_by(User._strawberries.desc()).all()
        if len(users) == 0:
            return
        users[0]._strawberries_ranking = 1
        r = 1
        b = users[0]._strawberries
        skipped = 0
        for user in users[1:]:
            if user._strawberries < b:
                r += 1 + skipped
                skipped = 0
            else:
                skipped += 1
            user._strawberries_ranking = r
            b = user._strawberries


    # User creation and password verification

    @staticmethod
    def create(username, password, email):
        password_hash=pbkdf2_sha256.hash(password)
        user = User(_username=username,
                    _password_hash=password_hash,
                    _email=email)
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def validate(username, password):
        user = User.query.filter(User._username==username).first()
        if user is not None and pbkdf2_sha256.verify(password, user._password_hash):
            return user
        else:
            return None

    @staticmethod
    def get(username):
        user = User.query.filter(User._username==username).first()
        return user

    @staticmethod
    def get_all_sorted_by_bananas():
        return User.query.filter(User._bananas_ranking != None).order_by(User._bananas.desc()).all()

    @staticmethod
    def get_total_number_of_users():
        return User.query.count()

    def verify(self, password):
        return pbkdf2_sha256.verify(password, self._password_hash)

    @staticmethod
    def _now():
        return int(time.time())

    def __repr__(self):
        return '<User %r>' % (self._username)
