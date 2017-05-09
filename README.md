# django-rundbg

Provides a lightweight development runserver on Werkzeug with a web-based debugger
with support for REST APIs.

## Features
- Friendly for API debugging, like Django Rest Framework. 
- Werkzeug [web-based debugger](http://werkzeug.pocoo.org/docs/0.11/debug/#using-the-debugger)

### :warning: Be very careful to keep this away from any production environment

## Installation and Configuration
From PyPI with pip

```
pip install django-rundbg
```

In your [development settings](https://code.djangoproject.com/wiki/SplitSettings#Multiplesettingfilesimportingfromeachother) file add the following:
```
from yourproject.settings_general import INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + ['django_rundbg',]

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True
```

## Quickstart
After installation and configuration, just run:
```
python manage.py rundbg --use-link
```

To try out, just place an `assert False` statement whenever you want to inspect your code and variables and this will show either at your
current browser window or in the dev console.

![Chrome Dev Console example](https://www.octobot.io/uploads/django-rundbg/chrome-dev-example.png)

## Invoking
After installation and configuration, just run:
```
python manage.py rundbg
```

Since it extends on Django's `runserver` you can pass on the same parameters than to `rundbg`:
```
python manage.py rundbg --no-reload 0.0.0.0:5678
```

Additionally, it supports one additional parameter useful for debugging XHR requests:
```
python manage.py rundbg --use-link
```

This will show an very simple error 500 page, with a _link_ to the Werkzeug Traceback and web-based interactive debugger that you can open in any browser window. The default behaviour for the 
Werkzeug debugger is to serve the debugging page to the request that created the exception.

Additionally, it supports the following parameters from `runserver_plus`:
- `--reloader-interval 2` After how many seconds auto-reload should scan for updates in poller-mode.
- `--keep-meta-shutdown` Keep `request.META['werkzeug.server.shutdown']` function which is automatically removed because Django 
debug pages tries to call the function and unintentionally shuts down the Werkzeug server.

*Werkzeug security PIN is disabled*.

## Credits

This project is strongly based upon the work of others:
- The [Django Extensions](https://github.com/django-extensions/django-extensions) `runserver_plus` is a
more comprehensive command than this one.
- The [Werkzeug](http://werkzeug.pocoo.org/) server.
- [Another take](https://github.com/philippbosch/django-werkzeug-debugger-runserver) on the same challenge.

## Authors
- Juan Saavedra

With :heart: from [Octobot](https://www.octobot.io)
