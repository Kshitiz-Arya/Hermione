import os
from motor.motor_asyncio import AsyncIOMotorClient

connection = AsyncIOMotorClient(os.environ.get('connect'))


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


async def insert(guild_id: str, database: str, update_statement: dict, connect: AsyncIOMotorClient = connection):
    collection = connect[database][str(guild_id)]

    # Need to pass type of document with colunms
    await collection.insert_one(update_statement)



# todo Rename this function to get_document
async def get_document(guild_id, database, query, return_column, connect=connection):
    # This function just return one doucment
    # Just pass an empty dict as query for getting all the columns
    # This always returns _id

    collections = connect[database][str(guild_id)]
    document = {column: 1 for column in return_column}

    return_doucment = await collections.find_one(query, document)
    return return_doucment


async def get_documents(guild, database, query: dict, return_column: list, limit=0, connect=connection):
    collections = connect[database][guild.id]
    document = {column: 1 for column in return_column}
    num_document = await collections.count_documents(query)

    return await collections.find(query, document, limit=limit).to_list(num_document)


async def get_stats(guild, database: str, chapter: int = None, connect=connection):
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

    match = {"$match": {'chapter': str(chapter)}}

    # if chapter is not none, instert match to pipeline at index 0
    if chapter:
        pipeline.insert(0, match)

    result = await collections.aggregate(pipeline).to_list(None)
    return result[0].values() if result else []


async def update(guild_id, database, columns: list, values: list, match: dict, connect=connection):
    collection = connect[database][str(guild_id)]
    update_str = {"$set": dict(zip(columns, values))}
    await collection.update_one(match, update_str)

async def delete_document(guild_id:str, database:str, match:dict, connect=connection):
    collection = connect[database][str(guild_id)]
    await collection.delete_one(match)