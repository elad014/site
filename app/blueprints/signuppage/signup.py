from flask import Flask,render_template, Blueprint,redirect,url_for,request,flash 
from db import DB_Config, DB_Manager
from utils import Logger
import logging
from werkzeug.security import generate_password_hash, check_password_hash

signup_bp = Blueprint('signup',__name__,template_folder= 'templates')
logger = logging.getLogger(__name__)

@signup_bp.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        print("=== DEBUG: SIGNUP ATTEMPT ===")
        try:
            # Debug: Print before getting connection
            print("DEBUG: Getting database connection...")
            cursor = DB_Config.get_cursor()
            db_manager = DB_Manager(cursor)
            print("DEBUG: Database connection successful")
            
            # Get form data
            print("DEBUG: Getting form data...")
            data = {
                'user_id': request.form.get('user_id'),
                'email': request.form.get('email'),
                'full_name': request.form.get('full_name'),
                'phone_number': request.form.get('phone_number'),
                'password': generate_password_hash(request.form.get('password')),
                'country': request.form.get('country'),
                'user_type': 0
            }
            
            print("DEBUG: Form data collected:")
            for key, value in data.items():
                if key == 'password':
                    print(f"DEBUG:   {key}: [HASHED PASSWORD]")
                else:
                    print(f"DEBUG:   {key}: {value}")
            
            # Debug: Check if users table exists and print current users
            print("DEBUG: Checking current users before insert...")
            DB_Config.debug_users()
            
            print("DEBUG: Attempting to insert new user...")
            # Insert new user
            db_manager.insert_record('users', data)
            cursor.connection.commit()
            print("DEBUG: User insert successful!")
            
            # Debug: Print users after insert
            print("DEBUG: Checking users after insert...")
            DB_Config.debug_users()
            
            print("DEBUG: Redirecting to login page...")
            flash("Account created successfully! Please login.", "success")
            return redirect("/")
            
        except Exception as e:
            print(f"DEBUG ERROR: Exception during signup: {e}")
            print(f"DEBUG ERROR: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG ERROR: Traceback: {traceback.format_exc()}")
            logger.error(f"Signup error: {e}")
            flash("Error creating account. Please try again.", "error")
            return redirect(url_for('signup.signup'))
        finally:
            try:
                cursor.close()
                print("DEBUG: Database connection closed")
            except:
                print("DEBUG: Error closing database connection")
        print("=== END DEBUG SIGNUP ===")
    
    return render_template('signup.html')