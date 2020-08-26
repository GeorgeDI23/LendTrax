'''
A website that tracks lender consents for optional prepayments on credit facilities.
Allows user to create new deals, upload lender lists, and download list of lender ellections.
'''

#System Libraries
import os
import datetime
import pytz
import time

#Downloaded Libraries
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import csv
from pandas import read_excel, read_csv
from sqlalchemy import create_engine
import pymysql
from functools import wraps

#SQL Connection
import mysql.connector 

# MySQL login from 'credentials.txt' file include the below elements on each line
credentialFile = open("credentials.txt")
hostX = credentialFile.readline().strip()
userX = credentialFile.readline().strip()
passwordX = credentialFile.readline().strip()
databaseX = credentialFile.readline().strip()
credentialFile.close()

# Extensions allowed to be uploaded via lenderlist upload
ALLOWED_EXTENSIONS = set(['csv', 'xls', 'xlsx', 'xlsb'])

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message), code
def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Filter for dollars
def usd(value):
    value = float(value)
    return f"${value:,.2f}"
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# SQL Processor
def sqlEx(query, headings):
    # Establish a mysql connection
    db = mysql.connector.connect( host = hostX,
		user = userX, password = passwordX, database = databaseX)
    # Executes SQL Query
    cursor = db.cursor()
    cursor.execute(query)
    #either pass headings or indication of update SQL
    if(headings[0] == "update"):
        db.commit()
        return True
    elif(headings[0] == "*"):
        records = cursor.fetchall()
        if not records:
            return False
        cursor.execute("show columns from " + headings[1] +";") 
        col = cursor.fetchall()
        columns = []
        for item in col:
            columns.append(item[0])
    else:
        records = cursor.fetchall()
        columns = headings
    #Blend headings and results and return
    ret =[]
    lcount = 0
    for line in records:
        entry = {}
        icount = 0
        for item in columns:
            entry[str(item)] = str(records[lcount][icount])
            icount+=1
        ret.append(entry)
        lcount+=1
    db.commit()
    db.close()
    return ret

@app.route("/")
@login_required
def index():
    #Identify user
    mei = session["user_id"][0]

    # check if agent bank logging in
    if mei != "agentbank":
       return redirect("/vote")
    else:
        #display main interface with instructions on how to proceed
        dealname = session["user_id"][1]
        return render_template("index.html")

@app.route("/vote", methods=["GET", "POST"])
@login_required
def vote():
    """Consent vote by lender"""
    # Pulling data used for both POST/GET
    lenderpull = sqlEx("SELECT * FROM "+session["user_id"][1]+" WHERE mei = '"+session["user_id"][0]+"';",["*", session["user_id"][1]])
    datapull = []
    datapull.append(lenderpull[0]["mei"])
    datapull.append(lenderpull[0]["child"])
    datapull.append(lenderpull[0]["commitment"])
    paymentpull = sqlEx("SELECT payment FROM deals WHERE dealname = '"+session["user_id"][1]+"';",['payment'])
    paymentpull = float((float(paymentpull[0]['payment'])/100) * float(datapull[2]))
    contactpull = sqlEx("SELECT contact FROM deals WHERE dealname = '"+session["user_id"][1]+"';", ['contact'])

    dealname = session["user_id"][1]
    child = datapull[1]
    position = float(datapull[2])
    payment = paymentpull
    contact = contactpull[0]['contact']

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure election was submitted
        if not request.form.get("radio1"):
            return apology("Please submit a choice", 400)

        choice = request.form.get("radio1")
        session["choice"] = choice

        return redirect(url_for('confirmation', choice=choice))

    # User reached route via GET (as by clicking a link or via redirect)255
    else:
        return render_template("vote.html", dealname=dealname, child=child, position=position, payment=payment, contact=contact)

