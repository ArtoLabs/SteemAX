#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime
from steem import Steem
from steembase import exceptions
from steemax import axmsg
from steemax import axdb
import sys
import re

nodes = ['https://steemd.pevo.science',
    'https://steemd.minnowsupportproject.org',
    'https://steemd.steemgigs.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com']

xdb = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
xmsg = axmsg.AXmsg()
s = Steem(nodes)

steemaxacct = "artturtle"


class Reaction():
    ''' The reaction class defines the behavior of steemax as it processes SBD transactions and their related
    memo messages.
    '''


    def start(self, acct1, acct2, memofrom, rstatus):
        ''' The start method grants the authority to the exchange from the inviter. Once an invite has been 
        created at the steemax website, the inviter must authorize sending the invite by using the memo id
        and the start command.
        '''  
        if acct1 == memofrom:
            if rstatus < 0:
                self.reaction = "started"
                xdb.update_status(0)
                self.returnmsg = ("Hello " + acct2 + ", " + acct1 + " has invited you to an auto-upvote exchange. To respond to this " +
                    "invite please visit [link]")
            else:
                self.ignore("The inviter has already authorized this exchange.")
        else:
            self.ignore("Invalid action. The " + acct1 + " has not yet authorized this exhange.")


    def accept(self, acct1, acct2, mf, rstatus):
        ''' The accept method is used to authorize a change whenever an invite or a barter is sent. When an invite is sent the 
        invitee can respond with the accept command to authorize the exchange. The invitee must first go to the steemax website
        and submit either their private posting key or (soon to come) steemconnect token. Similarly, a barter is authorized when the receiving
        party responds with the accept command in the memo
        '''
        if acct2 == mf and (int(rstatus) in range(0,2)):
            self.reaction = "accepted"
            xdb.update_status(1)
            self.returnmsg = acct2 + " has accepted the invite. The auto-upvote exchange will begin immediately."
        elif acct1 == mf and int(rstatus) == 1 or int(rstatus) == 3:
            self.reaction = "accepted"
            xdb.update_status(1)
            self.returnmsg = acct1 + " has accepted the invite. The auto-upvote exchange will begin immediately."
        else:
            if acct2 == mf:
                self.ignore("Please wait for " + acct1 + " to respond.")
            else:
                self.ignore("Please wait for " + acct2 + " to respond.")


    def barter(self, acct1, acct2, memoid, mf, rstatus, per, ratio, dur):
        ''' A barter command can be used any time after both parties have authorized the exchange and both posting keys (steemconnect tokens)
        are present.
        '''
        if acct1 == mf and int(rstatus) > 0:
            self.reaction = "acct1 bartering"
            status = 2
            self.returnmsg = (acct1 + " has offered to barter. They offer " + per + 
                "% of their upvote at a ratio of " + ratio + ":1 for " + dur + " days. " +
                "Send any amount along with the memo code '" + memoid + ":accept' to accept this offer. " +
                "To generate your own barter offer, please visit [link]")
        elif acct2 == mf and int(rstatus) > 0:
            self.reaction = "acct2 bartering"
            status = 3
            self.returnmsg = (acct2 + " has offered to barter. They suggest a percentage of " + per + 
                "% of your upvote at a ratio of " + ratio + "("+acct1+"):1("+acct2+") for " + dur + " days. " +
                "Send any amount along with the memo code '" + memoid + ":accept' to accept this offer. " + 
                "To generate your own barter offer, please visit [link]")
        else:
            status = False
            if acct2 == mf:
                self.ignore("Invalid barter. Please wait for " + acct1 + " to respond first.")
            elif acct1 == mf:
                self.ignore("Invalid barter. Please wait for " + acct2 + " to respond first.")
        if status:
            if xdb.update_invite(per, ratio, dur, memoid, status):
                xmsg.message("Invite for Memo ID " + memoid + " has been updated.")
            else:
                xmsg.error_message("Could not update Memo ID " + memoid)


    def cancel(self, canceller)
        ''' The cancel command can be given at any time by either party
        '''
        self.reaction = "cancelled"
        xdb.update_status(4)
        self.returnmsg = canceller + " has cancelled the exchange."


    def ignore(self, reason):
        ''' If a command or action is invalid a refund is sent with a reason.
        '''
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


    def parse_memo(self, memofrom=None, memo=None, amt=None, trxid=None, txtime=None):
        ''' Takes the memo message received from an inviter or invitee and separates it into
        it's various parts.
        '''
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


    def send(self, to="artopium", amt="0.001 SBD", msg="test"):
        ''' Actually sends the transaction to the steem blockchain
        '''
        r = amt.split(" ")
        try:
            s.commit.transfer(to, float(r[0]), r[1], msg, steemaxacct)
        except exceptions.RPCError as e:
            xmsg.error_message(exceptions.decodeRPCErrorMsg(e))
            return False
        except:
            e = sys.exc_info()[0]
            xmsg.error_message(e)
            return False
        else:
            xmsg.message("Transaction committed. Sent " + r[0] + " " + r[1] + " to " + to + " with the memo: " + msg)
            return True


    def fetch_history(self):
        ''' Grabs the transaction history to see what's been sent to steemax. using the methods above, the memo message
        is parsed, and according to the command contained in the message and the memo id the steemax account wither forwards
        the money sent and performs the directed action, or if an action is invalid refunds the money to the sender. Uses
        steempy cli wallet for authorization.
        Currently using @artturtle account for testing. 
        '''
        last_trans_time = xdb.get_most_recent_trans()
        react = Reaction()
        h = s.get_account_history(steemaxacct, -1, 100)
        for a in h:
            this_trans_time = datetime.strptime(a[1]['timestamp'], '%Y-%m-%dT%H:%M:%S')
            if a[1]['op'][0] == 'transfer' and this_trans_time > last_trans_time:
                self.parse_memo(a[1]['op'][1]['from'], a[1]['op'][1]['memo'], a[1]['op'][1]['amount'], a[1]['trid'], a[1]['timestamp'])
                if a[1]['op'][1]['to'] == steemaxacct and re.match(r'^\s*[0-9]{32}$', self.memoid):
                    if xdb.verify_memoid(self.memofrom, self.memoid):
                        acct1 = xdb.dbresults[0][0]
                        acct2 = xdb.dbresults[0][1]
                        rstatus = int(xdb.dbresults[0][2])
                        # Parse the commands and react accordingly
                        if (self.action == "start"):
                             react.start(acct1, acct2, self.memofrom, rstatus)
                        elif (self.action == "cancel"):
                            react.cancel()
                        elif (self.action == "accept"):
                            react.accept(acct1, acct2, self.memofrom, rstatus)
                        elif (self.action == "barter"):
                            react.barter(acct1, acct2, self.memoid, self.memofrom, rstatus, self.percentage, self.ratio, self.duration)
                        else:
                            react.ignore("Invalid action.")
                        # If the command was invalid send the money back
                        if react.reaction == "refund":
                            sendto = self.memofrom
                        else:
                            sendto = xdb.sendto
                        if self.send(sendto, self.amt, react.returnmsg):
                            xdb.add_trans(self.trxid, self.memofrom, self.amt, self.memoid, react.reaction, self.txtime)
                        else:
                            xmsg.error_message("Could not send transaction.")
                    else:
                        xdb.add_trans(self.trxid, self.memofrom, self.amt, self.memoid, "Invalid Memo ID. Ignored", self.txtime)
                    


# Run as main

if __name__ == "__main__":

    a = AXtrans()
    a.fetch_history()

    #a.send()

# EOF

