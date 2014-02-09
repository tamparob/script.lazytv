#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (C) 2013 KodeKarnage
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
#  This script uses significant elements from service.skin.widgets
#  by Martijn & phil65

import random
import xbmcgui
import xbmcaddon
import time
import datetime
import sys
import os
import ast
import json
#from resources.lazy_lib import *

plf            = {"jsonrpc": "2.0","id": 1, "method": "Files.GetDirectory", 		"params": {"directory": "special://profile/playlists/video/", "media": "video"}}
eps_query      = {"jsonrpc": "2.0","id": 1, "method": "VideoLibrary.GetEpisodes",	"params": {"properties": ["season","episode","runtime","resume","playcount","tvshowid","lastplayed","file"],"tvshowid": "placeholder" }}
seek           = {"jsonrpc": "2.0","id": 1, "method": "Player.Seek",				"params": {"playerid": 1, "value": 0 }}
clear_playlist = {"jsonrpc": "2.0","id": 1, "method": "Playlist.Clear",				"params": {"playlistid": 1}}
add_this_ep    = {'jsonrpc': '2.0','id': 1, "method": 'Playlist.Add', 				"params": {'item' : {'episodeid' : 'placeholder' }, 'playlistid' : 1}}
get_items      = {'jsonrpc': '2.0','id': 1, "method": 'Player.GetItem',				"params": {'playerid': 1, 'properties': ['tvshowid','resume']}}

#sys.stdout = open('C:\\Temp\\test.txt', 'w')
'''
bug_exists = False #Buggalo
try:
	__buggalo__    = xbmcaddon.Addon("script.module.buggalo")
	_bugversion_ = __buggalo__.getAddonInfo("version")
	bv = _bugversion_.split(".")
	bvtup = (bv[0],bv[1],bv[2])
	if bvtup > (1,1,3):
		import buggalo
		bug_exists = True
except:
	pass'''

__addon__         = xbmcaddon.Addon()
__addonid__       = __addon__.getAddonInfo('id')
__setting__       = __addon__.getSetting
lang              = __addon__.getLocalizedString
dialog            = xbmcgui.Dialog()
scriptPath        = __addon__.getAddonInfo('path')
__release__       = "Frodo" if xbmcaddon.Addon('xbmc.addon').getAddonInfo('version') == (12,0,0) else "Gotham"

WINDOW            = xbmcgui.Window(10000)

__resource__      =  os.path.join(scriptPath, 'resources', 'lib')
sys.path.append(__resource__)

start_time       = time.time()
base_time        = time.time()

primary_function = __setting__('primary_function')
populate_by      = __setting__('populate_by')
select_pl        = __setting__('select_pl')
default_playlist = __setting__('file')
length           = int(__setting__('length'))
multipleshows    = __setting__('multipleshows')
premieres        = __setting__('premieres')
resume_partials  = __setting__('resume_partials')	#ONLY applies in random playlist, need to populate resume_dict
nextprompt       = __setting__('nextprompt')				#HANDLE IN SERVICE OR THROUGH PLAYER CLASS
promptduration   = __setting__('promptduration')		#HANDLE IN SERVICE OR THROUGH PLAYER CLASS
notify           = __setting__('notify')
keep_logs        = True if __setting__('logging') == 'true' else False
window_length    = int(__setting__('window_length'))
limitshows       = True if __setting__('limitshows') == 'true' else False

# This is a throwaway variable to deal with a python bug
try:
	throwaway = datetime.datetime.strptime('20110101','%Y%m%d')
except:
	pass

def log(message, label=''):
	if keep_logs:
		global start_time
		global base_time
		new_time   = time.time()
		gap_time   = "%5f" % (new_time - start_time)
		start_time = new_time
		total_gap  = "%5f" % (new_time - base_time)
		logmsg     = '%s : %s :: %s ::: %s     %s ' % (__addonid__+'addon', round(float(total_gap),5), round(float(gap_time),5), label,message)
		xbmc.log(msg = logmsg)



