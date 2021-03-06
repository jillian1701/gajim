#!/usr/bin/env python
# -*- coding:utf-8 -*-
## src/gajim.py
##
## Copyright (C) 2003-2008 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2004-2005 Vincent Hanquez <tab AT snarc.org>
## Copyright (C) 2005 Alex Podaras <bigpod AT gmail.com>
##                    Norman Rasmussen <norman AT rasmussen.co.za>
##                    Stéphan Kochen <stephan AT kochen.nl>
## Copyright (C) 2005-2006 Dimitur Kirov <dkirov AT gmail.com>
##                         Alex Mauer <hawke AT hawkesnest.net>
## Copyright (C) 2005-2007 Travis Shirk <travis AT pobox.com>
##                         Nikos Kouremenos <kourem AT gmail.com>
## Copyright (C) 2006 Junglecow J <junglecow AT gmail.com>
##                    Stefan Bethge <stefan AT lanpartei.de>
## Copyright (C) 2006-2008 Jean-Marie Traissard <jim AT lapin.org>
## Copyright (C) 2007 Lukas Petrovicky <lukas AT petrovicky.net>
##                    James Newton <redshodan AT gmail.com>
## Copyright (C) 2007-2008 Brendan Taylor <whateley AT gmail.com>
##                         Julien Pivotto <roidelapluie AT gmail.com>
##                         Stephan Erb <steve-e AT h3c.de>
## Copyright (C) 2008 Jonathan Schleifer <js-gajim AT webkeks.org>
##
## This file is part of Gajim.
##
## Gajim is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## Gajim is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Gajim. If not, see <http://www.gnu.org/licenses/>.
##

import os

if os.name == 'nt':
	import warnings
	warnings.filterwarnings(action='ignore')

	if os.path.isdir('gtk'):
		# Used to create windows installer with GTK included
		paths = os.environ['PATH']
		list_ = paths.split(';')
		new_list = []
		for p in list_:
			if p.find('gtk') < 0 and p.find('GTK') < 0:
				new_list.append(p)
		new_list.insert(0, 'gtk/lib')
		new_list.insert(0, 'gtk/bin')
		os.environ['PATH'] = ';'.join(new_list)
		os.environ['GTK_BASEPATH'] = 'gtk'

import sys

import logging
consoleloghandler = logging.StreamHandler()
consoleloghandler.setLevel(1)
consoleloghandler.setFormatter(
logging.Formatter('%(asctime)s %(name)s: %(levelname)s: %(message)s'))
log = logging.getLogger('gajim')
log.setLevel(logging.WARNING)
log.addHandler(consoleloghandler)
log.propagate = False
log = logging.getLogger('gajim.gajim')

# create intermediate loggers
logging.getLogger('gajim.c')
logging.getLogger('gajim.c.x')

import getopt
from common import i18n

def parseLogLevel(arg):
	if arg.isdigit():
		return int(arg)
	if arg.isupper():
		return getattr(logging, arg)
	raise ValueError(_('%s is not a valid loglevel'), repr(arg))

def parseLogTarget(arg):
	arg = arg.lower()
	if arg.startswith('.'): return arg[1:]
	if arg.startswith('gajim'): return arg
	return 'gajim.' + arg

def parseAndSetLogLevels(arg):
	for directive in arg.split(','):
		directive = directive.strip()
		targets, level = directive.rsplit('=', 1)
		level = parseLogLevel(level.strip())
		for target in targets.split('='):
			target = parseLogTarget(target.strip())
			if target == '':
				consoleloghandler.setLevel(level)
				print "consoleloghandler level set to %s" % level
			else:
				logger = logging.getLogger(target)
				logger.setLevel(level)
				print "Logger %s level set to %d" % (target, level)

def parseOpts():
	profile = ''
	verbose = False
	config_path = None

	try:
		shortargs = 'hqvl:p:c:'
		longargs = 'help quiet verbose loglevel= profile= config_path='
		opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs.split())
	except getopt.error, msg:
		print msg
		print 'for help use --help'
		sys.exit(2)
	for o, a in opts:
		if o in ('-h', '--help'):
			print 'gajim [--help] [--quiet] [--verbose] [--loglevel subsystem=level[,subsystem=level[...]]] [--profile name] [--config-path]'
			sys.exit()
		elif o in ('-q', '--quiet'):
			consoleloghandler.setLevel(logging.CRITICAL)
			verbose = False
		elif o in ('-v', '--verbose'):
			consoleloghandler.setLevel(logging.INFO)
			verbose = True
		elif o in ('-p', '--profile'): # gajim --profile name
			profile = a
		elif o in ('-l', '--loglevel'):
			parseAndSetLogLevels(a)
		elif o in ('-c', '--config-path'):
			config_path = a
	return profile, verbose, config_path

profile, verbose, config_path = parseOpts()
del parseOpts, parseAndSetLogLevels, parseLogTarget, parseLogLevel

import locale
profile = unicode(profile, locale.getpreferredencoding())

import common.configpaths
common.configpaths.gajimpaths.init(config_path)
del config_path
common.configpaths.gajimpaths.init_profile(profile)
del profile

# PyGTK2.10+ only throws a warning
import warnings
warnings.filterwarnings('error', module='gtk')
try:
	import gtk
except Warning, msg:
	if str(msg) == 'could not open display':
		print >> sys.stderr, _('Gajim needs X server to run. Quiting...')
		sys.exit()
warnings.resetwarnings()

if os.name == 'nt':
	import warnings
	warnings.filterwarnings(action='ignore')

pritext = ''

from common import exceptions
try:
	from common import gajim
except exceptions.DatabaseMalformed:
	pritext = _('Database Error')
	sectext = _('The database file (%s) cannot be read. Try to repair it or remove it (all history will be lost).') % common.logger.LOG_DB_PATH
else:
	from common import dbus_support
	if dbus_support.supported:
		import dbus

	if os.name == 'posix': # dl module is Unix Only
		try: # rename the process name to gajim
			import dl
			libc = dl.open('/lib/libc.so.6')
			libc.call('prctl', 15, 'gajim\0', 0, 0, 0)
		except Exception:
			pass

	if gtk.pygtk_version < (2, 8, 0):
		pritext = _('Gajim needs PyGTK 2.8 or above')
		sectext = _('Gajim needs PyGTK 2.8 or above to run. Quiting...')
	elif gtk.gtk_version < (2, 8, 0):
		pritext = _('Gajim needs GTK 2.8 or above')
		sectext = _('Gajim needs GTK 2.8 or above to run. Quiting...')

	try:
		import gtk.glade # check if user has libglade (in pygtk and in gtk)
	except ImportError:
		pritext = _('GTK+ runtime is missing libglade support')
		if os.name == 'nt':
			sectext = _('Please remove your current GTK+ runtime and install the latest stable version from %s') % 'http://gladewin32.sourceforge.net'
		else:
			sectext = _('Please make sure that GTK+ and PyGTK have libglade support in your system.')

	try:
		from common import check_paths
	except exceptions.PysqliteNotAvailable, e:
		pritext = _('Gajim needs PySQLite2 to run')
		sectext = str(e)

	if os.name == 'nt':
		try:
			import winsound # windows-only built-in module for playing wav
			import win32api # do NOT remove. we req this module
		except Exception:
			pritext = _('Gajim needs pywin32 to run')
			sectext = _('Please make sure that Pywin32 is installed on your system. You can get it at %s') % 'http://sourceforge.net/project/showfiles.php?group_id=78018'

if pritext:
	dlg = gtk.MessageDialog(None,
		gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
		gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message_format = pritext)

	dlg.format_secondary_text(sectext)
	dlg.run()
	dlg.destroy()
	sys.exit()

del pritext

import gtkexcepthook

import gobject
if not hasattr(gobject, 'timeout_add_seconds'):
	def timeout_add_seconds_fake(time_sec, *args):
		return gobject.timeout_add(time_sec * 1000, *args)
	gobject.timeout_add_seconds = timeout_add_seconds_fake

import re
import signal
import time
import math

import gtkgui_helpers
import notify
import message_control

from chat_control import ChatControlBase
from chat_control import ChatControl
from groupchat_control import GroupchatControl
from groupchat_control import PrivateChatControl
from atom_window import AtomWindow
from session import ChatControlSession

import common.sleepy

from common.xmpp import idlequeue
from common.zeroconf import connection_zeroconf
from common import nslookup
from common import proxy65_manager
from common import socks5
from common import helpers
from common import optparser
from common import dataforms

if verbose: gajim.verbose = True
del verbose

gajimpaths = common.configpaths.gajimpaths

pid_filename = gajimpaths['PID_FILE']
config_filename = gajimpaths['CONFIG_FILE']

import traceback
import errno

import dialogs
def pid_alive():
	try:
		pf = open(pid_filename)
	except IOError:
		# probably file not found
		return False

	try:
		pid = int(pf.read().strip())
		pf.close()
	except Exception:
		traceback.print_exc()
		# PID file exists, but something happened trying to read PID
		# Could be 0.10 style empty PID file, so assume Gajim is running
		return True

	if os.name == 'nt':
		try:
			from ctypes import (windll, c_ulong, c_int, Structure, c_char, POINTER, pointer, )
		except Exception:
			return True

		class PROCESSENTRY32(Structure):
			_fields_ = [
				('dwSize', c_ulong, ),
				('cntUsage', c_ulong, ),
				('th32ProcessID', c_ulong, ),
				('th32DefaultHeapID', c_ulong, ),
				('th32ModuleID', c_ulong, ),
				('cntThreads', c_ulong, ),
				('th32ParentProcessID', c_ulong, ),
				('pcPriClassBase', c_ulong, ),
				('dwFlags', c_ulong, ),
				('szExeFile', c_char*512, ),
				]
			def __init__(self):
				Structure.__init__(self, 512+9*4)

		k = windll.kernel32
		k.CreateToolhelp32Snapshot.argtypes = c_ulong, c_ulong,
		k.CreateToolhelp32Snapshot.restype = c_int
		k.Process32First.argtypes = c_int, POINTER(PROCESSENTRY32),
		k.Process32First.restype = c_int
		k.Process32Next.argtypes = c_int, POINTER(PROCESSENTRY32),
		k.Process32Next.restype = c_int

		def get_p(p):
			h = k.CreateToolhelp32Snapshot(2, 0) # TH32CS_SNAPPROCESS
			assert h > 0, 'CreateToolhelp32Snapshot failed'
			b = pointer(PROCESSENTRY32())
			f = k.Process32First(h, b)
			while f:
				if b.contents.th32ProcessID == p:
					return b.contents.szExeFile
				f = k.Process32Next(h, b)

		if get_p(pid) in ('python.exe', 'gajim.exe'):
			return True
		return False
	elif sys.platform == 'darwin':
		try:
			from osx import checkPID
			return checkPID(pid, 'Gajim.bin')
		except ImportError:
			return
	try:
		if not os.path.exists('/proc'):
			return True # no /proc, assume Gajim is running

		try:
			f = open('/proc/%d/cmdline'% pid)
		except IOError, e:
			if e.errno == errno.ENOENT:
				return False # file/pid does not exist
			raise

		n = f.read().lower()
		f.close()
		if n.find('gajim') < 0:
			return False
		return True # Running Gajim found at pid
	except Exception:
		traceback.print_exc()

	# If we are here, pidfile exists, but some unexpected error occured.
	# Assume Gajim is running.
	return True

if pid_alive():
	path_to_file = os.path.join(gajim.DATA_DIR, 'pixmaps/gajim.png')
	pix = gtk.gdk.pixbuf_new_from_file(path_to_file)
	gtk.window_set_default_icon(pix) # set the icon to all newly opened wind
	pritext = _('Gajim is already running')
	sectext = _('Another instance of Gajim seems to be running\nRun anyway?')
	dialog = dialogs.YesNoDialog(pritext, sectext)
	dialog.popup()
	if dialog.run() != gtk.RESPONSE_YES:
		sys.exit(3)
	dialog.destroy()
	# run anyway, delete pid and useless global vars
	if os.path.exists(pid_filename):
		os.remove(pid_filename)
	del path_to_file
	del pix
	del pritext
	del sectext
	dialog.destroy()

# Create .gajim dir
pid_dir =  os.path.dirname(pid_filename)
if not os.path.exists(pid_dir):
	check_paths.create_path(pid_dir)
# Create pid file
try:
	f = open(pid_filename, 'w')
	f.write(str(os.getpid()))
	f.close()
except IOError, e:
	dlg = dialogs.ErrorDialog(_('Disk Write Error'), str(e))
	dlg.run()
	dlg.destroy()
	sys.exit()
del pid_dir
del f

def on_exit():
	# delete pid file on normal exit
	if os.path.exists(pid_filename):
		os.remove(pid_filename)
	# Save config
	gajim.interface.save_config()
	if sys.platform == 'darwin':
		try:
			import osx
			osx.shutdown()
		except ImportError:
			pass

import atexit
atexit.register(on_exit)

parser = optparser.OptionsParser(config_filename)

import roster_window
import profile_window
import config

class GlibIdleQueue(idlequeue.IdleQueue):
	'''
	Extends IdleQueue to use glib io_add_wath, instead of select/poll
	In another, `non gui' implementation of Gajim IdleQueue can be used safetly.
	'''
	def init_idle(self):
		''' this method is called at the end of class constructor.
		Creates a dict, which maps file/pipe/sock descriptor to glib event id'''
		self.events = {}
		# time() is already called in glib, we just get the last value
		# overrides IdleQueue.current_time()
		self.current_time = lambda: gobject.get_current_time()

	def add_idle(self, fd, flags):
		''' this method is called when we plug a new idle object.
		Start listening for events from fd
		'''
		res = gobject.io_add_watch(fd, flags, self._process_events,
			priority=gobject.PRIORITY_LOW)
		# store the id of the watch, so that we can remove it on unplug
		self.events[fd] = res

	def _process_events(self, fd, flags):
		try:
			return self.process_events(fd, flags)
		except Exception:
			self.remove_idle(fd)
			self.add_idle(fd, flags)
			raise

	def remove_idle(self, fd):
		''' this method is called when we unplug a new idle object.
		Stop listening for events from fd
		'''
		gobject.source_remove(self.events[fd])
		del(self.events[fd])

	def process(self):
		self.check_time_events()

class PassphraseRequest:
	def __init__(self, keyid):
		self.keyid = keyid
		self.callbacks = []
		self.dialog_created = False
		self.completed = False

	def run_callback(self, account, callback):
		gajim.connections[account].gpg_passphrase(self.passphrase)
		callback()

	def add_callback(self, account, cb):
		if self.completed:
			self.run_callback(account, cb)
		else:
			self.callbacks.append((account, cb))
			if not self.dialog_created:
				self.create_dialog(account)

	def complete(self, passphrase):
		self.passphrase = passphrase
		self.completed = True
		if passphrase is not None:
			gobject.timeout_add_seconds(30, gajim.interface.forget_gpg_passphrase,
				self.keyid)
		for (account, cb) in self.callbacks:
			self.run_callback(account, cb)
		del self.callbacks

	def create_dialog(self, account):
		title = _('Passphrase Required')
		second = _('Enter GPG key passphrase for key %(keyid)s (account '
			'%(account)s).') % {'keyid': self.keyid, 'account': account}

		def _cancel():
			# user cancelled, continue without GPG
			self.complete(None)

		def _ok(passphrase, checked, count):
			if gajim.connections[account].test_gpg_passphrase(passphrase):
				# passphrase is good
				self.complete(passphrase)
				return

			if count < 3:
				# ask again
				dialogs.PassphraseDialog(_('Wrong Passphrase'),
					_('Please retype your GPG passphrase or press Cancel.'),
					ok_handler=(_ok, count + 1), cancel_handler=_cancel)
			else:
				# user failed 3 times, continue without GPG
				self.complete(None)

		dialogs.PassphraseDialog(title, second, ok_handler=(_ok, 1),
			cancel_handler=_cancel)
		self.dialog_created = True

