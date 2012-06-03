This repository is currently a placeholder.

django-tornadio2
================

There currently doesn't exist and out-of-the-box app that gives Django the ability to communicate over WebSockets.

TornadIO2 is an implementation of the socket.io protocol on top of the Torando non-blocking web server. Since TornadIO2 and Tornado are written in python, integrating them with Django is almost straightforward.

Goal/Requirements:
------------------

* A management command to start Tornado and setup URL patterns and handlers.
* A connection class to manage active sessions.
* Utility functions to facilitate common tasks.