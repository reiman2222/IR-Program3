#Tyler Rodgers, Chase Moore, Jack Edwards

import re
import math
import porter

#a Document object represents a document in the cran collection.
class Document:
    def __init__(self):
        self.author    = ''
        self.title     = ''
        self.body_text = ''
        self.number = -1

    # Creates document object
    @staticmethod
    def buildDocument(initAuth, initTitle, initBody, num):
        d = Document()
        d.author    = initAuth
        d.title     = initTitle
        d.body_text = initBody
        d.number    = num
        return d

#END CLASS

#an Index is a two tiered inverted index with tier1 as an
#inverted index on the titles a Documents and tier2 
#as and inverted index on the body text of Documents.
class Index:
    def __init__(self):
        self.tier1 = {}
        self.tier2 = {}
        self.numDocuments = -1
    
    #createIndex creates an Index.
    @staticmethod
    def createIndex():
        index = Index()
        index.numDocuments = 0
        return index
	
    #populate adds all terms in list of Documents docList to the index self.
    def populateIndex(self, docList):
        for doc in docList:
            self.updateIndex(self.tier1, doc.title, doc.number)
            self.updateIndex(self.tier2, doc.body_text, doc.number)
            self.numDocuments += 1
			
    #updateIndex adds all terms in string content to tier tier of Index self.
    #docID is the documents ID of the doument whoes content is being indexed.
    def updateIndex(self, tier, content, docID):
        wordList = content.split()
        for word in wordList:
            token = tokenize(word)
            
            if token != '':
                if token in tier:
                    wasInTier = False
                    for t in tier[token]:
                        if(t.termStr == token):
                            wasInTier = True
                            termList = t
                            lastDocTuple = t.getLast()
                
                            if(lastDocTuple[0] == docID):
                                termList.incLastTF()
                            else:
                                termList.addDoc(docID)
                                termList.incDocFreq()
                    if(wasInTier == False):
                        t.append = Term.buildTerm(token, docID)
                    
                else:
                    tier[token] = []
                    tier[token].append(Term.buildTerm(token, docID))
                
    #tfxidf computes the tf-idf of term term in document number docnum
    #with respect to tier tier.
    def tfxidf(self, term, docnum, tier):
        tf  = -1
        df  = -1
        idf = -1
        termObject = None

        if term in tier:
            inDoc = False
            for t in tier[term]:
                if(t.termStr == term):
                    termObject = t
                    for tup in t.docList:
                        if tup[0] == docnum:
                            tf = tup[1]
                            inDoc = True
                            break
                if(not inDoc):
                    return 0
        else: 
            return 0
        
        df = termObject.documentFrequency
        idf = math.log(self.numDocuments / df)

        return math.log(1 + tf) * idf
    
    #computeSimilarity computes the similarity between list of terms
    #query and document number docnum in tier tier of the Index self.            
    def computeSimilarity(self, query, docnum, tier):
        query_vector = []
        doc_vector   = []
        
        for term in query:
            query_vector.append(1)
            doc_vector.append(self.tfxidf(term, docnum, tier))
        
        return dotProduct(query_vector, doc_vector) / (len(query_vector) * 2)
        
#END CLASS

#a Term represents an entry in a tier of a Index.
#Terms contain termStr the term the Term object represents stored as a string,
#documentFrequency the document frequency of the term,
#and docList a list of tuples of the form (docID, term frequency) to record the
#term frequency of the term in each document.
class Term:
    def __init__(self):
        self.termStr = ''
        self.documentFrequency = -1
        self.docList = [] #list of tuples of the form (docID, term frequency)
    
    #buildTerm returns a Term object for term t as a string where the first
    #occurence of term t is in document number docID.
    @staticmethod
    def buildTerm(t, docID):
        term = Term()
        term.termStr = t
        term.documentFrequency = 1
        term.docList.append((docID, 1))
        return term
        
    #getLast returns the last docID term frequency tuple in the Term self.
    def getLast(self):
        return self.docList[len(self.docList) - 1]
    
    #incLastTF increments the term frequency of the last
    #docID term frequency tuple in the Term self.
    def incLastTF(self):
        last = self.getLast()
        self.docList[len(self.docList) - 1] = (last[0], last[1] + 1)
        
    #addDoc creates a new docID term frequency tuple and appends it to the
    #docList of Term self. the term frequency of the tuple is set to 1.
    def addDoc(self, docID):
        self.docList.append((docID, 1))
        
    #incDocFreq increments the document frequency of Term self.   
    def incDocFreq(self):
        self.documentFrequency += 1
	    
