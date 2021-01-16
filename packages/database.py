import os
import sqlite3
from sqlite3 import Error

def create_connection(guild, db_file):
    # create a database connection to a SQLite database #
    conn = None
    dir = os.getcwd()
    print(f'Connected to {db_file}')
    db_file = f"{dir}/Storage/{guild.name} - {guild.id}/database/{db_file}.db"
    try:
        conn = sqlite3.connect(db_file)
        return conn

    except Error as e:
        print(e)


def create_table(database, table, guild):
    try:
        connection = create_connection(guild, database).cursor()
        connection.execute(query(table))
    except Error as e:
        print(e)
    finally:
        if connection:
            connection.close()


def execute(guild, database, query, values=None):
    try:
        connection = create_connection(guild, database)
        cursor = connection.cursor()
        if values is None:
            commit = cursor.execute(query)
            connection.commit()
            return commit
        else:
            commit = cursor.execute(query, values)
            connection.commit()
            return commit
    except Error as e:
        print(e)
    finally:
        if connection:
            connection.close()


def get_table(guild, database, table):
    table = execute(guild, database, query('get_table', table))
    if table:
        column = list(map(lambda x: x[0], table.description))
        return column


def query(input, table=None, column=None):      # Concider removing this function
    query = {
                'edit':      """
                                 CREATE TABLE IF NOT EXISTS edit
                                 (
                                   Message_ID TEXT PRIMARY KEY,
                                   Author_ID  TEXT,
                                   Author     INT,
                                   Book       INT,
                                   Chapter    INT,
                                   Original   TEXT NOT NULL,
                                   Sugested   TEXT NOT NULL,
                                   Reason     TEXT,
                                   Rank       TEXT,
                                   Org_channel TEXT
                                 )
                              """,

                'history':    """
                                 Create table if not exists history
                                 (
                                   Old_ID TEXT PRIMARY KEY,
                                   New_ID TEXT,
                                   Org_channel TEXT
                                 )""",

                'get_table':  f"""
                              SELECT *
                              FROM {table}
                              """

             }
    return query[input]


def insert(guild, database, table, column, values):
    Connection = create_connection(guild, database)
    sql = f''' INSERT INTO {table}{column}
              VALUES({'?' + ',?'*(len(values)-1)}) '''
    cur = Connection.cursor()
    cur.execute(sql, values)
    Connection.commit()
    return cur.lastrowid


def getsql(guild, database, table, column, value):
    Connection = create_connection(guild, database)
    sql = f''' SELECT * FROM {table}
               WHERE {column} = {value}'''
    cur = Connection.cursor()
    cur.execute(sql)
    rows = cur.fetchone()
    return rows

def update(guild, database, table, U_column, U_value, R_column, R_value): # U_column = Update Column, R column = Reference Column
    Connection = create_connection(guild, database)
    sql = f''' UPDATE {table}
               SET {U_column} = {U_value}
               WHERE {R_column} = {R_value}'''
    cur = Connection.cursor()
    cur.execute(sql, values)
    return Connection.commit()
