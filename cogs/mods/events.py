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
                    "Accepted": 65280,
                    "Rejected": 16711680,
                    "Not Sure": 16776960,
                    "No Vote": 65535,
                },
                "allowedEdits": {},
                "emojis": {
                    "Accepted": "\u2705",
                    "Rejected": "\u274c",
                    "Not Sure": "\ud83d\ude10",
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
    async def on_raw_message_edit(self, payload):

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
