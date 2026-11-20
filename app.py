from flask import Flask,render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
import sqlite3,os
from datetime import datetime
from forecasting import forecast_price,sample_forecast
app=Flask(__name__); app.secret_key=os.environ.get("SECRET_KEY","change-this-secret-key")
DB=os.path.join(os.path.dirname(__file__),"smart_grid.db")
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 with db() as c:
  c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT)")
  c.execute("""CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY,user_id INTEGER,created TEXT,date TEXT,hour INTEGER,demand REAL,renewable REAL,temp REAL,price REAL)""")
  if not c.execute("SELECT id FROM users WHERE email='demo@smartgrid.ai'").fetchone():
   c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",("Demo User","demo@smartgrid.ai",generate_password_hash("GridDemo123!")))
def auth(): return bool(session.get("uid"))
@app.route("/")
def home(): return render_template("home.html")
@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
  if not name or not email or len(pw)<8: flash("Enter all details; password must be at least 8 characters.","error")
  else:
   try:
    with db() as c:c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,generate_password_hash(pw)))
    return redirect(url_for("login"))
   except sqlite3.IntegrityError: flash("Email already registered.","error")
 return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  with db() as c:u=c.execute("SELECT * FROM users WHERE email=?",(request.form.get("email","").lower().strip(),)).fetchone()
  if u and check_password_hash(u["password"],request.form.get("password","")):
   session.clear();session["uid"]=u["id"];session["name"]=u["name"];return redirect(url_for("dashboard"))
  flash("Incorrect email or password.","error")
 return render_template("login.html")
@app.route("/logout")
def logout():session.clear();return redirect(url_for("home"))
@app.route("/dashboard")
def dashboard():
 if not auth():return redirect(url_for("login"))
 with db() as c:
  rows=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC LIMIT 8",(session["uid"],)).fetchall()
  count=c.execute("SELECT COUNT(*) n FROM predictions WHERE user_id=?",(session["uid"],)).fetchone()["n"]
  avg=c.execute("SELECT AVG(price) a FROM predictions WHERE user_id=?",(session["uid"],)).fetchone()["a"]
 return render_template("dashboard.html",rows=rows,count=count,avg=avg)
@app.route("/predict",methods=["GET","POST"])
def predict():
 if not auth():return redirect(url_for("login"))
 result=None
 if request.method=="POST":
  try:
   date=request.form["date"]; hour=int(request.form["hour"]); demand=float(request.form["demand"]); renewable=float(request.form["renewable"]); temp=float(request.form["temp"])
   if not(0<=hour<=23 and 0<=demand<=100000 and 0<=renewable<=100000 and -30<=temp<=60):raise ValueError()
   result=forecast_price(date,hour,demand,renewable,temp)
   with db() as c:c.execute("INSERT INTO predictions(user_id,created,date,hour,demand,renewable,temp,price) VALUES(?,?,?,?,?,?,?,?)",(session["uid"],datetime.now().strftime("%Y-%m-%d %H:%M"),date,hour,demand,renewable,temp,result["price"]))
  except (ValueError,KeyError):flash("Check all inputs and try again.","error")
 return render_template("predict.html",result=result)
@app.route("/history")
def history():
 if not auth():return redirect(url_for("login"))
 with db() as c:rows=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC",(session["uid"],)).fetchall()
 return render_template("history.html",rows=rows)
@app.route("/forecast-data")
def data():
 if not auth():return redirect(url_for("login"))
 return render_template("data.html",rows=sample_forecast())
@app.route("/analytics")
def analytics():
 if not auth():return redirect(url_for("login"))
 with db() as c:rows=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC LIMIT 20",(session["uid"],)).fetchall()
 return render_template("analytics.html",rows=rows)
if __name__=="__main__":init_db();app.run(debug=True)
