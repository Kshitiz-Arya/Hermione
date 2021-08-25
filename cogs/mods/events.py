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
        """This event is called when the bot joins a guild

        Args:
            guild (discord.Guild): The guild that the bot joined
        """
        print(f"Joined {guild.name}")

        guild_owner = guild.owner_id

        # print(type(guild.audit_logs(limit=1).next().action))
        def check(event):
            return event.target.id == self.client.user.id   # The fuck I did here?

        bot_entry = await guild.audit_logs(
            action=discord.AuditLogAction.bot_add).find(check)

        directory = ["books", "database", "images"]

        for d in directory:
            os.makedirs(f"Storage/{guild.id}/{d}")

        config = {
            "mods": {
                "colour": {
                    "Accepted": 65280,
                    "Rejected": 16711680,
                    "Not Sure": 16776960,
                    "No Vote": 65535,
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
        edit_id = payload.message_id

        config = read("config", guild)

        authors = config["mods"]["authors"]
        allowedEdits = config["mods"]["allowedEdits"]
        emojis = config["mods"]["emojis"]
        channels = [c[0] for c in list(allowedEdits.values())]

        channels = [c[0] for c in list(allowedEdits.values())]
        stats_msgs = [s[1] for s in list(allowedEdits.values())]

        if (channel in channels and emoji in emojis.values()
                and user_id in authors):
            # Look into making this a seperate function
            edit_status = list(emojis.keys())[list(
                emojis.values()).index(emoji)]
            row = await db.get_document(guild.id, "editorial", {'edit_msg_id': edit_id}, ['_id'])

            if row is None:
                return

            # ids are received in bson.Int64 format, which needs to be converted back to int
            old_id = row['edit_msg_id'].real

            stats_msg = stats_msgs[channels.index(channel)]
            Editorial_Channel = self.client.get_channel(channel)
            chapter = list(allowedEdits.keys())[list(
                allowedEdits.values()).index([channel, stats_msg])]
            mainAuthor = await guild.fetch_member(user_id)
            mainAuthor_name = mainAuthor.nick or mainAuthor.name
            embed_msg = await Editorial_Channel.fetch_message(edit_id)

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
            await db.update(guild.id, "editorial", ['status'], [edit_status], {'_id': old_id})

            await update_stats(  # todo Making bot slow. Average Response time :- 2.70 s
                self.client.user, chapter, guild, Editorial_Channel, stats_msg)

            # todo Figure out another way to check if msg exist or not
            # org_channel = self.client.get_channel(org_channel)
            # msg = await org_channel.fetch_message(old_id)
            # breakpoint()
            # # Adding reaction to the original message if available
            # await msg.add_reaction(emoji)

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
        # member = self.client.user
        emoji = str(payload.emoji)
        edit_id = payload.message_id

        config = read("config", guild)

        authors = config["mods"]["authors"]
        allowedEdits = config["mods"]["allowedEdits"]
        emojis = config["mods"]["emojis"]
        channels = [c[0] for c in list(allowedEdits.values())]

        stats_msgs = [c[1] for c in list(allowedEdits.values())]

        if (channel in channels and emoji in emojis.values()
                and user in authors):
            # Look into making this a seperate function

            row = await db.get_document(guild.id, 'editorial', {'edit_msg_id': edit_id}, ['_id'])

            if row is None:
                return

            org_id = row['_id'].real

            stats_msg = stats_msgs[channels.index(channel)]
            Editorial_Channel = self.client.get_channel(channel)
            chapter = list(allowedEdits.keys())[list(
                allowedEdits.values()).index([channel, stats_msg])]

            embed_msg = await Editorial_Channel.fetch_message(edit_id)

            # colour = {'accepted': 0x46e334, rejected: 0xff550d, 'notsure': 0x00ffa6}

            colour = read("config", guild)["mods"]["colour"]

            updated_embed = embed_msg.embeds[0].to_dict()
            updated_embed["color"] = colour["No Vote"]
            updated_embed["footer"]["text"] = "Author's Vote - Not Voted Yet"
            updated_embed["footer"]["icon_url"] = None
            updated_embed = discord.Embed.from_dict(updated_embed)

            await embed_msg.edit(embed=updated_embed)

            await db.update(guild.id, "editorial", ['status'], ['Not Voted Yet'], {'_id': org_id})

            await update_stats(self.client.user, chapter, guild,
                               Editorial_Channel, stats_msg)

            # if org_id.isnumeric():
            #     # Removing the reaction from original message

            #     org_channel = self.client.get_channel(org_channel)
            #     msg = await org_channel.fetch_message(org_id)
            #     await msg.remove_reaction(emoji, member)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """This event will be called if the editor modify his/her original editorial message

        Args:
            payload (discord.RawMessageUpdateEvent): The payload of the event

        """
        data = payload.data
        guild_id = data["guild_id"]
        msg_id = data["id"]

        guild = self.client.get_guild(int(guild_id))

        config = read("config", guild)
        colour = config["mods"]["colour"]
        allowedEdits = config["mods"]["allowedEdits"]
        prefix = config["prefix"]

        query = {'_id': int(msg_id)}
        results = await db.get_document(guild.id, "editorial", query, ['edit_msg_id'])

        if 'author' not in data.keys() or 'bot' in data['author'] or results is None:
            return

        msg = data["content"]
        edit_msg_id = results['edit_msg_id']

        edit_command = f'{prefix}edit '
        suggest_command = f'{prefix}suggest '

        if msg.startswith(edit_command):  # Replace with startwith
            chapter, edits = msg[len(edit_command):].split(maxsplit=1)

            editorial_channel_id, msg_stats = allowedEdits[chapter]
            editorial_channel = guild.get_channel(editorial_channel_id)
            msg = await editorial_channel.fetch_message(edit_msg_id)

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

            rank_row, rank_col, change_status = ranking(guild, chapter, org)

            updated_embed_dict["fields"][0]["value"] = org
            updated_embed_dict["fields"][1]["value"] = sug
            updated_embed_dict["fields"][2]["value"] = res
            updated_embed_dict["fields"][3]["value"] = change_status

            await db.update(guild, "editorial", ('original', 'suggested', 'reason', 'rank_row', 'rank_col'), (org, sug, res, rank_row, rank_col), {"_id": msg_id})

        elif msg.startswith(suggest_command):
            try:
                chapter, suggestion = msg[len(suggest_command):].split(
                    maxsplit=1)
                if not chapter.isnumeric():
                    raise ValueError("Chapter number should be a Integer!")
            except ValueError:
                return None  # TODO Bot should reply to the edited chapter with error text!

            editorial_channel_id, msg_stats = allowedEdits[chapter]
            editorial_channel = guild.get_channel(editorial_channel_id)
            msg = await editorial_channel.fetch_message(edit_msg_id)

            updated_embed_dict = msg.embeds[0].to_dict()

            vote = updated_embed_dict["footer"]["text"]

            if "Not Voted Yet" not in vote:
                return

            updated_embed_dict["fields"][0]["value"] = suggestion

            await db.update(guild, "editorial", ['suggested'],
                            [suggestion], {"_id": msg_id})

        updated_embed_dict["color"] = colour["No Vote"]
        updated_embed = discord.Embed.from_dict(updated_embed_dict)

        await msg.edit(embed=updated_embed)
        await update_stats(self.client.user, chapter, guild,
                           editorial_channel, msg_stats)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """This event will be called if the editor deletes his/her original editorial message.
        If the edit request has been reviewed by the author(s) then the edit embed will be anonymized.

        Args:
            payload (discord.RawMessageDeleteEvent): The payload of the event

        """
        msg_id = payload.message_id
        guild_id = payload.guild_id
        guild = self.client.get_guild(int(guild_id))

        query = {'_id': int(msg_id)}
        results = await db.get_document(guild.id, "editorial", query, ['chapter', 'edit_msg_id'])

        if results is None:
            return

        _, chapter, edit_msg_id = results.values()

        allowedEdits = read("config", guild)["mods"]["allowedEdits"]
        edit_channel_id, msg_stats = allowedEdits[str(chapter)]
        edit_channel = self.client.get_channel(int(edit_channel_id))
        edit_msg = await edit_channel.fetch_message(edit_msg_id)

        embed_dict = edit_msg.embeds[0].to_dict()

        vote = embed_dict["footer"]["text"]

        if "Not Voted Yet" in vote:

            await edit_msg.delete()
            await db.delete_document(guild.id, 'editorial', {'_id': msg_id})
            await update_stats(self.client.user, chapter, guild,
                               edit_channel, msg_stats)
        else:

            author = {
                "name": "Anonymous",
                "url": "",
                "icon_url":
                "https://cdn.discordapp.com/embed/avatars/0.png",
            }

            embed_dict["author"] = author

            updated_embed = discord.Embed.from_dict(embed_dict)
            await edit_msg.edit(embed=updated_embed)

            await db.update(guild.id, 'editorial', ['editor', 'editor_id'], ['anonymous', 0], {"_id": msg_id})


###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Events(client))
