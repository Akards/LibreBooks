# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, session, redirect, url_for

# PostgreSQL IP address
IP_ADDR = "34.69.97.14"

# Create the application
app = Flask(__name__, template_folder='../templates')
app.secret_key=os.urandom(32)
#####################################################
# Database handling 
  
def connect_db():
    """Connects to the database."""
    debug("Connecting to DB.")
    conn = psycopg2.connect(host=IP_ADDR, user="postgres", password="rhodes", dbname="librabooks", 
        cursor_factory=psycopg2.extras.DictCursor)
    return conn
    
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'pg_db'):
        g.pg_db = connect_db()
    return g.pg_db
    
@app.teardown_appcontext
def close_db(error):
    """Closes the database automatically when the application
    context ends."""
    debug("Disconnecting from DB.")
    if hasattr(g, 'pg_db'):
        g.pg_db.close()

####################################################
# Routes
@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/portal")
def portal():
    db = get_db()
    cursor = db.cursor()
    user_type = str(session['type'])
    user_id = str(session['user'])
    user_id=user_id.replace("[","")
    user_id=user_id.replace("]","")
    if user_type == 'payer':
        cursor.execute("select full_name from payer where id=%s",[user_id])
    else:
        cursor.execute("select full_name from accountant where id=%s",[user_id])
    db.commit()
    name = cursor.fetchone()
    return render_template('portal.html', name=name[0])

#@app.route("/dump")
#def dump_entries():
#    db = get_db()
#    cursor = db.cursor()
#    cursor.execute('select id, date, title, content from entries order by date')
#    rows = cursor.fetchall()
#    output = ""
#    for r in rows:
#        debug(str(dict(r)))
#        output += str(dict(r))
#        output += "\n"
#    return "<pre>" + output + "</pre>"

@app.route("/logout")
def logout():
    session.pop('user',None)
    return render_template("logout.html")

@app.route("/payer_login", methods=['get', 'post'])
def payer_login():
    if "step" not in request.form:
        return render_template("payer_login.html", step="attempt")
    elif request.form["step"] == "account_lookup":
        debug("account_lookup")
        db = get_db()
        cursor = db.cursor()
        user = request.form["user"]
        cursor.execute("select * from payer where email=%s",[user])
        db.commit()
        rowlist = cursor.fetchall()
        if len(rowlist) == 0:
            debug(rowlist)
            return render_template("payer_login.html", step="not_user")
        else:
            db.commit()
            return render_template("payer_login.html", step="user", user=user)
    elif request.form["step"] == "test_pass":
        password=request.form["password"]
        user=request.form["user"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("select email from payer where email=%s and pass_hash=%s",[user,password])
        db.commit()
        rowlist = cursor.fetchall()
        if len(rowlist) == 0:
            debug("does not exist")
            return render_template("payer_login.html", step="not_password", user=user)
        else:
            debug("exists")
            cursor.execute("select id from payer where email=%s and pass_hash=%s",[user,password])
            db.commit()
            id = cursor.fetchone()
            session['logged on'] = True
            session['user'] = id
            session['type'] = "payer"
            return redirect(url_for("portal"))


@app.route("/acountant_login", methods=['get', 'post'])
def accountant_login():
    if "step" not in request.form:
        return render_template("accountant_login.html", step="attempt")
    elif request.form["step"] == "account_lookup":
        debug("account_lookup")
        db = get_db()
        cursor = db.cursor()
        user = request.form["user"]
        cursor.execute("select email from accountant where email=%s",[user])
        db.commit()
        rowlist = cursor.fetchall()
        if len(rowlist) == 0:
            debug(rowlist)
            return render_template("accountant_login.html", step="not_user")
        else:
            db.commit()
            return render_template("accountant_login.html", step="user", user=user)
    elif request.form["step"] == "test_pass":
        password=request.form["password"]
        user=request.form["user"]
        db = get_db()
        cursor = db.cursor()
        #user = request.form["user"]
        cursor.execute("select email from accountant where email=%s and pass_hash=%s",[user,password])
        db.commit()
        rowlist = cursor.fetchall()
        if len(rowlist) == 0:
            debug("does not exist")
            return render_template("accountant_login.html", step="not_password", user=user)
        else:
            cursor.execute("select id from accountant where email=%s and pass_hash=%s",[user,password])
            db.commit()
            id = cursor.fetchone()
            session['logged on'] = True
            session['user'] = id
            session['type'] = "accountant"
            return redirect(url_for("portal"))
######################################################
# Command line utilities

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().execute(f.read())
    db.commit()

@app.cli.command('initdb')
def init_db_command():
    """Initializes the database."""
    print("Initializing DB.")
    init_db()
    
def populate_db():
    db = get_db()
    with app.open_resource('populate.sql', mode='r') as f:
        db.cursor().execute(f.read())
    db.commit()

@app.cli.command('populate')
def populate_db_command():
    """Populates the database with sample data."""
    print("Populating DB with sample data.")
    populate_db()




#####################################################
# Debugging

def debug(s):
    """Prints a message to the screen (not web browser) 
    if FLASK_DEBUG is set."""
    if app.config['DEBUG']:
        print(s)