class Interface:

################################################################################		
### Methods handling events from connection 
################################################################################	

	def handle_event_roster(self, account, data):
		#('ROSTER', account, array)
		# FIXME: Those methods depend to highly on each other
		# and the order in which they are called
		self.roster.fill_contacts_and_groups_dicts(data, account)
		self.roster.add_account_contacts(account)
		self.roster.fire_up_unread_messages_events(account)
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('Roster', (account, data))

	def handle_event_warning(self, unused, data):
		#('WARNING', account, (title_text, section_text))
		dialogs.WarningDialog(data[0], data[1])

	def handle_event_error(self, unused, data):
		#('ERROR', account, (title_text, section_text))
		dialogs.ErrorDialog(data[0], data[1])

	def handle_event_information(self, unused, data):
		#('INFORMATION', account, (title_text, section_text))
		dialogs.InformationDialog(data[0], data[1])

	def handle_event_ask_new_nick(self, account, data):
		#('ASK_NEW_NICK', account, (room_jid,))
		room_jid = data[0]
		gc_control = self.msg_win_mgr.get_gc_control(room_jid, account)
		if not gc_control and \
		room_jid in self.minimized_controls[account]:
			gc_control = self.minimized_controls[account][room_jid]
		if gc_control: # user may close the window before we are here
			title = _('Unable to join group chat')
			prompt = _('Your desired nickname in group chat %s is in use or '
				'registered by another occupant.\nPlease specify another nickname '
				'below:') % room_jid
			gc_control.show_change_nick_input_dialog(title, prompt)

	def handle_event_http_auth(self, account, data):
		#('HTTP_AUTH', account, (method, url, transaction_id, iq_obj, msg))
		def response(account, iq_obj, answer):
			self.dialog.destroy()
			gajim.connections[account].build_http_auth_answer(iq_obj, answer)

		def on_yes(is_checked, account, iq_obj):
			response(account, iq_obj, 'yes')

		sec_msg = _('Do you accept this request?')
		if gajim.get_number_of_connected_accounts() > 1:
			sec_msg = _('Do you accept this request on account %s?') % account
		if data[4]:
			sec_msg = data[4] + '\n' + sec_msg
		self.dialog = dialogs.YesNoDialog(_('HTTP (%(method)s) Authorization for '
			'%(url)s (id: %(id)s)') % {'method': data[0], 'url': data[1],
			'id': data[2]}, sec_msg, on_response_yes=(on_yes, account, data[3]),
			on_response_no=(response, account, data[3], 'no'))

	def handle_event_error_answer(self, account, array):
		#('ERROR_ANSWER', account, (id, jid_from, errmsg, errcode))
		id, jid_from, errmsg, errcode = array
		if unicode(errcode) in ('403', '406') and id:
			# show the error dialog
			ft = self.instances['file_transfers']
			sid = id
			if len(id) > 3 and id[2] == '_':
				sid = id[3:]
			if sid in ft.files_props['s']:
				file_props = ft.files_props['s'][sid]
				file_props['error'] = -4
				self.handle_event_file_request_error(account,
					(jid_from, file_props, errmsg))
				conn = gajim.connections[account]
				conn.disconnect_transfer(file_props)
				return
		elif unicode(errcode) == '404':
			conn = gajim.connections[account]
			sid = id
			if len(id) > 3 and id[2] == '_':
				sid = id[3:]
			if sid in conn.files_props:
				file_props = conn.files_props[sid]
				self.handle_event_file_send_error(account,
					(jid_from, file_props))
				conn.disconnect_transfer(file_props)
				return

		ctrl = self.msg_win_mgr.get_control(jid_from, account)
		if ctrl and ctrl.type_id == message_control.TYPE_GC:
			ctrl.print_conversation('Error %s: %s' % (array[2], array[1]))

	def handle_event_con_type(self, account, con_type):
		# ('CON_TYPE', account, con_type) which can be 'ssl', 'tls', 'tcp'
		gajim.con_types[account] = con_type
		self.roster.draw_account(account)

	def handle_event_connection_lost(self, account, array):
		# ('CONNECTION_LOST', account, [title, text])
		path = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events',
			'connection_lost.png')
		path = gtkgui_helpers.get_path_to_generic_or_avatar(path)
		notify.popup(_('Connection Failed'), account, account,
			'connection_failed', path, array[0], array[1])

	def unblock_signed_in_notifications(self, account):
		gajim.block_signed_in_notifications[account] = False

	def handle_event_status(self, account, status): # OUR status
		#('STATUS', account, status)
		model = self.roster.status_combobox.get_model()
		if status == 'offline':
			# sensitivity for this menuitem
			if gajim.get_number_of_connected_accounts() == 0:
				model[self.roster.status_message_menuitem_iter][3] = False
			gajim.block_signed_in_notifications[account] = True
		else:
			# 30 seconds after we change our status to sth else than offline
			# we stop blocking notifications of any kind
			# this prevents from getting the roster items as 'just signed in'
			# contacts. 30 seconds should be enough time
			gobject.timeout_add_seconds(30, self.unblock_signed_in_notifications, account)
			# sensitivity for this menuitem
			model[self.roster.status_message_menuitem_iter][3] = True

		# Inform all controls for this account of the connection state change
		ctrls = self.msg_win_mgr.get_controls()
		if account in self.minimized_controls:
			# Can not be the case when we remove account
			ctrls += self.minimized_controls[account].values()
		for ctrl in ctrls:
			if ctrl.account == account:
				if status == 'offline' or (status == 'invisible' and \
				gajim.connections[account].is_zeroconf):
					ctrl.got_disconnected()
				else:
					# Other code rejoins all GCs, so we don't do it here
					if not ctrl.type_id == message_control.TYPE_GC:
						ctrl.got_connected()
				if ctrl.parent_win:
					ctrl.parent_win.redraw_tab(ctrl)

		self.roster.on_status_changed(account, status)
		if account in self.show_vcard_when_connect:
			self.edit_own_details(account)
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('AccountPresence', (status, account))

	def edit_own_details(self, account):
		jid = gajim.get_jid_from_account(account)
		if 'profile' not in self.instances[account]:
			self.instances[account]['profile'] = \
				profile_window.ProfileWindow(account)
			gajim.connections[account].request_vcard(jid)

	def handle_event_notify(self, account, array):
		# 'NOTIFY' (account, (jid, status, status message, resource,
		# priority, # keyID, timestamp, contact_nickname))
		#
		# Contact changed show

		# FIXME: Drop and rewrite...

		statuss = ['offline', 'error', 'online', 'chat', 'away', 'xa', 'dnd',
			'invisible']
		# Ignore invalid show
		if array[1] not in statuss:
			return
		old_show = 0
		new_show = statuss.index(array[1])
		status_message = array[2]
		jid = array[0].split('/')[0]
		keyID = array[5]
		contact_nickname = array[7]

		# Get the proper keyID
		keyID = helpers.prepare_and_validate_gpg_keyID(account, jid, keyID)

		resource = array[3]
		if not resource:
			resource = ''
		priority = array[4]
		if gajim.jid_is_transport(jid):
			# It must be an agent
			ji = jid.replace('@', '')
		else:
			ji = jid

		highest = gajim.contacts. \
			get_contact_with_highest_priority(account, jid)
		was_highest = (highest and highest.resource == resource)

		conn = gajim.connections[account]

		# Update contact
		jid_list = gajim.contacts.get_jid_list(account)
		if ji in jid_list or jid == gajim.get_jid_from_account(account):
			lcontact = gajim.contacts.get_contacts(account, ji)
			contact1 = None
			resources = []
			for c in lcontact:
				resources.append(c.resource)
				if c.resource == resource:
					contact1 = c
					break

			if contact1:
				if contact1.show in statuss:
					old_show = statuss.index(contact1.show)
				# nick changed
				if contact_nickname is not None and \
				contact1.contact_name != contact_nickname:
					contact1.contact_name = contact_nickname
					self.roster.draw_contact(jid, account)

				if old_show == new_show and contact1.status == status_message and \
				contact1.priority == priority: # no change
					return
			else:
				contact1 = gajim.contacts.get_first_contact_from_jid(account, ji)
				if not contact1:
					# Presence of another resource of our
					# jid
					# Create self contact and add to roster
					if resource == conn.server_resource:
						return
					contact1 = gajim.contacts.create_contact(jid=ji,
						name=gajim.nicks[account], groups=['self_contact'],
						show=array[1], status=status_message, sub='both', ask='none',
						priority=priority, keyID=keyID, resource=resource,
						mood=conn.mood, tune=conn.tune, activity=conn.activity)
					old_show = 0
					gajim.contacts.add_contact(account, contact1)
					lcontact.append(contact1)
				elif contact1.show in statuss:
					old_show = statuss.index(contact1.show)
				# FIXME: What am I?
				if (resources != [''] and (len(lcontact) != 1 or \
				lcontact[0].show != 'offline')) and jid.find('@') > 0:
					old_show = 0
					contact1 = gajim.contacts.copy_contact(contact1)
					lcontact.append(contact1)
				contact1.resource = resource

				self.roster.add_contact(contact1.jid, account)

			if contact1.jid.find('@') > 0 and len(lcontact) == 1:
				# It's not an agent
				if old_show == 0 and new_show > 1:
					if not contact1.jid in gajim.newly_added[account]:
						gajim.newly_added[account].append(contact1.jid)
					if contact1.jid in gajim.to_be_removed[account]:
						gajim.to_be_removed[account].remove(contact1.jid)
					gobject.timeout_add_seconds(5, self.roster.remove_newly_added,
						contact1.jid, account)
				elif old_show > 1 and new_show == 0 and conn.connected > 1:
					if not contact1.jid in gajim.to_be_removed[account]:
						gajim.to_be_removed[account].append(contact1.jid)
					if contact1.jid in gajim.newly_added[account]:
						gajim.newly_added[account].remove(contact1.jid)
					self.roster.draw_contact(contact1.jid, account)
					gobject.timeout_add_seconds(5, self.roster.remove_to_be_removed,
						contact1.jid, account)
			contact1.show = array[1]
			contact1.status = status_message
			contact1.priority = priority
			contact1.keyID = keyID
			timestamp = array[6]
			if timestamp:
				contact1.last_status_time = timestamp
			elif not gajim.block_signed_in_notifications[account]:
				# We're connected since more that 30 seconds
				contact1.last_status_time = time.localtime()
			contact1.contact_nickname = contact_nickname

		if gajim.jid_is_transport(jid):
			# It must be an agent
			if ji in jid_list:
				# Update existing iter and group counting
				self.roster.draw_contact(ji, account)
				self.roster.draw_group(_('Transports'), account)				
				if new_show > 1 and ji in gajim.transport_avatar[account]:
					# transport just signed in.
					# request avatars
					for jid_ in gajim.transport_avatar[account][ji]:
						conn.request_vcard(jid_)
				# transport just signed in/out, don't show
				# popup notifications for 30s
				account_ji = account + '/' + ji
				gajim.block_signed_in_notifications[account_ji] = True
				gobject.timeout_add_seconds(30,
					self.unblock_signed_in_notifications, account_ji)
			locations = (self.instances, self.instances[account])
			for location in locations:
				if 'add_contact' in location:
					if old_show == 0 and new_show > 1:
						location['add_contact'].transport_signed_in(jid)
						break
					elif old_show > 1 and new_show == 0:
						location['add_contact'].transport_signed_out(jid)
						break
		elif ji in jid_list:
			# It isn't an agent
			# reset chatstate if needed:
			# (when contact signs out or has errors)
			if array[1] in ('offline', 'error'):
				contact1.our_chatstate = contact1.chatstate = \
					contact1.composing_xep = None

				# TODO: This causes problems when another
				#	resource signs off!
				conn.remove_transfers_for_contact(contact1)

				# disable encryption, since if any messages are
				# lost they'll be not decryptable (note that
				# this contradicts XEP-0201 - trying to get that
				# in the XEP, though)
				#
				# FIXME: This *REALLY* are TOO many leves of
				#	 indentation! We even need to introduce
				#	 a temp var here to make it somehow fit!
				for sess in conn.get_sessions(ji):
					if (ji+'/'+resource) != str(sess.jid):
						continue
					ctrl = sess.control
					if ctrl:
						ctrl.no_autonegotiation = False
					if sess.enable_encryption:
						sess.terminate_e2e()
						conn.delete_session(jid,
						sess.thread_id)

			self.roster.chg_contact_status(contact1, array[1], status_message,
				account)
			# Notifications
			if old_show < 2 and new_show > 1:
				notify.notify('contact_connected', jid, account, status_message)
				if self.remote_ctrl:
					self.remote_ctrl.raise_signal('ContactPresence', (account,
						array))

			elif old_show > 1 and new_show < 2:
				notify.notify('contact_disconnected', jid, account, status_message)
				if self.remote_ctrl:
					self.remote_ctrl.raise_signal('ContactAbsence', (account, array))
				# FIXME: stop non active file transfers
			# Status change (not connected/disconnected or
			# error (<1))
			elif new_show > 1:
				notify.notify('status_change', jid, account, [new_show,
					status_message])
				if self.remote_ctrl:
					self.remote_ctrl.raise_signal('ContactStatus', (account, array))
		else:
			# FIXME: MSN transport (CMSN1.2.1 and PyMSN) don't
			#	 follow the XEP, still the case in 2008.
			#	 It's maybe a GC_NOTIFY (specialy for MSN gc)
			self.handle_event_gc_notify(account, (jid, array[1], status_message,
				array[3], None, None, None, None, None, [], None, None))

		highest = gajim.contacts.get_contact_with_highest_priority(account, jid)
		is_highest = (highest and highest.resource == resource)

		# disconnect the session from the ctrl if the highest resource has changed
		if (was_highest and not is_highest) or (not was_highest and is_highest):
			ctrl = self.msg_win_mgr.get_control(jid, account)

			if ctrl:
				ctrl.set_session(None)
				ctrl.contact = highest

	def handle_event_msgerror(self, account, array):
		#'MSGERROR' (account, (jid, error_code, error_msg, msg, time[, session]))
		full_jid_with_resource = array[0]
		jids = full_jid_with_resource.split('/', 1)
		jid = jids[0]

		session = None
		if len(array) > 5:
			session = array[5]

		gc_control = self.msg_win_mgr.get_gc_control(jid, account)
		if not gc_control and \
		jid in self.minimized_controls[account]:
			gc_control = self.minimized_controls[account][jid]
		if gc_control and gc_control.type_id != message_control.TYPE_GC:
			gc_control = None
		if gc_control:
			if len(jids) > 1: # it's a pm
				nick = jids[1]

				if session:
					ctrl = session.control
				else:
					ctrl = self.msg_win_mgr.get_control(full_jid_with_resource, account)

				if not ctrl:
					tv = gc_control.list_treeview
					model = tv.get_model()
					iter = gc_control.get_contact_iter(nick)
					if iter:
						show = model[iter][3]
					else:
						show = 'offline'
					gc_c = gajim.contacts.create_gc_contact(room_jid = jid,
						name = nick, show = show)
					ctrl = self.new_private_chat(gc_c, account, session)

				ctrl.print_conversation(_('Error %(code)s: %(msg)s') % {
					'code': array[1], 'msg': array[2]}, 'status')
				return

			gc_control.print_conversation(_('Error %(code)s: %(msg)s') % {
				'code': array[1], 'msg': array[2]}, 'status')
			if gc_control.parent_win and gc_control.parent_win.get_active_jid() == jid:
				gc_control.set_subject(gc_control.subject)
			return

		if gajim.jid_is_transport(jid):
			jid = jid.replace('@', '')
		msg = array[2]
		if array[3]:
			msg = _('error while sending %(message)s ( %(error)s )') % {
				'message': array[3], 'error': msg}
		array[5].roster_message(jid, msg, array[4], msg_type='error')

	def handle_event_msgsent(self, account, array):
		#('MSGSENT', account, (jid, msg, keyID))
		msg = array[1]
		# do not play sound when standalone chatstate message (eg no msg)
		if msg and gajim.config.get_per('soundevents', 'message_sent', 'enabled'):
			helpers.play_sound('message_sent')

	def handle_event_msgnotsent(self, account, array):
		#('MSGNOTSENT', account, (jid, ierror_msg, msg, time, session))
		msg = _('error while sending %(message)s ( %(error)s )') % {
			'message': array[2], 'error': array[1]}
		array[4].roster_message(array[0], msg, array[3], account,
			msg_type='error')

	def handle_event_subscribe(self, account, array):
		#('SUBSCRIBE', account, (jid, text, user_nick)) user_nick is JEP-0172
		dialogs.SubscriptionRequestWindow(array[0], array[1], account, array[2])
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('Subscribe', (account, array))

	def handle_event_subscribed(self, account, array):
		#('SUBSCRIBED', account, (jid, resource))
		jid = array[0]
		if jid in gajim.contacts.get_jid_list(account):
			c = gajim.contacts.get_first_contact_from_jid(account, jid)
			c.resource = array[1]
			self.roster.remove_contact_from_groups(c.jid, account,
				[('Not in Roster'),])
		else:
			keyID = ''
			attached_keys = gajim.config.get_per('accounts', account,
				'attached_gpg_keys').split()
			if jid in attached_keys:
				keyID = attached_keys[attached_keys.index(jid) + 1]
			name = jid.split('@', 1)[0]
			name = name.split('%', 1)[0]
			contact1 = gajim.contacts.create_contact(jid=jid, name=name,
				groups=[], show='online', status='online',
				ask='to', resource=array[1], keyID=keyID)
			gajim.contacts.add_contact(account, contact1)
			self.roster.add_contact(jid, account)
		dialogs.InformationDialog(_('Authorization accepted'),
				_('The contact "%s" has authorized you to see his or her status.')
				% jid)
		if not gajim.config.get_per('accounts', account, 'dont_ack_subscription'):
			gajim.connections[account].ack_subscribed(jid)
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('Subscribed', (account, array))

	def handle_event_unsubscribed(self, account, jid):
		gajim.connections[account].ack_unsubscribed(jid)
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('Unsubscribed', (account, jid))

		contact = gajim.contacts.get_first_contact_from_jid(account, jid)
		if not contact:
			return
		def on_yes(is_checked, list_):
			self.roster.on_req_usub(None, list_)
		list_ = [(contact, account)]
		dialogs.YesNoDialog(
			_('Contact "%s" removed subscription from you') % jid,
			_('You will always see him or her as offline.\nDo you want to remove him or her from your contact list?'),
			on_response_yes=(on_yes, list_))
		# FIXME: Per RFC 3921, we can "deny" ack as well, but the GUI does not show deny

	def handle_event_agent_info_error(self, account, agent):
		#('AGENT_ERROR_INFO', account, (agent))
		try:
			gajim.connections[account].services_cache.agent_info_error(agent)
		except AttributeError:
			return

	def handle_event_agent_items_error(self, account, agent):
		#('AGENT_ERROR_INFO', account, (agent))
		try:
			gajim.connections[account].services_cache.agent_items_error(agent)
		except AttributeError:
			return

	def handle_event_agent_removed(self, account, agent):
		# remove transport's contacts from treeview
		jid_list = gajim.contacts.get_jid_list(account)
		for jid in jid_list:
			if jid.endswith('@' + agent):
				c = gajim.contacts.get_first_contact_from_jid(account, jid)
				gajim.log.debug(
					'Removing contact %s due to unregistered transport %s'\
					% (jid, agent))
				gajim.connections[account].unsubscribe(c.jid)
				# Transport contacts can't have 2 resources
				if c.jid in gajim.to_be_removed[account]:
					# This way we'll really remove it
					gajim.to_be_removed[account].remove(c.jid)
				self.roster.remove_contact(c.jid, account, backend=True)

	def handle_event_register_agent_info(self, account, array):
		# ('REGISTER_AGENT_INFO', account, (agent, infos, is_form))
		# info in a dataform if is_form is True
		if array[2] or 'instructions' in array[1]:
			config.ServiceRegistrationWindow(array[0], array[1], account,
				array[2])
		else:
			dialogs.ErrorDialog(_('Contact with "%s" cannot be established') \
				% array[0], _('Check your connection or try again later.'))

	def handle_event_agent_info_items(self, account, array):
		#('AGENT_INFO_ITEMS', account, (agent, node, items))
		our_jid = gajim.get_jid_from_account(account)
		if 'pep_services' in gajim.interface.instances[account] and \
		array[0] == our_jid:
			gajim.interface.instances[account]['pep_services'].items_received(
				array[2])
		try:
			gajim.connections[account].services_cache.agent_items(array[0],
				array[1], array[2])
		except AttributeError:
			return

	def handle_event_agent_info_info(self, account, array):
		#('AGENT_INFO_INFO', account, (agent, node, identities, features, data))
		try:
			gajim.connections[account].services_cache.agent_info(array[0],
				array[1], array[2], array[3], array[4])
		except AttributeError:
			return

	def handle_event_new_acc_connected(self, account, array):
		#('NEW_ACC_CONNECTED', account, (infos, is_form, ssl_msg, ssl_err,
		# ssl_cert, ssl_fingerprint))
		if 'account_creation_wizard' in self.instances:
			self.instances['account_creation_wizard'].new_acc_connected(array[0],
				array[1], array[2], array[3], array[4], array[5])

	def handle_event_new_acc_not_connected(self, account, array):
		#('NEW_ACC_NOT_CONNECTED', account, (reason))
		if 'account_creation_wizard' in self.instances:
			self.instances['account_creation_wizard'].new_acc_not_connected(array)

	def handle_event_acc_ok(self, account, array):
		#('ACC_OK', account, (config))
		if 'account_creation_wizard' in self.instances:
			self.instances['account_creation_wizard'].acc_is_ok(array)

		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('NewAccount', (account, array))

	def handle_event_acc_not_ok(self, account, array):
		#('ACC_NOT_OK', account, (reason))
		if 'account_creation_wizard' in self.instances:
			self.instances['account_creation_wizard'].acc_is_not_ok(array)

	def handle_event_quit(self, p1, p2):
		self.roster.quit_gtkgui_interface()

	def handle_event_myvcard(self, account, array):
		nick = ''
		if 'NICKNAME' in array and array['NICKNAME']:
			gajim.nicks[account] = array['NICKNAME']
		elif 'FN' in array and array['FN']:
			gajim.nicks[account] = array['FN']
		if 'profile' in self.instances[account]:
			win = self.instances[account]['profile']
			win.set_values(array)
			if account in self.show_vcard_when_connect:
				self.show_vcard_when_connect.remove(account)
		jid = array['jid']
		if jid in self.instances[account]['infos']:
			self.instances[account]['infos'][jid].set_values(array)

	def handle_event_vcard(self, account, vcard):
		# ('VCARD', account, data)
		'''vcard holds the vcard data'''
		jid = vcard['jid']
		resource = vcard.get('resource', '')
		fjid = jid + '/' + str(resource)

		# vcard window
		win = None
		if jid in self.instances[account]['infos']:
			win = self.instances[account]['infos'][jid]
		elif resource and fjid in self.instances[account]['infos']:
			win = self.instances[account]['infos'][fjid]
		if win:
			win.set_values(vcard)

		# show avatar in chat
		ctrl = None
		if resource and self.msg_win_mgr.has_window(fjid, account):
			win = self.msg_win_mgr.get_window(fjid, account)
			ctrl = win.get_control(fjid, account)
		elif self.msg_win_mgr.has_window(jid, account):
			win = self.msg_win_mgr.get_window(jid, account)
			ctrl = win.get_control(jid, account)

		if ctrl and ctrl.type_id != message_control.TYPE_GC:
			ctrl.show_avatar()

		# Show avatar in roster or gc_roster
		gc_ctrl = self.msg_win_mgr.get_gc_control(jid, account)
		if not gc_ctrl and \
		jid in self.minimized_controls[account]:
			gc_ctrl = self.minimized_controls[account][jid]
		if gc_ctrl and gc_ctrl.type_id == message_control.TYPE_GC:
			gc_ctrl.draw_avatar(resource)
		else:
			self.roster.draw_avatar(jid, account)
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('VcardInfo', (account, vcard))

	def handle_event_last_status_time(self, account, array):
		# ('LAST_STATUS_TIME', account, (jid, resource, seconds, status))
		tim = array[2]
		if tim < 0:
			# Ann error occured
			return
		win = None
		if array[0] in self.instances[account]['infos']:
			win = self.instances[account]['infos'][array[0]]
		elif array[0] + '/' + array[1] in self.instances[account]['infos']:
			win = self.instances[account]['infos'][array[0] + '/' + array[1]]
		if win:
			c = gajim.contacts.get_contact(account, array[0], array[1])
			if c: # c can be none if it's a gc contact
				c.last_status_time = time.localtime(time.time() - tim)
				if array[3]:
					c.status = array[3]
				win.set_last_status_time()
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('LastStatusTime', (account, array))

	def handle_event_os_info(self, account, array):
		#'OS_INFO' (account, (jid, resource, client_info, os_info))
		win = None
		if array[0] in self.instances[account]['infos']:
			win = self.instances[account]['infos'][array[0]]
		elif array[0] + '/' + array[1] in self.instances[account]['infos']:
			win = self.instances[account]['infos'][array[0] + '/' + array[1]]
		if win:
			win.set_os_info(array[1], array[2], array[3])
		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('OsInfo', (account, array))

	def handle_event_gc_notify(self, account, array):
		#'GC_NOTIFY' (account, (room_jid, show, status, nick,
		# role, affiliation, jid, reason, actor, statusCode, newNick, avatar_sha))
		nick = array[3]
		if not nick:
			return
		room_jid = array[0]
		fjid = room_jid + '/' + nick
		show = array[1]
		status = array[2]

		# Get the window and control for the updated status, this may be a
		# PrivateChatControl
		control = self.msg_win_mgr.get_gc_control(room_jid, account)

		if not control and \
		room_jid in self.minimized_controls[account]:
			control = self.minimized_controls[account][room_jid]

		if not control or (control and control.type_id != message_control.TYPE_GC):
			return

		control.chg_contact_status(nick, show, status, array[4], array[5],
			array[6], array[7], array[8], array[9], array[10], array[11])

		contact = gajim.contacts.\
			get_contact_with_highest_priority(account, room_jid)
		if contact:
			self.roster.draw_contact(room_jid, account)

		# print status in chat window and update status/GPG image
		ctrl = self.msg_win_mgr.get_control(fjid, account)
		if ctrl:
			statusCode = array[9]
			if '303' in statusCode:
				new_nick = array[10]
				ctrl.print_conversation(_('%(nick)s is now known as %(new_nick)s') \
					% {'nick': nick, 'new_nick': new_nick}, 'status')
				gc_c = gajim.contacts.get_gc_contact(account, room_jid, new_nick)
				c = gajim.contacts.contact_from_gc_contact(gc_c)
				ctrl.gc_contact = gc_c
				ctrl.contact = c
				ctrl.draw_banner()
				old_jid = room_jid + '/' + nick
				new_jid = room_jid + '/' + new_nick
				self.msg_win_mgr.change_key(old_jid, new_jid, account)
			else:
				contact = ctrl.contact
				contact.show = show
				contact.status = status
				uf_show = helpers.get_uf_show(show)
				ctrl.print_conversation(_('%(nick)s is now %(status)s') % {
					'nick': nick, 'status': uf_show}, 'status')
				if status:
					ctrl.print_conversation(' (', 'status', simple=True)
					ctrl.print_conversation('%s' % (status), 'status', simple=True)
					ctrl.print_conversation(')', 'status', simple=True)
				ctrl.parent_win.redraw_tab(ctrl)
				ctrl.update_ui()
			if self.remote_ctrl:
				self.remote_ctrl.raise_signal('GCPresence', (account, array))

	def handle_event_gc_msg(self, account, array):
		# ('GC_MSG', account, (jid, msg, time, has_timestamp, htmlmsg,
		# [status_codes]))
		jids = array[0].split('/', 1)
		room_jid = jids[0]

		gc_control = self.msg_win_mgr.get_gc_control(room_jid, account)
		if not gc_control and \
		room_jid in self.minimized_controls[account]:
			gc_control = self.minimized_controls[account][room_jid]

		if not gc_control:
			return
		xhtml = array[4]

		if gajim.config.get('ignore_incoming_xhtml'):
			xhtml = None
		if len(jids) == 1:
			# message from server
			nick = ''
		else:
			# message from someone
			nick = jids[1]

		gc_control.on_message(nick, array[1], array[2], array[3], xhtml, array[5])

		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('GCMessage', (account, array))

	def handle_event_gc_subject(self, account, array):
		#('GC_SUBJECT', account, (jid, subject, body, has_timestamp))
		jids = array[0].split('/', 1)
		jid = jids[0]

		gc_control = self.msg_win_mgr.get_gc_control(jid, account)

		if not gc_control and \
		jid in self.minimized_controls[account]:
			gc_control = self.minimized_controls[account][jid]

		contact = gajim.contacts.\
			get_contact_with_highest_priority(account, jid)
		if contact:
			contact.status = array[1]
			self.roster.draw_contact(jid, account)

		if not gc_control:
			return
		gc_control.set_subject(array[1])
		# Standard way, the message comes from the occupant who set the subject
		text = None
		if len(jids) > 1:
			text = _('%(jid)s has set the subject to %(subject)s') % {
				'jid': jids[1], 'subject': array[1]}
		# Workaround for psi bug http://flyspray.psi-im.org/task/595 , to be
		# deleted one day. We can receive a subject with a body that contains
		# "X has set the subject to Y" ...
		elif array[2]:
			text = array[2]
		if text is not None:
			if array[3]:
				gc_control.print_old_conversation(text)
			else:
				gc_control.print_conversation(text)

	def handle_event_gc_config(self, account, array):
		#('GC_CONFIG', account, (jid, form))  config is a dict
		room_jid = array[0].split('/')[0]
		if room_jid in gajim.automatic_rooms[account]:
			if 'continue_tag' in gajim.automatic_rooms[account][room_jid]:
				# We're converting chat to muc. allow participants to invite
				form = dataforms.ExtendForm(node = array[1])
				for f in form.iter_fields():
					if f.var == 'muc#roomconfig_allowinvites':
						f.value = True
					elif f.var == 'muc#roomconfig_publicroom':
						f.value = False
					elif f.var == 'muc#roomconfig_membersonly':
						f.value = True
					elif f.var == 'public_list':
						f.value = False
				gajim.connections[account].send_gc_config(room_jid, form)
			else:
				# use default configuration
				gajim.connections[account].send_gc_config(room_jid, array[1])
			# invite contacts
			# check if it is necessary to add <continue />
			continue_tag = False
			if 'continue_tag' in gajim.automatic_rooms[account][room_jid]:
				continue_tag = True
			if 'invities' in gajim.automatic_rooms[account][room_jid]:
				for jid in gajim.automatic_rooms[account][room_jid]['invities']:
					gajim.connections[account].send_invite(room_jid, jid,
						continue_tag=continue_tag)
			del gajim.automatic_rooms[account][room_jid]
		elif room_jid not in self.instances[account]['gc_config']:
			self.instances[account]['gc_config'][room_jid] = \
			config.GroupchatConfigWindow(account, room_jid, array[1])

	def handle_event_gc_config_change(self, account, array):
		#('GC_CONFIG_CHANGE', account, (jid, statusCode))  statuscode is a list
		# http://www.xmpp.org/extensions/xep-0045.html#roomconfig-notify
		# http://www.xmpp.org/extensions/xep-0045.html#registrar-statuscodes-init
		jid = array[0]
		statusCode = array[1]

		gc_control = self.msg_win_mgr.get_gc_control(jid, account)
		if not gc_control and \
		jid in self.minimized_controls[account]:
			gc_control = self.minimized_controls[account][jid]
		if not gc_control:
			return

		changes = []
		if '100' in statusCode:
			# Can be a presence (see chg_contact_status in groupchat_control.py)
			changes.append(_('Any occupant is allowed to see your full JID'))
			gc_control.is_anonymous = False
		if '102' in statusCode:
			changes.append(_('Room now shows unavailable member'))
		if '103' in statusCode:
			changes.append(_('room now does not show unavailable members'))
		if '104' in statusCode:
			changes.append(
				_('A non-privacy-related room configuration change has occurred'))
		if '170' in statusCode:
			# Can be a presence (see chg_contact_status in groupchat_control.py)
			changes.append(_('Room logging is now enabled'))
		if '171' in statusCode:
			changes.append(_('Room logging is now disabled'))
		if '172' in statusCode:
			changes.append(_('Room is now non-anonymous'))
			gc_control.is_anonymous = False
		if '173' in statusCode:
			changes.append(_('Room is now semi-anonymous'))
			gc_control.is_anonymous = True
		if '174' in statusCode:
			changes.append(_('Room is now fully-anonymous'))
			gc_control.is_anonymous = True

		for change in changes:
			gc_control.print_conversation(change)

	def handle_event_gc_affiliation(self, account, array):
		#('GC_AFFILIATION', account, (room_jid, users_dict))
		room_jid = array[0]
		if room_jid in self.instances[account]['gc_config']:
			self.instances[account]['gc_config'][room_jid].\
				affiliation_list_received(array[1])

	def handle_event_gc_password_required(self, account, array):
		#('GC_PASSWORD_REQUIRED', account, (room_jid, nick))
		room_jid = array[0]
		nick = array[1]

		def on_ok(text):
			gajim.connections[account].join_gc(nick, room_jid, text)
			gajim.gc_passwords[room_jid] = text

		def on_cancel():
			# get and destroy window
			if room_jid in gajim.interface.minimized_controls[account]:
				self.roster.on_disconnect(None, room_jid, account)
			else:
				win = self.msg_win_mgr.get_window(room_jid, account)
				ctrl = self.msg_win_mgr.get_gc_control(room_jid, account)
				win.remove_tab(ctrl, 3)

		dlg = dialogs.InputDialog(_('Password Required'),
			_('A Password is required to join the room %s. Please type it.') % \
			room_jid, is_modal=False, ok_handler=on_ok, cancel_handler=on_cancel)
		dlg.input_entry.set_visibility(False)

	def handle_event_gc_invitation(self, account, array):
		#('GC_INVITATION', (room_jid, jid_from, reason, password, is_continued))
		jid = gajim.get_jid_without_resource(array[1])
		room_jid = array[0]
		if helpers.allow_popup_window(account) or not self.systray_enabled:
			dialogs.InvitationReceivedDialog(account, room_jid, jid, array[3],
				array[2], is_continued=array[4])
			return

		self.add_event(account, jid, 'gc-invitation', (room_jid, array[2],
			array[3], array[4]))

		if helpers.allow_showing_notification(account):
			path = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events',
				'gc_invitation.png')
			path = gtkgui_helpers.get_path_to_generic_or_avatar(path)
			event_type = _('Groupchat Invitation')
			notify.popup(event_type, jid, account, 'gc-invitation', path,
				event_type, room_jid)

	def forget_gpg_passphrase(self, keyid):
		if keyid in self.gpg_passphrase:
			del self.gpg_passphrase[keyid]
		return False

	def handle_event_bad_passphrase(self, account, array):
		#('BAD_PASSPHRASE', account, ())
		use_gpg_agent = gajim.config.get('use_gpg_agent')
		sectext = ''
		if use_gpg_agent:
			sectext = _('You configured Gajim to use GPG agent, but there is no '
			'GPG agent running or it returned a wrong passphrase.\n')
		sectext += _('You are currently connected without your OpenPGP key.')
		keyID = gajim.config.get_per('accounts', account, 'keyid')
		self.forget_gpg_passphrase(keyID)
		dialogs.WarningDialog(_('Your passphrase is incorrect'), sectext)

	def handle_event_gpg_password_required(self, account, array):
		#('GPG_PASSWORD_REQUIRED', account, (callback,))
		callback = array[0]
		keyid = gajim.config.get_per('accounts', account, 'keyid')
		if keyid in self.gpg_passphrase:
			request = self.gpg_passphrase[keyid]
		else:
			request = PassphraseRequest(keyid)
			self.gpg_passphrase[keyid] = request
		request.add_callback(account, callback)

	def handle_event_roster_info(self, account, array):
		#('ROSTER_INFO', account, (jid, name, sub, ask, groups))
		jid = array[0]
		name = array[1]
		sub = array[2]
		ask = array[3]
		groups = array[4]
		contacts = gajim.contacts.get_contacts(account, jid)
		if (not sub or sub == 'none') and (not ask or ask == 'none') and \
		not name and not groups:
			# contact removes us.
			if contacts:
				self.roster.remove_contact(jid, account, backend=True)
				return
		elif not contacts:
			if sub == 'remove':
				return
			# Add new contact to roster
			contact = gajim.contacts.create_contact(jid=jid, name=name,
				groups=groups, show='offline', sub=sub, ask=ask)
			gajim.contacts.add_contact(account, contact)
			self.roster.add_contact(jid, account)
		else:
			# it is an existing contact that might has changed
			re_draw = False
			# if sub or groups changed: remove and re-add
			# Maybe observer status changed:
			# according to xep 0162, contact is not an observer anymore when 
			# we asked him is auth, so also remove him if ask changed
			old_groups = contacts[0].get_shown_groups()
			if contacts[0].sub != sub or contacts[0].ask != ask\
			or old_groups != groups:
				re_draw = True
			for contact in contacts:
				if not name:
					name = ''
				contact.name = name
				contact.sub = sub
				contact.ask = ask
				contact.groups = groups or []
			if re_draw:
				# Refilter and update old groups
				for group in old_groups:
					self.roster.draw_group(group, account)

		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('RosterInfo', (account, array))

	def handle_event_bookmarks(self, account, bms):
		# ('BOOKMARKS', account, [{name,jid,autojoin,password,nick}, {}])
		# We received a bookmark item from the server (JEP48)
		# Auto join GC windows if neccessary

		self.roster.set_actions_menu_needs_rebuild()
		invisible_show = gajim.SHOW_LIST.index('invisible')
		# do not autojoin if we are invisible
		if gajim.connections[account].connected == invisible_show:
			return

		self.auto_join_bookmarks(account)

	def handle_event_file_send_error(self, account, array):
		jid = array[0]
		file_props = array[1]
		ft = self.instances['file_transfers']
		ft.set_status(file_props['type'], file_props['sid'], 'stop')

		if helpers.allow_popup_window(account):
			ft.show_send_error(file_props)
			return

		self.add_event(account, jid, 'file-send-error', file_props)

		if helpers.allow_showing_notification(account):
			img = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events', 'ft_error.png')
			path = gtkgui_helpers.get_path_to_generic_or_avatar(img)
			event_type = _('File Transfer Error')
			notify.popup(event_type, jid, account, 'file-send-error', path,
				event_type, file_props['name'])

	def handle_event_gmail_notify(self, account, array):
		jid = array[0]
		gmail_new_messages = int(array[1])
		gmail_messages_list = array[2]
		if gajim.config.get('notify_on_new_gmail_email'):
			img = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events',
				'new_email_recv.png')
			title = _('New mail on %(gmail_mail_address)s') % \
				{'gmail_mail_address': jid}
			text = i18n.ngettext('You have %d new mail conversation',
				'You have %d new mail conversations', gmail_new_messages,
				gmail_new_messages, gmail_new_messages)

			if gajim.config.get('notify_on_new_gmail_email_extra'):
				cnt = 0
				for gmessage in gmail_messages_list:
					#FIXME: emulate Gtalk client popups. find out what they parse and
					# how they decide what to show each message has a 'From',
					# 'Subject' and 'Snippet' field
					if cnt >=5:
						break
					senders = ',\n     '.join(reversed(gmessage['From']))
					text += _('\n\nFrom: %(from_address)s\nSubject: %(subject)s\n%(snippet)s') % \
						{'from_address': senders, 'subject': gmessage['Subject'],
						'snippet': gmessage['Snippet']} 
					cnt += 1 

			if gajim.config.get_per('soundevents', 'gmail_received', 'enabled'):
				helpers.play_sound('gmail_received')
			path = gtkgui_helpers.get_path_to_generic_or_avatar(img)
			notify.popup(_('New E-mail'), jid, account, 'gmail',
				path_to_image=path, title=title,
				text=gobject.markup_escape_text(text))

		if self.remote_ctrl:
			self.remote_ctrl.raise_signal('NewGmail', (account, array))

	def handle_event_file_request_error(self, account, array):
		# ('FILE_REQUEST_ERROR', account, (jid, file_props, error_msg))
		jid, file_props, errmsg = array
		ft = self.instances['file_transfers']
		ft.set_status(file_props['type'], file_props['sid'], 'stop')
		errno = file_props['error']

		if helpers.allow_popup_window(account):
			if errno in (-4, -5):
				ft.show_stopped(jid, file_props, errmsg)
			else:
				ft.show_request_error(file_props)
			return

		if errno in (-4, -5):
			msg_type = 'file-error'
		else:
			msg_type = 'file-request-error'

		self.add_event(account, jid, msg_type, file_props)

		if helpers.allow_showing_notification(account):
			# check if we should be notified
			img = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events', 'ft_error.png')

			path = gtkgui_helpers.get_path_to_generic_or_avatar(img)
			event_type = _('File Transfer Error')
			notify.popup(event_type, jid, account, msg_type, path,
				title = event_type, text = file_props['name'])

	def handle_event_file_request(self, account, array):
		jid = array[0]
		if jid not in gajim.contacts.get_jid_list(account):
			keyID = ''
			attached_keys = gajim.config.get_per('accounts', account,
				'attached_gpg_keys').split()
			if jid in attached_keys:
				keyID = attached_keys[attached_keys.index(jid) + 1]
			contact = gajim.contacts.create_contact(jid=jid, name='',
				groups=[_('Not in Roster')], show='not in roster', status='',
				sub='none', keyID=keyID)
			gajim.contacts.add_contact(account, contact)
			self.roster.add_contact(contact.jid, account)
		file_props = array[1]
		contact = gajim.contacts.get_first_contact_from_jid(account, jid)

		if helpers.allow_popup_window(account):
			self.instances['file_transfers'].show_file_request(account, contact,
				file_props)
			return

		self.add_event(account, jid, 'file-request', file_props)

		if helpers.allow_showing_notification(account):
			img = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events',
				'ft_request.png')
			txt = _('%s wants to send you a file.') % gajim.get_name_from_jid(
				account, jid)
			path = gtkgui_helpers.get_path_to_generic_or_avatar(img)
			event_type = _('File Transfer Request')
			notify.popup(event_type, jid, account, 'file-request',
				path_to_image = path, title = event_type, text = txt)

	def handle_event_file_error(self, title, message):
		dialogs.ErrorDialog(title, message)

	def handle_event_file_progress(self, account, file_props):
		if time.time() - self.last_ftwindow_update > 0.5:
			# update ft window every 500ms
			self.last_ftwindow_update = time.time()
			self.instances['file_transfers'].set_progress(file_props['type'],
				file_props['sid'], file_props['received-len'])

	def handle_event_file_rcv_completed(self, account, file_props):
		ft = self.instances['file_transfers']
		if file_props['error'] == 0:
			ft.set_progress(file_props['type'], file_props['sid'],
				file_props['received-len'])
		else:
			ft.set_status(file_props['type'], file_props['sid'], 'stop')
		if 'stalled' in file_props and file_props['stalled'] or \
			'paused' in file_props and file_props['paused']:
			return
		if file_props['type'] == 'r': # we receive a file
			jid = unicode(file_props['sender'])
		else: # we send a file
			jid = unicode(file_props['receiver'])

		if helpers.allow_popup_window(account):
			if file_props['error'] == 0:
				if gajim.config.get('notify_on_file_complete'):
					ft.show_completed(jid, file_props)
			elif file_props['error'] == -1:
				ft.show_stopped(jid, file_props)
			return

		msg_type = ''
		event_type = ''
		if file_props['error'] == 0 and gajim.config.get(
		'notify_on_file_complete'):
			msg_type = 'file-completed'
			event_type = _('File Transfer Completed')
		elif file_props['error'] == -1:
			msg_type = 'file-stopped'
			event_type = _('File Transfer Stopped')

		if event_type == '':
			# FIXME: ugly workaround (this can happen Gajim sent, Gaim recvs)
			# this should never happen but it does. see process_result() in socks5.py
			# who calls this func (sth is really wrong unless this func is also registered
			# as progress_cb
			return

		if msg_type:
			self.add_event(account, jid, msg_type, file_props)

		if file_props is not None:
			if file_props['type'] == 'r':
				# get the name of the sender, as it is in the roster
				sender = unicode(file_props['sender']).split('/')[0]
				name = gajim.contacts.get_first_contact_from_jid(account,
					sender).get_shown_name()
				filename = os.path.basename(file_props['file-name'])
				if event_type == _('File Transfer Completed'):
					txt = _('You successfully received %(filename)s from %(name)s.')\
						% {'filename': filename, 'name': name}
					img = 'ft_done.png'
				else: # ft stopped
					txt = _('File transfer of %(filename)s from %(name)s stopped.')\
						% {'filename': filename, 'name': name}
					img = 'ft_stopped.png'
			else:
				receiver = file_props['receiver']
				if hasattr(receiver, 'jid'):
					receiver = receiver.jid
				receiver = receiver.split('/')[0]
				# get the name of the contact, as it is in the roster
				name = gajim.contacts.get_first_contact_from_jid(account,
					receiver).get_shown_name()
				filename = os.path.basename(file_props['file-name'])
				if event_type == _('File Transfer Completed'):
					txt = _('You successfully sent %(filename)s to %(name)s.')\
						% {'filename': filename, 'name': name}
					img = 'ft_done.png'
				else: # ft stopped
					txt = _('File transfer of %(filename)s to %(name)s stopped.')\
						% {'filename': filename, 'name': name}
					img = 'ft_stopped.png'
			img = os.path.join(gajim.DATA_DIR, 'pixmaps', 'events', img)
			path = gtkgui_helpers.get_path_to_generic_or_avatar(img)
		else:
			txt = ''

		if gajim.config.get('notify_on_file_complete') and \
			(gajim.config.get('autopopupaway') or \
			gajim.connections[account].connected in (2, 3)):
			# we want to be notified and we are online/chat or we don't mind
			# bugged when away/na/busy
			notify.popup(event_type, jid, account, msg_type, path_to_image = path,
				title = event_type, text = txt)

	def handle_event_stanza_arrived(self, account, stanza):
		if account not in self.instances:
			return
		if 'xml_console' in self.instances[account]:
			self.instances[account]['xml_console'].print_stanza(stanza, 'incoming')

	def handle_event_stanza_sent(self, account, stanza):
		if account not in self.instances:
			return
		if 'xml_console' in self.instances[account]:
			self.instances[account]['xml_console'].print_stanza(stanza, 'outgoing')

	def handle_event_vcard_published(self, account, array):
		if 'profile' in self.instances[account]:
			win = self.instances[account]['profile']
			win.vcard_published()
		for gc_control in self.msg_win_mgr.get_controls(message_control.TYPE_GC) + \
		self.minimized_controls[account].values():
			if gc_control.account == account:
				show = gajim.SHOW_LIST[gajim.connections[account].connected]
				status = gajim.connections[account].status
				gajim.connections[account].send_gc_status(gc_control.nick,
					gc_control.room_jid, show, status)

	def handle_event_vcard_not_published(self, account, array):
		if 'profile' in self.instances[account]:
			win = self.instances[account]['profile']
			win.vcard_not_published()

	def handle_event_signed_in(self, account, empty):
		'''SIGNED_IN event is emitted when we sign in, so handle it'''
		# block signed in notifications for 30 seconds
		gajim.block_signed_in_notifications[account] = True
		self.roster.set_actions_menu_needs_rebuild()
		self.roster.draw_account(account)
		if self.sleeper.getState() != common.sleepy.STATE_UNKNOWN and \
		gajim.connections[account].connected in (2, 3):
			# we go online or free for chat, so we activate auto status
			gajim.sleeper_state[account] = 'online'
		else:
			gajim.sleeper_state[account] = 'off'
		invisible_show = gajim.SHOW_LIST.index('invisible')
		# We cannot join rooms if we are invisible
		if gajim.connections[account].connected == invisible_show:
			return
		# join already open groupchats
		for gc_control in self.msg_win_mgr.get_controls(message_control.TYPE_GC) + \
		self.minimized_controls[account].values():
			if account != gc_control.account:
				continue
			room_jid = gc_control.room_jid
			if room_jid in gajim.gc_connected[account] and\
					gajim.gc_connected[account][room_jid]:
				continue
			nick = gc_control.nick
			password = gajim.gc_passwords.get(room_jid, '')
			gajim.connections[account].join_gc(nick, room_jid, password)

	def handle_event_metacontacts(self, account, tags_list):
		gajim.contacts.define_metacontacts(account, tags_list)

	def handle_atom_entry(self, account, data):
		atom_entry, = data
		AtomWindow.newAtomEntry(atom_entry)

	def handle_event_failed_decrypt(self, account, data):
		jid, tim, session = data

		details = _('Unable to decrypt message from '
			'%s\nIt may have been tampered with.') % jid

		if session.control:
			session.control.print_conversation_line(details,
				'status', '', tim)
		else:
			dialogs.WarningDialog(_('Unable to decrypt message'),
				details)

		# terminate the session
		session.terminate_e2e()
		session.conn.delete_session(jid, session.thread_id)

		# restart the session
		session.negotiate_e2e(False)

	def handle_event_privacy_lists_received(self, account, data):
		# ('PRIVACY_LISTS_RECEIVED', account, list)
		if account not in self.instances:
			return
		if 'privacy_lists' in self.instances[account]:
			self.instances[account]['privacy_lists'].privacy_lists_received(data)

	def handle_event_privacy_list_received(self, account, data):
		# ('PRIVACY_LISTS_RECEIVED', account, (name, rules))
		if account not in self.instances:
			return
		name = data[0]
		rules = data[1]
		if 'privacy_list_%s' % name in self.instances[account]:
			self.instances[account]['privacy_list_%s' % name].\
				privacy_list_received(rules)
		if name == 'block':
			gajim.connections[account].blocked_contacts = []
			gajim.connections[account].blocked_groups = []
			gajim.connections[account].blocked_list = []
			for rule in rules:
				if rule['type'] == 'jid' and rule['action'] == 'deny':
					gajim.connections[account].blocked_contacts.append(rule['value'])
				if rule['type'] == 'group' and rule['action'] == 'deny':
					gajim.connections[account].blocked_groups.append(rule['value'])
				gajim.connections[account].blocked_list.append(rule)
				#elif rule['type'] == "group" and action == "deny":
				#	text_item = _('%s group "%s"') % _(rule['action']), rule['value']
				#	self.store.append([text_item])
				#	self.global_rules.append(rule)
				#else:
				#	self.global_rules_to_append.append(rule)
			if 'blocked_contacts' in self.instances[account]:
				self.instances[account]['blocked_contacts'].\
					privacy_list_received(rules)

	def handle_event_privacy_lists_active_default(self, account, data):
		if not data:
			return
		# Send to all privacy_list_* windows as we can't know which one asked
		for win in self.instances[account]:
			if win.startswith('privacy_list_'):
				self.instances[account][win].check_active_default(data)

	def handle_event_privacy_list_removed(self, account, name):
		# ('PRIVACY_LISTS_REMOVED', account, name)
		if account not in self.instances:
			return
		if 'privacy_lists' in self.instances[account]:
			self.instances[account]['privacy_lists'].privacy_list_removed(name)

	def handle_event_zc_name_conflict(self, account, data):
		def on_ok(new_name):
			gajim.config.set_per('accounts', account, 'name', new_name)
			status = gajim.connections[account].status
			gajim.connections[account].username = new_name
			gajim.connections[account].change_status(status, '')
		def on_cancel():
			gajim.connections[account].change_status('offline','')

		dlg = dialogs.InputDialog(_('Username Conflict'),
			_('Please type a new username for your local account'), input_str=data,
			is_modal=True, ok_handler=on_ok, cancel_handler=on_cancel)

	def handle_event_ping_sent(self, account, contact):
		if contact.jid == contact.get_full_jid():
			# If contact is a groupchat user
			jids = [contact.jid]
		else:
			jids = [contact.jid, contact.get_full_jid()]		
		for jid in jids:
			ctrl = self.msg_win_mgr.get_control(jid, account)
			if ctrl:
				ctrl.print_conversation(_('Ping?'), 'status')

	def handle_event_ping_reply(self, account, data):
		contact = data[0]
		seconds = data[1]
		if contact.jid == contact.get_full_jid():
			# If contact is a groupchat user
			jids = [contact.jid]
		else:
			jids = [contact.jid, contact.get_full_jid()]
		for jid in jids:
			ctrl = self.msg_win_mgr.get_control(jid, account)
			if ctrl:
				ctrl.print_conversation(_('Pong! (%s s.)') % seconds, 'status')

	def handle_event_ping_error(self, account, contact):
		if contact.jid == contact.get_full_jid():
			# If contact is a groupchat user
			jids = [contact.jid]
		else:
			jids = [contact.jid, contact.get_full_jid()]
		for jid in jids:
			ctrl = self.msg_win_mgr.get_control(jid, account)
			if ctrl:
				ctrl.print_conversation(_('Error.'), 'status')

	def handle_event_search_form(self, account, data):
		# ('SEARCH_FORM', account, (jid, dataform, is_dataform))
		if data[0] not in self.instances[account]['search']:
			return
		self.instances[account]['search'][data[0]].on_form_arrived(data[1],
			data[2])

	def handle_event_search_result(self, account, data):
		# ('SEARCH_RESULT', account, (jid, dataform, is_dataform))
		if data[0] not in self.instances[account]['search']:
			return
		self.instances[account]['search'][data[0]].on_result_arrived(data[1],
			data[2])

	def handle_event_resource_conflict(self, account, data):
		# ('RESOURCE_CONFLICT', account, ())
		# First we go offline, but we don't overwrite status message
		self.roster.send_status(account, 'offline',
			gajim.connections[account].status)
		def on_ok(new_resource):
			gajim.config.set_per('accounts', account, 'resource', new_resource)
			self.roster.send_status(account, gajim.connections[account].old_show,
				gajim.connections[account].status)
		dlg = dialogs.InputDialog(_('Resource Conflict'),
			_('You are already connected to this account with the same resource. Please type a new one'), input_str = gajim.connections[account].server_resource,
			is_modal = False, ok_handler = on_ok)

	def handle_event_pep_config(self, account, data):
		# ('PEP_CONFIG', account, (node, form))
		if 'pep_services' in self.instances[account]:
			self.instances[account]['pep_services'].config(data[0], data[1])

	def handle_event_unique_room_id_supported(self, account, data):
		'''Receive confirmation that unique_room_id are supported'''
		# ('UNIQUE_ROOM_ID_SUPPORTED', server, instance, room_id)
		instance = data[1]
		instance.unique_room_id_supported(data[0], data[2])

	def handle_event_unique_room_id_unsupported(self, account, data):
		# ('UNIQUE_ROOM_ID_UNSUPPORTED', server, instance)
		instance = data[1]
		instance.unique_room_id_error(data[0])

	def handle_event_ssl_error(self, account, data):
		# ('SSL_ERROR', account, (text, errnum, cert, sha1_fingerprint))
		server = gajim.config.get_per('accounts', account, 'hostname')

		def on_ok(is_checked):
			if is_checked[0]:
				# Check if cert is already in file
				certs = ''
				if os.path.isfile(gajim.MY_CACERTS):
					f = open(gajim.MY_CACERTS)
					certs = f.read()
					f.close()
				if data[2] in certs:
					dialogs.ErrorDialog(_('Certificate Already in File'),
						_('This certificate is already in file %s, so it\'s not added again.') % gajim.MY_CACERTS)
				else:
					f = open(gajim.MY_CACERTS, 'a')
					f.write(server + '\n')
					f.write(data[2] + '\n\n')
					f.close()
				gajim.config.set_per('accounts', account, 'ssl_fingerprint_sha1',
					data[3])
			if is_checked[1]:
				ignore_ssl_errors = gajim.config.get_per('accounts', account,
					'ignore_ssl_errors').split()
				ignore_ssl_errors.append(str(data[1]))
				gajim.config.set_per('accounts', account, 'ignore_ssl_errors',
					' '.join(ignore_ssl_errors))
			gajim.connections[account].ssl_certificate_accepted()

		def on_cancel():
			gajim.connections[account].disconnect(on_purpose=True)
			self.handle_event_status(account, 'offline')

		pritext = _('Error verifying SSL certificate')
		sectext = _('There was an error verifying the SSL certificate of your jabber server: %(error)s\nDo you still want to connect to this server?') % {'error': data[0]}
		if data[1] in (18, 27):
			checktext1 = _('Add this certificate to the list of trusted certificates.\nSHA1 fingerprint of the certificate:\n%s') % data[3]
		else:
			checktext1 = ''
		checktext2 = _('Ignore this error for this certificate.')
		dialogs.ConfirmationDialogDubbleCheck(pritext, sectext, checktext1,
			checktext2, on_response_ok=on_ok, on_response_cancel=on_cancel)

	def handle_event_fingerprint_error(self, account, data):
		# ('FINGERPRINT_ERROR', account, (new_fingerprint,))
		def on_yes(is_checked):
			gajim.config.set_per('accounts', account, 'ssl_fingerprint_sha1',
				data[0])
			# Reset the ignored ssl errors
			gajim.config.set_per('accounts', account, 'ignore_ssl_errors', '')
			gajim.connections[account].ssl_certificate_accepted()
		def on_no():
			gajim.connections[account].disconnect(on_purpose=True)
			self.handle_event_status(account, 'offline')
		pritext = _('SSL certificate error')
		sectext = _('It seems the SSL certificate has changed or your connection '
			'is being hacked.\nOld fingerprint: %(old)s\nNew fingerprint: %(new)s'
			'\n\nDo you still want to connect and update the fingerprint of the '
			'certificate?') % {'old': gajim.config.get_per('accounts', account,
			'ssl_fingerprint_sha1'), 'new': data[0]}
		dialog = dialogs.YesNoDialog(pritext, sectext, on_response_yes=on_yes,
			on_response_no=on_no)

	def handle_event_plain_connection(self, account, data):
		# ('PLAIN_CONNECTION', account, (connection))
		server = gajim.config.get_per('accounts', account, 'hostname')
		def on_ok(is_checked):
			if not is_checked[0]:
				on_cancel()
				return
			if is_checked[1]:
				gajim.config.set_per('accounts', account,
					'warn_when_plaintext_connection', False)
			gajim.connections[account].connection_accepted(data[0], 'tcp')
		def on_cancel():
			gajim.connections[account].disconnect(on_purpose=True)
			self.handle_event_status(account, 'offline')
		pritext = _('Insecure connection')
		sectext = _('You are about to send your password on an unencrypted '
			'connection. Are you sure you want to do that?')
		checktext1 = _('Yes, I really want to connect insecurely')
		checktext2 = _('Do _not ask me again')
		dialog = dialogs.ConfirmationDialogDubbleCheck(pritext, sectext,
			checktext1, checktext2, on_response_ok=on_ok,
			on_response_cancel=on_cancel, is_modal=False)

	def handle_event_insecure_ssl_connection(self, account, data):
		# ('INSECURE_SSL_CONNECTION', account, (connection, connection_type))
		server = gajim.config.get_per('accounts', account, 'hostname')
		def on_ok(is_checked):
			if not is_checked[0]:
				on_cancel()
				return
			if is_checked[1]:
				gajim.config.set_per('accounts', account,
					'warn_when_insecure_ssl_connection', False)
			if gajim.connections[account].connected == 0:
				# We have been disconnecting (too long time since window is opened)
				# re-connect with auto-accept
				gajim.connections[account].connection_auto_accepted = True
				show, msg = gajim.connections[account].continue_connect_info[:2]
				self.roster.send_status(account, show, msg)
				return
			gajim.connections[account].connection_accepted(data[0], data[1])
		def on_cancel():
			gajim.connections[account].disconnect(on_purpose=True)
			self.handle_event_status(account, 'offline')
		pritext = _('Insecure connection')
		sectext = _('You are about to send your password on an insecure '
			'connection. You should install PyOpenSSL to prevent that. Are you sure you want to do that?')
		checktext1 = _('Yes, I really want to connect insecurely')
		checktext2 = _('Do _not ask me again')
		dialog = dialogs.ConfirmationDialogDubbleCheck(pritext, sectext,
			checktext1, checktext2, on_response_ok=on_ok,
			on_response_cancel=on_cancel, is_modal=False)

	def handle_event_pubsub_node_removed(self, account, data):
		# ('PUBSUB_NODE_REMOVED', account, (jid, node))
		if 'pep_services' in self.instances[account]:
			if data[0] == gajim.get_jid_from_account(account):
				self.instances[account]['pep_services'].node_removed(data[1])

	def handle_event_pubsub_node_not_removed(self, account, data):
		# ('PUBSUB_NODE_NOT_REMOVED', account, (jid, node, msg))
		if data[0] == gajim.get_jid_from_account(account):
			dialogs.WarningDialog(_('PEP node was not removed'),
				_('PEP node %(node)s was not removed: %(message)s') % {
				'node': data[1], 'message': data[2]})

	def register_handlers(self):
		self.handlers = {
			'ROSTER': self.handle_event_roster,
			'WARNING': self.handle_event_warning,
			'ERROR': self.handle_event_error,
			'INFORMATION': self.handle_event_information,
			'ERROR_ANSWER': self.handle_event_error_answer,
			'STATUS': self.handle_event_status,
			'NOTIFY': self.handle_event_notify,
			'MSGERROR': self.handle_event_msgerror,
			'MSGSENT': self.handle_event_msgsent,
			'MSGNOTSENT': self.handle_event_msgnotsent,
			'SUBSCRIBED': self.handle_event_subscribed,
			'UNSUBSCRIBED': self.handle_event_unsubscribed,
			'SUBSCRIBE': self.handle_event_subscribe,
			'AGENT_ERROR_INFO': self.handle_event_agent_info_error,
			'AGENT_ERROR_ITEMS': self.handle_event_agent_items_error,
			'AGENT_REMOVED': self.handle_event_agent_removed,
			'REGISTER_AGENT_INFO': self.handle_event_register_agent_info,
			'AGENT_INFO_ITEMS': self.handle_event_agent_info_items,
			'AGENT_INFO_INFO': self.handle_event_agent_info_info,
			'QUIT': self.handle_event_quit,
			'NEW_ACC_CONNECTED': self.handle_event_new_acc_connected,
			'NEW_ACC_NOT_CONNECTED': self.handle_event_new_acc_not_connected,
			'ACC_OK': self.handle_event_acc_ok,
			'ACC_NOT_OK': self.handle_event_acc_not_ok,
			'MYVCARD': self.handle_event_myvcard,
			'VCARD': self.handle_event_vcard,
			'LAST_STATUS_TIME': self.handle_event_last_status_time,
			'OS_INFO': self.handle_event_os_info,
			'GC_NOTIFY': self.handle_event_gc_notify,
			'GC_MSG': self.handle_event_gc_msg,
			'GC_SUBJECT': self.handle_event_gc_subject,
			'GC_CONFIG': self.handle_event_gc_config,
			'GC_CONFIG_CHANGE': self.handle_event_gc_config_change,
			'GC_INVITATION': self.handle_event_gc_invitation,
			'GC_AFFILIATION': self.handle_event_gc_affiliation,
			'GC_PASSWORD_REQUIRED': self.handle_event_gc_password_required,
			'BAD_PASSPHRASE': self.handle_event_bad_passphrase,
			'ROSTER_INFO': self.handle_event_roster_info,
			'BOOKMARKS': self.handle_event_bookmarks,
			'CON_TYPE': self.handle_event_con_type,
			'CONNECTION_LOST': self.handle_event_connection_lost,
			'FILE_REQUEST': self.handle_event_file_request,
			'GMAIL_NOTIFY': self.handle_event_gmail_notify,
			'FILE_REQUEST_ERROR': self.handle_event_file_request_error,
			'FILE_SEND_ERROR': self.handle_event_file_send_error,
			'STANZA_ARRIVED': self.handle_event_stanza_arrived,
			'STANZA_SENT': self.handle_event_stanza_sent,
			'HTTP_AUTH': self.handle_event_http_auth,
			'VCARD_PUBLISHED': self.handle_event_vcard_published,
			'VCARD_NOT_PUBLISHED': self.handle_event_vcard_not_published,
			'ASK_NEW_NICK': self.handle_event_ask_new_nick,
			'SIGNED_IN': self.handle_event_signed_in,
			'METACONTACTS': self.handle_event_metacontacts,
			'ATOM_ENTRY': self.handle_atom_entry,
			'FAILED_DECRYPT': self.handle_event_failed_decrypt,
			'PRIVACY_LISTS_RECEIVED': self.handle_event_privacy_lists_received,
			'PRIVACY_LIST_RECEIVED': self.handle_event_privacy_list_received,
			'PRIVACY_LISTS_ACTIVE_DEFAULT': \
				self.handle_event_privacy_lists_active_default,
			'PRIVACY_LIST_REMOVED': self.handle_event_privacy_list_removed,
			'ZC_NAME_CONFLICT': self.handle_event_zc_name_conflict,
			'PING_SENT': self.handle_event_ping_sent,
			'PING_REPLY': self.handle_event_ping_reply,
			'PING_ERROR': self.handle_event_ping_error,
			'SEARCH_FORM': self.handle_event_search_form,
			'SEARCH_RESULT': self.handle_event_search_result,
			'RESOURCE_CONFLICT': self.handle_event_resource_conflict,
			'PEP_CONFIG': self.handle_event_pep_config,
			'UNIQUE_ROOM_ID_UNSUPPORTED': \
				self.handle_event_unique_room_id_unsupported,
			'UNIQUE_ROOM_ID_SUPPORTED': self.handle_event_unique_room_id_supported,
			'GPG_PASSWORD_REQUIRED': self.handle_event_gpg_password_required,
			'SSL_ERROR': self.handle_event_ssl_error,
			'FINGERPRINT_ERROR': self.handle_event_fingerprint_error,
			'PLAIN_CONNECTION': self.handle_event_plain_connection,
			'INSECURE_SSL_CONNECTION': self.handle_event_insecure_ssl_connection,
			'PUBSUB_NODE_REMOVED': self.handle_event_pubsub_node_removed,
			'PUBSUB_NODE_NOT_REMOVED': self.handle_event_pubsub_node_not_removed,
		}
		gajim.handlers = self.handlers

