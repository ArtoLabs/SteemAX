#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime
from steem import Steem
from steembase import exceptions
import re
import axmsg
import axdb
import sys
import os

nodes = [


    'https://steemd.pevo.science',
    'https://steemd.minnowsupportproject.org',
    'https://steemd.steemgigs.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com'
    
]

xdb = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
xmsg = axmsg.AXmsg()
s = Steem(nodes)

steemaxacct = "artturtle"


class Reaction():


    def start(self, acct1, acct2, memofrom, rstatus):    
        if acct1 == memofrom:
            if rstatus < 0:
                self.reaction = "started"
                self.status = 0
                self.returnmsg = ("Hello " + acct2 + ", " + acct1 + " has invited you to an auto-upvote exchange. To respond to this " +
                    "invite please visit [link]")
            else:
                self.ignore("The inviter has already authorized this exchange.")
        else:
            self.ignore("Invalid action. The inviter has not yet authorized this exhange.")


    def accept(self, acct2, memofrom):
        if acct2 == memofrom:
            self.reaction = "accepted"
            self.status = 1
            self.returnmsg = acct2 + " has accepted the invite. The auto-upvote exchange will begin immediately."
        else:
            self.ignore("Please wait for the invitee to respond.")


    def barter(self, acct1, acct2, mf, rstatus, per, ratio, dur):
        if acct1 == mf and rstatus == 3:
            self.reaction = "acct1 bartering"
            self.status = 2
            self.returnmsg = (acct1 + " has offered to barter. They offer " + per + 
                "% of their upvote at a ratio of " + ratio + ":1 for " + dur + " days. " +
                "Send any amount along with the memo code '" + memoid + ":accept' to accept this offer.")
        elif acct2 == mf and rstatus == 2:
            self.reaction = "acct2 bartering"
            self.status = 3
            self.returnmsg = (acct2 + " has offered to barter. They suggest a percentage of " + per + 
                "% of your upvote at a ratio of " + ratio + "("+acct1+"):1("+acct2+") for " + dur + " days. " +
                "Send any amount along with the memo code '" + memoid + ":accept' to accept this offer.")
        else:
            self.ignore("Invalid barter. Please wait for the other side to respond first.")


    def cancel(self, canceller):
        self.reaction = "cancelled"
        self.status = 4
        self.returnmsg = canceller + " has cancelled the exchange."

    def ignore(self, reason):
        self.reaction = "refund"
        self.returnmsg = reason



class AXtrans:
    ''' Class for automatically handling transactions made to steemax for authentication
    '''

    def __init__(self):
        self.memoid=None
        self.action=None
        self.percentage=None
        self.ratio=None
        self.duration=None


    def x_parse_memo(self, memofrom=None, memo=None, amt=None, trxid=None, txtime=None):
        self.memofrom=memofrom
        self.amt=amt
        self.trxid=trxid
        self.txtime=txtime
        # Ew this is dirty and came from strangers! Must be sanitized!
        memo = memo.split(":")
        self.memoid = memo[0]
        if len(memo) > 1:
            self.action = memo[1]
        if len(memo) == 5:
            self.percentage = memo[2]
            self.ratio = memo[3]
            self.duration = memo[4]


    def x_send(self, to="artopium", amt="0.001 SBD", msg="test"):
        r = amt.split(" ")
        try:
            s.commit.transfer(to, float(r[0]), r[1], msg, steemaxacct)
        except exceptions.RPCError as e:
            xmsg.x_error_message(exceptions.decodeRPCErrorMsg(e))
            return False
        except:
            e = sys.exc_info()[0]
            xmsg.x_error_message(e)
            return False
        else:
            print ("Transaction committed. Sent " + r[0] + " " + r[1] + " to " + to + " with the memo: " + msg)
            return True


    def x_fetch_history(self):
        ''' Grabs the transaction history to see what's been sent to steemax.
        Currently using @artturtle account for testing. Replace with the account of choice
        '''
        last_trans_time = xdb.x_get_most_recent_trans()
        react = Reaction()
        h = s.get_account_history(steemaxacct, -1, 100)
        for a in h:
            this_trans_time = datetime.strptime(a[1]['timestamp'], '%Y-%m-%dT%H:%M:%S')
            if a[1]['op'][0] == 'transfer' and this_trans_time > last_trans_time:
                self.x_parse_memo(a[1]['op'][1]['from'], a[1]['op'][1]['memo'], a[1]['op'][1]['amount'], a[1]['trx_id'], a[1]['timestamp'])
                if a[1]['op'][1]['to'] == steemaxacct and re.match(r'^\s*[0-9]{32}$', self.memoid):
                    if xdb.x_verify_memoid(self.memofrom, self.memoid):
                        acct1 = xdb.dbresults[0][0]
                        acct2 = xdb.dbresults[0][1]
                        rstatus = int(xdb.dbresults[0][2])


                        if (self.action == "start"):
                             react.start(acct1, acct2, self.memofrom, rstatus)
                        elif (self.action == "cancel"):
                            react.cancel()
                        elif (self.action == "accept"):
                            if rstatus == 3:
                                react.accept(acct1, self.memofrom)
                            else:
                                react.accept(acct2, self.memofrom)
                        elif (self.action == "barter"):
                            react.barter(acct1, acct2, self.memofrom, self.percentage, self.ratio, self.duration, self.memoid)
                        else:
                            react.ignore("Invalid action.")


                        if react.reaction == "refund":
                            sendto = self.memofrom
                        else:
                            sendto = xdb.sendto
                        if self.x_send(sendto, self.amt, react.returnmsg):
                            xdb.x_add_trans(self.trxid, self.memofrom, self.amt, self.memoid, react.reaction, self.txtime)
                    else:
                        xdb.x_add_trans(self.trxid, self.memofrom, self.amt, self.memoid, "Invalid Memo ID. Ignored", self.txtime)
                    


# Run as main

if __name__ == "__main__":

    a = AXtrans()
    a.x_fetch_history()

    #a.x_send()

# EOF

