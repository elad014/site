from flask import Flask,render_template, Blueprint,redirect,url_for, request, flash, session
from db import DB_Config, DB_Manager
from utils import Logger
from stocks.stocks import Stock

logger = Logger.setup_logger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
login_bp = Blueprint('login',__name__,template_folder= 'templates')

def get_stocks_data():
    """Fetch stocks data from the database"""
    try:
        cursor = DB_Config.get_cursor()
        cursor.execute("SELECT * FROM stocks ORDER BY id DESC LIMIT 10")
        stocks = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, stock)) for stock in stocks]
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        return []
    finally:
        cursor.close()

@login_bp.route('/')
def login_page():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        cursor = DB_Config.get_cursor()
        db_manager = DB_Manager(cursor)
        
        # Check if user exists and password matches
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        
        if user:
            # Successful login
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login_page'))
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        flash('An error occurred during login', 'error')
        return redirect(url_for('login_page'))
    finally:
        cursor.close()

@app.route('/signup')
def signup_page():
    return render_template('signup.html')
