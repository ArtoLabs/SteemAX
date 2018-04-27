#!/usr/bin/python3

from cmd import Cmd
import steemax.axe
import steemax.axdb
import steemax.axverify
import re
import sys

def enter_account_name(a, mode):

    # Prompt user for their Steemit account name. 
    # 'a' indicates entering the account name for an invitee or inviter

    if a:
        msg = 'Your account name @'
    else:
        msg = 'Their account name @'
    while True:
        acct = input(msg)
        if not re.match( r'^[a-z0-9\-]+$', acct) or len(acct) == 0 or len(acct) > 32:
            print ("The account name you entered is blank or contains invalid characters.")
        else:
            if steemax.axverify.get_vote_value(acct, 100, 0, mode):
                break

    return acct


def enter_memo_id(acct):

    # Prompt user for the unique Memo ID that was generated during the creation of an invite

    while True:
        memoid = input('Memo ID: ')
        if not re.match( r'^[0-9]+$', memoid) or len(memoid) == 0 or len(memoid) > 32:
            print ("The Memo ID you entered is blank or contains invalid characters.")
        else:
            if steemax.axdb.x_verify_memoid(acct, memoid, ""):
                break

    return memoid


def enter_percentage(acct):

    # Prompt user for the percentage of their upvote they wish to exchange. 
    # This is always a percentage of the inviter's (Account1) upvote, not the invitee (Account2)

    while True:
        per = input("Percentage of " + acct + "'s upvote (1 to 100): ")
        if not re.match( r'^[0-9]+$', per) or len(per) == 0 or len(per) > 3 or int(per) < 1 or int(per) > 100:
            print ("Please only enter a number between 1 and 100.")
        else:
            break

    return per


def enter_ratio(acct1, acct2, per, flag):

    # Prompt user for the ratio between accounts for the exchanges. This ratios is expressed as a two digit decimal number
    # to two places in proportion to 1, i.e. XX.xx to 1. e.g. 0.01 to 1, 10.10 to 1, 1.25 to 1, etc.
    # This is always so that X is inviter's (Account1) upvote, to 1 which is the invitee's (Account2) upvote

    while True:
        ratio = input('Ratio between upvotes. Enter as X ('+acct1+') to 1 ('+acct2+'). X is: ')
        if not re.match( r'^[0-9\.]+$', ratio) or len(ratio) == 0 or len(ratio) > 5 or float(ratio) < 0.01 or float(ratio) > 99:
            print ("Please enter a one or two digit number to represent a ratio in the format x to 1 where x is your input. Enter a decimal to two places to represent a ratio less than one. e.g. 0.05 to 1")
        else:
            if steemax.axverify.x_eligible_votes(acct1, acct2, per, ratio, "", flag):
                break

    return ratio


def enter_duration():

    # Promt user to enter the duration of the auto exchange in the number of days

    while True:
        dur = input('Duration of exchange in days: ')
        if not re.match( r'[0-9]', dur) or len(dur) == 0 or len(dur) > 3:
            print ("Please only enter a number up to three digits.")
        else:
            break

    return dur


def enter_key(acct):

    # Prompt user for their private posting key as found in their steemit.com wallet

    while True:
        key = input('Your Private Posting Key: ')
        if not re.match( r'^[A-Za-z0-9]+$', key) or len(key) == 0 or len(key) > 64:
            print ("The private posting key you entered is blank or contains invalid characters.")
        else:
            if steemax.axverify.x_verify_key(acct, key, ""):
                break

    return key


# Command shell


def run(args=None):

    steemax.axdb.x_first_time_setup("")
    prompt = MyPrompt()
    prompt.prompt = '[steemax]# '
    prompt.cmdloop('\n   ** Welcome to SteemAX ** \n')


class MyPrompt(Cmd):


    def do_run(self, args):
        steemax.axe.x_run_exchanges("")


    # Start an auto-upvote exchange between two Steemit accounts 

    def do_invite(self, args):

        acct1 = enter_account_name(1, "verbose")
        acct2 = enter_account_name(0, "verbose")
        key = enter_key(acct1)
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 1)
        dur = enter_duration()

        memoid = steemax.axdb.x_add_invite (acct1, acct2, key, per, ratio, dur, "")

        if memoid:
            print ("An invite has been created. Here is your unique Memo ID for this exchange:\n\n   " + memoid + "\n")
        else:
            print ("An invite could not be created.")


     # Accept an invite to an exchange

    def do_accept(self, args):

        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        if not steemax.axdb.x_verify_invitee(acct, memoid, ""):
            return
        key = enter_key(acct)
        if steemax.axdb.x_accept_invite(acct, memoid, key, ""):
            print ("The exchange invite has been accepted and the auto-upvote exchanges will begin.")
        else:
            print ("Could not accept the invite.")


    # Barter on the percentage, ratio and duration of an exchange

    def do_barter(self, args):

        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        asin = steemax.axdb.x_verify_account(acct, memoid, "")
        if not asin:
            return
        if asin[0] == 1 and asin[1] == 0:
            acct1 = acct
            acct2 = asin[3]
        elif asin[0] == 0 and asin[1] == 1:
            acct1 = asin[2]
            acct2 = acct
        else:
            print(acct + " is neither inviter or invitee. I know, it's weird.")
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 1)
        dur = enter_duration()

        if not steemax.axdb.x_verify_memoid(acct, memoid, ""):
            print ("Memo ID does not match the account provided.")
        else:
            if steemax.axdb.x_update_invite(per, ratio, dur, memoid, ""):
                print ("Invite for Memo ID " + memoid + " has been updated.")
            else:
                print ("Could not update Memo ID " + memoid)


    # Cancel an invite to an exchange

    def do_cancel(self, args):

        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        if not steemax.axdb.x_verify_account(acct, memoid, ""):
            return
        if steemax.axdb.x_cancel(acct, memoid, ""):
            print ("The exchange has been canceled")
        else:
            print ("Could not cancel the exchange")


    # Find out if a certain percentage and ratio between two accounts will create an eligible exchange

    def do_eligible(self, args):

        acct1 = enter_account_name(1, "verbose")    
        acct2 = enter_account_name(0, "verbose")
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 0)


    # Find and verify a Steemit account and see if it has started an exchange

    def do_account(self, args):

        acct = enter_account_name(1, "verbose")
        steemax.axdb.x_verify_account(acct, "", "")


    def do_pool(self, args):

        steemax.axverify.x_get_steemit_balances("verbose")


    # Quit

    def do_quit(self, args):

        """Quits the program."""
        print ("Quitting.")
        raise SystemExit


# Run as main

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    run()

# EOF

