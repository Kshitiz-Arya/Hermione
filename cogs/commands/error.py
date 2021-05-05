import discord
from discord.ext import commands
import json
import traceback
import sys

def read(file):
    with open(f'{file}.json', 'r') as f:
        return json.load(f)

def save(data, file):
    with open(f'{file}.json', 'w') as f:
        json.dump(data, f, indent=4)

print('Connected to error module!')
class Error_control(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        command = ctx.command
        print('Ignoring exception in command {}:'.format(str(command)), file=sys.stderr)
        trace = traceback.format_exception(type(error), error, error.__traceback__)

        err = read('error-log')
        err.append({str(type(error)): {str(ctx.command): [str(error.args), trace]}})
        save(err, 'error-log')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('You need to provide proper arguments for command to work.', delete_after=30)
            return
        
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the permission to use this command!", delete_after=30)

        if isinstance(error, commands.CommandInvokeError):
            err = error.__cause__
            if isinstance(err, discord.HTTPException):
                code = err.code
                if code == 10014 and str(command) == 'setEmojis':
                    await ctx.send('Please enter valid emojis!', delete_after=30)
                elif code == 50035:
                    pass
            
def setup(client):
    client.add_cog(Error_control(client))