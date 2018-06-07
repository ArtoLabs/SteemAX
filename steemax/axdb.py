#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime, timedelta
from steemax import axmsg
import pymysql
import random
import sys
import re

xmsg = axmsg.AXmsg()

class AXdb:
    '''Used to retrieve and store data in the steemax MySQL database'''


    def __init__(self, dbuser, dbpass, dbname):
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.dbname = dbname


    def open_db(self):
        ''' opens a database connection
        '''
        self.db = pymysql.connect("localhost",self.dbuser,self.dbpass,self.dbname)
        self.cursor = self.db.cursor()


    def get_results(self):
        ''' Gets the results of an SQL statement
        '''
        try:
            self.cursor.execute(self.sql)
            self.dbresults = self.cursor.fetchall()
        except:
            e = sys.exc_info()[0]
            xmsg.error_message(e)
            self.dbresults = False
            self.db.rollback()
            return False
        return len(self.dbresults)


    def commit(self):
        ''' Commits the actions of an SQL statement to the database
        '''
        try:
            self.cursor.execute(self.sql)
            self.db.commit()
        except:
            e = sys.exc_info()[0]
            xmsg.error_message(e)
            self.db.rollback()
            return False
        return True


    def first_time_setup(self):
        '''Check to see if the the table named "axlist" is present in the database "steemax". If not make it.
        Check to see if the the table named "axglobal" is present in the database "steemax". If not make it and initialize it.
        '''
        self.open_db()
        self.sql = "SELECT * FROM axlist WHERE 1;"
        if not self.get_results():
            self.sql = ("CREATE TABLE IF NOT EXISTS axlist (ID int(10), Account1 varchar(50), Account2 varchar(50), Key1 varchar(100), Key2 varchar(100), Percentage varchar(5), Ratio varchar(5), Duration varchar(5), MemoID varchar(40), Status varchar(10), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            self.commit()
            xmsg.message("Created axlist table in the steemax database.")
        self.sql = "SELECT * FROM axglobal WHERE 1;"
        if not self.get_results():
            self.sql = ("CREATE TABLE IF NOT EXISTS axglobal (ID int(10), RewardBalance varchar(50), RecentClaims varchar(50), Base varchar(50), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            self.commit()
            self.sql = "INSERT INTO axglobal (ID, RewardBalance, RecentClaims, Base) VALUES ('1', '0', '0', '0');" 
            self.commit()
            xmsg.message("Created and initialized axglobal table in the steemax database.")
        self.sql = "SELECT * FROM axtrans WHERE 1;"
        if not self.get_results():
            self.sql = ("CREATE TABLE IF NOT EXISTS axtrans (ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, TXID varchar(50), MemoFrom varchar(20), Amount varchar(20), MemoID varchar(40), Action varchar(20), TxTime TIMESTAMP NULL, DiscoveryTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP);")
            self.commit()
            xmsg.message("Created axtrans table in the steemax database.")
        self.db.close()


    def get_most_recent_trans(self):
        ''' Returns the timestamp from the most recent memo id message. 
        '''
        self.open_db()
        self.sql = "SELECT TxTime FROM axtrans WHERE 1 ORDER BY TxTime DESC LIMIT 1;"
        if not self.get_results():
            self.db.close()
            return datetime.utcnow() - timedelta(days=5)
        else:
            self.db.close()
            return self.dbresults[0][0]


    def add_trans(self, txid, memofrom, amt, memoid, action, txtime):
        ''' Adds a processed transaction to the axtrans database table which is a history of all processed transactions
        '''
        self.open_db()
        self.sql = "INSERT INTO axtrans (TXID, MemoFrom, Amount, MemoID, Action, TxTime) VALUES ('"+txid+"', '"+memofrom+"', '"+amt+"', '"+memoid+"', '"+action+"', '"+txtime+"');" 
        self.commit()
        self.db.close()


    def check_reward_fund_renewal(self):
        ''' Checks the timestamp from the database to see if the stored info is stale (older than 120 seconds)
        '''
        delta = datetime.now() - self.dbresults[0][3]
        if delta.seconds > 120:
            return True
        else:
            return False


    def save_reward_fund(self, rb, rc, base):
        ''' Saves the current Reward Balance, Recent Claims and the price of STEEM in the database for quicker 
        retreival and less taxation on steem nodes.
        '''
        self.open_db()
        self.sql = "UPDATE axglobal SET RewardBalance = '"+str(rb)+"', RecentClaims = '"+str(rc)+"', Base = '"+str(base)+"' WHERE ID = '1';"
        r = self.commit()
        self.db.close()
        return r


    def fetch_reward_fund(self):
        ''' Retrives the Reward Balance, Recent Claims and the price of STEEM from the database instead of from
        the steem node
        '''
        self.open_db()
        self.sql = "SELECT RewardBalance, RecentClaims, Base, Time FROM axglobal WHERE ID = '1';"
        if not self.get_results():
            xmsg.error_message("Could not fetch reward fund.")
            self.db.close()
            return False
        else:
            self.db.close()
            return True


    def verify_memoid(self, acct0, memoid):
        self.open_db()
        '''Verify that the Memo ID entered matches the account name entered
        This is necessary so that each account can update the invite during the barter process
        '''
        acct1 = ""
        acct2 = ""
        # Get both account names if the Memo ID exists and verify the account given to the method.give a sendto account for passing transactions
        self.sql = "SELECT Account1, Account2, Status FROM axlist WHERE MemoID = '" + memoid + "';"
        if not self.get_results():
            xmsg.error_message("Could not find Memo ID.")
        else:
            acct1 = self.dbresults[0][0]
            acct2 = self.dbresults[0][1]
        if acct0 == acct1:
            self.sendto = acct2
        elif acct0 == acct2:
            self.sendto = acct1
        else:
            xmsg.error_message("Account does not match Memo ID.")
            self.db.close()
            return False
        # Does the account name match the Memo ID?
        if acct0!= acct1 and acct0 != acct2:
            xmsg.error_message("Verify Memo ID: Account names do not match.")
            self.db.close()
            return False
        else:
            self.db.close()
            return True


    def cancel (self, acct, memoid):
        self.open_db()
        ''' Either account can cancel
        '''
        self.sql = "DELETE FROM axlist WHERE (Account1 = '"+acct+"' OR (Account2 = '"+acct+"')) AND (MemoID = '"+memoid+"');"
        r = self.commit()
        self.db.close()
        return r


    def update_invite(self, percent, ratio, duration, memoid, status):
        self.open_db()
        '''This is used during the barter process. Both accounts can update the percentage,
        ratio and duration of the exchange until an agreement is made. This pauses the exchange
        and puts it into a status which indicates an agreement has not been made.
        Update the percentage, ratio and duration based on the Memo ID which is verified using
        the verify_memoid function.
        '''
        self.sql = ("UPDATE axlist SET Percentage = '" + str(percent) + "', Ratio = '" + str(ratio) + "', Duration = '" + 
            str(duration) + "', Status = '" + str(status) + "' WHERE MemoID = '" + str(memoid) + "';")
        r = self.commit()
        self.db.close()
        return r


    def update_status(self, status):
        ''' Updates the status of an exchange, specifically used if a barter has been started. The status numbers represent:
                -1 = waiting for inviter to authorize
                 0 = invite has beed sent. waiting for invitee to authorize
                 1 = exchange authorized by both parties, exchange is underway
                 2 = inviter (account1) has offered to barter
                 3 = invitee (account2) has offered to barter
                 4 = exchange has been cancelled
        '''
        self.open_db()
        self.sql = ("UPDATE axlist SET Status = '"+str(status)+"';")
        r = self.commit()
        self.db.close()
        return r


    def verify_account (self, acct, memoid):
        self.open_db()
        ''' Check to see if this is the inviter (Account1). If the account is an inviter show a report.
        Then check to see if this is the invitee (Account2). If the account is an invitee show a report.
        Return false if there are no entries in the database
        '''
        asinviter = 0
        asinvitee = 0
        inviter = ""
        invitee = ""
        self.sql = "SELECT Account2 FROM axlist WHERE Account1 = '" + acct + "'" # The ; gets added next steps
        if memoid:
            self.sql = self.sql + " AND (MemoID = '" + memoid + "');"
        else:
            self.sql = self.sql + ";"
        if self.get_results():
            xmsg.message(acct + " is the inviter of " + str(len(self.dbresults)) + " exchange(s)")
            asinviter = len(self.dbresults)
            invitee = self.dbresults[0][0]
        self.sql = "SELECT Account1 FROM axlist WHERE Account2 = '" + acct + "'" # The ; gets added next steps
        if memoid:
            self.sql = self.sql + " AND (MemoID = '" + memoid + "');"
        else:
            self.sql = self.sql + ";"
        if self.get_results():
            xmsg.message(acct + " is the invitee of " + str(len(self.dbresults)) + " exchange(s)")
            asinvitee = len(self.dbresults)
            inviter = self.dbresults[0][0]
        if not asinviter and not asinvitee:
            xmsg.message(acct + " is not in the database. Please start an invite.")
            self.db.close()
            return False
        self.db.close()
        return [asinviter, asinvitee, inviter, invitee]


    def check_status (self, memoid):
        ''' The check status method is used to determine if authorization requests are valid
        '''
        self.open_db()
        self.sql = "SELECT Status FROM axlist WHERE MemoID = '"+memoid+"';"
        if self.get_results():
            self.db.close()
            return self.dbresults[0][0]
        else:
            self.db.close()
            return False


    def verify_invitee (self, acct2, memoid):
        '''Check that account is truly an invitee (Account2) and not inviter (Account1)
        '''
        self.open_db()
        self.sql = "SELECT * FROM axlist WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
        if not self.get_results():
            xmsg.message(acct2 + " is not an invitee.")
            self.db.close()
            return False
        self.db.close()
        return True


    def accept_invite(self, acct2, memoid, key):
        self.open_db()
        '''The exchange is initiated when both accounts agree on the settings, and
        Account2 (invitee) has submitted the Memo ID along with their private
        posting key. If the invitee wishes to barter, this function is still invoked first
        then update_invite which pauses the exchange and sets the exchange status to "2" (see above)
        Update the private posting key and set the Status to "1" which indicates
        an agreement has been made and thus making the auto-upvote exchange active
        '''
        self.sql = "UPDATE axlist SET Key2 = '" + key + "', Status = '0' WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
        r = self.commit()
        self.db.close()
        return r


    def add_invite (self, acct1, acct2, key1, percent, ratio, duration):
        self.open_db()
        '''Adds the initial invite to the database and provides the unique Memo ID.
        Checks for duplicate accounts. Checks for duplicate invites.
        Adds both account names, the inviter's private posting key, the percentage, ratio and 
        the duration of the exchange. This sets the Status to "0" indicating that the invitation
        has not been accepted nor has a barter process been started. Returns the unique Memo ID.
        '''
        memoid = self.generate_nonce()
        if acct1 == acct2:
            xmsg.message("The same account name was entered for both accounts.")
            self.db.close()
            return False
        self.sql = ("SELECT * FROM axlist WHERE (Account1 = '" + acct1 + "' OR (Account1 = '" + acct2 + "')) AND (Account2 = '" + 
            acct1 + "' OR (Account2 = '" + acct2 + "'));")
        if self.get_results():
            xmsg.message("An exchange has already been made between these accounts.")
            self.db.close()
            return False
        self.sql = ("INSERT INTO axlist (Account1, Account2, Key1, Percentage, Ratio, Duration, MemoID, Status) VALUES ('" + acct1 + 
            "', '" + acct2 + "', '" + key1 + "', '" + percent + "', '" + ratio + "', '" + duration + "', '" + memoid + "', '-1');")
        if self.commit():
            self.db.close()
            return memoid
        else:
            self.db.close()
            return False


    def get_axlist (self, mode):
        ''' Gets all auto-upvote exchanges
        '''
        self.open_db()
        self.sql = """SELECT * FROM axlist WHERE 1;"""
        self.get_results()
        self.db.close()
        return self.dbresults


    def generate_nonce(self, length=32):
        '''Generates the unique Memo ID
        '''
        return ''.join([str(random.randint(0, 9)) for i in range(length)])


# Run as main

if __name__ == "__main__":

    a = AXdb("steemax", "SteemAX_pass23", "steemax")
    if a.fetch_reward_fund():
        xmsg.message(a.dbresults[0][0] + "\n" + a.dbresults[0][1] + "\n" + a.dbresults[0][2])
    else:
        xmsg.message("No results from database while testing axdb.py")

# EOF
