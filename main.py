from discord.ext import commands
import os
import sys

from discord.ext import commands
import logging

logger = logging.getLogger('discord')
logger.setLevel(10)
handler = logging.FileHandler(filename='discord-main.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
client = commands.Bot(command_prefix='.')


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
                await ctx.send(f'{extension} is loaded!', delete_after=10)

            else:
                pass


@client.command()
async def unload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is unloaded!', delete_after=10)

            else:
                pass


@client.command()
async def reload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is reloaded!', delete_after=10)
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
    ctx = await client.get_context(meg)
    await client.invoke(ctx)

Token = 'NjQ5MjEwNjQ4Njg5MTE1MTQ5.Xd5eiA.g0w8je98YJKHl7-afYQtkFNnIhk'
client.run(Token)
