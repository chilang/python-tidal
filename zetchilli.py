import tidalapi
import json
import datetime
import time
import requests
import itertools
import sys

class Rds(object):
    def __init__(self, **kwards):
        self.__dict__.update(kwards)
    def __str__(self):
        return '{%s}' % ','.join(['%s:%s' % (k, v) for k,v in self.__dict__.items()]).encode('utf-8')

def parse_rds_data(r):
    def jsonData(response):
        return json.loads(response.content[len('jsonData('):-1])

    for j in jsonData(r)['messages'][0]:
        yield Rds(**j)

def fetch_rds(timestamp):
    url = 'http://rds.eurozet.pl/reader/history.php?true=jsonData&startDate=%s&emitter=chilli' % timestamp
    response = requests.get(url)
    return parse_rds_data(response)



def search(api, song, artist):
    sr = api.search('track', song)
    # for t in sr.tracks:
    #    print t.id, t.name, t.artist.name
    return [t for t in sr.tracks if artist in t.artist.name]

def search_rds(api, rds):
    sr = search(api, '%s %s' % (rds.rds_title, rds.rds_artist), '')
    return len(sr) > 0 and sr[0].id or None

def import_playlist(api, name, rdses):
    pl = api.user.create_user_playlist(name, '')
    for rds in rdses:
        found = search_rds(api, rds)
        if found:
            pl.add_track(found)
            print 'FOUND', found, '->', rds.rds_title.encode('utf-8'), rds.rds_artist.encode('utf-8')
        else:
            print 'NOT FOUND', '->', rds.rds_title.encode('utf-8'), rds.rds_artist.encode('utf-8')

def to_timestamp(dt):
    return int(time.mktime(dt.timetuple()))


def fetch_chilli(d):
    for h in range(0, d.hour+1):
        ts = to_timestamp(d.replace(hour=h, minute=0, second=0, microsecond=0))
        yield fetch_rds(ts)

def create_zet_chilli_playlist(api, d):
    def concat(items):
        return list(itertools.chain(*items))

    items = concat(fetch_chilli(d))
    import_playlist(api, 'Zet Chilli - %s' % d.strftime('%Y %B %d'), items)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        date = datetime.datetime.strptime(sys.argv[3], '%d-%m-%Y').replace(hour=23)
    else:
        date = datetime.datetime.now()

    api = tidalapi.Session()
    api.login(sys.argv[1], sys.argv[2])
    create_zet_chilli_playlist(api, date)
