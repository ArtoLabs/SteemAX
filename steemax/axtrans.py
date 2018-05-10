#!/usr/bin/python3

from steem import Steem
import re
import axmsg
import axdb

nodes = [
    'https://steemd.minnowsupportproject.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com',
    'https://steemd.steemgigs.org'
]

s = Steem(nodes)
xmsg = axmsg.AXmsg()
xdb = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
steemaxacct = "artturtle"


class Reaction():


    def accept(self, acct, memofrom):
        if acct == memofrom:
            self.reaction = "pass"
            self.status = 1
        else:
            self.ignore("Please wait for the invitee to respond.")


    def barter(self, acct1, acct2, mf, rstatus):
        if acct1 == mf and rstatus == 3:
            self.reaction = "pass"
            self.status = 2
        elif acct2 == mf and rstatus == 2:
            self.reaction = "pass"
            self.status = 3
        else:
            self.ignore("Invalid barter. Please wait for the other side to respond first.")


    def cancel(self):
        self.reaction = "pass"
        self.status = 4


    def ignore(self, reason):
        self.reaction = "refund"
        print (reason)



class AXtrans:
    ''' Class for automatically handling transactions made to steemax for authentication
    '''


    def x_fetch_history(self):
        ''' Grabs the transaction history to see what's been sent to steemax.
        Currently using artturtle account for testing. Replace with the account of choice


        Status = 0 = invitee has not yet responded
        Status = 1 = both parties have accepted, the exchanges take place
        Status = 2 = account 1 (inviter) has offered a barter
        Status = 3 = account 2 (invitee) has offered a barter
        Status = 4 = cancelled

        MemoID:Action:Percentage:Ratio:Duration

        Actions: accept, barter, cancel

        Reactions: refund, pass

        ''
        xdb.x_get_most_recent_trans()
        for w in xdb.dbresults:
            print(w)
        '''

        react = Reaction()

        h = s.get_account_history(steemaxacct, -1, 100)
        for a in h:
            if a[1]['op'][0] == 'transfer':
                
                memofrom = a[1]['op'][1]['from']
                memo = a[1]['op'][1]['memo']
                amt = a[1]['op'][1]['amount']
                trxid = a[1]['trx_id']
                txtime = a[1]['timestamp']

                # This is dirty! Must be sanitized!
                memo = memo.split(":")
                memoid = memo[0]
                if len(memo) > 1:
                    action = memo[1]

                if len(memo) == 5:
                    percentage = memo[2]
                    ratio = memo[3]
                    duration = memo[4]
                else:
                    percentage = 0
                    ratio = 0
                    duration = 0
                    action = ""


                if a[1]['op'][1]['to'] == steemaxacct and re.match(r'^\s*[0-9]{32}$', memoid):
                    if xdb.x_verify_memoid(memofrom, memoid):

                        acct1 = xdb.dbresults[0][0]
                        acct2 = xdb.dbresults[0][1]
                        rstatus = xdb.dbresults[0][2]

                        if (action == "cancel"):
                            react.cancel()
                        elif (action == "accept"):
                            if rstatus == 3:
                                react.accept(acct1, memofrom)
                            else:
                                react.accept(acct2, memofrom)
                        elif (action == "barter"):
                            react.barter(acct1, acct2, memofrom)
                        else:
                            react.ignore("Invalid action.")
                        
                    #x_add_trans(self, trxid, f, amt, memoid, reaction, txtime)




# Run as main

if __name__ == "__main__":

    a = AXtrans()
    a.x_fetch_history()


# EOF

