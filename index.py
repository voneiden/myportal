#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
import cgitb
import wsgiref.util
import cPickle as pickle
import os
import email.feedparser
import email.utils
import re
import time
import random

class Home:
    def __init__(self,db):
        buffer = []
        self.varfinder = re.compile('\$\(.+?\)')
        self.db = db
        request = os.environ['REQUEST_URI']
        if ".." in request: 
            print "Status: 403 FORBIDDEN"
            print
        
        
        self.vars = {
        'page_title':'I hate titles.',
        'quote':'lol, inter'}
        
        if "/pictures" in request:
            buffer = self.displayPictures(request)
            if buffer: print "\n".join(buffer)
            
       
            
        else:
            path = request.replace('/cgi-bin/index.py','')
            if len(path) > 0:
                if path[0] == '/': path = path[1:]
            
            if len(path) == 0:
            
                self.head = self.load('style/head.html')
                self.post = self.load('style/post.html')
                self.foot = self.load('style/foot.html')
                
                
                self.articles = self.db.articles.keys()
                self.articles.sort(self.sort)
                
                # Handle request here
                buffer = self.displayPosts()
                print "\n".join(buffer)
                
            
                
            elif ".txt" in path:
                path = path.replace("content/blog","articles/archive")
                path = path.replace(".txt",".html")
                print "Status: 301 MOVED PERMANENTLY"
                print "Location: http://www.eiden.fi/cgi-bin/index.py/%s"%path
                print
                
            else:
                if '.html' in path:
                    self.head = self.load('style/head.html')
                    self.post = self.load('style/post.html')
                    self.foot = self.load('style/foot.html')
                    
                    
                    apath = path.replace('.html','.txt')
                    apath = "./%s"%apath
     
                    if apath in self.db.articles.keys():
                        article = self.db.articles[apath]
                        self.vars.update(article)
                        date = time.gmtime(article['date'])
                        self.vars['date'] = time.strftime("%B %d, %Y.",date)

                        buffer = []
                        buffer.append('Content-type: text/html; charset=UTF-8')
                        buffer.append('')
                        buffer.append(self.fill(self.head))
                        buffer.append(self.fill(self.post))
                        buffer.append(self.fill(self.foot))
                        
                        print "\n".join(buffer)
                        
                    else:
                        print "Status: 404 NOT FOUND"
                        print
                        
                else:
                    print "Status: 404 NOT FOUND"
                    print
                    
         

        
    def load(self,path):
        f = open(path,'r')
        x = f.read()
        f.close()
        return x
    
    def displayPosts(self,start=0):
        buffer = []
        buffer.append('Content-type: text/html; charset=UTF-8')
        buffer.append('')
        buffer.append(self.fill(self.head))
        
        for path in self.articles[:5]:
            article = self.db.articles[path]
            self.vars.update(article)
            date = time.gmtime(article['date'])

            self.vars['date'] = time.strftime("%B %d, %Y.",date)
            stream = self.fill(self.post)
            buffer.append(stream)
            
        buffer.append(self.fill(self.foot))
        return buffer
         

    def displayPictures(self,request):
        path = request.replace('/cgi-bin/index.py/','')
        
        if '.jpg' in request or ".png" in request:
            if os.access(path,os.F_OK):
                if '.jpg' in request: print "Content-type: image/jpeg"
                else: print "Content-type: image/png"
                print
                f = open(path,'rb')
                x = f.read()
                f.close()
                print x
            else:
                print "Status: 404"
                print

        
        elif '.html' in request:
            jpg = path.replace('.html','.jpg')
            png = path.replace('.html','.png')
            
            if   os.access(jpg,os.F_OK): image = jpg
            elif os.access(png,os.F_OK): image = png
            else: image = False
            
            if image:
                print "Content-type: text/html"
                print                
                self.head = self.load('style/head.html')
                self.post = self.load('style/post-nometa.html')
                self.foot = self.load('style/foot.html')
                
                buffer = []
                buffer.append(self.fill(self.head))
                self.vars['body'] = '''<a href="http://www.eiden.fi/cgi-bin/index.py/%s"><img src="http://www.eiden.fi/cgi-bin/index.py/%s" alt="%s"></a>'''%(image,image,image)
                buffer.append(self.fill(self.post))
                buffer.append(self.fill(self.foot))
                return buffer
                
                
            else:
                print "Status: 404 NOT FOUND"
                print
                
        else:
            self.head = self.load('style/head.html')
            self.post = self.load('style/post-nometa.html')
            self.thumbnail = self.load('style/post-thumbnail.html')
            self.foot = self.load('style/foot.html')
            #print "Content-type: text/plain"
            #print
            #print "Testing"
            #print "List pictures.."
            
            #TODO: CLEAN THIS FOR GODS SAKE
            if os.access(path,os.F_OK):
                print "Content-type: text/html"
                print 
                
                buffer = []
                buffer.append(self.fill(self.head))
                buffer.append("<table><tr>")
                walker = os.walk(path)
                fpath,dirs,files = walker.next()
                for i,dir in enumerate(dirs):
                    self.vars['body'] = dir
                    #if i % 5 == 0 : self.vars['thumbnail'] = 'thumbleft';buffer.append("<br>")
                    #else: self.vars['thumbnail'] = 'thumbright'
                    if i %5 == 0 and i != 0: buffer.append("</tr><tr>")
                    
                    choices = []
                    print "Checking","%s/%s"%(fpath,dir)
                    for subpath,subdirs,subfiles in os.walk("%s/%s"%(fpath,dir)):
                        for file in subfiles:
                            if ".jpg" in file.lower() or ".png" in file.lower():
                                if 'thumb' not in file and 'medium' not in file and "comment" not in file:
                                    choices.append("%s/%s"%(subpath,file))
                    self.vars['body'] = "%i pics"%(len(choices))
                    
                    if len(choices) > 0:
                        picture = random.choice(choices)
                        picture = picture.replace('.jpg','_thumb.jpg')
                        picture = picture.replace('.png','_thumb.png')
                        self.vars['body'] = '''<img src="http://www.eiden.fi/cgi-bin/index.py/%s" alt="none">'''%(picture)
                        self.vars['body'] = '''<a href="http://www.eiden.fi/cgi-bin/index.py/%s/%s">%s</a>'''%(fpath,dir,self.vars['body'])
                    buffer.append("<td><center>%s</center><br/>%s</td>"%(dir,self.fill(self.post)))
                    
                    #buffer.append(self.fill(self.thumbnail))
                buffer.append("</tr></table>")
                
                    
                buffer.append("<table><tr>")
                i = 0
                for file in files:
                    if ".jpg" not in file and ".png" not in file: continue
                    if 'thumb' in file or 'medium' in file or "comment" in file: continue
                    if i %5 == 0 and i != 0: buffer.append("</tr><tr>")
                    picture = "%s/%s"%(fpath,file)
                    picture = picture.replace('.jpg','_thumb.jpg')
                    picture = picture.replace('.png','_thumb.png')
                    file= file.replace('.jpg','.html')
                    file= file.replace('.png','.html')
                    self.vars['body'] = '''<img src="http://www.eiden.fi/cgi-bin/index.py/%s" alt="none">'''%(picture)
                    self.vars['body'] = '''<a href="http://www.eiden.fi/cgi-bin/index.py/%s/%s">%s</a>'''%(fpath,file,self.vars['body'])
                    buffer.append("<td>%s<br/><center>%s</center></td>"%(self.fill(self.post),".".join(file.split('.')[:-1])))
                    i += 1
                buffer.append(self.fill(self.foot))
                print "\n".join(buffer)
                
            else:
                print "Status: 404 NOT FOUND"
                print
                
        
    def fill(self,stream):
        for match in re.finditer(self.varfinder,stream):
            var = match.group()
            name = var[2:-1]
            #print "Checking var",name,vars
            if name not in self.vars: stream = stream.replace(var,'(variable missing)',1)
            else: stream = stream.replace(var,str(self.vars[name]),1)
        
        return stream
    def sort(self,a1,a2):
        a1 = self.db.articles[a1]
        a2 = self.db.articles[a2]
        if a1['date'] < a2['date']: return 1
        elif a1['date'] > a2['date']: return -1
        else: return 0
        



