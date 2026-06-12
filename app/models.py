from datetime import datetime
# pyrefly: ignore [missing-import]
from flask_sqlalchemy import SQLAlchemy
# pyrefly: ignore [missing-import]
from flask_login import UserMixin
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=True) # Full Arabic double name
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'employee', 'homeowner', 'admin'
    profile_image = db.Column(db.String(256), nullable=True) # Path to profile picture
    national_id_image = db.Column(db.String(256), nullable=True) # Path to ID image
    id_selfie_image = db.Column(db.String(256), nullable=True) # Path to Live Selfie with ID
    is_verified = db.Column(db.Boolean, default=False)
    id_rejected = db.Column(db.Boolean, default=False)
    
    # Compatibility details
    gender = db.Column(db.String(10)) # 'male', 'female'
    smoker = db.Column(db.Boolean, default=False)
    sleep_schedule = db.Column(db.String(20)) # 'early', 'late'
    personality = db.Column(db.String(20)) # 'social', 'quiet'
    occupation = db.Column(db.String(20)) # 'student', 'employee'
    
    # New Fields based on Documentation
    reliability_score = db.Column(db.Integer, default=70) # 0-100 scale (70 is neutral)
    national_id_number = db.Column(db.String(14), unique=True, nullable=True) # Egyptian National ID is 14 digits
    wallet_balance = db.Column(db.Float, default=0.0) # Simulated wallet

    # Ban / Moderation fields
    banned_until = db.Column(db.DateTime, nullable=True)   # None = not banned; 9999-12-31 = permanent
    ban_reason   = db.Column(db.String(512), nullable=True)
    
    listings = db.relationship('Listing', backref='owner', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='tenant', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(50), nullable=False) # Cairo, Giza, etc.
    area = db.Column(db.String(100), nullable=False) # Neighborhood (e.g. Nasr City)
    price = db.Column(db.Integer, nullable=False) # In EGP
    type = db.Column(db.String(50), nullable=False) # 'room', 'bed', 'shared_apartment'
    description = db.Column(db.Text, nullable=False)
    rules = db.Column(db.Text) # Smoking allowed, pets, etc.
    
    # Details
    available_places = db.Column(db.Integer, default=1)
    gender_req = db.Column(db.String(10)) # 'male', 'female', 'any'
    is_active = db.Column(db.Boolean, default=True) # Published directly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rental_period = db.Column(db.String(20), default='monthly') # 'monthly' or 'weekly'
    
    # Map & Amenities
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    amenities = db.Column(db.String(500)) # "wifi,ac,kitchen..."
    views = db.Column(db.Integer, default=0) # Performance tracking
    
    images = db.relationship('ListingImage', backref='listing', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='listing', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='listing', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='listing', lazy=True, cascade='all, delete-orphan')

    def compatibility_with(self, user):
        if not user or not hasattr(user, 'role') or user.role not in ['student', 'employee']:
            return 0
        score = 50 
        if user.smoker == self.owner.smoker: 
            score += 10
        if user.sleep_schedule == self.owner.sleep_schedule:
            score += 10
        if user.gender == self.gender_req or self.gender_req == 'any':
            score += 30
        return score

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @property
    def amenities_list(self):
        if not self.amenities:
            return []
        return [a.strip() for a in self.amenities.split(',') if a.strip()]

class ListingImage(db.Model):
    __tablename__ = 'listing_images'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    image_path = db.Column(db.String(256), nullable=False)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, pending_approval, pending_payment, confirmed, rejected, completed, cancelled
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_date = db.Column(db.DateTime, nullable=True) # When the stay starts
    check_out_date = db.Column(db.DateTime, nullable=True) # When the stay ends
    arrival_time = db.Column(db.String(50), nullable=True) # Expected arrival time (e.g. 14:00)
    
    total_price = db.Column(db.Float, default=0.0)
    commission_fee = db.Column(db.Float, default=0.0)
    
    # Escrow Release fields
    payment_released = db.Column(db.Boolean, default=False)
    owner_payout_amount = db.Column(db.Float, default=0.0)
    payout_method = db.Column(db.String(50), nullable=True) # visa, instapay, vodafone_cash
    payout_details = db.Column(db.String(150), nullable=True) # Phone, instapay IPA, or IBAN/Visa number
    
    # Cancellation tracking
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.String(20), nullable=True) # 'tenant' or 'homeowner'
    penalty_applied = db.Column(db.Float, default=0.0)
    
    notes = db.Column(db.Text)

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    homeowner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    status = db.Column(db.String(20), default='open') # open, closed, blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = db.relationship('User', foreign_keys=[tenant_id], backref='conversations_as_tenant')
    homeowner = db.relationship('User', foreign_keys=[homeowner_id], backref='conversations_as_homeowner')
    listing = db.relationship('Listing', backref='conversations', lazy=True)
    booking = db.relationship('Booking', backref='conversations', lazy=True)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    __table_args__ = (db.UniqueConstraint('user_id', 'listing_id', name='unique_user_favorite'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = (db.UniqueConstraint('listing_id', 'author_id', name='unique_user_review'),)
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(256), nullable=True) # Optional link to a page
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications_list', lazy=True)

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    admin_replied_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='open') # open, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='tickets', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column('type', db.String(20), nullable=False) # payment, payout, penalty, refund
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='transactions', lazy=True)
    booking = db.relationship('Booking', backref='transactions', lazy=True)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, resolved, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_made')
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], backref='reports_received')

class UserBlock(db.Model):
    __tablename__ = 'user_blocks'
    __table_args__ = (db.UniqueConstraint('blocker_id', 'blocked_id', name='unique_user_block'),)
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    blocker = db.relationship('User', foreign_keys=[blocker_id], backref='blocks_made')
    blocked_user = db.relationship('User', foreign_keys=[blocked_id], backref='blocked_by_users')
