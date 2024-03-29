import logging
import os
import sys

from discord import client
from discord.ext import commands
from discord.ext.commands.core import is_owner

from packages.command import PersistentView, read
from packages.pretty_help import PrettyHelp

logger = logging.getLogger('discord')
logger.setLevel(20)
handler = logging.FileHandler(filename='logs/discord-main.log',
                              encoding='utf-8',
                              mode='w')
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_prefix(_, message):
    """This function gets the prefix."""
    return read('config', message.guild)['prefix']


token = os.getenv('token')


class Bot(commands.Bot):
    """This class represents the main bot object."""

    def __init__(self):
        super().__init__(command_prefix=get_prefix)
        self.persistent_views_added = False

    async def on_ready(self):
        """This method is called when the bot is ready."""
        if not self.persistent_views_added:
            self.add_view(PersistentView(self))
            self.persistent_views_added = True

        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


client = Bot()
client.help_command = PrettyHelp(color=0x635cbd, no_category='Owner Commands')

###############################################################################
#                         AREA FOR COGS                                       #
###############################################################################

if __name__ == '__main__':
    _root = os.getcwd()
    sys.path.append(f'{_root}/packages')
    print('Added packages folder to path')


@client.command()
@is_owner()
async def load(ctx, extension):
    """Loads an extension

    Args:
        ctx (discord.ext.commands.Context): The context of the command
        extension (str): The extension to load
    """
    for directory in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{directory}'):
            if f'{extension}.py' in filename:
                client.load_extension(f'cogs.{directory}.{extension}')
                await ctx.send(f'{extension} is loaded!', delete_after=20)

            else:
                pass


@client.command()
@is_owner()
async def unload(ctx, extension):
    """Unloads an extension

    Args:
        ctx (discord.ext.commands.Context): The context of the command
        extension (str): The extension to unload
    """
    for directory in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{directory}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{directory}.{extension}')
                await ctx.send(f'{extension} is unloaded!', delete_after=20)

            else:
                pass


@client.command()
@is_owner()
async def reload(ctx, extension):
    """Reloads an extension

    Args:
        ctx (discord.ext.commands.Context): The context of the command
        extension (str): The extension to reload
    """
    for directory in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{directory}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{directory}.{extension}')
                client.load_extension(f'cogs.{directory}.{extension}')
                await ctx.send(f'{extension} is reloaded!', delete_after=20)
            else:
                pass


for direct in os.listdir("./cogs"):
    for file_name in os.listdir(f'./cogs/{direct}'):
        if file_name.endswith('.py'):
            client.load_extension(f'cogs.{direct}.{file_name[:-3]}')

###############################################################################
#                         AREA FOR EVENTS                                     #
###############################################################################


@client.event
async def on_message(msg):
    """This event triggers when a message is sent in a server

    Args:
        meg (discord.Message): The message that was sent
    """
    if msg.guild:
        ctx = await client.get_context(msg)
        await client.invoke(ctx)
    else:
        pass


@client.event
async def on_error(event, *args, **kwargs):
    """This event triggers when an error occurs

    Args:
        event (str): The event that triggered the error
        args (list): The arguments of the event
        kwargs (dict): The keyword arguments of the event
    """
    logger.error(f'{event} with {args} and {kwargs}')
    # ! Implement Error Handling here
    ctx, error = args
    raise error


client.run(token)
