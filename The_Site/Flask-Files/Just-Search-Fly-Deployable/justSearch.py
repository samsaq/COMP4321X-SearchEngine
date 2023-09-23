import os
import re
import numpy as np
import json
from nltk.stem import PorterStemmer
from collections import Counter
from flask import Flask, jsonify
from flask_cors import CORS
from math import log
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from numpy import dot
from numpy.linalg import norm
from models import Page, PageVectors, Term, Bigram, Trigram, ChildLink, TitleIndex, ContentIndex, ContentTermFrequency, TitleBigramIndex, ContentBigramIndex, TitleTrigramIndex, ContentTrigramIndex, DatabaseInfo
from flask_talisman import Talisman

# a flask api to handle the searching of the database

# these are global variables
debug = False

# initializations
app = Flask(__name__)
Talisman(app, content_security_policy=None)
app.debug = debug
CORS(app)  # for cross-origin requests

# stopword list, imported from a .txt file
stopwords = []
with open('stopwords.txt', 'r') as f:
    for line in f:
        stopwords.append(line.strip())

db_path = os.path.abspath("spidey.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

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

# function to search based off of the given query


# alt route to allow for default number of results
@app.route('/api/search/<query>', defaults={'numResults': 50})
@app.route('/api/search/<query>/<int:numResults>/')
def search(query="test", numResults=50):
    with app.app_context():
        # check that the query is not empty and not just whitespace
        if query == None or query.isspace():
            return jsonify({'status': 'error', 'message': 'Empty query'}), 400

        session = db.session  # double check if this is the correct session
        # preprocess the query string for the search
        queryTokens = re.findall(r'\b\w+\b', query.lower())
        # remove stopwords from the query
        queryTokens = [
            token for token in queryTokens if token not in stopwords]
        # stem the query
        ps = PorterStemmer()

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
            phraseTokens = [
                token for token in phraseTokens if token not in stopwords]
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
            unPickledVector = json.loads(doc.weighted_vector)
            docVectors[i] = unPickledVector
            docSims.append((docID,  cosineSimilarity(
                queryVector, unPickledVector).flatten()[0]))

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
                        # we can check both TitleTrigramIndex and ContentTrigramIndex beacuse if its in one its in the document
                        if session.query(TitleTrigramIndex).filter_by(page_id=docID, trigram_id=trigramID).count() == 0 and session.query(ContentTrigramIndex).filter_by(page_id=docID, trigram_id=trigramID).count() == 0:
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
                        # we can check both TitleBigramIndex and ContentBigramIndex beacuse if its in one its in the document
                        if session.query(TitleBigramIndex).filter_by(page_id=docID, bigram_id=bigramID).count() == 0 and session.query(ContentBigramIndex).filter_by(page_id=docID, bigram_id=bigramID).count() == 0:
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
        topKeywords = [(str(keyword[0]), int(keyword[1]))
                       for keyword in topKeywords]

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


# debugging execution
if debug:
    testSearchQuery = 'Movies are great "Dog Cat""'
    print(search(testSearchQuery))
if (not debug and __name__ == '__main__'):
    app.run()
