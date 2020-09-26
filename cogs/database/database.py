import discord
from discord.ext import commands
import json
import os

class Database(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()

    async def add_book(self, ctx, number, chapter, end=None):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        # for some reason the variable, chapter, is not evaluating in this command.
        # This is just a work around.
        _ = chapter
        print(_)
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)
        if end:
            book[str(number)] = {'start':int(chapter), 'end':int(end)}
        else:
            book[str(number)] = {'start':int(_), 'end':int(_)}

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)

        await ctx.send('New Book has been added!')


    @commands.command()

    async def add_chapter(self, ctx, number, chapter):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book[str(number)]['end'] = int(chapter)

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)

        await ctx.send('New chapter has been added!')


    @commands.command()

    async def remove_book(self, ctx, number):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book.pop(str(number))

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)
        await ctx.send(f'Book {number} has been removed!')


    @commands.command()

    async def remove_chapter(self, ctx, book_n):
        guild = ctx.guild
        cwd = os.getcwd() + f'/Storage/{guild.name} - {guild.id}/books'
        with open(f'{cwd}/books.json', 'r') as file:
            book = json.load(file)

        book[str(book_n)]['end'] -= 1

        with open(f'{cwd}/books.json', 'w') as file:
            json.dump(book, file, indent=4)
        await ctx.send('Chapter has been removed!')


def setup(client):
    client.add_cog(Database(client))
