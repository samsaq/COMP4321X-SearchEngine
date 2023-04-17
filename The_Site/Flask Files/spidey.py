import sys
import os
import sqlite3
import re
import hashlib
import numpy as np
import pickle
from bs4 import BeautifulSoup
from nltk import ngrams
from nltk.stem import PorterStemmer
from collections import deque, Counter
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, quote, parse_qs
from spideyTest import outputDatabase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask
from math import log
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import Column, Integer, Text, ForeignKey, func, PickleType
from numpy import dot
from numpy.linalg import norm

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

# define the ParentLink model
class ParentLink(db.Model):
    __tablename__ = 'ParentLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    parent_page_id = Column(Integer, ForeignKey('Page.page_id'))

    page = db.relationship("Page", foreign_keys=[page_id])
    parent_page = db.relationship("Page", foreign_keys=[parent_page_id])

# define the ChildLink model
class ChildLink(db.Model):
    __tablename__ = 'ChildLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_url = Column(Text)

    page = db.relationship("Page", foreign_keys=[page_id])
    child_page = db.relationship("Page", foreign_keys=[child_page_id])

# define the Term model
class Term(db.Model):
    __tablename__ = 'Term'

    term_id = Column(Integer, primary_key=True)
    term = Column(Text)

# define the TitleTermFrequency model
class TitleTermFrequency(db.Model):
    __tablename__ = 'TitleTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = db.relationship("Page")
    term = db.relationship("Term")

# define the ContentTermFrequency model
class ContentTermFrequency(db.Model):
    __tablename__ = 'ContentTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = db.relationship("Page")
    term = db.relationship("Term")

# define the TitleTermPosition model
class TitleTermPosition(db.Model):
    __tablename__ = 'TitleTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = db.relationship("Page")
    term = db.relationship("Term")

# define the ContentTermPosition model
class ContentTermPosition(db.Model):
    __tablename__ = 'ContentTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = db.relationship("Page")
    term = db.relationship("Term")

# define the TitleIndex model
class TitleIndex(db.Model):
    __tablename__ = 'TitleIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = db.relationship("Term")
    page = db.relationship("Page")

