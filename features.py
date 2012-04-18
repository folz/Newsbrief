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

            text = get_text(entry.link)
            words = get_words(text)

            article = Article(entry=entry, text=text, words=words)
            print article.entry.title, article.entry.link
            articles.put(article)

            self.downloads.task_done()

def get_text(url):
    return gateway.entry_point.getText(url)

def get_words(text):
    return map(clean_word, text.replace("\n", " ").split(" "))

def clean_word(word):
    if word.endswith((":", ",", ";")):
        word = word[:-1]

    return word.lower()

def get_articles(feedlist):
    allwords = {}
    articlewords = []
    articletitles = []
    articletext = {}
    ec = 0
    for i in range(5):
        t = EntryDownloader(downloads)
        t.setDaemon(True)
        t.start()

    for feedurl in national_news:
        f = feedparser.parse(feedurl)
        for e in f.entries:
            downloads.put(e)

    downloads.join()

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
    return gateway.entry_point.getSummary(text, sentences)

def main():
    print "init"
    allw, artw, artt, arttxt = get_articles(national_news)

    print "makematrix"
    wordmatrix, wordvec = makematrix(allw, artw)

    v = matrix(wordmatrix)
    print "factorize"
    weights, feat = factorize(v, pc=20, iter=50)

    print "features"
    clusters = showfeatures(weights, feat, artt, wordvec, out="national_news.txt")

    summaries = {}

    print "summarise"
    for key, val in clusters.items():
        summaries[key] = summarise(arttxt[val[0][1]], 20)

    print "Summaries!"
    with open("summaries.txt", 'w') as summariesfile:
        for key, val in summaries.items():
            writablekey = unicode(key).encode('utf-8')
            writableval = unicode(val).encode('utf-8')
            summariesfile.write(writablekey + '\n')
            summariesfile.write(writableval + '\n')
            summariesfile.write('\n')

if __name__ == "__main__":
    main()
