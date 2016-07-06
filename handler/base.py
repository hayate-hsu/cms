'''
'''
from __future__ import absolute_import, division, print_function, with_statement

# Tornado framework
import tornado.web
HTTPError = tornado.web.HTTPError

import tornado.ioloop
import tornado.auth
import tornado.escape
import tornado.options
import tornado.locale
import tornado.httpclient
import tornado.gen
import tornado.httputil
from tornado.log import access_log, gen_log, app_log

import os
import sys

# Mako template
import mako.lookup
import mako.template

from common import util
# import settings
import user_agents

json_encoder = util.json_encoder
json_decoder = util.json_decoder

from config import settings

TEMPLATE_PATH = os.path.join(settings['www'], settings['app'])
MOBILE_TEMPLATE_PATH = os.path.join(TEMPLATE_PATH, 'm')


class BaseHandler(tornado.web.RequestHandler):
    '''
        BaseHandler
        override class method to adapt special demands
    '''
    LOOK_UP = mako.lookup.TemplateLookup(directories=[TEMPLATE_PATH, ], 
                                         module_directory=os.path.join('/tmp/mako', settings['app']),
                                         output_encoding='utf-8',
                                         input_encoding='utf-8',
                                         encoding_errors='replace')
#     LOOK_UP_MOBILE = mako.lookup.TemplateLookup(directories=[MOBILE_TEMPLATE_PATH, ], 
#                                                 module_directory=os.path.join('/tmp/mako_mobile', settings['app']),
#                                                 output_encoding='utf-8',
#                                                 input_encoding='utf-8',
#                                                 encoding_errors='replace')

    RESPONSES = {}
    RESPONSES.update(tornado.httputil.responses)

    OK = {'Code':200, 'Msg':'OK'}

    def initialize(self, lookup=LOOK_UP):
        '''
        '''
        pass

    def render_string(self, filename, **kwargs):
        '''
            Override render_string to use mako template.
            Like tornado render_string method, this method also
            pass request handler environment to template engine
        '''
        try:
            # if not self.is_mobile:
            #     template = self.LOOK_UP.get_template(filename)
            # else:
            #     template = self.LOOK_UP_MOBILE.get_template(filename)
            template = self.LOOK_UP.get_template(filename)
            env_kwargs = dict(
                handler = self,
                request = self.request,
                locale = self.locale,
                _ = self.locale.translate,
                static_url = self.static_url,
                xsrf_form_html = self.xsrf_form_html,
                reverse_url = self.application.reverse_url,
                agent = self.agent,
            )
            env_kwargs.update(kwargs)
            return template.render(**env_kwargs)
        except:
            from mako.exceptions import RichTraceback
            tb = RichTraceback()
            for (module_name, line_no, function_name, line) in tb.traceback:
                print('File:{}, Line:{} in {}'.format(module_name, line_no, function_name))
                print(line)
            access_log.error('Render {} failed, {}:{}'.format(filename, tb.error.__class__.__name__, tb.error), 
                         exc_info=True)
            raise HTTPError(500, 'Render page failed')

    def render(self, filename, **kwargs):
        '''
            Render the template with the given arguments
        '''
        directory = TEMPLATE_PATH
        if self.is_mobile:
            directory = MOBILE_TEMPLATE_PATH

        if not os.path.exists(os.path.join(directory, filename)):
            raise HTTPError(404, 'File Not Found')

        self.finish(self.render_string(filename, **kwargs))

    def set_status(self, status_code, reason=None):
        '''
            Set custom error resson
        '''
        self._status_code = status_code
        self._reason = 'Unknown Error'
        if reason is not None:
            self._reason = tornado.escape.native_str(reason)
        else:
            try:
                self._reason = self.RESPONSES[status_code]
            except KeyError:
                raise ValueError('Unknown status code {}'.format(status_code))

    def write_error(self, status_code, **kwargs):
        '''
            Customer error return format
        '''
        if self.settings.get('Debug') and 'exc_info' in kwargs:
            self.set_header('Content-Type', 'text/plain')
            import traceback
            for line in traceback.format_exception(*kwargs['exc_info']):
                self.write(line)
            self.finish()
        else:
            self.render_json_response(Code=status_code, Msg=self._reason)

    def _handle_request_exception(self, e):
        if isinstance(e, tornado.web.Finish):
            # not an error; just finish the request without loggin.
            if not self._finished:
                self.finish(*e.args)
            return
        try:
            self.log_exception(*sys.exc_info())
        except Exception:
            access_log.error('Error in exception logger', exc_info=True)

        if self._finished:
            return 
        if isinstance(e, HTTPError):
            if e.status_code not in BaseHandler.RESPONSES and not e.reason:
                tornado.gen_log.error('Bad HTTP status code: %d', e.status_code)
                self.send_error(500, exc_info=sys.exc_info())
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info())
        else:
            self.send_error(500, exc_info=sys.exc_info())

    def log_exception(self, typ, value, tb):
        if isinstance(value, HTTPError):
            if value.log_message:
                format = '%d %s: ' + value.log_message
                args = ([value.status_code, self._request_summary()] + list(value.args))
                access_log.warning(format, *args)

        access_log.error('Exception: %s\n%r', self._request_summary(), 
                     self.request, exc_info=(typ, value, tb))

    def parse_json_request_body(self):
        '''
            support json request argument,

        '''
        content_type = self.request.headers.get('Content-Type', '')

        # parse json format arguments in request body content
        if content_type.startswith('application/json') and self.request.body:
            arguments = json_decoder(tornado.escape.native_str(self.request.body))
            # logger.info('arguments: {}'.format(arguments))
            for name, values in arguments.iteritems():
                self.request.arguments.setdefault(name, []).extend([values,])
        
    

    def render_json_response(self, **kwargs):
        '''
            Encode dict and return response to client
        '''
        callback = self.get_argument('callback', None)
        if callback:
            # return jsonp
            self.set_status(200, kwargs.get('Msg', None))
            self.finish('{}({})'.format(callback, json_encoder(kwargs)))
        else:
            self.set_status(kwargs['Code'], kwargs.get('Msg', None))
            self.set_header('Content-Type', 'application/json;charset=utf-8')
            self.finish(json_encoder(kwargs))

    def prepare(self):
        '''
            check client paltform
        '''
        # parse json request arguments(application/json)
        self.parse_json_request_body()

        self.agent_str = self.request.headers.get('User-Agent', '')
        self.agent = None
        self.is_mobile = False
        self.task_resp = None
        
        if self.agent_str:
            try:
                self.agent = user_agents.parse(self.agent_str)
                self.is_mobile = self.agent.is_mobile
            except UnicodeDecodeError:
                access_log.warning('Unicode decode error, agent str: {}'.format(self.agent_str))
                # assume user platfrom is mobile
                self.is_mobile = True
            except:
                access_log.warning('Parse user-agent failed, unknown exception.', exc_info=True)
                self.is_mobile = True

