import discord
from discord.ext import commands
import os
import shutil
import json
import database as db
import command as cmd


###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################

intents = discord.Intents.default()
intents.reactions = True
permissions = discord.Permissions
permissions.add_reactions = True
permissions.read_messsage_history = True


def in_channel():
        def predicate(ctx):
            guild = ctx.guild
            with open(f'Storage/{guild.name} - {guild.id}/database/channels.json', 'r') as file:
                channels = json.load(file)
            return ctx.channel.id in channels
        return commands.check(predicate)

class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f'Joined {guild.name}')

        bot_adder = None
        guild_owner = guild.owner_id
        # print(type(guild.audit_logs(limit=1).next().action))
        async for log in guild.audit_logs(limit=100):

            # print(log.action=='AuditLogAction.bot_add')
            if log.action.name == 'bot_add':
                print(log)
                bot_adder = log.user.id
                break

        server_dir = f'{guild.name} - {guild.id}'
        dir = ['books', 'database']
        files = ['books', 'allowedEdits', 'emojis']
        count = 0
        for d in dir:
            print(count)
            os.makedirs(f'Storage/{server_dir}/{d}')
            count += 1
        
        for f in files:
            with open(f'Storage/{server_dir}/database/{f}.json', 'w') as file:
                base = {}
                json.dump(base, file)
        with open(f'Storage/{server_dir}/database/authors.json', 'w') as file:
            base = [bot_adder, guild_owner]
            json.dump(base, file)
        
        with open(f'Storage/{server_dir}/database/channels.json', 'w') as file:
            base = []
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


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
            This event will react to the original meassage once author react to editorial message

            This is picking up reaction from outside the intended channel and reaction from bot itself
            Rectify this as soon as possible
            """

        guild = payload.guild_id
        guild = self.client.get_guild(guild)
        channel = payload.channel_id
        # msg = db.get_table(guild, 'editorial', 'history')
        user = payload.user_id
        emoji = str(payload.emoji)
        New_ID = payload.message_id
        server_dir = f'{guild.name} - {guild.id}'


        with open(f'Storage/{server_dir}/database/authors.json', 'r') as file:
            authors = json.load(file)
        with open(f'Storage/{server_dir}/database/channels.json', 'r') as file:
            channels = json.load(file)
        with open(f'Storage/{server_dir}/database/emojis.json', 'r') as file:
            emojis = json.load(file)

        if channel in channels:
            if emoji in emojis.values():
                if user in authors:
                        # Look into making this a seperate function
                        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
                            allowedEdits = json.load(file)
                        row = db.getsql(guild, 'editorial', 'history', 'New_ID', New_ID)
                        Old_ID = int(row[0][0])
                        channel = int(row[0][2])
                        edit_status = list(emojis.keys())[list(emojis.values()).index(emoji)]
                        Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, Editorial_Channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', Old_ID)[0]
                        Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
                        Editorial_Channel = self.client.get_channel(Editorial_Channel)

                        db.update(guild, 'editorial', 'edit', edit_status, '1', 'Message_ID', Old_ID)
                        channel = self.client.get_channel(channel)
                        msg = await channel.fetch_message(Old_ID)
                        embed_msg = await Editorial_Channel.fetch_message(New_ID)

                        embed = discord.Embed(color=0x00ff00)
                        embed.add_field(name='Author', value=author, inline=False)
                        embed.add_field(name='Original Text', value=org, inline=False)
                        embed.add_field(name='Sugested Text', value=sug, inline=False)
                        embed.add_field(name='Reason', value=res, inline=False)
                        embed.add_field(name='Authors Vote', value=edit_status, inline=True)
                        
                        await embed_msg.edit(embed=embed)
                        await update_stats(chapter, guild, Editorial_Channel, msg_stats)
                        await msg.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
            This event will react to the original meassage once author react to editorial message

            This is picking up reaction from outside the intended channel and reaction from bot itself
            Rectify this as soon as possible
            """

        guild = payload.guild_id
        guild = self.client.get_guild(guild)
        user = payload.user_id
        channel = payload.channel_id
        member = self.client.user
        emoji = str(payload.emoji)
        New_ID = payload.message_id
        server_dir = f'{guild.name} - {guild.id}'



        with open(f'Storage/{server_dir}/database/authors.json', 'r') as file:
            authors = json.load(file)
        with open(f'Storage/{server_dir}/database/channels.json', 'r') as file:
            channels = json.load(file)
        with open(f'Storage/{server_dir}/database/emojis.json', 'r') as file:
            emojis = json.load(file)

        if channel in channels:
            if emoji in emojis.values():
                if user in authors:
                    # Look into making this a seperate function
                    with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
                            allowedEdits = json.load(file)
                            row = db.getsql(guild, 'editorial',
                                            'history', 'New_ID', New_ID)
                            Old_ID = int(row[0][0])
                            channel = int(row[0][2])
                            edit_status = list(emojis.keys())[
                                            list(emojis.values()).index(emoji)]
                            Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, Editorial_Channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', Old_ID)[0]

                            Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
                            Editorial_Channel = self.client.get_channel(Editorial_Channel)

                            db.update(guild, 'editorial', 'edit', edit_status, 'NULL', 'Message_ID', Old_ID)
                            channel = self.client.get_channel(channel)
                            msg = await channel.fetch_message(Old_ID)
                            embed_msg = await Editorial_Channel.fetch_message(New_ID)

                            embed = discord.Embed(color=0x00ff00)
                            embed.add_field(name='Author', value=author, inline=False)
                            embed.add_field(name='Original Text', value=org, inline=False)
                            embed.add_field(name='Sugested Text', value=sug, inline=False)
                            embed.add_field(name='Reason', value=res, inline=False)
                            embed.add_field(name='Authors Vote', value='Not Voted Yet', inline=True)
                            
                            await embed_msg.edit(embed=embed)

                            await update_stats(chapter, guild, Editorial_Channel, msg_stats)
                            await msg.remove_reaction(emoji, member)

    @commands.command()
    @in_channel()
    async def editcheck(self, ctx, chapter, *, edit):
        try:
            org, sug, res = edit.split('<<')    # splitting the edit request into definable parts
        except ValueError:
            org, sug = edit.split('<<')
            res = "Not Provided!"
        guild = ctx.guild
        print(org, sug, res)
        try:
            rankRow, rankChar = cmd.ranking(guild, chapter, org)
        except:
            rankRow, rankChar = None, None
        
        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
            allowedEdits = json.load(file)

        if chapter in allowedEdits.keys():
            if rankRow == None:
                await ctx.send('This was not found in the chapter. It is possible that this has already been edited or you have entered the wrong line.', delete_after=10)
            elif len(org) < 2 or len(sug) < 2:
                print(org, sug)
                await ctx.send('One or more columns are empty! Please submit requests with proper formatting.', delete_after=10)
            elif chapter in allowedEdits.keys():

                channel = ctx.channel.id
                mID = ctx.message.id
                aID = ctx.author.id
                author = ctx.author.name if ctx.author.nick == None else ctx.author.nick
                book = cmd.Book(chapter, guild)
                column = str(tuple(db.get_table(guild, 'editorial', 'edit'))).replace("'", '')

                Editorial_Channel, msg_stats = allowedEdits[chapter]
                Editorial_Channel = self.client.get_channel(Editorial_Channel)
                values = (mID, aID, author, book, chapter, org, sug, res, rankRow, rankChar, channel, None, None, None)  # Last three zeros are the Acceptence value, which is 0 by default
                # values = (mID, aID, author, book, chapter, org, sug, res, rankRow, channel)
                db.insert(guild, 'editorial', 'edit', column, values)

                # Sending the embed to distineted channel
                embed = discord.Embed(color=0x00ff00)
                embed.add_field(name='Author', value=author, inline=False)
                embed.add_field(name='Original Text', value=org, inline=False)
                embed.add_field(name='Sugested Text', value=sug, inline=False)
                embed.add_field(name='Reason', value=res, inline=False)
                embed.add_field(name='Authors Vote', value='Not Voted Yet', inline=True)
                msg_send = await Editorial_Channel.send(embed=embed)


                column = "('Old_ID', 'New_ID', 'Org_channel')"
                values = (mID, msg_send.id, channel)
                db.insert(guild, 'editorial', 'history', column, values)
                
                await update_stats(chapter, guild, Editorial_Channel, msg_stats)

                await ctx.send('Your edit has been accepted.', delete_after=10)
                await ctx.send(f'This chapter is from Book {book}, Chapter {chapter}, Line {rankRow} and position {rankChar}', delete_after=10)
        else:
            await ctx.send('Editing is currently disabled for this chapter.', delete_after=10)


    @commands.command()
    @in_channel()
    async def edit(self, ctx, chapter, *, edit):
        try:
            # splitting the edit request into definable parts
            org, sug, res = edit.split('<<')
        except ValueError:
            org, sug = edit.split('<<')
            res = "Not Provided!"
        guild = ctx.guild
        print(org, sug, res)
        try:
            rankRow, rankChar = cmd.ranking(guild, chapter, org)
        except:
            rankRow, rankChar = None, None

        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
            allowedEdits = json.load(file)

        with open(f'Storage/{guild.name} - {guild.id}/database/emojis.json', 'r') as file:
            emojis = json.load(file)

        if chapter in allowedEdits.keys():
            if len(org) < 2 or len(sug) < 2:
                print(org, sug)
                await ctx.send('One or more columns are empty! Please submit requests with proper formatting.', delete_after=10)
            elif chapter in allowedEdits.keys():

                channel = ctx.channel.id
                mID = ctx.message.id
                aID = ctx.author.id
                author = ctx.author.name if ctx.author.nick == None else ctx.author.nick
                book = cmd.Book(chapter, guild)
                column = str(tuple(db.get_table(guild, 'editorial', 'edit'))).replace("'", '')

                Editorial_Channel, msg_stats = allowedEdits[chapter]
                Editorial_Channel = self.client.get_channel(Editorial_Channel)
                # Last three zeros are the Acceptence value, which is 0 by default
                values = (mID, aID, author, book, chapter, org, sug,
                        res, rankRow, rankChar, channel, None, None, None)
                # values = (mID, aID, author, book, chapter, org, sug, res, rankRow, channel)
                db.insert(guild, 'editorial', 'edit', column, values)

                # Sending the embed to distineted channel
                embed = discord.Embed(color=0x00ff00)
                embed.add_field(name='Author', value=author, inline=False)
                embed.add_field(name='Original Text', value=org, inline=False)
                embed.add_field(name='Sugested Text', value=sug, inline=False)
                embed.add_field(name='Reason', value=res, inline=False)
                embed.add_field(name='Authors Vote',value='Not Voted Yet', inline=True)

                msg_send = await Editorial_Channel.send(embed=embed)

                column = "('Old_ID', 'New_ID', 'Org_channel')"
                values = (mID, msg_send.id, channel)
                db.insert(guild, 'editorial', 'history', column, values)

                await update_stats(chapter, guild, Editorial_Channel, msg_stats)

                for emoji in emojis.values():
                        await msg_send.add_reaction(emoji)


                await ctx.send('Your edit has been accepted.', delete_after=10)
                await ctx.send(f'This chapter is from Book {book}, Chapter {chapter}, Line {rankRow} and position {rankChar}', delete_after=10)
        else:
            await ctx.send('Editing is currently disabled for this chapter.', delete_after=10)




