import streamlink
import obspython as obs
import threading

globSettings = None

def script_update(settings):
	global globSettings
	globSettings = settings

def script_load(settings):
	global globSettings
	globSettings = settings

def script_properties():
	props = obs.obs_properties_create()
	obs.obs_properties_add_text(props, "url", "Stream URL", obs.OBS_TEXT_DEFAULT)

	p = obs.obs_properties_add_list(props, "source", "Media Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_id(source)
			if source_id == "ffmpeg_source" or source_id == "vlc_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(p, name, name)

	obs.source_list_release(sources)
	
	r = obs.obs_properties_add_list(props, "res", "Preferred Resolution", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_list_add_string(r, "best", "best")
	obs.obs_property_list_add_string(r, "1080p", "1080p")
	obs.obs_property_list_add_string(r, "720p", "720p")
	obs.obs_property_list_add_string(r, "480p", "480p")
	obs.obs_property_list_add_string(r, "360p", "360p")
	obs.obs_property_list_add_string(r, "160p", "160p")
	obs.obs_property_list_add_string(r, "worst", "worst")

	obs.obs_properties_add_button(props, "set", "Open Stream in Media Source", open_source)

	return props

def open_source(*args):
	print(args)
	t = threading.Thread(target=change_input)
	t.start()

def change_input():
	global globSettings
	url = obs.obs_data_get_string(globSettings, "url")
	source = obs.obs_data_get_string(globSettings, "source")
	qual = obs.obs_data_get_string(globSettings, "res")
	if url != None and source != None:
		sourceObj = obs.obs_get_source_by_name(source)
		try:
			streamUrl = ""
			stream = streamlink.streams(url)
			
			if qual in stream:
				streamUrl = stream[qual].url
			elif qual + "60" in stream:
				streamUrl = stream[qual + "60"].url
			elif qual + "_alt" in stream:
				streamUrl = stream[qual + "_alt"].url
			elif qual + "60_alt" in stream:
				streamUrl = stream[qual + "60_alt"].url
			elif "best" in stream:
				streamUrl = stream["best"].url
			
			if streamUrl != "" and sourceObj != None:
				source_id = obs.obs_source_get_id(sourceObj)
				settings = obs.obs_data_create()
				if source_id == "ffmpeg_source":
					obs.obs_data_set_string(settings, "input", streamUrl)
					obs.obs_data_set_bool(settings, "is_local_file", False)
					obs.obs_source_update(sourceObj, settings)
				else:
					array = obs.obs_data_array_create()
					data = obs.obs_data_create()
					obs.obs_data_set_string(data, "name", streamUrl)
					obs.obs_data_set_string(data, "value", streamUrl)
					obs.obs_data_array_push_back(array, data)
					obs.obs_data_release(data)
					obs.obs_data_set_array(settings, "playlist", array)
					obs.obs_source_update(sourceObj, settings)
					obs.obs_data_array_release(array)
				
				obs.obs_data_release(settings)
		except streamlink.StreamlinkError:
			pass
		obs.obs_source_release(sourceObj)