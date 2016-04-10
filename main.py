import os , random
from flask import Flask, render_template, json, request,jsonify
from flask.ext.mysql import MySQL
import sys
app = Flask(__name__)
import time
from datetime import datetime as dt

today = time.strftime('%y-%m-%d')
print today
today = dt.strptime(today, "%y-%m-%d")

mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'saurabh'
app.config['MYSQL_DATABASE_PASSWORD'] = 'saurabh'
app.config['MYSQL_DATABASE_DB'] = 'Flight_Management_System'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

conn = mysql.connect()
c = conn.cursor()

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
def allNumbers(inputString):
    for i in inputString:
        if not i.isdigit():
            return False
    return True

@app.route("/")
def main():
    errors=""
    return render_template("index.html",errors=errors)

@app.route("/flights",methods=['GET','POST'])
def flights():
    _from = request.form['airport_from']
    _to   = request.form['airport_to']
    _date = request.form['date']

    if hasNumbers(_from) or hasNumbers(_to) or _from=="" or _to=="":
        errors = "Source and Destination Not Proper. Please Renter"
        return render_template("index.html",errors=errors)
    elif dt.strptime(_date[2:],"%y-%m-%d")<=today:
         errors = "Sorry date has passed"
         return render_template("index.html",errors=errors)
    
    
    print "Form Data as follows:-"
    print "From:",_from ,"To:" , _to ,"Date:" ,_date
    print "Query Executed:SELECT flight_no,arrival,departure,no_of_stoppages FROM route JOIN flight_details ON flight_no = fno WHERE source=(SELECT port_id FROM Airport WHERE city='%s') AND destination=(SELECT port_id FROM Airport WHERE city='%s')"%(_from,_to)

    try:
        c.execute ("SELECT flight_no,airlines,arrival,departure,no_of_stoppages,price,route_id FROM route JOIN flight_details ON flight_no = fno WHERE source=(SELECT port_id FROM Airport WHERE city='%s') AND destination=(SELECT port_id FROM Airport WHERE city='%s')"%(_from,_to))
        entries = []
        entries = [dict(Flight_no=row[0], Airlines=row[1],arrive_time = row[2],depart_time = row[3],stops = row[4],price = row[5],rid = row[6],date=_date) for row in c.fetchall()]
    except conn.Error as err:
        errors = "{}".format(err)
        return render_template("index.html",errors=errors)
        
    
    print "Results obtained:"
    print entries
    #Here route id is hidden in html and will be sent as post request

    
    return render_template("flights.html",entries=entries)


@app.route("/book",methods=['GET','POST'])
def book():
    print "Form data:-"
    _rid = request.args.get('rid')
    _date = request.args.get('date')
    if dt.strptime(_date[2:],"%y-%m-%d")<=today:
        errors = "Sorry date has passed"
        return render_template("index.html",errors=errors)
    
    entries = dict(rid = _rid,date=_date)
    print entries
    errors = ""
    return render_template("user_details.html",entries=entries,errors = errors)

@app.route("/payment",methods=['GET','POST'])
def payment():
    _rid = int(request.form['rid'])
    _date = request.form['date']
    entries = dict(rid = _rid,date=_date)
    _fn = request.form['firstname']
    _ln = request.form['lastname']
    if hasNumbers(_fn) or hasNumbers(_ln):
        errors = "First name or Latname has Numbers in it"
        return render_template("user_details.html",entries=entries,errors = errors)
        
    try:
        _age = int(request.form['age'])
    except ValueError as err:
            errors = "Age Invalid Enter again:{}".format(err)
            return render_template("user_details.html",entries=entries,errors = errors)
    if _age<0:
        errors = "Age Invalid Can't be negative"
        return render_template("user_details.html",entries=entries,errors = errors)
        
    _sex = request.form['sex']
    
    _email = request.form['email']
    if '@' not in _email or '.' not in _email:
        errors = "Invalid Email"
        return render_template("user_details.html",entries=entries,errors = errors)
    
    _phone = request.form['phone']
    if not allNumbers(_phone):
        errors = "Phone can't have characters"
        return render_template("user_details.html",entries=entries,errors = errors)
    elif len(_phone)!=10:
        errors = "Phone should be 10 digits long"
        return render_template("user_details.html",entries=entries,errors = errors)
    _meal = request.form['meal']
    
    try:
        _seats = int(request.form['seats'])
    except ValueError:
        errors = "Seats should be numbers"
        return render_template("user_details.html",entries=entries,errors = errors)
    if _seats<1 or _seats>100:
        errors = "Should Be greater than or equal to 1 and less then number of seats available"
        return render_template("user_details.html",entries=entries,errors = errors)

    _insuarance = request.form['insuarance']
    
    if _fn==""or _ln=="" or _age=="" or _sex=="" or _phone=="" or _meal=="" or _insuarance=="":
        errors = "Fill all fields"
        return render_template("user_details.html",entries=entries,errors = errors)
    
    _pid = random.randint(1000,99999)
    _pnr = random.randint(10000,999999)
    warning=""
    try:
        c.execute("INSERT INTO PASSENGER VALUES (%s,'%s','%s',%s,'%s','%s',%s)"%(_pid,_fn,_ln,_age,_sex,_email,long(_phone)))
        c.execute("INSERT INTO CHOOSES VALUES (%s,%s,'%s','%s','%s',%s,%s)"%(_pnr,_pid,_date,_meal,_insuarance,_seats,_rid))
    except conn.Error as err:
        errors = "{}".format(err)
        c.execute("select pid from passenger where email_id='%s'"%_email)
        try:
            _pid = c.fetchall()[0][0]
        except:
            c.execute("select pid from passenger where phone_no=%s"%_phone)
            _pid = c.fetchall()[0][0]
        warning = "Hola! You have been here Earlier Using Your old Details"
        c.execute("INSERT INTO CHOOSES VALUES (%s,%s,'%s','%s','%s',%s,%s)"%(_pnr,_pid,_date,_meal,_insuarance,_seats,_rid))

    c.execute('Select * from route where route_id=%s'%(_rid))
    price1 = int(c.fetchall()[0][6])
    price1= int(price1)
    price = price1
    price = price*int(_seats)
    add = 0
    #Discount Calculation:
    discount = 0
    c.execute("Select * from discount where dis_day='%s'"%(_date))
    try:
        discount = int(c.fetchall()[0][2])
    except IndexError:
        discount = 0
    if _meal == 'Y':
        add = add + 0.05*price
    if _insuarance == 'Y':
        add = add +  0.05*price
        
    price = price + add
    dis_price = price - (price*discount)/100
    entries = dict(flight_price=price1,pnr = _pnr,rid = _rid,date=_date,meal=_meal,insuarance = _insuarance,total_amount = price,dis_percent = discount,discounted=dis_price,seat=_seats)
    if _seats>1:
        for i in range(1,_seats):
            _dep_id = random.randint(10000,999999)
            c.execute("insert into dependents values(%s,%s)"%(_pnr,_dep_id))
            
    conn.commit()
    
    return render_template("Payment_gateway.html",entries=entries,warning=warning)

    
    

if __name__=="__main__":
    app.run(debug=True)



