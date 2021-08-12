import os
from motor.motor_asyncio import AsyncIOMotorClient

connect = AsyncIOMotorClient(os.environ.get('connect'))


# def create_connection(guild, db_file):
# create a database connection to a SQLite database #
#     conn = None
#     directory = os.getcwd()
#     db_file = f"{directory}/Storage/{guild.id}/database/{db_file}.db"
#     try:
#         conn = sqlite3.connect(db_file)
#         return conn

#     except Error as e:
#         raise e


# def create_table(database, table, guild):
#     try:
#         connection = create_connection(guild, database).cursor()
#         connection.execute(query(table))
#     except Error as e:
#         print(e)
#     finally:
#         if connection:
#             connection.close()


# def execute(guild, database, sql_query, values=None):
#     try:
#         connection = create_connection(guild, database)
#         cursor = connection.cursor()
#         if values is None:
#             commit = cursor.execute(sql_query)
#             connection.commit()
#             return commit.fetchall()

#         commit = cursor.execute(sql_query, values)
#         connection.commit()
#         return commit.fetchall()

#     except Error as e:
#         print(e)
#     finally:
#         if connection:
#             connection.close()


# def get_table(guild, database, table):
#     sql = "SELECT name FROM PRAGMA_TABLE_INFO('%s');" % table
#     table = execute(guild, database, sql)

#     return [element for tupl in table for element in tupl]
# table = execute(guild, database, query('get_table', table))
# if table:
#     column = list(map(lambda x: x[0], table.description))
#     return column


def query(query_name, table=None):  # Concider removing this function
    sql_query = {
        'edit':
        """
                                 CREATE TABLE IF NOT EXISTS edit
                                 (
                                   Message_ID TEXT,
                                   Author_ID  TEXT,
                                   Author     TEXT,
                                   Book       INT,
                                   Chapter    INT,
                                   Original   TEXT,
                                   Sugested   TEXT,
                                   Reason     TEXT,
                                   RankLine   TEXT,
                                   RankChar   TEXT,
                                   Org_channel TEXT,
                                   Accepted     Text,
                                   Rejected     Text,
                                   NotSure      Text
                                 )
                              """,
        'suggestion':
        """
                                    CREATE TABLE IF NOT EXISTS edit
                                    (
                                    Message_ID TEXT,
                                    Author_ID  TEXT,
                                    Author     TEXT,
                                    Sugested   TEXT,
                                    Org_channel TEXT,
                                    Accepted     Text,
                                    Rejected     Text,
                                    NotSure      Text
                                """,
        'history':
        """
                                 Create table if not exists history
                                 (
                                   Old_ID TEXT PRIMARY KEY,
                                   New_ID TEXT,
                                   Org_channel TEXT
                                 )""",
        'get_table':
        f"""
                              SELECT *
                              FROM {table}
                              """,
    }
    return sql_query[query_name]


async def insert(guild_id: str, database: str, update_statement: dict, connect: AsyncIOMotorClient = connect):
    collection = connect[database][str(guild_id)]

    # Need to pass type of document with colunms
    await collection.insert_one(update_statement)


# def insert(guild, database, table, column, values):
#     Connection = create_connection(guild, database)
#     sql = f''' INSERT INTO {table} {column}
#               VALUES({'?' + ',?'*(len(values)-1)}) '''
#     cur = Connection.cursor()
#     cur.execute(sql, values)
#     Connection.commit()
#     return cur.lastrowid

# todo Rename this function to get_document
async def getsql(guild, database, query, return_column, connect=connect):
    # This function just return one doucment
    # Just pass an empty dict as query for getting all the columns

    collections = connect[database][guild.id]
    document = {column: 1 for column in return_column}

    return await collections.find_one(query, document)


async def get_documents(guild, database, query: dict, return_column: list, limit=0, connect=connect):
    collections = connect[database][guild.id]
    document = {column: 1 for column in return_column}
    num_document = await collections.count_documents(query)

    return await collections.find(query, document, limit=limit).to_list(num_document)

# def getsql(guild, database, table, column, value):
#     Connection = create_connection(guild, database)
#     sql = f''' SELECT * FROM {table}
#                WHERE {column} = {value}'''
#     cur = Connection.cursor()
#     cur.execute(sql)
#     rows = cur.fetchall()
#     return rows


async def get_stats(guild, database: str, chapter: int = None, connect=connect):
    collections = connect[database][str(guild.id)]

    pipeline = [

        {
            "$group": {
                "_id": None,
                "distinct_editors": {"$addToSet": "$editor_id"},
                "distinct_book": {"$addToSet": "$book"},
                "count_message_id": {"$sum": 1},
                "count_accepted": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status",  "Accepted"]}, 1, 0]
                    }},
                "count_rejected": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status",  "Rejected"]}, 1, 0]
                    }},
                "count_not_sure": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status",  "Not Sure"]}, 1, 0]
                    }},
            }
        },
        {
            "$project": {
                "_id": 0,
                "count_message": "$count_message_id",
                "distinct_count_editors": {"$size": "$distinct_editors"},
                "distinct_count_book": {"$size": "$distinct_book"},
                "count_accepted": "$count_accepted",
                "count_rejected": "$count_rejected",
                "count_not_sure": "$count_not_sure"
            }

        }
    ]

    match = {"$match": {'chapter': chapter}}

# if chapter is not none, instert match to pipeline at index 0
    if chapter:
        pipeline.insert(0, match)

    result = await collections.aggregate(pipeline).to_list(None)
    return result[0].values()

# def get_stats(guild, chapter='all'):
#     Connection = create_connection(guild, 'editorial')
#     if chapter == 'all':

#         sql = """ SELECT COUNT(Accepted), COUNT(Rejected), COUNT(NotSure), COUNT(Message_ID), COUNT(DISTINCT(Book)), COUNT(DISTINCT(Author)) FROM edit"""
#     else:
#         sql = f""" SELECT COUNT(Accepted), COUNT(Rejected), COUNT(NotSure), COUNT(Message_ID), Book, COUNT(DISTINCT(Author)) FROM edit
#                     WHERE chapter = {chapter}"""
#     cur = Connection.cursor()
#     cur.execute(sql)
#     return cur.fetchone()


async def update(guild, database, columns: list, values: list, match: dict, connect=connect):
    collection = connect[database][guild.id]
    update_str = {"$set": dict(zip(columns, values))}
    await collection.update_one(match, update_str)

# def update(guild, database, table, U_column, U_value, R_column,
#            R_value):  # U_column = Update Column, R column = Reference Column
#     Connection = create_connection(guild, database)
#     sql = f''' UPDATE {table}
#                SET {U_column} = {U_value}
#                WHERE {R_column} = {R_value}'''
#     cur = Connection.cursor()
#     cur.execute(sql)
#     return Connection.commit()
