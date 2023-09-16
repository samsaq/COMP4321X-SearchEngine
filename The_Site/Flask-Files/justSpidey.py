from ssl import SSLError
import sys
import os
import re
import hashlib
import numpy as np
import json
from bs4 import BeautifulSoup
from nltk import ngrams
from nltk.stem import PorterStemmer
from collections import deque, Counter
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, quote, parse_qs
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from math import log
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from models import Page, PageVectors, Term, Bigram, Trigram, ParentLink, ChildLink, TitleIndex, ContentIndex, TitleTermPosition, ContentTermPosition, TitleTermFrequency, ContentTermFrequency, TitleBigramIndex, ContentBigramIndex, TitleTrigramIndex, ContentTrigramIndex, DatabaseInfo, Base

# creating a web scraper with selenium, beautifulsoup, and sqlite to get X pages from the given root url into a database setup for later searching

debug = True

if debug and os.path.basename(os.getcwd()) != 'Spidey':
    print("current directory is: " + os.getcwd() +
          " Changing to Spidey directory...")
    found_directory = False

    for root, dirs, files in os.walk('.'):
        if 'Spidey' in dirs:
            os.chdir(os.path.join(root, 'Spidey'))
            found_directory = True
            break

    if not found_directory:
        raise FileNotFoundError("The Spidey directory was not found.")

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
options.add_argument('--log-level=3')
service = Service(driverPath)

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())


def triggerScraping(seedUrl, targetVisited):

    # Check the parameters
    if targetVisited <= 1:
        print("targetVisited must be greater than 1")
        return
    if targetVisited > 1000:
        print("targetVisited must be less than or equal to 1000")
        return

    # check the url
    try:
        response = requests.get(seedUrl)
        response.raise_for_status()
    except SSLError:
        print(f"Invalid SSL/TLS certificate for URL: {seedUrl}")
        return
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
        # Return a 400 Bad Request error if the URL is invalid or the request fails
        print(f"Invalid URL: {seedUrl}")
        return

    visited = set()
    bfsQueue = deque()
    driver = webdriver.Chrome(service=service, options=options)
    # remove to the database file if it already exists
    if debug:
        try:
            os.remove('spidey.db')
        except OSError:
            pass

    # adding an sqlite3 sqlachemy database
    session = makeAlchemy()

    # scrape
    print("Scraping...")
    scrape(seedUrl, targetVisited, None, bfsQueue, visited, driver, session)
    session.commit()
    print ("Page data scraped")

    # get overall database information
    pages = session.query(Page).all()
    numPages = len(pages)
    numTerms = session.query(Term).count()
    avgTitleLength = session.query(func.avg(func.length(Page.title))).scalar()
    avgContentLength = session.query(func.avg(func.length(Page.content))).scalar()

    # generate the bigrams and trigrams
    print("Generating bigrams and trigrams...")
    for page in pages:
        generateBigramsTrigrams(session, page.page_id)
    session.commit()
    print("Bigrams and trigrams generated")

    # get the number of bigrams and trigrams
    numBigrams = session.query(Bigram).count()
    numTrigrams = session.query(Trigram).count()

    # precompute the vectors
    print("Precomputing vectors...")
    preConstructVectors(session, pages)
    session.commit()
    print("Vectors precomputed")

    # add the database information to the database
    databaseInfo = DatabaseInfo(num_pages=numPages, num_terms=numTerms, num_bigrams=numBigrams,
                                num_trigrams=numTrigrams, avg_title_length=avgTitleLength, avg_content_length=avgContentLength)
    session.add(databaseInfo)

    # close the session and driver
    session.commit()
    session.close()
    driver.close()
    print("Scrape complete")

# function to take the exisitng database & precalculate the vectors via the TF-IDF algorithm
# it will do so on a per page basis, and store the vectors in the database
def preConstructVectors(session, pages):
    for page in pages:
        titleVector, contentVector = tfidfVector(session, page.page_id)
        # currently using default weights for title and content (0.8, 0.2)
        weightedVector = getWeightedVector(titleVector, contentVector)
        # now to add the vectors to the database
        pageVector = PageVectors(page_id=page.page_id, title_vector=json.dumps(
            titleVector.tolist()), content_vector=json.dumps(contentVector.tolist()), weighted_vector=json.dumps(weightedVector.tolist()))
        session.add(pageVector)

