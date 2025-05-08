from flask import Flask,render_template, Blueprint,redirect,url_for, request, flash, session
from db import DB_Config, DB_Manager
from utils import Logger
from stocks.stocks import Stock

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print("im users", users)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        print("im user", user)  

        if user:            # Assuming the password is stored in the 5th column (adjust index if needed)
            stored_password = user[2]  # Make sure this index corresponds to the actual password field

            # Check if the password matches
            if check_password_hash(stored_password, password):
                print("Login successful")
                return redirect(url_for('stocks.stocks'))  # You might need to adjust this URL
            else:
                flash("Invalid password, please try again.", "error")
                return redirect(url_for('login.login_page'))  # Adjust if needed

        else:
            flash("User not found.", "error")
            return redirect(url_for('login.login_page'))  # Adjust if needed
            
    except Exception as e:
        print("Error:", e)
        flash("An error occurred, please try again.", "error")
        return redirect(url_for('login.login_page'))  # Adjust if needed

    finally:
        cursor.close()


@app.route('/signup')
def signup_page():
    return render_template('signup.html')
