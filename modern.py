from flask import Blueprint, render_template
from flask_login import login_required
from models import Product

modern_bp = Blueprint('modern', __name__, url_prefix='/modern')


@modern_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('modern/dashboard.html')


@modern_bp.route('/products')
@login_required
def products():
    return render_template('modern/products.html')


@modern_bp.route('/parts')
@login_required
def parts():
    return render_template('modern/parts.html')


@modern_bp.route('/schedule')
@login_required
def schedule():
    return render_template('modern/schedule.html')


@modern_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('modern/product_detail.html', product=product)
