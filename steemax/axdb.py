#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime
import pymysql
import random

class AXdb:
    '''Used to retrieve and store data in the steemax MySQL database'''


    def __init__(self, dbuser, dbpass, dbname):
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.dbname = dbname

        self.db = pymysql.connect("localhost",self.dbuser,self.dbpass,self.dbname)
        self.cursor = self.db.cursor()


    def __del__(self):
        self.db.close()


    def x_get_results(self):
        try:
            self.cursor.execute(self.sql)
            self.results = self.cursor.fetchall()
        except pymysql.InternalError as e:
            self.results = False
            self.db.rollback()
            return e
        return True


    def x_commit(self):
        try:
            self.cursor.execute(self.sql)
            self.db.commit()
        except pymysql.InternalError as e:
            self.db.rollback()
            return e
        return True


    def x_first_time_setup(self, mode):
        '''Check to see if the the table named "axlist" is present in the database "steemax". If not make it.
            Check to see if the the table named "axglobal" is present in the database "steemax". If not make it and initialize it.
        '''
        self.sql = "SELECT * FROM axlist WHERE 1;"
        if not self.x_get_results():
            self.sql = ("CREATE TABLE IF NOT EXISTS axlist (ID int(10), Account1 varchar(50), Account2 varchar(50), " +
                "Key1 varchar(100), Key2 varchar(100), Percentage varchar(5), Ratio varchar(5), Duration varchar(5), " +
                "MemoID varchar(40), Status varchar(10), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            self.x_commit()
            if mode != "quiet":
                print ("Created and initialized axlist table in the steemax database.")
        self.sql = "SELECT * FROM axglobal WHERE 1;"
        if not self.x_get_results():
            self.sql = ("CREATE TABLE IF NOT EXISTS axglobal (ID int(10), RewardBalance varchar(50), RecentClaims varchar(50), " +
                "Base varchar(50), Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            self.x_commit()
            self.sql = "INSERT INTO axglobal (ID, RewardBalance, RecentClaims, Base) VALUES ('1', '0', '0', '0');" 
            self.x_commit()
            if mode != "quiet":
                print ("Created and initialized axglobal table in the steemax database.")


    def x_check_reward_fund_renewal(self, time):
        delta = datetime.now() - time
        if delta.seconds > 120:
            return True
        else:
            return False


    def x_save_reward_fund(self, rb, rc, base, mode):
        self.sql = "UPDATE axglobal SET RewardBalance = '"+str(rb)+"', RecentClaims = '"+str(rc)+"', Base = '"+str(base)+"' WHERE ID = '1';"
        return self.x_commit()


    def x_fetch_reward_fund(self, mode):
        self.sql = "SELECT RewardBalance, RecentClaims, Base, Time FROM axglobal WHERE ID = '1';"
        if not self.x_get_results():
            if mode != "quiet":
                print ("Could not fetch reward fund.")
        return self.results[0]


    def x_verify_memoid(self, acct, memoid, mode):
        '''Verify that the Memo ID entered matches the account name entered
        This is necessary so that each account can update the invite during the barter process
        '''
        acct1 = ""
        acct2 = ""
        # Get both account names if the Memo ID exists
        self.sql = "SELECT Account1, Account2 FROM axlist WHERE MemoID = '" + memoid + "';"
        if not self.x_get_results():
            if mode != "quiet":
                print ("Could not find Memo ID.")
        else:
            for row in self.results:
                acct1 = row[0]
                acct2 = row[1]
        # Does the account name match the Memo ID?
        if acct != acct1 and acct != acct2:
            if mode != "quiet":
                print ("Verify Memo ID: Account names do not match.")
            return False
        else:
            return True


    def x_cancel (self, acct, memoid, mode):
        '''Either account can cancel
        '''
        self.sql = "DELETE FROM axlist WHERE (Account1 = '"+acct+"' OR (Account2 = '"+acct+"')) AND (MemoID = '"+memoid+"');"
        return self.x_commit()


    def x_update_invite(self, percent, ratio, duration, memoid, mode):
        '''This is used during the barter process. Both accounts can update the percentage,
        ratio and duration of the exchange until an agreement is made. This pauses the exchange
        and puts it into a status of "2" which indicates an agreement has not been made.
        Update the percentage, ratio and duration based on the Memo ID which is verified using
        the x_verify_memoid function.
        '''
        self.sql = ("UPDATE axlist SET Percentage = '" + percent + "', Ratio = '" + ratio + "', Duration = '" + 
            duration + "', Status = '2' WHERE MemoID = '" + memoid + "';")
        return self.x_commit()


    def x_verify_account (self, acct, memoid, mode):
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
        if self.x_get_results():
            if mode != "quiet":
                print (acct + " is the inviter of " + str(len(self.results)) + " exchange(s)")
            asinviter = len(self.results)
            invitee = self.results1[0][0]
        self.sql = "SELECT Account1 FROM axlist WHERE Account2 = '" + acct + "'" # The ; gets added next steps
        if memoid:
            self.sql = self.sql + " AND (MemoID = '" + memoid + "');"
        else:
            self.sql = self.sql + ";"
        if self.x_get_results():
            if mode != "quiet":
                print (acct + " is the invitee of " + str(len(self.results)) + " exchange(s)")
            asinvitee = len(self.results)
            inviter = self.results[0][0]
        if not asinviter and not asinvitee:
            if mode != "quiet":
                print (acct + " is not in the database. Please start an invite.")
            return False
        return [asinviter, asinvitee, inviter, invitee]


    def x_verify_invitee (self, acct2, memoid, mode):
        '''Check that account is truly an invitee (Account2) and not inviter (Account1)
        '''
        self.sql = "SELECT * FROM axlist WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
        if not self.x_get_results():
            if mode != "quiet":
                print (acct2 + " is not an invitee.")
            return False
        return True


    def x_accept_invite(self, acct2, memoid, key, mode):
        '''The exchange is initiated when both accounts agree on the settings, and
        Account2 (invitee) has submitted the Memo ID along with their private
        posting key. If the invitee wishes to barter, this function is still invoked first
        then x_update_invite which pauses the exchange and sets the exchange status to "2" (see above)
        Update the private posting key and set the Status to "1" which indicates
        an agreement has been made and thus making the auto-upvote exchange active
        '''
        self.sql = "UPDATE axlist SET Key2 = '" + key + "', Status = '1' WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
        return self.x_commit()


    def x_add_invite (self, acct1, acct2, key1, percent, ratio, duration, mode):
        '''Adds the initial invite to the database and provides the unique Memo ID.
        Checks for duplicate accounts. Checks for duplicate invites.
        Adds both account names, the inviter's private posting key, the percentage, ratio and 
        the duration of the exchange. This sets the Status to "0" indicating that the invitation
        has not been accepted nor has a barter process been started. Returns the unique Memo ID.
        '''
        memoid = self.generate_nonce()
        if acct1 == acct2:
            if mode != "quiet":
                print ("The same account name was entered for both accounts.")
            return False
        self.sql = ("SELECT * FROM axlist WHERE (Account1 = '" + acct1 + "' OR (Account1 = '" + acct2 + "')) AND (Account2 = '" + 
            acct1 + "' OR (Account2 = '" + acct2 + "'));")
        if self.x_get_results():
            if mode != "quiet":
                print ("An exchange has already been made between these accounts.")
            return False
        self.sql = ("INSERT INTO axlist (Account1, Account2, Key1, Percentage, Ratio, Duration, MemoID, Status) VALUES ('" + acct1 + 
            "', '" + acct2 + "', '" + key1 + "', '" + percent + "', '" + ratio + "', '" + duration + "', '" + memoid + "', '0');")
        if self.x_commit():
            return memoid
        else :
            return False


    def get_axlist (self, mode):
        self.sql = """SELECT * FROM axlist WHERE 1;"""
        return self.x_get_results()


    def generate_nonce(self, length=32):
        '''Generates the unique Memo ID
        '''
        return ''.join([str(random.randint(0, 9)) for i in range(length)])


# Run as main

if __name__ == "__main__":

    a = AXdb("steemax", "SteemAX_pass23", "steemax")
    b = a.x_fetch_reward_fund("")
    print (b[0] + "\n" + b[1] + "\n" + b[2])

# EOF

