import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
import os


###############################################################################
#                         AREA FOR Functions                                  #
###############################################################################


# This function takes chapter number and return Book number
# from which the chapter belongs to.
def Book(chapter):
    # Opening File where Book information is kept.
    file = open('Chapter.txt', 'r')
    # Each line in file represents a Book
    for book, line in enumerate(file, 1):
        start, end = line.split(' ')

        if start <= chapter <= end:
            break

        if book >= 3:
            return 0    # return 0 if chapter was not found in any Book
    file.close()
    return book         # return Book number


def ranking(org, chapter):
    # This code Rank each sentence according to their position in text file.
    str = open('./chapter/Chapter-{}.txt'.format(chapter), 'r')
    print('File has been opened')
    #   This is the phrase which we have to search.
    if '\n' in org:  # This is driver code
        print('This string have multiple lines')
        org = org.splitlines()

        for count, i in enumerate(str, 1):
            if org[0] in i:
                byte = i.find(org[0])
                return f'{count}: {byte}'

    else:
        print('This string have single line')
        for count, i in enumerate(str, 1):
            if org in i:
                byte = i.find(org)
                return f'{count}: {byte}'


def create_connection(guild, db_file):
    # create a database connection to a SQLite database #
    conn = None
    dir = os.getcwd()
    print(f'Connected to {db_file}')
    db_file = f"{dir}/database/{guild.name} - {guild.id}/{db_file}.db"
    try:
        conn = sqlite3.connect(db_file)
        return conn

    except Error as e:
        print(e)


def create_table(database, guild):
    try:
        connection = create_connection(guild, database)
        connection = connection.cursor()
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
    Connection = create_connection(database)
    sql = f''' INSERT INTO {table}{column}
              VALUES({'?' + ',?'*(len(values)-1)}) '''
    cur = Connection.cursor()
    cur.execute(sql, values)
    Connection.commit()
    return cur.lastrowid


###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################


class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f'Joined {guild.name}')
        if 'database' in os.listdir():
            os.chdir('database')
            os.mkdir(f'{guild.name} - {guild.id}')
            os.chdir('..')
        else:
            os.makedirs(f'database/{guild.name} {guild.id}')
            os.chdir('..')

        create_table('editorial', guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f'Left {guild.name}')
        os.chdir('database')
        os.rmdir(f'{guild.name} - {guild.id}')
        os.chdir('..')

    @commands.command()
    async def ping(self, ctx):
        for i in range(5):
            await ctx.send(f'{round(self.client.latency * 1000)} ms')

    @commands.command()
    async def edit(self, ctx, chapter, *, edit):
        await ctx.send('Your edit has been accepted.')
        await ctx.send(f'This chapter is from Book {Book(chapter)}')

        org, sug, res = edit.split('<<')    # splitting the edit request into definable parts

        guild = ctx.guild
        mID = ctx.message.id
        aID = ctx.author.id
        author = ctx.author.nick
        column = str(tuple(get_table(guild, 'editorial', 'edit'))).replace("'", '')
        rank = ranking(org, chapter)
        values = (mID, aID, author, org, sug, res, rank)
        insert(guild, 'editorial', 'edit', column, values)

    @commands.command()
    async def test(self, ctx, msg):
        await ctx.send('This is msg 1')


###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Basic(client))
