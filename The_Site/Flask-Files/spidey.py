from ssl import SSLError
import sys
import os
import re
import hashlib
import numpy as np
import pickle
from bs4 import BeautifulSoup
from nltk import ngrams
from nltk.stem import PorterStemmer
from collections import deque, Counter
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, quote, parse_qs
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask, Response, abort, jsonify, request
from math import log
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Text, ForeignKey, func, PickleType
from sqlalchemy.orm.exc import NoResultFound
#, Column, Integer, Text, ForeignKey, func, PickleType, NoResultFound
from numpy import dot
from numpy.linalg import norm

# creating a web scraper with selenium, beautifulsoup, and sqlite to get X pages from the given root url into a database setup for later searching

debug = False
debugRefreshData = False
scrapeRunning = False  # does this work when stateless?

if debug and os.getcwd() != 'Flask-Files':
    found_directory = False

    for root, dirs, files in os.walk('.'):
        if 'Flask-Files' in dirs:
            os.chdir(os.path.join(root, 'Flask-Files'))
            found_directory = True
            break

    if not found_directory:
        raise FileNotFoundError("The 'Flask-Files' directory was not found.")

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
options.add_argument('--log-level=3')
service = Service(driverPath)

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spidey.db'
db = SQLAlchemy(app)

# defining database models:
# define the Page model
class Page(db.Model):
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

    parent_page = db.relationship("Page", remote_side=[page_id])

    def __init__(self, url, title, content, raw_html, last_modified, size, parent_page_id, hash):
        self.url = url
        self.title = title
        self.content = content
        self.raw_html = raw_html
        self.last_modified = last_modified
        self.size = size
        self.parent_page_id = parent_page_id
        self.hash = hash

# define the ParentLink model
class ParentLink(db.Model):
    __tablename__ = 'ParentLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    parent_page_id = Column(Integer, ForeignKey('Page.page_id'))

    page = db.relationship("Page", foreign_keys=[page_id])
    parent_page = db.relationship("Page", foreign_keys=[parent_page_id])

    def __init__(self, page_id, parent_page_id):
        self.page_id = page_id
        self.parent_page_id = parent_page_id

# define the ChildLink model
class ChildLink(db.Model):
    __tablename__ = 'ChildLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_url = Column(Text)

    page = db.relationship("Page", foreign_keys=[page_id])
    child_page = db.relationship("Page", foreign_keys=[child_page_id])

    def __init__(self, page_id, child_page_id, child_url):
        self.page_id = page_id
        self.child_page_id = child_page_id
        self.child_url = child_url

# define the Term model
class Term(db.Model):
    __tablename__ = 'Term'

    term_id = Column(Integer, primary_key=True)
    term = Column(Text)

    def __init__(self, term):
        self.term = term

# define the TitleTermFrequency model
class TitleTermFrequency(db.Model):
    __tablename__ = 'TitleTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = db.relationship("Page")
    term = db.relationship("Term")

    def __init__(self, page_id, term_id, frequency):
        self.page_id = page_id
        self.term_id = term_id
        self.frequency = frequency

# define the ContentTermFrequency model
class ContentTermFrequency(db.Model):
    __tablename__ = 'ContentTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = db.relationship("Page")
    term = db.relationship("Term")

    def __init__(self, page_id, term_id, frequency):
        self.page_id = page_id
        self.term_id = term_id
        self.frequency = frequency

# define the TitleTermPosition model
class TitleTermPosition(db.Model):
    __tablename__ = 'TitleTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = db.relationship("Page")
    term = db.relationship("Term")

    def __init__(self, page_id, term_id, position_list):
        self.page_id = page_id
        self.term_id = term_id
        self.position_list = position_list

# define the ContentTermPosition model
class ContentTermPosition(db.Model):
    __tablename__ = 'ContentTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = db.relationship("Page")
    term = db.relationship("Term")

    def __init__(self, page_id, term_id, position_list):
        self.page_id = page_id
        self.term_id = term_id
        self.position_list = position_list

# define the TitleIndex model
class TitleIndex(db.Model):
    __tablename__ = 'TitleIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = db.relationship("Term")
    page = db.relationship("Page")

    def __init__(self, term_id, page_id):
        self.term_id = term_id
        self.page_id = page_id

