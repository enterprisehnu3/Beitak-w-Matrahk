from app import create_app
from app.models import db, User, Listing, ListingImage

app = create_app()

with app.app_context():
    # نبحث عن صاحب الحساب أبو بكر
    owner = User.query.filter(User.username.like('%Abubakr%')).first()
    if not owner:
        print("Owner Abubakr not found!")
    else:
        print(f"Creating 5 listings for: {owner.username}...")
        
        listings_data = [
            {
                "title": "غرفة مفروشة ومريحة للطلاب",
                "city": "القاهرة",
                "area": "مدينة نصر",
                "price": 2500,
                "type": "room",
                "description": "غرفة مكيفة شاملة الإنترنت والكهرباء في موقع مميز بمدينة نصر. مناسبة للطلبة لوجود هدوء تام للمذاكرة.",
                "rules": "ممنوع التدخين، ممنوع اصطحاب الحيوانات الأليفة",
                "available_places": 1,
                "gender_req": "male",
                "rental_period": "monthly",
                "images": [
                    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1502672260266-1c1f52d36abf?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "title": "سرير في غرفة مشتركة بالقرب من المترو",
                "city": "الجيزة",
                "area": "الدقي",
                "price": 1200,
                "type": "bed",
                "description": "سرير متوفر في غرفة ثنائية بموقع حيوي جداً في الدقي، دقائق مشي من محطة مترو الدقي.",
                "rules": "مسموح بالتدخين في البلكونة فقط",
                "available_places": 1,
                "gender_req": "male",
                "rental_period": "monthly",
                "images": [
                    "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1540518614846-7eded433c457?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "title": "غرفة فندقية بحمام خاص",
                "city": "القاهرة",
                "area": "المعادي",
                "price": 4500,
                "type": "room",
                "description": "غرفة ماستر كبيرة جداً بحمام داخلي خاص، فرش مودرن وعمارة راقية بها أمن وكاميرات.",
                "rules": "غير مسموح بالتجمعات أو الحفلات للصوت العالي",
                "available_places": 1,
                "gender_req": "any",
                "rental_period": "monthly",
                "images": [
                    "https://images.unsplash.com/photo-1598928506311-c55d43f12711?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1628592102751-ba83b0314276?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "title": "شقة سكنية بالكامل لمشاركة الموظفين",
                "city": "القاهرة",
                "area": "التجمع الخامس",
                "price": 8000,
                "type": "shared_apartment",
                "description": "شقة مساحة 150 متر مكيفة بالكامل بإطلالة على حديقة، معروضة لللإيجار الشهري للموظفين والمهندسين.",
                "rules": "مطلوب الإلتزام بالهدوء التام والنظافة الأسبوعية للمكان",
                "available_places": 3,
                "gender_req": "male",
                "rental_period": "monthly",
                "images": [
                    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "title": "غرفة استضافة لفترة قصيرة",
                "city": "الإسكندرية",
                "area": "سموحة",
                "price": 500,
                "type": "room",
                "description": "غرفة ممتازة للطلبة أو المغتربين لمدة قصيرة (الأسعار بالإسبوع)، قريبة من الجامعة والخدمات.",
                "rules": "النظافة الشخصية ضرورة حتمية للمكان",
                "available_places": 1,
                "gender_req": "any",
                "rental_period": "weekly",
                "images": [
                    "https://images.unsplash.com/photo-1522771731470-ea433e4e81de?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"
                ]
            }
        ]

        for data in listings_data:
            new_listing = Listing(
                owner_id=owner.id,
                title=data["title"],
                city=data["city"],
                area=data["area"],
                price=data["price"],
                type=data["type"],
                description=data["description"],
                rules=data["rules"],
                available_places=data["available_places"],
                gender_req=data["gender_req"],
                rental_period=data["rental_period"],
                is_active=True # جعلنا الإعلان نشط وموافق عليه مباشراً لسهولة التجربة
            )
            db.session.add(new_listing)
            db.session.flush() # للحصول على الـ ID الخاص بالإعلان فوراً

            for img_url in data["images"]:
                img = ListingImage(listing_id=new_listing.id, image_path=img_url)
                db.session.add(img)

        # حفظ الكل في قاعدة البيانات
        db.session.commit()
        print("Data seeded successfully! Added 5 listings with 2 images each.")
