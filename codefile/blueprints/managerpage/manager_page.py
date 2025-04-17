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
    # tbd - enter name to a new row in the db
    conn = psycopg2.connect(dbname=DB_NAME)
    # Create a cursor object
    cur = conn.cursor()
    name = "Sharon"
    cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING id;", (name,))
    inserted_id = cur.fetchone()[0]
    # Commit the transaction
    conn.commit()
    # Fetch all rows from the 'users' table
    cur.execute("SELECT * FROM users;")
    rows = cur.fetchall()

    # Print the rows (table content)
    print("\nTable Content:")
    for row in rows:
        print(row)

    # Close the cursor and connection
    cur.close()
    conn.close()
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
