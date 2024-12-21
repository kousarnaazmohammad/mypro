from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file 
from otp import genotp #here genotp is a function in otp.py file  and  # Function to generate OTP (defined in otp.py)
from cmail import sendmail #sendmail is a function name    # Function to send email (defined in cmail.py)
from token_1 import encode,decode   # Functions for encoding and decoding JWT tokens
import mysql.connector   # MySQL database connector
from io import BytesIO  #it converts byte to binary or vice-versa   # Used to handle binary data (e.g., files)
import flask_excel as excel   # Flask extension to work with Excel files
import re #regular expression -->it is used for pattern matching
from flask_session import Session   # For session management with Flask
from mysql.connector import (connection)    # MySQL connection interface
mydb=mysql.connector.connect(host="localhost",user="root",password="admin",db="snmprg")
app=Flask(__name__) #__name__ is an argument   # Initialize Flask app
excel.init_excel(app)  # Initialize flask_excel extension
app.secret_key="kousar"   # Secret key for session management
app.config['SESSION_TYPE']='filesystem'  # Store session data in filesystem
Session(app)  # Initialize Flask session
@app.route("/")   #link address is/
def home():
    return render_template("welcome.html")
@app.route("/create",methods=["GET","POST"])
def create():
    if request.method=="POST":
        print(request.form)
        username=request.form["uname"]
        uemail=request.form["email"]
        password=request.form["pwd"]
        cpassword=request.form["cpwd"]
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select count(*) from users where useremail=%s",[uemail])
        var1=cursor.fetchone() #fechall----list of records in tuple formate
        print(var1)
        if var1[0]==0:
           gotp=genotp() #calling function
           udata={"username":username,"uemail":uemail,"password":password,"otp":gotp}#here we have to give variable 
           subject="otp for simple notes app" #in body we have to pass only string formate otherwise we will get an error
           body=f"verify email by using the otp {gotp}"
           sendmail(to=uemail,subject=subject,body=body)
           flash("otp has send to your email")
           return redirect(url_for("otp",gotp=encode(data=udata))) 
        elif var1[0]>0:
            flash("email already exist")
            return redirect(url_for('login'))  
    return render_template("create.html")
@app.route("/otp/<gotp>",methods=["GET","POST"])
def otp(gotp):
    if request.method=="POST":
        uotp=request.form["otp"]
        try:
            dotp=decode(gotp)
            print(dotp)
        except Exception as e:
            return "something is wrong"
        if uotp==dotp:
            return redirect(url_for("login"))
        else:
            if uotp==dotp["otp"]:
                cursor=mydb.cursor(buffered=True)
                cursor.execute("insert into users(username,useremail,password) values(%s,%s,%s)",
                [dotp["username"],dotp["uemail"],dotp["password"]])
                mydb.commit()
                cursor.close()
                return redirect(url_for('login'))
            else:
                flash("wrong OTP")
                return redirect(url_for("create"))
    return render_template("otp.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if not session.get("user"):
        if request.method=="POST":
            uemail=request.form["email"]
            password=request.form["password"]
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select count(useremail) from users where useremail=%s",[uemail])
            bdata=cursor.fetchone()
            if bdata[0]==1:
                cursor.execute("select password from users where useremail=%s",[uemail])
                bpassword=cursor.fetchone()
                if password==bpassword[0].decode('utf-8'):
                    print(session)
                    session['user']=uemail
                    print(session)
                    return redirect(url_for('dashboard'))
                else:
                    flash("wrong password")
                    return redirect(url_for('login'))
            else:
                flash("the email you entered is not registered")
                return redirect(url_for('create'))
        return render_template('login.html')
    else:
        return redirect(url_for("dashboard"))
@app.route('/dashboard')
def dashboard():
    if session.get("user"):
        return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))
@app.route("/addnotes",methods=["GET","POST"])
def addnotes():
    if session.get("user"):
        if request.method=="POST":
            title=request.form["title"]
            description=request.form["content"]
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from users where useremail=%s",[session.get("user")])
            uid=cursor.fetchone()
            if uid:
                try:
                    cursor.execute("insert into notes(title,description,userid) values(%s,%s,%s)",
                    [title,description,uid[0]])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash("Dublicate title entry")
                    return redirect(url_for("dashboard"))
                else:
                    flash("notes added successfully")
                    return redirect(url_for("dashboard"))
            else:
                return "something went wrong to fetch uid"
        return render_template("addnotes.html")
    else:
        return redirect(url_for("login"))
@app.route("/view_all_notes")
def view_all_notes():
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from users where useremail=%s",[session.get("user")])
            uid=cursor.fetchone()
            cursor.execute("select nid,title,created_at from notes where userid=%s",[uid[0]])
            notesdata=cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
            flash("no data found")
            return redirect(url_for("dashboard"))
        else:
            return render_template("view_all_notes.html",notesdata=notesdata)
    else:
        return redirect(url_for("login"))
