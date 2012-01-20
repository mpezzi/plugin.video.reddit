import sys, urllib, urllib2, re, os, string
from xml.dom.minidom import parseString

# ERRORCODES:
# 0 = Ignore
# 200 = Ok
# 303 = Returned and error
# 500 = Uncaught error

class YouTubeCore(object):
	__plugin__ = 'Reddit.YouTubeCore'
	__dbg__ = True
	
	PREFERRED = True
	
	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
	
		
	def __init__(self):
		return None;
	  
	def _fetchPage(self, link=''):
		if self.__dbg__:
			print self.__plugin__ + " fetching page : " + link
	    
		request = urllib2.Request(link)
		request.add_header('User-Agent', self.USERAGENT)
	  
		try:
			con = urllib2.urlopen(request)
			result = con.read()
			new_url = con.geturl()
			con.close()
	    
	    # Return result if it isn't age restricted
			if ( result.find("verify-actions") == -1 and result.find("verify-age-actions") == -1):
				return ( result, 200 )
			else:
	      # TODO: handle login
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage. Need to login"
				return ( "", 500 )
	    
		except urllib2.HTTPError, e:
			err = str(e)
			if self.__dbg__:
				print self.__plugin__ + " _fetchPage HTTPError : " + err
	      
	    # 400 (Bad request)
			if ( err.find("400") > -1 ):
				return ( err, 303 )
	    # 401 (Not authorized)
			elif ( err.find("401") > -1 ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage 401 Not Authorized"
				return ( None, 303)
      # 403 (Forbidden)
			elif ( err.find("403") > -1 ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage got empty results back"
				return ( None, 303)
      # 501 (Not implemented) - A 501 response code indicates that you have tried to execute an unsupported operation.
			elif ( err.find("501") > -1):
				return ( err, 303 )

		except:
			if self.__dbg__:
				print self.__plugin__ + ' _fetchPage ERROR: %s::%s (%d) - %s' % (self.__class__.__name__, sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( "", 500 )

	def _convertFlashVars(self, html):
		obj = { "PLAYER_CONFIG": { "args": {} } }
		temp = html.split("&")
		for item in temp:
			it = item.split("=")
			obj["PLAYER_CONFIG"]["args"][it[0]] = urllib.unquote_plus(it[1])
		return obj

	def getVideoUrlMap(self, pl_obj, video = {}):
		if self.__dbg__:
			print self.__plugin__ + " getVideoUrlMap: " 
		links = {}
		video["url_map"] = "true"

		html = ""
		if pl_obj["args"].has_key("fmt_stream_map"):
			html = pl_obj["args"]["fmt_stream_map"]

		if len(html) == 0 and pl_obj["args"].has_key("url_encoded_fmt_stream_map"):
			html = urllib.unquote(pl_obj["args"]["url_encoded_fmt_stream_map"])

		if len(html) == 0 and pl_obj["args"].has_key("fmt_url_map"):
			html = pl_obj["args"]["fmt_url_map"]	

		html = urllib.unquote_plus(html)

		if pl_obj["args"].has_key("liveplayback_module"):
			video["live_play"] = "true"

		fmt_url_map = [html]
		if html.find("|") > -1:
			fmt_url_map = html.split('|')
		elif html.find(",url=") > -1:
			fmt_url_map = html.split(',url=')
		elif html.find("&conn=") > -1:
			video["stream_map"] = "true"
			fmt_url_map = html.split('&conn=')

		print self.__plugin__ + " getVideoUrlMap Searching for fmt_url_map 2: "  + repr(fmt_url_map)

		if len(fmt_url_map) > 0:
			for index, fmt_url in enumerate(fmt_url_map):
				if fmt_url.find("&url") > -1:
					fmt_url = fmt_url.split("&url")
					fmt_url_map += [fmt_url[1]]
					fmt_url = fmt_url[0]

				if (len(fmt_url) > 7 and fmt_url.find("&") > 7):
					quality = "5"
					final_url = fmt_url.replace(" ", "%20").replace("url=", "")

					if (final_url.rfind(';') > 0):
						final_url = final_url[:final_url.rfind(';')]

					if (final_url.rfind(',') > final_url.rfind('&id=')): 
						final_url = final_url[:final_url.rfind(',')]
					elif (final_url.rfind(',') > final_url.rfind('/id/') and final_url.rfind('/id/') > 0):
						final_url = final_url[:final_url.rfind('/')]

					if (final_url.rfind('itag=') > 0):
						quality = final_url[final_url.rfind('itag=') + 5:]
						if quality.find('&') > -1:
							quality = quality[:quality.find('&')]
						if quality.find(',') > -1:
							quality = quality[:quality.find(',')]
					elif (final_url.rfind('/itag/') > 0):
						quality = final_url[final_url.rfind('/itag/') + 6:]

					if final_url.find("&type") > 0:
						final_url = final_url[:final_url.find("&type")]
					if self.PREFERRED == "true":
						pos = final_url.find("://")
						fpos = final_url.find("fallback_host")
						if pos > -1 and fpos > -1:
							host = final_url[pos + 3:]
							if host.find("/") > -1:
								host = host[:host.find("/")]
							fmt_fallback = final_url[fpos + 14:]
							if fmt_fallback.find("&") > -1:
								fmt_fallback = fmt_fallback[:fmt_fallback.find("&")]
							final_url = final_url.replace(host, fmt_fallback)
							final_url = final_url.replace("fallback_host=" + fmt_fallback, "fallback_host=" + host)

					if final_url.find("rtmp") > -1 and index > 0:
						if pl_obj.has_key("url") or True:
							final_url += " swfurl=" + pl_obj["url"] + " swfvfy=1"

						playpath = False
						if final_url.find("stream=") > -1:
							playpath = final_url[final_url.find("stream=")+7:]
							if playpath.find("&") > -1:
								playpath = playpath[:playpath.find("&")]
						else:
							playpath = fmt_url_map[index - 1]

						if playpath:
							if pl_obj["args"].has_key("ptk") and pl_obj["args"].has_key("ptchn"):
								final_url += " playpath=" + playpath + "?ptchn=" + pl_obj["args"]["ptchn"] + "&ptk=" + pl_obj["args"]["ptk"] 

					links[int(quality)] = final_url.replace('\/','/')

		#if self.__dbg__:
		#	print self.__plugin__ + " getVideoUrlMap done " + repr(links)
		return links

	def selectVideoQuality(self, links):
		link = links.get
		video_url = ""
		
		if self.__dbg__:
			print self.__plugin__ + "selectedVideoQuality : "
			
		# SD videos are default, but go for the highest res
		if (link(35)):
			video_url = link(35)
		elif (link(34)):
			video_url = link(34)
		elif (link(59)): #<-- 480 for rtmpe
			video_url = link(59)
		elif (link(78)): #<-- seems to be around 400 for rtmpe
			video_url = link(78)
		elif (link(18)):
			video_url = link(18)
		elif (link(5)):
			video_url = link(5)
		elif (link(22)): # 720p
			video_url = link(22)
		elif (link(37)): # 1080p
			video_url = link(37)
		
		return video_url

	def video_id(self, value):
		# TODO: make this more fool proof
		value = value.replace('&amp;', '&')
		value = value.split('?')[1]
		value = value.split('=')[1]
		value = value.split('&')[0]
		return value