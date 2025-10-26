from flask import render_template, Blueprint, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required

from db.db import DB_Config
from models import User
from utils.utils import Logger

logger = Logger.setup_logger(__name__)

login_bp = Blueprint('login', __name__, template_folder='templates')

@login_bp.route('/')
def login_page():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect(url_for('login.login_page'))

    try:
        cursor = DB_Config.get_cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            user = User(user_data)
            if check_password_hash(user.password_hash, password):
                login_user(user)
                logger.info(f"Login successful for user: {email}")
                flash("Login successful!", "success")
                return redirect(url_for('stocks.stocks'))
            else:
                logger.warning(f"Invalid password for user: {email}")
                flash("Invalid password, please try again.", "error")
        else:
            logger.warning(f"User not found: {email}")
            flash("User not found. Please check your email or sign up.", "error")
        
        return redirect(url_for('login.login_page'))

    except Exception as e:
        logger.error(f"Login error: {e}")
        flash("An error occurred during login, please try again.", "error")
        return redirect(url_for('login.login_page'))

@login_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('login.login_page'))
