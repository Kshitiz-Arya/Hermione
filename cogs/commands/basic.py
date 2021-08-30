import discord
from discord.ext import commands

from datetime import datetime

import packages.database as db
from packages.command import Book, ranking, read, save, in_channel, EditConverter, update_stats, PersistentView
from typing import Optional

###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################

intents = discord.Intents.default()
intents.reactions = True
permissions = discord.Permissions
permissions.add_reactions = True
permissions.read_messsage_history = True
permissions.use_slash_commands = True


class Basic(commands.Cog):
    """This cog contains all the commands that are exposed to a normal user

    Args:
        Cog (commands.Cog): The base class for all cogs.
    """

    def __init__(self, client):
        self.client = client

    @commands.command()
    @in_channel()
    async def edit(self,
                   ctx: commands.Context,
                   chapter,
                   *,
                   edit: EditConverter) -> Optional[bool]:
        """This command takes editorial request from the editors and post it in the assigned channel.

        Args:
            chapter : The chapter number of the editorial request
            edit : Edits that user wants to make. The general format is Original>>Suggested>>Reason (Optional)

        Format:
            >edit chapter Original Line>>Suggested Line>>Reason for the edit (Optional)

        Example:
            >edit 1 The Birds is flying low.>>The Birds are flying low.>>Are insteed of is :- In this example, editor has provided the reason.

            >edit 1 His name is Leadvone>>His name is LeadVonE :- In this example, editors has not provided the reason
        """
        org, sug, res = edit

        if edit[0] is None:
            return
        guild = ctx.guild

        rankRow, rankChar, change_status = ranking(guild, chapter, org)

        config = read("config", guild)
        allowedEdits = config["mods"]["allowedEdits"]

        if chapter in allowedEdits.keys():
            if len(org) < 2 or len(sug) < 2:
                await ctx.reply(
                    "One or more columns are empty! Please submit requests with proper formatting.",
                    delete_after=10,
                )
                return

            channel_id = ctx.channel.id
            mID = ctx.message.id
            aID = ctx.author.id
            avatar = ctx.author.avatar.url

            try:
                author_name = ctx.author.name if (
                    nick := ctx.author.nick) is None else nick
            except AttributeError:
                author_name = ctx.author.name

            book = Book(chapter, guild)
            current_time = datetime.now()
            editorial_channel_id, msg_stats = allowedEdits[chapter]
            editorial_channel = self.client.get_channel(editorial_channel_id)

            # Sending the embed to distineted channel
            link = ctx.message.jump_url

            colour = read("config", guild)["mods"]["colour"]
            embed = discord.Embed(
                color=colour["No Vote"],
                description=f"[Message Link]({link})",
                timestamp=datetime.now(),
            )
            embed.set_author(name=author_name, icon_url=avatar)
            embed.set_footer(text="Author's Vote - Not Voted Yet")
            embed.add_field(name="Original Text", value=org, inline=False)
            embed.add_field(name="Sugested Text", value=sug, inline=False)
            embed.add_field(name="Reason", value=res, inline=False)
            embed.add_field(name="⠀", value=change_status, inline=False)

            msg_send = await editorial_channel.send(embed=embed, view=PersistentView(self.client))

            insert_statement = {
                '_id': mID,
                'editor_id': aID,
                'editor': author_name,
                'book': book,
                'chapter': chapter,
                'original': org,
                'suggested': sug,
                'reason': res,
                'rank_row': rankRow,
                'rank_col': rankChar,
                'edit_msg_id': msg_send.id,
                'org_channel_id': channel_id,
                'edit_channel_id': editorial_channel_id,
                'status': 'Not Voted Yet',
                'time': current_time,
                'type': 'edit'
            }
            await db.insert(guild.id, "editorial", insert_statement)

            await update_stats(self.client.user, chapter, guild,
                               editorial_channel, msg_stats)

            await ctx.reply("Your edit has been accepted.",
                            delete_after=10,
                            mention_author=False)
            return True
        await ctx.reply("Editing is currently disabled for this chapter.",
                            delete_after=10)

    @in_channel()
    @commands.command()
    async def suggest(self, ctx, chapter, *, suggestion):
        """Editors can use this command to submit any type of suggestions they have or bring notice to any dreaded plothole they may have noticed

        Args:
            chapter : Chapter number for which the suggestion is being submitting.
            suggestion : The suggestion that is being submitted.

        Format:
            >suggest chapter Suggestion

        Example:
            >suggest 1 Hermione is best :- She really is
        """
        guild = ctx.guild
        edit_channels = read("config", guild)["mods"]["allowedEdits"]

        if str(chapter) in edit_channels.keys():
            channel = ctx.channel
            author = ctx.author
            author_name = author.name if author.nick is None else author.nick

            book = Book(chapter, guild)

            msg = ctx.message
            link = msg.jump_url

            avatar = str(author.avatar_url) if bool(
                author.avatar_url) else discord.embeds.EmptyEmbed

            editorial_channel_id, msg_stats = edit_channels[chapter]
            editorial_channel = self.client.get_channel(editorial_channel_id)

            config = read("config", guild)
            colour = config["mods"]["colour"]
            sug = discord.Embed(
                color=colour["No Vote"],
                description=f"[Message Link]({link})",
                timestamp=datetime.now(),
            )
            sug.set_author(name=author_name, icon_url=avatar)
            sug.add_field(name="Suggestion", value=suggestion, inline=False)

            sug.set_footer(
                text="Author's Vote - Not Voted Yet | Provided by Hermione")

            msg_send = await editorial_channel.send(embed=sug, view=PersistentView(self.client))

            update_statement = {
                '_id': msg.id,
                'editor_id': author.id,
                'editor': author_name,
                'book': book,
                'chapter': chapter,
                'suggested': suggestion,
                'edit_msg_id': msg_send.id,
                'org_channel_id': channel.id,
                'edit_channel_id': editorial_channel_id,
                'status': 'Not Voted Yet',
                'type': 'suggestion'
            }
            await db.insert(guild.id, "editorial", update_statement)

            await update_stats(self.client.user, chapter, guild,
                               editorial_channel, msg_stats)

        else:
            await ctx.send("Suggestions for this chapter has been turned off!",
                           delete_after=30)

    @commands.command()
    @in_channel()
    async def invite(self, ctx):
        """[summary]

        Args:
            ctx :- [description]

        Format:
            >invite [description]

        Example:
            >invite [description] :- [description]
        """
        bot_invite = discord.Embed(
            colour=0x5C00AD,
            description="[Invite Link](https://discord.com/api/oauth2/authorize?client_id=649210648689115149&permissions=388288&scope=bot)",
            timestamp=datetime.now(),
        )
        bot_invite.set_author(
            name="Invite the bot to your server using this link!",
            icon_url=self.client.user.avatar_url,
        )
        await ctx.send(embed=bot_invite)

    @commands.command()
    async def dm(self, ctx):
        """[summary]

        Args:
            ctx :- [description]

        Format:
            >dm [description]

        Example:
            >dm [description] :- [description]
        """
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
            name="Thank You for Inviting Hermione to your Library!")
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


# skipcq: PY-D0003
def setup(client):
    client.add_cog(Basic(client))
