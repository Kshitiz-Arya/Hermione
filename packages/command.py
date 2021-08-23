import json
from datetime import datetime

from packages.menu import DefaultMenu
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands.converter import TextChannelConverter
from matplotlib import pyplot as plt
from io import BytesIO

import packages.database as db


class EditConverter(commands.Converter):
    """Extract original sentence, suggested sentence and reason from edit request.

    Attributes:
        original_sentence (str): Original sentence.
        suggested_sentence (str): Suggested sentence.
        reason (str): Reason for the edit.
    """

    def __init__(self):
        self.original_sentence = None
        self.suggested_sentence = None
        self.reason = None

    async def convert(self, ctx, argument):
        """Convert argument to edit request."""
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
        """ Yield successive num-sized chunks from dicts."""
        num = self.size
        if num < 1:
            raise ValueError("Number of Embed fields can't be zero")

        for i in range(0, len(tuple_list), num):
            yield tuple_list[i:i + num]

    def add_embed(self, dicts):
        """ Add a list of embeds to the paginator"""
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
        """Sends the pages to the channel."""
        pages = self.pages
        destination = self.ctx
        await self.menu.send_pages(self.ctx, destination, pages)


class PersistentView(discord.ui.View):
    def __init__(self, client: discord.Client, *args, **kwargs):
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(emoji="<:aye:877951041985982504>", style=discord.ButtonStyle.green, custom_id='persistent_view:green')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):  # skipcq: PYL-W0613
        """ This function is called when the green button is pressed.

        Args:
            button (discord.ui.Button): The button that was clicked
            interaction (discord.Interaction): The interaction data for the button
        """
        return_data = await self.preprocessing(interaction, 2)
        await interaction.response.defer()

        if return_data:
            guild, channel, edit_msg, org_msg_id, stats_msg_id, chapter, author_name, author_avatar, color = return_data
            await self.update_embed(guild, edit_msg, org_msg_id, 'Accepted', author_name, author_avatar, '\u2705', color)
            await update_stats(guild.me, chapter, guild, channel, stats_msg_id)

    @discord.ui.button(emoji="<:nay:877951041834995742>", style=discord.ButtonStyle.red, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):  # skipcq: PYL-W0613
        """ This function is called when the red button is pressed.

        Args:
            button (discord.ui.Button): The button that was clicked
            interaction (discord.Interaction): The interaction data for the button
        """
        return_data = await self.preprocessing(interaction, 0)
        await interaction.response.defer()

        if return_data:
            guild, channel, edit_msg, org_msg_id, stats_msg_id, chapter, author_name, author_avatar, color = return_data
            await self.update_embed(guild, edit_msg, org_msg_id, 'Rejected', author_name, author_avatar, '\u274c', color)
            await update_stats(guild.me, chapter, guild, channel, stats_msg_id)

    @discord.ui.button(emoji="<:james_book:877951041293910056>", style=discord.ButtonStyle.grey, custom_id='persistent_view:grey')
    async def grey(self, button: discord.ui.Button, interaction: discord.Interaction):  # skipcq: PYL-W0613
        """ This function is called when the grey button is pressed.

        Args:
            button (discord.ui.Button): The button that was clicked
            interaction (discord.Interaction): The interaction data for the button
        """
        return_data = await self.preprocessing(interaction, 1)
        await interaction.response.defer()

        if return_data:
            guild, channel, edit_msg, org_msg_id, stats_msg_id, chapter, author_name, author_avatar, color = return_data
            await self.update_embed(guild, edit_msg, org_msg_id, 'Not Sure', author_name, author_avatar, '😐', color)
            await update_stats(guild.me, chapter, guild, channel, stats_msg_id)

    async def preprocessing(self, interaction: discord.Interaction, vote: int):
        """ Extract data from the interaction and return it
        Args:
            interaction (discord.Interaction): The interaction to extract data from
            vote (int): The vote to be sent to the database

        Returns:
            tuple: Returns a tuple containing the following data:
                    guild (discord.Guild): The guild the interaction was made in
                    channel (discord.TextChannel): The channel the interaction was made in
                    edit_msg (discord.Message): The message that was edited
                    org_msg_id (int): The message ID of the original message
                    stats_msg_id (int): The message ID of the stats message
                    chapter (int): The chapter the interaction was made in
                    author_name (str): The name of the author of the interaction
                    author_avatar (str): The avatar of the author of the interaction
                    color (str): The color of the author's avatar
        """
        edit_msg = interaction.message
        guild = interaction.guild
        user = interaction.user
        channel = interaction.channel

        config = read('config', guild)
        server_config = config['mods']
        authors_list = server_config.get('authors', [])

        if user.id not in authors_list:
            vote = {str(hash(user)): vote}
            await db.update(guild.id, 'editorial', ['votes'], [vote], {'edit_msg_id': edit_msg.id})
            return None

        document = await db.get_document(guild.id, 'editorial', {'edit_msg_id': edit_msg.id}, ['chapter'])

        org_msg_id, chapter = document.values()
        stats_msg_id = server_config['allowedEdits'].get(chapter, None)[1]
        author_name = user.nick or user.name
        author_avatar = str(user.avatar.url)

        return [guild, channel, edit_msg, org_msg_id, stats_msg_id, chapter, author_name, author_avatar, server_config['colour']]

    async def update_embed(self, guild, edit_msg, org_msg_id, status, author_name, author_avatar, status_emoji, color):
        """ Update the embed to reflect the status of the edit

        Args:
            guild (discord.Guild): The guild the message was posted in
            edit_msg (discord.Message): The message that was edited
            org_msg_id (str): The message ID of the original message
            status (str): The status of the edit
            author_name (str): The name of the user who made the edit
            author_avatar (str): The avatar of the user who made the edit
            status_emoji (str): The emoji to use for the status
            color (str): The color of the embed
        """
        data = await self.get_voteing_graph(guild.id, edit_msg.id)
        image_url = await self.get_image_url(data['image']) if data else ''

        # Yes, No, Maybe for the voting fields
        yes, no, maybe = (0, 0, 0) if not data else data['votes']

        embed_dict = edit_msg.embeds[0].to_dict()
        embed_dict['color'] = color[status]
        embed_dict['footer']['text'] = f"{author_name} Voted - {status} {status_emoji}"
        embed_dict['image'] = {'url': image_url}
        embed_dict['footer']['icon_url'] = author_avatar
        if len(embed_dict['fields']) < 7:
            embed_dict['fields'].extend([{'name': 'Yes', 'value': yes, 'inline': True},
                                         {'name': 'No', 'value': no,
                                             'inline': True},
                                         {'name': 'Maybe', 'value': maybe, 'inline': True}])
        else:
            embed_dict['fields'][4]['value'] = yes
            embed_dict['fields'][5]['value'] = no
            embed_dict['fields'][6]['value'] = maybe

        updated_embed = discord.Embed.from_dict(embed_dict)
        await edit_msg.edit(embed=updated_embed)
        await db.update(guild.id, "editorial", ['status'], [status], {'_id': org_msg_id})

    async def get_voteing_graph(self, guild_id, edit_msg_id):
        """ Returns the voting graph for the given edit_msg_id
        Args:
            guild_id (int): The guild ID
            edit_msg_id (int): The edit message ID

        Returns:
            dict: A dictionary containing the voting graph data
        """
        voting_count = await db.get_voting_count(guild_id, 'editorial', edit_msg_id)
        voting_count.pop('_id', None)
        color = ['#59d32f', '#f46e11', '#5865f2']
        voting_count_list = [[key, value, color]
                             for key, value, color in zip(voting_count.keys(), voting_count.values(), color) if value != 0]

        if not voting_count_list:
            return None

        votes = list(zip(*voting_count_list))

        # Generating the pie chart
        plt.figure(facecolor='#23272a', figsize=[15, 15], dpi=100)
        plt.pie(votes[1], labels=votes[0], colors=votes[2], autopct='%1.1f%%', labeldistance=0.6,
                pctdistance=1.25, textprops={'color': '#ffffff', 'font': 'Humor Sans', 'size': 58, 'weight': 'bold'})

        # Adding a circle in the center to make it look like a donut
        circle = plt.Circle((0, 0), 0.35, color='#23272a')
        p = plt.gcf()
        p.gca().add_artist(circle)

        # Saving the image to a BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return {'image': discord.File(img, filename='voting_graph.png'), 'votes': voting_count.values()}

    async def get_image_url(self, image: discord.File) -> str:
        """Returns the URL of the image to be posted

        Args:
            image (discord.File): The image to be posted

        Returns:
            str: URL of the image to be posted
        """
        main_guild = self.client.get_guild(834496709119705149)
        image_channel = main_guild.get_channel(878343416352751637)

        msg = await image_channel.send(file=image)
        return msg.attachments[0].url


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
    """Returns the position of the sentence in the chapter
    Args:
        guild (discord.Guild): The guild the message was posted in
        chapter (int): The chapter number
        org (str): The original sentence
    Returns:
        list: A list containing the position of the sentence in the chapter
    """
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
    """Reads the file and returns the data
    Args:
        file (str): The file to be read
        guild (discord.Guild): The guild, who's file is to be read
    Returns:
        dict: A dictionary containing the data
    """
    with open(f'Storage/{guild.id}/database/{file}.json', "r") as f:
        return json.load(f)


