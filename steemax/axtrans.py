#!/usr/bin/python3

import sys
import re
from dateutil.parser import parse
from datetime import datetime
from steemax import axdb
from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem



class MemoMsg():



    def __init__(self):
        self.db = axdb.AXdb("steemax", 
                            "SteemAX_pass23", 
                            "steemax")



    def invite_msg(self, acct1, acct2, memoid):
        self.reaction = "started"
        self.db.update_status(0, memoid)
        self.returnmsg = (("Hello {}, {} has invited you "
                            + " to an auto-upvote exchange. " 
                            + "To accept this invite "
                            + "please send any amount SBD to "
                            + "@steemax with the following in "
                            + "the memo:\n\n{}"
                            + ":accept\n\nTo barter and to "
                            + "see a list of all "
                            + "your invites please visit "
                            + "https://steemax.info/@{}"
                            ).format(acct2, acct1, memoid, acct2))



    def accepted_msg(self, acct, memoid):
        self.reaction = "accepted"
        self.db.update_status(1, memoid)
        self.returnmsg = ("{} has accepted the invite. ".format(acct)
                            + "The auto-upvote exchange will "
                            + "begin immediately.")



    def barter_msg(self, reaction, 
                        status, 
                        acct, 
                        per, 
                        ratio, 
                        dur, 
                        memoid):
        self.reaction = reaction
        self.db.update_invite(per, ratio, dur, memoid, status)
        self.returnmsg = (("{} has offered to barter. They offer " 
                            + "{}% of their upvote at a ratio of " 
                            + "{}:1 for {} days. " 
                            + "Send any amount along with the " 
                            + "memo code:\n\n{}:accept " 
                            + "To generate your own barter offer, "
                            + "please visit [link]").format(
                            acct, per, ratio, dur, memoid))



    def ignore(self, reason):
        self.reaction = "refund"
        self.returnmsg = reason



    def cancel(self, canceller, memoid):
        ''' The cancel command can be 
        given at any time by either party
        '''
        self.reaction = "cancelled"
        self.db.update_status(4, memoid)
        self.returnmsg = (canceller 
            + " has cancelled the exchange.")



class Reaction(MemoMsg):



    def start(self, acct1, acct2, memofrom, rstatus, memoid):
        ''' The start method grants the authority to the 
        exchange from the inviter. 
        ''' 
        if acct1 == memofrom:
            if rstatus < 1:
                self.invite_msg(acct1, acct2, memoid)
            else:
                self.ignore("{} has already".format(acct1)
                        + "authorized this exchange.")
        else:
            self.ignore("Invalid action. {} ".format(acct1)
                        + " has not yet authorized this "
                        + "exhange.")



    def accept(self, acct1, acct2, memofrom, rstatus, memoid):
        ''' The accept method is used to authorize 
        a change whenever an invite or a barter is 
        sent. 
        '''
        if (acct2 == memofrom   
                    and (int(rstatus) 
                    in range(0,2))):
            self.accepted_msg(acct2, memoid)
        elif (acct1 == memofrom 
                    and int(rstatus) == 1 
                    or int(rstatus) == 3):
            self.accepted_msg(acct1)
        else:
            self.ignore("Please wait for " 
                + memofrom + " to respond.")

        

    def barter(self, acct1, acct2, memoid, memofrom, 
                            rstatus, per, ratio, dur):
        ''' A barter command can be used any 
        time after both parties have authorized 
        the exchange.
        '''
        if (acct1 == memofrom 
                    and int(rstatus) > 0):
            self.barter_msg("acct1 bartering", 2, 
                            acct1, per, ratio, dur, memoid)
        elif acct2 == memofrom and int(rstatus) > 0:
            self.barter_msg("acct2 bartering", 3, 
                            acct2, per, ratio, dur, memoid)
        else:
            self.ignore("Invalid barter. Please wait for " 
                        + memofrom + " to respond first.")



