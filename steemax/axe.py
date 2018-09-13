#!/usr/bin/python3

from steemax import axdb
from steemax import axverify
from steemax import default


class Axe:
    def __init__(self):
        self.db = axdb.AXdb(default.dbuser,
                            default.dbpass,
                            default.dbname)
        self.verify = axverify.AXverify()

    def exchange(self):
        """ This method actualizes the exchange between Steemians.
        ID          row[0]
        Inviter     row[1]
        Invitee     row[2]
        Percentage  row[3]
        Ratio       row[4]
        Duration    row[5]
        MemoID      row[6]
        Status      row[7]
        Timestamp   row[8]
        """
        axlist = self.db.get_axlist(run=True)
        for row in axlist:
            print("Comparing " + str(row[1]) + " vs. " + str(row[2]))
            if self.verify.eligible_posts(row[1], row[2]) is not False:
                print("Posts are eligible.")
                # In the method eligible_votes
                # the last argument is a flag set to "2" indicating
                # that even if the calculated vote weight for the invitee
                # exceeds more than 100%
                # or less than 1% to go ahead and
                # make the exchange anyway at 100% or 1%
                # IF the flag is set to 1 vote values are calculated
                # at 100% voting power, whereas if the flag is set
                # to 0 or 2 vote values are calculated at their
                # current voting power.
                if self.verify.eligible_votes(row[1],
                                              row[2],
                                              row[3],
                                              row[4],
                                              2) is not False:
                    print("Votes are eligible")
                    # Inviter votes invitee's post
                    self.verify.vote_on_it(row[1],
                                           row[2],
                                           self.verify.post_two,
                                           int(row[3]))
                    # Invitee votes inviter's post
                    self.verify.vote_on_it(row[2],
                                           row[1],
                                           self.verify.post_one,
                                           self.verify.vote_cut)
                    self.verify.get_vote_value(row[1], int(row[3]))
                    vv1 = self.verify.votevalue
                    self.verify.get_vote_value(row[2], self.verify.vote_cut)
                    vv2 = self.verify.votevalue
                    self.db.archive_exchange(row[6], row[1], row[2],
                                             vv1, vv2,
                                             self.verify.post_one,
                                             self.verify.post_two)

# EOF