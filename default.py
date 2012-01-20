"""
Plugin for streaming video from Reddit
"""

import sys, re, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib, urllib2
import simplejson as json
import YouTubeCore

YouTubeCore = YouTubeCore.YouTubeCore()

__plugin__ = "Reddit"
__credits__ = "Alex Pezzi alexpezzi@gmail.com"
__version__ = "1.0"

# Reddit Configuration.
REDDIT_FEED_URL = 'http://www.reddit.com/r/'
REDDIT_FEED_SUBREDDITS = ['videos', 'funny', 'tech', 'gaming', 'AWW', 'WTF', 'music', 'listen', 'TIL', 'PBS', 'TED', 'politics', 'atheism', 'sports', 'documentaries']
REDDIT_FEED_LIMIT = 100

# Youtube Playback
YOUTUBE_EMBED_STREAM = 'http://www.youtube.com/get_video_info?video_id=%s'

# Addon Modes
MODE_ROOT = 0
MODE_SUBREDDIT = 10
MODE_PLAY_VIDEO = 20

# Parameter keys
PARAMETER_KEY_MODE = 'mode'
PARAMETER_KEY_URL = 'url'
PARAMETER_KEY_SUBREDDIT = 'subreddit'

# Utility functions
def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]

  return param

def XBMC_PATH(path, filename):
  translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
  translatedpath = re.sub(' ', '\ ', translatedpath)
  return translatedpath

def ADD_DIRECTORY_ITEM(name, parameters = {}, isFolder = True, icon = 'DefaultVideo.png'):
  li = xbmcgui.ListItem( name, iconImage = "DefaultFolder.png", thumbnailImage = icon )
  li.setInfo( type = 'Video', infoLabels = { 'Title': name } )
  url = sys.argv[0] + '?' + urllib.urlencode(parameters)
  return xbmcplugin.addDirectoryItem( handle = int(sys.argv[1]), url = url, listitem = li, isFolder = isFolder )

def SUBREDDIT():
  for name in REDDIT_FEED_SUBREDDITS:
    ADD_DIRECTORY_ITEM(name, parameters = { PARAMETER_KEY_MODE: MODE_SUBREDDIT, PARAMETER_KEY_SUBREDDIT: name }, isFolder = True)
  xbmcplugin.endOfDirectory( handle = handle, succeeded = True )

# Get Subreddit channel.
def SUBREDDIT_ITEMS(subreddit):
  data = json.load(urllib.urlopen(REDDIT_FEED_URL + subreddit + '/.json?limit=' + REDDIT_FEED_LIMIT)) 

  videos = []
  for item in data['data']['children']:
    if item['data']['domain'] == 'youtube.com':
      url = item['data']['url']
      ADD_DIRECTORY_ITEM(item['data']['title'], parameters = { PARAMETER_KEY_MODE: MODE_PLAY_VIDEO, PARAMETER_KEY_URL: item['data']['url'] }, isFolder = False, icon = item['data']['thumbnail'])
  xbmcplugin.endOfDirectory( handle = handle, succeeded = True )

def PLAY(url):
  player_object = {}
  video = {}
  links = []

  videoid = YouTubeCore.video_id(url)
  (result, status) = YouTubeCore._fetchPage(link = YOUTUBE_EMBED_STREAM % videoid)

  if result.find('status=fail') > -1:
    return

  if status == 200:
    player_object = YouTubeCore._convertFlashVars(result)

  # Find playback URI
  if player_object.has_key('PLAYER_CONFIG'):
    if player_object['PLAYER_CONFIG'].has_key('args'):
      if player_object['PLAYER_CONFIG']['args'].has_key('ttsurl'):
        video['ttsurl'] = player_object['PLAYER_CONFIG']['args'].has_key('ttsurl')

      links = YouTubeCore.getVideoUrlMap(player_object["PLAYER_CONFIG"], video)
      video_url = YouTubeCore.selectVideoQuality(links)
      xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(video_url)


# Addons
addon = xbmcaddon.Addon(id='plugin.video.reddit')
addonpath = addon.getAddonInfo('path')

# Plugin Handle
handle = int(sys.argv[1])

# Parameter values
params = get_params()
url = None
subreddit = None
mode = MODE_ROOT

try:
  url = urllib.unquote_plus(params["url"])
except:
  pass
try:
  subreddit = urllib.unquote_plus(params["subreddit"])
except:
  pass
try:
  mode = int(params["mode"])
except:
  pass

print '###########################################################'
print mode
print '###########################################################'

if mode == MODE_ROOT:
  SUBREDDIT()
elif mode == MODE_SUBREDDIT:
  SUBREDDIT_ITEMS(subreddit)
elif mode == MODE_PLAY_VIDEO:
  PLAY(url)
