#!/usr/bin/python3

import re
from steemax import axverify
from steemax import axdb
from steemax import default



class Web:



    def __init__ (self):
        self.verify = axverify.AXverify()
        self.db = axdb.AXdb(default.dbuser, 
                        default.dbpass, 
                        default.dbname)



    def template (self, templatefile="", **kwargs):
        fh = open(templatefile, 'r')
        template = fh.read()
        regobj = re.compile(
            r"^(.+)(?:\n|\r\n?)((?:(?:\n|\r\n?).+)+)", 
            re.MULTILINE)
        newtemplate = regobj.sub('', template)
        for key, value in kwargs.items():
            newtemplate = re.sub(str(key), 
                                str(value), 
                                newtemplate)
        return newtemplate



    def login (self, token):
        token = re.sub(r'[^A-Za-z0-9\-\_\.]', 
                        '', str(token))
        if (token is not None
                    and self.verify.steem.verify_key (
                    acctname="", tokenkey=token)):
            self.username = self.verify.steem.username
            if self.db.get_user_token(self.username):
                self.db.update_token(self.username, 
                            self.verify.steem.accesstoken, 
                            self.verify.steem.refreshtoken)
            else:
                self.db.add_user(self.username, 
                            self.verify.steem.privatekey, 
                            self.verify.steem.refreshtoken, 
                            self.verify.steem.accesstoken)

            return ("\r\n" + self.template("index.html", 
                                ACCOUNT1=self.username))
        else:
            url = self.verify.steem.connect.auth_url()
            return ("Location: " + url + "\r\n")



# EOF