################################################################################		
### Methods dealing with gajim.events
################################################################################

	def add_event(self, account, jid, type_, event_args):
		'''add an event to the gajim.events var'''
		# We add it to the gajim.events queue
		# Do we have a queue?
		jid = gajim.get_jid_without_resource(jid)
		no_queue = len(gajim.events.get_events(account, jid)) == 0
		# type_ can be gc-invitation file-send-error file-error file-request-error
		# file-request file-completed file-stopped
		# event_type can be in advancedNotificationWindow.events_list
		event_types = {'file-request': 'ft_request',
			'file-completed': 'ft_finished'}
		event_type = event_types.get(type_)
		show_in_roster = notify.get_show_in_roster(event_type, account, jid)
		show_in_systray = notify.get_show_in_systray(event_type, account, jid)
		event = gajim.events.create_event(type_, event_args,
			show_in_roster = show_in_roster,
			show_in_systray = show_in_systray)
		gajim.events.add_event(account, jid, event)

		self.roster.show_title()
		if no_queue: # We didn't have a queue: we change icons
			if not gajim.contacts.get_contact_with_highest_priority(account, jid):
				if type_ == 'gc-invitation':
					self.roster.add_groupchat(jid, account, status='offline')
				else:
					# add contact to roster ("Not In The Roster") if he is not
					self.roster.add_to_not_in_the_roster(account, jid)
			else:
				self.roster.draw_contact(jid, account)

		# Select the contact in roster, it's visible because it has events.
		self.roster.select_contact(jid, account)

	def handle_event(self, account, fjid, type_):
		w = None
		ctrl = None
		session = None

		resource = gajim.get_resource_from_jid(fjid)
		jid = gajim.get_jid_without_resource(fjid)

		if type_ in ('printed_gc_msg', 'printed_marked_gc_msg', 'gc_msg'):
			w = self.msg_win_mgr.get_window(jid, account)
			if jid in self.minimized_controls[account]:
				self.roster.on_groupchat_maximized(None, jid, account)
				return
			else:
				ctrl = self.msg_win_mgr.get_gc_control(jid, account)

		elif type_ in ('printed_chat', 'chat', ''):
			# '' is for log in/out notifications

			if type_ != '':
				event = gajim.events.get_first_event(account, fjid, type_)
				if not event:
					event = gajim.events.get_first_event(account, jid, type_)
				if not event:
					return

			if type_ == 'printed_chat':
				ctrl = event.parameters[0]
			elif type_ == 'chat':
				session = event.parameters[8]
				ctrl = session.control
			elif type_ == '':
				ctrl = self.msg_win_mgr.get_control(fjid, account)

			if not ctrl:
				highest_contact = gajim.contacts.get_contact_with_highest_priority(
					account, jid)
				# jid can have a window if this resource was lower when he sent
				# message and is now higher because the other one is offline
				if resource and highest_contact.resource == resource and \
				not self.msg_win_mgr.has_window(jid, account):
					# remove resource of events too
					gajim.events.change_jid(account, fjid, jid)
					resource = None
					fjid = jid
				contact = None
				if resource:
					contact = gajim.contacts.get_contact(account, jid, resource)
				if not contact:
					contact = highest_contact

				ctrl = self.new_chat(contact, account, resource = resource, session = session)

				gajim.last_message_time[account][jid] = 0 # long time ago

			w = ctrl.parent_win
		elif type_ in ('printed_pm', 'pm'):
			# assume that the most recently updated control we have for this party
			# is the one that this event was in
			event = gajim.events.get_first_event(account, fjid, type_)
			if not event:
				event = gajim.events.get_first_event(account, jid, type_)

			if type_ == 'printed_pm':
				ctrl = event.parameters[0]
			elif type_ == 'pm':
				session = event.parameters[8]

			if session and session.control:
				ctrl = session.control
			elif not ctrl:
				room_jid = jid
				nick = resource
				gc_contact = gajim.contacts.get_gc_contact(account, room_jid,
					nick)
				if gc_contact:
					show = gc_contact.show
				else:
					show = 'offline'
					gc_contact = gajim.contacts.create_gc_contact(
						room_jid = room_jid, name = nick, show = show)

				if not session:
					session = gajim.connections[account].make_new_session(
						fjid, None, type_='pm')

				self.new_private_chat(gc_contact, account, session=session)
				ctrl = session.control

			w = ctrl.parent_win
		elif type_ in ('normal', 'file-request', 'file-request-error',
		'file-send-error', 'file-error', 'file-stopped', 'file-completed'):
			# Get the first single message event
			event = gajim.events.get_first_event(account, fjid, type_)
			if not event:
				# default to jid without resource
				event = gajim.events.get_first_event(account, jid, type_)
				if not event:
					return
				# Open the window
				self.roster.open_event(account, jid, event)
			else:
				# Open the window
				self.roster.open_event(account, fjid, event)
		elif type_ == 'gmail':
			url=gajim.connections[account].gmail_url
			if url:
				helpers.launch_browser_mailer('url', url)
		elif type_ == 'gc-invitation':
			event = gajim.events.get_first_event(account, jid, type_)
			data = event.parameters
			dialogs.InvitationReceivedDialog(account, data[0], jid, data[2],
				data[1], data[3])
			gajim.events.remove_events(account, jid, event)
			self.roster.draw_contact(jid, account)
		if w:
			w.set_active_tab(ctrl)
			w.window.window.focus()
			# Using isinstance here because we want to catch all derived types
			if isinstance(ctrl, ChatControlBase):
				tv = ctrl.conv_textview
				tv.scroll_to_end()

