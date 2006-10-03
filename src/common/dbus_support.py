##  dbus_support.py
##
## Copyright (C) 2005 Yann Le Boulanger <asterix@lagaule.org>
## Copyright (C) 2005 Nikos Kouremenos <kourem@gmail.com>
## Copyright (C) 2005 Dimitur Kirov <dkirov@gmail.com>
## Copyright (C) 2005 Andrew Sayman <lorien420@myrealbox.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

import os
import sys

from common import gajim
from common import exceptions

_GAJIM_ERROR_IFACE = 'org.gajim.dbus.Error'

try:
	import dbus
	import dbus.service
	import dbus.glib
	supported = True # does use have D-Bus bindings?
except ImportError:
	supported = False
	if not os.name == 'nt': # only say that to non Windows users
		print _('D-Bus python bindings are missing in this computer')
		print _('D-Bus capabilities of Gajim cannot be used')

class SessionBus:
	'''A Singleton for the D-Bus SessionBus'''
	def __init__(self):
		self.session_bus = None
	
	def SessionBus(self):
		if not supported:
			raise exceptions.DbusNotSupported

		if not self.present():
				raise exceptions.SessionBusNotPresent
		return self.session_bus

	def bus(self):
		return self.SessionBus()

	def present(self):
		if not supported:
			return False
		if self.session_bus is None:
			try:
				self.session_bus = dbus.SessionBus()
			except dbus.dbus_bindings.DBusException:
				self.session_bus = None
				return False
			if self.session_bus is None:
				return False
		return True

session_bus = SessionBus()

def get_interface(interface, path):
	'''Returns an interface on the current SessionBus. If the interface isn't 
	running, it tries to start it first.'''
	if not supported:
		return None
	if session_bus.present():
		bus = session_bus.SessionBus()
	else:
		return None
	try:
		obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
		dbus_iface = dbus.Interface(obj, 'org.freedesktop.DBus')
		running_services = dbus_iface.ListNames()
		started = True
		if interface not in running_services:
			# try to start the service
			if dbus_iface.StartServiceByName(interface, dbus.UInt32(0)) == 1:
				started = True
			else:
				started = False
		if not started:
			return None
		obj = bus.get_object(interface, path)
		return dbus.Interface(obj, interface)
	except Exception, e:
		gajim.log.debug(str(e))
		return None


def get_notifications_interface():
	'''Returns the notifications interface.'''
	return get_interface('org.freedesktop.Notifications',
		'/org/freedesktop/Notifications')

if supported:
	class MissingArgument(dbus.DBusException):
		_dbus_error_name = _GAJIM_ERROR_IFACE + '.MissingArgument'
	
	class InvalidArgument(dbus.DBusException):
		'''Raised when one of the provided arguments is invalid.'''
		_dbus_error_name = _GAJIM_ERROR_IFACE + '.InvalidArgument'