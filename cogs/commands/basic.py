import discord
from discord.ext import commands
import os
import shutil
from datetime import datetime

import database as db
from command import Book, ranking, read, save, in_channel, EditConverter, update_stats
import logging
import time


###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################

intents = discord.Intents.default()
intents.reactions = True
permissions = discord.Permissions
permissions.add_reactions = True
permissions.read_messsage_history = True

class Basic(commands.Cog):
    """
    This cog has contains the command for submiting edits and suggestions
    """

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined {guild.name}")

        guild_owner = guild.owner_id
        # print(type(guild.audit_logs(limit=1).next().action))
        def check(event):
            return event.target.id == self.client.user.id

        bot_entry = await guild.audit_logs(action=discord.AuditLogAction.bot_add).find(
            check
        )

        dir = ["books", "database", "images"]

        for d in dir:
            os.makedirs(f"Storage/{guild.id}/{d}")

        config = {
            "mods": {
                "colour": {
                    "accepted": 65280,
                    "rejected": 16711680,
                    "notsure": 16776960,
                    "noVote": 65535,
                },
                "allowedEdits": {},
                "emojis": {
                    "accepted": "\u2705",
                    "rejected": "\u274c",
                    "notsure": "\ud83d\ude10",
                },
                "authors": [bot_entry.user.id, guild_owner],
                "channels": [],
            },
            "prefix": ">",
            "books": {},
        }

        save(config, "config", guild)

        db.create_table("editorial", "edit", guild)
        db.create_table("editorial", "history", guild)

        bot = self.client.user
        bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0

        information_dm = discord.Embed(
            color=0x00FF00,
            description="Here is what you should do now!",
            timestamp=datetime.now(),
        )
        information_dm.set_author(
            name="Thank You for Inviting Hermione to your Library!", icon_url=bot_avatar
        )
        information_dm.set_footer(text="Provided to you by Hermione")
        information_dm.add_field(
            name="Step 1",
            value="Use .help Command to learn how to use other commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 2",
            value="Use .addChannel command to restict the bot to certain channels, where bot can interact with mods and users.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 3",
            value="Use .addAuthor command to add users to Author/Mod list. If users are not in the author list then they won't be able to use any mods commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 4",
            value="Use .setEmojis to set the emojis corresponding to Accepted, Rejected and Not Sure respectively",
            inline=False,
        )
        information_dm.add_field(
            name="Step 5",
            value="Use .changeColour to set colours for embeds to change to. This command need 4 colours in hex form for Accepted, Rejected, Not Sure and Not Voted Yet.",
        )
        information_dm.add_field(
            name="Step 6",
            value="Use .add_book command to store the information about which chapters are in which book. The general format is .add_book book-no start-chapter end-chapter",
            inline=False,
        )
        information_dm.add_field(
            name="Step 7",
            value="Use .allowEdits command to enable editing for certain chapters. The general format is .allowEdits #channel-name. (You need to mention the channel for this command to work)",
            inline=False,
        )

        await bot_entry.user.send(embed=information_dm)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"Left {guild.name}")
        os.chdir("Storage")
        shutil.rmtree(f"{guild.id}")
        os.chdir("..")

    @commands.Cog.listener()
    # @test
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

        config = read("config", guild)

        authors = config["mods"]["authors"]
        allowedEdits = config["mods"]["allowedEdits"]
        emojis = config["mods"]["emojis"]
        channels = [c[0] for c in list(allowedEdits.values())]

        channels = [c[0] for c in list(allowedEdits.values())]
        stats_msgs = [s[1] for s in list(allowedEdits.values())]

        if channel in channels:
            if emoji in emojis.values():
                if user_id in authors:
                    # Look into making this a seperate function
                    edit_status = list(emojis.keys())[
                        list(emojis.values()).index(emoji)
                    ]

                    row = db.getsql(guild, "editorial", "history", "New_ID", New_ID)
                    Old_ID = 0
                    if len(row) > 0:
                        Old_ID = int(row[0][0])
                        org_channel = int(row[0][2])

                        (
                            Message_ID,
                            author_ID,
                            author_name,
                            Book,
                            chapter,
                            org,
                            sug,
                            res,
                            RankCol,
                            RankChar,
                            Editorial_Channel,
                            Accepted,
                            Rejected,
                            NotSure,
                        ) = db.getsql(guild, "editorial", "edit", "Message_ID", Old_ID)[
                            0
                        ]

                    stats_msg = stats_msgs[channels.index(channel)]
                    Editorial_Channel = self.client.get_channel(channel)
                    chapter = list(allowedEdits.keys())[
                        list(allowedEdits.values()).index([channel, stats_msg])
                    ]
                    mainAuthor = await guild.fetch_member(user_id)
                    mainAuthor_name = mainAuthor.nick or mainAuthor.name
                    embed_msg = await Editorial_Channel.fetch_message(New_ID)

                    if bool(mainAuthor.avatar_url):
                        main_avatar = str(mainAuthor.avatar_url)

                    colour = read("config", guild)["mods"]["colour"]

                    updated_embed = embed_msg.embeds[0].to_dict()
                    updated_embed["color"] = int(colour[edit_status])
                    updated_embed["footer"][
                        "text"
                    ] = f"{mainAuthor_name} Voted - {edit_status.title()} {emoji}"
                    updated_embed["footer"]["icon_url"] = main_avatar
                    updated_embed = discord.Embed.from_dict(updated_embed)
                    await embed_msg.edit(embed=updated_embed)

                    db.update(
                        guild,
                        "editorial",
                        "edit",
                        edit_status,
                        "1",
                        "Message_ID",
                        Old_ID,
                    )

                    await update_stats(  # todo Making bot slow. Average Responce time :- 2.70 s
                        self.client.user, chapter, guild, Editorial_Channel, stats_msg
                    )

                    if len(row) > 0:
                        # Adding reaction to the original message if available

                        org_channel = self.client.get_channel(org_channel)
                        msg = await org_channel.fetch_message(Old_ID)
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

        config = read("config", guild)

        authors = config["mods"]["authors"]
        allowedEdits = config["mods"]["allowedEdits"]
        emojis = config["mods"]["emojis"]
        channels = [c[0] for c in list(allowedEdits.values())]

        stats_msgs = [c[1] for c in list(allowedEdits.values())]

        if channel in channels:
            if emoji in emojis.values():
                if user in authors:
                    # Look into making this a seperate function

                    edit_status = list(emojis.keys())[
                        list(emojis.values()).index(emoji)
                    ]

                    row = db.getsql(guild, "editorial", "history", "New_ID", New_ID)
                    Old_ID = 0
                    if len(row) > 0:
                        Old_ID = int(row[0][0])
                        org_channel = int(row[0][2])

                        (
                            Message_ID,
                            Author_ID,
                            author,
                            Book,
                            chapter,
                            org,
                            sug,
                            res,
                            RankCol,
                            RankChar,
                            Editorial_Channel,
                            Accepted,
                            Rejected,
                            NotSure,
                        ) = db.getsql(guild, "editorial", "edit", "Message_ID", Old_ID)[
                            0
                        ]  # Editorial_Channel should not be here, convert this to channel

                    stats_msg = stats_msgs[channels.index(channel)]
                    Editorial_Channel = self.client.get_channel(channel)
                    chapter = list(allowedEdits.keys())[
                        list(allowedEdits.values()).index([channel, stats_msg])
                    ]

                    embed_msg = await Editorial_Channel.fetch_message(New_ID)

                    # colour = {'accepted': 0x46e334, rejected: 0xff550d, 'notsure': 0x00ffa6}

                    colour = read("config", guild)["mods"]["colour"]

                    updated_embed = embed_msg.embeds[0].to_dict()
                    updated_embed["color"] = colour["noVote"]
                    updated_embed["footer"]["text"] = f"Author's Vote - Not Voted Yet"
                    updated_embed["footer"]["icon_url"] = None
                    updated_embed = discord.Embed.from_dict(updated_embed)

                    await embed_msg.edit(embed=updated_embed)

                    db.update(
                        guild,
                        "editorial",
                        "edit",
                        edit_status,
                        "NULL",
                        "Message_ID",
                        Old_ID,
                    )

                    await update_stats(
                        self.client.user, chapter, guild, Editorial_Channel, stats_msg
                    )

                    if len(row) > 0:
                        # Removing the reaction from original message

                        org_channel = self.client.get_channel(org_channel)
                        msg = await org_channel.fetch_message(Old_ID)
                        await msg.remove_reaction(emoji, member)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        channel = payload.channel_id
        data = payload.data
        guild_id = data["guild_id"]
        mID = data["id"]
        guild = self.client.get_guild(int(guild_id))
        colour = read("config", guild)["mods"]["colour"]

        try:
            bot = data["author"]["bot"]
        except:
            bot = 0

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, "editorial", sql)
        if not bot and len(results) != 0:
            newID = results[0][0]
            config = read("config", guild)
            allowedEdits = config["mods"]["allowedEdits"]
            prefix = config["prefix"]

            sql2 = f"select author from edit where Message_ID = {mID}"
            results = db.execute(guild, "editorial", sql2)
            if len(results) != 0:
                author = results[0][0]

            # Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', mID)[0]
            msg = data["content"]

            update_sql = f"""UPDATE edit
                            SET Original = ?, Sugested = ?, Reason = ?
                            WHERE Message_ID = {mID}
                            """

            if msg[:6] == f"{prefix}edit ":
                chapter, edits = msg[6:].split(maxsplit=1)

                Editorial_Channel, msg_stats = allowedEdits[chapter]
                Editorial_Channel = guild.get_channel(Editorial_Channel)
                msg = await Editorial_Channel.fetch_message(newID)

                updated_embed_dict = msg.embeds[0].to_dict()

                vote = updated_embed_dict["footer"]["text"]

                if "Not Voted Yet" not in vote:
                    return

                try:
                    # splitting the edit request into definable parts
                    org, sug, res = edits.split(">>")
                except ValueError:
                    try:
                        org, sug = edits.split(">>")
                        res = "Not Provided!"
                    except ValueError:
                        return None

                try:
                    rankRow, rankChar = ranking(guild, chapter, org)
                    change_status = f"**Proposed change was found in the chapter at line {rankRow}!**"

                except TypeError:
                    rankRow, rankChar = None, None
                    change_status = "**Proposed change was not found in the chapter!**"

                except FileNotFoundError:
                    rankRow, rankChar = None, None
                    change_status = "**Chapter has not yet been uploaded!**"

                updated_embed_dict["fields"][0]["value"] = org
                updated_embed_dict["fields"][1]["value"] = sug
                updated_embed_dict["fields"][2]["value"] = res
                updated_embed_dict["fields"][3]["value"] = change_status

                db.execute(
                    guild,
                    "editorial",
                    update_sql,
                    (
                        org,
                        sug,
                        res,
                    ),
                )

            elif msg[:9] == f"{prefix}suggest ":
                try:
                    chapter, suggestion = msg[8:].split(maxsplit=1)
                    if not chapter.isnumeric():
                        raise ValueError("Chapter should be a Integer")
                except ValueError:
                    return None  # TODO Bot should reply to the edited chapter with error text!

                Editorial_Channel, msg_stats = allowedEdits[chapter]
                Editorial_Channel = guild.get_channel(Editorial_Channel)
                msg = await Editorial_Channel.fetch_message(newID)

                updated_embed_dict = msg.embeds[0].to_dict()

                vote = updated_embed_dict["footer"]["text"]
                if "Not Voted Yet" not in vote:
                    return

                updated_embed_dict["fields"][0]["value"] = suggestion

                db.execute(guild, "editorial", update_sql, (None, suggestion, None))

            updated_embed_dict["color"] = colour["noVote"]
            updated_embed = discord.Embed.from_dict(updated_embed_dict)

            await msg.edit(embed=updated_embed)
            await update_stats(
                self.client.user, chapter, guild, Editorial_Channel, msg_stats
            )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        channel_id = payload.channel_id
        mID = payload.message_id
        guild_id = payload.guild_id
        guild = self.client.get_guild(int(guild_id))

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, "editorial", sql)
        if len(results) != 0:
            newID = results[0][0]

            sql2 = f"select chapter from edit where Message_ID = {mID}"
            results = db.execute(guild, "editorial", sql2)
            if len(results) != 0:
                chapter = results[0][0]
                server_dir = f"{guild.name} - {guild_id}"

                allowedEdits = read("config", guild)["mods"]["allowedEdits"]

            Editorial_Channel, msg_stats = allowedEdits[str(chapter)]
            Editorial_Channel = self.client.get_channel(int(Editorial_Channel))
            edit_msg = await Editorial_Channel.fetch_message(newID)

            embed_dict = edit_msg.embeds[0].to_dict()

            vote = embed_dict["footer"]["text"]
            if "Not Voted Yet" in vote:

                delete_sql = f"delete from edit where Message_ID = {mID}"
                delete_sql2 = f"delete from history where Old_ID = {mID}"

                await edit_msg.delete()
                db.execute(guild, "editorial", delete_sql)
                db.execute(guild, "editorial", delete_sql2)
                await update_stats(
                    self.client.user, chapter, guild, Editorial_Channel, msg_stats
                )
            else:
                update_sql = f"""UPDATE edit
                                SET Author_ID = 0, Author = "anonymous", Message_ID = 0
                                WHERE Message_ID = {mID}"""

                delete_sql1 = f"delete from history where Old_ID = {mID}"

                author = {
                    "name": "Anonymous",
                    "url": "",
                    "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png",
                }

                embed_dict["author"] = author

                updated_embed = discord.Embed.from_dict(embed_dict)
                await edit_msg.edit(embed=updated_embed)

                db.execute(guild, "editorial", update_sql)
                db.execute(guild, "editorial", delete_sql1)

    @commands.command()
    @in_channel()
    async def edit(self, ctx, chapter, *, edit: EditConverter, context=0):
        """
        Format :- .edit chapter Original Line>>Suggested Line>>Reason (Optional)
        """
        
        org, sug, res = edit

        if edit[0] is None:
            return
        guild = ctx.guild

        try:
            rank = ranking(guild, chapter, org)
            if isinstance(rank, FileNotFoundError):
                raise FileNotFoundError
            rankRow, rankChar = rank
            change_status = (
                f"**Proposed change was found in the chapter at line {rankRow}!**"
            )

        except FileNotFoundError:
            rankRow, rankChar = None, None
            change_status = "**Chapter is yet to be uploaded!**"

        except TypeError:
            rankRow, rankChar = None, None
            change_status = "**Proposed change was not found in the chapter!**"

        config = read("config", guild)
        allowedEdits = config["mods"]["allowedEdits"]
        emojis = config["mods"]["emojis"]

        if chapter in allowedEdits.keys():
            if len(org) < 2 or len(sug) < 2:
                await ctx.send(
                    "One or more columns are empty! Please submit requests with proper formatting.",
                    delete_after=10,
                )

            channel_id = ctx.channel.id
            if context == 0:
                mID = ctx.message.id
                aID = ctx.author.id
                author_name = (
                    ctx.author.name if ctx.author.nick == None else ctx.author.nick
                )
                avatar = str(ctx.author.avatar_url) if bool(ctx.author.avatar_url) else 0

            else:
                mID = context.message.id
                aID = context.author.id
                author_name = context.author.name
                avatar = str(context.author.avatar_url) if bool(context.author.avatar_url) else 0


            # if bool(self.client.user.avatar_url):
            #     bot_avatar = str(self.client.user.avatar_url)

            book = Book(chapter, guild)
            column = str(tuple(db.get_table(guild, "editorial", "edit"))).replace(
                "'", ""
            )

            Editorial_Channel, msg_stats = allowedEdits[chapter]
            Editorial_Channel = self.client.get_channel(Editorial_Channel)
            # Last three zeros are the Acceptence value, which is 0 by default
            values = (
                mID,
                aID,
                author_name,
                book,
                chapter,
                org,
                sug,
                res,
                rankRow,
                rankChar,
                channel_id,
                None,
                None,
                None,
            )
            # values = (mID, aID, author, book, chapter, org, sug, res, rankRow, channel)
            db.insert(guild, "editorial", "edit", column, values)

            # Sending the embed to distineted channel
            link = ctx.message.jump_url

            colour = read("config", guild)["mods"]["colour"]
            embed = discord.Embed(
                color=colour["noVote"],
                description=f"[Message Link]({link})",
                timestamp=datetime.now(),
            )
            embed.set_author(name=author_name, icon_url=avatar)
            embed.set_footer(text=f"Author's Vote - Not Voted Yet")
            embed.add_field(name="Original Text", value=org, inline=False)
            embed.add_field(name="Sugested Text", value=sug, inline=False)
            embed.add_field(name="Reason", value=res, inline=False)
            embed.add_field(name="⠀", value=change_status, inline=False)

            msg_send = await Editorial_Channel.send(embed=embed)

            column = "('Old_ID', 'New_ID', 'Org_channel')"
            values = (mID, msg_send.id, channel_id)
            db.insert(guild, "editorial", "history", column, values)

            await update_stats(
                self.client.user, chapter, guild, Editorial_Channel, msg_stats
            )

            for emoji in emojis.values():
                await msg_send.add_reaction(emoji)

            await ctx.send("Your edit has been accepted.", delete_after=10)
            await ctx.send(
                f"This chapter is from Book {book}, Chapter {chapter}, Line {rankRow} and position {rankChar}",
                delete_after=10,
            )
            return True
        else:
            await ctx.send(
                "Editing is currently disabled for this chapter.", delete_after=10
            )

    @in_channel()
    @commands.command()
    async def suggest(self, ctx, chapter, *, suggestion):

        """
        Format :- .suggest chapter Suggestion
        """

        guild = ctx.guild
        edit_channels = read("config", guild)["mods"]["allowedEdits"]

        if str(chapter) in edit_channels.keys():
            channel = ctx.channel
            author = ctx.author
            author_name = author.name if author.nick is None else author.nick

            msg = ctx.message
            link = msg.jump_url
            bot = self.client.user
            bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0
            if bool(author.avatar_url):
                avatar = str(author.avatar_url)

            Editorial_Channel, msg_stats = edit_channels[chapter]
            Editorial_Channel = self.client.get_channel(Editorial_Channel)

            emojis = read("config", guild)["mods"]["emojis"]

            column = str(tuple(db.get_table(guild, "editorial", "edit"))).replace(
                "'", ""
            )
            values = (
                msg.id,
                author.id,
                author_name,
                Book(chapter, guild),
                chapter,
                None,
                suggestion,
                None,
                None,
                None,
                channel.id,
                None,
                None,
                None,
            )
            db.insert(guild, "editorial", "edit", column, values)

            colour = read("config", guild)["mods"]["colour"]
            sug = discord.Embed(
                color=colour["noVote"],
                description=f"[Message Link]({link})",
                timestamp=datetime.now(),
            )
            sug.set_author(name=author_name, icon_url=avatar)
            sug.add_field(name="Suggestion", value=suggestion, inline=False)

            sug.set_footer(text="Author's Vote - Not Voted Yet | Provided by Hermione")

            msg_send = await Editorial_Channel.send(embed=sug)

            column = "('Old_ID', 'New_ID', 'Org_channel')"
            values = (msg.id, msg_send.id, channel.id)
            db.insert(guild, "editorial", "history", column, values)

            await update_stats(
                self.client.user, chapter, guild, Editorial_Channel, msg_stats
            )
            for emoji in emojis.values():
                await msg_send.add_reaction(emoji)

        else:
            await ctx.send(
                "Suggestions for this chapter has been turned off!", delete_after=30
            )

    @commands.command()
    @in_channel()
    async def invite(self, ctx):
        bot_invite = discord.Embed(
            colour=0x5C00AD,
            description=f"[Invite Link](https://discord.com/api/oauth2/authorize?client_id=649210648689115149&permissions=388288&scope=bot)",
            timestamp=datetime.now(),
        )
        bot_invite.set_author(
            name="Invite the bot to your server using this link!",
            icon_url=self.client.user.avatar_url,
        )
        await ctx.send(embed=bot_invite)

    @commands.command()
    async def dm(self, ctx):

        user = ctx.message.author
        bot = self.client.user
        bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0

        print(f"DMing! to {user.name}")
        information_dm = discord.Embed(
            color=0x00FF00,
            description="Here is what you should do now!",
            timestamp=datetime.now(),
        )
        information_dm.set_author(
            name="Thank You for Inviting Hermione to your Library!"
        )
        information_dm.set_footer(text="Provided to you by Hermione")
        information_dm.set_thumbnail(url=bot_avatar)
        information_dm.add_field(
            name="Step 1",
            value="Use .help Command to learn how to use other commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 2",
            value="Use .addChannel command to restict the bot to certain channels, where bot can interact with mods and users.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 3",
            value="Use .addAuthor command to add users to Author/Mod list. If users are not in the author list then they won't be able to use any mods commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 4",
            value="Use .setEmojis to set the emojis corresponding to Accepted, Rejected and Not Sure respectively",
            inline=False,
        )
        information_dm.add_field(
            name="Step 5",
            value="Use .changeColour to set colours for embeds to change to. This command need 4 colours in hex form for Accepted, Rejected, Not Sure and Not Voted Yet.",
        )
        information_dm.add_field(
            name="Step 6",
            value="Use .add_book command to store the information about which chapters are in which book. The general format is .add_book book-no start-chapter end-chapter",
            inline=False,
        )
        information_dm.add_field(
            name="Step 7",
            value="Use .allowEdits command to enable editing for certain chapters. The general format is .allowEdits #channel-name. (You need to mention the channel for this command to work)",
            inline=False,
        )
        information_dm.add_field(
            name="Step 8",
            value="You can use .setPrefix command to change the default prefix to access the bot.",
        )
        await user.send(embed=information_dm)


###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################





def setup(client):
    client.add_cog(Basic(client))
