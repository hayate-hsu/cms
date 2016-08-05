'''
    cms : content manager system
    manager group
    manager account
    manager message
'''
from __future__ import absolute_import, division, print_function, with_statement

# Tornado framework
import tornado.web
HTTPError = tornado.web.HTTPError
from tornado.log import access_log, gen_log, app_log

from handler.base import BaseHandler

from common import util
_now = util.now

from config import settings

from worker import msg
from worker import manager

import os

from config import ueditor

# json_encoder = util.json_encoder
json_encoder = util.json_encoder
json_decoder = util.json_decoder

class MainHandler(BaseHandler):
    '''
    '''
    def get(self):
        user = self.get_argument('manager', '') or self.get_argument('user', '')
        if user:
            token = self.get_argument('token')
            token, expired = token.split('|')
            token2 = util.token2(user, expired)
            if token != token2:
                raise HTTPError(400, reason='Abnormal token')
            self.render('index.html', groups=manager.check_location(user))
        else:
            self.redirect('login.html')

class PageHandler(BaseHandler):
    '''
    '''
    def get(self, page):
        '''
            Render html page
        '''
        page = page.lower()
        user = self.get_argument('manager', '') or self.get_argument('user', '')
        if user:
            # manager get it's messages
            token = self.get_argument('token')
            token, expired = token.split('|')
            token2 = util.token2(user, expired)
            if token != token2:
                raise HTTPError(400, reason='Abnormal token')
            
            group = manager.check_location(user)

            gmtypes = msg.get_gmtypes(group)
            self.render(page, groups=group, gmtypes=gmtypes)
        else:
            return self.render(page)

class AuthTokenHandler(BaseHandler):
    def check_token(self):
        user = self.get_argument('manager') or self.get_argument('user')
        token = self.get_argument('token')

        manager.check_token(user, token)


class GMTypeHandler(AuthTokenHandler):
    def get(self, _id=''):
        user = self.get_argument('manager') or self.get_argument('user')
        self.check_token()
        group = manager.check_location(user)
        if _id:
            gmtype = msg.get_gmtype(group, _id)
            gmtypes = [gmtype, ]
        else:
            gmtypes = msg.get_gmtypes(group)

        self.render_json_response(gmtypes=gmtypes, **self.OK)

    def post(self, _id=''):
        user = self.get_argument('manager') or self.get_argument('user')
        self.check_token()
        group = manager.check_location(user)
        name = self.get_argument('name')
        msg.create_gmtype(group, name)
        self.render_json_response(**self.OK)

    def put(self, _id=''):
        if not _id:
            raise HTTPError(400)
        user = self.get_argument('manager') or self.get_argument('user')
        self.check_token()
        group = manager.check_location(user)
        name = self.get_argument('name')
        msg.update_gmtype(_id, group, name)
        self.render_json_response(**self.OK)

    def delete(self, _id=''):
        user = self.get_argument('manager') or self.get_argument('user')
        self.check_token()
        group = manager.check_location(user)
        msg.delete_gmtype(group, _id)
        self.render_json_response(**self.OK)

class AccountHandler(BaseHandler):
    '''
        manager account login
    '''
    def post(self):
        '''
            manager login
        '''
        user = self.get_argument('manager') or self.get_argument('user')
        # password has been encrypted by md5
        password = self.get_argument('password')

        _user = manager.get_manager(user, password)
        if not _user:
            raise HTTPError(404, reason='can\'t found account')

        token = util.token(user)

        _user.pop('possword', '')

        self.render_json_response(User=_user['name'], token=token, **self.OK)
        access_log.info('{} login successfully'.format(_user['name']))