# define the ContentIndex model
class ContentIndex(db.Model):
    __tablename__ = 'ContentIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = db.relationship("Term")
    page = db.relationship("Page")

    def __init__(self, term_id, page_id):
        self.term_id = term_id
        self.page_id = page_id

# define the Bigram model
class Bigram(db.Model):
    __tablename__ = 'Bigram'

    bigram_id = Column(Integer, primary_key=True)
    term1_id = Column(Integer, ForeignKey('Term.term_id'))
    term2_id = Column(Integer, ForeignKey('Term.term_id'))

    term1 = db.relationship("Term", foreign_keys=[term1_id])
    term2 = db.relationship("Term", foreign_keys=[term2_id])

# define the TitleBigramPosition model
class TitleBigramPosition(db.Model):
    __tablename__ = 'TitleBigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    bigram_id = Column(Integer, ForeignKey(
        'Bigram.bigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    bigram = db.relationship("Bigram")

    def __init__(self, page_id, bigram_id, position_list, frequency):
        self.page_id = page_id
        self.bigram_id = bigram_id
        self.position_list = position_list
        self.frequency = frequency

# define the ContentBigramPosition model
class ContentBigramPosition(db.Model):
    __tablename__ = 'ContentBigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    bigram_id = Column(Integer, ForeignKey(
        'Bigram.bigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    bigram = db.relationship("Bigram")

    def __init__(self, page_id, bigram_id, position_list, frequency):
        self.page_id = page_id
        self.bigram_id = bigram_id
        self.position_list = position_list
        self.frequency = frequency

# define the Trigram model
class Trigram(db.Model):
    __tablename__ = 'Trigram'

    trigram_id = Column(Integer, primary_key=True)
    term1_id = Column(Integer, ForeignKey('Term.term_id'))
    term2_id = Column(Integer, ForeignKey('Term.term_id'))
    term3_id = Column(Integer, ForeignKey('Term.term_id'))

    term1 = db.relationship("Term", foreign_keys=[term1_id])
    term2 = db.relationship("Term", foreign_keys=[term2_id])
    term3 = db.relationship("Term", foreign_keys=[term3_id])

# define the TitleTrigramPosition model
class TitleTrigramPosition(db.Model):
    __tablename__ = 'TitleTrigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    trigram_id = Column(Integer, ForeignKey(
        'Trigram.trigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    trigram = db.relationship("Trigram")

    def __init__(self, page_id, trigram_id, position_list, frequency):
        self.page_id = page_id
        self.trigram_id = trigram_id
        self.position_list = position_list
        self.frequency = frequency

# define the ContentTrigramPosition model
class ContentTrigramPosition(db.Model):
    __tablename__ = 'ContentTrigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    trigram_id = Column(Integer, ForeignKey(
        'Trigram.trigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    trigram = db.relationship("Trigram")

    def __init__(self, page_id, trigram_id, position_list, frequency):
        self.page_id = page_id
        self.trigram_id = trigram_id
        self.position_list = position_list
        self.frequency = frequency

# define the model for the PageVectors table
class PageVectors(db.Model):
    __tablename__ = 'PageVectors'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    title_vector = Column(PickleType, nullable=False)
    content_vector = Column(PickleType, nullable=False)
    weighted_vector = Column(PickleType, nullable=False)

    page = db.relationship("Page")

    def __init__(self, page_id, title_vector, content_vector, weighted_vector):
        self.page_id = page_id
        self.title_vector = title_vector
        self.content_vector = content_vector
        self.weighted_vector = weighted_vector

# define the model for overall database information
class DatabaseInfo(db.Model):
    __tablename__ = 'DatabaseInfo'

    database_id = Column(Integer, primary_key=True)
    num_pages = Column(Integer)
    num_terms = Column(Integer)
    num_bigrams = Column(Integer)
    num_trigrams = Column(Integer)
    avg_title_length = Column(Integer)
    avg_content_length = Column(Integer)

    def __init__(self, num_pages, num_terms, num_bigrams, num_trigrams, avg_title_length, avg_content_length):
        self.num_pages = num_pages
        self.num_terms = num_terms
        self.num_bigrams = num_bigrams
        self.num_trigrams = num_trigrams
        self.avg_title_length = avg_title_length
        self.avg_content_length = avg_content_length

