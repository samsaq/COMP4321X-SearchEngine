import sys, os, requests, string, sqlite3, urllib3, re, hashlib, certifi
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import deque, Counter
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, quote, parse_qs
from spideyTest import outputDatabase

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

# function to canonicalize urls
def canonicalize(url):
    #Canonicalizes a URL by performing the following operations:
    # 1. Normalizes the scheme and hostname to lower case.
    # 2. Removes the default port for the scheme (e.g. port 80 for HTTP).
    # 3. Removes any trailing slashes from the path.
    # 4. Removes any URL fragments.
    # 5. Removes any query parameters that are known not to affect the content of the page.
    # 6. Decodes any percent-encoded characters in the URL.
    # 7. Removes duplicate slashes from the path.
    # 8. Sorts the query parameters by name.
    parsed_url = urlparse(url)
    # Normalize scheme and hostname to lower case
    parsed_url = parsed_url._replace(scheme=parsed_url.scheme.lower())
    parsed_url = parsed_url._replace(netloc=parsed_url.netloc.lower())
    # Remove default ports (these are the most common ones)
    default_ports = {
        'http': 80,
        'https': 443,
        'ftp': 21,
        'ftps': 990,
        'ssh': 22,
        'telnet': 23,
        'smtp': 25,
        'pop3': 110,
        'imap': 143,
        'ldap': 389,
        'ldaps': 636,
    }
    if parsed_url.port == default_ports.get(parsed_url.scheme):
        parsed_url = parsed_url._replace(netloc=parsed_url.hostname)
        parsed_url = parsed_url._replace(port=None)
    # Remove trailing slash from path
    if parsed_url.path.endswith('/') and len(parsed_url.path) > 1:
        parsed_url = parsed_url._replace(path=parsed_url.path.rstrip('/'))
    # Remove URL fragments
    parsed_url = parsed_url._replace(fragment='')
    # Remove query parameters that do not affect page content (these ones should just be used for tracking)
    query_params = []
    for param, value in parse_qs(parsed_url.query, keep_blank_values=True).items():
        if param.lower() in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'ref']:
            continue
        for v in value:
            query_params.append((param, v))
    if query_params:
        sorted_params = sorted(query_params, key=lambda x: x[0])
        encoded_params = []
        for param, value in sorted_params:
            encoded_params.append((quote(param, safe=''), quote(value, safe='')))
        parsed_url = parsed_url._replace(query=urlencode(encoded_params))
    else:
        parsed_url = parsed_url._replace(query='')
    # Decode percent-encoded characters
    parsed_url = parsed_url._replace(path=quote(parsed_url.path, safe='/'))
    # Remove duplicate slashes from path
    parsed_url = parsed_url._replace(path='/'.join(filter(None, parsed_url.path.split('/'))))
    return urlunparse(parsed_url)

# function to try and get the page, skipping if it fails due to verification or timeout, exits the program if we've run out of links early
def getPage(curUrl, bfsQueue):
    try:
        # get the page
        page = requests.get(curUrl, verify=certifi.where(), timeout=5)
        return page
    except Exception as e:
        # if there's nothing in the queue, except the code and end the program
        if len(bfsQueue) == 0:
            print("No more links to visit, as the last one has excepted. Exiting...")
            exit()
        else:
            # if there is something else in the queue, move on to that
            nextLink = bfsQueue.popleft()
            while nextLink is None or nextLink in visited:
                if len(bfsQueue) == 0:
                    print("No more links to visit, as the last one has excepted. Exiting...")
                    exit()
                nextLink = bfsQueue.popleft()
            return getPage(nextLink, bfsQueue)

# from each page, we need to get the page title, page url, last modification date, size of page (in characters)
# and the first 10 links on the page, as well as top 10 keywords along with their frequency

# the function to recursively scrape the pages
def scrape(curUrl, targetVisited, parentUrl, bfsQueue):

    curUrl = canonicalize(curUrl)

    # base case
    if curUrl in visited:
        return
    elif len(visited) >= targetVisited:
        return
    else:
        # get the page
        page = getPage(curUrl, bfsQueue)
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
