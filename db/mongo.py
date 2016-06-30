from __future__ import absolute_import, division, print_function, with_statement
import pymongo
from gridfs import GridFS

class MongoDB(pymongo.mongo_client.MongoClient):
    '''
    '''
    def __init__(self, uri, db_name, **kwargs):
        '''
            mongodb://[username:password]@host1[:port1][,host2[:port2]]...[,hostN[:portN]][/[database][?options]
        '''
        kwargs['read_preference'] = pymongo.read_preferences.ReadPreference.SECONDARY_PREFERRED
        super(MongoDB, self).__init__(uri, **kwargs)
        self.db = getattr(self, db_name)

    def find_one(self, collection, filter_or_id=None, *args, **kwargs):
        coll = getattr(self.db, collection)
        return coll.find_one(filter_or_id, *args, **kwargs)

    # def find(self, collection, **kwargs):
    #     coll = getattr(self.db, collection)
    #     return coll.find_one(**kwargs)

