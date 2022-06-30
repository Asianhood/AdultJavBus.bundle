import ssl
import urllib2
import json
from lxml import html
import re, time
from dateutil.parser import parse
import datetime
import random
import SearchStudio


# preferences
preference = Prefs
DEBUG = preference['debug']
if DEBUG:
  Log('Agent debug logging is enabled!')
else:
  Log('Agent debug logging is disabled!')


# URLS
SEARCH_URL = 'https://www.javbus.com/search/%s'
BASE_URL = 'https://www.javbus.com'
THUMBNAIL_URL = BASE_URL + '/pics/thumb/'


INITIAL_SCORE = 100


user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,}


def Start():
    pass


def ValidatePrefs():
      pass


def dump(obj):
    for attr in dir(obj):
        Log("obj.%s = %r" % (attr, getattr(obj, attr)))
    
def getElementFromUrl(url):
    return html.fromstring(request(url))

def request(url):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers={'User-Agent':user_agent,}
    request = urllib2.Request(url,headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return urllib2.urlopen(request,context=ctx).read()



def elementToString(ele):
    html.tostring(ele, encoding='unicode')


def file_exists(url):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers={'User-Agent':user_agent,}
    try:
        response = urllib2.Request(url,headers=headers)
        status_code = urllib2.urlopen(response).getcode()
        if status_code == 200:
            return True
        else:
            return False
    except urllib2.HTTPError:
        return False

def query_string(file_name):
    code_match_pattern1 = '[a-zA-Z]{2,9}[-_][0-9]{2,9}'
    code_match_pattern2 = '([a-zA-Z]{2,9})([0-9]{2,9})'
    re_rules1 = re.compile(code_match_pattern1, flags=re.IGNORECASE)
    re_rules2 = re.compile(code_match_pattern2, flags=re.IGNORECASE)

    file_code1 = re_rules1.findall(file_name)
    file_code2 = re_rules2.findall(file_name)
    if file_code1:
        query = file_code1[0].upper()
    elif file_code2:
        query = file_code2[0][0].upper() + '-' + file_code2[0][1]
    else:
        query = file_name
    return query

studioascollection = preference['studioascollection']
orgininalruntime = preference['orgininalruntime']



class JavBusAgent(Agent.Movies):
    name = 'JavBus'
    languages = [Locale.Language.English,  Locale.Language.Japanese]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.adultjavmovie', 'com.plexapp.agents.lambda', 'com.plexapp.agents.Jav18']


    def search(self, results, media, lang):
        file_name = media.name.replace(' ', '-')
        query = query_string(file_name)

        # javbus.search(query,results,media,lang)
        try:
            url = str(SEARCH_URL % query)

            for movie in getElementFromUrl(url).xpath('//a[contains(@class,"movie-box")]'):
                
                # curName = movie.text_content().strip()
                # curID = movie.get('href').split('/')[3]
                curID = movie.get('href')
                ShortID = movie.get('href').split('/')[3]
                score = INITIAL_SCORE - Util.LevenshteinDistance(query.replace('-','').lower(), ShortID.replace('-','').lower())
                
                entryScore = int(score)
                curName = movie.xpath('.//img')[0].get("title")

                # curNameEn = translator.translate(curName, dest="en")

                curDateTime = movie.xpath('.//date[2]')[0].text_content().strip()

                curYear = re.search(r"(\d{4})", str(curDateTime)).group(1)

                movName =  ShortID + ' [' + curDateTime + '] ' + curName

                img = movie.xpath('.//img')[0].get("src")
                imgName = img.split('/')[3].replace('.jpg','')

                movID = ShortID + '|' + imgName + "|" + curDateTime
                
                results.Append(MetadataSearchResult(id=movID, name=movName, year=curYear, lang=lang, score=entryScore))
                # results.Append(MetadataSearchResult(id=theGuid, name=title, year=year, lang=lang, score=bestHitScore))
                
            results.Sort('score', descending=True)
        except Exception as e: pass

    def update(self, metadata, media, lang):
        i = 0
        collectors = []
        url=str(BASE_URL + '/' + str(metadata.id).split("|")[0])
        # url_en=str(BASE_URL + '/en/' + str(metadata.id).split("|")[0])
        movie = getElementFromUrl(url).xpath('//div[@class="row movie"]')[0]


        movie_en = getElementFromUrl(url.replace('https://www.javbus.com', 'https://www.javbus.com/en')).xpath('//div[@class="row movie"]')[0]


        metadata.title = query_string(media.title)
        metadata.collections.clear()
        # metadata.posters.clear()
        thumbUrl = THUMBNAIL_URL + str(metadata.id).split("|")[1] + '.jpg'
        if file_exists(thumbUrl):
            metadata.posters[thumbUrl] = Proxy.Preview(HTTP.Request(thumbUrl), sort_order=i)
        
        bigImage = THUMBNAIL_URL.replace('thumb','cover') + str(metadata.id).split("|")[1] + '_b.jpg'
        if file_exists(bigImage):
            metadata.art[bigImage] = Proxy.Preview(HTTP.Request(bigImage), sort_order=i)

        if movie.xpath('//h3'):
            metadata.title = movie_en.xpath('//h3')[0].text_content().strip()


        if movie.xpath('//h3'):
            metadata.original_title = query_string(movie.xpath('//h3')[0].text_content().strip())

        if movie_en.xpath('//h3'):
            enTitle = movie_en.xpath('//h3')[0].text_content().strip()
            if movie_en.xpath('//*[.="Length:"]/following-sibling::text()'):
                originalrun = movie_en.xpath('//*[.="Length:"]/following-sibling::text()')[0].strip()
                if orgininalruntime:
                    summary = metadata.summary = enTitle.replace('/',"\r") + " [" + originalrun + "]"
                else:
                    summary = metadata.summary = enTitle.replace('/',"\r")
         

        #Add janan country to meta
        metadata.countries.clear()
        country = 'Japan'
        metadata.countries.add(country)

  

        # Genres
        try:
            genrelist = []
            metadata.genres.clear()
            ignoregenres = [x.lower().strip() for x in preference['ignoregenres'].split('|')]
            metadata.genres.clear()   
            if movie_en.xpath('//span[@class="genre"]/label/a//text()'):
                genres = movie_en.xpath('//span[@class="genre"]/label/a//text()')
            for genre in genres:
                genre = genre.strip()
                genre = SearchStudio.getSearchGenre(str(genre))
                genrelist.append(genre)
                if not genre.lower().strip() in ignoregenres: metadata.genres.add(genre)
        except: pass

        # Studio
        try:
            if movie_en.xpath('//*[text()[contains(.,"Studio")]]'):
                studio = movie_en.xpath('//*[text()[contains(.,"Studio")]]/following-sibling::a/text()')[0].strip()
                studio = SearchStudio.getSearchStudio(str(studio))
                metadata.studio = studio
                if studioascollection: 
                    collectors.append(studio.lower())
                    metadata.collections.add(studio)
        except: pass
      

        if movie_en.xpath('//*[text()[contains(.,"Label")]]/following-sibling::a'):
            label = movie_en.xpath('//*[text()[contains(.,"Label")]]/following-sibling::a')
            tagline = 'Label: ' + label[0].text_content().strip()


        if movie_en.xpath('//*[text()[contains(.,"Series")]]/following-sibling::a'):
            series = movie_en.xpath('//*[text()[contains(.,"Series")]]/following-sibling::a')
            tagline = tagline + ', Series: ' + series[0].text_content().strip()

        
        if len(tagline) > 0:
            metadata.tagline = tagline
            

        #actors
        actorsname = ''
        metadata.roles.clear()
        if movie_en.xpath('//ul//div[@class="star-name"]/a'):
        # if movie_en.xpath('//*[@class="star-name"]/a'):
            for actor in  movie_en.xpath('//ul//div[@class="star-name"]/a'):
                elementToString(actor)
                role = metadata.roles.new()
                actorname = role.name = actor.xpath('./@title')[0]             
                upperurl = actor.xpath('./@href')[0]
                upperurl = upperurl.replace("https://www.javbus.com/en/star","https://www.javbus.com/pics/actress")
                upperurl = upperurl + '_a.jpg'
                role.photo = upperurl    
                actorsname =  actorname + "\r" + actorsname
        else:
            actorname = "Fail Getting Actorss"


        if len(actorname) > 0:
            metadata.summary = summary + "\r\r" + actorsname

        
        try:           
            if movie_en.xpath('.//span[contains(text(),"Label:")]//following-sibling::a'):
                label = movie_en.xpath('.//span[contains(text(),"Label:")]//following-sibling::a')[0].text_content().strip()
                if not label.lower() in collectors: metadata.collections.add(label)
        except: pass

        try:
            if movie_en.xpath('.//span[contains(text(),"Series:")]//following-sibling::a'):
                series = movie_en.xpath('.//span[contains(text(),"Series:")]//following-sibling::a')[0].text_content().strip()
                if not series.lower() in collectors: metadata.collections.add(series)
        except: pass

        # Director
        try:
            metadata.directors.clear()
            if movie_en.xpath('.//span[contains(text(),"Director:")]//following-sibling::a'):
                htmldirector = movie_en.xpath('.//span[contains(text(),"Director:")]//following-sibling::a')[0].text_content().strip()
                if (len(htmldirector) > 0):
                    director = metadata.directors.new()
                    director.name = htmldirector
        except: pass


        try:
            if movie.xpath('//*[text()[contains(.,"Release Date:")]]/following-sibling::text()'):
                movRelDT = movie.xpath('//*[text()[contains(.,"Release Date:")]]/following-sibling::text()').strip()
                metadata.summary = datetime.datetime.strptime(movRelDT, '%Y-%m-%d')
        except: pass
        

        try:
            # if movie.xpath('//*[text()[contains(.,"Release Date:")]]/following-sibling::text()'):
            #     movRelDT = movie.xpath('//*[text()[contains(.,"Release Date:")]]/following-sibling::text()')[0].replace(" ",'').strip()
            if movie.xpath('//div[@class="row movie"]/div[2]/p[2]/span/following-sibling::text()'):
                movRelDT = movie.xpath('//div[@class="row movie"]/div[2]/p[2]/span/following-sibling::text()')[0].strip()
                # movRelDT = str(metadata.id).split("|")[2]
                if (len(movRelDT) > 0):
                    metadata.originally_available_at = Datetime.ParseDate(movRelDT).date()
                    metadata.year = metadata.originally_available_at.year
        except: pass    
              
        # ##For background drop image turn on to download sample screenshot    
        if preference['pullscreens']:
            pullscreenscount = int(preference['pullscreenscount'])
            if not (pullscreenscount > 0 and pullscreenscount < 50):
                pullscreenscount = 3
            try:
                if movie.xpath('//div[@id="sample-waterfall"]//a'):
                    imgs = movie.xpath('//div[@id="sample-waterfall"]//a')
                    if len(imgs):
                        screencount = 0
                        imagelist = self.Rand(1,len(imgs),pullscreenscount)
                        # for sampleimage in movie.xpath('//div[@id="sample-waterfall"]//a'):
                        for sampleimage in imgs:
                            screencount += 1                            
                            if screencount in imagelist:
                                background = sampleimage.get('href')
                                metadata.art[background] = Proxy.Preview(HTTP.Request(background))
            except: pass


    def Rand(self, start, end, num):
        res = []
        for j in range(num):
            res.append(random.randint(start, end))
        return res


