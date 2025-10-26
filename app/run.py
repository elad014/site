import os
import sys

# Add project root and blueprints to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Parent directory
sys.path.insert(0, project_root)  # Add project root for 'db' module
sys.path.append(os.path.join(current_dir, 'blueprints'))  # Add blueprints

from flask import Flask
from flask_login import LoginManager

from app.blueprints.loginpage.login import login_bp
from app.blueprints.signuppage.signup import signup_bp
from app.blueprints.managerpage.manager_page import manager_bp
from app.blueprints.stocks.stocks import stocks_bp
from db.db import DB_Config
from app.models import User

app = Flask(__name__)
app.secret_key = '456789'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login.login_page" # Redirect to login page if user is not authenticated

@login_manager.user_loader
def load_user(user_id):
    cursor = DB_Config.get_cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (int(user_id),))
    user_data = cursor.fetchone()
    cursor.close()
    if user_data:
        return User(user_data)
    return None

app.register_blueprint(login_bp)
app.register_blueprint(signup_bp, url_prefix='/signup')
app.register_blueprint(manager_bp, url_prefix='/manager')
app.register_blueprint(stocks_bp, url_prefix='/stocks')

if __name__ == '__main__':
    ## MR-2 
    app.run(debug=True, host='0.0.0.0', port=8080)

