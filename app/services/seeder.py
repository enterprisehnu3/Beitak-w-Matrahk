from app.models import db, User, Listing, ListingImage, Booking
from datetime import datetime

def seed_data():
    if User.query.first():
        # Check if listings exist, if not add them
        if Listing.query.count() == 0:
            pass # proceed to add listings
        else:
            return

    # Create dummy users if not exist
    if not User.query.filter_by(email='admin@beitak.com').first():
        admin = User(username='admin', email='admin@beitak.com', role='admin', is_verified=True)
        admin.set_password('admin123')
        db.session.add(admin)
    
    owner = User.query.filter_by(email='owner@beitak.com').first()
    if not owner:
        owner = User(username='Ahmed Owner', email='owner@beitak.com', role='homeowner', is_verified=True, smoker=False, sleep_schedule='early')
        owner.set_password('123456')
        db.session.add(owner)
    
    student = User.query.filter_by(email='ali@beitak.com').first()
    if not student:
        student = User(username='Ali Student', email='ali@beitak.com', role='student', is_verified=True, smoker=False, sleep_schedule='early', gender='male')
        student.set_password('123456')
        db.session.add(student)
    
    db.session.commit()
    
    # Create dummy listings
    l1 = Listing(
        owner_id=owner.id,
        title='غرفة مفروشة لوكس بمدينة نصر',
        city='Cairo',
        area='Nasr City',
        price=3500,
        type='room',
        description='غرفة ماستر بحمام خاص في شقة مودرن بمدينة نصر الحي السابع. تشطيب الترا سوبر لوكس، فرش جديد، مكيفة. الشقة بها مطبخ مجهز بالكامل وغسالة وثلاجة. انترنت سريع. العمارة بها اسانسير وأمن 24 ساعة.',
        gender_req='male',
        is_active=True,
        available_places=1,
        rental_period='monthly',
        latitude=30.0561,
        longitude=31.3323,
        amenities="wifi,ac,kitchen,elevator"
    )
    
    l2 = Listing(
        owner_id=owner.id,
        title='سرير في غرفة مزدوجة بالدقي',
        city='Giza',
        area='Dokki',
        price=1500,
        type='bed',
        description='استضافة سريعة للطالبات او المغتربات لظروف الامتحانات او العمل. شقة هادئة ونظيفة جداً بجوار محطة المترو. متاح الحجز بالأسبوع.',
        gender_req='female',
        is_active=True,
        available_places=2,
        rental_period='weekly',
        latitude=30.0382,
        longitude=31.2114,
        amenities="wifi,hot_water,kitchen"
    )

    db.session.add_all([l1, l2])
    db.session.commit()

    # Add realistic images (Using local files for stability)
    # Bedroom 1
    if ListingImage.query.count() == 0:
        img1 = ListingImage(listing_id=l1.id, image_path='/static/uploads/room1.jpg')
        img1_2 = ListingImage(listing_id=l1.id, image_path='/static/uploads/room2.jpg')
        
        # Bedroom 2 (Shared)
        img2 = ListingImage(listing_id=l2.id, image_path='/static/uploads/room4.jpg')
        img2_2 = ListingImage(listing_id=l2.id, image_path='/static/uploads/room3.jpg')

        db.session.add_all([img1, img1_2, img2, img2_2])
        db.session.commit()