# define the ContentIndex model
class ContentIndex(db.Model):
    __tablename__ = 'ContentIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = db.relationship("Term")
    page = db.relationship("Page")

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
    bigram_id = Column(Integer, ForeignKey('Bigram.bigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    bigram = db.relationship("Bigram")

# define the ContentBigramPosition model
class ContentBigramPosition(db.Model):
    __tablename__ = 'ContentBigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    bigram_id = Column(Integer, ForeignKey('Bigram.bigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    bigram = db.relationship("Bigram")

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
    trigram_id = Column(Integer, ForeignKey('Trigram.trigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    trigram = db.relationship("Trigram")

# define the ContentTrigramPosition model
class ContentTrigramPosition(db.Model):
    __tablename__ = 'ContentTrigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    trigram_id = Column(Integer, ForeignKey('Trigram.trigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = db.relationship("Page")
    trigram = db.relationship("Trigram")

# define the model for the PageVectors table
class PageVectors(db.Model):
    __tablename__ = 'PageVectors'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    title_vector = Column(PickleType, nullable=False)
    content_vector = Column(PickleType, nullable=False)
    weighted_vector = Column(PickleType, nullable=False) # default no-phrase vector to weight towards titles
    title_bigram_vector = Column(PickleType, nullable=False)
    content_bigram_vector = Column(PickleType, nullable=False)
    title_trigram_vector = Column(PickleType, nullable=False)
    content_trigram_vector = Column(PickleType, nullable=False)

    page = db.relationship("Page")


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
    session = makeAlchemy()

    # scrape
    scrape(seedUrl, targetVisited, None, bfsQueue, visited, driver, session)
    session.commit()

    # get overall database information
    pages = session.query(Page).all()
    numPages = len(pages)
    numTerms = session.query(Term).count()
    avgTitleLength = session.query(func.avg(Page.title_length)).scalar()
    avgContentLength = session.query(func.avg(Page.content_length)).scalar()

    # generate the bigrams and trigrams
    for page in pages:
        generateBigramsTrigrams(session, page.page_id)
    session.commit()

    # get the number of bigrams and trigrams
    numBigrams = session.query(Bigram).count()
    numTrigrams = session.query(Trigram).count()

    # precompute the vectors
    preConstructVectors(session, pages, avgTitleLength, avgContentLength)
    session.commit()
    
    # add the database information to the database
    databaseInfo = DatabaseInfo(num_pages=numPages, num_terms=numTerms, num_bigrams=numBigrams, num_trigrams=numTrigrams, avg_title_length=avgTitleLength, avg_content_length=avgContentLength)
    session.add(databaseInfo)

    # close the session and driver
    session.commit()
    session.close()
    driver.close()

# function to take the exisitng database & precalculate the vectors via the TF-IDF algorithm
# it will do so on a per page basis, and will do so for the term, bigram, and trigram vectors for both the title and content
def preConstructVectors(session, pages, avgTitleLength, avgContentLength):
    
    for page in pages:
        titleVector, contentVector, titleBigramVector, contentBigramVector, titleTrigramVector, contentTrigramVector = BM25Vector(session, page.page_id, avgTitleLength, avgContentLength)
        weightedVector = weightedVector(titleVector, contentVector) # currently using default weights for title and content (0.8, 0.2)
        # now to add the vectors to the database
        pageVector = PageVectors(page_id=page.page_id, title_vector=pickle.dumps(titleVector), content_vector=pickle.dumps(contentVector), weighted_vector=pickle.dumps(weightedVector), title_bigram_vector=pickle.dumps(titleBigramVector), content_bigram_vector=pickle.dumps(contentBigramVector), title_trigram_vector=pickle.dumps(titleTrigramVector), content_trigram_vector=pickle.dumps(contentTrigramVector))
        session.add(pageVector)

# a BM25 function to take the given page, and reuturns the title and content vectors for the page
def BM25Vector(session, pageID, avgTitleLength, avgContentLength):
    page = session.query(Page).filter(Page.page_id == pageID).first()
    title_terms = session.query(Term, TitleTermFrequency).filter(Term.term_id == TitleTermFrequency.term_id).filter(TitleTermFrequency.page_id == pageID).all()
    content_terms = session.query(Term, ContentTermFrequency).filter(Term.term_id == ContentTermFrequency.term_id).filter(ContentTermFrequency.page_id == pageID).all()

    # create bigrams and trigrams for the title
    title_bigrams = list(ngrams(page.title.split(), 2))
    title_trigrams = list(ngrams(page.title.split(), 3))

    # create bigrams and trigrams for the content
    content_bigrams = list(ngrams(page.content.split(), 2))
    content_trigrams = list(ngrams(page.content.split(), 3))
    title_bigrams_ids, title_trigrams_ids = getBigramsTrigramsIDs(session, title_bigrams, title_trigrams)
    content_bigrams_ids, content_trigrams_ids = getBigramsTrigramsIDs(session, content_bigrams, content_trigrams)
    # we have the ids as lists

    # use the BM25 algorithm to calculate the term vectors for the title and content seperately
    # variable presets are k1 = 2.5, b = 0.75, delta = 0.25
    title_vector = np.zeros(len(title_terms))
    content_vector = np.zeros(len(content_terms))
    title_bigram_vector = np.zeros(len(title_bigrams))
    content_bigram_vector = np.zeros(len(content_bigrams))
    title_trigram_vector = np.zeros(len(title_trigrams))
    content_trigram_vector = np.zeros(len(content_trigrams))
    for i, (term, term_frequency) in enumerate(title_terms):
        df = session.query(func.count(TitleTermFrequency.page_id)).filter_by(term_id=term.term_id).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))

        # calculate the tf-idf for the term
        tf_idf = ((2.5 * term_frequency.frequency) / (term_frequency.frequency + 1.5 * (0.25 + 0.75 * (len(page.title) / avgTitleLength)))) * idf

        # append to the title vector
        title_vector[i] = tf_idf

    for i, (term, term_frequency) in enumerate(content_terms):
        df = session.query(func.count(ContentTermFrequency.page_id)).filter_by(term_id=term.term_id).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))

        # calculate the tf-idf for the term
        tf_idf = ((2.5 * term_frequency.frequency) / (term_frequency.frequency + 1.5 * (0.25 + 0.75 * (len(page.content) / avgContentLength)))) * idf

        # append to the content vector
        content_vector[i] = tf_idf

    # iterate through title bigrams and trigrams, and calculate their tf-idf scores
    for i in range(len(title_bigrams)):
        tf = session.query(TitleBigramPosition.frequency).filter_by(page_id=pageID, bigram_id=title_bigrams_ids[i]).scalar()
        # df = number of pages that contain the bigram, so get the number of TitleBigramPosition entries with the bigram_id
        df = session.query(func.count(TitleBigramPosition.page_id)).filter_by(bigram_id=title_bigrams_ids[i]).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))
        tf_idf = ((2.5 * tf) / (tf + 1.5 * (0.25 + 0.75 * (len(page.title) / avgTitleLength)))) * idf
        title_bigram_vector[len(title_terms) + i] = tf_idf

    for i in range(len(content_bigrams)):
        tf = session.query(ContentBigramPosition.frequency).filter_by(page_id=pageID, bigram_id=content_bigrams_ids[i]).scalar()
        # df = number of pages that contain the bigram, so get the number of ContentBigramPosition entries with the bigram_id
        df = session.query(func.count(ContentBigramPosition.page_id)).filter_by(bigram_id=content_bigrams_ids[i]).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))
        tf_idf = ((2.5 * tf) / (tf + 1.5 * (0.25 + 0.75 * (len(page.content) / avgContentLength)))) * idf
        content_bigram_vector[len(content_terms) + i] = tf_idf
    
    for i in range(len(title_trigrams)):
        tf = session.query(TitleTrigramPosition.frequency).filter_by(page_id=pageID, trigram_id=title_trigrams_ids[i]).scalar()
        # df = number of pages that contain the trigram, so get the number of TitleTrigramPosition entries with the trigram_id
        df = session.query(func.count(TitleTrigramPosition.page_id)).filter_by(trigram_id=title_trigrams_ids[i]).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))
        tf_idf = ((2.5 * tf) / (tf + 1.5 * (0.25 + 0.75 * (len(page.title) / avgTitleLength)))) * idf
        title_trigram_vector[len(title_terms) + len(title_bigrams) + i] = tf_idf

    for i in range(len(content_trigrams)):
        tf = session.query(ContentTrigramPosition.frequency).filter_by(page_id=pageID, trigram_id=content_trigrams_ids[i]).scalar()
        # df = number of pages that contain the trigram, so get the number of ContentTrigramPosition entries with the trigram_id
        df = session.query(func.count(ContentTrigramPosition.page_id)).filter_by(trigram_id=content_trigrams_ids[i]).scalar()
        idf = log((session.query(func.count(Page.page_id)).scalar() - df + 0.5) / (df + 0.5))
        tf_idf = ((2.5 * tf) / (tf + 1.5 * (0.25 + 0.75 * (len(page.content) / avgContentLength)))) * idf
        content_trigram_vector[len(content_terms) + len(content_bigrams) + i] = tf_idf
    # return the all of the vectors as numpy arrays
    return title_vector, content_vector, title_bigram_vector, content_bigram_vector, title_trigram_vector, content_trigram_vector