# function for API call to remake the database based off of the given parameters


@app.route('/api/triggerScraping/<path:seedUrl>/<int:targetVisited>/', methods=['POST'])
def triggerScraping(seedUrl, targetVisited):
    with app.app_context():
        global scrapeRunning
        if scrapeRunning:  # may not work due to statelessness of flask DOUBLE CHECK
            # if a scrape is already running, return the request with an error that the scrape is already running
            return jsonify({'error': 'scrape already running'}), 400

        # Check the parameters
        if targetVisited <= 1:
            return jsonify({'status': 'error', 'message': 'Too little pages - targetVisited must be greater than 1'}), 400
        if targetVisited > 1000:
            return jsonify({'status': 'error', 'message': 'Too many pages - targetVisited must be less than or equal to 1000'}), 400

        # check the url
        try:
            response = requests.get(seedUrl)
            response.raise_for_status()
        except SSLError:
            return jsonify({'status': 'error', 'message': f"Invalid SSL/TLS certificate for URL: {seedUrl}"}), 400
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
            # Return a 400 Bad Request error if the URL is invalid or the request fails
            return jsonify({'status': 'error', 'message': f"Invalid URL: {seedUrl}"}), 400

        scrapeRunning = True
        visited = set()
        bfsQueue = deque()
        driver = webdriver.Chrome(service=service, options=options)
        # remove to the database file if it already exists
        if debug and debugRefreshData:
            try:
                os.remove('instance/spidey.db')
            except OSError:
                pass

        # adding an sqlite3 sqlachemy database
        session = makeAlchemy()

        # scrape
        if debug and debugRefreshData:
            scrape(seedUrl, targetVisited, None, bfsQueue, visited, driver, session)
        session.commit()

        # get overall database information
        pages = session.query(Page).all()
        numPages = len(pages)
        numTerms = session.query(Term).count()
        avgTitleLength = session.query(func.avg(func.length(Page.title))).scalar()
        avgContentLength = session.query(func.avg(func.length(Page.content))).scalar()

        # generate the bigrams and trigrams
        if debug and debugRefreshData:
            for page in pages:
                generateBigramsTrigrams(session, page.page_id)
            session.commit()

        # get the number of bigrams and trigrams
        numBigrams = session.query(Bigram).count()
        numTrigrams = session.query(Trigram).count()

        # precompute the vectors
        preConstructVectors(session, pages)
        session.commit()

        # add the database information to the database
        databaseInfo = DatabaseInfo(num_pages=numPages, num_terms=numTerms, num_bigrams=numBigrams,
                                    num_trigrams=numTrigrams, avg_title_length=avgTitleLength, avg_content_length=avgContentLength)
        session.add(databaseInfo)

        # close the session and driver
        scrapeRunning = False
        session.commit()
        session.close()
        driver.close()
    
# function to take the exisitng database & precalculate the vectors via the TF-IDF algorithm
# it will do so on a per page basis, and store the vectors in the database
def preConstructVectors(session, pages):
    for page in pages:
        titleVector, contentVector = tfidfVector(session, page.page_id)
        # currently using default weights for title and content (0.8, 0.2)
        weightedVector = getWeightedVector(titleVector, contentVector)
        # now to add the vectors to the database
        pageVector = PageVectors(page_id=page.page_id, title_vector=pickle.dumps(titleVector), content_vector=pickle.dumps(contentVector), weighted_vector=pickle.dumps(weightedVector))
        session.add(pageVector)

# function to take a given page, and return the title and content vectors for the page
def tfidfVector(session, pageID):
    #fetch the page
    page = session.query(Page).filter(Page.page_id == pageID).first()
    title = page.title
    content = page.content

    # get the number of pages, title terms, and content terms (use titleIndex and contentIndex)
    numPages = session.query(func.count(Page.page_id)).scalar()
    numTitleTerms = session.query(func.count(TitleIndex.term_id)).scalar()
    numContentTerms = session.query(func.count(ContentIndex.term_id)).scalar()
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
    term_id = session.query(Term.term_id).filter(Term.term == term).one().term_id
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
    weightedVector = (titleWeight * titleVector) + (contentWeight * contentVector)
    # Return the weighted composite vector
    return weightedVector

