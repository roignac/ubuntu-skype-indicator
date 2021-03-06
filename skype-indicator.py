#!/usr/bin/env python
#
#Copyright 2010 Jonathan Foucher
#
#Authors:
#		Jonathan Foucher <jfoucher@6px.eu>
#
#This program is free software: you can redistribute it and/or modify it 
#under the terms of either or both of the following licenses:
#
#1) the GNU Lesser General Public License version 3, as published by the 
#Free Software Foundation; and/or
#2) the GNU Lesser General Public License version 2.1, as published by 
#the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
#PURPOSE.	See the applicable version of the GNU Lesser General Public 
#License for more details.
#
#You should have received a copy of both the GNU Lesser General Public 
#License version 3 and version 2.1 along with this program.	If not, see 
#<http://www.gnu.org/licenses/>
#


import indicate
import gobject
import pynotify
import gtk
import hashlib
import Skype4Py
import urllib
import os
import time
import glob

class notification:
	notif_type = None
	handle = None
	name = None
	msg = None
	count = -1
	timestamp = None
	indicator = None
	avatar_path = None
	avatar_file = None
	pixbuf = None
	skype = None
	
	def __init__(self, notif_type, handle, msg, skype):
		self.notif_type = notif_type
		self.handle = handle
		self.skype = skype
		self.msg = msg

		# Determine a name for specific notif_type
		self.name = {
			'message': self.get_user_name,
			'chat'	 : self.get_chat_name,
			'call'	 : self.get_call_name
		}.get(self.notif_type)(self.handle)

		#Get a timestamp for missed event
		self.timestamp = {
			'message': self.get_timestamp_of_last_missed_message,
			'chat'	 : self.get_timestamp_of_last_missed_message,
			'call'	 : self.get_timestamp_of_last_missed_call
		}.get(self.notif_type)(self.handle)

		# Create an avatar
		self.find_avatar_for_handle(self.handle)

	def ellipsis(self, name):
		""" Add an ellipsis after ellipsis_length symbols if name is too long """
		name = (name[:ellipsis_length] + '..') if len(name) > ellipsis_length else name
		return name

	def get_user_name(self, handle):
		"""getting user name"""
		if self.skype.User(handle).DisplayName:
			user_name = self.skype.User(handle).DisplayName
		elif self.skype.User(handle).FullName:
			user_name = self.skype.User(handle).FullName
		else:
			user_name = handle
		return self.ellipsis(user_name)

	def get_chat_name(self, handle):
		"""getting chat name"""
		return self.ellipsis(self.skype.Chat(handle).FriendlyName)

	def get_call_name(self, handle):
		"""getting call name - constructing it out of participants names"""
		call_name = "Call from %s" % self.skype.Call(handle).PartnerDisplayName
		return self.ellipsis(call_name)

	def get_last_private_message(self, handle):
		"""getting last private message """
		return self.msg.Body

	def get_last_chat_message(self, handle):
		"""getting last message in chat"""
		return "%s: %s" % (self.msg.FromDisplayName, self.msg.Body)

	def get_call_notification_contents(self, handle):
		"""getting call notification text"""
		call = self.skype.Call(handle)
		call_name = "Missed call with "
		for participant in call.Participants:
			call_name += "%s," % participant.DisplayName
		return self.ellipsis(call_name)

	def find_avatar_for_handle(self, handle):
		if self.notif_type == 'message':
			data_file_part = 'user'
			magic_key = "\x03\x10"
		elif self.notif_type == 'chat':
			data_file_part = 'chat'
			magic_key = "\x03"
		h=hashlib.md5(handle).hexdigest()
		self.avatar_file=os.path.join(avatar_directory, "%s.jpg" % str(h))
		if not os.path.exists(self.avatar_file):
			#Try to get user data from files in ~/.Skype
			data_files = glob.glob(os.path.join(os.path.expanduser("~/.Skype"), current_user_name, "%s*.dbb" % data_file_part))
			for data_file in data_files:
				#Open file and seek for magic_key+handle combination
				file = open(data_file,'r')
				file_contents = file.read()
				file.close()
				position = file_contents.find(magic_key + handle)
				if position != -1:
					self.grab_avatar_from_file(data_file, position, handle)

		# If file has not bveen create, give up and generate the avatar
		if not os.path.exists(self.avatar_file):
			urllib.urlretrieve('http://friedcellcollective.net/monsterid/monster/%s/64' % h, self.avatar_file)
		self.pixbuf=gtk.gdk.pixbuf_new_from_file(self.avatar_file)
		return self.avatar_file

	def grab_avatar_from_file(self, full_path, position, handle):
		""" create an avatar from avataprir_data """
		#Open file and read the whole file
		file = open(full_path,'r')
		file_contents = file.read()
		file.close()
		#Find the nearest l33l block to 'position'
		leel_block_start_position = file_contents.find("l33l", 0, position)
		while leel_block_start_position != -1:
			old_start_position = leel_block_start_position
			leel_block_start_position = file_contents.find("l33l", leel_block_start_position+1, position)
		leel_block_start_position = old_start_position
		#Find the end of l33l block
		leel_block_end_position = file_contents.find("l33l", leel_block_start_position+1)
		# Seek for JPEG block within l33l block
		jpeg_start_position = file_contents.find("\xff\xd8", leel_block_start_position, leel_block_end_position)
		if jpeg_start_position != -1:
			jpeg_end_position = file_contents.find("\xff\xd9", jpeg_start_position, leel_block_end_position)
			if jpeg_end_position != -1:
				avatar_data=file_contents[jpeg_start_position:jpeg_end_position+2]
				avatar = open(self.avatar_file,'w')
				avatar.write(avatar_data)
				avatar.flush()
				avatar.close()

	def get_timestamp_of_last_missed_message(self, handle):
		"""getting a timestamp of last missed message"""
		return self.msg.Timestamp

	def get_timestamp_of_last_missed_call(self, handle):
		""" getting timestamp of last missed call"""
		return self.skype.Call(handle).Timestamp

	def update_count(self):
		"""update a count message for this indicator"""
		self.count += 1
		self.indicator.set_property("count", str(self.count))

	def create_indicator(self):
		""" Create a new active indicator """
		self.indicator = indicate.Indicator()
		self.indicator.set_property("subtype", "im")
		self.indicator.set_property("sender", self.name)
		self.indicator.set_property_icon("icon", self.pixbuf)
		self.indicator.set_property_time("time", self.timestamp)
		self.indicator.set_property("draw-attention", "true")
		self.indicator.show()
		self.indicator.connect("user-display", self.display_skype)

	def create_notification(self):
		""" Create a new notification """
		# Determine a message for specific notif_type
		self.message_text = {
			'message': self.get_last_private_message,
			'chat'	 : self.get_last_chat_message,
			'call'	 : self.get_call_notification_contents
		}.get(self.notif_type)(self.handle)
		n = pynotify.Notification(self.name, self.message_text, "notification-message-im")
		n.set_property("icon-name", self.avatar_file)
		n.show()

	def display_skype(self, indicator, timestamp):
		""" display skype window for specific notif_type """
		#hide this indicator and make messaging menu go back to normal
		self.indicator.hide()
		self.indicator.set_property("draw-attention", "false")
		#Call correct funtion to open the Skype window
		{
			'message': self.display_user,
			'chat'	 : self.display_chat,
			'call'	 : self.display_call
		}.get(self.notif_type)(self.handle)
		#Destroy the object by setting handle to None - will be removed during append_notification call
		self.handle = None

	def display_user(self, handle):
		self.skype.Client.OpenMessageDialog(handle)

	def display_chat(self, handle):
		self.skype.Client.OpenDialog('CHAT', handle)

	def display_call(self, handle):
		pass
		#FIXME: Open call window
		#self.skype.Client.OpenDialog('CALL', handle)