def gracefail(message):
	dialog.ok("LazyTV",message)
	sys.exit()

def json_query(query, ret):
	try:
		xbmc_request = json.dumps(query)
		result = xbmc.executeJSONRPC(xbmc_request)
		result = unicode(result, 'utf-8', errors='ignore')
		if ret:
			return json.loads(result)['result']
		else:
			return json.loads(result)
	except:
		return {}




def playlist_selection_window():
	#Purpose: launch Select Window populated with smart playlists

	playlist_files = json_query(plf, True)['files']

	if playlist_files != None:

		plist_files   = dict((x['label'],x['file']) for x in playlist_files)
		playlist_list =  plist_files.keys()

		playlist_list.sort()
		inputchoice = xbmcgui.Dialog().select(lang(32048), playlist_list)

		return plist_files[playlist_list[inputchoice]]
	else:
		return 'empty'

def day_conv(date_string):
	op_format = '%Y-%m-%d %H:%M:%S'
	Y, M, D, h, mn, s, ux, uy, uz        = time.strptime(date_string, op_format)
	lw_max    = datetime.datetime(Y, M, D, h ,mn, s)
	date_num  = time.mktime(lw_max.timetuple())
	return date_num


def day_calc(date_string, todate, output):
	op_format = '%Y-%m-%d %H:%M:%S'
	lw = time.strptime(date_string, op_format)
	if output == 'diff':
		lw_date    = datetime.date(lw[0],lw[1],lw[2])
		day_string = str((todate - lw_date).days) + " days)"
		return day_string
	else:
		lw_max   = datetime.datetime(lw[0],lw[1],lw[2],lw[3],lw[4],lw[5])
		date_num = time.mktime(lw_max.timetuple())
		return date_num


def next_show_engine(showid, eps = [], Season = 'null', Episode = 'null'):

	if not eps:
		eps_query['params']['tvshowid'] = int(showid)
		ep = json_query(eps_query, True)				# query grabs the TV show episodes

		if 'episodes' not in ep: 						#ignore show if show has no episodes
			return 'null'
		else:
			eps = ep['episodes']

	#uses the season and episode number to create a list of unwatched shows newer than the last watched one
	unplayed_eps = [x for x in eps if ((x['season'] == int(Season) and x['episode'] > int(Episode)) or (x['season'] > int(Season)))]

	#sorts the list of unwatched shows by lowest season and lowest episode, filters the list to remove empty strings
	next_ep = sorted(unplayed_eps, key = lambda unplayed_eps: (unplayed_eps['season'], unplayed_eps['episode']))
	next_ep = filter(None, next_ep)

	if not next_ep:
		return 'null', ['null','null']
	elif 'episodeid' not in next_ep[0]:
		return 'null', ['null','null']
	else:
		return next_ep[0]['episodeid'], [next_ep[0]['season'],next_ep[0]['episode']]


