import os
from tinydb import TinyDB, Query

# contains the code to read the database from spidey.py

# database output function
# this function will output the database to a .txt file called spider_results.txt
# the form of the output is as follows:
# Page title
# URL
# Last modification date, size of page
# Keyword1 freq1; Keyword2 freq2; Keyword3 freq3; ... ...
# Child Link1
# Child Link2 ... ...
# ——————————————————————————————
# next page

def outputDatabase(databaseFile):
    db = TinyDB(databaseFile)
    pageTable = db.table('pages')

    # if the file already exists, delete it
    if os.path.exists('spider_results.txt'):
        os.remove('spider_results.txt')

    for page in pageTable.all():
        # get data from page
        title = page['title']
        url = page['url']
        lastModified = page['lastModified']
        size = page['size']
        childLinks = page['childLinks']
        keywords = page['sortedKeywords']
        frequencies = page['sortedFrequencies']

        # format data
        output = f"{title}\n{url}\n{lastModified}, {size}\n"
        for i in range(min(10, len(keywords))):
            output += f"{keywords[i]} {frequencies[i]};\n"
        for link in range(min(10, len(childLinks))):
            output += f"{childLinks[link]}\n" 
        output += "——————————————————————————————\n"

        # if output contains any non-utf-8 characters, replace them with a question mark
        output = output.encode('utf-8', errors='replace').decode('utf-8')

        # write to file
        with open('spider_results.txt', 'a', encoding='utf-8') as f:
            f.write(output)

def main():
    # output the database to spider_results.txt, if it exists (if not, print an error message)
    if os.path.exists('spideydb.json'):
        outputDatabase('spideydb.json')
    else:
        print("Database file does not exist. Please run spidey.exe first.")

if __name__ == '__main__':
    main()
