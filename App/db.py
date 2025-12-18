from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    google_id = db.Column(db.String(255), unique=True)

def get_or_create_user(google_id, email, username):
    # check if user exists
    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            username=username
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

class BinReading(db.Model):
    __tablename__ = 'binreading'
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.id'), nullable=False)
    distance = db.Column(db.Float, nullable=False)

    bin = db.relationship('Bin', backref=db.backref('readings', cascade='all, delete-orphan'))

    @property
    def fill_level(self):
        return self.bin.capacity - self.distance
    
    @property
    def fill_percentage(self):
        if self.bin.capacity <= 0:
            return 0
        return (self.fill_level / self.bin.capacity) * 100
