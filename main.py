from cogs.mods.error import send
import json
import logging
import os
import sys
from dotenv import load_dotenv

from discord.ext import commands
from discord.ext.commands.core import check, is_owner
from packages.pretty_help import PrettyHelp

logger = logging.getLogger('discord')
logger.setLevel(20)
handler = logging.FileHandler(filename='logs/discord-main.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def read(file, guild):
    with open(f'Storage/{guild.id}/database/{file}.json', "r") as f:
        return json.load(f)


def get_prefix(_, message):
    return read('config', message.guild)['prefix']

load_dotenv()
token = os.getenv('token')
# menu = DefaultMenu(page_left="\U0001F44D", page_right="👎", remove=":classical_building:", active_time=5)

client = commands.Bot(command_prefix=get_prefix, case_insensitive=True, strip_after_prefix=True)
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
async def restart(ctx):

    await ctx.bot.close()
    await ctx.bot.login(token, bot=True)

@client.command()
@is_owner()
async def load(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is loaded!', delete_after=20)

            else:
                pass


@client.command()
@is_owner()
async def unload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is unloaded!', delete_after=20)

            else:
                pass


@client.command()
@is_owner()
async def reload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is reloaded!', delete_after=20)
            else:
                pass


for dir in os.listdir("./cogs"):
    for filename in os.listdir(f'./cogs/{dir}'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{dir}.{filename[:-3]}')


###############################################################################
#                         AREA FOR EVENTS                                     #
###############################################################################


@client.event
async def on_ready():
    print('Hermione is ready for a new adventure!!!')


@client.event
async def on_message(meg):
    if meg.guild:
        ctx = await client.get_context(meg) 
        await client.invoke(ctx)
    else:
        pass

@client.event
async def on_error(event, *args, **kwargs):
    #! Implement Error Handling here
    ctx, error = args
    raise error
    pass
    
client.run(token)
