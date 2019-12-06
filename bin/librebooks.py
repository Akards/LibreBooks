# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, session, redirect, url_for

from flask_table import Table, Col, DatetimeCol, LinkCol
from datetime import datetime


# PostgreSQL IP address
IP_ADDR = "34.69.97.14"

# Create the application
app = Flask(__name__, template_folder='../templates', static_folder='../static')
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

#####################################################
# Class definitions
class invoice_table(Table):
    account = Col("Account ID")
    account_name = Col("Account Name")
    amount = Col("Amount")
    date_created = DatetimeCol("Date Issued")
    pay = LinkCol("Pay", "pay_invoices", url_kwargs=dict(account='account', amount='amount'))

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

#this is terrible terrible form but I don't see why it wouldnt work. It's not threadsafe but neither is flask so who really cares
tran_accts = []
@app.route("/create_tran")
def create_tran():
    global tran_accts
    rows = ""
    total = ""
    buttonOrError = ""
    sum = 0.0
    for i in range(0, len(tran_accts)):
        if tran_accts[i][0] == True: #debit
            rows = rows + "<tr><td>" + tran_accts[i][1] + "</td><td>" + str(tran_accts[i][2]) + "</td><td></td></tr>"
            sum = sum + tran_accts[i][2]
        else:
            rows = rows + "<tr><td>" + tran_accts[i][1] + "</td><td></td><td>(" + str(tran_accts[i][2]) + ")</td></tr>"
            sum = sum - tran_accts[i][2]
    if sum != 0:
        total = '<p style="color:red";>Total: <b>' + str(sum) + '</b></p>'
        buttonOrError = '<p style="color:red";>Cannot post with non-zero balance</p>'
    else:
        total = "<p>Total: 0</p>"
        buttonOrError = '<form method="get" action="portal"><button type="submit">post</button></form>'
        #buttonOrError = '<button type="button" >Post</button> <br/>'
    return render_template("Create_Tran.html", Rows = rows, Total = total, ButtonOrError = buttonOrError)

notVisited = True #I couldn't get get requests to work, im just gonna do this abomination and figure it out later
@app.route("/select_acct", methods=['get', 'post'])
def select_acct():
    global notVisited
    global tran_accts
    if notVisited == True:
        notVisited = False
        tran_accts = [(True, "Cash", 15), (False, "MARIE CALLENDERS PASTA AL DENTE RIGATONI MARINARA CLASSICO FRESH STEAMER", 20)]
    else:
        tran_accts = [(True, "Cash", 15), (False, "MARIE CALLENDERS PASTA AL DENTE RIGATONI MARINARA CLASSICO FRESH STEAMER", 15)]
    return render_template("select_acct.html")


