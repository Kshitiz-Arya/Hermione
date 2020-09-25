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


def create_table(database, guild):
    try:
        connection = create_connection(guild, database).cursor()
        connection.execute(query('edit'))
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
    column = list(map(lambda x: x[0], table.description))
    return column


def query(input, table=None, column=None):      # Concider removing this function
    query = {
                'edit':      """
                                 CREATE TABLE IF NOT EXISTS edit
                                 (
                                   Message_ID TEXT PRIMARY KEY,
                                   Author     TEXT,
                                   Author_ID  INT,
                                   Book       INT,
                                   Chapter    INT,
                                   Original   TEXT NOT NULL,
                                   Sugested   TEXT NOT NULL,
                                   Reason     TEXT,
                                   Rank       TEXT
                                 )
                              """,

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


def getsql(guild, database, table, column):
    Connection = create_connection(guild, database)
    sql = f''' SELECT * FROM {table}
               WHERE chapter = {column}'''
    cur = Connection.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return rows
