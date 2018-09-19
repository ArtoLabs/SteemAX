#!/usr/bin/python3
from cgi import FieldStorage
from steemax import web
code = FieldStorage().getvalue('code')
print ("Content-type: text/html")
print (web.Web().login(code))