@app.route("/manage_invoices", methods=['get', 'post'])
def manage_invoices():
    if session['logged on'] == True and session['type'] == "accountant":
        user_id = str(session['user'])
        user_id=user_id.replace("[","")
        user_id=user_id.replace("]","")

        q8= 'select payer.full_name, payer.company_name, account.name, account.date_created, account.amount, account.id,'
        q9 = ' account.comp_name from (select invoice.id, accountant_account.comp_name, accountant_account.acc_id,' 
        q10 = 'invoice.payer, invoice.date_created, accountant_account.name, invoice.amount from '
        q11 = '(select * from (select * from (select * from (select accountant.id, accountant.security_level,'
        q12 = 'can_access.comp_id from accountant join can_access on accountant.id=can_access.user_id where id='
        q13 = user_id + ') as comp_access join company on comp_access.comp_id = company.id) as comp_access join owns ' 
        q14 = 'on comp_access.comp_id = owns.comp_id) as comp_owns join (select account.id, account.name, ' 
        q15 = 'account.security_level from account) as account on comp_owns.acc_id = account.id and ' 
        q16 = 'comp_owns.security_level >= account.security_level) as accountant_account join invoice '
        q17 = 'on accountant_account.acc_id = invoice.account) as account join payer on payer.id = account.payer'

        if "step" not in request.form:
            db = get_db()
            cursor = db.cursor()
            query= q8+q9+q10+q11+q12+q13+q14+q15+q16+q17
            cursor.execute(query)
            invoice_list= cursor.fetchall()
            print("found invoices")
            return render_template("manage_invoices.html", step="invoice_list", invoices=invoice_list)
        elif request.form["step"] == "paid_invoice":
            invoice = str(request.form["postid"])
            invoice=invoice.replace("[","")
            invoice=invoice.replace("]","")
            db = get_db()
            cursor = db.cursor()
            query= "select invoice.amount from invoice where invoice.id = " + invoice
            cursor.execute(query)
            amount= cursor.fetchone()
            q6= "(select invoice.account from invoice where invoice.id = " + invoice + ") "
            q7= "update account set balance = balance + " + str(amount[0]) + " where id = "
            query = q7 + q6
            cursor.execute(query)
            db.commit()
            query = "delete from invoice where id = " + invoice
            cursor.execute(query)
            db.commit()
            return render_template("manage_invoices.html", step="written_off",)
        elif request.form["step"] == "unpaid_invoice":
            invoice = str(request.form["postid"])
            invoice=invoice.replace("[","")
            invoice=invoice.replace("]","")
            db = get_db()
            cursor = db.cursor()
            query = "delete from invoice where id = " + invoice
            cursor.execute(query)
            db.commit()
            return render_template("manage_invoices.html", step="written_off")
        elif request.form["step"] == "back":
            return redirect(url_for("portal"))
    else:
        return redirect(url_for("home"))