class Database:
    def __init__(self):
        self.load()
        
    def load(self):
        add   = 0
        rem   = 0
        mod   = 0
        # First load old article databse
        try: 
            f = open('articles.db','rb')
            self.articles = pickle.load(f)
            f.close()
        except IOError: self.articles = {}
        
        # Then scan for articles
        articles = []
        for path,folders,files in os.walk('./articles'):
            path = path.replace('\\','/')
            for file in files:
                if '.txt' in file:
                    articles.append("%s/%s"%(path,file))
                    
        # Check if there are articles that exist no more
        for article in self.articles.keys():
            if article not in articles: 
                del self.articles[article]
                rem += 1
            
        # Finally add missing articles!
        for article in articles:
            mtime = os.stat(article)[8]
            if article not in self.articles.keys():
                add += 1
                self.load_article(article,mtime)
            else:
                if mtime != self.articles[article]['mtime']:
                    mod += 1
                    self.load_article(article,mtime)

        #print "%i articles added, %i articles removed and %i articles modified."%(add,rem,mod)
        #print "Total %i articles loaded"%len(self.articles)
        if add or rem or mod:
            self.save()
            
    def save(self):
        f = open('articles.db','wb')
        pickle.dump(self.articles,f)
        f.close()
        #print "Saved"
    def load_article(self,article,mtime):
        f = open(article,'r')
        contents = f.read()
        f.close()
        parser = email.feedparser.FeedParser()
        parser.feed(contents)
        parsed = parser.close()
        
        author = parsed['From']
        date   = parsed['Date']
        subject = parsed['Subject']
        body    = parsed.get_payload()
        
        #Todo this fails with TypeError if the date is not OK
        date = email.utils.mktime_tz(email.utils.parsedate_tz(date))
        
        message = {'author':author,'date':date,'subject':subject,'body':body,'mtime':mtime}
        
        self.articles[article] = message

#if __name__ == '__main__':

cgitb.enable(1,'./logs',5,'html')
db = Database()
home = Home(db)
    