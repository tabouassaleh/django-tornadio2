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

from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict
from django.utils.functional import empty, memoize
from django.utils.importlib import import_module

def mixin(Cls, MixinClass):
    Cls.__bases__ += (MixinClass,)
    Cls._events.update(MixinClass._events)

def load_classes(path_list, BaseClass=None):
    for path in path_list:
        yield get_class(path, BaseClass)

def _get_class(import_path, BaseClass):
    """
    Import and return a class defined by the import path.

    Generalized from django/contrib/staticfiles/finders.py.
    """
    module, attr = import_path.rsplit('.', 1)
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        Cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
                                   'class.' % (module, attr))
    if BaseClass and not issubclass(Cls, BaseClass):
        raise ImproperlyConfigured('Finder "%s" is not a subclass of "%s"' %
                                   (Cls, BaseClass))
    return Cls

_classes = SortedDict()
get_class = memoize(_get_class, _classes, 1)
