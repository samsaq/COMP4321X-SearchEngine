import sys
import os
import sqlite3
import re
import hashlib
from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import deque, Counter
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, quote, parse_qs
from spideyTest import outputDatabase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask

# creating a web scraper with selenium, beautifulsoup, and sqlite to get X pages from the given root url into a database setup for later searching

debug = True

if (debug):
    os.chdir('Spidey')

# initializations
app = Flask(__name__)

# detect what operating system is being used, and set the path to the chromedriver accordingly
if sys.platform == 'win32':
    driverPath = './web_Drivers/chromedriver_win32/chromedriver.exe'
# if using macOS, we need to determine if arm or not
elif sys.platform == 'darwin':
    machine = platform.machine()
    if "arm" in machine.lower():
        driverPath = './web_Drivers/chromedriver_mac_arm64/chromedriver'
    driverPath = '.web_Drivers/chromedriver_mac64/chromedriver'
elif sys.platform == 'linux':
    driverPath = './web_Drivers/chromedriver_linux64/chromedriver'
else:
    raise ValueError("Unsupported OS")

# setting chrome options
options = Options()
service = Service(driverPath)

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())

# create the database engine
engine = create_engine('spidey.db', echo=False) # use echo for debugging later - it will print out all the SQL commands being executed
# create a declarative base for SQLAlchemy models
Base = declarative_base()

# defining database models:
# define the Page model
class Page(Base):
    __tablename__ = 'Page'

    page_id = Column(Integer, primary_key=True)
    url = Column(Text)
    title = Column(Text)
    content = Column(Text)
    raw_html = Column(Text)
    last_modified = Column(Text)
    size = Column(Integer)
    parent_page_id = Column(Integer, ForeignKey('Page.page_id'))
    hash = Column(Text)

    parent_page = relationship("Page", remote_side=[page_id])

# define the ParentLink model
class ParentLink(Base):
    __tablename__ = 'ParentLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    parent_page_id = Column(Integer, ForeignKey('Page.page_id'))

    page = relationship("Page", foreign_keys=[page_id])
    parent_page = relationship("Page", foreign_keys=[parent_page_id])

# define the ChildLink model
class ChildLink(Base):
    __tablename__ = 'ChildLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_url = Column(Text)

    page = relationship("Page", foreign_keys=[page_id])
    child_page = relationship("Page", foreign_keys=[child_page_id])

# define the Term model
class Term(Base):
    __tablename__ = 'Term'

    term_id = Column(Integer, primary_key=True)
    term = Column(Text)

# define the TermFrequency model
class TermFrequency(Base):
    __tablename__ = 'TermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = relationship("Page")
    term = relationship("Term")

# define the TitleTermPosition model
class TitleTermPosition(Base):
    __tablename__ = 'TitleTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = relationship("Page")
    term = relationship("Term")

# define the ContentTermPosition model
class ContentTermPosition(Base):
    __tablename__ = 'ContentTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = relationship("Page")
    term = relationship("Term")

# define the TitleIndex model
class TitleIndex(Base):
    __tablename__ = 'TitleIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = relationship("Term")
    page = relationship("Page")

# define the ContentIndex model
class ContentIndex(Base):
    __tablename__ = 'ContentIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = relationship("Term")
    page = relationship("Page")

# function for API call to remake the database based off of the given parameters
def triggerScraping(seedUrl, targetVisited):
    visited = set()
    bfsQueue = deque()
    driver = webdriver.Chrome(service=service, options=options)
    # remove to the database file if it already exists
    try:
        os.remove('spidey.db')
    except OSError:
        pass

    # adding an sqlite3 sqlachemy database
    sessionFactory = makeAlchemy(engine)
    scrapeSession = sessionFactory()
    scrape(seedUrl, targetVisited, None, bfsQueue, visited, driver, scrapeSession)
    
    # close the session and driver
    scrapeSession.close()
    driver.close()

# function to take an exisitng database & precalculate the vectors via the TF-IDF algorithm
# it will add the vectors to the database as well
def preConstructVectors(sessionFactory):
    session = sessionFactory()
    pass

# function to take database and format output for API JSON return, in response to queries
# we might add more parameters to this function later
# Incomplete for now
def reformatData():
    pass

# creating an sqlachemcy database
def makeAlchemy(engine):
    # create the session (replaces the connection and cursor)
    sessionFactory = sessionmaker(bind=engine)

    # create the tables
    Base.metadata.create_all(engine)

    # return the sessionFactory - this is what we will use to make sessions to interact with the database
    return sessionFactory

# function to hash pages for later comparison (Reserved for page to page in database comparison in the future, like for page updates)
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
    # Canonicalizes a URL by performing the following operations:
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
            encoded_params.append(
                (quote(param, safe=''), quote(value, safe='')))
        parsed_url = parsed_url._replace(query=urlencode(encoded_params))
    else:
        parsed_url = parsed_url._replace(query='')
    # Decode percent-encoded characters
    parsed_url = parsed_url._replace(path=quote(parsed_url.path, safe='/'))
    # Remove duplicate slashes from path
    parsed_url = parsed_url._replace(
        path='/'.join(filter(None, parsed_url.path.split('/'))))
    return urlunparse(parsed_url)

# function to try and get the page, skipping if it fails due to verification or timeout, exits the program if we've run out of links early


def getPage(curUrl, bfsQueue, visited, driver):
    try:
        # get the page with selenium, with a 10 second timeout
        driver.get(curUrl)
        return
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
                    print(
                        "No more links to visit, as the last one has excepted. Exiting...")
                    exit()
                nextLink = bfsQueue.popleft()
            return getPage(nextLink, bfsQueue, visited, driver)