def save(data, file, guild: discord.Guild) -> None:
    """Saves the data to the file
    Args:
        data (dict): The data to be saved
        file (str): The file to be saved
        guild (discord.Guild): The guild, who's file is to be saved
    """
    with open(f'Storage/{guild.id}/database/{file}.json', "w") as f:
        json.dump(data, f, indent=4)


def get_prefix(guild: discord.Guild):
    """Returns the prefix for the guild
    Args:
        guild (discord.Guild): The guild to get the prefix for
    Returns:
        str: The prefix for the guild
    """
    return read('config', guild)['prefix']


def in_channel():
    """Returns the channel where the bot is supposed to interact with users
    Returns:
        bool: True if the bot is supposed to interact with users in the channel
    """

    def predicate(ctx):
        """Predicate to check if the bot is supposed to interact with users in the channel

        Args:
            ctx (command.Context): The context of the message

        Raises:
            commands.MissingPermissions: If the bot is not supposed to interact with users in the channel

        Returns:
            bool: True if the bot is supposed to interact with users in the channel else False
        """
        guild = ctx.guild
        channels = read('config', guild)['mods']['channels']
        if ctx.channel.id in channels:
            return True

        raise commands.MissingPermissions(
            ['Bot is not active in this channel!'])

    return commands.check(predicate)


