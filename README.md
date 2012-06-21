***This is work in progress. The code should work, but it's missing tests, documentation, and an example.***

django-tornadio2
================

There currently doesn't exist an out-of-the-box app that gives Django the ability to communicate over WebSockets.

[TornadIO2](http://readthedocs.org/docs/tornadio2/en/latest/) is an implementation of the [socket.io](http://socket.io/) protocol on top of the [Torando](http://www.tornadoweb.org/) non-blocking web server. Since TornadIO2 and Tornado are written in python, integrating them with Django is almost straightforward.

Goal/Requirements
-----------------

* A management command to start Tornado and setup URL patterns and handlers.
* A connection class to manage active sessions.
* Utility functions (in the connection class) to facilitate common tasks, such as user authentication.

Contributing
------------
Please share your ideas, questions, and requests in the [Issues](https://github.com/tgcondor/django-tornadio2/issues) section.

**Related projects that inspired this work:**
* [django-socketio](https://github.com/stephenmcd/django-socketio)
* [django-tornadio](https://github.com/k1000/django-tornadio)