@app.route("/confirmation", methods=["GET", "POST"])
@login_required
def confirmation():
    """Confirm decision and post to database"""
    choice = session["choice"]

    # Pulling data used for both POST/GET
    lenderpull = sqlEx("SELECT * FROM "+session["user_id"][1]+" WHERE mei = '"+session["user_id"][0]+"';", ["*",session["user_id"][1]])
    datapull = []
    datapull.append(lenderpull[0]["mei"])
    datapull.append(lenderpull[0]["child"])
    datapull.append(lenderpull[0]["commitment"])
    paymentpull = sqlEx("SELECT payment FROM deals WHERE dealname = '"+session["user_id"][1]+"';",['payment']) #dealname=session["user_id"][1])
    paymentpull = float((float(paymentpull[0]['payment'])/100) * float(datapull[2]))
    contactpull = sqlEx("SELECT contact FROM deals WHERE dealname = '"+session["user_id"][1]+"';",['contact'])

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if choice == 'decline':
            choice = '0'
        else:
            choice = '1'
        # Grab time when election made, localized to NYC Time
        datentime = datetime.datetime.now()
        datentime = datentime.astimezone(pytz.timezone("America/New_York"))
        datentime = datentime.strftime('%y-%m-%d %H:%M:%S')


        # Registers the vote
        vote_update = sqlEx("UPDATE "+session["user_id"][1]+" SET vote = '"+choice+"' WHERE mei = '"+session["user_id"][0]+"';", ['update'])
        voted_update = sqlEx("UPDATE "+session["user_id"][1]+" SET voted = '1' WHERE mei = '"+session["user_id"][0]+"';", ['update'])
        voted_update = sqlEx("UPDATE "+session["user_id"][1]+" SET type = 'online' WHERE mei = '"+session["user_id"][0]+"';", ['update'])
        voted_update = sqlEx("UPDATE "+session["user_id"][1]+" SET time = '"+datentime+"' WHERE mei = '"+session["user_id"][0]+"';", ['update'])

        flash('Vote successfully registered. Thank you.')
        return redirect("/exit")

    # User reached route via GET (as by clicking a link or via redirect)255
    else:
        dealname = session["user_id"][1]
        child = datapull[1]
        position = float(datapull[2])
        payment = paymentpull
        return render_template("confirmation.html", dealname=dealname, child=child, position=position, payment=payment, choice=choice)

@app.route("/exit", methods=["GET"])
@login_required
def exit():
    # Returns confirmation of submission then logs out lender
    return render_template("exit.html")
    return redirect("/login")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def add():
    """Upload file to database"""
    # Check that database is currently unpopulated to prevent overwrite
    dbcheck = sqlEx("SELECT * FROM "+session["user_id"][1]+";", ["*", session["user_id"][1]])
    if dbcheck:
        return apology("This lender list is currently populated.", 400)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure file was submitted
        if 'lenderlist' not in request.files:
            return apology("Please select a file to upload", 400)

        lenderlist = request.files["lenderlist"]

        if lenderlist.filename == '':
            return apology("Please select a file to upload", 400)

        # Below is from upload file docs listed above, minorly edited
        extension = lenderlist.filename.rsplit('.', 1)[1].lower()
        EXCEL = set(['xls', 'xlsx', 'xlsb'])
        if extension in ALLOWED_EXTENSIONS:
            if extension == 'csv':
                lenderdb = read_csv(lenderlist, index_col=False) # setup to keep index column from csv as separate column from index
                lenderdb['voted'] = 0 # Should be uploading fresh lenderlists
                lenderdb['id'] = 0
                flash('File successfully uploaded')
            if extension in EXCEL:
                lenderdb = read_excel(lenderlist)
                lenderdb['voted'] = 0 # Should be uploading fresh lenderlists
                lenderdb['id'] = 0
                flash('File successfully uploaded')
            if not lenderdb.empty:
                dbEngine = create_engine("mysql+pymysql://"+userX+":"+passwordX+"@"+hostX+"/"+databaseX, echo=True)
                dbb = dbEngine.connect()
                lenderdb.to_sql(str(session["user_id"][1]).strip(), con=dbb, index = False, if_exists='append')
                dbb.close()
                dbEngine.dispose()
                

        # Error message if incorrect type of file uploaded (based on extension)
        else:
            flash("File must be in CSV, XLS, XLSX, or XLSB format.")

        # Returns user to status page with message at top
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)255
    else:
        return render_template("upload.html")

@app.route("/status", methods=["GET"])
@login_required
def status():
    if request.method == "GET":
        ''' The actual pull of history -- Selection of what is printed is done via jinja '''
        transactions = sqlEx("SELECT * FROM "+session["user_id"][1]+" WHERE voted = 1", ["*",session["user_id"][1]])
        if not transactions:
            transactions = []

        ''' The actual pull of history -- Selection of what is printed is done via jinja '''
        nonvoted = sqlEx("SELECT * FROM "+session["user_id"][1]+" WHERE NOT voted = 1", ["*", session["user_id"][1]])
        if not nonvoted:
            nonvoted = []

        if transactions == [] and nonvoted == []:
            return apology("This lender list is currently blank.", 400)

        # Calculations for values presented
        vcount = 0.00
        len_vcount_int = 0
        len_count = 0
        for item in transactions:
            vcount = vcount + float(item['commitment'])
            len_vcount_int += 1
            len_count += 1

        nvcount = 0.00

        for item in nonvoted:
            nvcount = nvcount + float(item['commitment'])
            len_count += 1

        totalcommitment = vcount + nvcount
        per_vcount = round((vcount / totalcommitment) * 100, 2)

        len_vcount_per = round((len_vcount_int / len_count) * 100, 2)

        consent = 0.00
        for item in transactions:
            if item['vote'] == '1':
                consent = consent + float(item['commitment'])

        per_consented = round((consent/totalcommitment)*100, 2)

        consented = round(consent, 2)

        """ Final display of history"""
        return render_template("status.html", transactions=transactions, nonvoted=nonvoted, 
                    voted = per_vcount, voted_lender = len_vcount_per, per_consented = per_consented, 
                    consented = consented, dealname = session["user_id"][1])

