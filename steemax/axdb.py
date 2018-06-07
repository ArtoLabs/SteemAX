#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime, timedelta
from steemax import axmsg
from steemax.db import DB
import pymysql
import random
import sys
import re

xmsg = axmsg.AXmsg()

class AXdb(DB):
    '''Used to retrieve and store data in the steemax MySQL database'''


    def __init__(self, dbuser, dbpass, dbname):
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.dbname = dbname


    def first_time_setup(self):
        '''Check to see if the the table named "axlist" is present in the database "steemax". If not make it.
        Check to see if the the table named "axglobal" is present in the database "steemax". If not make it and initialize it.
        '''
        if not self.get_results("SELECT * FROM axlist WHERE 1;"):

            self.commit("CREATE TABLE IF NOT EXISTS axlist (ID int(10), Account1 varchar(50), Account2 varchar(50), Key1 varchar(100), Key2 varchar(100), Percentage varchar(5), Ratio varchar(5), Duration varchar(5), MemoID varchar(40), Status varchar(10), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

            xmsg.message("Created axlist table in the steemax database.")

        if not self.get_results("SELECT * FROM axglobal WHERE 1;"):

            self.commit("CREATE TABLE IF NOT EXISTS axglobal (ID int(10), RewardBalance varchar(50), RecentClaims varchar(50), Base varchar(50), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

            self.commit("INSERT INTO axglobal (ID, RewardBalance, RecentClaims, Base) VALUES ('1', '0', '0', '0');")

            xmsg.message("Created and initialized axglobal table in the steemax database.")

        if not self.get_results("SELECT * FROM axtrans WHERE 1;"):

            self.commit("CREATE TABLE IF NOT EXISTS axtrans (ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, TXID varchar(50), MemoFrom varchar(20), Amount varchar(20), MemoID varchar(40), Action varchar(20), TxTime TIMESTAMP NULL, DiscoveryTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP);")

            xmsg.message("Created axtrans table in the steemax database.")



    def get_most_recent_trans(self):
        ''' Returns the timestamp from the most recent memo id message. 
        '''
        if not self.get_results("SELECT TxTime FROM axtrans WHERE 1 ORDER BY TxTime DESC LIMIT 1;"):
            return datetime.utcnow() - timedelta(days=5)
        else:
            return self.dbresults[0][0]


    def add_trans(self, txid, memofrom, amt, memoid, action, txtime):
        ''' Adds a processed transaction to the axtrans database table which is a history of all processed transactions
        '''
        self.commit("INSERT INTO axtrans (TXID, MemoFrom, Amount, MemoID, Action, TxTime) VALUES ('"+txid+"', '"+memofrom+"', '"+amt+"', '"+memoid+"', '"+action+"', '"+txtime+"');")



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
        return self.commit("UPDATE axglobal SET RewardBalance = '"+str(rb)+"', RecentClaims = '"+str(rc)+"', Base = '"+str(base)+"' WHERE ID = '1';")



    def fetch_reward_fund(self):
        ''' Retrives the Reward Balance, Recent Claims and the price of STEEM from the database instead of from
        the steem node
        '''
        return self.get_results("SELECT RewardBalance, RecentClaims, Base, Time FROM axglobal WHERE ID = '1';")



    def verify_memoid(self, acct0, memoid):
        '''Verify that the Memo ID entered matches the account name entered
        This is necessary so that each account can update the invite during the barter process
        '''
        if not self.get_results("SELECT Account1, Account2, Status FROM axlist WHERE MemoID = '" + memoid + "';"):
            xmsg.error_message("Could not find Memo ID.")
            return False
        
        acct1 = self.dbresults[0][0] or None
        acct2 = self.dbresults[0][1] or None

        if acct0 == acct1:
            self.sendto = acct2
        elif acct0 == acct2:
            self.sendto = acct1
        else:
            xmsg.error_message("Account does not match Memo ID.")
            return False

        if acct0!= acct1 and acct0 != acct2:
            xmsg.error_message("Verify Memo ID: Account names do not match.")
            return False
        else:
            return True


    def cancel (self, acct, memoid):
        ''' Either account can cancel
        '''
        return self.commit("DELETE FROM axlist WHERE (Account1 = '"+acct+"' OR (Account2 = '"+acct+"')) AND (MemoID = '"+memoid+"');")



    def update_invite(self, percent, ratio, duration, memoid, status):
        '''This is used during the barter process. Both accounts can update the percentage,
        ratio and duration of the exchange until an agreement is made. This pauses the exchange
        and puts it into a status which indicates an agreement has not been made.
        Update the percentage, ratio and duration based on the Memo ID which is verified using
        the verify_memoid function.
        '''
        return self.commit("UPDATE axlist SET Percentage = '" + str(percent) + "', Ratio = '" + str(ratio) + "', Duration = '" + 
            str(duration) + "', Status = '" + str(status) + "' WHERE MemoID = '" + str(memoid) + "';")



    def update_status(self, status):
        ''' Updates the status of an exchange, specifically used if a barter has been started. The status numbers represent:
                -1 = waiting for inviter to authorize
                 0 = invite has beed sent. waiting for invitee to authorize
                 1 = exchange authorized by both parties, exchange is underway
                 2 = inviter (account1) has offered to barter
                 3 = invitee (account2) has offered to barter
                 4 = exchange has been cancelled
        '''
        return self.commit("UPDATE axlist SET Status = '"+str(status)+"';")



    def verify_account (self, acct, memoid):
        ''' Check to see if this is the inviter (Account1). If the account is an inviter show a report.
        Then check to see if this is the invitee (Account2). If the account is an invitee show a report.
        Return false if there are no entries in the database
        '''

        sql = "SELECT Account2 FROM axlist WHERE Account1 = '" + acct + "'"
        if memoid:
            sql = sql + " AND (MemoID = '" + memoid + "');"
        else:
            sql = sql + ";"

        if self.get_results(sql):
            xmsg.message(acct + " is the inviter of " + str(len(self.dbresults)) + " exchange(s)")
            asinviter = len(self.dbresults) or 0
            invitee = self.dbresults[0][0] or ""

        sql = "SELECT Account1 FROM axlist WHERE Account2 = '" + acct + "'"
        if memoid:
            sql = sql + " AND (MemoID = '" + memoid + "');"
        else:
            sql = sql + ";"

        if self.get_results(sql):
            xmsg.message(acct + " is the invitee of " + str(len(self.dbresults)) + " exchange(s)")
            asinvitee = len(self.dbresults) or 0
            inviter = self.dbresults[0][0] or ""

        if not asinviter and not asinvitee:
            xmsg.message(acct + " is not in the database. Please start an invite.")
            return False

        return [asinviter, asinvitee, inviter, invitee]


    def check_status (self, memoid):
        ''' The check status method is used to determine if authorization requests are valid
        '''
        if self.get_results("SELECT Status FROM axlist WHERE MemoID = '"+memoid+"';"):
            return self.dbresults[0][0]
        else:
            return False


    def verify_invitee (self, acct2, memoid):
        '''Check that account is truly an invitee (Account2) and not inviter (Account1)
        '''
        if not self.get_results("SELECT * FROM axlist WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"):
            xmsg.message(acct2 + " is not an invitee.")
            return False
        else:
            return True


    def accept_invite(self, acct2, memoid, key):
        '''The exchange is initiated when both accounts agree on the settings, and
        Account2 (invitee) has submitted the Memo ID along with their private
        posting key. If the invitee wishes to barter, this function is still invoked first
        then update_invite which pauses the exchange and sets the exchange status to "2" (see above)
        Update the private posting key and set the Status to "1" which indicates
        an agreement has been made and thus making the auto-upvote exchange active
        '''
        return self.commit("UPDATE axlist SET Key2 = '" + key + "', Status = '0' WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');")



    def add_invite (self, acct1, acct2, key1, percent, ratio, duration):
        '''Adds the initial invite to the database and provides the unique Memo ID.
        Checks for duplicate accounts. Checks for duplicate invites.
        Adds both account names, the inviter's private posting key, the percentage, ratio and 
        the duration of the exchange. This sets the Status to "0" indicating that the invitation
        has not been accepted nor has a barter process been started. Returns the unique Memo ID.
        '''
        memoid = self.generate_nonce()
        if acct1 == acct2:
            xmsg.message("The same account name was entered for both accounts.")
            return False

        if self.get_results("SELECT * FROM axlist WHERE (Account1 = '" + acct1 + "' OR (Account1 = '" + acct2 + "')) AND (Account2 = '" + 
            acct1 + "' OR (Account2 = '" + acct2 + "'));"):
            xmsg.message("An exchange has already been made between these accounts.")
            return False

        if self.commit("INSERT INTO axlist (Account1, Account2, Key1, Percentage, Ratio, Duration, MemoID, Status) VALUES ('" + acct1 + 
            "', '" + acct2 + "', '" + key1 + "', '" + percent + "', '" + ratio + "', '" + duration + "', '" + memoid + "', '-1');"):
            return memoid
        else:
            return False


    def get_axlist (self, mode):
        ''' Gets all auto-upvote exchanges
        '''
        self.get_results("SELECT * FROM axlist WHERE 1;")
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