# function to take a given page, and return the title and content vectors for the page
def tfidfVector(session, pageID):
    # fetch the page
    page = session.query(Page).filter(Page.page_id == pageID).first()
    title = page.title
    content = page.content

    # get the number of pages, title terms, and content terms (use titleIndex and contentIndex)
    numPages = session.query(func.count(Page.page_id)).scalar()
    numTerms = session.query(func.count(Term.term_id)).scalar()

    # tokenize, remove stopwords, and stem the title and content
    titleTokens = re.findall(r'\b\w+\b', title.lower())
    contentTokens = re.findall(r'\b\w+\b', content.lower())

    # remove stopwords from both title and content
    titleTokens = [
        token for token in titleTokens if token not in stopwords]
    contentTokens = [
        token for token in contentTokens if token not in stopwords]

    # stem with porter's
    ps = PorterStemmer()
    titleStems = [ps.stem(token) for token in titleTokens]
    contentStems = [ps.stem(token) for token in contentTokens]

    # count frequency of each word, making a list of tuples (the tf of the tf-idf)
    contentFreq = Counter(contentStems).most_common()
    titleFreq = Counter(titleStems).most_common()

    # create the title and content vectors
    title_vector = np.zeros(numTerms)
    content_vector = np.zeros(numTerms)

    # we can use get_n(term) to get the n for a given term and use that to get the idf

    # now to do the title vector
    for term, freq in titleFreq:
        # get the tf of the term using the titleFreq
        tf = freq
        # get the idf of the term using the get_n
        if (get_n(term, session) == 0):
            if (debug):
                print("term: " + term + " has n = 0")
            idf = 0
        else:
            idf = log(numPages / get_n(term, session))
        tfidf = tf * idf
        # get the index of the term as the term_id of the term in the database - 1
        index = session.query(Term.term_id).filter(
            Term.term == term).first()[0] - 1
        # set the value of the vector at the index to the tfidf
        title_vector[index] = tfidf

    # now to do the content vector
    for term, freq in contentFreq:
        # get the tf of the term using the contentFreq
        tf = freq
        # get the idf of the term using the get_n
        if (get_n(term, session) == 0):
            if (debug):
                print("term: " + term + " has n = 0")
            idf = 0
        else:
            idf = log(numPages / get_n(term, session))
        tfidf = tf * idf
        # get the index of the term as the term_id of the term in the database - 1
        index = session.query(Term.term_id).filter(
            Term.term == term).first()[0] - 1
        # set the value of the vector at the index to the tfidf
        content_vector[index] = tfidf

    return title_vector, content_vector

# function to take a given query and return the tfidf vector for the query
# variant of the above function, but for a query instead of a page
def tfidfQueryVector(query, session):
    # get global database info
    numPages = session.query(DatabaseInfo.num_pages).first()[0]
    numTerms = session.query(DatabaseInfo.num_terms).first()[0]

    # tokenize, remove stopwords, and stem the query
    queryTokens = re.findall(r'\b\w+\b', query.lower())
    # remove stopwords from the query
    queryTokens = [
        token for token in queryTokens if token not in stopwords]
    # stem with porter's
    ps = PorterStemmer()
    queryStems = [ps.stem(token) for token in queryTokens]
    # count frequency of each word, making a list of tuples (the tf of the tf-idf)
    queryFreq = Counter(queryStems).most_common()
    # create the query vector
    queryVector = np.zeros(numTerms)
    # now to do the query vector
    for term, freq in queryFreq:
        # get the tf of the term using the queryFreq
        tf = freq
        # get the idf of the term using the get_n
        # also, if the term is not in the database, then we skip it
        termExists = session.query(Term.term).filter(Term.term == term).first()
        if not termExists:
            continue
        else:
            idf = log(numPages / get_n(term, session))
        tfidf = tf * idf
        # get the index of the term as the term_id of the term in the database - 1
        index = session.query(Term.term_id).filter(
            Term.term == term).first()[0] - 1
        # set the value of the vector at the index to the tfidf
        queryVector[index] = tfidf
    return queryVector

# helper function for the above two - gets the number of pages that contain the given term
def get_n(term, session):
    # get the term_id of the term
    term_id = session.query(Term.term_id).filter(
        Term.term == term).one().term_id
    # get the number of titles and contents that contain the term
    title_docs = session.query(TitleIndex.page_id).filter(
        TitleIndex.term_id == term_id).all()
    content_docs = session.query(ContentIndex.page_id).filter(
        ContentIndex.term_id == term_id).all()
    # form lists of the page_ids for each
    title_docs_ids = [doc[0] for doc in title_docs]
    content_docs_ids = [doc[0] for doc in content_docs]
    # remove duplicates and get the length of the union of the two lists
    tempArray = title_docs_ids + content_docs_ids
    intersectArray = set(tempArray)
    n = len(intersectArray)
    return n