# function to get a BM25 vector for a given query (the query has been preprocessesd already for stemming and stopword removal, and is now a list of terms)
def getBM25QueryVector (session, queryFreq, queryBigrams, queryTrigrams): # queryFreq is a list of tuples of (term, frequency) sorted by frequency
    # get the database information needed to calculate the BM25 vector
    databaseInfo = session.query(DatabaseInfo).first()

    # calculate the BM25 vector and return a numpy array
    # variable presets are k1 = 2.5, b = 0.75, delta = 0.25, as in the BM25Vector function
    k1 = 2.5
    b = 0.75
    delta = 0.25
    numTerms = len(queryFreq)
    queryVector = np.zeros(databaseInfo.num_terms)
    for i in range(numTerms):
        term = queryFreq[i][0]
        termFreq = queryFreq[i][1]
        termID = session.query(Term.term_id).filter_by(term=term).one().term_id
        idf = get_bm25_idf(term)
        numerator = idf * termFreq * (k1 + 1)
        denominator = termFreq + k1 * (1 - b + b * get_n(term) / databaseInfo.num_docs) + delta
        queryVector[termID] = numerator / denominator

    # calculate bigram vector
    numBigrams = len(queryBigrams)
    queryBigramsVector = np.zeros(databaseInfo.num_bigrams)
    for i in range(numBigrams):
        bigram = queryBigrams[i]
        bigramFreq = queryBigrams.count(bigram)
        bigramID = session.query(Bigram.bigram_id).filter_by(bigram=bigram).one().bigram_id
        idf = get_bm25_idf(bigram)
        numerator = idf * bigramFreq * (k1 + 1)
        denominator = bigramFreq + k1 * (1 - b + b * get_n(bigram) / databaseInfo.num_docs) + delta
        queryBigramsVector[bigramID] = numerator / denominator

    # calculate trigram vector
    numTrigrams = len(queryTrigrams)
    queryTrigramsVector = np.zeros(databaseInfo.num_trigrams)
    for i in range(numTrigrams):
        trigram = queryTrigrams[i]
        trigramFreq = queryTrigrams.count(trigram)
        trigramID = session.query(Trigram.trigram_id).filter_by(trigram=trigram).one().trigram_id
        idf = get_bm25_idf(trigram)
        numerator = idf * trigramFreq * (k1 + 1)
        denominator = trigramFreq + k1 * (1 - b + b * get_n(trigram) / databaseInfo.num_docs) + delta
        queryTrigramsVector[trigramID] = numerator / denominator

    return queryVector, queryBigramsVector, queryTrigramsVector