class skypeIndicator:
	server = None
	notifications = []

	def __init__(self):
		""" Initialize """
		#get skype control
		self.skype = Skype4Py.Skype()
		#Check that skype is running, otherwise - start it and wait for 10 secs
		try:
			if not self.skype.Client.IsRunning:
				self.skype.Client.Start()
		except:
			os.system("skype &")
			time.sleep(10)

		try:
			self.skype.Attach()
		except Skype4Py.errors.SkypeAPIError:
			print "Please open skype first"
			self.noSkype()

		#Get current username
		global current_user_name
		current_user_name = self.skype.CurrentUserHandle
		#create notification icon
		self.create_server()
		#Setting event callbacks
		self.skype.OnMessageStatus = self.callback_messages
		self.skype.OnCallStatus = self.callback_calls
		#Adding missed events
		self.create_indicators()

	def noSkype(self):
		"""Shows a notification if skype is not started"""
		n = pynotify.Notification('Start Skype', 'Please start skype otherwise this won\'t work', "notification-message-im")
		n.set_property("icon-name",gtk.STOCK_DIALOG_WARNING)
		n.show()
		return n

	def create_server(self):
		""" Create a new Skype notification server """
		#Create a notification server
		self.server = indicate.indicate_server_ref_default()
		self.server.set_type("message.im")
		self.server.set_desktop_file("/usr/share/applications/skype.desktop")
		self.server.connect("server-display", self.server_display)
		self.server.show()

	def server_display(self, widget, timestamp=None):
		""" Open main Skype window """
		self.skype.Client.Focus()

	def create_indicators(self):
		""" Check for missed messages / chats / calls """
		for msg in self.skype.MissedMessages:
			self.callback_messages(msg, 'RECEIVED')

		for call in self.skype.MissedCalls:
			self.callback_calls(self, call, 'RECEIVED')

	def callback_messages(self, msg, status):
		if status == 'RECEIVED':
			chat_members = len(msg.Chat.Members)
			if (chat_members > 2):
				new_notification=notification("chat", msg.ChatName, msg, self.skype)
			else:
				new_notification=notification("message", msg.FromHandle, msg, self.skype)
			self.append_notification(new_notification)

	def callback_calls(self, call, status):
		if status == Skype4Py.clsRinging and call.Type.startswith('INCOMING'):
			new_notification=notification("call", call.Id, None, self.skype)
			self.append_notification(new_notification)

	def append_notification(self, new_notification):
		""" Append a new notification, checking previous notifications"""
		found = False
		# Check that the indicator for this event type and handle has not already been created
		for notification in self.notifications:
			# Removing notifications with handle None
			if notification.handle == None:
				del self.notifications[self.notifications.index(notification)]
			if ((notification.handle == new_notification.handle) and (notification.notif_type == new_notification.notif_type)):
				notification.update_count()
				found = True

		#Create a new indicator and notification
		if not found:
			new_notification.create_indicator()
			new_notification.create_notification()
			self.notifications.append(new_notification)

if __name__ == "__main__":
	#Global variables
	avatar_directory = None
	ellipsis_length = 30
	user_files = ["user256", "user1024", "user4096", "user16384", "user32768"]
	chat_files = ["chat256", "chat1024", "chat4096", "chat16384", "chat32768"]
	current_user_name = None

	#Prepare a variable to store avatars. Check that avatar dir exists, otherwise - create it
	avatar_directory = os.path.expanduser("~/.cache/ubuntu-skype-indicator")
	if not os.path.isdir(avatar_directory):
		os.mkdir(avatar_directory)

	skypeind=skypeIndicator()

	# Loop
	gobject.timeout_add_seconds(5, skypeind.create_indicators)
	gtk.main()