################################################################################		
### Methods dealing with emoticons
################################################################################

	def image_is_ok(self, image):
		if not os.path.exists(image):
			return False
		img = gtk.Image()
		try:
			img.set_from_file(image)
		except Exception:
			return False
		t = img.get_storage_type()
		if t != gtk.IMAGE_PIXBUF and t != gtk.IMAGE_ANIMATION:
			return False
		return True

	def make_regexps(self):
		# regexp meta characters are:  . ^ $ * + ? { } [ ] \ | ( )
		# one escapes the metachars with \
		# \S matches anything but ' ' '\t' '\n' '\r' '\f' and '\v'
		# \s matches any whitespace character
		# \w any alphanumeric character
		# \W any non-alphanumeric character
		# \b means word boundary. This is a zero-width assertion that
		# 					matches only at the beginning or end of a word.
		# ^ matches at the beginning of lines
		#
		# * means 0 or more times
		# + means 1 or more times
		# ? means 0 or 1 time
		# | means or
		# [^*] anything but '*'	(inside [] you don't have to escape metachars)
		# [^\s*] anything but whitespaces and '*'
		# (?<!\S) is a one char lookbehind assertion and asks for any leading whitespace
		# and mathces beginning of lines so we have correct formatting detection
		# even if the the text is just '*foo*'
		# (?!\S) is the same thing but it's a lookahead assertion
		# \S*[^\s\W] --> in the matching string don't match ? or ) etc.. if at the end
		# so http://be) will match http://be and http://be)be) will match http://be)be

		legacy_prefixes = r"((?<=\()(www|ftp)\.([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+(?=\)))"\
				r"|((www|ftp)\.([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+"\
				r"\.([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+)"
		# NOTE: it's ok to catch www.gr such stuff exist!

		#FIXME: recognize xmpp: and treat it specially
		links = r"((?<=\()[A-Za-z][A-Za-z0-9\+\.\-]*:"\
			r"([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+"\
			r"(?=\)))|([A-Za-z][A-Za-z0-9\+\.\-]*:([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+)"

		#2nd one: at_least_one_char@at_least_one_char.at_least_one_char
		mail = r'\bmailto:\S*[^\s\W]|' r'\b\S+@\S+\.\S*[^\s\W]'

		#detects eg. *b* *bold* *bold bold* test *bold* *bold*! (*bold*)
		#doesn't detect (it's a feature :P) * bold* *bold * * bold * test*bold*
		formatting = r'|(?<!\w)' r'\*[^\s*]' r'([^*]*[^\s*])?' r'\*(?!\w)|'\
			r'(?<!\w|\<)' r'/[^\s/]' r'([^/]*[^\s/])?' r'/(?!\w)|'\
			r'(?<!\w)' r'_[^\s_]' r'([^_]*[^\s_])?' r'_(?!\w)'

		latex = r'|\$\$[^$\\]*?([\]\[0-9A-Za-z()|+*/-]|[\\][\]\[0-9A-Za-z()|{}$])(.*?[^\\])?\$\$'

		basic_pattern = links + '|' + mail + '|' + legacy_prefixes

		if gajim.config.get('use_latex'):
			basic_pattern += latex

		if gajim.config.get('ascii_formatting'):
			basic_pattern += formatting
		self.basic_pattern_re = re.compile(basic_pattern, re.IGNORECASE)

		emoticons_pattern = ''
		if gajim.config.get('emoticons_theme'):
			# When an emoticon is bordered by an alpha-numeric character it is NOT
			# expanded.  e.g., foo:) NO, foo :) YES, (brb) NO, (:)) YES, etc.
			# We still allow multiple emoticons side-by-side like :P:P:P
			# sort keys by length so :qwe emot is checked before :q
			keys = self.emoticons.keys()
			keys.sort(self.on_emoticon_sort)
			emoticons_pattern_prematch = ''
			emoticons_pattern_postmatch = ''
			emoticon_length = 0
			for emoticon in keys: # travel thru emoticons list
				emoticon = emoticon.decode('utf-8')
				emoticon_escaped = re.escape(emoticon) # espace regexp metachars
				emoticons_pattern += emoticon_escaped + '|'# | means or in regexp
				if (emoticon_length != len(emoticon)):
					# Build up expressions to match emoticons next to other emoticons
					emoticons_pattern_prematch  = emoticons_pattern_prematch[:-1]  + ')|(?<='
					emoticons_pattern_postmatch = emoticons_pattern_postmatch[:-1] + ')|(?='
					emoticon_length = len(emoticon)
				emoticons_pattern_prematch += emoticon_escaped  + '|'
				emoticons_pattern_postmatch += emoticon_escaped + '|'
			# We match from our list of emoticons, but they must either have
			# whitespace, or another emoticon next to it to match successfully
			# [\w.] alphanumeric and dot (for not matching 8) in (2.8))
			emoticons_pattern = '|' + \
				'(?:(?<![\w.]' + emoticons_pattern_prematch[:-1]	+ '))' + \
				'(?:'		 + emoticons_pattern[:-1]				+ ')'  + \
				'(?:(?![\w]'  + emoticons_pattern_postmatch[:-1]  + '))'

		# because emoticons match later (in the string) they need to be after
		# basic matches that may occur earlier
		emot_and_basic_pattern = basic_pattern + emoticons_pattern
		self.emot_and_basic_re = re.compile(emot_and_basic_pattern,
			re.IGNORECASE + re.UNICODE)

		# at least one character in 3 parts (before @, after @, after .)
		self.sth_at_sth_dot_sth_re = re.compile(r'\S+@\S+\.\S*[^\s)?]')

		# Invalid XML chars
		invalid_XML_chars = u'[\x00-\x08]|[\x0b-\x0c]|[\x0e-\x19]|[\ud800-\udfff]|[\ufffe-\uffff]'
		self.invalid_XML_chars_re = re.compile(invalid_XML_chars)

		re.purge() # clear the regular expression cache

	def on_emoticon_sort(self, emot1, emot2):
		len1 = len(emot1)
		len2 = len(emot2)
		if len1 < len2:
			return 1
		elif len1 > len2:
			return -1
		return 0

	def popup_emoticons_under_button(self, button, parent_win):
		''' pops emoticons menu under button, located in parent_win'''
		gtkgui_helpers.popup_emoticons_under_button(self.emoticons_menu,
			button, parent_win)

	def prepare_emoticons_menu(self):
		menu = gtk.Menu()
		def emoticon_clicked(w, str_):
			if self.emoticon_menuitem_clicked:
				self.emoticon_menuitem_clicked(str_)
				# don't keep reference to CB of object
				# this will prevent making it uncollectable
				self.emoticon_menuitem_clicked = None
		def selection_done(widget):
			# remove reference to CB of object, which will
			# make it uncollectable
			self.emoticon_menuitem_clicked = None
		counter = 0
		# Calculate the side lenght of the popup to make it a square
		size = int(round(math.sqrt(len(self.emoticons_images))))
		for image in self.emoticons_images:
			item = gtk.MenuItem()
			img = gtk.Image()
			if isinstance(image[1], gtk.gdk.PixbufAnimation):
				img.set_from_animation(image[1])
			else:
				img.set_from_pixbuf(image[1])
			item.add(img)
			item.connect('activate', emoticon_clicked, image[0])
			#FIXME: add tooltip with ascii
			menu.attach(item, counter % size, counter % size + 1,
				counter / size, counter / size + 1)
			counter += 1
		menu.connect('selection-done', selection_done)
		menu.show_all()
		return menu

	def _init_emoticons(self, path, need_reload = False):
		#initialize emoticons dictionary and unique images list
		self.emoticons_images = list()
		self.emoticons = dict()
		self.emoticons_animations = dict()

		sys.path.append(path)
		import emoticons
		if need_reload:
			# we need to reload else that doesn't work when changing emoticon set
			reload(emoticons)
		emots = emoticons.emoticons
		for emot_filename in emots:
			emot_file = os.path.join(path, emot_filename)
			if not self.image_is_ok(emot_file):
				continue
			for emot in emots[emot_filename]:
				emot = emot.decode('utf-8')
				# This avoids duplicated emoticons with the same image eg. :) and :-)
				if not emot_file in self.emoticons.values():
					if emot_file.endswith('.gif'):
						pix = gtk.gdk.PixbufAnimation(emot_file)
					else:
						pix = gtk.gdk.pixbuf_new_from_file(emot_file)
					self.emoticons_images.append((emot, pix))
				self.emoticons[emot.upper()] = emot_file
		del emoticons
		sys.path.remove(path)

	def init_emoticons(self, need_reload = False):
		emot_theme = gajim.config.get('emoticons_theme')
		if not emot_theme:
			return

		path = os.path.join(gajim.DATA_DIR, 'emoticons', emot_theme)
		if not os.path.exists(path):
			# It's maybe a user theme
			path = os.path.join(gajim.MY_EMOTS_PATH, emot_theme)
			if not os.path.exists(path): # theme doesn't exist, disable emoticons
				dialogs.WarningDialog(_('Emoticons disabled'),
					_('Your configured emoticons theme has not been found, so emoticons have been disabled.'))
				gajim.config.set('emoticons_theme', '')
				return
		self._init_emoticons(path, need_reload)
		if len(self.emoticons) == 0:
			# maybe old format of emoticons file, try to convert it
			try:
				import pprint
				import emoticons
				emots = emoticons.emoticons
				fd = open(os.path.join(path, 'emoticons.py'), 'w')
				fd.write('emoticons = ')
				pprint.pprint( dict([(file, [i for i in emots.keys() if emots[i] ==\
					file]) for file in set(emots.values())]), fd)
				fd.close()
				del emoticons
				self._init_emoticons(path, need_reload=True)
			except Exception:
				pass
			if len(self.emoticons) == 0:
				dialogs.WarningDialog(_('Emoticons disabled'),
					_('Your configured emoticons theme cannot been loaded. You maybe need to update the format of emoticons.py file. See http://trac.gajim.org/wiki/Emoticons for more details.'))
		if self.emoticons_menu:
			self.emoticons_menu.destroy()
		self.emoticons_menu = self.prepare_emoticons_menu()

