#!/usr/bin/python3
from cgi import FieldStorage
from steemax import web
import os
ip = os.environ["REMOTE_ADDR"]
response = FieldStorage().getvalue('g-recaptcha-response')
code = FieldStorage().getvalue('code')
account = FieldStorage().getvalue('account')
per = FieldStorage().getvalue('percentage')
ratio = FieldStorage().getvalue('ratio')
dur = FieldStorage().getvalue('duration')
print ("Content-type: text/html")
print (web.Web().invite(code, 
                        account, 
                        per, 
                        ratio, 
                        dur, 
                        response, 
                        ip))
