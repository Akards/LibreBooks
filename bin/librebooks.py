# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, session, redirect, url_for
from flask_table import Table, Col, DatetimeCol, LinkCol

# PostgreSQL IP address
IP_ADDR = "34.69.97.14"

# Create the application
app = Flask(__name__, template_folder='../templates')
app.secret_key=os.urandom(32)

class invoice_table(Table):
    account = Col("Account ID")
    account_name = Col("Account Name")
    amount = Col("Amount")
    date_created = DatetimeCol("Date Issued")
    pay = LinkCol("Pay", "pay_invoices", url_kwargs=dict(account='account'))
    #pay = ButtonCol("Pay", "pay_invoices", form_hidden_fields=dict(step="selected", account="account"))
    #, form_attrs=dict(account="account")

class invoice_entry(object):
    def __init__(self, account, account_name, amount, date):
        self.account = account
        self.account_name = account_name
        self.amount = amount
        self.date = date
        self.pay = account

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


@app.route("/pay_invoices", methods=['get', 'post'])
def pay_invoices():
    #if session['logged on'] != True:
    #    return redirect(url_for("/"))
    if request.args.get('account') == None:
        user_id = str(session['user'])
        user_id=user_id.replace("[","")
        user_id=user_id.replace("]","")
        db = get_db()
        cursor = db.cursor()
        q1 = "select account.id as account, account.name as account_name, invoice.amount as amount, "
        q2 = "invoice.date_created as date_created from account join invoice on account.id = invoice.account "
        q3 = "and invoice.payer = " + user_id
        cursor.execute(q1+q2+q3)
        db.commit()
        rowlist = cursor.fetchall()
        table = invoice_table(rowlist)
        return table.__html__()
    else:
        debug("paying invoice")
        account_id = request.args.get('account')
        db = get_db()
        cursor=db.cursor()
        cursor.execute("delete from invoice where account = " + account_id)
        db.commit()
        return redirect(url_for("pay_invoices"))



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
