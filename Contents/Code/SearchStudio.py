

import StudiosListParsing
import re


def getSearchStudio(studioName):
    
    for studio, full in StudiosListParsing.studios:
        r = re.compile(re.escape(studio))
        if r.match(studioName):
            studioName = r.sub(full, studioName, 1)
            break
    
    return studioName


def getSearchGenre(genresName):
    
    for genre, full in StudiosListParsing.genres:
        r = re.compile(re.escape(genre))
        if r.match(genresName):
            genresName = r.sub(full, genresName, 1)
            break
    
    return genresName 