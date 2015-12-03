PyJSONProxy - simple proxy and scraper


simple proxy
============

AJAX requests are restricted by the `same origin policy`_. This can be
bypassed by using either `JSONP`_, `CORS`_ or a local proxy. This
implements the third variant. So you can do something like this::

    $ curl http://localhost:5000/github/xi/
    {
      "login": "xi",
      ...
    }

With a configuration like this::

    ENDPOINTS = {
        'github': {
            'host': 'https://api.github.com/users/'
        }
    }


scraping
========

Maybe the more interesting part is that this also contains a simple
scraping mechanism. So if a service does not offer an API but only plain
HTML pages, PyJSONProxy can extract information from there::

    $ curl http://localhost:5000/github/xi/
    {
      "url": "https://github.com/xi/",
      "login": "xi",
      "activity": [
        ...
      ],
      "repos": [{
        ...
      }]
      ...
    }

::

    ENDPOINTS = {
        'github': {
            'host': 'https://github.com/',
            'type': 'scrape',
            'fields': {
                'login': '.vcard-username',
                'fullname': '.vcard-fullname',
                'email': '.vcard-details .email',
                'join-date': '.vcard-details .join-date@datetime',
                'activity': {
                    'selector': '.contribution-activity-listing ul a'
                },
                'repos': {
                    'selector': '.popular-repos a.mini-repo-list-item',
                    'fields': {
                        'url': '@href',
                        'name': '.repo',
                        'description': '.repo-description'
                    }
                }
            }
        }
    }

Selectors are generally CSS-selectors with the additional option to
select an attribute by appending an ``@`` and the attribute name. If no
attribute is selected, the text content of the element will be used.


CORS header
===========

By setting ``ALLOW_CORS`` to ``True``, an
``Access-Control-Allow-Origin``-header with value ``*`` will be set for
all responses.


Documentation
=============

Some simple documentation is automatically generated and available under
``/`` (for all endpoints) or ``/{endpoint}/`` (for an individual
endpoint). To provide some input for this documentation, you can add a
description to both endpoints and fields::

    ENDPOINTS = {
        'github': {
            'host': 'https://github.com/',
            'type': 'scrape',
            'doc': 'Access data about GitHub users',
            'fields': {
              'login': '.vcard-username',
              'fullname': '.vcard-fullname',
              'email': '.vcard-details .email'
              'join-date': '.vcard-details .join-date@datetime'
            },
            'fields_doc': {
              'login': 'github username',
              'fullname': 'the user\'s full name',
              'join-date': 'date when the user joined github in ISO-xx format'
            }
        }
    }


Note on security and performance
================================

Security and performance were not a priority in this project. So it
might be bad.


.. _same origin policy: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy
.. _JSONP: https://en.wikipedia.org/wiki/JSONP
.. _CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS
