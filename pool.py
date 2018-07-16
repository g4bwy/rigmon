import simplejson
import requests

from pools_config import pools


class Pool(object):
    def __init__(self, name):
        self.name = name
        self.pool = pools[name]
        self.api_url = self.pool['base_url'] + '?page=api'

        self.workers = []

    def req(self, cmd, uid=False, data=None, json=None, short=False):
        u = self.api_url + '&action=' + cmd + '&api_key=' + self.pool['api_key']
        if uid:
            u = u + '&id=' + self.pool['api_uid']

        if data is None and json is None:
            r = requests.get(u)
        else:
            r = requests.post(u, data=data, json=json)
        ret = simplejson.loads(r.content)
        if short:
            ret = ret[cmd]['data']
        return ret

    def update_workers(self):
        self.workers = self.req('getuserworkers', True)['getuserworkers']['data']

    @property
    def hashfactor(self):
        return self.pool['hashfactor']

    @property
    def sharefactor(self):
        return self.pool['sharefactor']

