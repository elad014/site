import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'blueprints'))

from flask import Flask
from flask_login import LoginManager

from loginpage.login import login_bp
from signuppage.signup import signup_bp
from managerpage.manager_page import manager_bp
from stocks.stocks import stocks_bp
from db import DB_Config
from models import User

app = Flask(__name__)
app.secret_key = '456789'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login.login_page" # Redirect to login page if user is not authenticated
####################################
@login_manager.user_loader
def load_user(user_id):
    cursor = DB_Config.get_cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (int(user_id),))
    user_data = cursor.fetchone()
    cursor.close()
    if user_data:
        return User(user_data)
    return None
###########################################
app.register_blueprint(login_bp)
app.register_blueprint(signup_bp, url_prefix='/signup')
app.register_blueprint(manager_bp, url_prefix='/manager')
app.register_blueprint(stocks_bp, url_prefix='/stocks')

if __name__ == '__main__':
    ## start the server
    app.run(debug=True, host='0.0.0.0', port=5000)