# function to search based off of the given query
@app.route('/api/search/<query>/', defaults={'numResults': 50}) # alt route to allow for default number of results
@app.route('/api/search/<query>/<int:numResults>/')
def search(query, numResults=50):
    with app.app_context():
        # check that the query is not empty and not just whitespace
        if query == None or query.isspace():
            return jsonify({'status': 'error', 'message': 'Empty query'}), 400

        session = db.session  # double check if this is the correct session
        # preprocess the query string for the search
        queryTokens = re.findall(r'\b\w+\b', query.lower())
        # remove stopwords from the query
        queryTokens = [token for token in queryTokens if token not in stopwords]
        # stem the query
        ps = PorterStemmer()
        queryStems = [ps.stem(token) for token in queryTokens]
        # count frequency of each word, making a list of tuples (sorted by frequency)
        queryFreq = Counter(queryStems).most_common()

        # get bigrams and trigrams for the query
        queryBigrams = list(ngrams(queryStems, 2))
        queryTrigrams = list(ngrams(queryStems, 3))

        # get an array of the words in the query to iterate through
        searchPhrases = extractPhrases(query)
        # check that the phrases are not too long & do not contain other phrases
        for phrase in searchPhrases:
            if len(phrase.split()) > 3:
                return jsonify({'status': 'error', 'message': f'Phrase: {phrase} too long please reduce to 3 words or less'}), 400
            for otherPhrase in searchPhrases:
                if phrase != otherPhrase and phrase in otherPhrase:
                    return jsonify({'status': 'error', 'message': f'Phrase: {phrase} is nested within another phrase: {otherPhrase}'}), 400

        # remove stopwords and stem the phrases
        for i in range(len(searchPhrases)):
            phraseTokens = re.findall(r'\b\w+\b', searchPhrases[i].lower())
            phraseTokens = [token for token in phraseTokens if token not in stopwords]
            ps = PorterStemmer()
            phraseStems = [ps.stem(token) for token in phraseTokens]
            searchPhrases[i] = ' '.join(phraseStems)

        # for each phrase in the query, get the phraseID and add it to the processedSearchPhrases list (phraseID is the trigramID if the phrase is a trigram, bigramID if a bigram, and termID if a unigram)
        # processedSearchPhrases is a list of tuples (phraseID, phrase, phraseSize)
        processedSearchPhrases = []
        for phrase in searchPhrases:
            phraseSize = len(phrase.split())
            try:
                if phraseSize == 3:
                    # get the termIDs for the words in the phrase
                    term1ID = session.query(Term.term_id).filter_by(
                        term=phrase.split()[0]).one().term_id
                    term2ID = session.query(Term.term_id).filter_by(
                        term=phrase.split()[1]).one().term_id
                    term3ID = session.query(Term.term_id).filter_by(
                        term=phrase.split()[2]).one().term_id
                    phraseID = session.query(Trigram.trigram_id).filter_by(
                        term1_id=term1ID, term2_id=term2ID, term3_id=term3ID).one().trigram_id
                elif phraseSize == 2:
                    # get the termIDs for the words in the phrase
                    term1ID = session.query(Term.term_id).filter_by(
                        term=phrase.split()[0]).one().term_id
                    term2ID = session.query(Term.term_id).filter_by(
                        term=phrase.split()[1]).one().term_id
                    phraseID = session.query(Bigram.bigram_id).filter_by(
                        term1_id=term1ID, term2_id=term2ID).one().bigram_id
                else:
                    # get the termID for the word in the phrase
                    termID = session.query(Term.term_id).filter_by(
                        term=phrase).one().term_id
                    phraseID = termID
            except NoResultFound:
                phraseID = None

            processedSearchPhrases.append((phraseID, phrase, phraseSize))

        # get the tfidf vector for the query as a numpy array
        queryVector = tfidfQueryVector(query, session)

        # get the database information needed for the search
        numDocs = session.query(func.count(Page.page_id)).scalar()
        numTerms = session.query(func.count(Term.term_id)).scalar()

        # calculate the cosine similarity between the query vector and all document vectors
        docVectors = np.zeros((numDocs, numTerms))
        docSims = []
        for i in range(numDocs):
            docID = i + 1
            doc = session.query(PageVectors).filter_by(page_id=docID).one()
            unPickledVector = pickle.loads(doc.weighted_vector)
            docVectors[i] = unPickledVector
            docSims.append((docID,  cosineSimilarity(queryVector.reshape(
                1, -1), unPickledVector.reshape(1, -1)).flatten()[0]))

            # now to check phrases and do weighting for matches within the document
            # modifiers for title and content weighting is handled with the getWeightedVector function and is already done

            for phraseID, phrase, phraseSize in processedSearchPhrases:
                if phraseID is not None:
                    if phraseSize == 3:
                        # split the phrase into the 3 terms
                        term1, term2, term3 = phrase.split()
                        # get the termIDs for the words in the phrase
                        term1ID = session.query(Term.term_id).filter_by(
                            term=term1).one().term_id
                        term2ID = session.query(Term.term_id).filter_by(
                            term=term2).one().term_id
                        term3ID = session.query(Term.term_id).filter_by(
                            term=term3).one().term_id
                        trigramID = session.query(Trigram.trigram_id).filter_by(
                            term1_id=term1ID, term2_id=term2ID, term3_id=term3ID).one().trigram_id
                        # check if the trigram is in the document (if this page_id has this trigram_id)
                        # we can check both TitleTrigramPosition and ContentTrigramPosition beacuse if its in one its in the document
                        if session.query(TitleTrigramPosition).filter_by(page_id=docID, trigram_id=trigramID).count() == 0 and session.query(ContentTrigramPosition).filter_by(page_id=docID, trigram_id=trigramID).count() == 0:
                            docID, docSim = docSims[i]
                            docSim *= 0.9
                            docSims[i] = (docID, docSim)
                        else:
                            docID, docSim = docSims[i]
                            docSim *= 1.1
                            docSims[i] = (docID, docSim)
                    elif phraseSize == 2:
                        # split the phrase into the 2 terms
                        term1, term2 = phrase.split()
                        # get the termIDs for the words in the phrase
                        term1ID = session.query(Term.term_id).filter_by(
                            term=term1).one().term_id
                        term2ID = session.query(Term.term_id).filter_by(
                            term=term2).one().term_id
                        bigramID = session.query(Bigram.bigram_id).filter_by(
                            term1_id=term1ID, term2_id=term2ID).one().bigram_id
                        # check if the bigram is in the document (if this page_id has this bigram_id)
                        # we can check both TitleBigramPosition and ContentBigramPosition beacuse if its in one its in the document
                        if session.query(TitleBigramPosition).filter_by(page_id=docID, bigram_id=bigramID).count() == 0 and session.query(ContentBigramPosition).filter_by(page_id=docID, bigram_id=bigramID).count() == 0:
                            docID, docSim = docSims[i]
                            docSim *= 0.95
                            docSims[i] = (docID, docSim)
                        else:
                            docID, docSim = docSims[i]
                            docSim *= 1.05
                            docSims[i] = (docID, docSim)
                    else:
                        # get the termID for the word in the phrase
                        termID = session.query(Term.term_id).filter_by(
                            term=phrase).one().term_id
                        # check if the term is in the document (if this page_id has this term_id)
                        # we can check both TitleIndex and ContentIndex beacuse if its in one its in the document
                        if session.query(TitleIndex).filter_by(page_id=docID, term_id=termID).count() == 0 and session.query(ContentIndex).filter_by(page_id=docID, term_id=termID).count() == 0:
                            docID, docSim = docSims[i]
                            docSim *= 0.975
                            docSims[i] = (docID, docSim)
                        else:
                            docID, docSim = docSims[i]
                            docSim *= 1.025
                            docSims[i] = (docID, docSim)

        # limit the values to be within the range of -1 and 1
        docSims = np.clip(docSims, -1, 1)

        # sort the document similarities in descending order and get the top numResults
        sortedSims = sorted(docSims, key=lambda x: x[1], reverse=True)
        topResults = sortedSims[:numResults]

        # convert the top results to JSON and return it
        convertedResults = convertTopResultsToJSON(topResults)
        return jsonify({"pages": convertedResults}), 200
    
