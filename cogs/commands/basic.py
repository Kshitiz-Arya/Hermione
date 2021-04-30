import discord
from discord.ext import commands
import os
import shutil
import json
from datetime import datetime
import database as db
import command as cmd
import logging

logger = logging.getLogger('discord')
logger.setLevel(10)
handler = logging.FileHandler(filename='discord-basic.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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
        user_id = payload.user_id
        emoji = str(payload.emoji)
        New_ID = payload.message_id
        server_dir = f'{guild.name} - {guild.id}'


        with open(f'Storage/{server_dir}/database/authors.json', 'r') as file:
            authors = json.load(file)
        with open(f'Storage/{guild.name} - {guild.id}/database/allowedEdits.json', 'r') as file:
            allowedEdits = json.load(file)
        with open(f'Storage/{server_dir}/database/emojis.json', 'r') as file:
            emojis = json.load(file)

        channels = [c[0] for c in list(allowedEdits.values())]

        if channel in channels:
            if emoji in emojis.values():
                if user_id in authors:
                        # Look into making this a seperate function
                        
                        row = db.getsql(guild, 'editorial', 'history', 'New_ID', New_ID)
                        Old_ID = int(row[0][0])
                        channel = int(row[0][2])
                        edit_status = list(emojis.keys())[list(emojis.values()).index(emoji)]
                        Message_ID, author_ID, author_name, Book, chapter, org, sug, res, RankCol, RankChar, Editorial_Channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', Old_ID)[0]
                        Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
                        Editorial_Channel = self.client.get_channel(Editorial_Channel)
                        author = await self.client.fetch_user(author_ID)


                        db.update(guild, 'editorial', 'edit', edit_status, '1', 'Message_ID', Old_ID)
                        channel = self.client.get_channel(channel)
                        msg = await channel.fetch_message(Old_ID)
                        embed_msg = await Editorial_Channel.fetch_message(New_ID)
                        link = msg.jump_url
                        if bool(author.avatar_url):
                            avatar = str(author.avatar_url)
                        colour = {'accepted': 0x46e334,
                                  'rejected': 0xff550d, 'notsure': 0x00ffa6}


                        updated_embed = embed_msg.embeds[0].to_dict()
                        updated_embed['color'] = int(colour[edit_status])
                        updated_embed['footer']['text'] = f"Author's Vote - {edit_status.title()} {emoji}"
                        updated_embed = discord.Embed.from_dict(updated_embed)
                        # embed = discord.Embed(color=colour[edit_status], description=f"[Message Link]({link})", timestamp=datetime.now())
                        # embed.set_author(name=author_name, icon_url=avatar)
                        # embed.set_footer(text=f"Author's Vote - {edit_status.title() + ' ' + emoji}")
                        # embed.add_field(name='Original Text', value=org, inline=False)
                        # embed.add_field(name='Sugested Text', value=sug, inline=False)
                        # embed.add_field(name='Reason', value=res, inline=False)
                        # embed.add_field(name='Authors Vote', value=edit_status + " " + emoji, inline=True)
                        
                        await embed_msg.edit(embed=updated_embed)
                        await update_stats(self.client.user, chapter, guild, Editorial_Channel, msg_stats)
                        await msg.add_reaction(emoji)
                        print(updated_embed.to_dict())

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
        with open(f'Storage/{server_dir}/database/allowedEdits.json', 'r') as file:
            allowedEdits = json.load(file)
        with open(f'Storage/{server_dir}/database/emojis.json', 'r') as file:
            emojis = json.load(file)
        
        channels = [c[0] for c in list(allowedEdits.values())]

        if channel in channels:
            if emoji in emojis.values():
                if user in authors:
                    # Look into making this a seperate function
                    
                    row = db.getsql(guild, 'editorial',
                                    'history', 'New_ID', New_ID)
                    Old_ID = int(row[0][0])
                    channel = int(row[0][2])
                    edit_status = list(emojis.keys())[
                                    list(emojis.values()).index(emoji)]
                    Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, Editorial_Channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', Old_ID)[0] # Editorial_Channel should not be here, convert this to channel

                    Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
                    Editorial_Channel = self.client.get_channel(Editorial_Channel)

                    db.update(guild, 'editorial', 'edit', edit_status, 'NULL', 'Message_ID', Old_ID)
                    channel = self.client.get_channel(channel)
                    msg = await channel.fetch_message(Old_ID)
                    embed_msg = await Editorial_Channel.fetch_message(New_ID)


                    link = msg.jump_url

                    embed = discord.Embed(
                        color=0x8b60d1, description=f"[Message Link]({link})", timestamp=datetime.now())
                    embed.set_author(name=author)
                    embed.set_footer(text="Author's Vote - Not Voted Yet")
                    embed.add_field(name='Original Text', value=org, inline=False)
                    embed.add_field(name='Sugested Text', value=sug, inline=False)
                    embed.add_field(name='Reason', value=res, inline=False)
                    
                    await embed_msg.edit(embed=embed)

                    await update_stats(self.client.user,chapter, guild, Editorial_Channel, msg_stats)
                    await msg.remove_reaction(emoji, member)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        channel = payload.channel_id
        data = payload.data
        guild_id = data['guild_id']
        mID = data['id']
        guild = self.client.get_guild(int(guild_id))
        try:
            bot = data['author']['bot']
        except:
            bot = 0

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, 'editorial', sql)
        if not bot and len(results) != 0:
            newID = results[0][0]
            sql2 = f"select author from edit where Message_ID = {mID}"
            results = db.execute(guild, 'editorial', sql2)
            if len(results) != 0:
                author = results[0][0]

            # Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', mID)[0]
            msg = data['content']
            server_dir = f'{guild.name} - {guild_id}'
            with open(f'Storage/{server_dir}/database/allowedEdits.json', 'r') as file:
                allowedEdits = json.load(file)



            if msg[:6] == '.edit ':
                chapter, edits = msg[6:].split(maxsplit=1)
                try:
                    # splitting the edit request into definable parts
                    org, sug, res = edits.split('<<')
                except ValueError:
                    try:
                        org, sug = edits.split('<<')
                        res = "Not Provided!"
                    except ValueError:
                        return None

            update_sql = f"""UPDATE edit
                            SET Original = ?, Sugested = ?, Reason = ?
                            WHERE Message_ID = {mID}
                            """
            Editorial_Channel, msg_stats = allowedEdits[chapter]
            Editorial_Channel = guild.get_channel(Editorial_Channel)
            msg = await Editorial_Channel.fetch_message(newID)

            link = msg.jump_url

            embed = discord.Embed(color=0x00ff00, description=f"[Message Link]({link})", timestamp=datetime.now())
            embed.set_author(name=author)
            embed.set_footer(text="Author's Vote - Not Voted Yet")
            embed.add_field(name='Original Text', value=org, inline=False)
            embed.add_field(name='Sugested Text', value=sug, inline=False)
            embed.add_field(name='Reason', value=res, inline=False)

            await msg.edit(embed=embed)
            await update_stats(self.client.user, chapter, guild, Editorial_Channel, msg_stats)
            db.execute(guild, 'editorial', update_sql, (org, sug, res,))
        

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        channel_id = payload.channel_id
        mID = payload.message_id
        guild_id = payload.guild_id
        guild = self.client.get_guild(int(guild_id))

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, 'editorial', sql)
        if len(results) != 0:
            newID = results[0][0]


            sql2 = f"select chapter from edit where Message_ID = {mID}"
            results = db.execute(guild, 'editorial', sql2)
            if len(results) != 0:
                chapter = results[0][0]
                server_dir = f'{guild.name} - {guild_id}'
                with open(f'Storage/{server_dir}/database/allowedEdits.json', 'r') as file:
                    allowedEdits = json.load(file)
            
            Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
            delete_sql = f"delete from edit where Message_ID = {mID}"
            delete_sql2 = f"delete from history where Old_ID = {mID}"

            Editorial_Channel = self.client.get_channel(int(Editorial_Channel))
            edit_msg = await Editorial_Channel.fetch_message(newID)
            await edit_msg.delete()
            db.execute(guild, 'editorial', delete_sql)
            db.execute(guild, 'editorial', delete_sql2)
            await update_stats(self.client.user,chapter, guild, Editorial_Channel, msg_stats)


    @commands.command()
    @in_channel()
    async def edit(self, ctx, chapter, *, edit, context=0):
        try:
            # splitting the edit request into definable parts
            org, sug, res = edit.split('<<')
        except ValueError:
            try:
                org, sug = edit.split('<<')
                res = "Not Provided!"
            except ValueError:
                await ctx.send("Your Edit is missing few thing. Please check and try again", delete_after=10)
                return None
        guild = ctx.guild

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
                if context == 0:
                    mID = ctx.message.id
                    aID = ctx.author.id
                    author = ctx.author.name if ctx.author.nick == None else ctx.author.nick
                else:
                    mID = context.message.id
                    aID = context.author.id
                    author = context.author.name

                book = cmd.Book(chapter, guild)
                column = str(tuple(db.get_table(guild, 'editorial', 'edit'))).replace("'", '')

                Editorial_Channel, msg_stats = allowedEdits[chapter]
                Editorial_Channel = self.client.get_channel(Editorial_Channel)
                # Last three zeros are the Acceptence value, which is 0 by default
                values = (mID, aID, author, book, chapter, org, sug, res, rankRow, rankChar, channel, None, None, None)
                # values = (mID, aID, author, book, chapter, org, sug, res, rankRow, channel)
                db.insert(guild, 'editorial', 'edit', column, values)

                # Sending the embed to distineted channel
                link = ctx.message.jump_url

                embed = discord.Embed(color=0x8b60d1, description=f"[Message Link]({link})", timestamp=datetime.now())
                embed.set_author(name=author)
                embed.set_footer(text="Author's Vote - Not Voted Yet")
                embed.add_field(name='Original Text', value=org, inline=False)
                embed.add_field(name='Sugested Text', value=sug, inline=False)
                embed.add_field(name='Reason', value=res, inline=False)

                msg_send = await Editorial_Channel.send(embed=embed)

                column = "('Old_ID', 'New_ID', 'Org_channel')"
                values = (mID, msg_send.id, channel)
                db.insert(guild, 'editorial', 'history', column, values)

                await update_stats(self.client.user, chapter, guild, Editorial_Channel, msg_stats)

                for emoji in emojis.values():
                        await msg_send.add_reaction(emoji)


                await ctx.send('Your edit has been accepted.', delete_after=10)
                await ctx.send(f'This chapter is from Book {book}, Chapter {chapter}, Line {rankRow} and position {rankChar}', delete_after=10)
        else:
            await ctx.send('Editing is currently disabled for this chapter.', delete_after=10)


    @in_channel()
    @commands.command()
    async def suggest(self, ctx, chapter, *,suggestion):
        guild = ctx.guild
        channel = ctx.channel
        author = ctx.author
        author_name = author.name if author.nick is None else author.nick
        msg = ctx.message
        link = msg.jump_url
        bot = self.client.user
        bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0
        if bool(author.avatar_url):
            avatar = str(author.avatar_url)
        
        with open(f"Storage/{guild.name} - {guild.id}/database/emojis.json", 'r') as file:
            emojis = json.load(file)

        sug = discord.Embed(color=0x8b60d1, description=f"[Message Link]({link})", timestamp=datetime.now())
        sug.set_author(name=author_name, icon_url=avatar)
        sug.add_field(name='Suggestion', value=suggestion, inline=False)
        sug.set_footer(text="Author's Vote - Not Voted Yet | Provided by Hermione", icon_url=bot_avatar)

        msg_send = await ctx.send(embed=sug)    
        for emoji in emojis.values():
            await msg_send.add_reaction(emoji)


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

async def update_stats(bot, chapter, guild, channel, msg_stats):

    accepted, rejected, notsure, total, book, editors = db.get_stats(guild, chapter)
    info = discord.Embed(color=0x815bc8, timestamp=datetime.now())

    bot_avatar = (bot.avatar_url) if bool(bot.avatar_url) else 0

    info.add_field(name="Number of Editors", value=editors, inline=False)
    info.add_field(name="Accepted Edits", value=accepted, inline=True)
    info.add_field(name="Rejected Edits", value=rejected, inline=True)
    info.add_field(name="Not Sure", value=notsure, inline=True)
    info.add_field(name="Total Edits", value=total, inline=False)
    info.set_author(name="Dodging Prision & Stealing Witches")
    info.set_thumbnail(url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
    info.set_footer(text=f'Book {book}, Chapter {chapter} | Provided By Hermione', icon_url=bot_avatar)

    msg = await channel.fetch_message(msg_stats)
    await msg.edit(embed=info)


def setup(client):
    client.add_cog(Basic(client))
