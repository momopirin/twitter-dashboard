import mysql.connector
import os

def parsed_config_file(filename="config.ini"):
    secret_dict = {}

    with open(filename) as f:
        for index, line in enumerate(f):
            if index == 0 and line.rstrip('\n') != "[mysql]":
                raise Exception("Header error: except to read mysql config file only!")
            if index > 0:
                line = line.rstrip('\n')
                key, val = line.split('=')
                key = key.strip()
                val = val.strip()
                secret_dict[key] = val
            
    return secret_dict

class DBHelper:
    def __init__(self, db_config):
        self.conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
        )
        self.cur = self.conn.cursor(buffered=True)
        self.cur.execute("SET collation_connection = 'utf8mb4_general_ci';")

    def get_connection(self):
        return self.conn
        
    def confirm_connection(self):
        if self.conn.is_connected():
            print('Connection established.')
        else:
            print('Connection failed.')

    def write_one_record(self, stmt, args): # could be insert, delete, etc. All write operations.
        self.cur.execute(stmt, args)
        self.conn.commit()

    def write_multiple_records(self, stmt, args):
        self.cur.executemany(stmt, args)
        self.conn.commit()

    def read_records(self, stmt):
        self.cur.execute(stmt)
        if self.cur.rowcount > 0:
            return self.cur.fetchall()
        else:
            return

    def close_connection(self):
        self.cur.close()
        self.conn.close()
        print('Connection closed.')