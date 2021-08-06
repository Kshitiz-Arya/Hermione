import discord
from discord.ext import commands
import os
import shutil
from cogs.mods.mods import draw
from packages.command import ranking, read, save, update_stats
import packages.database as db
from datetime import datetime
from random import random


class Events(commands.Cog):
    """
    This cog has contains the all the events
    """
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(f"Joined {guild.name}")

        guild_owner = guild.owner_id

        # print(type(guild.audit_logs(limit=1).next().action))
        def check(event):
            return event.target.id == self.client.user.id

        bot_entry = await guild.audit_logs(
            action=discord.AuditLogAction.bot_add).find(check)

        directory = ["books", "database", "images"]

        for d in directory:
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
        draw(guild, (65280, 16711680, 16776960, 65635))

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
            name="Thank You for Inviting Hermione to your Library!",
            icon_url=bot_avatar)
        information_dm.set_footer(text="Provided to you by Hermione")
        information_dm.add_field(
            name="Step 1",
            value="Use .help Command to learn how to use other commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 2",
            value=
            "Use .addChannel command to restict the bot to certain channels, where bot can interact with mods and users.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 3",
            value=
            "Use .addAuthor command to add users to Author/Mod list. If users are not in the author list then they won't be able to use any mods commands.",
            inline=False,
        )
        information_dm.add_field(
            name="Step 4",
            value=
            "Use .setEmojis to set the emojis corresponding to Accepted, Rejected and Not Sure respectively",
            inline=False,
        )
        information_dm.add_field(
            name="Step 5",
            value=
            "Use .changeColour to set colours for embeds to change to. This command need 4 colours in hex form for Accepted, Rejected, Not Sure and Not Voted Yet.",
        )
        information_dm.add_field(
            name="Step 6",
            value=
            "Use .add_book command to store the information about which chapters are in which book. The general format is .add_book book-no start-chapter end-chapter",
            inline=False,
        )
        information_dm.add_field(
            name="Step 7",
            value=
            "Use .allowEdits command to enable editing for certain chapters. The general format is .allowEdits #channel-name. (You need to mention the channel for this command to work)",
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

        if (
            channel in channels
            and emoji in emojis.values()
            and user_id in authors
        ):
            # Look into making this a seperate function
            edit_status = list(emojis.keys())[list(
                emojis.values()).index(emoji)]

            row = db.getsql(guild, "editorial", "history", "New_ID",
                            New_ID)

            if not row:
                return

            old_id = row[0][0]
            org_channel = int(row[0][2])

            stats_msg = stats_msgs[channels.index(channel)]
            Editorial_Channel = self.client.get_channel(channel)
            chapter = list(allowedEdits.keys())[list(allowedEdits.values()).index([channel, stats_msg])]
            mainAuthor = await guild.fetch_member(user_id)
            mainAuthor_name = mainAuthor.nick or mainAuthor.name
            embed_msg = await Editorial_Channel.fetch_message(New_ID)

            main_avatar = str(
                mainAuthor.avatar_url) or discord.embeds.EmptyEmbed

            colour = read("config", guild)["mods"]["colour"]

            updated_embed = embed_msg.embeds[0].to_dict()
            updated_embed["color"] = int(colour[edit_status])
            updated_embed["footer"][
                "text"] = f"{mainAuthor_name} Voted - {edit_status.title()} {emoji}"
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
                old_id,
            )

            await update_stats(  # todo Making bot slow. Average Response time :- 2.70 s
                self.client.user, chapter, guild, Editorial_Channel,
                stats_msg)

            if old_id.isnumeric():
                # Adding reaction to the original message if available

                org_channel = self.client.get_channel(org_channel)
                msg = await org_channel.fetch_message(old_id)
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

        if (
            channel in channels
            and emoji in emojis.values()
            and user in authors
        ):
            # Look into making this a seperate function

            edit_status = list(emojis.keys())[list(
                emojis.values()).index(emoji)]

            row = db.getsql(guild, "editorial", "history", "New_ID",
                            New_ID)

            if not row:
                return

            old_id = str(row[0][0])
            org_channel = int(row[0][2])

            stats_msg = stats_msgs[channels.index(channel)]
            Editorial_Channel = self.client.get_channel(channel)
            chapter = list(allowedEdits.keys())[list(allowedEdits.values()).index([channel, stats_msg])]

            embed_msg = await Editorial_Channel.fetch_message(New_ID)

            # colour = {'accepted': 0x46e334, rejected: 0xff550d, 'notsure': 0x00ffa6}

            colour = read("config", guild)["mods"]["colour"]

            updated_embed = embed_msg.embeds[0].to_dict()
            updated_embed["color"] = colour["noVote"]
            updated_embed["footer"][
                "text"] = "Author's Vote - Not Voted Yet"
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
                old_id,
            )

            await update_stats(self.client.user, chapter, guild,
                               Editorial_Channel, stats_msg)

            if old_id.isnumeric():
                # Removing the reaction from original message

                org_channel = self.client.get_channel(org_channel)
                msg = await org_channel.fetch_message(old_id)
                await msg.remove_reaction(emoji, member)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        data = payload.data
        guild_id = data["guild_id"]
        mID = data["id"]
        guild = self.client.get_guild(int(guild_id))
        colour = read("config", guild)["mods"]["colour"]

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, "editorial", sql)
        if 'bot' not in data['author'] and len(results) != 0:
            newID = results[0][0]
            config = read("config", guild)
            allowedEdits = config["mods"]["allowedEdits"]
            prefix = config["prefix"]

            sql2 = f"select author from edit where Message_ID = {mID}"
            results = db.execute(guild, "editorial", sql2)


            # Message_ID, Author_ID, author, Book, chapter, org, sug, res, RankCol, RankChar, channel, Accepted, Rejected, NotSure = db.getsql(guild, 'editorial', 'edit', 'Message_ID', mID)[0]
            msg = data["content"]

            update_sql = f"""UPDATE edit
                            SET Original = ?, Sugested = ?, Reason = ?
                            WHERE Message_ID = {mID}
                            """
            edit_command = f'{prefix}edit '
            suggest_command = f'{prefix}suggest '

            if msg[:(len(edit_command))] == edit_command:   # Replace with startwith
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
                    rankRow, _ = ranking(guild, chapter, org)
                    change_status = f"**Proposed change was found in the chapter at line {rankRow}!**"

                except TypeError:
                    rankRow, _ = None, None
                    change_status = "**Proposed change was not found in the chapter!**"

                except FileNotFoundError:
                    rankRow, _ = None, None
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

            elif msg[:len(suggest_command)] == suggest_command:
                try:
                    chapter, suggestion = msg[len(suggest_command):].split(maxsplit=1)
                    if not chapter.isnumeric():
                        raise ValueError("Chapter number should be a Integer!")
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

                db.execute(guild, "editorial", update_sql,
                           (None, suggestion, None))

            updated_embed_dict["color"] = colour["noVote"]
            updated_embed = discord.Embed.from_dict(updated_embed_dict)

            await msg.edit(embed=updated_embed)
            await update_stats(self.client.user, chapter, guild,
                               Editorial_Channel, msg_stats)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        mID = payload.message_id
        guild_id = payload.guild_id
        guild = self.client.get_guild(int(guild_id))

        sql = f"select New_ID from history where Old_id = {mID}"
        results = db.execute(guild, "editorial", sql)
        if len(results) != 0:
            newID = results[0][0]

            sql2 = f"select chapter from edit where Message_ID = {mID}"
            results = db.execute(guild, "editorial", sql2)

            chapter = results[0][0]

        
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
                await update_stats(self.client.user, chapter, guild,
                                   Editorial_Channel, msg_stats)
            else:
                rand_id = int(random()*10**18)  # Generating a 18 digit random id
                update_sql = f"""UPDATE edit
                                SET Author_ID = 0, Author = "anonymous", Message_ID = "{rand_id}"
                                WHERE Message_ID = {mID}"""

                delete_sql1 = f"""UPDATE history
                                SET Old_ID = "{rand_id}" where Old_ID = {mID}"""

                author = {
                    "name": "Anonymous",
                    "url": "",
                    "icon_url":
                    "https://cdn.discordapp.com/embed/avatars/0.png",
                }

                embed_dict["author"] = author

                updated_embed = discord.Embed.from_dict(embed_dict)
                await edit_msg.edit(embed=updated_embed)

                db.execute(guild, "editorial", update_sql)
                db.execute(guild, "editorial", delete_sql1)


###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Events(client))

