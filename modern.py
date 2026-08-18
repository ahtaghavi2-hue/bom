"""ماژول رابط کاربری مدرن - فایل موقت برای اجرای مهاجرت"""
from flask import Blueprint, render_template

modern_bp = Blueprint('modern', __name__, url_prefix='/modern')

@modern_bp.route('/')
def dashboard():
    return render_template('modern/dashboard.html')
