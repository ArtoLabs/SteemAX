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

        h = s.get_account_history(steemaxacct, -1, 100)
        for a in h:
            if a[1]['op'][0] == 'transfer':
                
                memofrom = a[1]['op'][1]['from']
                memo = a[1]['op'][1]['memo']
                amt = a[1]['op'][1]['amount']
                trxid = a[1]['trx_id']
                txtime = a[1]['timestamp']
                print (trxid + " " + txtime + " " + memofrom)
                # This is dirty! Must be sanitized!
                memo = memo.split(":")
                memoid = memo[0]
                if len(memo) > 1:
                    action = memo[1]
                else:
                    action = "accept"
                if len(memo) == 5:
                    percentage = memo[2]
                    ratio = memo[3]
                    duration = memo[4]
                else:
                    percentage = 0
                    ratio = 0
                    duration = 0


                if a[1]['op'][1]['to'] == steemaxacct and re.match(r'^\s*[0-9]{32}$', memoid):
                    if xdb.x_verify_memoid(memofrom, memoid):

                        acct1 = xdb.dbresults[0][0]
                        acct2 = xdb.dbresults[0][1]
                        rstatus = xdb.dbresults[0][2]

                        if (action == "cancel"):
                            reaction = "pass"
                            status = 4
                        # Invitee has not accepted or given posting key yet
                        
                        elif rstatus == 0:

                            if (action == "accept"):
                                if acct2 == memofrom:
                                    reaction = "pass"
                                    status = 1
                                else:
                                    self.x_refund("Please wait for the invitee to accept this invite.")
                            elif (action == "barter"):
                                if acct2 == memofrom:
                                    reaction = "pass"
                                    status = 3
                                else:
                                    self.x_refund("Please wait for the invitee to accept this invite.")
                            else:
                                self.x_refund("Invalid action")

                        elif rstatus == 1:
                            
                            if (action == "barter"):
                                reaction = "pass"
                                if acct2 == memofrom:
                                    status = 3
                                else:
                                    status = 2
                            else:
                                self.x_refund("Invalid action")

                        elif rstatus == 2:

                            if (action == "accept") or (action == "barter"):
                                if acct2 == memofrom:
                                    reaction = "pass"
                                else:
                                    self.x_refund("Please wait for the invitee to accept this invite.")
                            else:
                                self.x_refund("Please wait for the invitee to accept this invite.")

                        elif rstatus == 3:

                            if (action == "accept") or (action == "barter"):
                                if acct1 == memofrom:
                                    reaction = "pass"
                                else:
                                    self.x_refund("Please wait for the invitee to accept this invite.")
                            else:
                                self.x_refund("Please wait for the invitee to accept this invite.")

                        else:
                            self.x_refund("Please wait for the invitee to accept this invite.")

                        if xdb.x_check_trans_history(trxid):
                            if xdb.results[3] == memoid:
                                pass
                            else:
                                pass
                        else:
                            reaction = "ignore"
                            reason = ""
                    else:
                        self.x_refund("Memo ID " + memoid + " could not be found.")

                        print (amt + " from " + f + "   Memo: " + memoid)
                        print ("Status: " + xdb.dbresults[0][2])

                    #x_add_trans(self, trxid, f, amt, memoid, reaction, txtime)



    def x_refund(self, reason):
        print (reason)

# Run as main

if __name__ == "__main__":

    a = AXtrans()
    a.x_fetch_history()


# EOF

