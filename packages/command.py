import json
import os
import discord
from discord.ext import commands
from datetime import datetime
import database as db

from discord.ext.commands.converter import MessageConverter, TextChannelConverter

# This function takes chapter number and return Book number
# from which the chapter belongs to.

class EditConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            # splitting the edit request into definable parts
            org, sug, res = argument.split(">>")
        except ValueError:
            try:
                org, sug = argument.split(">>")
                res = "Not Provided!"

            except ValueError:
                if not ctx.command.name == "checkEdits":
                    await ctx.send(
                        "Your Edit is missing few thing. Please check and try again",
                        delete_after=10,
                    )

                return (None, None, None)


        return (org, sug, res)
        



def Book(chapter, guild):
    # Opening File where Book information is kept.
    config = read('config', guild)
    books = config['books']

    for b in books:
        if books[b]['start'] <= int(chapter) <= books[b]['end']:
            return b
        
    return 0



def ranking(guild, chapter, org):
    # This code Rank each sentence according to their position in text file.
    try:
        str = open(f'./Storage/{guild.id}/books/Chapter-{chapter}.txt', 'r')
        #   This is the phrase which we have to search.
        if '\n' in org:  # This is driver code
            org = org.splitlines()

            for count, i in enumerate(str, 1):
                if org[0] in i:
                    byte = i.find(org[0])
                    return [count, byte]

        else:
            for count, i in enumerate(str, 1):
                if org in i:
                    byte = i.find(org)
                    return [count, byte]
    except FileNotFoundError as Error:
        return Error

def read(file, guild):
    with open(f'Storage/{guild.id}/database/{file}.json', "r") as f:
        return json.load(f)

def save(data, file, guild):
    with open(f'Storage/{guild.id}/database/{file}.json', "w") as f:
        json.dump(data, f, indent=4)


def get_prefix(guild):

    return read('config', guild)['prefix']

def in_channel():
        def predicate(ctx):
            guild = ctx.guild
            channels = read('config', guild)['mods']['channels']
            return ctx.channel.id in channels
        return commands.check(predicate)

def is_author():
        def predicate(ctx):
            guild = ctx.guild
            
            authors = read('config', guild)['mods']['authors']

            if len(authors) > 0:
                return ctx.message.author.id in authors
            else:
                return True
        return commands.check(predicate)

async def update_stats(bot, chapter, guild, channel:TextChannelConverter, msg_stats=None):

    accepted, rejected, notsure, total, book, editors = db.get_stats(guild, chapter)
    info = discord.Embed(color=0x815BC8, timestamp=datetime.now())

    bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0

    info.add_field(name="Number of Editors", value=editors, inline=False)
    info.add_field(name="Accepted Edits", value=accepted, inline=True)
    info.add_field(name="Rejected Edits", value=rejected, inline=True)
    info.add_field(name="Not Sure", value=notsure, inline=True)
    info.add_field(name="Total Edits", value=total, inline=False)
    info.set_author(name="Dodging Prision & Stealing Witches")
    info.set_thumbnail(url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
    info.set_footer(
        text=f"Book {book}, Chapter {chapter} | Provided By Hermione",
        icon_url=bot_avatar,
    )

    if not isinstance(msg_stats, int) or msg_stats is None:
        msg = await channel.send(embed=info)
        return msg
    elif isinstance(msg_stats, discord.Message):
        await msg_stats.edit(embed=info)
    msg_stats = channel.get_partial_message(msg_stats)
    await msg_stats.edit(embed=info)