"""
Names: Adam Schlossberg, Ben Yaffee, Andrew Frantz, J. Hugh Wright
Date: 11/6/2019
Pledge: I have not given or recieved unauthorized aid on this program.
Description: A populate.py to create fake accounting Data. It takes a long time to work.
"""

import psycopg2
import random

conn = psycopg2.connect("dbname=librabooks user=postgres host=34.69.97.14 password=rhodes port=5432") #Change this to whatever 
cur = conn.cursor() 
cur.execute("DELETE FROM owns;")
cur.execute("DELETE FROM ledger;")
cur.execute("DELETE FROM transact;")
cur.execute("DELETE FROM invoice;")
cur.execute("DELETE FROM can_access;")
cur.execute("DELETE FROM accountant;") 
cur.execute("DELETE FROM company;") 
cur.execute("DELETE FROM payer;")
cur.execute("DELETE FROM inventory;")
cur.execute("DELETE FROM account;")

#Accountants 
f = open("../db_init/Accountants.csv", "r") 
f.readline() 
while (True): 
    line = f.readline(); 
    if not line: 
        break 
    words = line.split(',') 
    cur.execute("INSERT INTO accountant(pass_hash, email, full_name, security_level) values (%s, %s, %s, %s)", (words[2], words[1], words[3], words[4])) 
f.close() 
conn.commit() 

#Companies 
f = open("../db_init/Companies.csv", "r") 
f.readline() 
while (True): 
    line = f.readline(); 
    if not line: 
        break 
    words = line.split(',') 
    cur.execute("INSERT INTO company(comp_name) values (%s)",(words[1],)) 
f.close() 
conn.commit() 

#Can Access 
for x in range(50):
    cur.execute("INSERT INTO can_access(user_id, comp_id) values ((select id from accountant order by id limit 1 offset %s), (select id from company order by random() limit 1))", (str(x),)) 
conn.commit() 

#Payers 
f = open("../db_init/Payer.csv", "r") 
f.readline() 
for x in range(200): 
    line = f.readline() 
    if not line: 
        break 
    words = line.split(',') 
    cur.execute("INSERT INTO payer(pass_hash, email, full_name, company_name) values (%s,%s,%s,%s)",(words[4], words[3], words[2], words[1])) 
f.close() 
conn.commit() 

# Inventory 
f = open("../db_init/Inventory.csv", "r") 
f.readline() 
while(True): 
    iLine = f.readline() 
    if not iLine: 
        break 
    Words = iLine.split(",") 
    cur.execute("INSERT INTO account(name, type, balance, security_level) values (%s,%s,%s,%s)",("INV-" + Words[0][:50], "ASSET", "0", "0"))  
    cur.execute('SELECT id FROM account WHERE name = %s AND id NOT IN (SELECT id FROM inventory)', ('INV-' + Words[0][:50],))
    accs = cur.fetchone() 
    cur.execute("INSERT INTO inventory(id, price, quantity) values(%s, %s, %s)", ( accs[0], Words[2], "0")) 
f.close()

# Accounts (non-inventory) 
f = open("../db_init/Nouns.csv", 'r') 
f.readline() 
i = 0 
while(True): 
    Type = ""
    if i < 100: 
        Type = "ASSET" 
    elif i < 200: 
        Type = "EQUITY"
    else: 
        Type = "LIABILITY"
    line = f.readline() 
    if not line or i >= 300: 
        break 
    Words = line.split(',')
    cur.execute("INSERT INTO account(name, type, balance, security_level) values (%s, %s, %s, %s)", (Words[0].split(' ')[0][:59], Type, "0", "0"))
    i = i + 1
conn.commit()
f.close()

#transact, ledger (non-inventory) 
for i in range (0, 200): 
    amt = str(random.randint(0, 200)) 
    cur.execute("SELECT id FROM account ORDER BY RANDOM() LIMIT 2") 
    Accts = cur.fetchall() 
    cur.execute("INSERT INTO transact(amount, name) values (%s, %s)", (amt, "Transaction " + str(i)))
    cur.execute("SELECT id FROM transact WHERE name = %s;", ("Transaction " + str(i),))
    id = cur.fetchone()[0] 
    cur.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) values (%s, %s, %s, %s)", (id, Accts[0][0], amt, "C"))
    cur.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) values (%s, %s, %s, %s)", (id, Accts[1][0], amt, "D"))
    cur.execute("UPDATE account SET balance = balance + %s WHERE id = %s", (amt, Accts[1][0])) 
    cur.execute("UPDATE account SET balance = balance - %s WHERE id = %s", (amt, Accts[0][0]))  
conn.commit()

#transact, ledger (inventory) 
for i in range(0, 200): 
    amt = str(random.randint(0, 200)) 
    quantAmt = str(random.randint(0, 200)) 
    cur.execute("SELECT id FROM account WHERE name LIKE %s ORDER BY RANDOM() LIMIT 1", ("INV-%",)) 
    invAcct = cur.fetchone()  
    cur.execute("SELECT id FROM account WHERE name NOT LIKE %s ORDER BY RANDOM() LIMIT 2", ("INV-%",))
    nonInvAccts = cur.fetchall() 
    cur.execute("SELECT name FROM account WHERE id = %s;", (invAcct[0],))
    InvName = cur.fetchall()[0][0]
    cur.execute("INSERT INTO transact(amount, name) values (%s, %s)", (amt, "Purchase of " + quantAmt + " of " + InvName[:20] + ": " + str(i)))
    cur.execute("SELECT id FROM transact WHERE name = %s;", ("Purchase of " + quantAmt + " of " + InvName[:20] + ": " + str(i),))
    Id = cur.fetchone()[0] 
    cur.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) values (%s, %s, %s, %s)", (Id, nonInvAccts[0][0], amt, "C"))
    cur.execute("INSERT INTO ledger(trans_id, acc_id, amount, c_or_d) values (%s, %s, %s, %s)", (Id, nonInvAccts[1][0], amt, "D"))
    cur.execute("UPDATE account SET balance = balance + %s WHERE id = %s", (amt, nonInvAccts[1][0]))
    cur.execute("UPDATE account SET balance = balance - %s WHERE id = %s", (amt, nonInvAccts[0][0]))
    cur.execute("UPDATE inventory SET quantity = quantity + %s WHERE id = %s", (quantAmt, invAcct[0])) 
conn.commit() 

#Owns 
for x in range(50): 
    for y in range(2): 
        cur.execute("INSERT INTO owns(comp_id, acc_id) values ((SELECT id FROM company order by id limit 1 offset %s), (SELECT id FROM account order by random() limit 1 offset %s))", (str(x),str(y)))
conn.commit() 

#Invoice 
for i in range(200): 
    cur.execute("INSERT INTO invoice(payer, account, amount) values ((SELECT id FROM payer order by random() limit 1 offset %s), (SELECT id FROM account order by random() limit 1 offset %s), %s)",(str(i), str(i), str(random.randint(1,1000000)))) 
conn.commit()
conn.close() 
cur.close()  
