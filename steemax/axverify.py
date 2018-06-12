#!/usr/bin/python3

from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem


class AXverify:


    def __init__(self):

        self.msg = Msg()

        self.steem = SimpleSteem()

 

    def print_steemit_balances(self):

        self.steem.reward_pool_balances()

        bal_banner = ("\n------------------------------------------------" +
            "\n   Reward balance: " + str(self.steem.reward_balance) +
            "\n   Recent claims: " + str(self.steem.recent_claims) +
            "\n   Steem = $" + str(self.steem.base) +
            "\n------------------------------------------------\n")

        self.msg.message(bal_banner)



    def get_vote_value (self, acctname, voteweight=100, votepower=0, mode="quiet"):
        ''' Voteweight and votepower are entered as a percentage value (1 to 100)
        but the steem python library needs these values to be in the range of 150 to 10000.
        The value returned by 'voting_power' is set by the system at the time
        the account last voted. How long it's been since the last vote?
        Calculate true voting power since last vote in range of 150 to 10000.
        Convert to rshares and STEEEM.
        '''

        self.steem.check_balances(acctname)

        if votepower == 0:
            votepower = self.steem.votepower

        votevalue = self.steem.current_vote_value(self.steem.lastvotetime, 
                                                    self.steem.steempower, voteweight, votepower)

        if mode == "verbose":

            self.msg.message("\n__" + acctname + "__\n   Vote Power: " 
                            + str(self.steem.votepower) + "%\n   Steem Power: " 
                            + str(self.steem.steempower) + "\n   Vote Value at " + str(voteweight) 
                            + "%: $" + str(votevalue) + "\n")

        return self.steem.rshares



    def verify_post (self, account1, account2, mode):
        ''' Gets only the most recent post, gets the 
        timestamp and finds the age of the post in days.
        Is the post too old? Did account2 vote on the post already?
        '''

        permlink = self.steem.get_post_info(account1)

        if not permlink:

            self.msg.error_message("No post for " + account1)

            return False

        else:

            votes = self.steem.vote_history(account1, permlink)

            for v in votes:
                if v['voter'] == account2:
                    self.msg.message(account2 + " has aready voted on " + permlink)
                    return False

        return True



    def eligible_posts (self, account1, account2, mode):
        ''' Verify the posts of both accounts
        '''

        if not self.verify_post(account1, account2, mode):

            return False

        if not self.verify_post(account2, account1, mode):

            return False

        return True



    def eligible_votes (self, account1, account2, percentage, ratio, mode, flag):
        ''' If the flag is raised use the full voting 
        power to make the comparison rather
        than the current voting power. Full voting 
        power is used to make the ratio comparison
        at the time the invite is created and during 
        the barter process. Current voting power
        is used at the time of the actual exchange. 
        Verify that the upvote exchange will be equal.
        Determine how much (percentage) of account2's 
        upvote is needed to match account1.
        Calculate better ratio if there is one. If the 
        ratio cannot be acheived then 'exceeds' is true.
        Get the new vote value from account2 at the 
        adjusted percentage. Convert rshares to steem.
        If ratio was not acheived return false and suggest 
        a new ratio. Otherwise display approximate 
        upvote matches and return true.
        '''

        if flag == 1:
            vpow = 100
        else:
            vpow = 0

        # v1        Account 1 vote value
        v1 = self.get_vote_value(account1, percentage, vpow, mode)

        if not v1:
            return False

        # v2        Account 2 vote value at 100% weight
        v2 = self.get_vote_value(account2, 100, vpow, mode)

        if not v2:
            return False

        # v3        Percentage of Account2's vote needed to match Account1
        v3 = ((v1 / v2) * 100) / float(ratio)
        v3a = round(v3, 2)

        exceeds = False

        if v3a < 1:
            v3 = 1
            exceeds = True
        if v3a > 100:
            v3 = 100
            exceeds = True

        self.msg.message(account2 + " needs to vote " 
                        + str(v3a) + "% in order to meet " + account1)

        # v4        Account 2 vote value at percentage from v3
        v4 = self.get_vote_value(account2, v3, vpow, mode)


        # convert votes to steem value
        v1s = self.steem.rshares_to_steem(v1)
        v4s = self.steem.rshares_to_steem(v4)


        # Do the values entered cause the value of Account2's 
        # vote to be larger than 100% or smaller than 1% ?
        if exceeds:

            if v3 == 1:

                v5 = v4 - v1
                v5s = self.steem.rshares_to_steem(v5)
                self.msg.message(account2 + "'s vote of " + str(v4s) 
                                + " will be larger than " + account1 
                                + "'s vote by: " + str(v5s))

            if v3 == 100:

                v5 = v1 - v4
                v5s = self.steem.rshares_to_steem(v5)
                self.msg.message(account1 + "'s vote of " + str(v1s) 
                                + " will be larger than " + account2 
                                + "'s vote by: " + str(v5s))

            return False

        else:

            self.msg.message(account1 + " will upvote $" + str(v1s) 
                            + " and " + account2 + " will upvote $" + str(v4s))

            return True



# Run as main

if __name__ == "__main__":

    import sys

    a = AXverify()

    if len(sys.argv) < 4:
        print ("Please enter two account names and a percentage to find eligibility.")
    else:
        acct1 = str(sys.argv[1])
        acct2 = str(sys.argv[2])
        per = int(sys.argv[3])

        xe = a.eligible_votes(acct1, acct2, per, 1, "", "")
        print ("Match eligible: " + str(xe))


# EOF