# **************************************************
#
#  Message handler
#
# **************************************************
class MessageHandler(AuthTokenHandler):
    '''
        maintain message
        message type: 
            news
            notices (use subtitle)
            push to app notices (use subtitle)
            recruit
    '''
    def render_messages(self, **kwargs):
        '''
            Encode dict and return response to client
        '''
        # self.set_header('Access-Control-Allow-Origin', '*')
        origin = self.request.headers.get('Origin', '')
        if origin and origin in settings['sites']:
            self.set_header('Access-Control-Allow-Origin', origin)
        callback = self.get_argument('callback', None)
        # check should return jsonp
        if callback:
            self.set_status(200, kwargs.get('Msg', None))
            self.finish('{}({})'.format(callback, json_encoder(kwargs)))
        else:
            self.set_status(kwargs['Code'], kwargs.get('Msg', None))
            self.set_header('Content-Type', 'application/json')
            self.finish(json_encoder(kwargs))

    def render_message_response(self, message):
        '''
            return html|json based on the Accept contents
        '''
        accept = self.request.headers.get('Accept', 'text/html')
        if accept.startswith('application/json'):
            self.render_json_response(Code=200, Msg='OK', **message)
        else:
            if self.is_mobile:
                self.render('m_message.tmpt', **message)
            else:
                self.render('message.tmpt', **message)

    def get(self, _id=''):
        '''
            get message
        '''
        # logger.info('id: {}, {}'.format(_id, self.request))
        if _id:
            message = msg.get_message(_id)
            if not message:
                raise HTTPError(404, reason='Can\'t found message')
            return self.render_message_response(message)

        # get messages 
        user = self.get_argument('manager', '') or self.get_argument('user', '')
        groups, ismanager = 0, False
        if user:
            # manager get it's messages
            token = self.get_argument('token')
            token, expired = token.split('|')
            token2 = util.token2(user, expired)
            if token != token2:
                raise HTTPError(400, reason='Abnormal token')
            groups = manager.check_location(user)
            ismanager = True
        else:
            # user get messages
            groups = self.get_argument('groups')
        label = self.get_argument('label', '')
        page = int(self.get_argument('page', 0))
        nums = int(self.get_argument('per', 10))
        mask = int(self.get_argument('mask', 0))
        gmtype = int(self.get_argument('gmtype', 0))
        isimg = int(self.get_argument('isimg', 0))
        pos = page*nums

        messages = msg.get_messages(groups, mask, isimg, gmtype, label, pos, nums, ismanager)
        # logger.info('messages: {}'.format(messages[0]['image']))
        isEnd = 1 if len(messages) < nums else 0

        # self.render_json_response(Code=200, Msg='OK', messages=messages, end=isEnd)
        self.render_messages(Code=200, Msg='OK', messages=messages, end=isEnd)

    def post(self, _id=''):
        '''
            create new message record
            title subtitle section mask author groups status ctime content image
            labels : labes are separate by ' '
        '''
        user = self.get_argument('manager') or self.get_argument('user')
        self.check_token()
        kwargs = {key:value[0] for key,value in self.request.arguments.iteritems()}
        kwargs['author'] = user
        kwargs.pop('token')
        kwargs.pop('manager')
        kwargs['groups'] = manager.check_location(user)
       
        msg.create_message(**kwargs)
        self.render_json_response(**self.OK)

    def put(self, _id):
        '''
            update message record
        '''
        self.check_token()
        kwargs = {key:value[0] for key,value in self.request.arguments.iteritems()}
        kwargs.pop('token')
        kwargs.pop('manager')

        msg.update_message(_id, **kwargs)
        self.render_json_response(**self.OK)

    def delete(self, _id):
        self.check_token()
        msg.delete_message(_id)
        self.render_json_response(**self.OK)

class UeditorHandler(BaseHandler):
    '''
        support for ueditor upload images
    '''
    def get(self):
        self.set_header('Content-Type', 'application/json')
        self.finish(json_encoder(ueditor.config))

    def post(self):
        file_metas = self.request.files['upfile']

        filename, ext = '', '' 
        for meta in file_metas:
            filename = meta['filename']
            content_type = meta['content_type']
            now = _now()
            mask = util.generate_password(8)
            md5 = util.md5(filename, content_type, now, mask)
            _id = md5.hexdigest().lower()

            msg.create_file(meta['body'], _id=_id, filename=filename, content_type=content_type)
            break
        if filename and _id:
            self.render_json_response(url='/fs/'+_id, title=filename, type=content_type, 
                                      state='SUCCESS', **self.OK)
        else:
            raise HTTPError(400)

# @tornado.web.stream_request_body
class ImageHandler(BaseHandler):
    '''
        1. user upload image & update databse
    '''
    # def initialize(self):
    #     self.bytes_read = 0

    # def data_received(self, data):
    #     self.bytes_read += len(data)

    def _gen_image_id_(self, *args):
        now = util.now()

        return util.md5(now, *args).hexdigest()

    def get(self, _id):
        _id = _id.split('.')[0]
        gridout = msg.get_file(_id)
        self.set_header('Content_Type', gridout.content_type)
        self.finish(gridout.read())

    def post(self, _id=None):
        '''
            engineer uplaod image
            update engineer's image
        '''
        file_metas = self.request.files['uploadImg']
        filename, ext = _id, ''
        for meta in file_metas:
            filename = meta['filename']
            content_type = meta['content_type']
            
            if not _id:
                _id = self._gen_image_id_(filename, content_type, util.generate_password(8)) 
            else:
                # previous data has been existed, delete previous first
                msg.delete_file(_id)

            msg.create_file(meta['body'], _id=_id, filename=filename, content_type=content_type)
            break

        if filename:
            self.render_json_response(url='/fs/'+_id, **self.OK)
        else:
            raise HTTPError(400)
    
