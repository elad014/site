import os
import sys

from flask import render_template, Blueprint,redirect,url_for
from codefile.util import Util
from blueprints.managerpage.manager_page import ManagerPage

main_bp = Blueprint('main',__name__,template_folder= 'templates')

@main_bp.route('/')
def home():
    return render_template("main.html")  # Serve main.html from templates/html/

@main_bp.route('/goToManagerPage', methods=['GET', 'POST'])
def goToManagerPage():
    return ManagerPage()