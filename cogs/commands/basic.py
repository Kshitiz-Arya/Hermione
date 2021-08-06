import discord
from discord.ext import commands

from datetime import datetime

import packages.database as db
from packages.command import Book, ranking, read, save, in_channel, EditConverter, update_stats
from typing import Optional

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

    @commands.command()
    @in_channel()
    async def edit(self,
                   ctx: commands.Context,
                   chapter,
                   *,
                   edit: EditConverter,
                   context=0) -> Optional[bool]:
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
                await ctx.reply(
                    "One or more columns are empty! Please submit requests with proper formatting.",
                    delete_after=10,
                )
                return

            channel_id = ctx.channel.id
            if context == 0:
                mID = ctx.message.id
                aID = ctx.author.id
                author_name = (ctx.author.name
                               if ctx.author.nick is None else ctx.author.nick)
                avatar = str(ctx.author.avatar_url) if bool(
                    ctx.author.avatar_url) else 0

            else:
                mID = context.message.id
                aID = context.author.id
                author_name = context.author.name
                avatar = str(context.author.avatar_url) if bool(
                    context.author.avatar_url) else 0

            # if bool(self.client.user.avatar_url):
            #     bot_avatar = str(self.client.user.avatar_url)

            book = Book(chapter, guild)
            column = str(tuple(db.get_table(guild, "editorial",
                                            "edit"))).replace("'", "")

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
            embed.set_footer(text="Author's Vote - Not Voted Yet")
            embed.add_field(name="Original Text", value=org, inline=False)
            embed.add_field(name="Sugested Text", value=sug, inline=False)
            embed.add_field(name="Reason", value=res, inline=False)
            embed.add_field(name="⠀", value=change_status, inline=False)

            msg_send = await Editorial_Channel.send(embed=embed)

            column = "('Old_ID', 'New_ID', 'Org_channel')"
            values = (mID, msg_send.id, channel_id)
            db.insert(guild, "editorial", "history", column, values)

            await update_stats(self.client.user, chapter, guild,
                               Editorial_Channel, msg_stats)

            for emoji in emojis.values():
                await msg_send.add_reaction(emoji)

            if not context:
                await ctx.reply("Your edit has been accepted.",
                                delete_after=10,
                                mention_author=False)
            return True
        if not context:
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

            msg = ctx.message
            link = msg.jump_url

            avatar = str(author.avatar_url) if bool(
                author.avatar_url) else discord.embeds.EmptyEmbed

            Editorial_Channel, msg_stats = edit_channels[chapter]
            Editorial_Channel = self.client.get_channel(Editorial_Channel)

            emojis = read("config", guild)["mods"]["emojis"]

            column = str(tuple(db.get_table(guild, "editorial",
                                            "edit"))).replace("'", "")
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

            sug.set_footer(
                text="Author's Vote - Not Voted Yet | Provided by Hermione")

            msg_send = await Editorial_Channel.send(embed=sug)

            column = "('Old_ID', 'New_ID', 'Org_channel')"
            values = (msg.id, msg_send.id, channel.id)
            db.insert(guild, "editorial", "history", column, values)

            await update_stats(self.client.user, chapter, guild,
                               Editorial_Channel, msg_stats)
            for emoji in emojis.values():
                await msg_send.add_reaction(emoji)

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


def setup(client):
    client.add_cog(Basic(client))
