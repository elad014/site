import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'blueprints'))
from flask import Flask, render_template
from mainpage.main_page import main_bp
from managerpage.manager_page import manager_bp

app = Flask(__name__)

app.register_blueprint(main_bp)
app.register_blueprint(manager_bp, url_prefix= '/manager')

if __name__ == '__main__':
    print("aa")
    print("aa")
    print("new")
    app.run(debug=True)
