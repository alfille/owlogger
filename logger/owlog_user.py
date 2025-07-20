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
import base64
import getpass

# for encryption
try:
    import bcrypt
except:
    print("bcrypt module needs to be installed")
    print("either 'pip install bcrypt' or 'apt install python3-bcrypt'")
    sys.exit(1)
    
    
class Database:
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

    def list_users( self ):
        results = self.command(
            """SELECT username FROM userlist ORDER BY username ;""", None, True 
            )
        return results

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
    
def list_users( db ):
    print( '\n'.join([ u[0] for u in db.list_users() ]) )

def read_toml( args ):
    if "config" in args:
        try:
            with open( args.config, "rb" ) as c:
                toml = tomllib.load(c)
        except tomllib.TOMLDecodeError as e:
            with open ( args.config, "rb" ) as c:
                contents = c.read()
            for lin in zip(range(1,200),contents.decode('utf-8').split("\n")):
                print(f"{lin[0]:3d}. {lin[1]}")
            print(f"Trouble reading configuration file {args.config}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
            toml={}
    return toml

def main(sysargs):
    
    # Look for a config file location (else default) 
    # read it in TOML format
    # allow command line parameters to over-rule
    
    # Step 1: Parse only the --config argument
    parser = argparse.ArgumentParser(
        add_help=False
        )
    
    config = "/etc/owlogger/owlogger.toml"
    # config
    parser.add_argument("--config",
        required=False,
        default=config,
        dest="config",
        type=str,
        nargs="?",
        help=f"Location of any configuration file. Optional default={config}"
        )
    args, remaining_argv = parser.parse_known_args()

    # Process TOML
    # TOML file
    toml = read_toml( args )

    # Second pass at command line
    parser = argparse.ArgumentParser(
        parents=[parser],
        add_help=False
        )
    
    # Database file
    dbfile = "./logger_data.db"
    parser.add_argument('-f','--file',
        required=False,
        default=toml.get("database",dbfile),
        dest="database",
        type=str,
        nargs='?',
        help=f'database file location (optional) default={dbfile}'
        )

    parser.add_argument("-l", "--list",
        required=False,
        default=False,
        dest="list",
        action="store_true",
        help=f"List users registered in database"
        )
    args, remaining_argv = parser.parse_known_args()

    db = Database(args.database)

    if args.list:
        list_users(db)
        return

    # third pass
    parser = argparse.ArgumentParser(
        parents=[parser],
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
        default=toml.get("remove",False),
        action="store_true",
        help="Remove user from this database"
        )
    
    args=parser.parse_args()
    
    if args.remove:
        remove_user( db, args.username )
    else:
        add_user(    db, args.username )
 
if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