@app.route("/manage_payers", methods=['get', 'post'])
def manage_payers():
    if session['logged on'] == True and session['type'] == "accountant":
        user_id = str(session['user'])
        user_id=user_id.replace("[","")
        user_id=user_id.replace("]","")
        #cursor.execute('select full_name, email, company_name from payer order by full_name')
        q0 = 'select payer.id, payer.full_name, payer.email, payer.company_name, account.name from ('
        q1 = 'select accountant_account.acc_id, invoice.payer, accountant_account.name from (select * from (select * from (select accountant.id,'
        q2 = 'accountant.security_level, can_access.comp_id from accountant join can_access on accountant.id=can_access.user_id where id= '
        q3 = user_id + ') as comp_access join owns on comp_access.comp_id = owns.comp_id)' 
        q4 = 'as comp_owns join (select account.id, account.name, account.security_level from account)'
        q5 = ' as account on comp_owns.acc_id = account.id and comp_owns.security_level >= account.security_level)'
        q6 = ' as accountant_account join invoice on accountant_account.acc_id = invoice.account'
        q7 = ') as account join payer on payer.id = account.payer'
        if "step" not in request.form:
            return render_template("manage_payers.html", step="add_or_drop")
        elif request.form["step"] == "add":
            print("added")
            return render_template('manage_payers.html', step='add')
        elif request.form["step"] == "added":
            db = get_db()
            cursor = db.cursor()
            p= request.form['password']
            e =request.form['email']
            n=request.form['name']
            c=request.form['company']
            query='insert into payer(pass_hash, email, full_name, company_name) values'
            cursor.execute(query + '(%s, %s, %s, %s)',(p,e,n,c))
            db.commit()
            cursor.execute('select payer.id from payer where pass_hash=%s and email=%s and full_name= %s and company_name=%s',(str(p),str(e),str(n),str(c)))
            id_payer = cursor.fetchone()
            query = 'insert into invoice(account, amount, payer) values '
            cursor.execute(query + '(%s,%s,%s)',(request.form['account'], request.form['amount'],id_payer[0]))
            db.commit()
            print("committed")
            return render_template('manage_payers.html', step="done_adding")
        elif request.form["step"] == "drop":
            print("drop")
            db = get_db()
            cursor = db.cursor()
            query = q0 + q1 + q2 + q3 + q4 + q5 + q6 + q7
            cursor.execute(query)
            #cursor.execute('select accountant_account.acc_id, invoice.payer from (select * from (select * from (select accountant.id, accountant.security_level, can_access.comp_id from accountant join can_access on accountant.id=can_access.user_id where id= %s) as comp_access join owns on comp_access.comp_id = owns.comp_id)as comp_owns join (select account.id, account.security_level from account) as account on comp_owns.acc_id = account.id and comp_owns.security_level >= account.security_level) as accountant_account join invoice on accountant_account.acc_id = invoice.account', [session['user']])
            rowlist = cursor.fetchall()
            print(rowlist)
            return render_template('manage_payers.html', step="drop", payers=rowlist)
        elif request.form["step"] == 'deleted':
            db = get_db()
            cursor = db.cursor()
            #payer_id = 'select invoice.payer from (' + q1 + q2 + q3 + q4 + q5 + q6 + ') as invoice'
            payer_id = request.form.getlist("payerid")
            #payer_id = payer_id[0]
            #payer_id=payer_id.replace("[","")
            #payer_id=payer_id.replace("]","")
            print("##############################")
            print(payer_id)
            #payer_id = 'select invoice.payer from invoice where payer=%s',(request.form["postid"])
            #cursor.execute('select invoice.payer from invoice where payer=%s',(payer_id))
            #payers = cursor.fetchall()
            print('******************************')
            #print(payers)
            for payer in payer_id:
                cursor.execute('delete from invoice where payer=%s',[payer])
                db.commit()
                cursor.execute('delete from payer where id=%s',[payer])
                db.commit()
            return render_template('manage_payers.html', step="delete_done")
        elif request.form["step"] == 'portal':
            return redirect(url_for("portal"))
        elif request.form["step"] == 'back':
            return redirect(url_for("manage_payers"))
    else:
        return redirect(url_for("home"))


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
        return render_template('portal.html', name=name[0], type=user_type)
    else:
        return redirect(url_for("home")) ####from render_template("home.html")

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
        cursor.execute("select email from payer where email=%s",[user])
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
        q3 = "and invoice.payer = %s"
        cursor.execute(q1+q2+q3, [user_id])
        db.commit()
        rowlist = cursor.fetchall()
        table = invoice_table(rowlist)
        return render_template("pay_invoices.html", table=table.__html__())
    else:
        debug("paying invoice")
        account_id = request.args.get('account')
        amount = request.args.get('amount')
        db = get_db()
        cursor=db.cursor()
        cursor.execute("update account set balance = balance + %s where id = %s", [amount, account_id])
        cursor.execute("delete from invoice where account = " + account_id)
        db.commit()
        return redirect(url_for("pay_invoices"))

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
        sec = "0"
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

@app.route("/create_inventory", methods=['get', 'post'])
def create_inventory():
    if "accname" in request.form:
        debug("made it to the form")
        db = get_db()
        cursor = db.cursor()
        name = request.form["accname"]
        type = request.form["type"]
        balance = request.form["balance"]
        sec = "0"
        company = request.form["company"]
        price = request.form["price"]
        quantity = request.form["quantity"]

        cursor.execute("INSERT INTO account(name, type, balance, security_level) VALUES (%s, %s, %s, %s) RETURNING id;", [name, type, balance, sec])
        db.commit()
        acc_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO owns(comp_id, acc_id) VALUES (%s, %s);", [company, acc_id])
        db.commit()
        cursor.execute("INSERT INTO inventory(id, price, quantity) VALUES (%s, %s, %s);", [acc_id, price, quantity])
        db.commit()
        return redirect(url_for("portal"))
    else:
        db = get_db()
        cursor = db.cursor()
        companies = {}
        cursor.execute("SELECT comp_id FROM can_access where user_id=%s;", [session['user'][0]])
        db.commit()
        comp_ids = cursor.fetchall()
        for id in comp_ids:
            cursor.execute("SELECT comp_name from company where id=%s;", [id][0])
            db.commit()
            name = cursor.fetchone()[0]
            companies[str(id[0])] = name;
        return render_template("create_inventory.html", companies = companies);

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
                got_it = True
                db.commit()
        if got_it:
            return redirect(url_for("portal"))
        else:
            return render_template("delete_account.html", error=1)
    else:
        return render_template("delete_account.html")
