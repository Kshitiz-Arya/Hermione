import os
from motor.motor_asyncio import AsyncIOMotorClient

connection = AsyncIOMotorClient(os.environ.get('connect'))


async def insert(guild_id: str, database: str, update_statement: dict, connect: AsyncIOMotorClient = connection):
    """Insert a document into a database

    Args:
        guild_id (str): The guild id
        database (str): The database name
        update_statement (dict): The update statement to insert
        connect (optional): The connection to the database.
    """
    collection = connect[database][str(guild_id)]

    # Need to pass type of document with colunms
    await collection.insert_one(update_statement)


# todo Rename this function to get_document
async def get_document(guild_id: str, database: str, query: dict, return_column: list, connect=connection):
    """Get a single document from a database

    Args:
        guild_id (str): The guild id
        database (str): The database name
        query (dict): The query to find the document
        return_column (str): The column to return
        connect (optional): The connection to the database.

    Returns:
        dict: The document from the database
    """
    collections = connect[database][str(guild_id)]
    document = {column: 1 for column in return_column}

    return_doucment = await collections.find_one(query, document)
    return return_doucment


async def get_documents(guild_id, database: str, query: dict, return_column: list, limit: int = 0, connect=connection):
    """Get multiple documents from a database

    Args:
        guild (str): The guild id
        database (str): The database name
        query (dict): The query to find the documents
        return_column (list): The columns to return
        limit (int): The limit of documents to return
        connect (optional): The connection to the database.

    Returns:
        list: A list of documents
    """
    collections = connect[database][str(guild_id)]
    document = {column: 1 for column in return_column}

    return await collections.find(query, document, limit=limit).to_list(None)


async def get_stats(guild, database: str, chapter: int = None, connect=connection):
    """Get the stats for the database

    Args:
        guild (discord.Guild): The guild to get the stats for
        database (str): The database name
        chapter (int, optional): The chapter number to get the stats for. Defaults to None.
    """
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


async def update(guild_id, database, columns: list, values: list, match: dict, upsert: bool = False, connect=connection):
    """Update a document in a database

    Args:
        guild_id (str): The guild id
        database (str): The database name
        columns (list): The columns to update
        values (list): The new values for the columns
        match (dict): The match to find the document to update
        connect (optional): This represents the connection to the database.
    """
    collection = connect[database][str(guild_id)]
    update_str = [{"$set": dict(zip(columns, values))}]
    await collection.update_one(match, update_str, upsert=upsert)


async def delete_document(guild_id: str, database: str, match: dict, connect=connection):
    """Delete a document from a database

    Args:
        guild_id (str): The guild id
        database (str): The database name
        match (dict): The match query to find the document to delete
        connect (optional): The connection to the database.
    """
    collection = connect[database][str(guild_id)]
    await collection.delete_one(match)


async def get_voting_count(guild_id: str, database: str, connect=connection, **kwargs):
    """Get the count of voting for a message

    Args:
        guild_id (str): The guild id
        database (str): The database name
        message_id (int): The message id which is being voted
        connect (optional): The connection to the database.

    Returns:
        dict: A dictionary with the count of voting for the message
    """
    collection = connect[database][str(guild_id)]
    pipeline = [
        {
            '$project': {
                '_id': '$_id',
                'vote': {
                    '$objectToArray': '$votes'
                }
            }
        }, {
            '$unwind': '$vote'
        }, {
            '$group': {
                '_id': '$_id',
                'yes': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$vote.v', 2
                                ]
                            }, 1, 0
                        ]
                    }
                },
                'no': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$vote.v', 0
                                ]
                            }, 1, 0
                        ]
                    }
                },
                'not_sure': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$vote.v', 1
                                ]
                            }, 1, 0
                        ]
                    }
                }
            }
        }
    ]

    match = {'$match': kwargs}

    # if message_id is not none, instert match to pipeline at index 0
    if kwargs:
        pipeline.insert(0, match)
    voting_count = await collection.aggregate(pipeline=pipeline).to_list(None)
    return voting_count if voting_count else [{'yes': 0, 'no': 0, 'not_sure': 0}]
