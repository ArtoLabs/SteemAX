#!/usr/bin/python3
from cgi import FieldStorage
from steemax.web import Web
account = FieldStorage().getvalue('account')
print ("Content-type: text/html")
print (Web().archive_page(account))
