import os
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-rundbg',
    version='0.1.0',
    packages=['django_rundbg'],
    include_package_data=True,
    license='Apache License',
    description='Provides a lightweight development runserver on Werkzeug with debugging',
    keywords=['django', 'debug', 'django-rest-framework', 'api'],
    url='https://github.com/octobot-dev/django-rundbg',
    download_url='https://github.com/octobot-dev/django-rundbg/archive/0.1.tar.gz',
    author='Juan Saavedra',
    author_email='jsaavedra@octobot.io',
    zip_safe=True,
    install_requires=[
        'Django>=1.7',
        'Werkzeug>=0.11',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Information Technology',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ],
)
