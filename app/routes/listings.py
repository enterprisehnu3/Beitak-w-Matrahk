from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import db, Listing, ListingImage, User, Favorite, Review, Booking, Transaction
from app.services.upload import save_upload
from sqlalchemy import or_
from app.constants import CITY_TRANSLATIONS, GENDER_TRANSLATIONS, AMENITY_SYNONYMS
import os

listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/listings')
def browse():
    city = request.args.get('city')
    q = request.args.get('q')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    rental_period = request.args.get('rental_period')
    gender = request.args.get('gender')
    listing_types = request.args.getlist('type')
    
    query = Listing.query.filter_by(is_active=True)
    
    if city and city != "":
        query = query.filter(Listing.city == city)
        
    if q and q != "":
        search_terms = {q.lower()}
        # Check for Arabic translations to include English DB values
        for eng, ara in CITY_TRANSLATIONS.items():
            if q in ara or ara in q:
                search_terms.add(eng.lower())
        for eng, ara in GENDER_TRANSLATIONS.items():
            if q in ara or ara in q:
                search_terms.add(eng.lower())
        
        # Check for Amenity Synonyms
        for eng, synonyms in AMENITY_SYNONYMS.items():
            if any(syn in q for syn in synonyms) or q in synonyms:
                search_terms.add(eng.lower())
                # Also add the synonyms themselves to broaden search
                for s in synonyms:
                    search_terms.add(s.lower())
        
        # Build OR filter for all terms across all relevant fields
        conditions = []
        for term in search_terms:
            conditions.extend([
                Listing.title.contains(term),
                Listing.description.contains(term),
                Listing.area.contains(term),
                Listing.city.contains(term),
                Listing.type.contains(term),
                Listing.rules.contains(term),
                Listing.amenities.contains(term),
                Listing.gender_req.contains(term)
            ])
            # Search in owner username
            conditions.append(Listing.owner.has(User.username.contains(term)))
            
            # If term is a number, search in price
            if term.isdigit():
                conditions.append(Listing.price == int(term))
                
        query = query.filter(or_(*conditions))
        
    if price_min and price_min != "":
        try:
            query = query.filter(Listing.price >= int(price_min))
        except ValueError:
            pass
            
    if price_max and price_max != "":
        try:
            query = query.filter(Listing.price <= int(price_max))
        except ValueError:
            pass

    if rental_period and rental_period != "":
        query = query.filter(Listing.rental_period == rental_period)
        
    if listing_types:
        query = query.filter(Listing.type.in_(listing_types))
        
    if gender and gender != "":
        if gender == 'male':
             query = query.filter(Listing.gender_req.in_(['male', 'any']))
        elif gender == 'female':
             query = query.filter(Listing.gender_req.in_(['female', 'any']))
        
    # Amenities filter
    req_amenities = request.args.getlist('amenities')
    if req_amenities:
        for amen in req_amenities:
            query = query.filter(Listing.amenities.contains(amen))
            
    # Sorting logic
    sort_by = request.args.get('sort_by')
    if sort_by == 'price_asc':
        query = query.order_by(Listing.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Listing.price.desc())
    else: # newest or default
        query = query.order_by(Listing.created_at.desc())
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    paginated_listings = query.paginate(page=page, per_page=9)

    user_favorites = []
    if current_user.is_authenticated:
        user_favorites = [f.listing_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
    return render_template('listings/search.html', listings=paginated_listings.items, pagination=paginated_listings, user_favorites=user_favorites)

@listings_bp.route('/listing/<int:id>')
def detail(id):
    listing = Listing.query.get_or_404(id)
    compatibility = "N/A"
    is_favorited = False
    
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(user_id=current_user.id, listing_id=id).first() is not None
        
        if current_user.role in ['student', 'employee']:
            score = listing.compatibility_with(current_user)
            compatibility = f"{score}%"
    
    avg_rating = listing.average_rating

    listing.views += 1
    db.session.commit()
        
    return render_template('listings/detail.html', listing=listing, compatibility=compatibility, is_favorited=is_favorited, avg_rating=avg_rating)

@listings_bp.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'homeowner':
        flash('يجب أن تكون صاحب سكن لإضافة إعلان', 'warning')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        city = request.form.get('city')
        area = request.form.get('area')
        description = request.form.get('description')
        listing_type = request.form.get('type')
        gender_req = request.form.get('gender_req')
        rental_period = request.form.get('rental_period')
        
        if not title or not price or not city or not area or not description or not listing_type or not gender_req or not rental_period:
            flash('يرجى ملء جميع الحقول الإلزامية (الوصف التفصيلي إجباري)', 'danger')
            return redirect(url_for('listings.create'))

        files = request.files.getlist('images') if 'images' in request.files else []
        valid_files = [f for f in files if f and f.filename != '']
        if not valid_files:
            flash('يجب رفع صورة واحدة على الأقل للإعلان', 'danger')
            return redirect(url_for('listings.create'))

        new_listing = Listing(
            owner_id=current_user.id,
            title=title,
            price=price,
            city=city,
            area=area,
            description=description,
            type=listing_type,
            gender_req=gender_req,
            rental_period=rental_period,
            amenities=",".join(request.form.getlist('amenities')),
            latitude=request.form.get('latitude', type=float),
            longitude=request.form.get('longitude', type=float)
        )
        db.session.add(new_listing)
        db.session.flush() # To get listing.id

        # Handle image uploads
        for file in valid_files:
            img_path = save_upload(file, subfolder='listings')
            if img_path:
                img = ListingImage(listing_id=new_listing.id, image_path=img_path)
                db.session.add(img)

        try:
            db.session.commit()
            flash('تم إضافة الإعلان بنجاح، بانتظار الموافقة', 'success')
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء حفظ الإعلان، يرجى المحاولة مرة أخرى', 'danger')
            return redirect(url_for('listings.create'))
            
        return redirect(url_for('dashboard.index'))
        
    return render_template('listings/create.html')

@listings_bp.route('/edit_listing/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    listing = Listing.query.get_or_404(id)
    if listing.owner_id != current_user.id and current_user.role != 'admin':
        flash('غير مصرح لك بتعديل هذا الإعلان', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        # Handle existing image deletion
        if 'delete_image' in request.form:
            image_id = request.form.get('delete_image')
            image_to_delete = ListingImage.query.get(image_id)
            if image_to_delete and (image_to_delete.listing_id == listing.id or current_user.role == 'admin'):
                total_images = ListingImage.query.filter_by(listing_id=listing.id).count()
                if total_images <= 1:
                    flash('لا يمكن حذف الصورة الأخيرة. يجب أن يحتوي الإعلان على صورة واحدة على الأقل.', 'danger')
                    return redirect(url_for('listings.edit', id=id))
                db.session.delete(image_to_delete)
                db.session.commit()
                flash('تم حذف الصورة بنجاح', 'info')
                return redirect(url_for('listings.edit', id=id))

        title = request.form.get('title')
        price = request.form.get('price')
        city = request.form.get('city')
        area = request.form.get('area')
        description = request.form.get('description')
        listing_type = request.form.get('type')
        gender_req = request.form.get('gender_req')
        rental_period = request.form.get('rental_period')
        
        if not title or not price or not city or not area or not description or not listing_type or not gender_req or not rental_period:
            flash('يرجى ملء جميع الحقول الإلزامية (الوصف التفصيلي إجباري)', 'danger')
            return redirect(url_for('listings.edit', id=id))

        listing.title = title
        listing.price = price
        listing.city = city
        listing.area = area
        listing.description = description
        listing.type = listing_type
        listing.gender_req = gender_req
        listing.rental_period = rental_period
        listing.latitude = request.form.get('latitude', type=float)
        listing.longitude = request.form.get('longitude', type=float)
        listing.amenities = ",".join(request.form.getlist('amenities'))
        
        # Handle new image uploads
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename != '':
                    img_path = save_upload(file, subfolder='listings')
                    if img_path:
                        img = ListingImage(listing_id=listing.id, image_path=img_path)
                        db.session.add(img)

        try:
            db.session.commit()
            flash('تم تحديث الإعلان بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث الإعلان', 'danger')
            
        return redirect(url_for('dashboard.index'))

    return render_template('listings/edit.html', listing=listing)

@listings_bp.route('/delete_listing/<int:id>', methods=['POST'])
@login_required
def delete(id):
    listing = Listing.query.get_or_404(id)
    if listing.owner_id != current_user.id and current_user.role != 'admin':
        flash('غير مصرح لك بحذف هذا الإعلان', 'danger')
        return redirect(url_for('dashboard.index'))

    # Manual cleanup for transactions related to bookings of this listing
    booking_ids = [b.id for b in listing.bookings]
    if booking_ids:
        Transaction.query.filter(Transaction.booking_id.in_(booking_ids)).delete(synchronize_session=False)

    # Everything else is handled by cascade='all, delete-orphan'
    db.session.delete(listing)
    db.session.commit()
    flash('تم حذف الإعلان بنجاح', 'success')
    return redirect(url_for('dashboard.index'))

@listings_bp.route('/favorites')
@login_required
def favorites_page():
    my_favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/user_favorites.html', favorites=my_favorites)

@listings_bp.route('/listing/<int:listing_id>/review', methods=['POST'])
@login_required
def submit_review(listing_id):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    # Secure: only if had a confirmed booking
    booking = Booking.query.filter_by(listing_id=listing_id, tenant_id=current_user.id, status='confirmed').first()
    if not booking:
        flash('يجب أن يكون لديك حجز مؤكد لتتمكن من إضافة تقييم', 'danger')
        return redirect(url_for('listings.detail', id=listing_id))
        
    review = Review(listing_id=listing_id, author_id=current_user.id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash('تم إضافة تقييمك بنجاح', 'success')
    return redirect(url_for('listings.detail', id=listing_id))
@listings_bp.route('/toggle_favorite/<int:listing_id>', methods=['POST'])
@login_required
def toggle_favorite(listing_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, listing_id=listing_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return {"status": "removed"}
    else:
        new_fav = Favorite(user_id=current_user.id, listing_id=listing_id)
        db.session.add(new_fav)
        db.session.commit()
        return {"status": "added"}
