import sys, os, requests, string, sqlite3
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import deque, Counter
from spideyTest import outputDatabase
import urllib3, re, hashlib

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# creating a web scraper with beautifulsoup & requests & tinydb to get X pages from the url 
# and index the data before storing it in a database

debug = True

# the visited set
visited = set()

# inverted index
invertedIndex = {}

# the BFS queue initialization
bfsQueue = deque()

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())

# remove the database file if it already exists
try:
    os.remove('spidey.sqlite')
except OSError:
    pass

# adding an sqlite3 database
conn = sqlite3.connect('spidey.sqlite')
cur = conn.cursor()

# creating the page table
cur.execute('''CREATE TABLE Page
             (page_id INTEGER PRIMARY KEY,
              url TEXT,
              title TEXT,
              content TEXT,
              raw_html TEXT,
              last_modified TEXT,
              size INTEGER,
              parent_url TEXT,
              hash TEXT
              )''')

# creating a link table for child links
cur.execute('''CREATE TABLE Link
                (link_id INTEGER PRIMARY KEY,
                page_id INTEGER,
                child_url TEXT,
                Foreign Key(page_id) REFERENCES Page(page_id)
                )''')

# creating a term table for keywords
cur.execute('''CREATE TABLE Term
                (term_id INTEGER PRIMARY KEY,
                term TEXT)''')

# creating a term frequency table for keywords (we aren't worried about frequency in titles)
cur.execute('''CREATE TABLE TermFrequency
                (page_id INTEGER,
                term_id INTEGER,
                frequency INTEGER,
                Foreign Key(page_id) REFERENCES Page(page_id),
                Foreign Key(term_id) REFERENCES Term(term_id)
                )''')

# creating a term position table for titles
cur.execute('''CREATE TABLE TitleTermPosition
                (page_id INTEGER,
                term_id INTEGER,
                position_list TEXT,
                Foreign Key(page_id) REFERENCES Page(page_id),
                Foreign Key(term_id) REFERENCES Term(term_id)
                )''')

# creating a term position table for content
cur.execute('''CREATE TABLE ContentTermPosition
                (page_id INTEGER,
                term_id INTEGER,
                position_list TEXT,
                Foreign Key(page_id) REFERENCES Page(page_id),
                Foreign Key(term_id) REFERENCES Term(term_id)
                )''')

# creating an index table for the titles
cur.execute('''CREATE TABLE TitleIndex
                (term_id INTEGER,
                page_id INTEGER,
                Foreign Key(page_id) REFERENCES Page(page_id),
                Foreign Key(term_id) REFERENCES Term(term_id)
                )''')

# creating an index table for the content
cur.execute('''CREATE TABLE ContentIndex
                (term_id INTEGER,
                page_id INTEGER,
                Foreign Key(page_id) REFERENCES Page(page_id),
                Foreign Key(term_id) REFERENCES Term(term_id)
                )''')

conn.commit()


# unsure if we'll need all of these, but they'll be there just in case

# function to hash pages for later comparison
def hashPage(soup):
    # Remove unwanted elements
    for element in soup(["script", "style", "meta"]):
        element.decompose()
    # Extract the text content of the page
    page_content = soup.get_text()

    page_content = ' '.join(page_content.split())
    # hash the raw html
    return hashlib.sha256(page_content.encode('utf-8')).hexdigest()

# from each page, we need to get the page title, page url, last modification date, size of page (in characters)
# and the first 10 links on the page, as well as top 10 keywords along with their frequency