#     The Author will create the channel now and embed will send in the realtime
#     @commands.command()
#     async def get(self, ctx, chapter):
#         guild = ctx.guild
#         book   = cmd.Book(chapter, guild)

# ### This here for temperory purpuse ##
# ## This Block create a new category and channel if not already present and return channel data type
#         name = f'Edit: Book {book} - Chapter {chapter}'
#         guild = ctx.guild
#         categories = guild.categories
#         for category in categories:
#             if 'Editorial' in category.name:
#                 print('Category already present!')
#                 channel =  await guild.create_text_channel(name = name, category=category)
#                 flag = 0
#             else:
#                 flag = 1

#         if flag:
#             cat = await guild.create_category('Editorial')
#             channel =  await guild.create_text_channel(name = name, category=cat)


# #####

#         edits = db.getsql(guild, 'editorial', 'edit', 'chapter', chapter)  # Getting Rows from the Database
#         # history = db.getsql(guild, 'editorial', 'history', '1', '1')
#         # if history:
#         #     Old_IDs = [x[0] for x in history]
#         #     print(history[0])
#         #     print(history[0][0])
#         info = discord.Embed(color=0xff0000)
#         info.add_field(name="Book", value=book, inline=True)
#         info.add_field(name="Chapter", value=chapter, inline=True)
#         info.add_field(name="Total Edits", value=len(edits), inline=False)
#         await channel.send(embed=info)
#         print(edits)
#         # edits = (edits,)
#         for row in edits:
#             msg_ID = row[0]
#             Org_channel = row[9]
#             embed =  discord.Embed(color=0x00ff00)
#             embed.add_field(name='Author', value=row[2], inline=False)
#             embed.add_field(name='Original Text', value=row[5], inline=False)
#             embed.add_field(name='Sugested Text', value=row[6], inline=False)
#             embed.add_field(name='Reason', value=row[7], inline=False)

#             # string = f"**Author** : {row[2]}\n**Original** : {row[5]}\n**Sugested** : {row[6]}\n**Reason** : {row[7]}"
#             sent = await channel.send(embed = embed)
#             # column = str(tuple(db.get_table(guild, 'editorial', 'history'))).replace("'", '')
#             # values = (msg_ID, sent.id, Org_channel)
#             # db.insert(guild, 'editorial', 'history', column, values)

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


    
###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################

async def update_stats(chapter, guild, channel, msg_stats):

    accepted, rejected, notsure, total, book, editors = db.get_stats(guild, chapter)
    info = discord.Embed(color=0xff0000)
    info.add_field(name="Book", value=book, inline=True)
    info.add_field(name="Chapter", value=chapter, inline=True)
    info.add_field(name="Number of Editors", value=editors, inline=False)
    info.add_field(name="Accepted Edits", value=accepted, inline=True)
    info.add_field(name="Rejected Edits", value=rejected, inline=True)
    info.add_field(name="Not Sure", value=notsure, inline=True)
    info.add_field(name="Total Edits", value=total, inline=False)
    
    msg = await channel.fetch_message(msg_stats)
    await msg.edit(embed=info)


def setup(client):
    client.add_cog(Basic(client))
