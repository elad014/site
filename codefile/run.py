import os
import re

from flask import Flask, render_template
from blueprints.mainpage.main_page import main_bp
from blueprints.managerpage.manager_page import manager_bp

app = Flask(__name__)

app.register_blueprint(main_bp)
app.register_blueprint(manager_bp, url_prefix= '/manager')

if __name__ == '__main__':
    app.run(debug=True)