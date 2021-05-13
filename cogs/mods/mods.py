import logging
import os
from datetime import date, datetime, timedelta
from io import BytesIO
from dpytools.menus import confirm
from PIL import Image, ImageDraw

import database as db
import discord
import magic
import pandas as pd
from command import Book, in_channel, is_author, ranking, read, save, update_stats
from discord.ext import commands
from discord.ext.commands.converter import (
    ColorConverter,
    MemberConverter,
    TextChannelConverter,
)


class Mods(commands.Cog):

    """
    This cog has all the Mod commands to manage Hermione - the bot.
    """
    def __init__(self, client):
        self.client = client

    @commands.command()
    @in_channel()
    @is_author()
    async def add_book(self, ctx, book: int, chapter: int, end: int = None):
        guild = ctx.guild
        cwd = os.getcwd() + f"/Storage/{guild.id}/books"
        # For some reason the variable, chapter, is not evaluating in else section.
        # This is just a work around until root cause for this problem is found.
        # _ = chapter
        # print(_)
        config = read("config", guild)
        books = config["books"]

        if end:
            books[book] = {"start": chapter, "end": end}
        else:
            books[book] = {"start": chapter, "end": chapter}

        config["books"] = books
        save(config, "config", guild)

        await ctx.send("New Book has been added!")

    @commands.command()
    @in_channel()
    @is_author()
    async def add_chapter(self, ctx, book):
        guild = ctx.guild
        cwd = os.getcwd() + f"/Storage/{guild.id}/books"

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
    async def upload(self, ctx, chapter: int):

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
                print(file.content_type)
                if file.content_type != "text/plain; charset=utf-8":
                    await ctx.send(
                        "Please upload the chapter in txt format only!", delete_after=20
                    )
                    # raise BadArgument
                    return
                path = os.getcwd() + f"/Storage/{guild.id}/books/Chapter-{chapter}.txt"
                await file.save(path)
                await ctx.send("Received the file.", delete_after=20)

                try:
                    editChannel_id = read("config", guild)["mods"]["allowedEdits"][
                        str(chapter)
                    ][0]
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

                        updated_embed_dict["fields"][3]["value"] = change_status
                        updated_embed = discord.Embed.from_dict(updated_embed_dict)

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
    async def remove_book(self, ctx, number):
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
    async def remove_chapter(self, ctx, book_n):
        guild = ctx.guild
        cwd = os.getcwd() + f"/Storage/{guild.id}/books"

        config = read("config", guild)
        books = config["books"]

        books[str(book_n)]["end"] -= 1
        config["books"] = books

        save(config, "config", guild)
        await ctx.send("Chapter has been removed!")

    @commands.command()
    @in_channel()
    @is_author()
    async def allowEdit(self, ctx, chapter, channel: TextChannelConverter):
        guild = ctx.guild

        if Book(chapter, guild):

            if chapter == "suggestion":
                Etype = chapter
                footer_text = ""

            else:
                Etype = "edits"
                footer_text = f"Book {Book(chapter, guild)}, Chapter {chapter} |"

            # book = cmd.Book(chapter, guild)

            info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
            info.add_field(name=f"Accepted {Etype}", value=0, inline=True)
            info.add_field(name=f"Rejected {Etype}", value=0, inline=True)
            info.add_field(name="Not Sure", value=0, inline=True)
            info.add_field(name=f"Total {Etype}", value=0, inline=False)
            info.set_author(
                name="Dodging Prision & Stealing Witches", url="https://dpasw.com"
            )
            info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
            info.set_footer(
                text=f"{footer_text} Provided By Hermione",
                icon_url=self.client.user.avatar_url,
            )

            msg = await channel.send(embed=info)
            await msg.pin()
            config = read("config", guild)
            channels = config["mods"]["channels"]

            config["mods"]["allowedEdits"][chapter] = [channel.id, msg.id]
            channels.append(channel.id)
            config["mods"]["channels"] = channels

            save(config, "config", guild)
            await ctx.send(
                f"Editing Request enabled for chapter {chapter}", delete_after=10
            )
        else:
            await ctx.send(
                "You need to add this chapter using .add_chapter command first!",
                delete_after=20,
            )

    @commands.command()
    @in_channel()
    @is_author()
    async def disableEdit(self, ctx, chapter: int):
        guild = ctx.guild
        config = read("config", guild)

        config["mods"]["allowedEdits"].pop(chapter, None)
        save(config, "config", guild)

        await ctx.send(
            f"Editing Request disabled for chapter {chapter}", delete_after=10
        )

    @commands.command()
    @in_channel()
    @is_author()
    async def stats(self, ctx, chapter: int):
        guild = ctx.guild

        accepted, rejected, notsure, total, book, editors = db.get_stats(guild, chapter)

        info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(
            name="Dodging Prision & Stealing Witches", url="https://dpasw.com"
        )
        info.set_footer(text=f"Book {book}, Chapter {chapter} | Provided By Hermione")

        await ctx.send(embed=info)

    @commands.command()
    @in_channel()
    @is_author()
    async def allstats(self, ctx):
        guild = ctx.guild

        accepted, rejected, notsure, total, book, editors = db.get_stats(guild)

        info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
        info.add_field(name="Number of Editors", value=editors, inline=False)
        info.add_field(name="Accepted Edits", value=accepted, inline=False)
        info.add_field(name="Rejected Edits", value=rejected, inline=False)
        info.add_field(name="Not Sure", value=notsure, inline=False)
        info.add_field(name="Total Edits", value=total, inline=False)
        info.set_author(
            name="Dodging Prision & Stealing Witches", url="https://dpasw.com"
        )
        info.set_thumbnail(url="https://i.postimg.cc/xCBrj9JK/LeadVonE.jpg")
        info.set_footer(text=f"Book - {book}| Provided By Hermione")

        await ctx.send(embed=info)

    @commands.command()
    @in_channel()
    @is_author()
    async def editors(self, ctx, chapter):
        guild = ctx.guild
        sql = "SELECT DISTINCT(Author) FROM edit WHERE chapter=(?)"
        editors = db.execute(guild, "editorial", sql, chapter)
        print(editors)
        await ctx.send(
            "Here is the list of editors who helped with chapter %s" % chapter,
            delete_after=100,
        )
        await ctx.send(
            " ".join([element for tupl in editors for element in tupl]),
            delete_after=100,
        )  # The code inside join is flattening the nested tuple

    @commands.command()
    @in_channel()
    @is_author()
    async def allEditors(self, ctx):
        guild = ctx.guild
        sql = "SELECT DISTINCT(Author) FROM edit"
        editors = db.execute(guild, "editorial", sql)
        print(editors)
        await ctx.send(
            "Here is the list of editors who helped with the editing", delete_after=100
        )
        # The code inside join is flattening the nested tuple
        await ctx.send(
            " ".join([element for tupl in editors for element in tupl]),
            delete_after=100,
        )

    @commands.command()
    @in_channel()
    @is_author()
    async def addAuthor(self, ctx, author: MemberConverter):
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

            await ctx.send(f"Added {author_name} to the Author's list", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def delAuthor(self, ctx, author: MemberConverter):
        guild = ctx.guild
        author_id = author.id
        author_name = author.name or author.nick

        config = read("config", guild)
        authors = config["mods"]["authors"]

        if author_id in authors:
            authors.remove(author_id)
            config["mods"]["authors"] = authors
            save(config, "config", guild)

            await ctx.send(
                f"Removed {author_name} from the Author's list", delete_after=10
            )

        else:
            await ctx.send("Author is not in the list!", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def setEmojis(self, ctx, accepted, rejected, not_sure):
        guild = ctx.guild

        emojis = [accepted, rejected, not_sure]

        for e in emojis:
            await ctx.message.add_reaction(e)

        eTypes = ["accepted", "rejected", "notsure"]
        emojis_dict = dict(zip(eTypes, emojis))

        config = read("config", guild)
        config["mods"]["emojis"] = emojis_dict
        save(config, "config", guild)

        await ctx.send("Emoji list has been updeted!", delete_after=10)

    @commands.command()
    @is_author()
    async def addChannel(self, ctx, channel: TextChannelConverter):
        guild = ctx.guild
        channel_id = channel.id
        channel_name = ctx.channel.name

        config = read("config", guild)
        channels = config["mods"]["channels"]

        if channel_id in channels:
            await ctx.send("Channel is already in the list!", delete_after=10)
        else:
            channels.append(channel_id)
            await ctx.send(
                f"Added {channel_name} to the Channels list", delete_after=10
            )

        config["mods"]["channels"] = channels
        save(config, "config", guild)

    @commands.command()
    @is_author()
    async def delChannel(self, ctx, channel: TextChannelConverter):
        guild = ctx.guild
        channel_id = channel.id
        channel_name = ctx.channel.name

        config = read("config", guild)
        channels = config["mods"]["channels"]

        if channel_id in channels:
            channels.remove(channel_id)
            config["mods"]["channels"] = channels
            save(config, "config", guild)

            await ctx.send(
                f"Removed {channel_name} from the channels list", delete_after=10
            )

        else:
            await ctx.send("Channel is not in the list!", delete_after=10)

    @commands.command()
    @in_channel()
    @is_author()
    async def checkEdits(self, ctx, number, chap=0):
        guild = ctx.guild
        channel = ctx.channel
        date = datetime.now() - timedelta(days=int(number))

        messages = await channel.history(after=date, oldest_first=False).flatten()

        sql = f"select * from edit Order by Message_ID desc limit {len(messages)}"
        result = db.execute(guild, "editorial", sql)
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
        ) = [list(tup) for tup in zip(*result)]
        counter = 0

        for message in messages:
            msg = message.content

            if msg[:6] == ">edit ":
                if str(message.id) not in Message_ID:
                    try:
                        chapter, edits = msg[6:].split(maxsplit=1)
                    except ValueError:
                        pass
                    print(type(chapter), type(chap), chapter == str(chap))
                    if chapter == str(chap) or chap == 0:
                        context = await self.client.get_context(message)

                        result = await ctx.invoke(
                            self.client.get_command("edit"),
                            chapter=chapter,
                            edit=edits,
                            context=context,
                        )
                        print(result)
                        if result is True:
                            Message_ID.append(message.id)
                            counter += 1
        await ctx.send(f"Total Messages Recovered :- {counter}", delete_after=100)

    @commands.command()
    @in_channel()
    @is_author()
    async def export(self, ctx, chapter: int):
        guild = ctx.guild
        conn = db.create_connection(guild, "editorial")
        bio = BytesIO()

        script = (
            f"SELECT * FROM edit WHERE chapter = {chapter} Order By rankLine, rankChar"
        )
        df = pd.read_sql_query(script, conn)
        writer = pd.ExcelWriter(bio, engine="openpyxl")

        df.to_excel(writer, sheet_name=f"Edits - Chapter {chapter}")
        writer.save()
        bio.seek(0)
        # excel_file = bio.read()
        # print(excel_file.__sizeof__())
        await ctx.send(
            f"Here is all the edits in chapter {chapter}",
            file=discord.File(bio, f"Chapter-{chapter}.xlsx"),
        )
        if conn:
            conn.close()

    @commands.command()
    @in_channel()
    @is_author()
    async def changeColour(
        self,
        ctx,
        accepted: ColorConverter,
        rejected: ColorConverter,
        notsure: ColorConverter,
        noVote: ColorConverter):

        guild = ctx.guild
        config = read("config", guild)

        config["mods"]["colour"] = {
            "accepted": accepted.value,
            "rejected": rejected.value,
            "notsure": notsure.value,
            "noVote": noVote.value,
        }

        save(config, "config", guild)
        draw(guild, (accepted.value, rejected.value, notsure.value, noVote.value), 50)

        colour_img = discord.File(f'Storage/{guild.id}/image/colour.png', filename='colour.png')
        await ctx.send("Changed the embed colours to ",file=colour_img, delete_after=20)

    @commands.command()
    @in_channel()
    @is_author()
    async def setPrefix(self, ctx, prefix):
        guild = ctx.guild

        config = read("config", guild)
        config["prefix"] = prefix
        save(config, "config", guild)

        await ctx.send(f"Changed the prefix to {prefix}", delete_after=30)

    @commands.command(aliases=["lat"])
    @in_channel()
    async def latency(self, ctx: commands.Context):
        """
        Command to disply latency in ms.
        Latency is displayed on plain embed in the description field
        """
        ping = await ctx.send("Checking latency...")
        latency_ms = round(
            (ping.created_at.timestamp() - ctx.message.created_at.timestamp()) * 1000, 1
        )
        heartbeat_ms = round(ctx.bot.latency * 1000, 1)
        await ping.edit(
            content="",
            embed=discord.Embed(
                description=f"Latency: `{latency_ms}ms`\nHeartbeat: `{heartbeat_ms}ms`"
            ),
        )

    @commands.command()
    @in_channel()
    async def populate(self, ctx:commands.Context, chapter:int, channel: TextChannelConverter):
        guild = ctx.guild
        bot = self.client.user

        msg = await ctx.send(f"Do you want {channel.name} to be new home for all the edits from chapter {chapter}?", delete_after=40)

        choise = await confirm(ctx, msg, lock=True)
        stats_msg = await update_stats(bot, chapter, guild, channel)

        config = read('config', guild)
        if choise:
            config['mods']['allowedEdits'][str(chapter)] = [channel.id, stats_msg.id]
            save(config, 'config', guild)
        
        sql = 'SELECT * FROM edit where Chapter = ? ORDER BY RankLine, RankChar'
        results = db.execute(guild, 'editorial', sql, str(chapter))
        
        if not results:
            await ctx.send('Aborting the mission! There are not edits in this chapter.', delete_after=20)
        
        for row in results:
            mID, aID, aName, book, chapter, org, sug, res, rLine, rChar, oChannel, accepted, rejected, notSure = row
            
            votes = {'accepted': accepted, 'rejected': rejected, 'notsure': notSure}
            oChannel = guild.get_channel(int(oChannel))

            try:
                msg = await oChannel.fetch_message(int(mID))
                jLink = msg.jump_url
                author = msg.author
                aName = author.name or author.nick
                avatar = str(author.avatar_url)
            
            except discord.errors.NotFound:
                jLink, aName, avatar = None, 'Anonymous', "https://cdn.discordapp.com/embed/avatars/0.png"

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


            colour = config["mods"]["colour"]
            emojis = config['mods']['emojis']

            vote = next((vote for vote, val in votes.items() if val == "1"), 'noVote')

            embed = discord.Embed(
                color=colour[vote],
                description=f"[Message Link]({jLink})",
                timestamp=datetime.now(),
            )

            vote = 'Not Voted Yet' if vote == 'noVote' else vote

            embed.set_author(name=aName, icon_url=avatar)
            embed.set_footer(text=f"Author's Vote - {vote.title() }", icon_url=str(self.client.user.avatar_url))
            print(org, type(org), org is None)
            try:
                if org is not None:
                    embed.add_field(name="Original Text", value=org or '⠀', inline=False)
                    embed.add_field(name="Sugested Text", value=sug, inline=False)
                    embed.add_field(name="Reason", value=res, inline=False)
                    embed.add_field(name="⠀", value=change_status, inline=False)
                else:
                    embed.add_field(name='Suggestion', value=sug)

                msg_send = await channel.send(embed=embed)
            except:
                print(org, sug, res)
                print(type(org))
                breakpoint()

            # column = "('Old_ID', 'New_ID', 'Org_channel')"  #! Update history if message is found
            # values = (mID, msg_send.id, channel_id)
            # db.insert(guild, "editorial", "history", column, values)


            for emoji in emojis.values():
                await msg_send.add_reaction(emoji)


    @commands.command()
    @in_channel()
    @is_author()
    async def settings(self, ctx):
        # Provide all type of infos like name of all the authors, channels where bot is active, emojis, colours prefix and book info
        guild = ctx.guild
        bot = self.client

        config = read('config', guild)
        author_list = config['mods']['authors']
        channels = config['mods']['channels']
        emojis = "   ".join(list(config['mods']['emojis'].values()))
        colour = tuple(config['mods']['colour'].values())
        prefix = config['prefix']
        books = config['books']
        books_count = len(books.keys())
        editing_chapter =f'Chpater {" ,".join(tuple(config["mods"]["allowedEdits"].keys()))}'
        chapter = books[str(books_count)]['end']

        colour_img = discord.File(f'Storage/{guild.id}/image/colour.png', filename='colour.png')

        info=discord.Embed(title="Dodging Prison & Stealing Witches", color=0x7b68d9)
        info.set_author(name="LeadVonE", icon_url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
        # info.set_thumbnail(url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
        info.add_field(name=":books: Book".ljust(20, "⠀"), value=str(books_count).center(7, '⠀'), inline=True)
        info.add_field(name=":green_book: Chapter".ljust(25, "⠀"), value=str(chapter).center(7, '⠀'), inline=True)
        info.add_field(name=":bookmark_tabs: Words", value='646k'.center(7, '⠀'))
        info.add_field(name=":cowboy: Emojis", value=emojis.center(5, '⠀'), inline=True)
        info.add_field(name=":point_right: Prefix", value=f"**{prefix.center(7, '⠀')}**", inline=True)
        info.add_field(name=":man_farmer: Authors", value="LeadVonE, sfu, Kshitiz", inline=True)
        info.add_field(name=":writing_hand: Enabled Edits".center(5, '⠀'), value=editing_chapter.center(15, '⠀'), inline=True)
        info.add_field(name='⠀', value='⠀', inline=True)
        info.add_field(name=":house_with_garden: Channel", value="dpasw-edit, mods".center(10, '⠀'), inline=True)

        for b in range(1, books_count+1):
            start, end = books[str(b)].values()
            info.add_field(name=f":notebook_with_decorative_cover: Book {b}", value=f"{start} - {end}".center(10, '⠀'), inline=True)

        info.add_field(name='⠀', value='**:rainbow_flag: Colour**', inline=False)
        info.set_image(url=f'attachment://colour.png')
        info.set_footer(text="Provided to you by Hermione")
        await ctx.send(embed=info, file=colour_img)
        
def draw(guild, colours, size:int=50):
    #! make a image folder to save all the images

    img = Image.new("RGB", (200, 50), color=None)
    img2 = ImageDraw.Draw(img)
    pos = 0
    for c in colours:
        hex="%06x" % c
        img2.rectangle([pos, 0, 50+pos, 50+pos], fill=f"#{hex}")
        pos += 50

    img.save(f'Storage/{guild.id}/image/colour.png', 'PNG', dpi=(300,300))
    return 1
###############################################################################
#                         AREA FOR SETUP                                      #
###############################################################################


def setup(client):
    client.add_cog(Mods(client))
