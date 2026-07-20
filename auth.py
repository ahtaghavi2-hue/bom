from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('modern/login.html')
    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False) == True or data.get('remember') == 'on'
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(email=username).first()
    if not user or not user.check_password(password):
        if request.is_json:
            return jsonify({'success': False, 'message': 'نام کاربری یا رمز عبور اشتباه است'}), 401
        flash('نام کاربری یا رمز عبور اشتباه است', 'error')
        return redirect(url_for('auth.login'))
    if not user.is_active_user:
        if request.is_json:
            return jsonify({'success': False, 'message': 'حساب کاربری غیرفعال است'}), 403
        flash('حساب کاربری غیرفعال است', 'error')
        return redirect(url_for('auth.login'))
    login_user(user, remember=remember)
    user.last_login = datetime.utcnow()
    db.session.commit()
    next_page = request.args.get('next') or url_for('index')
    if request.is_json:
        return jsonify({'success': True, 'redirect': next_page})
    return redirect(next_page)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('modern/register.html')
    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')
    if not username or not email or not password:
        if request.is_json:
            return jsonify({'success': False, 'message': 'لطفاً تمام فیلدها را پر کنید'}), 400
        flash('لطفاً تمام فیلدها را پر کنید', 'error')
        return redirect(url_for('auth.register'))
    if password != confirm:
        if request.is_json:
            return jsonify({'success': False, 'message': 'رمز عبور و تکرار آن مطابقت ندارند'}), 400
        flash('رمز عبور و تکرار آن مطابقت ندارند', 'error')
        return redirect(url_for('auth.register'))
    if User.query.filter_by(username=username).first():
        if request.is_json:
            return jsonify({'success': False, 'message': 'این نام کاربری قبلاً ثبت شده است'}), 400
        flash('این نام کاربری قبلاً ثبت شده است', 'error')
        return redirect(url_for('auth.register'))
    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'success': False, 'message': 'این ایمیل قبلاً ثبت شده است'}), 400
        flash('این ایمیل قبلاً ثبت شده است', 'error')
        return redirect(url_for('auth.register'))
    user = User(username=username, email=email, role='viewer')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'message': 'ثبت‌نام با موفقیت انجام شد'})
    flash('ثبت‌نام با موفقیت انجام شد. لطفاً وارد شوید.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'created_at': current_user.created_at.isoformat(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
    })
