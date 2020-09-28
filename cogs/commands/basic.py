import discord
from discord.ext import commands
import os
import shutil
import json
import database as db
import commands as cmd


###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################


class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f'Joined {guild.name}')

        server_dir = f'{guild.name} - {guild.id}'
        dir = ['books', 'database']
        count = 0
        for d in dir:
            print(count)
            os.makedirs(f'Storage/{server_dir}/{d}')
            count += 1
        with open('books.json', 'w') as file:
            base = {}
            json.dump(base, file)
        db.create_table('editorial', guild)

        print(os.getcwd())


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f'Left {guild.name}')
        os.chdir('Storage')
        shutil.rmtree(f'{guild.name} - {guild.id}')
        os.chdir('..')


    @commands.command()
    async def ping(self, ctx):
        for i in range(5):
            await ctx.send(f'{round(self.client.latency * 1000)} ms')


    @commands.command()
    async def edit(self, ctx, chapter, *, edit):

        org, sug, res = edit.split('<<')    # splitting the edit request into definable parts

        guild = ctx.guild
        mID = ctx.message.id
        aID = ctx.author.id
        author = ctx.author.nick
        book   = cmd.Book(chapter, guild)
        column = str(tuple(db.get_table(guild, 'editorial', 'edit'))).replace("'", '')
        rank = cmd.ranking(guild, chapter, org)
        values = (mID, aID, author, book, chapter, org, sug, res, rank)
        db.insert(guild, 'editorial', 'edit', column, values)
        await ctx.send('Your edit has been accepted.')
        await ctx.send(f'This chapter is from Book {book}')


    @commands.command()
    async def test(self, ctx):
        await ctx.send('Bot is working!')
        await ctx.send(f'{os.getcwd()}')

        print(os.getcwd())


    @commands.command()
    async def print(self, ctx, chapter):
        guild = ctx.guild
        _ = db.getsql(guild, 'editorial', 'edit', chapter)
        print(_)


    @commands.command()

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
                path = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books/Chapter-{arg}.txt'
                await file.save(path)
                await ctx.send('Received the file.')
                print(f"Saved a new file of {file.size/1024} kb to the folder of {guild.name}")
        else:
            await ctx.send('No file included!')
            await ctx.send('Please try again!')


###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Basic(client))
