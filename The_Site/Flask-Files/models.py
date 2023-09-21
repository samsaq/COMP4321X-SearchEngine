from sqlalchemy import Column, Integer, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Seperating out the database models from the actual script

Base = declarative_base()

# Defining the models for the database - several can likely be removed

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
class ParentLink(Base):
    __tablename__ = 'ParentLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    parent_page_id = Column(Integer, ForeignKey('Page.page_id'))

    page = relationship("Page", foreign_keys=[page_id])
    parent_page = relationship("Page", foreign_keys=[parent_page_id])

    def __init__(self, page_id, parent_page_id):
        self.page_id = page_id
        self.parent_page_id = parent_page_id

# define the ChildLink model
class ChildLink(Base):
    __tablename__ = 'ChildLink'

    link_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_page_id = Column(Integer, ForeignKey('Page.page_id'))
    child_url = Column(Text)

    page = relationship("Page", foreign_keys=[page_id])
    child_page = relationship("Page", foreign_keys=[child_page_id])

    def __init__(self, page_id, child_page_id, child_url):
        self.page_id = page_id
        self.child_page_id = child_page_id
        self.child_url = child_url

# define the Term model
class Term(Base):
    __tablename__ = 'Term'

    term_id = Column(Integer, primary_key=True)
    term = Column(Text)

    def __init__(self, term):
        self.term = term

# define the TitleTermFrequency model
class TitleTermFrequency(Base):
    __tablename__ = 'TitleTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = relationship("Page", foreign_keys=[page_id])
    term = relationship("Term", foreign_keys=[term_id])

    def __init__(self, page_id, term_id, frequency):
        self.page_id = page_id
        self.term_id = term_id
        self.frequency = frequency

# define the ContentTermFrequency model
class ContentTermFrequency(Base):
    __tablename__ = 'ContentTermFrequency'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    frequency = Column(Integer)

    page = relationship("Page", foreign_keys=[page_id])
    term = relationship("Term", foreign_keys=[term_id])

    def __init__(self, page_id, term_id, frequency):
        self.page_id = page_id
        self.term_id = term_id
        self.frequency = frequency

# define the TitleTermPosition model
class TitleTermPosition(Base):
    __tablename__ = 'TitleTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = relationship("Page", foreign_keys=[page_id])
    term = relationship("Term", foreign_keys=[term_id])

    def __init__(self, page_id, term_id, position_list):
        self.page_id = page_id
        self.term_id = term_id
        self.position_list = position_list

# define the ContentTermPosition model
class ContentTermPosition(Base):
    __tablename__ = 'ContentTermPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    position_list = Column(Text)

    page = relationship("Page", foreign_keys=[page_id])
    term = relationship("Term", foreign_keys=[term_id])

    def __init__(self, page_id, term_id, position_list):
        self.page_id = page_id
        self.term_id = term_id
        self.position_list = position_list

# define the TitleIndex model
class TitleIndex(Base):
    __tablename__ = 'TitleIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = relationship("Term", foreign_keys=[term_id])
    page = relationship("Page", foreign_keys=[page_id])

    def __init__(self, term_id, page_id):
        self.term_id = term_id
        self.page_id = page_id

# define the ContentIndex model
class ContentIndex(Base):
    __tablename__ = 'ContentIndex'

    term_id = Column(Integer, ForeignKey('Term.term_id'), primary_key=True)
    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)

    term = relationship("Term", foreign_keys=[term_id])
    page = relationship("Page", foreign_keys=[page_id])

    def __init__(self, term_id, page_id):
        self.term_id = term_id
        self.page_id = page_id

# define the Bigram model
class Bigram(Base):
    __tablename__ = 'Bigram'

    bigram_id = Column(Integer, primary_key=True)
    term1_id = Column(Integer, ForeignKey('Term.term_id'))
    term2_id = Column(Integer, ForeignKey('Term.term_id'))

    term1 = relationship("Term", foreign_keys=[term1_id])
    term2 = relationship("Term", foreign_keys=[term2_id])

class TitleBigramIndex(Base):
    __tablename__ = 'TitleBigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    bigram_id = Column(Integer, ForeignKey('Bigram.bigram_id'), primary_key=True)

    page = relationship("Page", foreign_keys=[page_id])
    bigram = relationship("Bigram", foreign_keys=[bigram_id])

    def __init__(self, page_id, bigram_id):
        self.page_id = page_id
        self.bigram_id = bigram_id

# define the ContentBigramPosition model
class ContentBigramIndex(Base):
    __tablename__ = 'ContentBigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    bigram_id = Column(Integer, ForeignKey('Bigram.bigram_id'), primary_key=True)

    page = relationship("Page", foreign_keys=[page_id])
    bigram = relationship("Bigram", foreign_keys=[bigram_id])

    def __init__(self, page_id, bigram_id):
        self.page_id = page_id
        self.bigram_id = bigram_id

# define the Trigram model
class Trigram(Base):
    __tablename__ = 'Trigram'

    trigram_id = Column(Integer, primary_key=True)
    term1_id = Column(Integer, ForeignKey('Term.term_id'))
    term2_id = Column(Integer, ForeignKey('Term.term_id'))
    term3_id = Column(Integer, ForeignKey('Term.term_id'))

    term1 = relationship("Term", foreign_keys=[term1_id])
    term2 = relationship("Term", foreign_keys=[term2_id])
    term3 = relationship("Term", foreign_keys=[term3_id])

# define the TitleTrigramPosition model
class TitleTrigramIndex(Base):
    __tablename__ = 'TitleTrigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    trigram_id = Column(Integer, ForeignKey('Trigram.trigram_id'), primary_key=True)

    page = relationship("Page", foreign_keys=[page_id])
    trigram = relationship("Trigram", foreign_keys=[trigram_id])

    def __init__(self, page_id, trigram_id):
        self.page_id = page_id
        self.trigram_id = trigram_id

# define the ContentTrigramPosition model
class ContentTrigramIndex(Base):
    __tablename__ = 'ContentTrigramPosition'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    trigram_id = Column(Integer, ForeignKey('Trigram.trigram_id'), primary_key=True)
    position_list = Column(Text)
    frequency = Column(Integer)

    page = relationship("Page", foreign_keys=[page_id])
    trigram = relationship("Trigram", foreign_keys=[trigram_id])

    def __init__(self, page_id, trigram_id):
        self.page_id = page_id
        self.trigram_id = trigram_id

# define the model for the PageVectors table
class PageVectors(Base):
    __tablename__ = 'PageVectors'

    page_id = Column(Integer, ForeignKey('Page.page_id'), primary_key=True)
    title_vector = Column(JSON, nullable=False)
    content_vector = Column(JSON, nullable=False)
    weighted_vector = Column(JSON, nullable=False)

    page = relationship("Page", foreign_keys=[page_id])

    def __init__(self, page_id, title_vector, content_vector, weighted_vector):
        self.page_id = page_id
        self.title_vector = title_vector
        self.content_vector = content_vector
        self.weighted_vector = weighted_vector

# define the model for overall database information
class DatabaseInfo(Base):
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