################################################################################
### Methods for opening new messages controls
################################################################################

	def join_gc_room(self, account, room_jid, nick, password, minimize=False,
	is_continued=False):
		'''joins the room immediately'''
		if not nick:
			nick = gajim.nicks[account]

		if self.msg_win_mgr.has_window(room_jid, account) and \
		gajim.gc_connected[account][room_jid]:
			gc_ctrl = self.msg_win_mgr.get_gc_control(room_jid, account)
			win = gc_ctrl.parent_win
			win.set_active_tab(gc_ctrl)
			dialogs.ErrorDialog(_('You are already in group chat %s') % room_jid)
			return

		invisible_show = gajim.SHOW_LIST.index('invisible')
		if gajim.connections[account].connected == invisible_show:
			dialogs.ErrorDialog(
				_('You cannot join a group chat while you are invisible'))
			return

		minimized_control_exists = False
		if room_jid in gajim.interface.minimized_controls[account]:
			minimized_control_exists = True

		if not minimized_control_exists and \
		not self.msg_win_mgr.has_window(room_jid, account):
			# Join new groupchat
			if minimize:
				contact = gajim.contacts.create_contact(jid=room_jid, name=nick)
				gc_control = GroupchatControl(None, contact, account)
				gajim.interface.minimized_controls[account][room_jid] = gc_control
				self.roster.add_groupchat(room_jid, account)
			else:
				self.new_room(room_jid, nick, account, is_continued=is_continued)
		elif not minimized_control_exists:
			# We are already in that groupchat
			gc_control = self.msg_win_mgr.get_gc_control(room_jid, account)
			gc_control.parent_win.set_active_tab(gc_control)	
		else:
			# We are already in this groupchat and it is minimized
			self.roster.add_groupchat(room_jid, account)

		# Connect
		gajim.connections[account].join_gc(nick, room_jid, password)
		if password:
			gajim.gc_passwords[room_jid] = password

	def new_room(self, room_jid, nick, account, is_continued=False):
		# Get target window, create a control, and associate it with the window
		contact = gajim.contacts.create_contact(jid=room_jid, name=nick)
		mw = self.msg_win_mgr.get_window(contact.jid, account)
		if not mw:
			mw = self.msg_win_mgr.create_window(contact, account,
				GroupchatControl.TYPE_ID)
		gc_control = GroupchatControl(mw, contact, account,
			is_continued=is_continued)
		mw.new_tab(gc_control)

	def new_private_chat(self, gc_contact, account, session=None):
		contact = gajim.contacts.contact_from_gc_contact(gc_contact)
		type_ = message_control.TYPE_PM
		fjid = gc_contact.room_jid + '/' + gc_contact.name

		conn = gajim.connections[account]

		if not session and fjid in conn.sessions:
			sessions = filter(lambda s: isinstance(s, ChatControlSession),
				conn.sessions[fjid].values())

			# look for an existing session with a chat control
			for s in sessions:
				if s.control:
					session = s
					break

			if not session and not len(sessions) == 0:
				# there are no sessions with chat controls, just take the first one
				session = sessions[0]

		if not session:
			# couldn't find an existing ChatControlSession, just make a new one

			session = conn.make_new_session(fjid, None, 'pm')

		if not session.control:
			mw = self.msg_win_mgr.get_window(fjid, account)
			if not mw:
				mw = self.msg_win_mgr.create_window(contact, account, type_)

			session.control = PrivateChatControl(mw, gc_contact, contact, account,
				session)
			mw.new_tab(session.control)

		if len(gajim.events.get_events(account, fjid)):
			# We call this here to avoid race conditions with widget validation
			session.control.read_queue()

		return session.control

	def new_chat(self, contact, account, resource=None, session=None):
		# Get target window, create a control, and associate it with the window
		type_ = message_control.TYPE_CHAT

		fjid = contact.jid
		if resource:
			fjid += '/' + resource

		mw = self.msg_win_mgr.get_window(fjid, account)
		if not mw:
			mw = self.msg_win_mgr.create_window(contact, account, type_, resource)

		chat_control = ChatControl(mw, contact, account, session, resource)

		mw.new_tab(chat_control)

		if len(gajim.events.get_events(account, fjid)):
			# We call this here to avoid race conditions with widget validation
			chat_control.read_queue()

		return chat_control

	def new_chat_from_jid(self, account, fjid):
		jid, resource = gajim.get_room_and_nick_from_fjid(fjid)
		contact = gajim.contacts.get_contact(account, jid, resource)
		added_to_roster = False
		if not contact:
			added_to_roster = True
			contact = self.roster.add_to_not_in_the_roster(account, jid,
				resource=resource)

		ctrl = self.msg_win_mgr.get_control(fjid, account)

		if not ctrl:
			ctrl = self.new_chat(contact, account,
				resource=resource)
			if len(gajim.events.get_events(account, fjid)):
				ctrl.read_queue()

		mw = ctrl.parent_win
		mw.set_active_tab(ctrl)
		# For JEP-0172
		if added_to_roster:
			ctrl.user_nick = gajim.nicks[account]

	def on_open_chat_window(self, widget, contact, account, resource=None,
	session=None):

		# Get the window containing the chat
		fjid = contact.jid

		if resource:
			fjid += '/' + resource

		ctrl = None

		if session:
			ctrl = session.control
		if not ctrl:
			win = self.msg_win_mgr.get_window(fjid, account)

			if win:
				ctrl = win.get_control(fjid, account)

		if not ctrl:
			ctrl = self.new_chat(contact, account, resource=resource,
				session=session)
			# last message is long time ago
			gajim.last_message_time[account][ctrl.get_full_jid()] = 0

		win = ctrl.parent_win

		win.set_active_tab(ctrl)

		if gajim.connections[account].is_zeroconf and \
		gajim.connections[account].status in ('offline', 'invisible'):
			ctrl = win.get_control(fjid, account)
			if ctrl:
				ctrl.got_disconnected()

