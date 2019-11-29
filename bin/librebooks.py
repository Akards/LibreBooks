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

####################################################
# Routes

@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/portal")
def portal():
    if session['logged on'] == True:
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
    else:
        return render_template("home.html")

@app.route("/logout")
def logout():
    session.pop('user',None)
    session.pop('type',None)
    session['logged on'] = False
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


@app.route("/accountant_login", methods=['get', 'post'])
def accountant_login():
    if "step" not in request.form:
        return render_template("accountant_login.html", step="attempt")
    elif request.form["step"] == "account_lookup":
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
@app.route("/view_accounts", methods=['get', 'post'])
def view_accounts():
    if "step" not in request.form:
        db = get_db()
        cursor = db.cursor()
        companies = {}
        cursor.execute("SELECT comp_id FROM can_access where user_id=%s", [session['user'][0]])
        db.commit()
        comp_ids = cursor.fetchall()
        for id in comp_ids:
            cursor.execute("SELECT comp_name from company where id=%s", [id][0])
            db.commit()
            name = cursor.fetchone()[0]
            companies[str(id[0])] = name;
        return render_template("view_accounts.html", step="getcomp", companies=companies)

    elif request.form["step"] == "view":
        db = get_db()
        cursor = db.cursor()
        company = request.form["company"]
        cursor.execute("SELECT id, name, type, balance security_level FROM account join owns on id=acc_id WHERE comp_id = %s", [company])
        db.commit();
        accounts = cursor.fetchall()
        return render_template("view_accounts.html", step="view", accounts=accounts, len=len(accounts));

@app.route("/create_account", methods=['get', 'post'])
def create_account():
    if "accname" in request.form:
        debug("made it to the form")
        db = get_db()
        cursor = db.cursor()
        name = request.form["accname"]
        type = request.form["type"]
        balance = request.form["balance"]
        sec = request.form["sec"]
        company = request.form["company"]
        cursor.execute("INSERT INTO account(name, type, balance, security_level) VALUES (%s, %s, %s, %s) RETURNING id;", [name, type, balance, sec])
        db.commit()
        acc_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO owns(comp_id, acc_id) VALUES (%s, %s);", [company, acc_id])
        db.commit()
        return redirect(url_for("portal"))
    else:
        db = get_db()
        cursor = db.cursor()
        companies = {}
        cursor.execute("SELECT comp_id FROM can_access where user_id=%s", [session['user'][0]])
        db.commit()
        comp_ids = cursor.fetchall()
        for id in comp_ids:
            cursor.execute("SELECT comp_name from company where id=%s", [id][0])
            db.commit()
            name = cursor.fetchone()[0]
            companies[str(id[0])] = name;
        return render_template("create_account.html", companies = companies);

@app.route("/delete_account", methods=['get', 'post'])
def delete_account():
    if "id" in request.form:
        db = get_db()
        cursor = db.cursor()
        id = request.form["id"]

        cursor.execute("SELECT comp_id FROM can_access where user_id=%s", [session['user'][0]])
        db.commit()
        comp_ids = cursor.fetchall()
        got_it = False
        for comp_id in comp_ids:
            cursor.execute("SELECT * FROM owns where acc_id=%s AND comp_id=%s", [id, comp_id[0]])
            db.commit()
            accounts = cursor.fetchone()
            if accounts is not None:
                cursor.execute("SELECT * FROM INVENTORY WHERE id=%s", [id])
                db.commit()
                name = cursor.fetchone()
                if name is not None:
                    cursor.execute("DELETE FROM inventory WHERE id=%s", [id])
                db.commit()
                cursor.execute("DELETE FROM owns WHERE acc_id=%s AND comp_id=%s;", [id, comp_id[0]])
                cursor.execute("DELETE FROM owns WHERE acc_id=%s AND comp_id=%s;", [id, comp_id[0]])
                got_it = True
                db.commit()
        if got_it:
            return redirect(url_for("portal"))
        else:
            return render_template("delete_account.html", error=1)
    else:
        return render_template("delete_account.html")
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

######################################################
# Command line utilities 
        
def init_db():
    db = get_db()
    with app.open_resource('init.sql', mode='r') as f:
        db.cursor().execute(f.read())
    db.commit()

@app.cli.command('initdb')
def init_db_command():
    """Initializes the database."""
    print("Initializing DB.")
    init_db()

def populate_db():
    db = get_db()
    exec("populate.py")
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
