from flask import Flask, render_template, Blueprint, redirect, url_for, request, flash, session
from db import DB_Config, DB_Manager
from utils import Logger

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

logger = Logger.setup_logger(__name__)

login_bp = Blueprint('login', __name__, template_folder='templates')

@login_bp.route('/')
def login_page():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validate input
    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect(url_for('login.login_page'))
    
    try:
        cursor = DB_Config.get_cursor()
        
        # Get user by email
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Password is stored at index 2 in the users table
            stored_password = user[2]
            
            # Check if the password matches
            if check_password_hash(stored_password, password):
                logger.info(f"Login successful for user: {email}")
                flash("Login successful!", "success")
                return redirect(url_for('stocks.stocks'))
            else:
                logger.warning(f"Invalid password for user: {email}")
                flash("Invalid password, please try again.", "error")
                return redirect(url_for('login.login_page'))
        else:
            logger.warning(f"User not found: {email}")
            flash("User not found. Please check your email or sign up.", "error")
            return redirect(url_for('login.login_page'))
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        flash("An error occurred during login, please try again.", "error")
        return redirect(url_for('login.login_page'))
    finally:
        cursor.close()
