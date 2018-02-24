obs           = obslua
source_name   = ""
twentyfour    = false
seconds       = true
prefix        = ""
suffix        = ""
last_text     = ""
activated     = false

function timer_callback()
	local text = (prefix ~= ""	and prefix .. " " or "") .. os.date((twentyfour and "%H:" or "%I:") .. "%M" .. (seconds and ":%S" or "") .. (twentyfour and "" or "%p"), os.time()) .. (suffix ~= "" and " " .. suffix or "")
	if text ~= nil and text ~= last_text then
		local source = obs.obs_get_source_by_name(source_name)
		if source ~= nil then
			local settings = obs.obs_data_create()
			obs.obs_data_set_string(settings, "text", text)
			obs.obs_source_update(source, settings)
			obs.obs_data_release(settings)
			obs.obs_source_release(source)
		end
	end
	last_text = text
end

function activate(activating)
	if activating then
		timer_callback()
		obs.timer_add(timer_callback, 32)
	else
		obs.timer_remove(timer_callback)
	end
end

-- Called when a source is activated/deactivated
function activate_signal(cd, activating)
	local source = obs.calldata_source(cd, "source")
	if source ~= nil then
		local name = obs.obs_source_get_name(source)
		if (name == source_name) then
			activate(activating)
		end
	end
end

function source_activated(cd)
	activate_signal(cd, true)
end

function source_deactivated(cd)
	activate_signal(cd, false)
end

function reset(pressed)
	if not pressed then
		return
	end

	activate(false)
	local source = obs.obs_get_source_by_name(source_name)
	if source ~= nil then
		local active = obs.obs_source_active(source)
		obs.obs_source_release(source)
		activate(active)
	end
end

function reset_button_clicked(props, p)
	reset(true)
	return false
end

----------------------------------------------------------

-- A function named script_properties defines the properties that the user
-- can change for the entire script module itself
function script_properties()
	local props = obs.obs_properties_create()
	obs.obs_properties_add_bool(props, "twentyfour", "24 Hour Time")
	obs.obs_properties_add_bool(props, "seconds", "Display Seconds")
	obs.obs_properties_add_text(props, "prefix", "Prefix", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_text(props, "suffix", "Suffix", obs.OBS_TEXT_DEFAULT)
	local p = obs.obs_properties_add_list(props, "source", "Text Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	local sources = obs.obs_enum_sources()
	if sources ~= nil then
		for _, source in ipairs(sources) do
			source_id = obs.obs_source_get_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source" then
				local name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(p, name, name)
			end
		end
	end
	obs.source_list_release(sources)
	return props
end

-- A function named script_description returns the description shown to
-- the user
function script_description()
	return "Sets a text source to show current time.\n\nMade by VodBox\n\nBased on Countdown Script by Jim"
end

-- A function named script_update will be called when settings are changed
function script_update(settings)
	activate(false)

	twentyfour = obs.obs_data_get_bool(settings, "twentyfour")
	seconds = obs.obs_data_get_bool(settings, "seconds")
	prefix = obs.obs_data_get_string(settings, "prefix")
	suffix = obs.obs_data_get_string(settings, "suffix")
	source_name = obs.obs_data_get_string(settings, "source")

	reset(true)
end

-- A function named script_defaults will be called to set the default settings
function script_defaults(settings)
	obs.obs_data_set_default_bool(settings, "twentyfour", false)
	obs.obs_data_set_default_bool(settings, "seconds", true)
end

-- a function named script_load will be called on startup
function script_load(settings)
	local sh = obs.obs_get_signal_handler()
	obs.signal_handler_connect(sh, "source_activate", source_activated)
	obs.signal_handler_connect(sh, "source_deactivate", source_deactivated)
end
