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

intents = discord.Intents.default()
intents.reactions = True
permissions = discord.Permissions
permissions.add_reactions = True
permissions.read_messsage_history = True
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
        db.create_table('editorial', 'edit', guild)
        db.create_table('editorial','history', guild)

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
        channel = ctx.channel.id
        mID = ctx.message.id
        aID = ctx.author.id
        author = ctx.author.nick
        book   = cmd.Book(chapter, guild)
        column = str(tuple(db.get_table(guild, 'editorial', 'edit'))).replace("'", '')
        rank = cmd.ranking(guild, chapter, org)
        values = (mID, aID, author, book, chapter, org, sug, res, rank, channel)
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
        _ = db.getsql(guild, 'editorial', 'edit', 'chapter', chapter)
        print(_[0])


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



    @commands.command()
    async def get(self, ctx, chapter):
        guild = ctx.guild
        book   = cmd.Book(chapter, guild)

### This here for temperory purpuse ##
## This Block create a new category and channel if not already present and return channel data type
        name = f'Edit: Book {book} - Chapter {chapter}'
        guild = ctx.guild
        categories = guild.categories
        for category in categories:
            if 'Editorial' in category.name:
                print('Category already present!')
                channel =  await guild.create_text_channel(name = name, category=category)
                flag = 0
            else:
                flag = 1

        if flag:
            cat = await guild.create_category('Editorial')
            channel =  await guild.create_text_channel(name = name, category=cat)


#####

        edits = db.getsql(guild, 'editorial', 'edit', 'chapter', chapter)  # Getting Rows from the Database
        history = db.getsql(guild, 'editorial', 'history', '1', '1')
        if history:
            Old_IDs = [x[0] for x in history]
            print(history[0])
            print(history[0][0])
        info = discord.Embed(color=0xff0000)
        info.add_field(name="Book", value=book, inline=True)
        info.add_field(name="Chapter", value=chapter, inline=True)
        info.add_field(name="Total Edits", value=len(edits), inline=False)
        await channel.send(embed=info)
        for row in edits:
            msg_ID = row[0]
            Org_channel = row[9]
            embed =  discord.Embed(color=0x00ff00)
            embed.add_field(name='Author', value=row[2], inline=False)
            embed.add_field(name='Original Text', value=row[5], inline=False)
            embed.add_field(name='Sugested Text', value=row[6], inline=False)
            embed.add_field(name='Reason', value=row[7], inline=False)

            # string = f"**Author** : {row[2]}\n**Original** : {row[5]}\n**Sugested** : {row[6]}\n**Reason** : {row[7]}"
            sent = await channel.send(embed = embed)
            column = str(tuple(db.get_table(guild, 'editorial', 'history'))).replace("'", '')
            values = (msg_ID, sent.id, Org_channel)
            db.insert(guild, 'editorial', 'history', column, values)

    # def create(self, ctx, book, chapter):
    #     name = f'Edit: Book {book} - Chapter {chapter}'
    #     guild = ctx.guild
    #     categories = guild.categories
    #     for category in categories:
    #         if 'Editorial' in category.name:
    #             print('Category already present!')
    #             return await guild.create_text_channel(name = name, category=category)
    #             flag = 0
    #         else:
    #             flag = 1
    #
    #     if flag:
    #         cat = await guild.create_category('Editorial')
    #         return await guild.create_text_channel(name = name, category=cat)

    @commands.command()
    async def cat(self, ctx):
        embedVar = discord.Embed(title="Title", description="Desc", color=0x00ff00)
        embedVar.add_field(name="Field1", value="hi", inline=False)
        embedVar.add_field(name="Field2", value="hi2", inline=False)
        await ctx.send(embed=embedVar)


    @commands.Cog.listener()
    # This event will react to the original meassage once author react to editorial message

    # This is picking up reaction from outside the intended channel and reaction from bot itself
    # Rectify this as soon as possible
    async def on_raw_reaction_add(self, payload):
        guild = payload.guild_id
        guild = self.client.get_guild(guild)
        # msg = db.get_table(guild, 'editorial', 'history')
        member = payload.member
        emoji = str(payload.emoji)
        New_ID = payload.message_id

        if not member.id == self.client.user:
            # Look into making this a seperate function
            row = db.getsql(guild, 'editorial', 'history', 'New_ID', New_ID)
            print('row : ')
            print(row)
            Old_ID = int(row[0])
            channel = int(row[2])
            channel = self.client.get_channel(channel)
            msg = await channel.fetch_message(Old_ID)
            # message = await .fetch_message(Old_ID)
            await msg.add_reaction(emoji)
        else:
            pass
###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Basic(client))
