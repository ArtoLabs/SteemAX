#!/usr/bin/python3

from dateutil.parser import parse
from datetime import datetime
import pymysql
import random

dbuser = "steemax"
dbpass = "SteemAX_pass23"
dbname = "steemax"

def x_check_reward_fund_renewal(time):

    now = datetime.now()
    #t = datetime.strptime(time,'%Y-%m-%dT%H:%M:%S')
    delta = now - time
    td = delta.seconds
    if td > 120:
        return True
    else:
        return False


def x_save_reward_fund(rb, rc, base, mode):

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    sql = "UPDATE axglobal SET RewardBalance = '"+str(rb)+"', RecentClaims = '"+str(rc)+"', Base = '"+str(base)+"' WHERE ID = '1';"

    try:
        cursor.execute(sql)
        db.commit()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
        db.rollback()
        db.close()
        return False

    db.close()

    return True


def x_fetch_reward_fund(mode):

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    sql = "SELECT RewardBalance, RecentClaims, Base, Time FROM axglobal WHERE ID = '1';"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        if mode != "quiet":
            print ("Could not fetch reward fund.")

    db.close()

    return results[0]


def x_verify_memoid(acct, memoid, mode):

    # Verify that the Memo ID entered matches the account name entered
    # This is necessary so that each account can update the invite during the barter process

    acct1 = ""
    acct2 = ""

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    # Get both account names if the Memo ID exists

    sql = "SELECT Account1, Account2 FROM axlist WHERE MemoID = '" + memoid + "';"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for row in results:
            acct1 = row[0]
            acct2 = row[1]
    except:
        if mode != "quiet":
            print ("Could not find Memo ID.")

    db.close()

    # Does the account name match the Memo ID?

    if acct != acct1 and acct != acct2:
        if mode != "quiet":
            print ("Verify Memo ID: Account names do not match.")
        return False
    else:
        return True

def x_cancel (acct, memoid, mode):

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    # Either account can cancel

    sql = "DELETE FROM axlist WHERE (Account1 = '"+acct+"' OR (Account2 = '"+acct+"')) AND (MemoID = '"+memoid+"');"
    try:
        cursor.execute(sql)
        db.commit()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
        db.rollback()
        db.close()
        return False

    db.close()

    return True

def x_update_invite(percent, ratio, duration, memoid, mode):

    # This is used during the barter process. Both accounts can update the percentage,
    # ratio and duration of the exchange until an agreement is made. This pauses the exchange
    # and puts it into a status of "2" which indicates an agreement has not been made

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    # Update the percentage, ratio and duration based on the Memo ID which is verified using
    # the x_verify_memoid function above

    sql = "UPDATE axlist SET Percentage = '" + percent + "', Ratio = '" + ratio + "', Duration = '" + duration + "', Status = '2' WHERE MemoID = '" + memoid + "';"
    try:
        cursor.execute(sql)
        db.commit()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
        db.rollback()
        db.close()
        return False

    db.close()

    return True


def x_verify_account (acct, memoid, mode):

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    asinviter = 0
    asinvitee = 0
    inviter = ""
    invitee = ""

    # Check to see if this is the inviter (Account1)

    sql1 = "SELECT Account2 FROM axlist WHERE Account1 = '" + acct + "'"
    if memoid:
        sql1 = sql1 + " AND MemoID = '" + memoid + "';"
    else:
        sql1 = sql1 + ";"
    try:
        cursor.execute(sql1)
        results1 = cursor.fetchall()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))

    # If the account is an inviter show a report

    if results1:
        if mode != "quiet":
            print (acct + " is the inviter of " + str(len(results1)) + " exchange(s)")
        asinviter = len(results1)
        invitee = results1[0][0]

    # Check to see if this is the invitee (Account2)

    sql2 = "SELECT Account1 FROM axlist WHERE Account2 = '" + acct + "';"
    if memoid:
        sql2 = sql2 + " AND MemoID = '" + memoid + "';"
    else:
        sql2 = sql2 + ";"
    try:
        cursor.execute(sql2)
        results2 = cursor.fetchall()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))

    # If the account is an invitee show a report

    if results2:
        if mode != "quiet":
            print (acct + " is the invitee of " + str(len(results2)) + " exchange(s)")
        asinvitee = len(results2)
        inviter = results2[0][0]

    # Return false if there are no entries in the database

    if not asinviter and not asinvitee:
        if mode != "quiet":
            print (acct + " is not in the database. Please start an invite.")
        db.close()
        return False

    db.close()

    return [asinviter, asinvitee, inviter, invitee]


def x_verify_invitee (acct2, memoid, mode):

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()

    # Check that account is truly an invitee (Account2) and not inviter (Account1)

    sql = "SELECT * FROM axlist WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
    if not results:
        if mode != "quiet":
            print (acct2 + " is not an invitee.")
        db.close()
        return False

    db.close()

    return True


def x_accept_invite(acct2, memoid, key, mode):

    # The exchange is initiated when both accounts agree on the settings, and
    # Account2 (invitee) has submitted the Memo ID along with their private
    # posting key. If the invitee wishes to barter, this function is still invoked first
    # then x_update_invite which pauses the exchange and sets the exchange status to "2" (see above)

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()
    
    # Update the private posting key and set the Status to "1" which indicates
    # an agreement has been made and thus making the auto-upvote exchange active

    sql = "UPDATE axlist SET Key2 = '" + key + "', Status = '1' WHERE Account2 = '" + acct2 + "' AND (MemoID = '" + memoid + "');"
    try:
        cursor.execute(sql)
        db.commit()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
        db.rollback()
        db.close()
        return False

    db.close()

    return True


def x_add_invite (acct1, acct2, key1, percent, ratio, duration, mode):

    # Adds the initial invite to the database and provides the unique Memo ID

    memoid = generate_nonce()

    # Connect to database

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()
    
    # Check for duplicate accounts

    if acct1 == acct2:
        if mode != "quiet":
            print ("The same account name was entered for both accounts.")
        db.close()
        return False

    # Check for duplicate invites

    sql = "SELECT * FROM axlist WHERE (Account1 = '" + acct1 + "' OR (Account1 = '" + acct2 + "')) AND (Account2 = '" + acct1 + "' OR (Account2 = '" + acct2 + "'));"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        if mode != "quiet":
            print ("Error: unable to fetch data")

    if results:
        if mode != "quiet":
            print ("An exchange has already been made between these accounts.")
        db.close()
        return False

    # Add both account names, the inviter's private posting key, the percentage, ratio and 
    # the duration of the exchange. This sets the Status to "0" indicating that the invitation
    # has not been accepted nor has a barter process been started.

    sql = "INSERT INTO axlist (Account1, Account2, Key1, Percentage, Ratio, Duration, MemoID, Status) VALUES ('" + acct1 + "', '" + acct2 + "', '" + key1 + "', '" + percent + "', '" + ratio + "', '" + duration + "', '" + memoid + "', '0');"
    try:
        cursor.execute(sql)
        db.commit()
    except pymysql.InternalError as e:
        if mode != "quiet":
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
        db.rollback()
        db.close()
        return False

    db.close()

    # Returns the unique Memo ID

    return memoid


def get_axlist (mode):

    db = pymysql.connect("localhost",dbuser,dbpass,dbname)
    cursor = db.cursor()
    sql = """SELECT * FROM axlist WHERE 1;"""
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        if mode != "quiet":
            print ("Error: unable to fetch data")
    db.close()

    return results


def generate_nonce(length=32):

    # Generates the unique Memo ID

    return ''.join([str(random.randint(0, 9)) for i in range(length)])


# EOF