class AXtrans:



    def __init__(self):
        self.msg = Msg()
        self.db = axdb.AXdb("steemax", 
                            "SteemAX_pass23", 
                            "steemax")
        self.steem = SimpleSteem()
        self.react = Reaction()



    def parse_memo(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Ew this is dirty and came from 
        # strangers! Must be sanitized!
        try:
            memo = self.memo.split(":")
        except:
            return False
        self.memoid = memo[0] or None
        if re.match(r'^[A-Za-z0-9\:]$', self.memoid):
            return False
        if len(memo) > 1:
            self.action = memo[1] or None
            return True
        elif len(memo) == 5:
            self.percentage = memo[2] or None
            self.ratio = memo[3] or None
            self.duration = memo[4] or None
            return True
        else:
            return False



    def send(self, to="artopium", 
                    amt="0.001 SBD", 
                    msg="test"):
        r = amt.split(" ")
        if self.steem.transfer_funds(to, float(r[0]), 
                                    r[1], msg):
            self.msg.message(("Transaction committed. Sent {} "
                            "{} to {} with the memo: "
                            "{}").format(r[0], r[1], to, msg))



    def act(self, acct1, acct2, rstatus, sendto):
        if not self.db.get_user_token(self.memofrom):
            self.react.ignore(
                ("{} is not a current member of "
                + " https://steemax.trade! Join now "
                + "using SteemConnect.").format(self.memoid))
        elif (self.action == "start"):
            self.react.start(acct1, 
                        acct2, 
                        self.memofrom, 
                        rstatus,
                        self.memoid)
        elif (self.action == "cancel"):
            self.react.cancel(self.memofrom, 
                        self.memoid)
        elif (self.action == "accept"):
            self.react.accept(acct1, 
                        acct2, 
                        self.memofrom, 
                        rstatus,
                        self.memoid)
        elif (self.action == "barter"):
            self.react.barter(acct1, 
                        acct2, 
                        self.memoid, 
                        self.memofrom, 
                        rstatus, 
                        self.percentage, 
                        self.ratio, 
                        self.duration)
        else:
            self.react.ignore("Invalid action.")
        if self.react.reaction == "refund":
            self.sendto = self.memofrom
        else:
            self.sendto = sendto



    def parse_history_record(self, record, lasttrans):
        if (record[1]['op'][0] == 'transfer'
                and datetime.strptime(
                    record[1]['timestamp'], 
                    '%Y-%m-%dT%H:%M:%S')  
                > lasttrans
                and re.match(r'^[0-9]{32}', 
                    record[1]['op'][1]['memo'])
                and record[1]['op'][1]['to'] 
                == self.steem.mainaccount):
            return True
        else:
            return False



    def fetch_history(self):
        ''' Grabs the transaction history to see 
        what's been sent to steemax. the memo message 
        is parsed for a valid command and performs the 
        directed action.
        '''
        rt = self.db.get_most_recent_trans()
        for a in self.steem.get_my_history():
            if self.parse_history_record(a, rt):
                if self.parse_memo(memofrom=a[1]['op'][1]['from'], 
                                memo=a[1]['op'][1]['memo'], 
                                amount=a[1]['op'][1]['amount'], 
                                trxid=a[1]['trx_id'], 
                                txtime=a[1]['timestamp']):
                    if self.db.verify_memoid(self.memofrom, self.memoid):
                        self.act(self.db.dbresults[0][0],
                                self.db.dbresults[0][1],
                                int(self.db.dbresults[0][2]),
                                self.db.sendto)
                    else:
                        self.react.ignore("Invalid Memo ID.")
                        self.sendto = self.memofrom
                else:
                    self.react.ignore("Invalid Memo.")
                    self.sendto = self.memofrom

                self.send(self.sendto, 
                                self.amount, 
                                self.react.returnmsg)
                self.db.add_trans(self.trxid, 
                                self.memofrom, 
                                self.amount, 
                                self.memoid, 
                                self.react.reaction, 
                                self.txtime)
                    
                    


# Run as main

if __name__ == "__main__":

    a = AXtrans()
    a.fetch_history()

    #a.send()

# EOF