# from each page, we need to get the page title, page url, last modification date, size of page (in characters)
# and the first 10 links on the page, as well as top 10 keywords along with their frequency

# the function to recursively scrape the pages


def scrape(curUrl, targetVisited, parentID, bfsQueue, visited, driver, session):

    curUrl = canonicalize(curUrl)

    # base case
    if curUrl in visited:
        # if the curUrl has already been visited, the parentURL should be added to the parent table for this pageID, as found from the curUrl
        visitPageID = session.query(Page).filter_by(url=curUrl).first().page_id
        newParentLink = ParentLink(page_id=visitPageID, parent_page_id=parentID)
        session.merge(newParentLink) # if this doesn't work as INSERT OR IGNORE, swap to insert + .onconflict_do_nothing()
        return
    elif len(visited) >= targetVisited:
        return
    else:
        # get the page
        getPage(curUrl, bfsQueue, visited, driver)
        # parse page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        if soup.title is not None and soup.title.string.strip() != "":
            title = soup.title.string
        else:
            title = "No Title Given"
        rawHTML = driver.page_source
        hash = hashPage(soup)

        # get last modified date by
        lastModified = driver.execute_script("return document.lastModified")
        if lastModified is None:
            lastModified = driver.execute_script("return document.date")
            if lastModified is None:
                lastModified = "Unkown"

        # get the size of the page by getting the length of the raw html
        size = len(rawHTML)

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
        titleTokens = [
            token for token in titleTokens if token not in stopwords]
        contentTokens = [
            token for token in contentTokens if token not in stopwords]

        # stem with porter's
        ps = PorterStemmer()
        titleStems = [ps.stem(token) for token in titleTokens]
        contentStems = [ps.stem(token) for token in contentTokens]

        # count frequency of each word, making a list of tuples
        contentFreq = Counter(contentStems).most_common()
        titleFreq = Counter(titleStems).most_common()

        # inserting the page into the Page table with the session
        newPage = Page(curUrl, title, text, rawHTML, lastModified, size, parentID, hash)
        session.add(newPage)
        session.flush()
        pageID = newPage.page_id

        # inserting the child links into the ChildLink table (parent links are handled when the child is visited) with the session
        for link in links:
            newChildLink = ChildLink(pageID, None, link)
            session.add(newChildLink)
        
        # updating the child link table with the parentID when we are working on the child
        # we find child links with matching parentID as page_id and child_url as curUrl
        # we then update the child_page_id to be the pageID of the current page
        # this is done for all child links with the same parentID and curUrl
        session.query(ChildLink).filter(ChildLink.page_id == parentID, ChildLink.child_url == curUrl).update({ChildLink.child_page_id: pageID})

        if (parentID is not None):
            newParentLink = ParentLink(pageID, parentID)
            session.add(newParentLink)
            
        # add each unique term to the Term table
        for term in set(titleStems + contentStems):
            try:
                # attempt to retrieve the term from the database
                existingTerm = session.query(Term).filter_by(term=term).one()
            except NoResultFound:
                # if the term is not found in the database, add it to the session
                newTerm = Term(term=term)
                session.add(newTerm)

        # inserting into the term frequency table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTermFreq = TermFrequency(page_id=pageID, term_id=termID, frequency=freq)
            session.add(newTermFreq)
            
        # inserting into the ContentTermPosition table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            positions = [i for i, t in enumerate(contentStems) if t == stem]
            # the list in the database is a string of comma separated integers
            positionsList = ','.join(str(pos) for pos in positions)
            newContentTermPosition = ContentTermPosition(page_id=pageID, term_id=termID, position_list=positionsList)
            session.add(newContentTermPosition)

        # inserting into the TitleTermPosition table
        for stem, freq in titleFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            positions = [i for i, t in enumerate(titleStems) if t == stem]
            # the list in the database is a string of comma separated integers
            positionsList = ','.join(str(pos) for pos in positions)
            newTitleTermPosition = TitleTermPosition(page_id=pageID, term_id=termID, position_list=positionsList)
            session.add(newTitleTermPosition)

        # inserting into the ContentIndex table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newContentIndex = ContentIndex(term_id=termID, page_id=pageID)
            session.add(newContentIndex)

        # inserting into the TitleIndex table
        for stem, freq in titleFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTitleIndex = TitleIndex(term_id=termID, page_id=pageID)
            session.add(newTitleIndex)

        # commit changes to the database
        session.commit()

        # add to visited set
        visited.add(curUrl)

        if (debug):
            print("Remaining pages to scrape: " +
                  (str(targetVisited - len(visited))))

        # move on to the next page to keep scraping until we reach the target number of pages or we run out of pages to scrape
        # we are doing so in a breadth-first manner
        # we will use a queue to keep track of the pages to scrape
        # we will use a set to keep track of the pages we have already visited (faster than checking the database)

        bfsQueue.extend(link for link in links if link not in visited)

        # start scraping
        while bfsQueue:
            nextLink = bfsQueue.popleft()
            if nextLink not in visited and not None:
                scrape(nextLink, targetVisited, pageID, bfsQueue, visited, driver, session)


# debugging execution
if debug:
    seedUrl = 'https://cse.hkust.edu.hk/'
    targetVisited = 30
    triggerScraping(seedUrl, targetVisited)
    outputDatabase()

if __name__ == '__main__':
    app.run()
