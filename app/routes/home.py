from flask import Blueprint, render_template, redirect, url_for
from api.token_utils import is_logged_in

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    if is_logged_in():
        return redirect(url_for('employees.employees'))
    else:
        return render_template('home.html', logged_in=False)