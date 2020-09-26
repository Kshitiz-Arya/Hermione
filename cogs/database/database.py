from discord.ext import commands

class Database(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()

    async def add_book(self, ctx, number, chapter):
        await ctx.send('New Book has been added!')


    @commands.command()

    async def add_chapter(self, ctx, number):
        await ctx.send('New chapter has been added!')

    @commands.command()

    async def remove_chapter(self, ctx, number):
        await ctx.send('Chapter has been removed!')

    

def setup(client):
    client.add_cog(Database(client))