#!/usr/bin/python3

import re
import urllib3
import json
from urllib.parse import urlencode
from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem
from steemax import axdb
from steemax import axverify
from steemax import default
from steemax import sec


class Web:
    def __init__(self):
        self.steem = SimpleSteem(
            client_id=default.client_id,
            client_secret=default.client_secret,
            callback_url=default.callback_url,
            screenmode=default.msgmode)
        self.db = axdb.AXdb(
            default.dbuser,
            default.dbpass,
            default.dbname)
        self.msg = Msg(default.logfilename,
                       default.logpath,
                       default.msgmode)
        self.json_resp = None

    def load_template(self, templatefile=""):
        """ opens a template file and loads it
        into memory stored in a variable
        """
        templatepath = default.webpath + "/" + templatefile
        with open(templatepath, 'r') as fh:
            try:
                template = fh.read()
            except Exception as e:
                self.msg.error_message(e)
                return None
            else:
                return template

    def make_page(self, template, **kwargs):
        """ Fills in key / value pairs on a 
        given template
        """
        regobj = re.compile(
            r"^(.+)(?:\n|\r\n?)((?:(?:\n|\r\n?).+)+)",
            re.MULTILINE)
        newtemplate = regobj.sub('', template)
        for key, value in kwargs.items():
            newtemplate = re.sub(str(key),
                                 str(value),
                                 newtemplate)
        return newtemplate

    def index_page(self):
        """ Creates the Home page for SteemAX and includes
        the number of users and the number of exchanges.
        """
        return ("\r\n"
                + self.make_page(self.load_template(
                    "templates/index.html"),
                    USERS=self.db.number_of_users(),
                    EXCHANGES=self.db.number_of_exchanges()))

    def login(self, token, dest="home"):
        """ logs a user in using SteemConnect
        adds the user to the database if it's
        their first time.
        """
        if self.verify_token(token):
            if self.db.get_user_token(self.steem.username):
                self.db.update_token(self.steem.username,
                                     self.steem.accesstoken,
                                     self.steem.refreshtoken)
            else:
                self.db.add_user(self.steem.username,
                                 self.steem.privatekey,
                                 self.steem.refreshtoken,
                                 self.steem.accesstoken)
            if dest == "info":
                return ("\r\n"
                        + self.info_page(self.steem.username))
            else:
                return ("\r\n"
                        + self.make_page(self.load_template(
                            "templates/invite_form.html"),
                            ACCOUNT1=self.steem.username,
                            REFRESHTOKEN=self.steem.refreshtoken,
                            INVITECOUNT=self.db.number_of_invites(self.steem.username)))
        else:
            return self.auth_url()

    def invite(self, token, account2, per,
               ratio, dur, response, ip, ajax):
        """ Creates an invite. First we filter the users
        data then we create the invite in the database.
        If the request was sent via ajax then the returned
        result is simply the number one to indicate success.
        """
        ajax = sec.filter_number(int(ajax))
        response = sec.filter_token(response)
        per = sec.filter_number(per)
        ratio = sec.filter_number(ratio, 1000)
        dur = sec.filter_number(dur, 365)
        if not self.verify_recaptcha(response, ip):
            return self.error_page("Invalid captcha.", ajax)
        if float(per) < 1 or float(per) > 100:
           return self.error_page("The percentage can not be lower then "
                                + "1 or greater than 100 and must be a whole number.", ajax)    
        if float(dur) < 7 or float(dur) > 365:
           return self.error_page("The duration must be between 7 and 365 days.", ajax)
        if float(ratio) < 0.001 or float(ratio) > 1000:
           return self.error_page("The ratio must be between 0.001 and 1000 to 1.", ajax)
        if self.verify_token(sec.filter_token(token)):
            account2 = sec.filter_account(account2)
            if self.steem.account(account2) is False:
                return self.error_page(account2 
                    + " is an invalid account name.", ajax)
            else:
                verify = axverify.AXverify()
                if verify.eligible_votes(self.steem.username, account2, per, ratio, 1) is False:
                    return self.error_page(verify.response, ajax)
                memoid = self.db.add_invite(self.steem.username, account2, per, ratio, dur)
                if memoid is False:
                    return self.error_page(self.db.errmsg, ajax)
                elif int(memoid) > 0:
                    if (int(ajax) == 1):
                        return "\r\n1"
                    else:
                        return ("Location: https://steemax.info/@"
                                + self.steem.username + "\r\n")
        else:
            return self.auth_url()

    def archive_page(self, account=None):
        """ Provides a list of all the exchanges that
        have occured for a particular account. if
        no account is provided then a list of all exchanges
        for all accounts is returned.
        """
        infobox = ""
        if account is not None:
            account = sec.filter_account(account)
            # If the token is invalid return user to the login page
            if not self.db.get_user_token(account):
                return self.auth_url()
        axlist = self.db.get_exchange_archive(account)
        boxtemplate = self.load_template("templates/archivebox.html")
        for trade in axlist:
            date = (str(trade[6].strftime("%B")) + " "
                    + str(trade[6].day) + ", "
                    + str(trade[6].year))
            time = (str(trade[6].hour) + ":"
                    + str(trade[6].minute))
            box = self.make_page(boxtemplate,
                                 DATE=date,
                                 TIME=time,
                                 ACCOUNT1=trade[0],
                                 ACCOUNT2=trade[1],
                                 IDENT1=trade[2],
                                 IDENT2=trade[3],
                                 VOTEVALUE1=trade[4],
                                 VOTEVALUE2=trade[5])
            infobox = infobox + box
        pagetemplate = self.load_template("templates/archive.html")
        # If the account was provide we display it with the @
        # however if it's not we convert it to an empty string
        # so that it is not displayed in HTML
        if account is None:
            account = ""
        else:
            account = "@" + account
        return ("\r\n" + self.make_page(pagetemplate,
                                        ACCOUNT=account,
                                        INFOBOX=infobox))

    def info_page(self, account):
        """ Creates the page at steemax.info that displays
        all the exchanges a user is involved in and which
        provides the options to accept, barter or cancel a 
        particular exchange.
        """
        account = sec.filter_account(account)
        if not self.db.get_user_token(account):
            return self.auth_url()
        axlist = self.db.get_axlist(account)
        boxtemplate = self.load_template("templates/infobox.html")
        infobox = ""
        invitee = 0
        myaccount = ""
        otheraccount = ""
        buttoncode = ""
        exp = ""
        sendall = []
        acceptall = []
        cancelall = []
        for value in axlist:
            if account == value[2]:
                invitee = 1
                otheraccount = value[1]
                myaccount = value[2]
            else:
                invitee = 0
                otheraccount = value[2]
                myaccount = value[1]
            buttoncode = """
                <div class="closemodal-info" onClick="command('{}', '{}', '{}')">&times;</div>
                """.format(
                value[0],
                otheraccount,
                "cancel")
            cancelall.append(value[0])
            if int(value[7]) == -1 and invitee == 0:
                buttoncode += """
                <div class="send-button" onClick="command('{}', '{}', '{}')">Send</div>
                    """.format(
                    value[0],
                    otheraccount,
                    "start")
                sendall.append(value[0])
            if ((int(value[7]) == 0 and invitee == 1)
                    or (int(value[7]) == 2 and invitee == 1)
                    or (int(value[7]) == 3 and invitee == 0)):
                buttoncode += """
                <div class="accept-button" onClick="command('{}', '{}', '{}')">Accept</div>
                <div class="barter-button" onClick="barter_window('{}');">Barter</div>
                    """.format(
                    value[0],
                    otheraccount,
                    "accept",
                    value[0])
                acceptall.append(value[0])
            elif ((int(value[7]) == 0 and invitee == 0)
                    or (int(value[7]) == 3 and invitee == 1)
                    or (int(value[7]) == 2 and invitee == 0)):
                buttoncode += '<div id="pending">Pending</div>\n'
            if int(value[7]) == 1:
                buttoncode += '<div id="pending">Active</div>\n'
                exp = "Expires " + self.db.expiration_date(value[8], value[5])
            else:
                exp = value[5] + " days"
            if int(value[7]) != 4 and not (int(value[7]) == -1 and invitee == 1):
                box = self.make_page(boxtemplate,
                                    AXID=value[0],
                                    ACCOUNT1=value[1],
                                    ACCOUNT2=value[2],
                                    PERCENTAGE=value[3],
                                    DURATION=exp,
                                    DARATIO=value[4],
                                    MEMOID=value[6],
                                    INVITEE=invitee,
                                    OTHERACCOUNT=otheraccount,
                                    MYACCOUNT=myaccount,
                                    BTNCODE=buttoncode)
                infobox = infobox + box
        pagetemplate = self.load_template("templates/info.html")
        return ("\r\n" + self.make_page(pagetemplate, 
                                    ACCOUNT1=account,
                                    SENDALL=','.join(map(str, sendall)),
                                    CANCELALL=','.join(map(str, cancelall)),
                                    ACCEPTALL=','.join(map(str, acceptall)),
                                    INFOBOX=infobox))

    def verify_token(self, token):
        """ cleans and verifies a SteemConnect
        refresh token
        """
        token = sec.filter_token(token)
        if (token is not None
            and self.steem.verify_key(
                acctname="", tokenkey=token)):
            return True
        else:
            return False

    def auth_url(self):
        """ Returns the SteemConnect authorization
        URL for SteemAX
        """
        url = self.steem.connect.auth_url()
        return "Location: " + url + "\r\n"

    def error_page(self, msg, ajax):
        """ Returns the HTML page with the
        given error message
        """
        if (int(ajax) == 1):
            return "\r\n"+msg
        else:
            msg += ("<br><br>You may be receiving this error in this format "
                + "because you have disabled javascript. Please enable javascript "
                + "for a better user experience.")
            return ("\r\n"
                    + self.make_page(
                        self.load_template("templates/error.html"),
                        ERRORMSG=msg))

    def verify_recaptcha(self, response, remoteip):
        """ Verifies a Google recaptcha v2 token
        """
        http = urllib3.PoolManager()
        encoded_args = urlencode({'secret': default.recaptcha_secret,
                                  'response': response,
                                  'remoteip': remoteip})
        url = default.recaptcha_url + "?" + encoded_args
        req = http.request('POST', url)
        if req.status == 200:
            self.json_resp = json.loads(req.data.decode('utf-8'))
        if self.json_resp['success']:
            return True
        else:
            return False

# EOF
