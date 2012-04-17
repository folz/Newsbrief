from pprint import pprint

import feedparser
from numpy import *

import re
import time

from py4j.java_gateway import JavaGateway

SUMMARY_URL = 'http://www.bookkle.com/web/guest/api'

national_news = [
      'http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml'
    , 'http://www.npr.org/rss/rss.php?id=1003'
    , 'http://www.npr.org/rss/rss.php?id=1014'
    , 'http://feeds.washingtonpost.com/rss/national'
    , 'http://feeds.latimes.com/latimes/news/nationworld/nation'
    , 'http://feeds.latimes.com/latimes/news/politics/'
]

gateway = JavaGateway()

def get_article_content(url):
    return gateway.entry_point.getText(url)

def get_text(url):
    return get_article_content(url)

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
    for feedurl in feedlist:
        f = feedparser.parse(feedurl)

        for e in f.entries:
            print e
            if e in articletitles: continue

            txt = get_text(e.link)
            words = get_words(txt)

            articlewords.append({})
            articletitles.append(e.title)
            articletext[e.title] = txt

            for word in words:
                allwords.setdefault(word, 0)
                allwords[word]+=1
                articlewords[ec].setdefault(word, 0)
                articlewords[ec][word]+=1
            ec += 1
            time.sleep(.25)
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

if __name__ == "__main__":
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