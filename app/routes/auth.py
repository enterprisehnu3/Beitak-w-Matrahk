from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Booking, Listing, Notification
from app.services.upload import save_upload
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember-me') else False
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Check ban status
            if user.banned_until and user.banned_until > datetime.utcnow():
                is_permanent = user.banned_until.year == 9999
                banned_until_str = 'دائم' if is_permanent else user.banned_until.strftime('%Y-%m-%d — %H:%M UTC')
                # ISO format for JS countdown
                banned_until_iso = '' if is_permanent else user.banned_until.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                return render_template(
                    'auth/banned.html',
                    is_permanent=is_permanent,
                    banned_until_str=banned_until_str,
                    banned_until_iso=banned_until_iso,
                    ban_reason=user.ban_reason or 'مخالفة سياسة المنصة'
                )

            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
                
            if user.role == 'pending':
                return redirect(url_for('auth.selfie_verification'))
            return redirect(url_for('dashboard.index'))
            
        flash('بيانات الدخول غير صحيحة، يرجى التأكد من البريد الإلكتروني وكلمة المرور', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    from flask import session, make_response
    logout_user()
    session.clear()
    
    response = make_response(redirect(url_for('main.index')))
    # Explicitly clear the session cookie
    response.set_cookie('session', '', expires=0)
    # Prevent browser caching of the previous authenticated state
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    flash('تم تسجيل الخروج بنجاح. نراك قريباً!', 'info')
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        national_id_number = request.form.get('national_id_number')
        
        # Basic Validation
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not national_id_number:
            flash('يرجى ملء جميع الحقول المطلوبة', 'warning')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('كلمة المرور يجب أن لا تقل عن 8 أحرف', 'warning')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'warning')
            return redirect(url_for('auth.register'))

        if len(national_id_number) != 14:
            flash('رقم البطاقة يجب أن يكون 14 رقماً', 'warning')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مسجل بالفعل', 'warning')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مسجل بالفعل، يرجى اختيار اسم آخر', 'warning')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(national_id_number=national_id_number).first():
            flash('رقم البطاقة مسجل بالفعل', 'warning')
            return redirect(url_for('auth.register'))

        if 'id_card' not in request.files or request.files['id_card'].filename == '':
            flash('يجب رفع صورة بطاقة الرقم القومي لإتمام التسجيل', 'danger')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            username=username, 
            email=email, 
            role='pending', 
            national_id_number=national_id_number,
            gender=request.form.get('gender'),
            occupation=request.form.get('occupation')
        )
        new_user.set_password(password)

        # Use upload service
        if 'id_card' in request.files:
            file = request.files['id_card']
            img_path = save_upload(file, subfolder='ids')
            if img_path:
                new_user.national_id_image = img_path

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        # Redirect to the new selfie verification step
        return redirect(url_for('auth.selfie_verification'))
        
    return render_template('auth/register.html')

@auth_bp.route('/selfie_verification', methods=['GET', 'POST'])
@login_required
def selfie_verification():
    # Only pending users who haven't uploaded a selfie yet should access this
    if current_user.role != 'pending' and current_user.id_selfie_image:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        id_selfie = request.form.get('id_selfie')
        if not id_selfie:
            flash('يجب التقاط صورة سيلفي مع البطاقة لإتمام التوثيق', 'danger')
            return redirect(url_for('auth.selfie_verification'))
            
        if ',' in id_selfie:
            import base64
            import uuid
            import os
            from flask import current_app
            from werkzeug.utils import secure_filename
            
            try:
                header, encoded = id_selfie.split(',', 1)
                data = base64.b64decode(encoded)
                filename = secure_filename(f"{uuid.uuid4().hex}_selfie.jpg")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ids')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(data)
                    
                current_user.id_selfie_image = f"uploads/ids/{filename}"
                db.session.commit()
                
                # Proceed to role selection
                return redirect(url_for('auth.choose_role'))
                
            except Exception as e:
                current_app.logger.error(f"Failed to process selfie: {e}")
                flash('حدث خطأ أثناء معالجة صورة السيلفي، يرجى المحاولة مرة أخرى', 'danger')
                return redirect(url_for('auth.selfie_verification'))

    return render_template('auth/selfie_verification.html')

