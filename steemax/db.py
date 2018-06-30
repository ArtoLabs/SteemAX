#!/usr/bin/python3

import pymysql
import re
from screenlogger.screenlogger import Msg
from steemax import default

class DB():


    def __init__(self, dbuser, dbpass, dbname):
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.dbname = dbname
        self.msg = Msg(default.logfilename, 
                        default.logpath, 
                        default.msgmode)


    def open_db(self):
        ''' opens a database connection
        '''
        self.db = pymysql.connect("localhost",
                                    self.dbuser,
                                    self.dbpass,
                                    self.dbname)
        self.cursor = self.db.cursor()


    def get_results(self, sql, *args):
        ''' Gets the results of an SQL statement
        '''
        self.open_db()
        try:
            self.cursor.execute(pymysql.escape_string(sql), args)
            self.dbresults = self.cursor.fetchall()
        except Exception as e:
            self.msg.error_message(e)
            self.dbresults = False
            self.db.rollback()
            return False
        else:
            return len(self.dbresults)
        finally:
            self.db.close()


    def commit(self, sql, *args):
        ''' Commits the actions of an SQL 
        statement to the database
        '''
        self.open_db()
        try:
            self.cursor.execute(pymysql.escape_string(sql), args)
            self.db.commit()
        except Exception as e:
            self.msg.error_message(e)
            self.db.rollback()
            return False
        else:
            return True
        finally:
            self.db.close()


# EOF