def cosineSimilarity(a, b):
    return dot(a.T, b) / (norm(a) * norm(b))

# get the demarcated phrases from the query (marked by double quotes)
def extractPhrases(query):
    # Use regular expression to extract phrases enclosed in double quotes
    pattern = r'"([^"]*)"'
    matches = re.findall(pattern, query)

    # we aren't handling nested phrases now

    # Return the extracted phrases
    return matches

# take the top results from the search and convert them to JSON
# use the id to get the data
# we need the title, url, last modified date, top 10 keywords and their frequencies, the first 10 child links, and page content
def convertTopResultsToJSON(topResults):
    session = db.session
    resultJSONs = []
    # get the data needed for the JSON
    for docID, cosSim in topResults:
        page = session.query(Page).filter_by(page_id=docID).one()
        # get the top 10 keywords and their frequencies
        topKeywords = session.query(Term.term, ContentTermFrequency.frequency).join(ContentTermFrequency).filter(
            ContentTermFrequency.page_id == docID).order_by(ContentTermFrequency.frequency.desc()).limit(10).all()
        
        # make sure topKeywords is a list of strings
        topKeywords = [(str(keyword[0]), int(keyword[1])) for keyword in topKeywords]

        # get the first 10 child links
        childLinks = session.query(ChildLink).filter_by(
            page_id=docID).limit(10).all()
        
        # get the urls of the child links as a list for the JSON
        childLinks = [childLink.child_url for childLink in childLinks]

        lastModified = session.query(
            Page.last_modified).filter_by(page_id=docID).one()

        # get the last modified date as a string
        lastModified = lastModified[0]

        # convert the data to JSON
        pageJSON = {
            "title": page.title,
            "url": page.url,
            "lastModified": lastModified,
            "topKeywords": topKeywords,
            "childLinks": childLinks,
            "content": page.content
        }

        # add the JSON to the list of JSONs
        resultJSONs.append(pageJSON)

    return resultJSONs