class xGUI(xbmcgui.WindowXMLDialog):

	def onInit(self):

		self.ok = self.getControl(5)
		self.ok.setLabel(lang(32106))

		self.hdg = self.getControl(1)
		self.hdg.setLabel('LazyTV')
		self.hdg.setVisible(True)

		self.ctrl6failed = False

		try:
			self.name_list = self.getControl(6)
			self.x = self.getControl(3)
			self.x.setVisible(False)

		except:
			self.ctrl6failed = True  #for some reason control3 doesnt work for me, so this work around tries control6
			self.close()			 #and exits if it fails, CTRL6FAILED then triggers a dialog.select instead

		self.now = time.time()

		self.count = 0
		for i, show in enumerate(stored_showids):

			if self.count == 1000 or (limitshows == True and i == window_length):
				break

			self.pctplyd  = WINDOW.getProperty("%s.%s.PercentPlayed"           % ('LazyTV', show))
			if stored_lw[i] == 0:
				self.lw_time = 'never'
			else:
				self.gap = str(round((self.now - stored_lw[i]) / 86400.0, 1))
				if self.gap > 1:
					self.lw_time = self.gap + ' days'
				else:
					self.lw_time = self.gap + ' day'

			if self.pctplyd == '0%':
				self.pct = ''
			else:
				self.pct = self.pctplyd + ', '
			self.label2 = '(' + self.pct + self.lw_time + ')'
			self.thumb  = WINDOW.getProperty("%s.%s.Art(tvshow.poster)" % ('LazyTV', show))
			self.title  = WINDOW.getProperty("%s.%s.TVshowTitle" % ('LazyTV', show))
			self.tmp    = xbmcgui.ListItem(label=self.title, label2=self.label2, thumbnailImage = self.thumb)
			self.name_list.addItem(self.tmp)
			self.count += 1

		self.ok.controlRight(self.name_list)
		self.setFocus(self.name_list)
		log('window up')

	def onAction(self, action):
		actionID = action.getId()
		if (actionID in (10, 92)):
			self.load_show_id = -1
			self.close()

	def onClick(self, controlID):
		if controlID == 5:
			self.load_show_id = -1
			self.close()
		else:
			self.pos    = self.name_list.getSelectedPosition()
			self.playid = stored_episodes[self.pos]

			# notify the monitor that an onDeck show is being played
			WINDOW.setProperty("%s.%s" % ('LazyTV', 'daemon_message'),'showid_'.join(str(stored_showids[self.pos])))

			self.resume = WINDOW.getProperty("%s.%s.Resume" % ('LazyTV', self.pos))
			self.play_show(int(self.playid), self.resume)
			self.close()

	def play_show(self, epid, resume):
		xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "episodeid": %d }, "options":{ "resume": true }  }, "id": 1 }' % (epid))


def get_TVshows():
	#get the most recent info on inProgress TV shows, cross-check it with what is currently stored
	query          = '{"jsonrpc": "2.0","method": "VideoLibrary.GetTVShows","params": {"filter": {"field": "playcount", "operator": "is", "value": "0" },"properties": ["lastplayed"], "sort": {"order": "descending", "method": "lastplayed"} },"id": "1" }'
	nepl_retrieved = xbmc.executeJSONRPC(query)
	nepl_retrieved = unicode(nepl_retrieved, 'utf-8', errors='ignore')
	nepl_retrieved = json.loads(nepl_retrieved)

	if 'result' in nepl_retrieved and 'tvshows' in nepl_retrieved["result"] and nepl_retrieved['result']['tvshows']:
			nepl_retrieved = nepl_retrieved['result']['tvshows']
	else:
		nepl_retrieved = {}
	nepl_from_service = WINDOW.getProperty("LazyTV.nepl")
	nepl_stored = [int(x) for x in nepl_from_service.replace("[","").replace("]","").replace(" ","").split(",")]
	nepl        = [[day_conv(x['lastplayed']) if x['lastplayed'] else 0, x['tvshowid']] for x in nepl_retrieved if x['tvshowid'] in nepl_stored]
	return nepl


def process_stored(sel_pl):

	global stored_showids 		# will hold the showids for the playlist or window, this should be in the order of last watched
	global stored_lw			# will hold the last_watched stat for each showID (same order as stored_showids)
	global stored_episodes		# will hold the episode IDs for the playlist (same order as stored_showids)
	nepl = get_TVshows()

	if sel_pl == 'null':
		new_show_list = []
		for x in nepl:
			new_show_list.append(x[1])
		selected_pl = new_show_list
	else:
		selected_pl = convert_pl_to_showlist(sel_pl)

	stored_episodes = []
	stored_showids  = [x[1] for x in nepl]

	if selected_pl != 'null':
		stored_showids  = [x[1] for x in nepl if x[1] in selected_pl]
		stored_lw       = [x[0] for x in nepl if x[1] in selected_pl]
	else:
		stored_showids  = [x[1] for x in nepl]
		stored_lw       = [x[0] for x in nepl]

	stored_episodes  = [WINDOW.getProperty("%s.%s.EpisodeID"  % ('LazyTV', x)) for x in stored_showids]



