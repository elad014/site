from flask import Flask,render_template, Blueprint,redirect,url_for,request,flash
from db import DB_Config, DB_Manager
from utils import Logger

signup_bp = Blueprint('signup',__name__,template_folder= 'templates')

@signup_bp.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            cursor = DB_Config.get_cursor()
            db_manager = DB_Manager(cursor)
            
            # Get form data
            data = {
                'email': request.form.get('email'),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'phone_number': request.form.get('phone_number'),
                'password': request.form.get('password'),
                'user_type': request.form.get('user_type')
            }
            
            # Insert new user
            db_manager.insert_record('users', data)
            cursor.connection.commit()
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login.login_page'))
            
        except Exception as e:
            logger.error(f"Signup error: {e}")
            flash('An error occurred during signup', 'error')
            return redirect(url_for('login.signup'))
        finally:
            cursor.close()
    
    return render_template('signup.html')