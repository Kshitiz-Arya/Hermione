import os
# This function takes chapter number and return Book number
# from which the chapter belongs to.
def Book(chapter, guild):
    # Opening File where Book information is kept.
    file = open(f'Chapter.txt', 'r')
    # Each line in file represents a Book
    for book, line in enumerate(file, 1):
        start, end = line.split(' ')

        if start <= chapter <= end:
            break

        if book >= 3:
            return 0    # return 0 if chapter was not found in any Book
    file.close()
    return book         # return Book number


def ranking(guild, chapter, org):
    # This code Rank each sentence according to their position in text file.
    str = open(f'./Storage/{guild.name} - {guild.id}/books/Chapter-{chapter}.txt', 'r')
    print('File has been opened')
    #   This is the phrase which we have to search.
    if '\n' in org:  # This is driver code
        print('This string have multiple lines')
        org = org.splitlines()

        for count, i in enumerate(str, 1):
            if org[0] in i:
                byte = i.find(org[0])
                return f'{count}: {byte}'

    else:
        print('This string have single line')
        for count, i in enumerate(str, 1):
            if org in i:
                byte = i.find(org)
                return f'{count}: {byte}'