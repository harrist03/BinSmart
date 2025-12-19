from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    google_id = db.Column(db.String(255), unique=True)
    is_admin = db.Column(db.Boolean, default=False)

def get_or_create_user(google_id, email, username):
    # check if user exists
    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            username=username,
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
    
    return user

class Bin(db.Model):
    __tablename__ = 'bin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Float, nullable=False)
    is_full = db.Column(db.Boolean, default=False)

    def get_latest_reading(self):
        return BinReading.query.filter_by(bin_id=self.id).order_by(BinReading.timestamp.desc()).first()

class BinReading(db.Model):
    __tablename__ = 'binreading'
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.id'), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    bin = db.relationship('Bin', backref=db.backref('readings', cascade='all, delete-orphan'))

    @property
    def fill_level(self):
        return self.bin.capacity - self.distance
    
    @property
    def fill_percentage(self):
        if self.bin.capacity <= 0:
            return 0
        return (self.fill_level / self.bin.capacity) * 100