################################################################################		
### Other Methods
################################################################################	

	def read_sleepy(self):
		'''Check idle status and change that status if needed'''
		if not self.sleeper.poll():
			# idle detection is not supported in that OS
			return False # stop looping in vain
		state = self.sleeper.getState()
		for account in gajim.connections:
			if account not in gajim.sleeper_state or \
					not gajim.sleeper_state[account]:
				continue
			if state == common.sleepy.STATE_AWAKE and \
				gajim.sleeper_state[account] in ('autoaway', 'autoxa'):
				# we go online
				self.roster.send_status(account, 'online',
					gajim.status_before_autoaway[account])
				gajim.status_before_autoaway[account] = ''
				gajim.sleeper_state[account] = 'online'
			elif state == common.sleepy.STATE_AWAY and \
				gajim.sleeper_state[account] == 'online' and \
				gajim.config.get('autoaway'):
				# we save out online status
				gajim.status_before_autoaway[account] = \
					gajim.connections[account].status
				# we go away (no auto status) [we pass True to auto param]
				auto_message = gajim.config.get('autoaway_message')
				if not auto_message:
					auto_message = gajim.connections[account].status
				else:
					auto_message = auto_message.replace('$S','%(status)s')
					auto_message = auto_message.replace('$T','%(time)s')
					auto_message = auto_message % {
						'status': gajim.status_before_autoaway[account],
						'time': gajim.config.get('autoawaytime')
						}
				self.roster.send_status(account, 'away', auto_message, auto=True)
				gajim.sleeper_state[account] = 'autoaway'
			elif state == common.sleepy.STATE_XA and (\
				gajim.sleeper_state[account] == 'autoaway' or \
				gajim.sleeper_state[account] == 'online') and \
				gajim.config.get('autoxa'):
				# we go extended away [we pass True to auto param]
				auto_message = gajim.config.get('autoxa_message')
				if not auto_message:
					auto_message = gajim.connections[account].status
				else:
					auto_message = auto_message.replace('$S','%(status)s')
					auto_message = auto_message.replace('$T','%(time)s')
					auto_message = auto_message % {
						'status': gajim.status_before_autoaway[account], 
						'time': gajim.config.get('autoxatime')
						}
				self.roster.send_status(account, 'xa', auto_message, auto=True)
				gajim.sleeper_state[account] = 'autoxa'
		return True # renew timeout (loop for ever)

	def autoconnect(self):
		'''auto connect at startup'''
		# dict of account that want to connect sorted by status
		shows = {}
		for a in gajim.connections:
			if gajim.config.get_per('accounts', a, 'autoconnect'):
				if gajim.config.get_per('accounts', a, 'restore_last_status'):
					self.roster.send_status(a, gajim.config.get_per('accounts', a,
						'last_status'), helpers.from_one_line(gajim.config.get_per(
						'accounts', a, 'last_status_msg')))
					continue
				show = gajim.config.get_per('accounts', a, 'autoconnect_as')
				if not show in gajim.SHOW_LIST:
					continue
				if not show in shows:
					shows[show] = [a]
				else:
					shows[show].append(a)
		def on_message(message):
			if message is None:
				return
			for a in shows[show]:
				self.roster.send_status(a, show, message)
		for show in shows:
			message = self.roster.get_status_message(show, on_message)
		return False

	def show_systray(self):
		self.systray_enabled = True
		self.systray.show_icon()

	def hide_systray(self):
		self.systray_enabled = False
		self.systray.hide_icon()

	def on_launch_browser_mailer(self, widget, url, kind):
		helpers.launch_browser_mailer(kind, url)

	def process_connections(self):
		''' called each foo (200) miliseconds. Check for idlequeue timeouts.
		'''
		try:
			gajim.idlequeue.process()
		except Exception:
			# Otherwise, an exception will stop our loop
			if gajim.idlequeue.__class__ == GlibIdleQueue:
				gobject.timeout_add_seconds(2, self.process_connections)
			else:
				gobject.timeout_add(200, self.process_connections)
			raise
		return True # renew timeout (loop for ever)

	def save_config(self):
		err_str = parser.write()
		if err_str is not None:
			print >> sys.stderr, err_str
			# it is good to notify the user
			# in case he or she cannot see the output of the console
			dialogs.ErrorDialog(_('Could not save your settings and preferences'),
				err_str)
			sys.exit()

	def save_avatar_files(self, jid, photo, puny_nick = None, local = False):
		'''Saves an avatar to a separate file, and generate files for dbus notifications. An avatar can be given as a pixmap directly or as an decoded image.'''
		puny_jid = helpers.sanitize_filename(jid)
		path_to_file = os.path.join(gajim.AVATAR_PATH, puny_jid)
		if puny_nick:
			path_to_file = os.path.join(path_to_file, puny_nick)
		# remove old avatars
		for typ in ('jpeg', 'png'):
			if local:
				path_to_original_file = path_to_file + '_local'+  '.' + typ
			else:
				path_to_original_file = path_to_file + '.' + typ
			if os.path.isfile(path_to_original_file):
				os.remove(path_to_original_file)
		if local and photo:
			pixbuf = photo
			type = 'png'
			extension = '_local.png' # save local avatars as png file
		else:
			pixbuf, typ = gtkgui_helpers.get_pixbuf_from_data(photo, want_type = True)
			if  pixbuf is None:
				return
			extension = '.' + typ
			if typ not in ('jpeg', 'png'):
				gajim.log.debug('gtkpixbuf cannot save other than jpeg and png formats. saving %s\'avatar as png file (originaly %s)' % (jid, typ))
				typ = 'png'
				extension = '.png'
		path_to_original_file = path_to_file + extension
		pixbuf.save(path_to_original_file, typ)
		# Generate and save the resized, color avatar
		pixbuf = gtkgui_helpers.get_scaled_pixbuf(pixbuf, 'notification')
		if pixbuf:
			path_to_normal_file = path_to_file + '_notif_size_colored' + extension
			pixbuf.save(path_to_normal_file, 'png')
			# Generate and save the resized, black and white avatar
			bwbuf = gtkgui_helpers.get_scaled_pixbuf(
				gtkgui_helpers.make_pixbuf_grayscale(pixbuf), 'notification')
			if bwbuf:
				path_to_bw_file = path_to_file + '_notif_size_bw' + extension
				bwbuf.save(path_to_bw_file, 'png')

	def remove_avatar_files(self, jid, puny_nick = None, local = False):
		'''remove avatar files of a jid'''
		puny_jid = helpers.sanitize_filename(jid)
		path_to_file = os.path.join(gajim.AVATAR_PATH, puny_jid)
		if puny_nick:
			path_to_file = os.path.join(path_to_file, puny_nick)
		for ext in ('.jpeg', '.png'):
			if local:
				ext = '_local' + ext
			path_to_original_file = path_to_file + ext
			if os.path.isfile(path_to_file + ext):
				os.remove(path_to_file + ext)
			if os.path.isfile(path_to_file + '_notif_size_colored' + ext):
				os.remove(path_to_file + '_notif_size_colored' + ext)
			if os.path.isfile(path_to_file + '_notif_size_bw' + ext):
				os.remove(path_to_file + '_notif_size_bw' + ext)

	def auto_join_bookmarks(self, account):
		'''autojoin bookmarked GCs that have 'auto join' on for this account'''
		for bm in gajim.connections[account].bookmarks:
			if bm['autojoin'] in ('1', 'true'):
				jid = bm['jid']
				# Only join non-opened groupchats. Opened one are already
				# auto-joined on re-connection
				if not jid in gajim.gc_connected[account]:
					# we are not already connected
					minimize = bm['minimize'] in ('1', 'true')
					gajim.interface.join_gc_room(account, jid, bm['nick'],
					bm['password'], minimize = minimize)
				elif jid in self.minimized_controls[account]:
					# more or less a hack:
					# On disconnect the minimized gc contact instances 
					# were set to offline. Reconnect them to show up in the roster.
					self.roster.add_groupchat(jid, account)

	def add_gc_bookmark(self, account, name, jid, autojoin, minimize, password,
		nick):
		'''add a bookmark for this account, sorted in bookmark list'''
		bm = {
			'name': name,
			'jid': jid,
			'autojoin': autojoin,
			'minimize': minimize,
			'password': password,
			'nick': nick
		}
		place_found = False
		index = 0
		# check for duplicate entry and respect alpha order
		for bookmark in gajim.connections[account].bookmarks:
			if bookmark['jid'] == bm['jid']:
				dialogs.ErrorDialog(
					_('Bookmark already set'),
					_('Group Chat "%s" is already in your bookmarks.') % bm['jid'])
				return
			if bookmark['name'] > bm['name']:
				place_found = True
				break
			index += 1
		if place_found:
			gajim.connections[account].bookmarks.insert(index, bm)
		else:
			gajim.connections[account].bookmarks.append(bm)
		gajim.connections[account].store_bookmarks()
		self.roster.set_actions_menu_needs_rebuild()
		dialogs.InformationDialog(
				_('Bookmark has been added successfully'),
				_('You can manage your bookmarks via Actions menu in your roster.'))


	# does JID exist only within a groupchat?
	def is_pm_contact(self, fjid, account):
		bare_jid = gajim.get_jid_without_resource(fjid)

		gc_ctrl = self.msg_win_mgr.get_gc_control(bare_jid, account)

		if not gc_ctrl and \
		bare_jid in self.minimized_controls[account]:
			gc_ctrl = self.minimized_controls[account][bare_jid]

		return gc_ctrl and gc_ctrl.type_id == message_control.TYPE_GC

	def create_ipython_window(self):
		try:
			from ipython_view import IPythonView
		except ImportError:
			print 'ipython_view not found'
			return
		import pango

		if os.name == 'nt':
			font = 'Lucida Console 9'
		else:
			font = 'Luxi Mono 10'

		window = gtk.Window()
		window.set_size_request(750,550)
		window.set_resizable(True)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		view = IPythonView()
		view.modify_font(pango.FontDescription(font))
		view.set_wrap_mode(gtk.WRAP_CHAR)
		sw.add(view)
		window.add(sw)
		window.show_all()
		def on_delete(win, event):
			win.hide()
			return True
		window.connect('delete_event',on_delete)
		view.updateNamespace({'gajim': gajim})
		gajim.ipython_window = window

	def __init__(self):
		gajim.interface = self
		# This is the manager and factory of message windows set by the module
		self.msg_win_mgr = None
		self.jabber_state_images = {'16': {}, '32': {}, 'opened': {},
			'closed': {}}
		self.emoticons_menu = None
		# handler when an emoticon is clicked in emoticons_menu
		self.emoticon_menuitem_clicked = None
		self.minimized_controls = {}
		self.status_sent_to_users = {}
		self.status_sent_to_groups = {}
		self.gpg_passphrase = {}
		self.gpg_dialog = None
		self.default_colors = {
			'inmsgcolor': gajim.config.get('inmsgcolor'),
			'outmsgcolor': gajim.config.get('outmsgcolor'),
			'statusmsgcolor': gajim.config.get('statusmsgcolor'),
			'urlmsgcolor': gajim.config.get('urlmsgcolor'),
		}

		cfg_was_read = parser.read()
		# Do not set gajim.verbose to False if -v option was given
		if gajim.config.get('verbose'):
			gajim.verbose = True

		# Is Gajim default app?
		if os.name != 'nt' and gajim.config.get('check_if_gajim_is_default'):
			gtkgui_helpers.possibly_set_gajim_as_xmpp_handler()

		for account in gajim.config.get_per('accounts'):
			if gajim.config.get_per('accounts', account, 'is_zeroconf'):
				gajim.ZEROCONF_ACC_NAME = account
				break
		# Is gnome configured to activate row on single click ?
		try:
			import gconf
			client = gconf.client_get_default()
			click_policy = client.get_string(
				'/apps/nautilus/preferences/click_policy')
			if click_policy == 'single':
				gajim.single_click = True
		except Exception:
			pass
		# add default status messages if there is not in the config file
		if len(gajim.config.get_per('statusmsg')) == 0:
			for msg in gajim.config.statusmsg_default:
				gajim.config.add_per('statusmsg', msg)
				gajim.config.set_per('statusmsg', msg, 'message',
					gajim.config.statusmsg_default[msg])
		#add default themes if there is not in the config file
		theme = gajim.config.get('roster_theme')
		if not theme in gajim.config.get_per('themes'):
			gajim.config.set('roster_theme', _('default'))
		if len(gajim.config.get_per('themes')) == 0:
			d = ['accounttextcolor', 'accountbgcolor', 'accountfont',
				'accountfontattrs', 'grouptextcolor', 'groupbgcolor', 'groupfont',
				'groupfontattrs', 'contacttextcolor', 'contactbgcolor',
				'contactfont', 'contactfontattrs', 'bannertextcolor',
				'bannerbgcolor']

			default = gajim.config.themes_default
			for theme_name in default:
				gajim.config.add_per('themes', theme_name)
				theme = default[theme_name]
				for o in d:
					gajim.config.set_per('themes', theme_name, o,
						theme[d.index(o)])

		if gajim.config.get('autodetect_browser_mailer') or not cfg_was_read:
			gtkgui_helpers.autodetect_browser_mailer()

		if gajim.verbose:
			gajim.log.setLevel(gajim.logging.DEBUG)
		else:
			gajim.log.setLevel(None)

		# pygtk2.8+ on win, breaks io_add_watch.
		# We use good old select.select()
		if os.name == 'nt':
			gajim.idlequeue = idlequeue.SelectIdleQueue()
		else:
			# in a nongui implementation, just call:
			# gajim.idlequeue = IdleQueue() , and
			# gajim.idlequeue.process() each foo miliseconds
			gajim.idlequeue = GlibIdleQueue()
		# resolve and keep current record of resolved hosts
		gajim.resolver = nslookup.Resolver(gajim.idlequeue)
		gajim.socks5queue = socks5.SocksQueue(gajim.idlequeue,
			self.handle_event_file_rcv_completed,
			self.handle_event_file_progress,
			self.handle_event_file_error)
		gajim.proxy65_manager = proxy65_manager.Proxy65Manager(gajim.idlequeue)
		gajim.default_session_type = ChatControlSession
		self.register_handlers()
		if gajim.config.get('enable_zeroconf'):
			gajim.connections[gajim.ZEROCONF_ACC_NAME] = common.zeroconf.connection_zeroconf.ConnectionZeroconf(gajim.ZEROCONF_ACC_NAME)
		for account in gajim.config.get_per('accounts'):
			if not gajim.config.get_per('accounts', account, 'is_zeroconf'):
				gajim.connections[account] = common.connection.Connection(account)

		# gtk hooks
		gtk.about_dialog_set_email_hook(self.on_launch_browser_mailer, 'mail')
		gtk.about_dialog_set_url_hook(self.on_launch_browser_mailer, 'url')
		if gtk.pygtk_version >= (2, 10, 0) and gtk.gtk_version >= (2, 10, 0):
			gtk.link_button_set_uri_hook(self.on_launch_browser_mailer, 'url')

		self.instances = {}

		for a in gajim.connections:
			self.instances[a] = {'infos': {}, 'disco': {}, 'gc_config': {},
				'search': {}}
			self.minimized_controls[a] = {}
			gajim.contacts.add_account(a)
			gajim.groups[a] = {}
			gajim.gc_connected[a] = {}
			gajim.automatic_rooms[a] = {}
			gajim.newly_added[a] = []
			gajim.to_be_removed[a] = []
			gajim.nicks[a] = gajim.config.get_per('accounts', a, 'name')
			gajim.block_signed_in_notifications[a] = True
			gajim.sleeper_state[a] = 0
			gajim.encrypted_chats[a] = []
			gajim.last_message_time[a] = {}
			gajim.status_before_autoaway[a] = ''
			gajim.transport_avatar[a] = {}
			gajim.gajim_optional_features[a] = []
			gajim.caps_hash[a] = ''

		helpers.update_optional_features()

		if gajim.config.get('remote_control'):
			try:
				import remote_control
				self.remote_ctrl = remote_control.Remote()
			except Exception:
				self.remote_ctrl = None
		else:
			self.remote_ctrl = None

		if gajim.config.get('networkmanager_support') and dbus_support.supported:
			import network_manager_listener
			if not network_manager_listener.supported:
				print >> sys.stderr, _('Network Manager support not available')

		# Handle gnome screensaver
		if dbus_support.supported:
			def gnome_screensaver_ActiveChanged_cb(active):
				if not active:
					return
				if not gajim.config.get('autoaway'):
					# Don't go auto away if user disabled the option
					return
				for account in gajim.connections:
					if account not in gajim.sleeper_state or \
							not gajim.sleeper_state[account]:
						continue
					if gajim.sleeper_state[account] == 'online':
						# we save out online status
						gajim.status_before_autoaway[account] = \
							gajim.connections[account].status
						# we go away (no auto status) [we pass True to auto param]
						auto_message = gajim.config.get('autoaway_message')
						if not auto_message:
							auto_message = gajim.connections[account].status
						self.roster.send_status(account, 'away', auto_message,
							auto=True)
						gajim.sleeper_state[account] = 'autoaway'

			try:
				bus = dbus.SessionBus()
				bus.add_signal_receiver(gnome_screensaver_ActiveChanged_cb,
					'ActiveChanged', 'org.gnome.ScreenSaver')
			except Exception:
				pass

		self.show_vcard_when_connect = []

		self.sleeper = common.sleepy.Sleepy(
			gajim.config.get('autoawaytime') * 60, # make minutes to seconds
			gajim.config.get('autoxatime') * 60)

		gtkgui_helpers.make_jabber_state_images()

		self.systray_enabled = False
		self.systray_capabilities = False

		if (((os.name == 'nt') or (sys.platform == 'darwin')) and
			(gtk.pygtk_version >= (2, 10, 0)) and
			(gtk.gtk_version >= (2, 10, 0))):
			import statusicon
			self.systray = statusicon.StatusIcon()
			self.systray_capabilities = True
		else: # use ours, not GTK+ one
			# [FIXME: remove this when we migrate to 2.10 and we can do
			# cool tooltips somehow and (not dying to keep) animation]
			import systray
			self.systray_capabilities = systray.HAS_SYSTRAY_CAPABILITIES
			if self.systray_capabilities:
				self.systray = systray.Systray()

		if self.systray_capabilities and gajim.config.get('trayicon'):
			self.show_systray()

		path_to_file = os.path.join(gajim.DATA_DIR, 'pixmaps', 'gajim.png')
		pix = gtk.gdk.pixbuf_new_from_file(path_to_file)
		# set the icon to all windows
		gtk.window_set_default_icon(pix)

		self.roster = roster_window.RosterWindow()

		self.init_emoticons()
		self.make_regexps()

		# get instances for windows/dialogs that will show_all()/hide()
		self.instances['file_transfers'] = dialogs.FileTransfersWindow()

		# get transports type from DB
		gajim.transport_type = gajim.logger.get_transports_type()

		# test is dictionnary is present for speller
		if gajim.config.get('use_speller'):
			lang = gajim.config.get('speller_language')
			if not lang:
				lang = gajim.LANG
			tv = gtk.TextView()
			try:
				import gtkspell
				spell = gtkspell.Spell(tv, lang)
			except Exception:
				dialogs.AspellDictError(lang)

		if gajim.config.get('soundplayer') == '':
			# only on first time Gajim starts
			commands = ('aplay', 'play', 'esdplay', 'artsplay')
			for command in commands:
				if helpers.is_in_path(command):
					if command == 'aplay':
						command += ' -q'
					gajim.config.set('soundplayer', command)
					break

		self.last_ftwindow_update = 0

		gobject.timeout_add(100, self.autoconnect)
		if gajim.idlequeue.__class__ == GlibIdleQueue:
			gobject.timeout_add_seconds(2, self.process_connections)
		else:
			gobject.timeout_add(200, self.process_connections)
		gobject.timeout_add_seconds(gajim.config.get(
			'check_idle_every_foo_seconds'), self.read_sleepy)

