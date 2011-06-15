import cgi
import cgitb
import cPickle as pickle
import os
import email.feedparser
import email.utils
import re

class Home:
    def __init__(self,db):
        buffer = []
        self.varfinder = re.compile('\$\(.+?\)')
        self.db = db
        
        vars = {
        'page_title':'This is a cool test.'}
        
        
        f = open('style/head.html','r')
        x = f.read()
        f.close()
        
        stream = self.fill(x,vars)
        buffer.append(stream)
        
        f = open('style/post.html','r')
        x = f.read()
        f.close()
        
        for path,article in self.db.articles.items():
            vars.update(article)
            stream = self.fill(x,vars)
            buffer.append(stream)
         

        f = open('style/foot.html','r')
        x = f.read()
        f.close()
         
        buffer.append(x)
        
        f = open('style/output.html','w')
        f.write("\n".join(buffer))
        f.close()
        print "Done."
    def fill(self,stream,vars):
        for match in re.finditer(self.varfinder,stream):
            var = match.group()
            name = var[2:-1]
            print "Checking var",name,vars
            if name not in vars: stream = stream.replace(var,'(variable missing)',1)
            else: stream = stream.replace(var,str(vars[name]),1)
        
        return stream




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

        print "%i articles added, %i articles removed and %i articles modified."%(add,rem,mod)
        print "Total %i articles loaded"%len(self.articles)
        if add or rem or mod:
            self.save()
            
    def save(self):
        f = open('articles.db','wb')
        pickle.dump(self.articles,f)
        f.close()
        print "Saved"
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

if __name__ == '__main__':
    cgitb.enable(1,'./logs',5,'text')
    db = Database()
    home = Home(db)
    