def convert_pl_to_showlist(selected_pl):
	# derive filtered_showids from smart playlist
	filename = os.path.split(selected_pl)[1]
	clean_path = 'special://profile/playlists/video/' + filename

	#retrieve the shows in the supplied playlist, save their ids to a list
	plf['params']['directory'] = clean_path
	playlist_contents = json_query(plf, True)

	if 'files' not in playlist_contents:
		log('files not in playlist contents')
	else:
		if not playlist_contents['files']:
			log('playlist contents empty')
		else:
			for x in playlist_contents['files']:
				filtered_showids = [x['id'] for x in playlist_contents['files'] if x['type'] == 'tvshow']
				log(filtered_showids, 'showids in playlist')
				if not filtered_showids:
					log('no filtered shows')

	#returns the list of all and filtered shows and episodes
	return filtered_showids


def random_playlist(selected_pl):
	#get the showids and such from the playlist
	process_stored(selected_pl)

	#clear the existing playlist
	json_query(clear_playlist, False)

	added_ep_dict   = {}
	abandoned_shows = []
	count           = 0

	while count < length and len(abandoned_shows) != len(stored_episodes): 		#while the list isnt filled, and all shows arent abandoned
		multi = False

		R = random.randint(0,len(stored_episodes) - 1)	#get random number

		curr_showid = stored_showids[R]

		if curr_showid in added_ep_dict.keys():
			if multipleshows == 'true':		#check added_ep list if multiples allowed
				multi = True
				tmp_episode_id, tmp_details = next_show_engine(showid=curr_showid,Season=added_ep_dict[curr_showid][0],Episode=added_ep_dict[curr_showid][1])
				if tmp_episode_id == 'null':
					abandoned_shows.append(curr_showid)
					continue
			else:
				abandoned_shows.append(curr_showid)
				continue
		else:
			tmp_episode_id = stored_episodes[R]

		if premieres == 'false':
			if WINDOW.getProperty("%s.%s.EpisodeNo" % ('LazyTV',curr_showid)) == 's01e01':	#if desired, ignore s01e01
				abandoned_shows.append(curr_showid)
				continue

		#add episode to playlist
		add_this_ep['params']['item']['episodeid'] = int(tmp_episode_id)
		json_query(add_this_ep, False)

		#add episode to added episode dictionary
		if multi == False:
			added_ep_dict[curr_showid] = [WINDOW.getProperty("%s.%s.Season" % ('LazyTV', curr_showid)), WINDOW.getProperty("%s.%s.Episode" % ('LazyTV', curr_showid))]
		else:
			added_ep_dict[curr_showid] = [tmp_details[0],tmp_details[1]]

		count += 1

	if notify == 'true':
		WINDOW.setProperty("%s.playlist_running"	% ('LazyTV'), 'true')
		notification = True
	else:
		notification = False


	xbmc.Player().play(xbmc.PlayList(1))



def create_next_episode_list(selected_pl):
	#creates a list of next episodes for all shows or a filtered subset and adds them to a playlist

	process_stored(selected_pl)
	log('window called')
	list_window = xGUI("DialogSelect.xml", scriptPath, 'Default')
	list_window.doModal()
	del list_window


def main_entry():

	if populate_by == 'true':
		if select_pl == '0':
			selected_pl = playlist_selection_window()
		else:
			#get setting for default_playlist
			if not default_playlist:
				selected_pl = 'null'
			else:
				selected_pl = default_playlist
	else:
		selected_pl = 'null'
	if primary_function == '2':
		#assume this is selection
		choice = dialog.yesno('LazyTV', lang(32158),'',lang(32159), lang(32160),lang(32161))
		if choice == 1:
			random_playlist(selected_pl)
		elif choice == 0:
			create_next_episode_list(selected_pl)
		else:
			pass
	elif primary_function == '1':
		#assume this is random play
		random_playlist(selected_pl)
	else:
		#just build screen list
		create_next_episode_list(selected_pl)


