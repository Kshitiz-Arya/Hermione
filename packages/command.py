import json
from datetime import datetime
from packages.menu import DefaultMenu
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands.converter import TextChannelConverter

import packages.database as db


class EditConverter(commands.Converter):
    async def convert(self, ctx, argument):
        delimiter = '>>'
        try:
            # splitting the edit request into definable parts
            org, sug, res = argument.split(delimiter)
        except ValueError:
            try:
                org, sug = argument.split(delimiter)
                res = "Not Provided!"

            except ValueError:
                if not ctx.command.name == "checkEdits":
                    await ctx.reply(
                        "Your Edit is missing few thing. Please check and try again",
                        delete_after=10)

                return (None, None, None)

        return (org, sug, res)


class EmbedList:
    """A class that creates pages for Discord messages.

    Attributes
    -----------
    prefix: Optional[:class:`str`]
        The prefix inserted to every page. e.g. three backticks.
    suffix: Optional[:class:`str`]
        The suffix appended at the end of every page. e.g. three backticks.
    max_size: :class:`int`
        The maximum amount of codepoints allowed in a page.
    color: Optional[:class:`discord.Color`, :class: `int`]
        The color of the disord embed. Default is a random color for every invoke
    ending_note: Optional[:class:`str`]
        The footer in of the help embed
    """

    def __init__(self, ctx, **options):
        self.ctx = ctx
        self.colour = options.pop('colour', 0)
        self.tup_list = options.pop('tup_list')
        self.title = options.pop('title', '')
        self.description = options.pop('description', '')
        self.footer = options.pop("footer", False)
        self.author = options.pop('author', '')

        self.size = 24
        self.field_limit = 25
        self.char_limit = 6000
        self.menu = DefaultMenu()
        self.clear()
        self.add_embed(self.tup_list)

    def clear(self):
        """Clears the paginator to have no pages."""
        self._pages = []

    def _check_embed(self, embed: discord.Embed, *chars: str):
        """
        Check if the emebed is too big to be sent on discord

        Args:
            embed (discord.Embed): The embed to check

        Returns:
            bool: Will return True if the emebed isn't too large
        """
        check = (len(embed) + sum(len(char)
                                  for char in chars if char) < self.char_limit
                 and len(embed.fields) < self.field_limit)
        return check

    def _new_page(self):
        """
        Create a new page

        Args:
            title (str): The title of the new page

        Returns:
            discord.Emebed: Returns an embed with the title and color set
        """
        return discord.Embed(title=self.title,
                             description=self.description,
                             timestamp=datetime.now(),
                             color=self.colour)

    def _add_page(self, page: discord.Embed):
        """
        Add a page to the paginator

        Args:
            page (discord.Embed): The page to add
        """
        page.set_footer(text=self.footer)
        page.set_author(name=self.author)
        self._pages.append(page)

    def _chunks(self, tuple_list):
        """ Yield successive num-sized chunks from dicts.
        """
        num = self.size
        if num < 1:
            raise ValueError("Number of Embed fields can't be zero")

        for i in range(0, len(tuple_list), num):
            yield tuple_list[i:i + num]

    def add_embed(self, dicts):
        for d in self._chunks(dicts):
            embed = self._new_page()

            for tup in d:
                name, count = tup
                embed.add_field(name=name, value=count, inline=True)

            self._add_page(embed)

    @property
    def pages(self):
        """Returns the rendered list of pages."""
        if len(self._pages) == 1:
            return self._pages
        lst = []
        for page_no, page in enumerate(self._pages, start=1):
            page: discord.Embed
            page.description = (
                f"`Page: {page_no}/{len(self._pages)}`\n{page.description}")
            lst.append(page)
        return lst

    async def send_embeds(self):
        pages = self.pages
        destination = self.ctx
        await self.menu.send_pages(self.ctx, destination, pages)


def Book(chapter: int, guild: discord.Guild) -> Optional[int]:
    """Takes chapter number and returns the book number

    Args:
        chapter (int): Chapter in the book
        guild (discord.Guild): Represents a Discord Guild

    Returns:
        int or None: Returns book number if found else None
    """
    # Opening File where Book information is kept.
    config = read('config', guild)
    books = config['books']

    for b in books:
        if books[b]['start'] <= int(chapter) <= books[b]['end']:
            return b

    return None


def ranking(guild: discord.Guild, chapter: int, org):
    # This code Rank each sentence according to their position in text file.
    try:
        chapter_file = open(
            f'./Storage/{guild.id}/books/Chapter-{chapter}.txt', 'r')
        #   This is the phrase which we have to search.
        if '\n' in org:  # This is driver code
            org = org.splitlines()

            for count, i in enumerate(chapter_file, 1):
                if org[0] in i:
                    byte = i.find(org[0])
                    change_status = f"**Proposed change was found in the chapter at line {count}!**"
                    return [count, byte, change_status]

        else:
            for count, i in enumerate(chapter_file, 1):
                if org in i:
                    byte = i.find(org)
                    change_status = f"**Proposed change was found in the chapter at line {count}!**"
                    return [count, byte, change_status]

        change_status = "**Proposed change was not found in the chapter!**"
        return [None, None, change_status]

    except FileNotFoundError:
        change_status = "**Chapter has not yet been uploaded!**"
        return [None, None, change_status]


def read(file, guild: discord.Guild):
    with open(f'Storage/{guild.id}/database/{file}.json', "r") as f:
        return json.load(f)


def save(data, file, guild: discord.Guild) -> None:
    with open(f'Storage/{guild.id}/database/{file}.json', "w") as f:
        json.dump(data, f, indent=4)


def get_prefix(guild: discord.Guild):

    return read('config', guild)['prefix']


def in_channel():
    def predicate(ctx):
        guild = ctx.guild
        channels = read('config', guild)['mods']['channels']
        if ctx.channel.id in channels:
            return True

        raise commands.MissingPermissions(
            ['Bot is not active in this channel!'])

    return commands.check(predicate)


def is_author():
    def predicate(ctx):
        guild = ctx.guild

        authors = read('config', guild)['mods']['authors']

        if len(authors) > 0:
            if ctx.message.author.id in authors:
                return True

            raise commands.MissingPermissions(['You are not an Author!'])

        return True

    return commands.check(predicate)


async def update_stats(bot: discord.User,
                       chapter: int,
                       guild: discord.Guild,
                       channel: TextChannelConverter,
                       msg_stats=None) -> None:

    total, editors, book, accepted, rejected, notsure = await db.get_stats(guild, 'editorial', chapter)
    info = discord.Embed(color=0x815BC8, timestamp=datetime.now())

    bot_avatar = str(bot.avatar_url) if bool(bot.avatar_url) else 0

    info.add_field(name="Number of Editors", value=editors, inline=False)
    info.add_field(name="Accepted Edits", value=accepted, inline=True)
    info.add_field(name="Rejected Edits", value=rejected, inline=True)
    info.add_field(name="Not Sure", value=notsure, inline=True)
    info.add_field(name="Total Edits", value=total, inline=False)
    info.set_author(name="Dodging Prision & Stealing Witches")
    info.set_thumbnail(url="https://i.ibb.co/L9Jm2rg/images-5.jpg")
    info.set_footer(
        text=f"Book {book}, Chapter {chapter} | Provided By Hermione",
        icon_url=bot_avatar,
    )

    if not isinstance(msg_stats, int) or msg_stats is None:
        msg = await channel.send(embed=info)
        return msg

    if isinstance(msg_stats, discord.Message):
        await msg_stats.edit(embed=info)

    msg_stats = channel.get_partial_message(msg_stats)
    await msg_stats.edit(embed=info)
