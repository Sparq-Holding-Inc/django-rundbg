import logging
import sys

from werkzeug._compat import range_type
from werkzeug.debug import DebuggedApplication, tbtools
from werkzeug.utils import escape
from werkzeug.wrappers import BaseRequest as Request

logger = logging.getLogger("rundbg")

LINK_HTML = '''<html><head><title>Error 500</title></head>\
<body><h1>%(exception_type)s</h1>
<div>
  <p>%(exception)s</p>
  <p>Inspect at %(debugger_path)s?s=%(secret)s&tb=%(traceback_id)d</p>
</div><a href='%(debugger_path)s?s=%(secret)s&tb=%(traceback_id)d'>Open</a>
</body></html>'''


class TamperedTraceback(tbtools.Traceback):
    '''
    Traceback for Werkzeug debugger with additional `render_link` method

    We extend and override the `Traceback` class from Werkzeug to add an extra
    method to render only a link to the debugging console.
    '''

    def __init__(self, *args, **kwargs):
        super(TamperedTraceback, self).__init__(*args, **kwargs)

    def render_link(self, secret, debugger_path):
        """Render the Full HTML page with the traceback info."""
        exc = escape(self.exception)
        return LINK_HTML % {
            'exception': exc,
            'exception_type': escape(self.exception_type),
            'debugger_path': debugger_path,
            'traceback_id': self.id,
            'secret': secret
        }


def get_current_traceback(ignore_system_exceptions=False, show_hidden_frames=False, skip=0):
    '''
    Method to return the handler the Traceback of the exception

    This is here only to an instance of our Traceback class instead of the original.
    See werkzeug/debug/tbtools.py#L170
    '''
    exc_type, exc_value, tb = sys.exc_info()
    if ignore_system_exceptions and exc_type in tbtools.system_exceptions:
        raise
    for x in range_type(skip):
        if tb.tb_next is None:
            break
        tb = tb.tb_next
    tb = TamperedTraceback(exc_type, exc_value, tb)
    if not show_hidden_frames:
        tb.filter_hidden_frames()
    return tb


class RunDbgDebuggedApplication(DebuggedApplication):
    '''
    Enables debugging support with debugger console

    The constructor takes two optional parameter:
    :param use_link [False]: Render a link to debugger console instead of Werkzeug's Traceback page.
    :param debugger_path [/dbg-console]: The path to render the debugger

    Please see werkzeug/debug/__init__.py#L198
    '''

    def __init__(self, *args, **kwargs):
        self.debugger_path = kwargs.pop('debugger_path', '/dbg-console')
        self.use_link = kwargs.pop('use_link', False)
        super(RunDbgDebuggedApplication, self).__init__(*args, **kwargs)

    def get_debugger_path(self, environ):
        '''Return the path to the debugger. Include the host if present'''
        request = Request(environ)
        if request.headers.get('host'):
            return request.headers.get('host') + self.debugger_path
        else:
            return self.debugger_path

    def debug_application(self, environ, start_response):
        '''
        Run the application and conserve the traceback frames

        Please see werkzeug/debug/__init__.py#L280
        '''
        app_iter = None
        try:
            app_iter = self.app(environ, start_response)
            for item in app_iter:
                yield item
            if hasattr(app_iter, 'close'):
                app_iter.close()
        except Exception:
            if hasattr(app_iter, 'close'):
                app_iter.close()
            traceback = get_current_traceback(
                skip=1, show_hidden_frames=self.show_hidden_frames, ignore_system_exceptions=True)
            for frame in traceback.frames:
                self.frames[frame.id] = frame
            self.tracebacks[traceback.id] = traceback

            try:
                start_response(
                    '500 INTERNAL SERVER ERROR',
                    [
                        ('Content-Type', 'text/html; charset=utf-8'),
                        # Disable Chrome's XSS protection, the debug
                        # output can cause false-positives.
                        ('X-XSS-Protection', '0'),
                    ])
            except Exception:
                # if we end up here there has been output but an error
                # occurred.  in that situation we can do nothing fancy any
                # more, better log something into the error log and fall
                # back gracefully.
                environ['wsgi.errors'].write(
                    'Debugging middleware caught exception in streamed '
                    'response at a point where response headers were already '
                    'sent.\n')
            else:
                is_trusted = bool(self.check_pin_trust(environ))
                if self.use_link:
                    rendered = traceback.render_link(
                        secret=self.secret, debugger_path=self.get_debugger_path(environ))
                else:
                    rendered = traceback.render_full(
                        evalex=self.evalex, evalex_trusted=is_trusted, secret=self.secret)
                yield rendered.encode('utf-8', 'replace')

            traceback.log(environ['wsgi.errors'])

    def debugger_console(self, environ, start_response, traceback):
        '''Return the appropiate Traceback page'''
        try:
            start_response(
                '200 OK',
                [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    # Disable Chrome's XSS protection, the debug
                    # output can cause false-positives.
                    ('X-XSS-Protection', '0'),
                ])
        except Exception:
            # if we end up here there has been output but an error
            # occurred.  in that situation we can do nothing fancy any
            # more, better log something into the error log and fall
            # back gracefully.
            environ['wsgi.errors'].write('Debugging middleware caught exception in streamed '
                                         'response at a point where response headers were already '
                                         'sent.\n')
        else:
            is_trusted = bool(self.check_pin_trust(environ))
            yield traceback.render_full(evalex=self.evalex,
                                        evalex_trusted=is_trusted,
                                        secret=self.secret) \
                .encode('utf-8', 'replace')

        traceback.log(environ['wsgi.errors'])

    def __call__(self, environ, start_response):
        """Dispatch the requests."""
        # Taken literraly from Werkzeug:
        # important: don't ever access a function here that reads the incoming
        # form data!  Otherwise the application won't have access to that data
        # any more!

        # We will intercept the call only if we need to. If not, pass it along.
        request = Request(environ)
        if not request.args.get('__debugger__') == 'yes' and self.debugger_path is not None and \
                request.path == self.debugger_path and self.use_link:

            secret = request.args.get('s')
            traceback = self.tracebacks.get(request.args.get('tb', type=int))
            if secret == self.secret and traceback:
                return self.debugger_console(environ, start_response, traceback)

        logger.debug(super(RunDbgDebuggedApplication, self))

        return super(RunDbgDebuggedApplication, self).__call__(environ, start_response)
