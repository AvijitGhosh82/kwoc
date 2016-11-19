from flask import Flask, render_template, url_for, request, session, redirect
from flask_session import Session
import os
import psycopg2
import traceback
import json
import requests
import sys
from send_mail import send_mail

try:
    import urlparse
except Exception as e:
    from urllib import parse as urlparse

if "LOCAL_CHECK" in os.environ:
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    cursor = conn.cursor()

app = Flask(__name__)
sess = Session()


# @app.route("/student-register", methods=['GET', 'POST'])
def student_register(request):
    flag = None
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
        msg = "Database Connection cannot be set since you are running website locally"
        msgcode = 0
        return {"web": 'index.html' , "flag":"True", "msg":msg,"msgcode":msgcode}

    if request.method == "POST":
        form_dict = request.form.to_dict()
        query = "INSERT INTO student (f_name,l_name,email_id,roll_no,git_handle) values ('%s','%s','%s','%s','%s') " % (
            form_dict["fname"], form_dict["lname"], form_dict["emailid"], form_dict["rollno"], form_dict["githubhandle"])

        try:
            cursor.execute(query)
            conn.commit()
            mail_subject = "Successfully registered for Kharagpur Winter of Code!"
            mail_body = 'Hello ' + form_dict["fname"] + '<br>You have been successfully registered for the <b>Kharagpur Winter of Code</b>. ' + \
                        'Check out the <a href="http://kwoc.kossiitkgp.in/resources">Resources for KWoC</a> now.'
            mail_check = send_mail(
                mail_subject, mail_body, form_dict["emailid"])
            if not mail_check:
                slack_notification("Unable to send mail to the following student :\n{}".format(
                    form_dict))
            flag="True"
            msg=form_dict["fname"] + ", You have been successfully registered. Please check your email for instructions."
            msgcode=1
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
        except psycopg2.IntegrityError:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed ! User already registered"
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
        except:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed ! Please try again."
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}

# @app.route("/project-register", methods=['GET', 'POST'])
def project_register(request):
    flag = None
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
        msg = "Database Connection cannot be set since you are running website locally"
        msgcode = 0
        flag="True"
        return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
    if request.method == "POST":
        form_dict = request.form.to_dict()
        index = form_dict['plink'].find("github.com/")
        phandle = form_dict['plink'][index + 11:]
        query = "INSERT INTO project (f_name,l_name,email_id,project_link,project_name,project_handle, project_description) values ('%s','%s','%s','%s','%s','%s', '%s') " % (
            form_dict["fname"], form_dict["lname"], form_dict["emailid"], form_dict["plink"], form_dict["pname"], phandle, form_dict["pdesc"])

        try:
            cursor.execute(query)
            conn.commit()
            mail_subject = "Registered " + form_dict["pname"] + " for KWoC!"
            mail_body = "Hello " + form_dict["fname"] + '<br>Thank you for registering your project on KWoC.\n\n' + \
                        'Check out the <a href="http://kwoc.kossiitkgp.in/resources">Resources for KWoC</a> to get started with.'
            mail_check = send_mail(
                mail_subject, mail_body, form_dict["emailid"])
            if not mail_check:
                slack_notification("Unable to send mail to the following project :\n{}\nGot the follwing error :\n{}".format(
                    form_dict, traceback.format_exc()))
            flag="True"
            msg="Your project " + form_dict["pname"] + " has been successfully registered. Please check your email for instructions."
            msgcode=1
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
        except psycopg2.IntegrityError:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed ! Project already exists"
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}

        except:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed !"
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}

@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "POST" :
        if "plink" in request.form.to_dict() :
            reg_dict = project_register(request)
            return render_template('index.html' , flag=reg_dict["flag"] , msg=reg_dict["msg"],msgcode=reg_dict["msgcode"])
        else :
            reg_dict = student_register(request)
            return render_template('index.html' , flag=reg_dict["flag"] , msg=reg_dict["msg"],msgcode=reg_dict["msgcode"])
    else :
        return render_template('index.html')

@app.route("/resources")
def resources():
    return render_template('resources.html')

@app.route("/resources/timeline")
def timeline():
    return render_template('timeline.html')

@app.route("/resources/manuals")
def manuals():
    return render_template('manuals.html')

@app.route("/resources/social")
def social():
    return render_template('social.html')

@app.route("/resources/media")
def media():
    return render_template('media.html')

@app.route("/resources/faq")
def faq():
    return render_template('faq.html')

@app.route("/resources/contact")
def contact():
    return render_template('contact.html')


@app.route("/index")
def index():
    return render_template('index.html')


# if __name__ == "__main__":
def slack_notification(message):
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "text": "In KWOC Website following error occured :\n{}".format(message)
    })
    r = requests.post(
        os.environ["SLACK_WEBHOOK_URL"], headers=headers, data=data)

    if r.status_code != 200:
        print("in slack_notification : {}".format(r.status_code))
        print(r.text)
app.secret_key = 'kwoc'
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)
app.debug = True
# app.run()
