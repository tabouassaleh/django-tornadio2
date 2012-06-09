# Copyright (c) 2012 TitanFile Inc. <https://www.titanfile.com>
#
# Author: Tony Abou-Assaleh <taa@titanfile.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tornadio2 import SocketConnection
from tornadio2 import event
from tornadio2.conn import EventMagicMeta

from django.conf import settings
from django.contrib.auth import get_user

import sys
import logging

# TODO: Use a dummy request from Django instead of declaring a plain one. TAA - 2012-03-09.
class SessionRequest(object):
    """
    An object that stores a reference to a Django session.
    """
    def __init__(self, session_key):
        """
        Initialize the instance with a reference to a Django session.

        `session_key`
            The key of the session to be retrived.
        """
        from django.utils.importlib import import_module
        engine = import_module(settings.SESSION_ENGINE)
        self.session = engine.SessionStore(session_key)

class SocketEventHandler(SocketConnection):
    def get_user_instance(self, Model, **kwargs):
        """
        Get an instance belonging to the current user that matches the `id` in `kwargs`.

        This method ensures that only instances owned by the current user are accessed.
        """
        try:
            instance = Model.active.get(user=self.user, slug=kwargs['id'])
        except Model.DoesNotExist:
            return 'Contact does not exist', None
        except:
            print 'Exception in get_user_instance: kwargs = %s' % repr(kwargs)
            raise
        return instance

    def get_instance(self, Model, **kwargs):
        try:
            instance = Model.active.get(slug=kwargs['id'])
        except Model.DoesNotExist:
            return 'Contact does not exist', None
        except:
            print 'Exception in get_instance: kwargs = %s' % repr(kwargs)
            raise
        return instance
         
    def handle_read(self, read_model, read_collection, **kwargs):
        '''A read event can be triggered on a collection or individual models.'''
        if 'args' in kwargs and isinstance(kwargs['args'], list):
            return read_collection(**kwargs)
        else:
            return read_model(**kwargs)

class BackboneConnection(SocketConnection):
    """
    A SocketConnection wrapper for Django.
    """

    def on_event(self, name, *args, **kwargs):
        """Override TorndaIO2's default on_event handler.

        By default, it uses decorator-based approach to handle events,
        but you can override it to implement custom event handling.

        `name`
            Event name
        `args`
            Event args
        `kwargs`
            Event kwargs

        There's small magic around event handling.
        If you send exactly one parameter from the client side and it is dict,
        then you will receive parameters in dict in `kwargs`. In all other
        cases you will have `args` list.

        For example, if you emit event like this on client-side::

            sock.emit('test', {msg='Hello World'})

        you will have following parameter values in your on_event callback::

            name = 'test'
            args = []
            kwargs = {msg: 'Hello World'}

        However, if you emit event like this::

            sock.emit('test', 'a', 'b', {msg='Hello World'})

        you will have following parameter values::

            name = 'test'
            args = ['a', 'b', {msg: 'Hello World'}]
            kwargs = {}

        """
        # Ensure that the user is still authenticated for each event.
        try:
            self.user = get_user(self.session_request)
            if self.user.is_authenticated():
                print 'User is authenticated. Proceeding with the event handling.'
        except:
            print "Unexpected error:", sys.exc_info()
            self.close()
            return False
        name = name.replace(':', '_')  # turn iosync event such as user:read to user_read

        # Process collection IDs:
        id_sep = getattr(settings, 'SOCKETIO_ID_SEPARATOR', '-')
        if id_sep in name:
            name, collection_id = name.split(id_sep, 2)
            kwargs['collection_id'] = collection_id

        handler = self._events.get(name)

        if handler:
            try:
                # Backbone.iosync always sends data in kwargs, either in 'kwargs' or 'args' keys.
                if 'args' in kwargs:
                    # Collection read events send data in kwargs['args']
                    args = kwargs['args']
                if 'kwargs' in kwargs:
                    # Model read events send data in kwargs['kwargs']
                    kwargs = kwargs['kwargs']
                return handler(self, *args, **kwargs)
            except TypeError:
                logging.error(('Attempted to call event handler %s ' +
                                  'with %s args and %s kwargs.') % (handler, repr(args), repr(kwargs)))
                raise
        else:
            message = 'Invalid event name: %s' % name
            logging.error(message)
            return message

    def broadcast(self, event, message, include_self=False):
        session_items = self.session.server._sessions._items
        for session_id, session in session_items.iteritems():
            if include_self or session != self.session:
                session.conn.emit(event, message)

    @staticmethod
    def broadcast_user(user, event, message, exclude=None):
        if 'connections' not in settings.SOCKETIO_GLOBALS:
            return
        for conn in settings.SOCKETIO_GLOBALS['connections'][user.id]:
            if not exclude or conn not in exclude:
                conn.emit(event, message)

    def on_open(self, conn_info):
        session_key = conn_info.get_cookie('sessionid').value
        request = SessionRequest(session_key)
        self.session_request = request  # Store the request for future access to the session.
        user = get_user(request)
        if not user.is_authenticated():
            return False
        self.user = user
        settings.SOCKETIO_GLOBALS['connections'][user.id].add(self)

    def on_close(self):
        settings.SOCKETIO_GLOBALS['connections'][self.user.id].remove(self)

    @event
    def command(self, *args, **kwargs):
        """
        Shell-like API. Restricted access to superusers.
        """
        if not self.user.is_superuser:
            return 'Permission denied.', None
        command = kwargs['command']
        name = kwargs['event']
        del kwargs['command']
        del kwargs['event']
        # TODO: Incomplete. TAA - 2012-03-16.
        if name == 'emit':
            self.emit()
        super(BackboneConnection, self).on_event(name, *args, **kwargs)

class BaseSocket(BackboneConnection):
    '''A base socket class to be mixed in with other sockets.'''
    def on_message(self, message):
        print 'Received message: %s' % str(message)
