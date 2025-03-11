import os
from flask import render_template, Blueprint
from codefile.util import Util

manager_bp = Blueprint('manager',__name__,template_folder= 'templates')

@manager_bp.route('/')
def ManagerPage():
    print("Inside ManagerPage function!")  # Debugging print
    version = Util.read_version()
    log = Util.read_log()
    print(f"Version: {version}, Log: {log}")  # Debugging print
    return render_template("manager.html", version=version, log=log)


@manager_bp.route('/clean_log', methods=['POST'])
def clean_log():
    Util.clean_log()
    return {'message': 'Git update successful'}, 200

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
