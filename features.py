import feedparser
from numpy import *

import Queue
import threading

from py4j.java_gateway import JavaGateway

national_news = [
      'http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml'
    , 'http://www.npr.org/rss/rss.php?id=1003'
    , 'http://feeds.washingtonpost.com/rss/national'
    , 'http://feeds.latimes.com/latimes/news/nationworld/nation'
    , 'http://english.aljazeera.net/Services/Rss/?PostingId=200772115196613309'
    , 'http://rss.cnn.com/rss/cnn_us.rss'
]

world_news = [
      'http://feeds.bbci.co.uk/news/world/rss.xml'
    , 'http://www.npr.org/rss/rss.php?id=1004'
    , 'http://feeds.washingtonpost.com/rss/world'
    , 'http://feeds.washingtonpost.com/rss/world'
    , 'http://www.aljazeera.com/Services/Rss/?PostingId=2007731105943979989'
    , 'http://rss.cnn.com/rss/edition_world.rss'
]

gateway = JavaGateway()

downloads = Queue.Queue()
articles = Queue.Queue()

class Article:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class EntryDownloader(threading.Thread):
    def __init__(self, downloads):
        threading.Thread.__init__(self)
        self.downloads = downloads

    def run(self):
        while True:
            entry = self.downloads.get()

            text = get_article_content(entry.link)
            words = get_words(text)

            article = Article(entry=entry, text=text, words=words)
            print article.entry.title, article.entry.link
            articles.put(article)

            self.downloads.task_done()

def get_article_content(url):
    ''' Finds the textual article content in an HTML page. '''

    return gateway.entry_point.getText(url)

def get_words(text):
    ''' Returns a list of all words in a string. '''

    return map(clean_word, text.replace("\n", " ").split(" "))

def clean_word(word):
    ''' Takes a possible word and tries to make it a word. '''

    if word.endswith((":", ",", ";")):
        word = word[:-1]

    return word.lower()

def get_articles(feedlist):
    # Start five download daemons
    for i in range(5):
        t = EntryDownloader(downloads)
        t.setDaemon(True)
        t.start()

    # Add the RSS entries to the download queue, ready to be downloaded
    for feedurl in feedlist:
        f = feedparser.parse(feedurl)
        for e in f.entries:
            downloads.put(e)

    # By now, the download daemons should be grabbing the articles. Block until
    # the downloads queue is empty; i.e. there are no more articles to download.
    downloads.join()

def analyze_articles(articles):
    allwords = {}
    articlewords = []
    articletitles = []
    articletext = {}
    ec = 0

    # But analyze them sequentially for now
    while not articles.empty():
        article = articles.get()

        if article.entry.title not in articletitles:
            articlewords.append({})
            articletitles.append(article.entry.title)
            articletext[article.entry.title] = article.text

            for word in article.words:
                allwords.setdefault(word, 0)
                allwords[word]+=1
                articlewords[ec].setdefault(word, 0)
                articlewords[ec][word]+=1
            ec +=1
        articles.task_done()

    return allwords, articlewords, articletitles, articletext

def makematrix(allw, articlew):
    wordvec = []

    for word, count in allw.items():
        if count > 3 and count < len(articlew)*0.6:
            wordvec.append(word)

    l1 = [[(word in f and f[word] or 0) for word in wordvec] for f in articlew]
    return l1, wordvec

def difcost(a, b):
    dif = 0
    for i in range(shape(a)[0]):
        for j in range(shape(a)[1]):
            dif+=pow(a[i,j]-b[i,j],2)
    return dif

def factorize(v, pc=10, iter=50):
    ic=shape(v)[0]
    fc=shape(v)[1]

    w = matrix([[random.random() for j in range(pc)] for i in range(ic)])
    h = matrix([[random.random() for j in range(fc)] for i in range(pc)])

    for i in range(iter):
        wh = w*h

        cost = difcost(v, wh)

        if i % 10 == 0: print cost

        if cost == 0: break

        hn = (transpose(w)*v)
        hd = (transpose(w)*w*h)

        h = matrix(array(h)*array(hn)/array(hd))

        wn = (v*transpose(h))
        wd = (w*h*transpose(h))

        w = matrix(array(w)*array(wn)/array(wd))

    return w, h

def showfeatures(w, h, titles, wordvec, out="features.txt"):
    with open(out, "w") as outfile:
        pc, wc = shape(h)
        toppatterns=[[] for i in range(len(titles))]
        patternnames=[]
        clusters = {}

        for i in range(pc):
            slist = []
            for j in range(wc):
                slist.append((h[i,j], wordvec[j]))
            slist.sort()
            slist.reverse()

            n = [s[1] for s in slist[0:6]]
            outfile.write(str(n)+'\n')
            clusters[tuple(n)] = []
            patternnames.append(n)

            flist = []
            for j in range(len(titles)):
                flist.append((w[j,i], titles[j]))
                toppatterns[j].append((w[j,i], i, titles[j]))

            flist.sort()
            flist.reverse()

            for f in flist[0:3]:
                clusters[tuple(n)].append(f)
                outfile.write(str(f)+'\n')
            outfile.write('\n')
    return clusters

def summarise(text, sentences):
    ''' Summarise a body of text in some number of sentences. '''
    return gateway.entry_point.getSummary(text, sentences)

def main(name, feeds):
    print "downloading"
    get_articles(feeds)

    print "analyzing"
    allw, artw, artt, arttxt = analyze_articles(articles)

    print "matrixizing"
    wordmatrix, wordvec = makematrix(allw, artw)
    v = matrix(wordmatrix)

    print "factorizing"
    weights, feat = factorize(v, pc=20, iter=50)

    print "featurizing"
    clusters = showfeatures(weights, feat, artt, wordvec, out="{0}_news.txt".format(name))

    summaries = {}

    print "summarising" # haha, British
    for key, val in clusters.items():
        summaries[key] = summarise(arttxt[val[0][1]], 20)

    print "finalizing"
    with open("{0}_summaries.txt".format(name), 'w') as summariesfile:
        for key, val in summaries.items():
            writablekey = unicode(key).encode('utf-8')
            writableval = unicode(val).encode('utf-8')
            summariesfile.write(writablekey + '\n')
            summariesfile.write(writableval + '\n')
            summariesfile.write('\n')

if __name__ == "__main__":
    main("national", national_news)
    main("world", world_news)
