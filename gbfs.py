import urllib.request
import json
import pandas as pd
import time

class RateException(Exception):
    def __init__(self, message):
        self.message = message

def get_json_file(url):
    req = urllib.request.Request(url)
    r = urllib.request.urlopen(req).read()
    return json.loads(r.decode("utf-8"))

class Feed:
    @classmethod
    def __parse_feedtable(cls, feeds):
        return {x["name"]:x["url"] for x in feeds}

    def __init__(self, url):
        self.feeds = {}
        data = get_json_file(url)["data"]
        for lang, feeddata in data.items():
            self.feeds[lang] = self.__parse_feedtable(feeddata["feeds"])

        self.last_fetched = {}

    def _stale_time(self, feed_name):
        if not feed_name in self.last_fetched:
            return 0

        last_updated, ttl = self.last_fetched[ feed_name ]
        return last_updated+ttl

    def _fetch_raw(self, feedname, lang="en"):
        url = self.feeds[lang][feedname]

        return get_json_file(url)

    def feednames(self, lang="en"):
        return list( self.feeds[lang].keys() )

    def free_bike_status(self, lang="en", force=False):
        feed_name = "free_bike_status"

        # make sure the data isn't fetched before it goes stale
        stale_time = self._stale_time(feed_name)
        if not force and stale_time > time.time():
            raise RateException("Attempt to fetch before data stale.")

        # get raw data
        jsondata = self._fetch_raw( feed_name, lang )

        # build up dataframe for bike records
        last_updated, ttl = jsondata["last_updated"], jsondata["ttl"]
        
        df = pd.DataFrame.from_records( jsondata["data"]["bikes"] )
        df["last_updated"] = last_updated
        df["ttl"] = ttl

        # update TTL table
        self.last_fetched[feed_name] = (last_updated, ttl)

        return df