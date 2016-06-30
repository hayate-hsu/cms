from __future__ import absolute_import, division, print_function, with_statement

from db.mongo import MongoDB, GridFS

from config import settings


config = settings['mongo']
mongo = MongoDB(config['uri'], config['db'])

db = getattr(mongo, config['db'])


fs = GridFS(db)

