import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_ready(self):
        print('Hermione is ready for a new adventure!!!')

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.client.latency * 1000)} ms')

    @commands.command()
    async def edit(self, ctx, chapter, org, sug, res):
        await ctx.send('Your edit has been accepted')


def setup(client):
    client.add_cog(Basic(client))