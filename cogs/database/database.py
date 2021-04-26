import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import command as cmd
import database as db


def is_author():
        def predicate(ctx):
            guild = ctx.guild
            with open(f'Storage/{guild.name} - {guild.id}/database/authors.json', 'r') as file:
                authors = json.load(file)
            if len(authors) > 0:
                return ctx.message.author.id in authors
            else:
                return True
        return commands.check(predicate)


def in_channel():
        def predicate(ctx):
            guild = ctx.guild
            with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'r') as file:
                channels = json.load(file)
            return ctx.channel.id in channels
        return commands.check(predicate)

class Database(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @in_channel()
    @is_author()
    async def add_book(self, ctx, number, chapter, end=None):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        # For some reason the variable, chapter, is not evaluating in else section.
        # This is just a work around until root cause for this problem is found.
        _ = chapter
        print(_)
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)
        if end:
            book[str(number)] = {'start':int(chapter), 'end':int(end)}
        else:
            book[str(number)] = {'start':int(_), 'end':int(_)}

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)

        await ctx.send('New Book has been added!')


    @commands.command()
    @in_channel()
    @is_author()
    async def add_chapter(self, ctx, number, chapter):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book[str(number)]['end'] = int(chapter)

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)

        await ctx.send('New chapter has been added!')

    @commands.command()
    @in_channel()
    @is_author()
    async def upload(self, ctx, arg):

        """
        This command is to get the chapter from user.
        It takes chapter number as a argument.
        Chapter name follows the format of Chapter-{chapter_number}.txt.
        """

        msg = ctx.message
        attach = msg.attachments
        guild = ctx.guild

        if attach:
            for file in attach:
                path = os.getcwd() + \
                    f'/Storage/{guild.name} - {guild.id}/books/Chapter-{arg}.txt'
                await file.save(path)
                await ctx.send('Received the file.')
                print(f"Saved a new file of {file.size/1024} kb to the folder of {guild.name}")
        else:
            await ctx.send('No file included!')
            await ctx.send('Please try again!')


    @commands.command()
    @in_channel()
    @is_author()
    async def remove_book(self, ctx, number):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book.pop(str(number))

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)
        await ctx.send(f'Book {number} has been removed!')


    @commands.command()
    @in_channel()
    @is_author()
    async def remove_chapter(self, ctx, book_n):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book[str(book_n)]['end'] -= 1

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)
        await ctx.send('Chapter has been removed!')


    @commands.command()
    @in_channel()
    @is_author()
    async def allowEdit(self, ctx, chapter):
        guild = ctx.guild
        channel = ctx.message.channel_mentions[0]
        book = cmd.Book(chapter, guild)
        
        info = discord.Embed(color=0x815bc8, timestamp=datetime.now())
        info.add_field(name="Accepted Edits", value=0, inline=True)
        info.add_field(name="Rejected Edits", value=0, inline=True)
        info.add_field(name="Not Sure", value=0, inline=True)
        info.add_field(name="Total Edits", value=0, inline=False)
        info.set_author(name="Dodging Prision & Stealing Witches", url='https://dpasw.com')
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.set_footer(
            text=f'Book {book}, Chapter {chapter} | Provided By Hermione')

        msg = await channel.send(embed=info)
        await msg.pin()
        print(msg.id)
        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
            aEdit = json.load(file)
        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'r') as file:
            channels = json.load(file)

        aEdit[chapter] = [channel.id, msg.id]
        channels.append(channel.id)

        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'w') as file:
            json.dump(aEdit, file, indent=4)


        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'w') as file:
            json.dump(channels, file, indent=4)

        await ctx.send(f"Editing Request enabled for chapter {chapter}", delete_after=10)


    @commands.command()
    @in_channel()
    @is_author()
    async def disableEdit(self, ctx, chapter):
        guild = ctx.guild
        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
            aEdit = json.load(file)

        aEdit.pop(chapter, None)

        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'w') as file:
            json.dump(aEdit, file, indent=4)
        await ctx.send(f"Editing Request disabled for chapter {chapter}", delete_after=10)
        
    @commands.command()
    @in_channel()
    @is_author()
    async def stats(self, ctx, chapter):
        guild = ctx.guild

        accepted, rejected, notsure, total, book, editors = db.get_stats(guild, chapter)

        info = discord.Embed(color=0x815bc8, timestamp=datetime.now())
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(name="Dodging Prision & Stealing Witches", url='https://dpasw.com')
        info.set_footer(text=f'Book {book}, Chapter {chapter} | Provided By Hermione')

        await ctx.send(embed=info)


    @commands.command()
    @in_channel()
    @is_author()
    async def allstats(self, ctx):
        guild = ctx.guild

        accepted, rejected, notsure, total, book, editors = db.get_stats(guild)

        info = discord.Embed(color=0x815bc8, timestamp=datetime.now())
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(name="Dodging Prision & Stealing Witches", url='https://dpasw.com')
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.set_footer(text=f'Book - {book}| Provided By Hermione')

        await ctx.send(embed=info)

    @commands.command()
    @in_channel()
    @is_author()
    async def editors(self, ctx, chapter):
        guild = ctx.guild
        sql = "SELECT DISTINCT(Author) FROM edit WHERE chapter=(?)"
        editors = db.execute(guild, 'editorial', sql, chapter)
        print(editors)
        await ctx.send('Here is the list of editors who helped with chapter %s' % chapter, delete_after=100)
        await ctx.send(' '.join([element for tupl in editors for element in tupl]), delete_after=100)   # The code inside join is flattening the nested tuple

    
    @commands.command()
    @in_channel()
    @is_author()
    async def allEditors(self, ctx):
        guild = ctx.guild
        sql = "SELECT DISTINCT(Author) FROM edit"
        editors = db.execute(guild, 'editorial', sql)
        print(editors)
        await ctx.send('Here is the list of editors who helped with the editing', delete_after=100)
        # The code inside join is flattening the nested tuple
        await ctx.send(' '.join([element for tupl in editors for element in tupl]), delete_after=100)



    @commands.command()
    @in_channel()
    @is_author()
    async def addAuthor(self, ctx):
        guild = ctx.guild
        author = ctx.message.mentions[0]
        author_id = author.id
        author_name = author.name if author.nick == None else author.nick

        with open(f'Storage/{guild.name} - {guild.id}/database/authors.json', 'r') as file:
            authors = json.load(file)
            await ctx.send(f"Added {author_name} to the Author's list", delete_after=10)
        if author_id in authors:
            await ctx.send("Author is already in the list!", delete_after=10)
        else:
            authors.append(author_id)
        with open(f'Storage/{guild.name} - {guild.id}/database/authors.json', 'w') as file:
            authors = json.dump(authors, file)

    @commands.command()
    @in_channel()
    @is_author()
    async def delAuthor(self, ctx):
        guild = ctx.guild
        author = ctx.message.mentions[0]
        author_id = author.id
        author_name = ctx.author.name if ctx.author.nick == None else ctx.author.nick

        with open(f'Storage/{guild.name} - {guild.id}/database/authors.json', 'r') as file:
            authors = json.load(file)
        if author_id in authors:
            authors.remove(author_id)
            await ctx.send(f"Removed {author_name} from the Author's list", delete_after=10)

        else:
            await ctx.send("Author is not in the list!", delete_after=10)

        with open(f'Storage/{guild.name} - {guild.id}/database/authors.json', 'w') as file:
            authors = json.dump(authors, file)


    @commands.command()
    @in_channel()
    @is_author()
    async def setEmojis(self, ctx, accepted, rejected, not_sure):
        guild = ctx.guild

        emojis = [accepted, rejected, not_sure]
        eTypes = ['accepted', 'rejected', 'notsure']
        emojis_dict = dict(zip(eTypes, emojis))

        with open(f'Storage/{guild.name} - {guild.id}/database/emojis.json', 'w') as file:
            json.dump(emojis_dict, file)
        
        await ctx.send('Emoji list has been updeted!', delete_after=10)

    @commands.command()
    @is_author()
    async def addChannel(self, ctx):
        guild = ctx.guild
        channel = ctx.message.channel_mentions[0]
        channel_id = channel.id
        channel_name = ctx.channel.name

        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'r') as file:
            channels = json.load(file)

        if channel_id in channels:
            await ctx.send("Channel is already in the list!", delete_after=10)
        else:
            channels.append(channel_id)
            await ctx.send(f"Added {channel_name} to the Channels list", delete_after=10)

        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'w') as file:
            json.dump(channels, file)

    @commands.command()
    @is_author()
    async def delChannel(self, ctx):
        guild = ctx.guild
        channel = ctx.message.channel_mentions[0]
        channel_id = channel.id
        channel_name = ctx.channel.name

        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'r') as file:
            channels = json.load(file)

        if channel_id in channels:
            channels.remove(channel_id)
            await ctx.send(f"Removed {channel_name} from the channels list", delete_after=10)

        else:
            await ctx.send("Channel is not in the list!", delete_after=10)

        with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'w') as file:
            json.dump(channels, file)


    @commands.command()
    @in_channel()
    @is_author()
    async def checkEdits(self, ctx, number, chap=0):
        guild = ctx.guild
        channel = ctx.channel
        date = datetime.now() - timedelta(days=int(number))

        messages = await channel.history(after=date, oldest_first=False).flatten()

        sql = f"select * from edit Order by Message_ID desc limit {len(messages)}"
        result = db.execute(guild, 'editorial', sql)
        Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, Editorial_Channel, Accepted, Rejected, NotSure = [
            list(tup) for tup in zip(*result)]
        counter = 0

        for message in messages:
                msg = message.content

                if msg[:6] == '.edit ':
                    if str(message.id) not in Message_ID:
                        chapter, edits = msg[6:].split(maxsplit=1)
                        print(type(chapter), type(chap), chapter == str(chap))
                        if chapter == str(chap) or chap == 0:
                            context = await self.client.get_context(message)

                            await ctx.invoke(self.client.get_command('edit'), chapter=chapter, edit=edits, context=context)
                            Message_ID.append(message.id)
                            counter += 1
        await ctx.send(f"Total Messages Recovered :- {counter}", delete_after=100)


    @commands.command()
    @in_channel()
    @is_author()
    async def export(self, ctx, chapter):
        guild = ctx.guild
        conn = db.create_connection(guild, 'editorial')
        bio = BytesIO()

        script = f"SELECT * FROM edit WHERE chapter = {chapter}"
        df = pd.read_sql_query(script, conn)
        writer = pd.ExcelWriter(bio, engine="openpyxl")

        df.to_excel(writer, sheet_name=f"Edits - Chapter {chapter}")
        writer.save()
        bio.seek(0)
        # excel_file = bio.read()
        # print(excel_file.__sizeof__())
        await ctx.send(f"Here is all the edits in chapter {chapter}", file=discord.File(bio, f"Chapter-{chapter}.xlsx"))
        if conn:
            conn.close()

###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################

def setup(client):
    client.add_cog(Database(client))
