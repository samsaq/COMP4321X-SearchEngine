import sys
import os
import requests
import string
from tinydb import TinyDB, Query
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import deque

# creating a web scraper with beautifulsoup & requests & tinydb to get X pages from the url 
# and index the data before storing it in a database

debug = True

# the visited set
visited = set()

# inverted index
invertedIndex = {}

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())

# remove the database file if it already exists
try:
    os.remove('spideydb.json')
except OSError:
    pass

# defining the database
db = TinyDB('spideydb.json')
pages_table = db.table('pages')

# function to update the inverted index
# this takes in the list of words from a page
# updates the inverted index to contain for each word:
# a list of urls that contain that word
# the frequency of that word in that url (document)
# the positions of that word in that url (document)
def updateInvertedIndex(words, url):
    for i, word in enumerate(words):
        if word not in invertedIndex:
            # if the word is not in the inverted index, add it (and the url for the new document)
            invertedIndex[word] = {url: {"frequency": 1, "positions": [i]}}
        else:
            # if the word is in the inverted index, but the document is not, add the document
            if url not in invertedIndex[word]:
                invertedIndex[word][url] = {"frequency": 1, "positions": [i]}
            else:
                # if the word and the document are both in the inverted index, update the frequency and positions
                invertedIndex[word][url]["frequency"] += 1
                invertedIndex[word][url]["positions"].append(i)
    return invertedIndex
    
# stow the inverted index into the tinydb database (double check this function later)
def stowInvertedIndex():
    invertedIndex_table = db.table('invertedIndex')
    invertedIndex_table.insert(invertedIndex)

# from each page, we need to get the page title, page url, last modification date, size of page (in characters)
# and the first 10 links on the page, as well as top 10 keywords along with their frequency

# the function to recursively scrape the pages
def scrape(curUrl, targetVisited, parentUrl):
    # base case
    if curUrl in visited:
        return
    elif len(visited) >= targetVisited:
        return
    else:
        page = requests.get(curUrl)
        # parse page
        soup = BeautifulSoup(page.content, 'html.parser')
        title = soup.title.string
        
        # get last modified date from http header, if it doesn't exist use the date field from the html
        if 'Last-Modified' in page.headers:
            lastModified = page.headers['Last-Modified']
        else:
            lastModified = page.headers['Date']

        # get the size as the content length from the http header, if it doesn't exist use the length of the html
        if 'Content-Length' in page.headers:
            size = int(page.headers['Content-Length'])
        else:
            size = len(page.content)

        # get first 100 links (we have some limiters to make sure we don't get too many links)
        links = []
        for link in soup.find_all('a', limit=200):
            href = link.get('href')
            if href is not None and href.startswith('http'):
                links.append(href)
            if len(links) >= 100:
                break
        
        # get first 10 links
        first10Links = []
        for i in range(len(links)):
            if len(first10Links) >= 10:
                break
            first10Links.append(links[i])
        # get top 10 keywords
        # this means getting all text from the page, removing punctuation, 
        # stemming with porter's, ignoring stopwords, 
        # and then counting the frequency of each word
        # we will use a dictionary to store the words and their frequencies

        text = soup.get_text()
        # remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.lower().split()
        # stem with porter's
        ps = PorterStemmer()
        stemmedWords = []
        for word in words:
            stemmedWords.append(ps.stem(word))
        # remove stopwords
        filteredWords = []
        for word in stemmedWords:
            if word not in stopwords:
                filteredWords.append(word)
        # count frequency of each word
        wordFreq = {}
        for word in filteredWords:
            if word in wordFreq:
                wordFreq[word] += 1
            else:
                wordFreq[word] = 1
        # sort the dictionary by frequency
        sortedWordFreq = sorted(wordFreq.items(), key=lambda x: x[1], reverse=True)
        # get top 10 keywords and the top 10 frequencies
        top10Keywords = []
        for i in range(10):
            top10Keywords.append(sortedWordFreq[i][0])
        top10Frequencies = []
        for i in range(10):
            top10Frequencies.append(sortedWordFreq[i][1])
        
        # update the inverted index
        invertedIndex = updateInvertedIndex(filteredWords, curUrl)

        # insert into database
        pages_table.insert({'title': title, 'url': curUrl, 'lastModified': lastModified, 'size': size, 'childLinks': first10Links, 'top10Keywords': top10Keywords, 'top10Frequencies': top10Frequencies, 'parentPage': parentUrl ,'text': text})

        # add to visited set
        visited.add(curUrl)

        # move on to the next page to keep scraping until we reach the target number of pages or we run out of pages to scrape
        # we are doing so in a breadth-first manner
        # we will use a queue to keep track of the pages to scrape
        # we will use a set to keep track of the pages we have already visited (faster than checking the database)

        # create a queue of links in breadth-first order to scrape
        bfsQueue = deque(links)

        # start scraping
        while bfsQueue:
            nextLink = bfsQueue.popleft()
            if nextLink not in visited:
                scrape(nextLink, targetVisited, curUrl)
        
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
        top10Keywords = page['top10Keywords']
        top10Frequencies = page['top10Frequencies']

        # format data
        output = f"{title}\n{url}\n{lastModified}, {size}\n"
        for i in range(len(top10Keywords)):
            output += f"{top10Keywords[i]} {top10Frequencies[i]};\n"
        for link in childLinks:
            output += f"{link}\n"
        output += "——————————————————————————————\n"

        # write to file
        with open('spider_results.txt', 'a') as f:
            f.write(output)

# function execution
#seedUrl = sys.argv[1]
#targetVisited = int(sys.argv[2])
#scrape(seedUrl, targetVisited, None)

# debugging execution
if debug:
    seedUrl = 'https://cse.hkust.edu.hk/'
    targetVisited = 10
    scrape(seedUrl, targetVisited, None)
    outputDatabase('spideydb.json')