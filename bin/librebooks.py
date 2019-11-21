# Blog Flask application

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g

# PostgreSQL IP address
IP_ADDR = "YOUR IP ADDRESS"

# Create the application
app = Flask(__name__)

####################################################
# Routes

@app.route("/")
def homepage():
    return render_template("home.html")