# helper function for the above - gets the idf of a given term overall (for both title and content)
def get_bm25_idf(term):
    N = db.session.query(Page).count() # total number of documents
    n = get_n(term) # number of documents that contain the term
    idf = log((N-n+0.5)/(n+0.5))
    return idf

# helper function for the above - gets the number of pages that contain the given term
def get_n(term):
    title_docs = set([freq.page_id for freq in TitleTermFrequency.query.filter_by(term=term)])
    content_docs = set([freq.page_id for freq in ContentTermFrequency.query.filter_by(term=term)])
    n = len(title_docs.union(content_docs))
    return n

# function to create a weighted composite vector with title and content vectors
def getWeightedVector(titleVector, contentVector, titleWeight=0.8, contentWeight=0.2):
    # Take a weighted average of the title and body vectors to create a composite vector
    weightedVector = titleWeight * titleVector + contentWeight * contentVector
    
    # Return the weighted composite vector
    return weightedVector

# function to search based off of the given query - currently has no phrase search
def search(session, query, numResults=50):
    # preprocess the query string for the search
    queryTokens = re.findall(r'\b\w+\b', query.lower())
    # remove stopwords from the query
    queryTokens = [token for token in queryTokens if token not in stopwords]
    # stem the query
    ps = PorterStemmer()
    queryStems = [ps.stem(token) for token in queryTokens]
    # count frequency of each word, making a list of tuples
    queryFreq = Counter(queryStems).most_common()
    
    # get bigrams and trigrams for the query
    queryBigrams = list(ngrams(queryStems, 2))
    queryTrigrams = list(ngrams(queryStems, 3))
    
    queryBigramsList = [tuple(row) for row in queryBigrams]
    queryBigramsFreq = Counter(queryBigramsList).most_common()
    queryTrigramsList = [tuple(row) for row in queryTrigrams]
    queryTrigramsFreq = Counter(queryTrigramsList).most_common()

    bigramIDsList, trigramIDsList = getBigramsTrigramsIDs(session, queryBigramsFreq, queryTrigramsFreq)

    # get the BM25 vector for the query as a numpy array
    queryVector = getBM25QueryVector(session, queryFreq, queryBigrams, queryTrigrams)

    # now to use the query vector to search the database with cosine similarity
    # we need to get the numResults most similar pages to the query

    # get the database information needed for the search
    databaseInfo = session.query(DatabaseInfo).first()
    numDocs = databaseInfo.num_docs
    numTerms = databaseInfo.num_terms

    # calculate the cosine similarity between the query vector and all document vectors
    docVectors = np.zeros((numDocs, numTerms))
    for i in range(numDocs):
        docID = i + 1
        doc = session.query(PageVectors).filter_by(page_id=docID).one()
        unPickledVector = pickle.loads(doc.weighted_vector)
        docVectors[i] = unPickledVector
    docSims = cosine_similarity(queryVector.reshape(1, -1), docVectors).flatten()

    # sort the document similarities in descending order and get the top numResults
    topDocIDs = np.argsort(docSims)[::-1][:numResults]
    topDocSims = docSims[topDocIDs]
    topPages = []
    for i in range(numResults):
        docID = topDocIDs[i] + 1
        page = session.query(Page).filter_by(id=docID).one()
        topPages.append((page.title, page.url, topDocSims[i]))

    return topPages

def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))

