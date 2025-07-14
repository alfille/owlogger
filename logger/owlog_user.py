#!/usr/bin/env python3
# owlog_user.py
#
# Add user / password to database
# table userlist
# username plain text
# password is a bcrypted hash
#
# by Paul H Alfille 2025
# MIT License

import sqlite3

import sys
import argparse
import bcrypt
import base64
import getpass
    
class database:
    # sqlite3 interface
    def __init__(self, database="./logger_data.db"):
        # Create database if needed
        self.database = database
        # log table
        self.command(
            """CREATE TABLE IF NOT EXISTS datalog (
                id INTEGER PRIMARY KEY, 
                date DATATIME DEFAULT CURRENT_TIMESTAMP, 
                value TEXT
            );""" )
        self.command(
            """CREATE INDEX IF NOT EXISTS idx_date ON datalog(date);"""
            )
        # version table (single record)
        self.command(
            """CREATE TABLE IF NOT EXISTS version (
                id INTEGER PRIMARY KEY CHECK (id = 1), 
                version INTEGER DEFAULT 0
            );""" )
        # user/password table
        self.command(
            """CREATE TABLE IF NOT EXISTS userlist (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            );""" )

    def get_version( self ):
        try:
            records = self.command( """SELECT version FROM version WHERE id = 1""", None, True )
        except:
            return 0
        if len(records)==0:
            return 0;
        return records[0][0]

    def set_version( self, v ):
        self.command( 
            """INSERT INTO version( id, version)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    version = excluded.version
                ;""", ( v, ), False )
        
    def set_password( self, username, password_hash ):
        self.command( 
            """INSERT INTO userlist( username, password_hash )
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash = excluded.password_hash
                ;""", ( username, password_hash ), False )

    def del_password( self, username):
        self.command(
            """DELETE FROM userlist WHERE username = ? ;""", (username,), False 
            )

    def get_password( self, username ):
        # get password if exists
        records = self.command( """SELECT password_hash FROM userlist WHERE username=?""", (username,), True )
        # returns single element list or empty list
        return records

    def command( self, cmd, value_tuple=None, fetch=False ):
        # Connect to database and handle command
        #print(cmd)
        #print(value_tuple)
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                if value_tuple:
                    cursor.execute( cmd, value_tuple )
                else:
                    cursor.execute( cmd )
            if fetch:
                records = cursor.fetchall()
            else:
                records = None
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Failed to open database <{self.database}>: {e}")
            raise e
        #print("SQL ",records)
        return records
        
def add_user( db, username ):
    try:
        password = getpass.getpass(f"Password for {username}: ")
    except Exception as error:
        print('ERROR: ', error)
    else:    
        db.set_password( 
            username, 
            bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') 
            )
        
def remove_user( db, username ):
    db.del_password( username )

def main(sysargs):
    
    dbfile = "./logger_data.db"
    # Command line first
    parser = argparse.ArgumentParser(
        prog="owlog_user",
        description="Add users and passwords to database for `owlogger` security",
        epilog="Repository: https://github.com/alfille/owlogger")

    # username
    parser.add_argument( "username",
        help="Username to add, update or remove"
        )

    # remove
    parser.add_argument( "-r", "--remove",
        required = False,
        dest="remove",
        default=False,
        action="store_true",
        help="Remove user from this database"
        )
    
    # Database file
    dbfile = "logger_data.db"
    parser.add_argument('-f','--file',
        required=False,
        default=dbfile,
        dest="dbfile",
        type=str,
        nargs='?',
        help=f'database file location (optional) default={dbfile}'
        )

    args=parser.parse_args()
    
    db = database(args.dbfile)

    if args.remove:
        remove_user( db, args.username )
    else:
        add_user(    db, args.username )

 
if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
