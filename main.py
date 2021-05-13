import json
import logging
import os
import sys

from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(20)
handler = logging.FileHandler(filename='logs/discord-main.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def read(file, guild):
    with open(f'Storage/{guild.id}/database/{file}.json', "r") as f:
        return json.load(f)


def get_prefix(client, message):
    return read('config', message.guild)['prefix']

client = commands.Bot(command_prefix=get_prefix, help_command=None)


###############################################################################
#                         AREA FOR COGS                                       #
###############################################################################


if __name__ == '__main__':
    _root = os.getcwd()
    sys.path.append(f'{_root}/packages')
    print('Added packages folder to path')


@client.command()
async def load(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is loaded!', delete_after=20)

            else:
                pass


@client.command()
async def unload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is unloaded!', delete_after=20)

            else:
                pass


@client.command()
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

with open('token.json', 'r') as file:
    Token = json.load(file)['token']
client.run(Token)
