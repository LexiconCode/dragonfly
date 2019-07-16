#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it
#   under the terms of the GNU Lesser General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with Dragonfly.  If not, see
#   <http://www.gnu.org/licenses/>.
#

"""
Base Window class
============================================================================

"""

from six import string_types, integer_types

from .window_movers import window_movers

#===========================================================================


class BaseWindow(object):
    """
        The base Window class for controlling and placing windows.

    """

    #-----------------------------------------------------------------------
    # Class attributes to retrieve existing Window objects.

    _windows_by_name = {}
    _windows_by_id = {}

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        """ Get the foreground window. """
        raise NotImplementedError()

    @classmethod
    def get_all_windows(cls):
        """ Get a list of all windows. """
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        self._id = None
        self.id = id
        self._names = set()

    def __str__(self):
        args = list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    @property
    def id(self):
        """ Protected access to id attribute. """
        return self._id

    @id.setter
    def id(self, value):
        self._set_id(value)

    def _set_id(self, id):
        if not isinstance(id, integer_types):
            raise TypeError("Window id/handle must be integer or long,"
                            " but received {0!r}".format(id))
        self._id = id
        self._windows_by_id[id] = self

    # The 'handle' and '_handle' attributes have been kept in for backwards-
    # compatibility. They just reference the BaseWindow 'id' property.

    handle = property(fget=lambda self: self._id,
                      fset=_set_id,
                      doc="Protected access to handle attribute.")
    _handle = property(fget=lambda self: self._id)

    def _get_name(self):
        if not self._names:
            return None
        for name in self._names:
            return name

    def _set_name(self, name):
        assert isinstance(name, string_types)
        self._names.add(name)
        self._windows_by_name[name] = self

    name = property(fget=_get_name,
                    fset=_set_name,
                    doc="Protected access to name attribute.")

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_window_text(self):
        # Method to get the window title.
        raise NotImplementedError()

    def _get_class_name(self):
        # Method to get the window class name.
        raise NotImplementedError()

    def _get_window_module(self):
        # Method to get the window executable.
        raise NotImplementedError()

    @property
    def title(self):
        """ Read-only access to the window's title. """
        return self._get_window_text()

    @property
    def classname(self):
        """ Read-only access to the window's class name. """
        return self._get_class_name()

    #: Alias of :attr:`classname`.
    cls_name = classname

    @property
    def executable(self):
        """ Read-only access to the window's executable. """
        return self._get_window_module()

    @property
    def is_minimized(self):
        """ Whether the window is currently minimized. """
        raise NotImplementedError()

    @property
    def is_maximized(self):
        """ Whether the window is currently maximized. """
        raise NotImplementedError()

    @property
    def is_visible(self):
        """
        Whether the window is currently visible.

        This may be indeterminable for some windows.
        """
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        """
        Method to get the window's position as a :class:`Rectangle` object.

        :returns: window position
        :rtype: Rectangle
        """
        raise NotImplementedError()

    def set_position(self, rectangle):
        """
        Method to set the window's position using a :class:`Rectangle`
        object.

        :param rectangle: window position
        :type rectangle: Rectangle
        """
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        """ Minimize the window (if possible). """
        raise NotImplementedError()

    def maximize(self):
        """ Maximize the window (if possible). """
        raise NotImplementedError()

    def restore(self):
        """ Restore the window if it is minimized or maximized. """
        raise NotImplementedError()

    def set_foreground(self):
        """ Set the window as the foreground (active) window. """
        raise NotImplementedError()

    def move(self, rectangle, animate=None):
        """
        Move the window, optionally animating its movement.

        :param rectangle: new window position and size
        :param animate: name of window mover
        :type rectangle: Rectangle
        :type animate: str
        """
        if not animate:
            self.set_position(rectangle)
        else:
            try:
                window_mover = window_movers[animate]
            except KeyError:
                # If the given window mover name isn't found, don't animate.
                self.set_position(rectangle)
            else:
                window_mover.move_window(self, self.get_position(), rectangle)