# function to create a weighted composite vector with title and content vectors
def getWeightedVector(titleVector, contentVector, titleWeight=0.8, contentWeight=0.2):
    # Take a weighted average of the title and body vectors to create a composite vector
    weightedVector = (titleWeight * titleVector) + \
        (contentWeight * contentVector)
    # Return the weighted composite vector
    return weightedVector

# function to generate the bigrams and trigrams for a given page & add them to the database
def generateBigramsTrigrams(session, pageID):
    # start by getting the page's title and content
    page = session.query(Page).filter_by(page_id=pageID).one()
    title = page.title
    content = page.content

    # clean the data up
    titleTokens = re.findall(r'\b\w+\b', title.lower())
    contentTokens = re.findall(r'\b\w+\b', content.lower())

    # remove stopwords from both title and content
    titleTokens = [
        token for token in titleTokens if token not in stopwords]
    contentTokens = [
        token for token in contentTokens if token not in stopwords]

    # stem with porter's
    ps = PorterStemmer()
    titleStems = [ps.stem(token) for token in titleTokens]
    contentStems = [ps.stem(token) for token in contentTokens]

    # get the bigrams and trigrams from the title and content
    title_bigrams = list(ngrams(titleStems, 2))
    title_trigrams = list(ngrams(titleStems, 3))
    content_bigrams = list(ngrams(contentStems, 2))
    content_trigrams = list(ngrams(contentStems, 3))

    # for each bigram and trigram, add it to the database if it doesn't already exist
    for bigram in set(title_bigrams + content_bigrams):
        term1, term2 = bigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        # check if the bigram already exists
        bigramExists = session.query(Bigram).filter_by(
            term1_id=term1_id, term2_id=term2_id).first()
        # if it doesn't exist, add it to the database
        if bigramExists is None:
            newBigram = Bigram(term1_id=term1_id, term2_id=term2_id)
            session.add(newBigram)
            session.flush()

    for trigram in set(title_trigrams + content_trigrams):
        term1, term2, term3 = trigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        term3_id = session.query(Term.term_id).filter_by(
            term=term3).one().term_id
        # check if the trigram already exists
        trigramExists = session.query(Trigram).filter_by(
            term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).first()
        # if it doesn't exist, add it to the database
        if trigramExists is None:
            newTrigram = Trigram(
                term1_id=term1_id, term2_id=term2_id, term3_id=term3_id)
            session.add(newTrigram)
            session.flush()

    # loop through the title_bigrams and add them to the TitleBigramIndex for the page
    # do so for the title_trigrams, content_bigrams, and content_trigrams as well with their tables
    for bigram in title_bigrams:
        term1, term2 = bigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        bigram_id = session.query(Bigram.bigram_id).filter_by(
            term1_id=term1_id, term2_id=term2_id).one().bigram_id
        # add the bigram to the TitleBigramIndex
        newTitleBigramIndex = TitleBigramIndex(
            page_id=pageID, bigram_id=bigram_id)
        session.add(newTitleBigramIndex)
        session.flush()
    
    for bigram in content_bigrams:
        term1, term2 = bigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        bigram_id = session.query(Bigram.bigram_id).filter_by(
            term1_id=term1_id, term2_id=term2_id).one().bigram_id
        # add the bigram to the ContentBigramIndex
        newContentBigramIndex = ContentBigramIndex(
            page_id=pageID, bigram_id=bigram_id)
        session.add(newContentBigramIndex)
        session.flush()
    
    for trigram in title_trigrams:
        term1, term2, term3 = trigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        term3_id = session.query(Term.term_id).filter_by(
            term=term3).one().term_id
        trigram_id = session.query(Trigram.trigram_id).filter_by(
            term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).one().trigram_id
        # add the trigram to the TitleTrigramIndex
        newTitleTrigramIndex = TitleTrigramIndex(
            page_id=pageID, trigram_id=trigram_id)
        session.add(newTitleTrigramIndex)
        session.flush()
    
    for trigram in content_trigrams:
        term1, term2, term3 = trigram
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        term3_id = session.query(Term.term_id).filter_by(
            term=term3).one().term_id
        trigram_id = session.query(Trigram.trigram_id).filter_by(
            term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).one().trigram_id
        # add the trigram to the ContentTrigramIndex
        newContentTrigramIndex = ContentTrigramIndex(
            page_id=pageID, trigram_id=trigram_id)
        session.add(newContentTrigramIndex)
        session.flush()

    # session closed outside for clarity
    if (debug):
        print("Generated bigram and trigram positions for page " + str(pageID))