if __name__ == "__main__":
	try:
		service_running = WINDOW.getProperty('LazyTV_service_running')
	except:
		service_running
	if service_running == 'true':
		log('entered LazyTV')
		main_entry()
		log('exited LazyTV')
	else:
		gracefail("LazyTV Service not running. Please enable service and try again.")

''' NOT MUCH INTEREST IN THE SKIN SERVICING ASPECT OF THE ADDON, COMMENTING OUT
try:
	params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
except:
	params = {}
episodeid = params.get( "episodeid", "" )		# will only occur when an item is requested to be played
request   = params.get( "request", "" )			# will only occur when a skin requests a plugin directory
limit     = params.get( "limit", "" )			# will only occur when a skin requests a plugin directory

if episodeid:		# play item
	xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "episodeid": %d }, "options":{ "resume": true }  }, "id": 1 }' % int(episodeid))

elif request:		# generate plugin directory
	skin_servicing(int(sys.argv[1]), request, limit)

else:				# ADDON REQUEST'''



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#@@@@@@@@@@
#@@@@@@@@@@ add notification and next show prompt to service
#@@@@@@@@@@
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

'''def skin_servicing(handle, request = 'lastwatched', limit = 10):

	NOT MUCH INTEREST IN THE SKIN SERVICING ASPECT OF THE ADDON, COMMENTING OU

	#request = lastwatched or random
	#limit = integer up to len(nepl)

	properties = ["Art(thumb)",
	"Art(tvshow.banner)",
	"Art(tvshow.characterart)",
	"Art(tvshow.clearart)",
	"Art(tvshow.clearlogo)",
	"Art(tvshow.fanart)",
	"Art(tvshow.landscape)",
	"Art(tvshow.poster)",
	"AudioChannels",
	"AudioCodec",
	"CountEps",
	"CountonDeckEps",
	"CountUnwatchedEps",
	"CountWatchedEps",
	"DBID",
	"EpisodeID",
	"EpisodeNo",
	"File",
	"Path",
	"PercentPlayed",
	"Play",
	"Rating",
	"Resume",
	"VideoAspect",
	"VideoCodec",
	"VideoResolution",
	"Watched"]


	infos = {
	"Title":"Title",
	"Episode":"Episode",
	"Season":"Season",
	"Premiered":"Premiered",
	"Plot":"Plot",
	"Duration":"Runtime",
	"TVshowTitle":"TVshowTitle"}

	nepl = get_TVshows()

	position_list = range(len(nepl))
	if request == 'random':
		random.shuffle(position_list)

	count = 0
	for x in position_list:
		if count < limit:
			liz = xbmcgui.ListItem(self.WINDOW.getProperty("%s.%s.%s"%('LazyTV',x[1],'Title')))
			for prop in properties:
				if prop == "Art(thumb)":
					liz.setThumbnailImage(WINDOW.getProperty("%s.%s.%s"%('LazyTV',x[1],prop)))
				else:
					liz.setProperty( type="Video", infoLabels=	{ prop: WINDOW.getProperty("%s.%s.%s"%('LazyTV',x[1],prop)) } )

			for info in infos.keys():
				liz.setInfo( type="Video", infoLabels=	{ info: WINDOW.getProperty("%s.%s.%s"%('LazyTV',x[1],infos[info])) } )

			liz.setIconImage('DefaultTVShows.png')


			xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=item['file'], listitem=liz, isFolder=False )
			count += 1

	xbmcplugin.endOfDirectory( handle=int(sys.argv[1]) )'''