#END CLASS        

#tokenize(word) tokenizes a string. 
#word is the string to tokenize.
def tokenize(word):
    regex = re.compile('[^a-zA-Z]+')
    w = regex.sub('', word)
    w = w.lower()
    w = porter.stem(w)
    return w

#getRawText returns the contents of file filename.
def getRawText(filename):
    f = open(filename, 'r')
    fileText = f.read()
    return fileText

#parseCorpus returns a list of Documetns representing each document
#in the cran corpus. courpus is the cran corpus as a sting.
def parseCorpus(corpus):
    docList = []
    docs = []
    #corpus split on entries
    re_entry = re.compile("\.I ")
    docs = re.split(re_entry, corpus)

    del(docs[0])
    #getArticleInformation(docs[0])

    for entry in docs:
        docList.append(getArticleInformation(entry))

    return docList

#dotProduct returns the dot product of vectors(list of numbers) a and b.
#dotProduct expects len(a) == len(b).
def dotProduct(a, b):
    total = 0
    for i in range(0, len(a)):
        total += (a[i] * b[i])
    return total
    
#getArticleInformation returns a Document object generated from string unprocessedDocs.
def getArticleInformation(unprocessedDocs):
    doc_buster = re.compile("\.[A-Z]\n")
    doc_attributes = re.split(doc_buster, unprocessedDocs)

    # build a document using the relevant information and return it
    return Document.buildDocument(doc_attributes[2],doc_attributes[1],doc_attributes[4],int(doc_attributes[0]))

#doQuery returns a list document numbers where
#the top k documents are selected are returned and sorted
#based on there similatry to query q. index is the tiered index
#to run the query against. 
def doQuery(query, index, k):
    q = query.split()
    
    #tokenize query
    j = 0
    while(j < len(q)):
        token = tokenize(q[j])
        if(token == ''):
            del q[j]
            j -= 1
        else:
            q[j] = porter.stem(token)
            j += 1
    
    #tier1sim is list of tuples of the form (docID, similarity) 
    #similarity is the similarity between document number docID and query q.
    tier1Sim = []
    
    i = 0
    while(i < index.numDocuments):
        tier1Sim.append((i + 1, index.computeSimilarity(q, i + 1, index.tier1)))
        i += 1
        
    sortedSim = sorted(tier1Sim, key = lambda tup: tup[1], reverse = True)
    
    sortedSim = sortedSim[0:k]
    simTier2 = []
    
    i = 0
    while(i < len(sortedSim)):
        docID = sortedSim[i][0]
        simTier2.append((docID, index.computeSimilarity(q, docID, index.tier2)))
        i += 1
        
    resultListTups = sorted(simTier2, key = lambda tup: tup[1], reverse = True)
    
    resultList = []
    i = 0
    while(i < len(resultListTups)):
        resultList.append(resultListTups[i][0])
        i += 1
    
    return resultList

#showResults prints the titles and document numbers of all entries 
#in list of tuples results. results is a list of document numbers.
#docList is thelist of documents that holds the title and document
#number information.
def showResults(results, docList):
    print('The results for your query are:\n')
    
    i = 0
    while(i < len(results)):
        print('Document number: ' + str(results[i]))
        print(docList[results[i] - 1].title)
        i += 1
        
    print('\n')

#######################################
#                MAIN                 #
#######################################

#read corpus and generate a list of files
theFile = getRawText('corpus/cran.all.1400')
docList = parseCorpus(theFile)

k = -1 #top k results the user would like to see

#create tiered index
index = Index.createIndex()
index.populateIndex(docList)

print('Documents indexed.\n')

#get k for top k retreival
print('Enter an integer for top k results you would like to see.')
k = int(input())


print('\nEnter a query or type -stop to stop\n')

#get user input
continueQuerying = True
while(continueQuerying):
    usrQuery = input()
    
    if(usrQuery == '-stop'):
        break
        
    results = doQuery(usrQuery, index, k)
    showResults(results, docList)
    
    print('Enter a query or type -stop to stop\n')
    
print('\nexiting')
    
