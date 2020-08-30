from discord.ext import commands


###############################################################################
#                         AREA FOR Functions                                  #
###############################################################################

# This function takes chapter number and return Book number
# from which the chapter belongs to.
def Book(chapter):
    # Opening File where Book information is kept.
    file = open('Chapter.txt', 'r')
    # Each line in file represents a Book
    for book, line in enumerate(file, 1):
        start, end = line.split(' ')

        if start <= chapter <= end:
            break

        if book >= 3:
            return 0    # return 0 if chapter was not found in any Book
    file.close()
    return book         # return Book number


def rank(org, chapter):
    # This code Rank each sentence according to their position in text file.
    str = open('./chapter/Chapter-{}.txt'.format(chapter), 'r')
    print('File has been opened')
    #   This is the phrase which we have to search.
    if '\n' in org:  # This is driver code
        print('This string have multiple lines')
        org = org.splitlines()

        for count, i in enumerate(str, 1):
            if org[0] in i:
                byte = i.find(org[0])
                print('({}, {})'.format(count, byte))

    else:
        print('This string have single line')
        for count, i in enumerate(str, 1):
            if org in i:
                byte = i.find(org)
                print('({}, {})'.format(count, byte))

###############################################################################
#                         AREA FOR COMMANDS                                   #
###############################################################################


class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        for i in range(5):
            await ctx.send(f'Pong! {round(self.client.latencyclient.latency * 1000)} ms')

    @commands.command()
    async def edit(self, ctx, chapter, *, edit):
        await ctx.send('Your edit has been accepted.')
        await ctx.send(f'This chapter is from Book {Book(chapter)}')

        org, sug, res = edit.split('<<')
        rank(org, chapter)

    @commands.command()
    async def test(self, ctx, msg):
        await ctx.send('This is msg 1')


def setup(client):
    client.add_cog(Basic(client))
