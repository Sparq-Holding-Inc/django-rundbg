# -*- coding: utf-8 -*-
import errno
import logging
import os
import socket
import sys
from datetime import datetime

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.runserver import Command as OriginalCommand
from django_rundbg.werkzeug_patch import RunDbgDebuggedApplication

logger = logging.getLogger("rundbg")


class Command(OriginalCommand):
    help = "Starts a lightweight Web server with Werkzeug Debugger for development."

    default_addr = '127.0.0.1'
    default_addr_ipv6 = '::1'
    default_port = '8000'
    protocol = 'http'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--reloader-interval',
            dest='reloader_interval',
            action="store",
            type=int,
            default=2,
            help='After how many seconds auto-reload should scan'
            ' for updates in poller-mode [default=%s]' % 2)
        parser.add_argument(
            '--keep-meta-shutdown',
            dest='keep_meta_shutdown_func',
            action='store_true',
            default=False,
            help="Keep request.META['werkzeug.server.shutdown'] function which is"
            " automatically removed because Django debug pages tries to call"
            " the function and unintentionally shuts down the Werkzeug server.")
        parser.add_argument(
            '--use-link',
            dest='use-link',
            action='store_true',
            default=False,
            help="Show a simple page with a link to the original Werkzeug Traceback page")

    def run(self, **options):
        try:
            from werkzeug.serving import run_simple
            from werkzeug.serving import WSGIRequestHandler as _WSGIRequestHandler

        except ImportError:
            raise CommandError(
                "Werkzeug is required to use rundbg.  Please visit http://werkzeug.pocoo.org/"
                " or install via pip. (pip install Werkzeug)")

        class WSGIRequestHandler(_WSGIRequestHandler):

            def make_environ(self):
                environ = super(WSGIRequestHandler, self).make_environ()
                if not options.get('keep_meta_shutdown_func'):
                    del environ['werkzeug.server.shutdown']
                return environ

        threading = options['use_threading']
        # 'shutdown_message' is a stealth option.
        shutdown_message = options.get('shutdown_message', '')
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'

        self.stdout.write("Performing system checks...\n\n")
        self.check(display_num_errors=True)
        # Need to check migrations here, so can't use the
        # requires_migrations_check attribute.
        self.check_migrations()
        now = datetime.now().strftime('%B %d, %Y - %X')
        self.stdout.write(now)
        self.stdout.write(("Django version %(version)s, using settings %(settings)r\n"
                           "Starting development server at %(protocol)s://%(addr)s:%(port)s/\n"
                           "Quit the server with %(quit_command)s.\n") % {
                               "version": self.get_version(),
                               "settings": settings.SETTINGS_MODULE,
                               "protocol": self.protocol,
                               "addr": '[%s]' % self.addr if self._raw_ipv6 else self.addr,
                               "port": self.port,
                               "quit_command": quit_command,
                           })

        use_reloader = options.get('use_reloader', True)
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        reloader_interval = options.get('reloader_interval', 2)

        handler = RunDbgDebuggedApplication(
            self.get_handler(None, **options), use_link=True, evalex=True)

        # Werkzeug needs to be clued in its the main instance if running
        # without reloader or else it won't show key.
        # https://git.io/vVIgo
        if not use_reloader:
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'

        os.environ['WERKZEUG_DEBUG_PIN'] = 'off'

        try:
            run_simple(
                self.addr,
                int(self.port),
                handler,
                use_reloader=use_reloader,
                reloader_interval=reloader_interval,
                threaded=threading,
                request_handler=WSGIRequestHandler,)
        except socket.error as e:
            # Use helpful error messages instead of ugly tracebacks.
            ERRORS = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            try:
                error_text = ERRORS[e.errno]
            except KeyError:
                error_text = e
            self.stderr.write("Error: %s" % error_text)
            # Need to use an OS exit because sys.exit doesn't work in a thread
            os._exit(1)
        except KeyboardInterrupt:
            if shutdown_message:
                self.stdout.write(shutdown_message)
            sys.exit(0)
