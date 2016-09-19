'''
'''
from __future__ import absolute_import, division, print_function, with_statement

import tornado.web
from tornado.util import errno_from_exception
from tornado.platform.auto import set_close_exec
from tornado.log import access_log, gen_log, app_log

import tornado.options
define, options = tornado.options.define, tornado.options.options

define('port', default=7080, help='running on the given port', type=int)
# define('app', default='example', type=str, help='serve name')

# log configuration
define('log_file_prefix', type=str, default='/var/log/cms/serve_7080.log')
define('log_rotate_mode', type=str, default='time', help='time or size')

import errno
import os
import sys

import socket

from config import settings

# from handler.example import MainHandler
from handler.cms import (MainHandler, AccountHandler, UeditorHandler, ImageHandler, 
                         GMTypeHandler, MessageHandler, PageHandler, JobsHandler, 
                         JobsTypeHandler, JobsAddressHandler)
from common import util 



class Application(tornado.web.Application):
    '''
        Web application class.
        Redefine __init__ method.
    '''
    def __init__(self, app, src='/web', www='/www'):
        handlers = [
            (r'/account', AccountHandler),
            (r'/ue$', UeditorHandler),
            # (r'/group/?(.*)$', GroupsHandler),
            # (r'/section/?(.*)$', SectionHandler),
            (r'/gmtype/(.*)$', GMTypeHandler),
            (r'/message/?(.*)$', MessageHandler),
            (r'/fs/?(.*)$', ImageHandler),
            (r'/job/type/(.*)$', JobsTypeHandler),
            (r'/job/address/(.*)$', JobsAddressHandler),
            (r'/jobs.json$', JobsHandler),
            (r'/job/(.*)$', JobsHandler),
            (r'/(.+\.html)', PageHandler),
            (r'/', MainHandler),
        ]
        src_path = os.path.join(src, app)
        i18n_path = os.path.join(src_path, 'i18n')
        static_path = os.path.join(www, app)
        settings = {
            'cookie_secret':util.sha1(app).hexdigest(),
            'static_path':static_path,
            # 'static_url_prefix':'resource/',
            'debug':False,
            'autoreload':True,
            'autoescape':'xhtml_escape',
            'i18n_path':i18n_path,
            # 'login_url':'',
            'xheaders':True,    # use headers like X-Real-IP to get the user's IP address instead of
                                # attributeing all traffic to the balancer's IP address.
        }
        super(Application, self).__init__(handlers, **settings)

_DEFAULT_BACKLOG = 128
# These errnos indicate that a non-blocking operation must be retried
# at a later time. On most paltforms they're the same value, but on 
# some they differ
_ERRNO_WOULDBLOCK = (errno.EWOULDBLOCK, errno.EAGAIN)
if hasattr(errno, 'WSAEWOULDBLOCK'):
    _ERRNO_WOULDBLOCK += (errno.WSAEWOULDBLOCK, )

def bind_udp_socket(port, address=None, family=socket.AF_UNSPEC, backlog=_DEFAULT_BACKLOG, flags=None):
    '''
    '''
    udp_sockets = []
    if address == '':
        address = None
    if not socket.has_ipv6 and family == socket.AF_UNSPEC:
        family = socket.AF_INET
    if flags is None:
        flags = socket.AI_PASSIVE
    bound_port = None
    for res in socket.getaddrinfo(address, port, family, socket.SOCK_DGRAM, 0, flags):
        af, socktype, proto, canonname, sockaddr = res
        try:
            sock = socket.socket(af, socktype, proto)
        except socket.error as e:
            if errno_from_exception(e) == errno.EAFNOSUPPORT:
                continue
            raise
        set_close_exec(sock.fileno())
        if os.name != 'nt':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if af == socket.AF_INET6:
            if hasattr(socket, 'IPPROTO_IPV6'):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

        # automatic port allocation with port=None
        # should bind on the same port on IPv4 & IPv6 
        host, requested_port = sockaddr[:2]
        if requested_port == 0 and bound_port is not None:
            sockaddr = tuple([host, bound_port] + list(sockaddr[2:]))
        sock.setblocking(0)
        sock.bind(sockaddr)
        bound_port = sock.getsockname()[1]
        udp_sockets.append(sock)
    return udp_sockets

def add_udp_handler(sock, servers, io_loop=None):
    '''
        Read data in 4096 buffer
    '''
    if io_loop is None:
        io_loop = tornado.ioloop.IOLoop.current()
    def udp_handler(fd, events):
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    data_handler(sock, data, addr)
                    # ac data arrived, deal with
                    pass
            except socket.error as e:
                if errno_from_exception(e) in _ERRNO_WOULDBLOCK:
                    # _ERRNO_WOULDBLOCK indicate we have accepted every
                    # connection that is avaiable
                    return
                import traceback
                traceback.print_exc(file=sys.stdout)
            except: 
                import traceback
                traceback.print_exc(file=sys.stdout)
    io_loop.add_handler(sock.fileno(), udp_handler, tornado.ioloop.IOLoop.READ)

def data_handler(sock, data, addr):
    '''
        User logout
    '''
    pass

def main():
    tornado.options.parse_command_line()

    portal_pid = os.path.join(settings['RUN_PATH'], '{}/p_{}.pid'.format(settings['app'], options.port))
    with open(portal_pid, 'w') as f:
        f.write('{}'.format(os.getpid()))

    # import tcelery
    # tcelery.setup_nonblocking_producer()

    app = Application(settings['app'], settings['src'], settings['www'])
    app.listen(options.port, xheaders=app.settings.get('xheaders', False))
    io_loop = tornado.ioloop.IOLoop.instance()

    # udp_sockets = bind_udp_socket(udp_port)
    # for udp_sock in udp_sockets:
    #     add_udp_handler(udp_sock, '', io_loop)

    app_log.info('{} Server Listening:{} Started'.format(settings['app'], options.port))
    io_loop.start()

if __name__ == '__main__':
    main()
