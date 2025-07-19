import os
from flask import render_template, Blueprint
import psycopg2
from utils import Utils

# Database connection parameters
DB_NAME = "mydb"

manager_bp = Blueprint('manager',__name__,template_folder= 'templates')

@manager_bp.route('/')
def ManagerPage():    
    version = Utils.read_version()
    log = Utils.read_log()    
    return render_template("manager.html", version=version, log=log)


@manager_bp.route('/clean_log', methods=['POST'])
def clean_log():
    Utils.clean_log()
    return {'message': 'Log Cleaned Successfully'}, 200

@manager_bp.route('/git_update', methods=['POST'])
def git_update():
    print("[INFO] Update files from git w8 4 finish!!!")
    if is_production:
        os.system("cd /home/ubuntu/Desktop/site/codefile && git reset --hard HEAD  && git pull https://github.com/elad014/site.git main --progress")
    return {'message': 'Git update successful'}, 200

def is_production():
    try:
        with open("prodaction.txt",'r') as file:
            key = file.read()
        return key == 'yes'
    except:
        pass
