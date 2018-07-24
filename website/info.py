#!/usr/bin/python3
from cgi import FieldStorage
from steemax.web import Web
account = FieldStorage().getvalue('account')
code = FieldStorage().getvalue('code')
print ("Content-type: text/html")
print (Web().info_page(account))