# the function to recursively scrape the pages
def scrape(curUrl, targetVisited, parentUrl, bfsQueue):
    # base case
    if curUrl in visited:
        return
    elif len(visited) >= targetVisited:
        return
    else:
        page = requests.get(curUrl, verify=False)
        # parse page
        soup = BeautifulSoup(page.content, 'html.parser')
        if soup.title is not None and soup.title.string.strip() != "":
            title = soup.title.string
        else:
            title = "No Title Given"
        rawHTML = page.text
        hash = hashPage(soup)
        
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

        text = soup.get_text()

        # Tokenize document content and title
        titleTokens = re.findall(r'\b\w+\b', title.lower())
        contentTokens = re.findall(r'\b\w+\b', text.lower())
        
        # remove stopwords from both title and content
        titleTokens = [token for token in titleTokens if token not in stopwords]
        contentTokens = [token for token in contentTokens if token not in stopwords]

        # stem with porter's
        ps = PorterStemmer()
        titleStems = [ps.stem(token) for token in titleTokens]
        contentStems = [ps.stem(token) for token in contentTokens]

        # count frequency of each word, making a list of tuples
        contentFreq = Counter(contentStems).most_common()
        titleFreq = Counter(titleStems).most_common()

        # inserting the page into the Page table
        cur.execute('''INSERT INTO Page (url, title, content, raw_html, last_modified, size, parent_url, hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (curUrl, title, text, rawHTML, lastModified, size, parentUrl, hash))
        pageID = cur.lastrowid

        # inserting the child links into the Link table
        for link in links:
            cur.execute('''INSERT INTO Link (page_id, child_url) VALUES (?, ?)''', (pageID, link))
        
        # inserting into the term table, if the term is already in the table, it will be skipped
        for term in set(titleStems + contentStems):
            cur.execute('''INSERT OR IGNORE INTO Term (term) VALUES (?)''', (term,))

        # inserting into the term frequency table
        for stem, freq in contentFreq:
            termID = cur.execute('''SELECT term_id FROM Term WHERE term = ?''', (stem,)).fetchone()[0]
            cur.execute("INSERT INTO TermFrequency (page_id, term_id, frequency) VALUES (?, ?, ?)", (pageID, termID, freq))

        # inserting into the ContentTermPosition table
        for stem, freq in contentFreq:
            termID = cur.execute('''SELECT term_id FROM Term WHERE term = ?''', (stem,)).fetchone()[0]
            positions = [i for i, t in enumerate(contentStems) if t == stem]
            positionsList = ','.join(str(pos) for pos in positions) # the list in the database is a string of comma separated integers
            cur.execute("INSERT INTO ContentTermPosition (page_id, term_id, position_list) VALUES (?, ?, ?)", (pageID, termID, positionsList))

        # inserting into the TitleTermPosition table
        for stem, freq in titleFreq:
            termID = cur.execute('''SELECT term_id FROM Term WHERE term = ?''', (stem,)).fetchone()[0]
            positions = [i for i, t in enumerate(titleStems) if t == stem]
            positionsList = ','.join(str(pos) for pos in positions) # the list in the database is a string of comma separated integers
            cur.execute("INSERT INTO TitleTermPosition (page_id, term_id, position_list) VALUES (?, ?, ?)", (pageID, termID, positionsList))
        
        # inserting into the ContentIndex table
        for stem, freq in contentFreq:
            termID = cur.execute('''SELECT term_id FROM Term WHERE term = ?''', (stem,)).fetchone()[0]
            cur.execute("INSERT INTO ContentIndex (term_id, page_id) VALUES (?, ?)", (termID, pageID))
        
        # inserting into the TitleIndex table
        for stem, freq in titleFreq:
            termID = cur.execute('''SELECT term_id FROM Term WHERE term = ?''', (stem,)).fetchone()[0]
            cur.execute("INSERT INTO TitleIndex (term_id, page_id) VALUES (?, ?)", (termID, pageID))

        # commit changes to the database
        conn.commit()

        # add to visited set
        visited.add(curUrl)

        # move on to the next page to keep scraping until we reach the target number of pages or we run out of pages to scrape
        # we are doing so in a breadth-first manner
        # we will use a queue to keep track of the pages to scrape
        # we will use a set to keep track of the pages we have already visited (faster than checking the database)

        bfsQueue.extend(link for link in links if link not in visited)

        # start scraping
        while bfsQueue:
            nextLink = bfsQueue.popleft()
            if nextLink not in visited and not None:
                scrape(nextLink, targetVisited, curUrl, bfsQueue)

# debugging execution
if debug:
    seedUrl = 'https://cse.hkust.edu.hk/'
    targetVisited = 30
    scrape(seedUrl, targetVisited, None, bfsQueue)
    cur.close()
    conn.close()
    outputDatabase()
else: # command line execution for spideyTest.py & TAs
    seedUrl = sys.argv[1]
    targetVisited = int(sys.argv[2])
    scrape(seedUrl, targetVisited, None, bfsQueue)
    cur.close()
    conn.close()
    outputDatabase()