@app.route("/download", methods=["GET"])
@login_required
def download():
    """Downloads Currency Status of lender list in csv"""
    if request.method == "GET":
        with open('output.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['id', 'mei', 'parent', 'child', 'shortname', 'commitment', 'vote', 'voted', 'type', 'time'])
            source = sqlEx("SELECT * FROM "+session["user_id"][1]+";", ["*",session["user_id"][1]])
            identifiers = ['id', 'mei', 'parent', 'child', 'shortname', 'commitment', 'vote', 'voted', 'type', 'time']

            for lender in source:
                lenderlist = lender
                stuff = []
                for x in identifiers:
                    if x == "vote":
                        if lenderlist[x] == "0":
                            stuff.append("Refused")
                        elif lenderlist[x] == "1":
                            stuff.append("Consented")
                        else:
                            stuff.append(lenderlist[x])
                    elif x == "voted":
                        if lenderlist[x] == "0":
                            stuff.append("False")
                        else:
                            stuff.append("True")                        
                    else:
                        stuff.append(lenderlist[x])
                writer.writerow(stuff)
        try:
            return send_file('output.csv', as_attachment=True, attachment_filename='output.csv')
        except Exception as e:
            return str(e)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log lender in"""
    # clear the logged in session
    session.clear()

    # Lender reached route via POST
    if request.method == "POST":

        # Ensure deal was submitted
        if not request.form.get("deal"):
            return apology("Please provide deal name as specified on notice", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Please provide password as specified on notice", 403)

        # Query database for deal, password, and lender
        rows = sqlEx("SELECT * FROM deals WHERE dealname = '"+str(request.form.get("deal"))+"';",["*", "deals"])

        if not rows or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid deal, username and/or password", 403)

        if not request.form.get("mei")=='agentbank':
            lenderpull = sqlEx("SELECT * FROM " + request.form.get("deal") +" WHERE mei = '"+request.form.get("mei") + "';", ["*", request.form.get("deal")])
        else:  
            lenderpull = []

        # Error is incorrect MEI
        if not lenderpull and not request.form.get("mei")=='agentbank':
            return apology("Invalid MEI", 403)

        # Prevents overwriting existing vote
        if not request.form.get('mei')=='agentbank':
            if lenderpull[0]['voted'] == '1':
                return apology("Vote has already been registered for this lender.", 403)

        # Persistant login and saved lender identity
        identity = []
        if not request.form.get('mei')=='agentbank':
            identity.append(lenderpull[0]["mei"])
        else:
            identity.append('agentbank')
        identity.append(rows[0]["dealname"])
        session["user_id"] = identity
        session["deal"] = request.form.get("deal")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    # MySQL Updated
    """Register a new deal"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure dealname, password, contact provided
        if not request.form.get("deal"):
            return apology("Must provide dealname", 400)

        # Ensure loan value supplied
        elif not request.form.get("loan"):
            return apology("Must provide total loan value", 400)

        # Ensure payment value supplied
        elif not request.form.get("payment"):
            return apology("Must provide payment amount", 400)

        # Ensure passwords were submitted and match
        elif not request.form.get("password"):
            return apology("Must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Ensure a deal contact is provided for inquiries
        elif not request.form.get("contact"):
            return apology("Must provide a deal contact for lender inquiries", 400)

        # Adds deal to deals list and creates new, blank lender database
        else:
            check = sqlEx("SELECT * FROM deals WHERE dealname = '"+request.form.get("deal")+"';", ["*","deals"])
            if check:
                return apology("Dealname already exists. Please add in format NAMEMMYY", 400)

            percentage = float(request.form.get("payment")) / float(request.form.get("loan"))

            hashp = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
            result = sqlEx("INSERT INTO deals VALUES (NULL,'"+request.form.get("deal")+"\
                            ','"+hashp+"','"+request.form.get("contact")+"',"+str(percentage)+");",["update"])

            if result:
                result = sqlEx("CREATE TABLE IF NOT EXISTS "+request.form.get("deal")+"(id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, \
                                    mei text NOT NULL, parent text NOT NULL, child text NOT NULL, shortname text NOT NULL, \
                                    commitment int NOT NULL, vote boolean, voted boolean NOT NULL, type text, time datetime)",
                                    ["update"])

        # update deal logged in under
        dealname = request.form.get("deal")

        session["user_id"][1] = dealname

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)