importantValue = True
@app.route("/view_journal")
def view_journal():
    global importantValue
    global oz1
    global oz2
    if importantValue == True:
        importantValue = False
        return render_template("view_journal.html", bod = "")
    else:
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return render_template("view_journal.html", bod = oz1 + dt_string + oz2)

@app.route("/create_tran_get_type", methods = ['POST', 'GET'])
def create_tran_get_type():
    return render_template("Create_Tran_Get_Type.html")

@app.route("/create_sale", methods = ['get', 'post'])
def create_sale():
    if "inv" in request.form:
        db = get_db()
        cursor = db.cursor()
        trans_name = request.form["trans_name"]
        inv = request.form["inv"]
        acc = request.form["acc"]
        num = int(request.form["num"]) #number of items
        type = request.form["type"] #Buying or Selling (B or S)

        cursor.execute("SELECT price FROM inventory WHERE id = %s;", [inv])
        db.commit()
        price = int(cursor.fetchone()[0])

        amount = price * num

        cursor.execute("INSERT INTO transact(amount, name) VALUES (%s, %s) RETURNING id;", [amount, trans_name])
        db.commit()
        trans = cursor.fetchone()[0]
        if type == 'B': #Buying Inventory
            cursor.execute("UPDATE account SET balance=balance+%s WHERE id = %s;", [amount, inv])
            cursor.execute("UPDATE inventory SET quantity=quantity+%s WHERE id = %s;", [num, inv])

            cursor.execute("UPDATE account SET balance=balance-%s WHERE id = %s;", [amount, acc])

            cursor.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) VALUES (%s, %s, %s, %s);",
                           [trans, inv, amount, 'C'])
            cursor.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) VALUES (%s, %s, %s, %s);",
                           [trans, acc, amount, 'D'])
            db.commit()
        else: #Selling Inventory
            cursor.execute("UPDATE account SET balance=balance-%s WHERE id = %s;", [amount, inv])
            cursor.execute("UPDATE inventory SET quantity=quantity-%s WHERE id = %s;", [num, inv])

            cursor.execute("UPDATE account SET balance=balance+%s WHERE id = %s;", [amount, acc])

            cursor.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) VALUES (%s, %s, %s, %s);",[trans, inv, amount, 'D'])
            cursor.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) VALUES (%s, %s, %s, %s);",[trans, acc, amount, 'C'])
            db.commit()
        return redirect(url_for("portal"))

    else:
        db = get_db()
        cursor = db.cursor()
        inv_accs = []
        all_accs = []
        cursor.execute("SELECT comp_id FROM can_access where user_id=%s;", [session['user'][0]])
        db.commit()
        comp_ids = cursor.fetchall()
        for comp_id in comp_ids:
            cursor.execute("SELECT acc_id, name FROM owns join account on acc_id = id where comp_id=%s;", [comp_id[0]])
            db.commit()
            all_accs.extend(cursor.fetchall())

            cursor.execute("SELECT acc_id, name FROM inventory join (account join owns on acc_id = id) on acc_id = inventory.id where comp_id=%s;", [comp_id[0]])
            db.commit()
            inv_accs.extend(cursor.fetchall())
        return render_template("create_sale.html", inventory = inv_accs, accounts = all_accs)


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
    with app.open_resource('populate.py', mode='r') as f: #exec("populate.py")
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

oz1 = '<table style="width:500px;border: 1px solid black"> <tr bgcolor="#ddd"><td>SALE 1</td><td>'
oz2 = '</td><td>15.00</td></tr> <tr><td>Cash</td><td>15.00</td></tr> <tr><td>MARIE CALLENDERS PASTA AL DENTE RIGATONI MARINARA CLASSICO FRESH STEAMER</td><td></td><td>(15.00)</td></table>'