@app.route("/readnotes/<nid>")
def readnotes(nid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select * from notes where nid=%s",[nid])
            notesdata=cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            flash("notes not found")
            return redirect(url_for("dashboard"))
        else:
            return render_template("readnotes.html",notesdata=notesdata)
    else:
        return redirect(url_for("login"))
@app.route("/updatenotes/<nid>",methods=["GET","POST"])
def updatenotes(nid):
    if session.get("user"):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notes where nid=%s",[nid])
        notesdata=cursor.fetchone()
        if request.method=="POST":
            title=request.form["title"]
            content=request.form["description"]
            cursor.execute("update notes set title=%s , description=%s where nid=%s",
            [title,content,nid])
            mydb.commit()
            flash("notes updated successfully")
            return redirect(url_for("readnotes",nid=nid))
        return render_template('updatenotes.html',notesdata=notesdata)
    else:
        return redirect(url_for("login"))
@app.route("/deletenotes/<nid>")
def deletenotes(nid):
    if session.get("user"):
        try:
            cursor = mydb.cursor(buffered=True)
            # cursor.execute('select * from notes where n_id=%s',[n_id])
            # notesdata = cursor.fetchone()
            cursor.execute('delete from notes where nid=%s',[nid])
            notesdata = cursor.fetchone()
            mydb.commit()
            mydb.close()
        except Exception as e:
            print(e)
            flash('Notes is not Deleted')
            return redirect(url_for('dashboard'))
        else:
            flash('Notes deleted successfully')
            return redirect(url_for('view_all_notes',nid=nid))
    else:
        return redirect(url_for("login"))
@app.route("/uploadfile",methods=["GET","POST"])
def uploadfile():
    if session.get("user"):
        try:
            if request.method=="POST":
                filedata=request.files["file"]
                print(filedata)
                fdata=filedata.read()#here data is readed in byte format(yha content read hota) #fdata is wt we have uploaded
                filename=filedata.filename 
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select userid from users where useremail=%s",[session.get("user")])
                uid=cursor.fetchone()
                cursor.execute("insert into file_data(filename,fdata,added_by) values(%s,%s,%s)",[filename,fdata,uid[0]])
                mydb.commit()
                cursor.close()
                flash("file uploaded successfully")
                return redirect(url_for("dashboard"))
        except Exception as e:
            print(e)
            flash("unable to upload file")
            return redirect(url_for("dashboard"))
        else:
            return render_template("fileupload.html")
    else:
        return redirect(url_for("login"))
@app.route("/allfiles")
def allfiles():
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from users where useremail=%s",[session.get("user")])
            uid=cursor.fetchone()
            cursor.execute("select fid,filename, created_at from file_data where added_by=%s",[uid[0]])
            filesdata=cursor.fetchall()
        except Exception as e:
            print(e)
            flash("no files found")
            return redirect(url_for("dashboard"))
        else:
            return render_template("view_all_files.html",filesdata=filesdata)
    else:
        return redirect(url_for("login"))
@app.route("/viewfile/<fid>")
def viewfiles(fid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select filename,fdata from file_data where fid=%s",[fid])
            filedata=cursor.fetchone()
            bytes_data=BytesIO(filedata[1])
            return send_file(bytes_data,download_name=filedata[0],as_attachment=False) #reads file
        except Exception as e:
            print(e)
            flash("couldn't load file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("login"))
@app.route("/downloadfile/<fid>")
def downloadfile(fid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select filename,fdata from file_data where fid=%s",[fid])
            filedata=cursor.fetchone()
            bytes_data=BytesIO(filedata[1])
            return send_file(bytes_data,download_name=filedata[0],as_attachment=True) #reads file
        except Exception as e:
            print(e)
            flash("couldn't load file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("login"))
@app.route("/deletefile/<fid>")
def deletefile(fid):
    if session.get("user"):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('delete from file_data where fid=%s',[fid])
            notesdata = cursor.fetchone()
            mydb.commit()
            mydb.close()
        except Exception as e:
            print(e)
            flash('file is not Deleted')
            return redirect(url_for('dashboard'))
        else:
            flash('file deleted successfully')
            return redirect(url_for('view_all_files',fid=fid))
    else:
        return redirect(url_for("login"))
@app.route("/logout")
def logout():
    if session.get("user"):
        session.pop("user")
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))
@app.route("/getexceldata")
def getexceldata():
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from users where useremail=%s",[session.get("user")])
            uid=cursor.fetchone()
            cursor.execute("select nid,title,description,created_at from notes where userid=%s",[uid[0]])
            notesdata=cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
            flash("no data found")
            return redirect(url_for("dashboard"))
        else:
            array_data=[list(i) for i in notesdata]
            columns=["Notesid","Title","Description","Created_at"]
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,"xlsx",filename="notesdata")
    else:
        return redirect(url_for("login"))
@app.route("/search",methods=["GET","POST"])
def search():
    if session.get("user"):
        if request.method=="POST":
            search=request.form["searcheddata"]
            strg=["A-Za-z0-9"]
            pattern=re.compile(f'^{strg}',re.IGNORECASE) # cap(^) compares starting letters 
            if (pattern.match(search)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select * from notes where nid like %s or title like %s or description like %s or created_at like %s",
                [search+'%',search+'%',search+'%',search+'%'])#
                sdata=cursor.fetchall()
                cursor.close()
                return render_template("dashboard.html",sdata=sdata)
            else:
                flash("no data found")
                return redirect(url_for("dashboard"))
        else:
            return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))

app.run(debug=True,use_reloader=True)




