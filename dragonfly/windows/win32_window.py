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
Window class for Windows
============================================================================

"""

import win32gui
import win32con
from ctypes          import windll, pointer, c_wchar, c_ulong

from .base_window    import BaseWindow
from .rectangle      import Rectangle, unit
from .monitor        import monitors


#===========================================================================

class Win32Window(BaseWindow):
    """
        The Window class is an interface to the Win32 window control
        and placement.

    """

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        handle = win32gui.GetForegroundWindow()
        if handle in cls._windows_by_id:
            return cls._windows_by_id[handle]
        window = Win32Window(handle=handle)
        return window

    @classmethod
    def get_all_windows(cls):
        def function(handle, argument):
            argument.append(Win32Window(handle))
        argument = []
        win32gui.EnumWindows(function, argument)
        return argument

#    @classmethod
#    def get_window_by_executable(cls, executable):
#        def function(handle, argument):
#            title = windll.user32.GetWindowText(handle)
#            print "title: %r" % title
#        windll.user32.EnumWindows(function, argument)


    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, handle):
        super(Win32Window, self).__init__(id=handle)

    def __str__(self):
        args = ["handle=%d" % self.handle] + list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Direct access to various Win32 methods.

    def _win32gui_func(name):
        func = getattr(win32gui, name)
        return lambda self: func(self._handle)

    _get_rect           = _win32gui_func("GetWindowRect")
    _destroy            = _win32gui_func("DestroyWindow")
    _set_foreground     = _win32gui_func("SetForegroundWindow")
    _bring_to_top       = _win32gui_func("BringWindowToTop")
    _get_window_text    = _win32gui_func("GetWindowText")
    _get_class_name     = _win32gui_func("GetClassName")

    def _win32gui_test(name):
        test = getattr(win32gui, name)
        fget = lambda self: test(self._handle) and True or False
        return property(fget=fget,
                        doc="Shortcut to win32gui.%s() function." % name)

    is_valid        = _win32gui_test("IsWindow")
    is_enabled      = _win32gui_test("IsWindowEnabled")
    is_visible      = _win32gui_test("IsWindowVisible")
    is_minimized    = _win32gui_test("IsIconic")
#   is_maximized    = _win32gui_test("IsZoomed")  # IsZoomed is unavailable

    def _win32gui_show_window(state):
        return lambda self: win32gui.ShowWindow(self._handle, state)

    minimize        = _win32gui_show_window(win32con.SW_MINIMIZE)
    maximize        = _win32gui_show_window(win32con.SW_MAXIMIZE)
    restore         = _win32gui_show_window(win32con.SW_RESTORE)

    def _get_window_module(self):
        # Get this window's process ID.
        pid = c_ulong()
        windll.user32.GetWindowThreadProcessId(self._handle, pointer(pid))

        # Get the process handle of this window's process ID.
        #  Access permission flags:
        #  0x0410 = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        handle = windll.kernel32.OpenProcess(0x0410, 0, pid)

        # Retrieve and return the process's executable path.
        try:
            # Try to use the QueryForProcessImageNameW function
            #  available since Windows Vista.
            buffer_len = c_ulong(256)
            buffer = (c_wchar * buffer_len.value)()
            windll.kernel32.QueryFullProcessImageNameW(handle, 0,
                                                       pointer(buffer),
                                                       pointer(buffer_len))
            buffer = buffer[:]
            buffer = buffer[:buffer.index("\0")]
        except Exception:
            # If the function above failed, fall back to the older
            #  GetModuleFileNameEx function, available since windows XP.
            #  Note that this fallback function seems to fail when
            #  this process is 32 bit Python and handle refers to a
            #  64-bit process.
            buffer_len = 256
            buffer = (c_wchar * buffer_len)()
            windll.psapi.GetModuleFileNameExW(handle, 0, pointer(buffer),
                                              buffer_len)
            buffer = buffer[:]
            buffer = buffer[:buffer.index("\0")]
        finally:
            windll.kernel32.CloseHandle(handle)

        return str(buffer)

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        l, t, r, b = self._get_rect()
        w = r - l; h = b - t
        return Rectangle(l, t, w, h)

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        l, t, w, h = rectangle.ltwh
        win32gui.MoveWindow(self._handle, l, t, w, h, 1)

    def get_containing_monitor(self):
        center = self.get_position().center
        for monitor in monitors:
            if monitor.rectangle.contains(center):
                return monitor
        # Fall through, return first monitor.
        return monitors[0]

    def get_normalized_position(self):
        monitor = self.get_containing_monitor()
        rectangle = self.get_position()
        rectangle.renormalize(monitor.rectangle, unit)
        return rectangle

    def set_normalized_position(self, rectangle, monitor=None):
        if not monitor: monitor = self.get_containing_monitor()
        rectangle.renormalize(unit, monitor.rectangle)
        self.set_position(rectangle)

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def set_foreground(self):
        if self.is_minimized:
            self.restore()
        self._set_foreground()
