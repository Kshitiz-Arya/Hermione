from discord.ext import commands
import os

client = commands.Bot(command_prefix='.')


@client.command()
async def load(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is loaded!')

            else:
                pass


@client.command()
async def unload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is unloaded!')

            else:
                pass


@client.command()
async def reload(ctx, extension):
    for dir in os.listdir('./cogs'):
        for filename in os.listdir(f'./cogs/{dir}'):
            if f'{extension}.py' in filename:
                client.unload_extension(f'cogs.{dir}.{extension}')
                client.load_extension(f'cogs.{dir}.{extension}')
                await ctx.send(f'{extension} is reloaded!')
            else:
                pass


for dir in os.listdir("./cogs"):
    for filename in os.listdir(f'./cogs/{dir}'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{dir}.{filename[:-3]}')


@client.event
async def on_ready():
    print('Hermione is ready for a new adventure!!!')


Token = 'NjQ5MjEwNjQ4Njg5MTE1MTQ5.Xd5eiA.g0w8je98YJKHl7-afYQtkFNnIhk'
client.run(Token)
