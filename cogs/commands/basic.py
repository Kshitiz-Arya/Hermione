from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        for i in range(5):
            await ctx.send(f'Pong! {round(self.client.latency * 1000)} ms')

    @commands.command()
    async def edit(self, ctx, chapter, org, sug, res):
        ctx.send('Your edit has been accepted')

    @commands.command()
    async def test(self, ctx, msg):
        await ctx.send('This is msg 1')


def setup(client):
    client.add_cog(Basic(client))