# function to get the bigram and trigram IDs for a given query - helper function for search
# takes in a numpy array of bigrams and trigrams from the ngrams function
def getBigramsTrigramsIDs(session, bigramsArray, trigramsArray):
    bigramsIDs = []
    trigramsIDs = []
    for i in range(len(bigramsArray)):
        term1, term2 = bigramsArray[i]
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        bigramID = session.query(Bigram).filter_by(
            term1_id=term1_id, term2_id=term2_id).one().bigram_id
        bigramsIDs.append(bigramID)
    for i in range(len(trigramsArray)):
        term1, term2, term3 = trigramsArray[i]
        term1_id = session.query(Term.term_id).filter_by(
            term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(
            term=term2).one().term_id
        term3_id = session.query(Term.term_id).filter_by(
            term=term3).one().term_id
        trigramID = session.query(Trigram).filter_by(
            term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).one().trigram_id
        trigramsIDs.append(trigramID)
    return bigramsIDs, trigramsIDs

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

    # session closed outside for clarity
    if(debug):
        print("Generated bigram and trigram positions for page " + str(pageID))

# creating an sqlachemcy database
def makeAlchemy():
    with app.app_context():
        # create the session (replaces the connection and cursor)
        session = db.session

        # create the tables
        db.create_all()

        # return the sessionFactory - this is what we will use to make sessions to interact with the database
        return session
    # if we got here, something went wrong - return an error exception
    raise Exception('Could not create database in makeAlchemy()')

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

    with app.app_context():

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
            print ("Finished scraping " + str(targetVisited) + " pages. Exiting...")
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
            for link in soup.find_all('a'): # the use of limiters was causing issues with the links
                href = link.get('href')
                if href is not None: # previously checked for href.startswith("http") but this was causing issues with relative links
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
    justSearching = True
    seedUrl = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
    targetVisited = 30
    if(not justSearching):
        triggerScraping(seedUrl, targetVisited)
    testSearchQuery = 'Hong Kong University of Science and Technology "crawler" "Test Page" "officially certified academic"'
    print(search(testSearchQuery))

if __name__ == '__main__':
    app.run()
