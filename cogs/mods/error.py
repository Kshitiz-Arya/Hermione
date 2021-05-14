import discord
from discord.ext import commands
import json
import traceback
import sys
from datetime import datetime
import logging

logger = logging.getLogger('discord')
logger.setLevel(20)
handler = logging.FileHandler(filename='logs/discord-main.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def read(file):
    with open(f'{file}.json', 'r') as f:
        return json.load(f)

def save(data, file):
    with open(f'{file}.json', 'w') as f:
        json.dump(data, f, indent=4)

async def send(self, ctx, error):
    main_guild = self.client.get_guild(834496709119705149)
    err_channel = main_guild.get_channel(840150395748745217)
    trace = traceback.format_exception(type(error), error, error.__traceback__)
    length = len(str(trace))
    print(length)
    error_embed = discord.Embed(color=0x4500ff, timestamp=datetime.now())
    error_embed.set_author(name='Hermione')
    error_embed.set_thumbnail(url=self.client.user.avatar_url)
    error_embed.add_field(name='Command Text', value=ctx.message.content, inline=False)
    error_embed.add_field(name='Error', value=str(type(error)), inline=False)
    error_embed.add_field(name='Arguments', value=f"{''.join(error.args)}", inline=False)
    error_embed.set_footer(text=f'Command - {str(ctx.command)} | Guild - {ctx.guild.name}, Channel - {ctx.channel.name}')
    if length < 1000:
        error_embed.add_field(name='Traceback', value=f'```python\n{"".join(trace)}```', inline=False)
    else:
        error_embed2 = discord.Embed(color=0x4500ff, description=f'```{"".join(trace)}```' , timestamp=datetime.now())
        error_embed2.set_author(name='Traceback')
        msg = await err_channel.send(embed=error_embed)
        await msg.reply(f'```python\n{"".join(trace)}```')
        return
    await err_channel.send(embed=error_embed)

class Error_control(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        command = ctx.command
        
        if isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send('You need to provide proper arguments for command to work.', delete_after=30)

            elif isinstance(error, commands.BadArgument):
                await ctx.send('Invalid Argument Type!')
            else:
                send(self, ctx, error)
            
        elif isinstance(error, commands.CheckFailure):
                await ctx.send("You don't have the permission to use this command!", delete_after=30)

        elif isinstance(error, commands.CommandInvokeError):
                err = error.__cause__
                if isinstance(err, discord.HTTPException):
                    code = err.code
                    if code == 10014 and str(command) == 'setEmojis':
                        await ctx.send('Please enter valid emojis!', delete_after=30)
                    elif code == 50035:
                        pass
                    elif code == 50006:
                        if command.name in ('editors', 'allEditors'):
                            await ctx.send('No Editors found')
                        else:
                            send(self, ctx, err)
                    else:
                        await send(self, ctx, error)
                
                elif isinstance(err, IndexError):

                    if command.name in ('delAuthor', 'addAuthor') :
                        await ctx.send("You need to mention the Authors name for this command to work!", delete_after=20)
                    else:
                        await send(self, ctx, error)
                
                elif isinstance(err, TypeError):
                    print('Type Error')
                else:
                    await send(self, ctx, error)

        elif isinstance(error, commands.CommandNotFound):
            logger.error('Command was not found!')
            pass
        
        else:  
            print('Ignoring exception in command {}:'.format(str(command)), file=sys.stderr)
            trace = traceback.format_exception(type(error), error, error.__traceback__)

            err = read('error-log')
            err.append({str(type(error)): {str(ctx.command): [str(error.args), trace]}})
            save(err, 'error-log')

            await send(self, ctx, error)


           

def setup(client):
    client.add_cog(Error_control(client))