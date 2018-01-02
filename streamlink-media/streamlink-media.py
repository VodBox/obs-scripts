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
			name = obs.obs_source_get_name(source)
			obs.obs_property_list_add_string(p, name, name)

	obs.source_list_release(sources)

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
	if url != None and source != None:
		sourceObj = obs.obs_get_source_by_name(source)
		try:
			streamUrl = streamlink.streams(url)["best"].url
			if sourceObj != None:
				settings = obs.obs_data_create()
				obs.obs_data_set_string(settings, "input", streamUrl)
				obs.obs_data_set_bool(settings, "is_local_file", False)
				obs.obs_source_update(sourceObj, settings)
				obs.obs_data_release(settings)
		except streamlink.StreamlinkError:
			pass
		obs.obs_source_release(sourceObj)

def script_unload():
	global globSettings
	obs.obs_data_release(globSettings)