if __name__ == '__main__':
	def sigint_cb(num, stack):
		sys.exit(5)
	# ^C exits the application normally to delete pid file
	signal.signal(signal.SIGINT, sigint_cb)

	if gajim.verbose:
		print >> sys.stderr, "Encodings: d:%s, fs:%s, p:%s" % \
		(sys.getdefaultencoding(), sys.getfilesystemencoding(), locale.getpreferredencoding())

	if ((os.name != 'nt') and (sys.platform != 'darwin')):
		# Session Management support
		try:
			import gnome.ui
		except ImportError:
			print >> sys.stderr, _('Session Management support not available (missing gnome.ui module)')
		else:
			def die_cb(cli):
				gajim.interface.roster.quit_gtkgui_interface()
			gnome.program_init('gajim', gajim.version)
			cli = gnome.ui.master_client()
			cli.connect('die', die_cb)

			path_to_gajim_script = gtkgui_helpers.get_abspath_for_script(
				'gajim')

			if path_to_gajim_script:
				argv = [path_to_gajim_script]
				# FIXME: remove this typeerror catch when gnome python is old and
				# not bad patched by distro men [2.12.0 + should not need all that
				# NORMALLY]
				try:
					cli.set_restart_command(argv)
				except AttributeError:
					cli.set_restart_command(len(argv), argv)

	check_paths.check_and_possibly_create_paths()

	if sys.platform == 'darwin':
		try:
			import osx
			osx.init()
		except ImportError:
			pass

	Interface()

	try:
		gtk.main()
	except KeyboardInterrupt:
		print >> sys.stderr, 'KeyboardInterrupt'

# vim: se ts=3:
