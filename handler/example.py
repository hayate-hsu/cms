'''
'''
from __future__ import absolute_import, division, print_function, with_statement

# Tornado framework
import tornado.web
HTTPError = tornado.web.HTTPError

from handler.base import BaseHandler

# json_encoder = util.json_encoder2
# json_decoder = util.json_decoder

class MainHandler(BaseHandler):
    '''
    '''
    def get(self):
        self.render_json_response(Response='In Get Method', **self.OK)

