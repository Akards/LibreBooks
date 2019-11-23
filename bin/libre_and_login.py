# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, session, redirect, url_for

# PostgreSQL IP address
IP_ADDR = "34.69.97.14"

# Create the application
app = Flask(__name__)


app.secret_key=os.urandom(32)
####################################################
# Routes

@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/portal")
def portal():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('select full_name from %s where id=%s',[session['type'],session['user']])
    db.commit()
    name = cursor.fetchone()
    return render_template('portal.html', name=name)

@app.route("/payer_login", methods=['get', 'post'])
def payer_login():
    if "step" not in request.form:
        return render_template("login.html", step="attempt")
    elif request.form["step"] == "account_lookup":
        debug("account_lookup")
        db = get_db()
        cursor = db.cursor()
        user = request.form["user"]
        cursor.execute("select email from payer where email=%s",[user])
        db.commit()
        rowlist = cursor.fetchall()
        if len(rowlist) == 0:
            debug(rowlist)
            return render_template("login.html", step="not_user")
        else:
            db.commit()
            return render_template("login.html", step="user", user=user)
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
            return render_template("login.html", step="not_password", user=user)
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
        return render_template("login.html", step="attempt")
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
            return render_template("login.html", step="not_user")
        else:
            db.commit()
            return render_template("login.html", step="user", user=user)
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
            return render_template("login.html", step="not_password", user=user)
        else:
            cursor.execute("select id from accountant where email=%s and pass_hash=%s",[user,password])
	    db.commit()
	    id = cursor.fetchone()
            session['logged on'] = True
            session['user'] = id
	    session['type'] = "accountant"
            return redirect(url_for("portal"))


@app.route("/logout")
def logout():
    session.pop('user',None)
    session.pop('type',None)
    session.pop('logged on',None)
    return render_template("logout.html")
