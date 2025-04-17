import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'blueprints'))
from flask import Flask, render_template
from mainpage.main_page import main_bp
from managerpage.manager_page import manager_bp
from stocks.stocks import stocks_bp
from db import DB_Config

app = Flask(__name__)

app.register_blueprint(main_bp)
app.register_blueprint(manager_bp, url_prefix= '/manager')
app.register_blueprint(stocks_bp, url_prefix='/stocks')

if __name__ == '__main__':
    # Create a cursor and print table content
    DB_Config.print_table_content('stocks')
    
    app.run(debug=True, host='0.0.0.0', port=5000)

