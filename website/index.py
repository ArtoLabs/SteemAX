#!/usr/bin/python3
from cgi import FieldStorage
from steemax import web
print ("Content-type: text/html")
print (web.Web().index_page())
