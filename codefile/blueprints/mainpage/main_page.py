import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'blueprints'))

from flask import render_template, Blueprint,redirect,url_for
from blueprints.managerpage.manager_page import ManagerPage

main_bp = Blueprint('main',__name__,template_folder= 'templates')


@main_bp.route('/')
def home():
    return render_template("main.html")  # Serve main.html from templates/html/

@main_bp.route('/manager', methods=['GET', 'POST'])
def manager():
    return ManagerPage()