@auth_bp.route('/choose-role', methods=['GET', 'POST'])
@login_required
def choose_role():
    if request.method == 'POST':
        role_choice = request.form.get('role_choice') # homeowner, student, employee
        if role_choice == 'tenant':
            role_choice = 'student'
            
        if role_choice in ['homeowner', 'student', 'employee']:
            current_user.role = role_choice
            db.session.commit()
            flash('تم تعيين دور الحساب بنجاح!', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('auth/choose_role.html')

@auth_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    confirmed_tenant_bookings = Booking.query.filter(Booking.tenant_id == user.id, Booking.status.in_(['confirmed', 'completed'])).count()
    
    user_listings = []
    owner_bookings_count = 0
    if user.role == 'homeowner':
        user_listings = Listing.query.filter_by(owner_id=user.id, is_active=True).all()
        owner_bookings_count = Booking.query.join(Listing).filter(Listing.owner_id == user.id, Booking.status.in_(['confirmed', 'completed'])).count()
        
    return render_template('auth/profile.html', user=user, confirmed_tenant_bookings=confirmed_tenant_bookings, owner_bookings_count=owner_bookings_count, user_listings=user_listings)

@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Handle regular profile fields
        current_user.smoker = True if request.form.get('smoker') == 'true' else False
        current_user.sleep_schedule = request.form.get('sleep_schedule')
        current_user.personality = request.form.get('personality')
        current_user.occupation = request.form.get('occupation')
        
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                # Validate extension
                allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if ext not in allowed_extensions:
                    flash('عذراً، التنسيقات المسموح بها هي: PNG, JPG, JPEG, WEBP فقط', 'danger')
                    return redirect(url_for('auth.edit_profile'))
                
                img_path = save_upload(file, subfolder='profiles')
                if img_path:
                    current_user.profile_image = img_path
                    
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('auth.view_profile', user_id=current_user.id))
        
    return render_template('auth/edit_profile.html')

@auth_bp.route('/delete-profile-image', methods=['POST'])
@login_required
def delete_profile_image():
    if current_user.profile_image:
        import os
        from flask import current_app
        try:
            # Safely attempt to delete the physical file if it exists
            rel_path = current_user.profile_image.lstrip('/')
            if rel_path.startswith('static/uploads/'):
                full_path = os.path.join(current_app.root_path, '..', rel_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    os.remove(full_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting profile image file: {e}")
            
        current_user.profile_image = None
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف الصورة الشخصية بنجاح'})
    return jsonify({'success': False, 'message': 'لا توجد صورة شخصية لحذفها'}), 400

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('كلمة المرور الحالية غير صحيحة', 'danger')
        return redirect(url_for('auth.edit_profile'))
        
    if new_password != confirm_password:
        flash('كلمة المرور الجديدة غير متطابقة', 'danger')
        return redirect(url_for('auth.edit_profile'))
        
    if len(new_password) < 8:
        flash('كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل', 'danger')
        return redirect(url_for('auth.edit_profile'))
        
    current_user.set_password(new_password)
    db.session.commit()
    flash('تم تغيير كلمة المرور بنجاح', 'success')
    return redirect(url_for('auth.edit_profile'))

@auth_bp.route('/reupload-id', methods=['GET', 'POST'])
@login_required
def reupload_id():
    # Only allow if ID is actually rejected
    if not current_user.id_rejected:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        if 'id_card' not in request.files or request.files['id_card'].filename == '':
            flash('يجب رفع صورة البطاقة الجديدة', 'danger')
            return redirect(url_for('auth.reupload_id'))
            
        file = request.files['id_card']
        img_path = save_upload(file, subfolder='ids')
        if img_path:
            current_user.national_id_image = img_path
            # Reset verification status
            current_user.id_rejected = False
            current_user.is_verified = False
            db.session.commit()
            
            flash('تم رفع صورة البطاقة بنجاح، يرجى الانتظار لحين مراجعتها من الإدارة.', 'success')
            return redirect(url_for('dashboard.index'))
            
    return render_template('auth/reupload_id.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Here you would typically send an email with a reset token.
            # For now, we'll just show a success message to complete the flow.
            flash('تم إرسال تعليمات إعادة تعيين كلمة المرور إلى بريدك الإلكتروني (تأكد من مجلد الرسائل غير المرغوب فيها).', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('هذا البريد الإلكتروني غير مسجل لدينا.', 'danger')
            return redirect(url_for('auth.forgot_password'))
            
    return render_template('auth/forgot_password.html')
