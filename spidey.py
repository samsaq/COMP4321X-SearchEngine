import requests
import string
from tinydb import TinyDB, Query
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
import sys
import os

# creating a web scraper with beautifulsoup & requests & tinydb to get X pages from the url 
# and index the data before storing it in a database

# the test url
testUrl = 'https://cse.hkust.edu.hk/'

# the number of pages to scrape (for testing)
pagesCount = 2

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

# defining the schema

# from each page, we need to get the page title, page url, last modification date, size of page (in characters)
# and the first 10 links on the page, as well as top 10 keywords along with their frequency

# the function to recursively scrape the pages
def scrape(startUrl, pagesCount):
    # base case
    if pagesCount == 0:
        return
    else:
        # get page
        page = requests.get(startUrl)
        # parse page
        soup = BeautifulSoup(page.content, 'html.parser')
        # get title
        title = soup.title.string
        # get url
        curUrl = page.url
        # get last modified date
        lastModified = soup.find('p', class_= 'copyright').child.text
        # get size of page
        size = len(page.text)
        # get first 10 links
        links = soup.find_all('a', limit=10)
        # get top 10 keywords
        # this means getting all text from the page, removing punctuation, 
        # stemming with porter's, ignoring stopwords, 
        # and then counting the frequency of each word
        # we will use a dictionary to store the words and their frequencies

        # get all text from the page
        text = soup.get_text()
        # remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # split into words
        words = text.split()
        # stem with porter's
        # for now, we will use NTLK's porter stemmer (may change later if not allowed)
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
        top10Keywords = sortedWordFreq[:10]
        top10Frequencies = []
        for i in range(10):
            top10Frequencies.append(sortedWordFreq[i][1])
        
        # insert into database
        pages_table.insert({'title': title, 'url': curUrl, 'lastModified': lastModified, 'size': size, 'links': links, 'top10Keywords': top10Keywords, 'top10Frequencies': top10Frequencies})

        # decrement pagesCount
        pagesCount -= 1

        # move on to the next page to keep scraping until pagesCount == 0
        # we are doing so in a breadth-first manner
        # we will use a queue to keep track of the pages to scrape


        # temp note - make sure to implement a parent page field in the database, the first page will have a parent page of None