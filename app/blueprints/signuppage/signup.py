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
        try:
            cursor = DB_Config.get_cursor()
            db_manager = DB_Manager(cursor)
            
            # Get form data
            data = {
                'user_id': request.form.get('user_id'),
                'email': request.form.get('email'),
                'full_name': request.form.get('full_name'),
                'phone_number': request.form.get('phone_number'),
                'password': generate_password_hash(request.form.get('password')),
                'country': request.form.get('country'),
                'user_type': 0
            }
            
            # Insert new user
            db_manager.insert_record('users', data)
            cursor.connection.commit()
            
            return redirect("/")
            
        except Exception as e:
            print(e)
            return redirect(url_for('signup.signup'))
        finally:
            cursor.close()
    
    return render_template('signup.html')