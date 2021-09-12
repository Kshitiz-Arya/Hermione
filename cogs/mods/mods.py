import os
from datetime import datetime, timedelta
from io import BytesIO, StringIO

import discord
import packages.database as db
import pandas as pd
from discord.ext import commands
from discord.ext.commands.converter import (ColorConverter, MemberConverter,
                                            TextChannelConverter)
from packages.command import (Book, EmbedList, PersistentView, in_channel,
                              is_author, ranking, read, save, update_stats)
from PIL import Image, ImageDraw


class Mods(commands.Cog):
    """This cog contains commands for moderators to handle the bot.

    Args:
        Cog (commands.Cog): The base class for all cogs.
    """

    def __init__(self, client):
        self.client = client

    @commands.command()
    @in_channel()
    @is_author()
    async def add_book(self,
                       ctx,
                       book: int,
                       first_chapter: int,
                       last_chapter: int = None):
        """This command is used to add a new book.

        Args:
            book : Book Number
            first_chapter : First Chapter of the Book
            last_chapter (optional): Last Chapter of the Book. Defaults to None.

        Format:
            >add_book book-number first-chapter-number last-chapter-number

        Example:
            >add_book 2 15 36 :- In this example, the book only has one chapter, therefore only first chapter is provided
            >add_book 3 37 :- In this example, the book has more then one chapter, therefore first chapter and last chapter are provided.
        """
        # ! Check For Negative Number
        guild = ctx.guild
        config = read("config", guild)
        books = config["books"]

        if not all(num is not None and num > 0
                   for num in (book, first_chapter, last_chapter)):
            await ctx.reply(
                'Please make sure that all the numbers are positive!',
                delete_after=30)
            return

        if last_chapter:
            books[str(book)] = {"start": first_chapter, "end": last_chapter}
        else:
            books[str(book)] = {"start": first_chapter, "end": first_chapter}

        config["books"] = books
        save(config, "config", guild)

        await ctx.send("New Book has been added!")

    @commands.command()
    @in_channel()
    @is_author()
    async def add_chapter(self, ctx: commands.Context, book):
        """This commands is used to add a chapter to a book

        Args:
            book :- The book, in which chapter is to be added

        Format:
            >add_chapter book_number

        Example:
            >add_chapter 3 :- Adding chapter to book no. 3
        """
        guild = ctx.guild
        config = read("config", guild)
        books = config["books"]

        if book in books:
            books[str(book)]["end"] += 1
        else:
            await ctx.send(
                f"Book {book} was not found in the list!\nUse .add_book command to add the book.",
                delete_after=30,
            )
            return

        config["books"] = books
        save(config, "config", guild)

        await ctx.send("New chapter has been added!")

    @commands.command()
    @in_channel()
    @is_author()
    async def upload(self, ctx: commands.Context, chapter: int):
        """This command is used to upload a chapter to the server. User need to attatch the text document of the chapter with the message
        Documnet should be in .txt format

        Args:
            chapter :- The chapter number of chapter being uploaded

        Format:
            >upload chapter_number (User need to attatch the text document of the chapter with the message)

        Example:
            >upload 1 (Attach the Chapter Document):- Uploading chapter 2
        """
        msg = ctx.message
        attach = msg.attachments
        guild = ctx.guild

        if attach:
            for file in attach:
                print(file.content_type)
                if file.content_type != "text/plain; charset=utf-8":
                    await ctx.send(
                        "Please upload the chapter in txt format only!",
                        delete_after=20)
                    # raise BadArgument
                    return
                path = os.getcwd(
                ) + f"/Storage/{guild.id}/books/Chapter-{chapter}.txt"
                await file.save(path)
                await ctx.send("Received the file.", delete_after=20)

                try:
                    editChannel_id = read(
                        "config",
                        guild)["mods"]["allowedEdits"][str(chapter)][0]
                except KeyError:
                    return

                editChannel = guild.get_channel(editChannel_id)

                async for message in editChannel.history():

                    if len(message.embeds) == 0:
                        continue

                    updated_embed_dict = message.embeds[0].to_dict()
                    org = updated_embed_dict["fields"][0]["value"]
                    edit_type = updated_embed_dict["fields"][0]["name"]

                    if edit_type == "Suggestion":
                        continue

                    try:
                        rank = ranking(guild, chapter, org)
                        if isinstance(rank, FileNotFoundError):
                            raise FileNotFoundError
                        rankRow, _ = rank
                        change_status = f"**Proposed change was found in the chapter at line {rankRow}!**"

                    except FileNotFoundError:
                        rankRow = None
                        change_status = "**Chapter is yet to be uploaded!**"

                    except TypeError:
                        rankRow = None
                        change_status = (
                            "**Proposed change was not found in the chapter!**"
                        )

                    try:
                        reason_name = updated_embed_dict["fields"][2]['name']
                        if reason_name != 'Reason':
                            continue

                        updated_embed_dict["fields"][3][
                            "value"] = change_status
                        updated_embed = discord.Embed.from_dict(
                            updated_embed_dict)

                    except IndexError:
                        # ! This can be remove once we exit the current guild. This is here mostly for backward compatiblity
                        updated_embed_dict["fields"].append({
                            "name": "⠀",
                            "value": change_status,
                            "inline": False,
                        })

                    await message.edit(embed=updated_embed)

                await ctx.send("Updated all the edit status", delete_after=20)

        else:
            await ctx.send("No file included!")
            await ctx.send("Please try again!")

    @commands.command()
    @in_channel()
    @is_author()
    async def remove_book(self, ctx: commands.Context, number):
        """This command is used to remove a book from the bot

        Args:
            number :- Book number to be removed

        Format:
            >remove_book book_number

        Example:
            >remove_book 1 :- Removing the Book 1
        """
        guild = ctx.guild
        config = read("config", guild)
        books = config["books"]

        books.pop(str(number))

        config["books"] = books
        save(config, "config", guild)
        await ctx.send(f"Book {number} has been removed!")

    @commands.command()
    @in_channel()
    @is_author()
    async def remove_chapter(self, ctx: commands.Context, book_n):
        """This command is used to remove one chapter from a book

        Args:
            book_n :- Book number from which one chapter is being removed

        Format:
            >remove_chapter book_number

        Example:
            >remove_chapter 3 :- Removing one chapter from the Book 3
        """
        guild = ctx.guild
        config = read("config", guild)
        books = config["books"]

        books[str(book_n)]["end"] -= 1
        config["books"] = books

        save(config, "config", guild)
        await ctx.send("Chapter has been removed!")

    @commands.command()
    @in_channel()
    @is_author()
    async def allowEdit(self, ctx: commands.Context, chapter: int,
                        channel: TextChannelConverter):
        """This command is used to enable editing for a given chapter

        Args:
            chapter :- Chapter for which editing is being enabled
            channel :- Channel where all edits of the chpater will be posted. This can be Channel mention, Channel ID or Channel name.

        Format:
            >allowEdit chapter Channel-mention/name/id

        Example:
            >allowEdit 2 #edit-2 :- Enabled edits for chapter 2 and posting all edits to channel "edit-2". Here User has mentioned the channel

            >allowEdit 3 edit-3 :- Enableing edits for chapter 3 and posting all edits to channel "edit-3". Here User has provided the channel name.

            >allowEdit 4 839217799695171543 :- Enabling edits for chapter 4 and posting all edits to channel with provided ID. Here Used has provided the channel id.

        """
        guild = ctx.guild

        if Book(chapter, guild):

            Etype = "edits"
            footer_text = f"Book {Book(chapter, guild)}, Chapter {chapter} |"

            # book = cmd.Book(chapter, guild)

            info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
            info.add_field(name=f"Accepted {Etype}", value=0, inline=True)
            info.add_field(name=f"Rejected {Etype}", value=0, inline=True)
            info.add_field(name="Not Sure", value=0, inline=True)
            info.add_field(name=f"Total {Etype}", value=0, inline=False)
            info.set_author(name="Dodging Prision & Stealing Witches",
                            url="https://dpasw.com")
            info.set_thumbnail(
                url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
            info.set_footer(
                text=f"{footer_text} Provided By Hermione",
                icon_url=self.client.user.display_avatar,
            )

            msg = await channel.send(embed=info)
            await msg.pin()
            config = read("config", guild)
            channels = config["mods"]["channels"]

            config["mods"]["allowedEdits"][chapter] = [channel.id, msg.id]
            channels.append(channel.id)
            config["mods"]["channels"] = channels

            save(config, "config", guild)
            await ctx.send(f"Editing Request enabled for chapter {chapter}",
                           delete_after=10)
        else:
            await ctx.send(
                "You need to add this chapter using **.add_chapter** command first!",
                delete_after=20,
            )

    @commands.command()
    @in_channel()
    @is_author()
    async def disableEdit(self, ctx: commands.Context, chapter: str):
        """This command is used to disable edit for a given chapter

        Args:
            chapter :- Chapter number for which editing is to be disabled

        Format:
            >disableEdit chapter-num

        Example:
            >disableEdit 3 :- Disabling edit for chapter number 3
        """
        guild = ctx.guild
        config = read("config", guild)

        channel = config["mods"]["allowedEdits"][chapter][0]
        config['mods']['channels'].remove(channel)

        config["mods"]["allowedEdits"].pop(chapter, None)
        save(config, "config", guild)

        await ctx.send(f"Editing Request disabled for chapter {chapter}",
                       delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def stats(self, ctx: commands.Context, chapter: int):
        """This command is used to get various statistics about a certain chapter. These stats include total edits, count of Accepted and Rejected edit and word count.

        Args:
            chapter :- Chapter for which stats is needed

        Format:
            >stats chapter-number

        Example:
            >stats 2 :- Requesting Statistics about chapter 3
        """
        guild = ctx.guild

        result = await db.get_stats(guild, 'editorial', chapter)
        if not result:  # Empty result means no entery for the chapter
            await ctx.send('No **Stats** found for this chapter', delete_after=30)
            return

        total, editors, book, accepted, rejected, notsure = result

        info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(name="Dodging Prision & Stealing Witches",
                        url="https://dpasw.com")
        info.set_footer(
            text=f"Book {book}, Chapter {chapter} | Provided By Hermione")

        await ctx.send(embed=info)

    @commands.command()
    @in_channel()
    @is_author()
    async def allstats(self, ctx):
        """This command is used to get statistics about every books and their edits.

        Args:
            None
        Format:
            >allstats

        Example:
            >allstats :- Getting stats about every books and their edits.
        """
        guild = ctx.guild

        result = await db.get_stats(guild, 'editorial')
        if not result:  # Empty result means no entery for the chapter
            await ctx.send('No **Stats** found', delete_after=30)
            return

        total, editors, book, accepted, rejected, notsure = result

        print(book)
        info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(name="Dodging Prision & Stealing Witches",
                        url="https://dpasw.com")
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.set_footer(text=f"Total Book - {book}| Provided By Hermione")

        await ctx.send(embed=info)

    @commands.command()
    @in_channel()
    @is_author()
    async def editors(self,
                      ctx: commands.Context,
                      chapter: int,
                      return_type: str = None):
        """This command is used to get the list of each editors who has worked on a given chapter.

        Args:
            chapter :- Chapter number for which list of editors is needed
            type (optional) :- If set, bot will send the list of editors name instead of the embed. Pass 'list' to toggle this argument

        Format:
            >editors chapter-number

        Example:
            >editors 4 :- Get the embed with editor's name and number of edits they have submitted for chapter 4
            >editors 1 list :- Getting list of editors who has worked on chapter 1
        """
        guild = ctx.guild
        sql = """SELECT Author, COUNT(*) as num FROM edit WHERE chapter=(?) GROUP BY author_id ORDER BY Author"""

        editors = db.execute(guild, "editorial", sql, str(chapter)) or []

        if not editors:
            await ctx.send('**No Editors Found**', delete_after=30)
            return

        if return_type is not None and return_type.lower() == 'list':
            names = ", ".join(editor[0] for editor in editors)
            file = StringIO(names)
            file.seek(0)
            await ctx.send(file=discord.File(
                file, filename=f'Editors List - Chap {chapter}.txt'))

        else:
            title = f'Editors - Chapter {chapter}'
            author = 'Dodging Prision & Stealing Witches'
            footer = f'Total Editors - {len(editors)}'

            embeds = EmbedList(ctx,
                               tup_list=editors,
                               title=title,
                               author=author,
                               footer=footer,
                               colour=0x858393)
            await embeds.send_embeds()

    @commands.command()
    @in_channel()
    @is_author()
    async def allEditors(self, ctx, return_type: str = None):
        """This command is used to get list of every editors

        Args:
            type (optional) :- If set, bot will send the list of editors name instead of the embed. Pass 'list' to toggle this argument

        Format:
            >allEditors list (optional)

        Example:
            >allEditors  :- Get the embed with editor's name and number of edits they have submitted.
            >allEditors list :- Getting list of every editors
        """
        guild = ctx.guild
        sql = """SELECT Author, COUNT(*) as num FROM edit GROUP BY author_id ORDER BY Author"""

        editors = db.execute(guild, "editorial", sql) or []

        if not editors:
            await ctx.send('**No Editors Found**', delete_after=30)
            return

        if return_type is not None and return_type.lower() == 'list':
            names = ", ".join(editor[0] for editor in editors)
            file = BytesIO(bytes(names, encoding='utf-8'))
            file.seek(0)
            await ctx.send(file=discord.File(file, filename='Editors List.txt')
                           )

        else:

            author = 'Dodging Prision & Stealing Witches'
            footer = f'Total Editors - {len(editors)}'

            embeds = EmbedList(ctx,
                               tup_list=editors,
                               author=author,
                               footer=footer,
                               colour=0x858393)
            await embeds.send_embeds()

    @commands.command()
    @in_channel()
    @is_author()
    async def addAuthor(self, ctx: commands.Context, author: MemberConverter):
        """Adding members to Author list. These authors has permission to change the bot settings.

        Args:
            author :- Member who are to be added to the Author's list. This can be member's name, id or mention.

        Format:
            >addAuthor Member-mention, id or name

        Example:
            >addAuthor #Kshitiz :- Adding Kshitiz to Authors list. Here Kshitiz has been mentioned
            >addAuthor Kshitiz :- Adding Kshitiz to Authors list. Here Kshitiz's name has been provided
            >addAuthor 843478299246329432 :- Adding Kshitiz to Authors list. Here Kshitiz's id has been provided
        """
        guild = ctx.guild
        author_id = author.id
        author_name = author.name or author.nick

        config = read("config", guild)
        authors = config["mods"]["authors"]

        if author_id in authors:
            await ctx.send("Author is already in the list!", delete_after=10)
        else:
            authors.append(author_id)
            config["mods"]["authors"] = authors
            save(config, "config", guild)

            await ctx.send(f"Added {author_name} to the Author's list",
                           delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def delAuthor(self, ctx: commands.Context, author: MemberConverter):
        """This command is used to remove a member from Authors list

        Args:
            author :- Member who is to be removed from Authors list. This can be Member's mention, id or name

        Format:
            >delAuthor Authors-mention/id/name

        Example:
            >delAuthor #Kshitiz :- Removing Kshitiz from the Authors list. Here Kshitiz has been mentioned.
            >delAuthor Kshitiz :- Removing Kshitiz from the Authors list. Here Kshitiz's name has been provided
            >delAuthor 843478299246329432 :- Removing Kshitiz from the Authors list. Here Kshitiz's id has been provided
        """
        guild = ctx.guild
        author_id = author.id
        author_name = author.name or author.nick

        config = read("config", guild)
        authors = config["mods"]["authors"]

        if author_id in authors:
            authors.remove(author_id)
            config["mods"]["authors"] = authors
            save(config, "config", guild)

            await ctx.send(f"Removed {author_name} from the Author's list",
                           delete_after=10)

        else:
            await ctx.send("Author is not in the list!", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def setEmojis(self, ctx: commands.Context, accepted, rejected,
                        not_sure):
        """This program is used to change the default emojis for voting perpose.

        Args:
            accepted :- Emoji that will be used for accepting the edit
            rejected :- Emoji that will be used for rejecting the edit
            not_sure :- Emoji that will be used when author is not sure about the edit

        Format:
            >setEmojis accepting-emoji rejecting-emoji not_sure-emoji

        Example:
            >setEmojis ✔️ ❌ 😐 :- Changing the emojis used for accepting, rejecting and when author is not sure to ✔️ ❌ and 😐 respectively
        """
        guild = ctx.guild

        emojis = [accepted, rejected, not_sure]

        for e in emojis:
            await ctx.message.add_reaction(e)

        eTypes = ["Accepted", "Rejected", "Not Sure"]
        emojis_dict = dict(zip(eTypes, emojis))

        config = read("config", guild)
        config["mods"]["emojis"] = emojis_dict
        save(config, "config", guild)

        await ctx.send("Emoji list has been updeted!", delete_after=10)

    @commands.command()
    @is_author()
    async def addChannel(self, ctx: commands.Context,
                         channel: TextChannelConverter):
        """This command is used to allow bot to add a channel to the allowed-channel list.  Bot won't respond to any command outside of allowed-channel list

        Args:
            channel :- Channel where bot will interact with users or authors. This can be Channels mention, id or name

        Format:
            >addChannel channel-mention/id/name

        Example:
            >addChannel #edit :- Adding channel "edit" to the allowed-channels list. Here channel has been mentioned
            >addChannel edit :- Adding channel "edit" to the allowed-channels list. Here channel's name has been provided
            >addChannel 842349594825457533 :- Adding channel with given id to the allowed-channels list. Here channel's id has been provided
        """
        guild = ctx.guild
        channel_id = channel.id
        channel_name = channel.name

        send_messages = channel.permissions_for(guild.me).send_messages
        if not send_messages:
            await ctx.reply(
                f"Bot doesn't have permission to **send messages** in **{channel.name}**!\nPlease add the bot to the channel first!",
                delete_after=30)
            return

        config = read("config", guild)
        channels = config["mods"]["channels"]

        if channel_id in channels:
            await ctx.send("Channel is already in the list!", delete_after=10)
        else:
            channels.append(channel_id)
            await ctx.send(
                f"Added __**{channel_name}**__ to the Channels list",
                delete_after=10)

        config["mods"]["channels"] = channels
        save(config, "config", guild)

    @commands.command()
    @is_author()
    async def delChannel(self, ctx: commands.Context,
                         channel: TextChannelConverter):
        """This command is used to remove given channel from the allowed-channel list.

        Args:
            channel :- Channel which is to be removed from the allowed-channel list. This can be channel mention, id or name

        Format:
            >delChannel Channel-mention/id/name

        Example:
            >delChannel #edit :- Removing channel "edit" from the allowed channel list. Here channel has been mentioned.
            >delChannel edit :- Removing channel "edit" from the allowed channel list. Here channel's name has been provided.
            >delChannel 842349594825457533 :- Removing channel with given id from the allowed channel list. Here channel's id has been provided.
        """
        guild = ctx.guild
        channel_id = channel.id
        channel_name = channel.name

        config = read("config", guild)
        channels = config["mods"]["channels"]

        if channel_id in channels:
            channels.remove(channel_id)
            config["mods"]["channels"] = channels
            save(config, "config", guild)

            await ctx.send(
                f"Removed __**{channel_name}**__ from the channels list",
                delete_after=10)

        else:
            await ctx.send("Channel is not in the list!", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def checkEdits(self, ctx: commands.Context, days: int) -> None:
        """This command is used to pickup any edit or suggestion, which bot may have missed due to any reason.

        Args:
            No-of-days :- Number of previous days to look for edits in message history

        Format:
            >checkEdits days chapter(optional)

        Example:
            >checkEdits 2 :- Hermione will look for edits in last 2 days of message history
        """
        count = 0
        guild = ctx.guild
        channel = ctx.channel
        date = datetime.now() - timedelta(days=days)
        prefix = ctx.clean_prefix
        message = channel.history(
            after=date, oldest_first=True).filter(filter_commands, prefix)

        old_msg_ids_dicts = await db.get_documents(guild.id, "editorial", {"time": {"$gt": date}}, ['_id'])
        old_msg_ids = [x['_id'] for x in old_msg_ids_dicts]

        async for msg in message:
            if msg.id not in old_msg_ids:
                context = await self.client.get_context(msg)
                status = await self.client.invoke(context)

                count += 1 if status else 0

        await ctx.send(f"Total number of messages picked up : {count}", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def export(self, ctx: commands.Context, chapter: str):
        """This cahpter is used to get all edits and suggestion in .xlsx format

        Args:
            chapter :- Chapter number for which edit are requested

        Format:
            >export chapter-number

        Example:
            >export 1 :- Requested edits and suggestions for chapter 1
        """
        guild = ctx.guild
        bio = BytesIO()

        return_keys = ['editor', 'original', 'suggested', 'reason', 'rank_row', 'rank_col', 'status', 'type', 'time']
        documents = await db.get_documents(guild.id, "editorial", {"chapter": chapter}, return_keys)
        votes = await db.get_voting_count(guild.id, 'editorial', chapter=chapter)

        # Merge documents and votes and create a excel file from it
        df = pd.DataFrame(documents)
        v = pd.DataFrame(votes)
        df = df.merge(v, on='_id', how='outer')
        df.fillna(0, inplace=True)
        df.to_excel(bio, index=False)

        bio.seek(0)
        await ctx.reply(
            f"Here is all the edits in chapter {chapter}",
            file=discord.File(bio, f"Chapter-{chapter}.xlsx"),
            mention_author=False
        )


    @commands.command(aliases=["changeColor"])
    @in_channel()
    @is_author()
    async def changeColour(self, ctx: commands.Context,
                           accepted: ColorConverter, rejected: ColorConverter,
                           notsure: ColorConverter, noVote: ColorConverter):
        """This command is used to change the default embed colours for edit is posted, accepted, rejected or when author is not sure about the edit

        Args:
            accepted :- Colour in hex format for Accepted embed
            rejected :- Colour in hex format for Rejected embed
            notsure :- Colour in hex format for when author is not sure about the edit
            noVote :- Colour in hex format when edit is yet to be voted by the author

        Format:
            >changeColour accepted-colour rejected-colour notsure-colour noVote-colour

        Example:
            >changeColour #0f0 #f00 #ff0 #0ff :- Changing dufault embed colour to #0f0 for accepted-edit, #f00 for rejected-edit, #ff0 for when author is not sure about the edit and #0ff for when edit is yet to be voted
            >changeColour #00ff00 #ff0000 #ffff00 #00ffff :- Changing dufault embed colour to #00ff00 for accepted-edit, #ff0000 for rejected-edit, #ffff00 for when author is not sure about the edit and #00ffff for when edit is yet to be voted
        """
        guild = ctx.guild
        config = read("config", guild)

        config["mods"]["colour"] = {
            "Accepted": accepted.value,
            "Rejected": rejected.value,
            "Not Sure": notsure.value,
            "Not Voted Yet": noVote.value,
        }

        save(config, "config", guild)
        draw(guild,
             (accepted.value, rejected.value, notsure.value, noVote.value))

        colour_img = discord.File(f'Storage/{guild.id}/images/colour.png',
                                  filename='colour.png')
        await ctx.send("Changed the embed colours to ",
                       file=colour_img,
                       delete_after=20)

    @commands.command()
    @in_channel()
    @is_author()
    async def setPrefix(self, ctx: commands.Context, prefix):
        """This command is used to change the default prefix to interact the bot

        Args:
            prefix :- New prefix

        Format:
            >setPrefix new-prefix

        Example:
            >setPrefix ! :- Changing the default prefix to !
        """
        guild = ctx.guild

        config = read("config", guild)
        config["prefix"] = prefix
        save(config, "config", guild)

        await ctx.send(f"Changed the prefix to {prefix}", delete_after=30)

    @commands.command(aliases=["lat"])
    @in_channel()
    async def latency(self, ctx: commands.Context):
        """This command used to disply latency in ms. Latency is displayed on plain embed in the description field

        Args:
            None
        Format:
            >latency

        Example:
            >latency  :- Displaing latency is ms
        """
        ping = await ctx.send("Checking latency...")
        latency_ms = round(
            (ping.created_at.timestamp() - ctx.message.created_at.timestamp())
            * 1000, 1)
        heartbeat_ms = round(ctx.bot.latency * 1000, 1)
        await ping.edit(
            content="",
            embed=discord.Embed(
                description=f"Latency: `{latency_ms}ms`\nHeartbeat: `{heartbeat_ms}ms`"),
        )

    @commands.command()
    @in_channel()
    @is_author()
    async def migrate(self, ctx: commands.Context, chapter: str,
                      channel: TextChannelConverter):
        """This command is used to migrate all the edits of a given chapter from one channel to another. This command is useful when older channel is either unusable or has been deleted.

        Args:
            chapter :- Chapter for which edits are to be migrated
            channel :- Channel where edits are to be posted. This can be channel mention, id or name

        Format:
            >migrate chapter-name channel-mention/id/name

        Example:
            >migrate 1 #edit :- Populating the edits of chapter 1 to channel edit. Here channel is mentioned
            >migrate 1 edit :- Populating the edits of chapter 1 to channel edit. Here channel name is provided
            >migrate 1 842349594825457533 :- Populating the edits of chapter 1 to channel with provided id. Here channel id is provided
        """
        guild = ctx.guild
        buttons = PersistentView(self.client)
        image_url = ''
        stats_msg = await update_stats(self.client.user, chapter, guild, channel)

        config = read("config", guild)
        config['mods']['allowedEdits'][chapter] = [channel.id, stats_msg.id]
        config['mods']['channels'].append(channel.id)
        save(config, "config", guild)

        documents = await db.get_documents(guild.id, 'editorial', {'chapter': chapter, 'type': 'edit'}, ['_id', 'edit_msg_id', 'editor', 'editor_id', 'original', 'suggested', 'reason', 'status', 'org_channel_id', 'time'])
        for doc in documents:
            org_msg_id, editor_id, editor_name, original, suggested, reason, edit_msg_id, org_channel_id, status, time = doc.values()
            jump_link = f"https://discord.com/channels/{guild.id}/{org_channel_id}/{org_msg_id}"
            change_status = ranking(guild, chapter, original)[2]

            if editor_id:
                editor = await guild.fetch_member(editor_id)
                editor_avatar = editor.display_avatar.url
            else:
                editor_avatar = '"https://cdn.discordapp.com/embed/avatars/0.png"'

            embed = discord.Embed(
                color=config['mods']['colour'][status],
                description=f"[Message Link]({jump_link})",
                timestamp=time,
            )
            embed.set_author(name=editor_name, icon_url=editor_avatar)
            embed.set_footer(text=f"Author's Vote - {status}")
            embed.add_field(name="Original Text", value=original, inline=False)
            embed.add_field(name="Sugested Text",
                            value=suggested, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="⠀", value=change_status, inline=False)

            if status != 'Not Voted Yet':
                data = await buttons.get_voteing_graph(guild.id, edit_msg_id)
                image_url = await buttons.get_image_url(data['image']) if data else ''
                yes, no, maybe = (0, 0, 0) if not data else data['votes']

                embed.set_image(url=image_url)
                embed.add_field(name="Yes", value=yes, inline=True)
                embed.add_field(name="No", value=no, inline=True)
                embed.add_field(name="Maybe", value=maybe, inline=True)

            msg_sent = await channel.send(embed=embed, view=buttons)
            await db.update(guild.id, 'editorial', ['edit_msg_id', 'edit_channel_id'], [msg_sent.id, channel.id], {'_id': org_msg_id})

        await ctx.reply(f'Successfully migrated {len(documents)} edits to {channel.mention}', mention_author=False)

    @commands.command()
    @in_channel()
    @is_author()
    async def settings(self, ctx: commands.Context):
        """This command display all type of informations like author, channels where bot is active, book info and more

        Args:
            None
        Format:
            >settings

        Example:
            >settings  :- Displaying different informations and settings of Hermione
        """
        # Provide all type of infos like name of all the authors, channels where bot is active, emojis, colours prefix and book info
        async with ctx.typing():

            guild = ctx.guild

            config = read('config', guild)
            author_list = config['mods']['authors']
            channels_list = config['mods']['channels']
            emojis = "   ".join(list(
                config['mods']['emojis'].values())) + '\n⠀'
            prefix = config['prefix']
            books = config['books']
            books_count = len(books.keys())

            editing_chapter = tuple(config["mods"]["allowedEdits"].keys())
            editing_channels = [
                c[0] for c in config['mods']['allowedEdits'].values()
            ]
            editing_chapter_str = f'Chpater {" ,".join(editing_chapter)} \n⠀' if len(
                editing_chapter) > 0 else '**No Active Chapters**\n⠀'
            chapter = books[str(books_count)]['end'] if len(books) > 0 else 0

            colour_img = discord.File(f'Storage/{guild.id}/images/colour.png',
                                      filename='colour.png')

            author_names = set()
            channel_names = set()

            interactive_channels = set(channels_list) - set(
                editing_channels
            )  # List of channel except channels where edits are posted!

            for author_id in author_list:
                _ = await guild.fetch_member(author_id)
                author_names.update({_.name})

            for channel_id in interactive_channels:
                _ = guild.get_channel(channel_id)
                channel_names.update({_.name})

            authors_name = ", ".join(author_names)
            channels_name = ", ".join(channel_names)

            info = discord.Embed(title="Dodging Prison & Stealing Witches",
                                 color=0x7b68d9)
            info.set_author(name="LeadVonE",
                            icon_url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
            # info.set_thumbnail(url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
            info.add_field(name=":books: Book".ljust(20, "⠀"),
                           value=(str(books_count) + '\n⠀').center(7, '⠀'),
                           inline=True)
            info.add_field(name=":green_book: Chapter".ljust(25, "⠀"),
                           value=str(chapter).center(7, '⠀'),
                           inline=True)
            info.add_field(name=":bookmark_tabs: Words",
                           value='646k'.center(7, '⠀'))
            info.add_field(name=":cowboy: Emojis",
                           value=emojis.center(5, '⠀'),
                           inline=True)
            info.add_field(name=":point_right: Prefix",
                           value=f"**{prefix.center(7, '⠀')}**",
                           inline=True)
            info.add_field(name=":man_farmer: Authors",
                           value=f"**{authors_name}**",
                           inline=True)
            info.add_field(name=":writing_hand: Enabled Edits".center(5, '⠀'),
                           value=editing_chapter_str.center(15, '⠀'),
                           inline=True)
            info.add_field(name='⠀', value='⠀', inline=True)
            info.add_field(name=":house_with_garden: Channel",
                           value=f"**{channels_name}**".center(10, '⠀'),
                           inline=True)

            for b in range(1, books_count + 1):
                start, end = books[str(b)].values()
                info.add_field(
                    name=f":notebook_with_decorative_cover: Book {b}",
                    value=f"{start} - {end}".center(10, '⠀'),
                    inline=True)

            info.add_field(name='⠀',
                           value='**:rainbow_flag: Colour**',
                           inline=False)
            info.set_image(url='attachment://colour.png')
            info.set_footer(text="Provided to you by Hermione")
            await ctx.send(embed=info, file=colour_img)


def draw(guild: discord.Guild, colours: tuple):
    """Generate a palette image with all the colours passed as tuple

    Args:
        guild (discord.Guild): [Represents a Discord guild.]
        colours (int): [The raw integer colour valu]
        size (int, optional): [Size of each colour palette]. Defaults to 50.

    Returns:
        [None]
    """
    img = Image.new("RGB", (200, 50), color=None)
    img2 = ImageDraw.Draw(img)
    pos = 0
    for c in colours:
        colour_hex = "%06x" % c
        img2.rectangle([pos, 0, 50 + pos, 50 + pos], fill=f"#{colour_hex}")
        pos += 50

    img.save(f'Storage/{guild.id}/images/colour.png', 'PNG', dpi=(300, 300))


def filter_commands(message: discord.Message, prefix) -> bool:
    """Return true if the message is a valid command

    Args:
        message (discord.Message): [Represents a Discord message.]

    Returns:
        [bool]
    """
    # prefix = message.context.clean_prefix
    return message.content.startswith(prefix+'edit ') or message.content.startswith(prefix+'suggest ')

###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################

# skipcq: PY-D0003


def setup(client):
    client.add_cog(Mods(client))