def is_author():
    """Returns the predicate to check if the user is a author/mod

    Returns:
        bool: True if the user is a author/mod
    """

    def predicate(ctx):
        """Returns the predicate to check if the user is a author/mod

        Args:
            ctx (command.Context): The context of the command

        Raises:
            commands.MissingPermissions: If the user is not a author/mod

        Returns:
           bool: True if the user is a author/mod
        """
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
    """Updates the stats of the chapter

    Args:
        bot (discord.User): The bot
        chapter (int): The chapter number
        guild (discord.Guild): The guild, where chapter's stat is to be updated
        channel (discord.TextChannelConverter): The channel stat is to be updated
        msg_stats (discord.Message): The stats message
    """
    total, editors, book, accepted, rejected, notsure = await db.get_stats(guild, 'editorial', chapter)
    info = discord.Embed(color=0x815BC8, timestamp=datetime.now())
    total_reviewed = accepted + rejected + notsure

    bot_avatar = bot.avatar.url

    info.add_field(name=":hash: Number of Editors",
                   value=editors, inline=False)
    info.add_field(name=":white_check_mark: Accepted Edits",
                   value=accepted, inline=True)
    info.add_field(name=":x: Rejected Edits", value=rejected, inline=True)
    info.add_field(name=":shrug: Not Sure", value=notsure, inline=True)
    info.add_field(name=":writing_hand: Edits Reviewed",
                   value=total_reviewed, inline=True)
    info.add_field(name=":mag: Total Edits", value=total, inline=True)
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