# creating an sqlachemcy database
def makeAlchemy():
    engine = create_engine("sqlite:///spidey.db")

    # Bind the engine to the base class
    Base.metadata.bind = engine

    # Create the tables
    Base.metadata.create_all(bind=engine)

    # create the session (replaces the connection and cursor)
    Session = sessionmaker(bind=engine)
    session = Session()

    # return the sessionFactory - this is what we will use to make sessions to interact with the database
    return session

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
def canonicalize(url, base_url=None):
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

    # resolve relative URLs
    if base_url is not None and not parsed_url.netloc:
        # Resolve relative URL using base URL
        parsed_url = urlparse(urljoin(base_url, url))

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
    if parsed_url.port == default_ports.get(parsed_url.scheme) and parsed_url.port is not None and parsed_url.hostname is not None:
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
        # check for response errors and toss out the page if we get one
        response = requests.head(curUrl)
        if response.status_code < 200 and response.status_code >= 300:
            raise Exception("Response error: " + str(response.status_code))
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

    # get the parent url (if there is none, then it's the root)
    curUrl = canonicalize(curUrl)

    # base case
    if curUrl in visited:
        # if the curUrl has already been visited, the parentURL should be added to the parent table for this pageID, as found from the curUrl
        visitPageID = session.query(Page).filter_by(url=curUrl).first().page_id
        newParentLink = ParentLink(
            page_id=visitPageID, parent_page_id=parentID)
        # if this doesn't work as INSERT OR IGNORE, swap to insert + .onconflict_do_nothing()
        session.merge(newParentLink)
        return
    elif len(visited) >= targetVisited:
        if debug:
            print("Finished scraping " + str(targetVisited) + " pages. Exiting...")
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

        # get the links in the page
        links = []
        # the use of limiters was causing issues with the links
        for link in soup.find_all('a'):
            href = link.get('href')
            # previously checked for href.startswith("http") but this was causing issues with relative links
            if href is not None:
                links.append(href)

        # if any link within links is a relative link, we need to make it absolute
        # use the current url as the base with urljoin and replace the link in links
        for i in range(len(links)):
            if not links[i].startswith("http"):
                links[i] = urljoin(curUrl, links[i])

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
        newPage = Page(curUrl, title, text, rawHTML,
                       lastModified, size, parentID, hash)
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
        session.query(ChildLink).filter(ChildLink.page_id == parentID,
                                        ChildLink.child_url == curUrl).update({ChildLink.child_page_id: pageID})

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

        # inserting into the content term frequency table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTermFreq = ContentTermFrequency(
                page_id=pageID, term_id=termID, frequency=freq)
            session.add(newTermFreq)

        # inserting into the title term frequency table
        for stem, freq in titleFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTermFreq = TitleTermFrequency(
                page_id=pageID, term_id=termID, frequency=freq)
            session.add(newTermFreq)

        # inserting into the ContentTermPosition table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            positions = [i for i, t in enumerate(contentStems) if t == stem]
            # the list in the database is a string of comma separated integers
            positionsList = ','.join(str(pos) for pos in positions)
            newContentTermPosition = ContentTermPosition(
                page_id=pageID, term_id=termID, position_list=positionsList)
            session.add(newContentTermPosition)

        # inserting into the TitleTermPosition table
        for stem, freq in titleFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            positions = [i for i, t in enumerate(titleStems) if t == stem]
            # the list in the database is a string of comma separated integers
            positionsList = ','.join(str(pos) for pos in positions)
            newTitleTermPosition = TitleTermPosition(
                page_id=pageID, term_id=termID, position_list=positionsList)
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
            if (bfsQueue):
                print("BFS Queue length: " + str(len(bfsQueue)))

        # move on to the next page to keep scraping until we reach the target number of pages or we run out of pages to scrape
        # we are doing so in a breadth-first manner
        # we will use a queue to keep track of the pages to scrape
        # we will use a set to keep track of the pages we have already visited (faster than checking the database)

        bfsQueue.extend(link for link in links if link not in visited)

        if not bfsQueue:
            print("No more pages to scrape at: " + curUrl)

        # start scraping
        while bfsQueue:
            nextLink = bfsQueue.popleft()
            if nextLink not in visited and not None:
                scrape(nextLink, targetVisited, pageID,
                       bfsQueue, visited, driver, session)


# debugging execution
if debug:
    seedUrl = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
    targetVisited = 30
    triggerScraping(seedUrl, targetVisited)

if __name__ == '__main__' and not debug:
    # get the seed url and target number of pages to scrape from the command line
    seedUrl = sys.argv[1]
    targetVisited = int(sys.argv[2])
    triggerScraping(seedUrl, targetVisited)
