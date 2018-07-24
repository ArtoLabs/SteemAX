#!/usr/bin/python3

import random
import sys
import re
from dateutil.parser import parse
from datetime import datetime, timedelta
from steemax.db import DB
from steemax import default
from screenlogger.screenlogger import Msg


class AXdb(DB):


    def __init__ (self, dbuser, dbpass, dbname):
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.dbname = dbname
        self.msg = Msg(default.logfilename, 
                        default.logpath, 
                        default.msgmode)


    def first_time_setup (self):
        ''' Sets up all three needed tables if they do not
        already exist
        '''
        if not self.get_results("SELECT * FROM users WHERE 1;"):
            self.commit('CREATE TABLE IF NOT EXISTS users '
                + '(ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, '
                + 'Account varchar(50), PrivateKey varchar(100), '
                + 'RefreshToken varchar(400), Token varchar(400), '
                + 'Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
        if not self.get_results("SELECT * FROM axlist WHERE 1;"):
            self.commit('CREATE TABLE IF NOT EXISTS axlist '
                + '(ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, '
                + 'Account1 varchar(50), Account2 varchar(50), '
                + 'Percentage varchar(5), Ratio varchar(5), '
                + 'Duration varchar(5), MemoID varchar(100), '
                + 'Status varchar(10), '
                + 'Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
        if not self.get_results("SELECT * FROM axtrans WHERE 1;"):
            self.commit('CREATE TABLE IF NOT EXISTS axtrans '
                + '(ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, '
                + 'TXID varchar(50), MemoFrom varchar(20), '
                + 'Amount varchar(20), MemoID varchar(100), '
                + 'Action varchar(20), TxTime TIMESTAMP NULL, '
                + 'DiscoveryTime TIMESTAMP NOT NULL '
                + 'DEFAULT CURRENT_TIMESTAMP '
                + 'ON UPDATE CURRENT_TIMESTAMP);')


    def get_most_recent_trans (self):
        ''' Returns the timestamp from 
        the most recent memo id message. 
        '''
        if not self.get_results('SELECT TxTime FROM axtrans '
                            + 'WHERE 1 ORDER BY TxTime DESC LIMIT 1;'):
            return datetime.utcnow() - timedelta(days=5)
        else:
            return self.dbresults[0][0]


    def add_trans (self, txid, memofrom, amt, 
                    memoid, action, txtime):
        ''' Adds a processed transaction 
        to the axtrans database 
        '''
        return self.commit('INSERT INTO axtrans (TXID, MemoFrom, '
            + 'Amount, MemoID, Action, TxTime) '
            + 'VALUES (%s, %s, %s, %s, %s, %s);',
            txid, memofrom, amt,  memoid, action, txtime)
        

    def verify_memoid (self, acct0, memoid):
        '''Verify that the Memo ID entered 
        matches the account name entered. 
        '''
        if not self.get_results('SELECT Account1, Account2, '
                                + 'Status FROM axlist WHERE MemoID = %s;',
                                memoid):
            self.msg.error_message("Memo ID not in database.")
            return False
        if acct0 == self.dbresults[0][0]:
            self.sendto = self.dbresults[0][1]
            self.inviter = self.dbresults[0][0]
            self.invitee = self.dbresults[0][1]
        elif acct0 == self.dbresults[0][1]:
            self.sendto = self.dbresults[0][0]
            self.inviter = self.dbresults[0][1]
            self.invitee = self.dbresults[0][0]
        else:
            self.msg.error_message("Account does not match Memo ID.")
            return False
        return True


    def cancel (self, acct, memoid):
        ''' Either account can cancel
        '''
        return self.commit('DELETE FROM axlist WHERE %s IN '
            + '(Account1, Account2) AND (MemoID = %s);',
            acct, memoid)


    def get_invite (self, memoid):
        ''' Gets an invite from the database
        and returns it as a list
        '''
        if self.get_results("SELECT Percentage, Ratio, Duration, "
                        + "Status FROM axlist WHERE MemoID = %s;", 
                        memoid):
            return [self.dbresults[0][0], 
                    self.dbresults[0][1], 
                    self.dbresults[0][2], 
                    self.dbresults[0][3]]
        else:
            self.msg.error_message("No invite found for " + memoid)
            return [0, 0, 0, 0]


    def update_invite (self, percent, ratio, duration, memoid, status):
        ''' Updates and invite during
        the barter process
        '''
        return self.commit('UPDATE axlist SET Percentage = %s, '
            + 'Ratio = %s, Duration = %s, Status = %s WHERE MemoID = %s;',
            percent, ratio, duration, status, memoid)


    def update_status (self, status, memoid):
        '''
        -1 = waiting for inviter to authorize
         0 = invite sent. waiting for invitee
         1 = exchange authorized by both parties
         2 = inviter (account1) has offered to barter
         3 = invitee (account2) has offered to barter
         4 = exchange has been cancelled
        '''
        return self.commit("UPDATE axlist SET Status = %s WHERE MemoID = %s;", 
            status, memoid)


    def check_status (self, memoid):
        ''' Checks the status of an invite
        so that steemax knows how to react to
        a command
        '''
        if self.get_results("SELECT Status FROM axlist WHERE MemoID = %s;", 
                memoid):
            return self.dbresults[0][0]
        else:
            return False


    def get_user_token (self, acct):
        ''' Gets a user's SteemConnect tokens 
        and Private Posting Key
        '''
        if self.get_results("SELECT PrivateKey, Token, RefreshToken "
                            + "FROM users WHERE Account = %s;",
                            acct):
            return self.dbresults[0][1]
        else:
            return False


    def update_token (self, acct, accesstoken, refreshtoken):
        ''' Updates a user's SteemConnect tokens
        '''
        return self.commit("UPDATE users SET Token = %s, "
                            + "RefreshToken = %s WHERE Account = %s;",
                            accesstoken, refreshtoken, acct)


    def add_invite (self, acct1, acct2, percent, ratio, duration):
        '''Adds the initial invite to the database 
        and provides the unique Memo ID.
        '''
        memoid = self.generate_memoid()
        if acct1 == acct2:
            self.errmsg = ('The same account name was '
                        + 'entered for both accounts.')
            self.msg.error_message(self.errmsg)
            return False
        if self.get_results('SELECT * FROM axlist '
                        + 'WHERE %s IN (Account1, Account2) '
                        + 'AND (%s IN (Account1, Account2));',
                        acct1, acct2):
            self.errmsg = ('An exchange has already been '
                        + 'made between these accounts.')
            self.msg.error_message(self.errmsg)
            return False
        if self.commit('INSERT INTO axlist (Account1, Account2, '
                        + 'Percentage, Ratio, '
                        + 'Duration, MemoID, Status) '
                        + 'VALUES (%s, %s, %s, %s, %s, %s, %s);',
                        acct1, acct2, 
                        percent, ratio, duration, memoid, -1):
            return memoid
        else:
            return False


    def add_user (self, acct, key, refreshtoken, accesstoken):
        ''' Adds a user and their tokens/key to the database
        '''
        return self.commit('INSERT INTO users (Account, PrivateKey, '
                        + 'RefreshToken, Token) '
                        + 'VALUES (%s, %s, %s, %s);',
                        acct, key, refreshtoken, accesstoken)


    def get_axlist (self, account=None):
        ''' Gets the entire list of transactions
        to be processed
        '''
        if not account:
            self.get_results("SELECT * FROM axlist WHERE 1;")
        else:
            self.get_results('SELECT * FROM axlist '                    
                        + 'WHERE %s IN (Account1, Account2);',
                        account)
        return self.dbresults


    def generate_memoid (self, length=32):
        return ''.join([str(random.randint(0, 9)) for i in range(length)])

    

# EOF