# function to get the bigram and trigram IDs for a given query - helper function for search
# takes in a numpy array of bigrams and trigrams from the ngrams function
def getBigramsTrigramsIDs(session, bigramsArray, trigramsArray):
    bigramsIDs = []
    trigramsIDs = []
    for i in range(len(bigramsArray)):
        term1, term2 = bigramsArray[i]
        term1_id = session.query(Term.term_id).filter_by(term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(term=term2).one().term_id
        bigramID = session.query(Bigram).filter_by(term1_id=term1_id, term2_id=term2_id).one().bigram_id
        bigramsIDs.append(bigramID)
    for i in range(len(trigramsArray)):
        term1, term2, term3 = trigramsArray[i]
        term1_id = session.query(Term.term_id).filter_by(term=term1).one().term_id
        term2_id = session.query(Term.term_id).filter_by(term=term2).one().term_id
        term3_id = session.query(Term.term_id).filter_by(term=term3).one().term_id
        trigramID = session.query(Trigram).filter_by(term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).one().trigram_id
        trigramsIDs.append(trigramID)
    return bigramsIDs, trigramsIDs

# Double Check the names used when adding to the database here, they may be off
# function to generate the bigrams and trigrams for a given page & add them to the database
def generateBigramsTrigrams(session, pageID):
    # Retrieve the term IDs and position lists for the page's content and title
    content_query = session.query(ContentTermPosition.term_id, ContentTermPosition.position_list).filter(ContentTermPosition.page_id == pageID)
    title_query = session.query(TitleTermPosition.term_id, TitleTermPosition.position_list).filter(TitleTermPosition.page_id == pageID)
    content_result = content_query.all()
    title_result = title_query.all()

    # Compute the position lists for the bigrams and trigrams in the content
    content_bigram_positions = {}
    content_trigram_positions = {}
    for positions in [pos for _, pos in content_result]:
        content_bigrams = list(ngrams(positions.split(','), 2))
        content_trigrams = list(ngrams(positions.split(','), 3))
        for bigram in content_bigrams:
            content_bigram_positions[bigram] = [int(pos) + 1 for pos in bigram]
        for trigram in content_trigrams:
            content_trigram_positions[trigram] = [int(pos) + 1 for pos in trigram]

    # Compute the position lists for the bigrams and trigrams in the title
    title_bigram_positions = {}
    title_trigram_positions = {}
    for positions in [pos for _, pos in title_result]:
        title_bigrams = list(ngrams(positions.split(','), 2))
        title_trigrams = list(ngrams(positions.split(','), 3))
        for bigram in title_bigrams:
            title_bigram_positions[bigram] = [int(pos) + 1 for pos in bigram]
        for trigram in title_trigrams:
            title_trigram_positions[trigram] = [int(pos) + 1 for pos in trigram]

    # Add the bigrams and trigrams to the database
    for bigram in set(list(content_bigram_positions.keys()) + list(title_bigram_positions.keys())):
        term1_id, term2_id = bigram
        # check if the bigram already exists in the database
        existing_bigram = session.query(Bigram).filter_by(term1_id=term1_id, term2_id=term2_id).first()
        if not existing_bigram:
            # create a new bigram and add it to the database
            new_bigram = Bigram(term1_id=term1_id, term2_id=term2_id)
            session.add(new_bigram)
            session.flush()

    for trigram in set(list(content_trigram_positions.keys()) + list(title_trigram_positions.keys())):
        term1_id, term2_id, term3_id = trigram
        # check if the trigram already exists in the database
        existing_trigram = session.query(Trigram).filter_by(term1_id=term1_id, term2_id=term2_id, term3_id=term3_id).first()
        if not existing_trigram:
            # create a new trigram and add it to the database
            new_trigram = Trigram(term1_id=term1_id, term2_id=term2_id, term3_id=term3_id)
            session.add(new_trigram)
            session.flush()

    # session closed outside for clarity

# creating an sqlachemcy database
def makeAlchemy():
    # create the session (replaces the connection and cursor)
    session = db.session

    # create the tables
    db.create_all()

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

        # inserting into the content term frequency table
        for stem, freq in contentFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTermFreq = ContentTermFrequency(page_id=pageID, term_id=termID, frequency=freq)
            session.add(newTermFreq)

        # inserting into the title term frequency table
        for stem, freq in titleFreq:
            termID = session.query(Term).filter_by(term=stem).one().term_id
            newTermFreq = TitleTermFrequency(page_id=pageID, term_id=termID, frequency=freq)
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
