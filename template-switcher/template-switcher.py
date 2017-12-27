import obspython as obs
import math
import json
import os
import time
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

templateLists = []
activeList = None
active = None
clicked = False
globSettings = None

initial = []
destination = []
animTime = math.inf
stopTime = 10000
animScene = None

def easeInOutQuad(t, b, c, d):
	t /= d/2
	if t < 1:
		return c/2*t*t + b
	t-=1
	return -c/2 * (t*(t-2) - 1) + b

def tick_callback(tick):
	global globSettings
	global animTime
	global stopTime
	global initial
	global destination
	global animScene
	
	if animTime < stopTime:
		animTime += tick
		animTime = min(animTime, stopTime)
		scaleFactor = easeInOutQuad(animTime / stopTime, 0, 1, 1)
		result = []
		if obs.obs_source_get_name(animScene) in obs.obs_frontend_get_scene_names():
			items = obs.obs_scene_enum_items(obs.obs_scene_from_source(animScene))
			for i in range(len(initial)):
				pos = obs.vec2()
				pos.x = scaleFactor*(destination[i]["pos"][0] - initial[i]["pos"][0]) + initial[i]["pos"][0]
				pos.y = scaleFactor*(destination[i]["pos"][1] - initial[i]["pos"][1]) + initial[i]["pos"][1]
				rot = scaleFactor*(destination[i]["rot"] - initial[i]["rot"]) + initial[i]["rot"]
				scale = obs.vec2()
				scale.x = scaleFactor*(destination[i]["scale"][0] - initial[i]["scale"][0]) + initial[i]["scale"][0]
				scale.y = scaleFactor*(destination[i]["scale"][1] - initial[i]["scale"][1]) + initial[i]["scale"][1]
				alignment = destination[i]["alignment"]
				bounds = obs.vec2()
				bounds.x = scaleFactor*(destination[i]["bounds"][0] - initial[i]["bounds"][0]) + initial[i]["bounds"][0]
				bounds.y = scaleFactor*(destination[i]["bounds"][1] - initial[i]["bounds"][1]) + initial[i]["bounds"][1]
				boundsType = destination[i]["boundsType"]
				boundsAlignment = destination[i]["boundsAlignment"]
				crop = obs.obs_sceneitem_crop()
				crop.left = math.floor(scaleFactor*(destination[i]["crop"][0] - initial[i]["crop"][0]) + initial[i]["crop"][0])
				crop.right = math.floor(scaleFactor*(destination[i]["crop"][1] - initial[i]["crop"][1]) + initial[i]["crop"][1])
				crop.top = math.floor(scaleFactor*(destination[i]["crop"][2] - initial[i]["crop"][2]) + initial[i]["crop"][2])
				crop.bottom = math.floor(scaleFactor*(destination[i]["crop"][3] - initial[i]["crop"][3]) + initial[i]["crop"][3])
				obs.obs_sceneitem_set_pos(items[i], pos)
				obs.obs_sceneitem_set_rot(items[i], rot)
				obs.obs_sceneitem_set_scale(items[i], scale)
				obs.obs_sceneitem_set_alignment(items[i], alignment)
				obs.obs_sceneitem_set_bounds(items[i], bounds)
				obs.obs_sceneitem_set_bounds_type(items[i], boundsType)
				obs.obs_sceneitem_set_bounds_alignment(items[i], boundsAlignment)
				obs.obs_sceneitem_set_crop(items[i], crop)
		if animTime == stopTime:
			obs.obs_source_release(animScene)

def start_animation(info):
	global initial
	global destination
	global animTime
	global stopTime
	global globSettings
	global animScene
	
	print("anim")
	
	animTime = 0
	stopTime = obs.obs_data_get_int(globSettings, "duration")/1000
	print(stopTime)
	
	f = open(info,'r')
	destination = json.loads(f.read())
	f.close()
	
	animScene = obs.obs_frontend_get_current_scene()
	items = obs.obs_scene_enum_items(obs.obs_scene_from_source(animScene))
	initial = getTransformationList(items)
	
# ------------------------------------------------------------

# A function named script_properties defines the properties that the user can
# change for the entire script module itself
def script_properties():
	global templateLists
	global activeList
	global globSettings
	
	props = obs.obs_properties_create()
	obs.obs_properties_add_int(props, "duration", "Transition Time (ms)", 0, 100000, 100)

	p = obs.obs_properties_add_list(props, "scene", "Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	activeList = obs.obs_properties_add_list(props, "active", "Active Template", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	scenes = obs.obs_frontend_get_scene_names()
	if scenes is not None:
		for scene in scenes:
			if not scene.startswith("_"):
				templateLists.append(obs.obs_properties_add_editable_list(props, "template" + scene, "Templates (" + scene + ")", obs.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS, "JSON file (*.json)", ""))
				obs.obs_property_list_add_string(p, scene, scene)
			
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	obs.obs_source_release(currentScene)
	
	items = obs.obs_data_get_array(globSettings, "template" + sceneName)
	for num in range(obs.obs_data_array_count(items)):
		item = obs.obs_data_array_item(items, num)
		value = obs.obs_data_get_string(item, "value")
		obs.obs_property_list_add_string(activeList, value, value)
	
	obs.obs_properties_add_button(props, "save", "Save Current Layout as Template", save)

	return props

# a function name script_description returns the description shown to the user
def script_description():
	return "Allows for smooth switching between user made templates, within a scene\n\nMade by Dillon (VodBox)"

# A function named script_update will be called when settings are changed
def script_update(settings):
	global data
	global globSettings
	global active
	global clicked
	
	globSettings = settings
	
	newActive = obs.obs_data_get_string(settings, "active")
	if active != None and newActive != active:
		start_animation(newActive)
	
	print("active:" + active if active != None else "")
	print("newActive:" + newActive)
	active = newActive
#	if clicked:
#		clicked = False
#		array = obs.obs_data_get_array(settings, "template")
#		array2 = obs.obs_data_get_array(settings, "active")
#		arrayItem = obs.obs_data_create()
#		obs.obs_data_set_string(arrayItem, "value", "Test")
#		obs.obs_data_array_push_back(array, arrayItem);
#		obs.obs_data_release(arrayItem)
#		obs.obs_data_set_array(settings, "template", array);
#		obs.obs_data_array_release(array);

# A function named script_defaults will be called to set the default settings
def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "duration", 2)
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	obs.obs_data_set_string(settings, "scene", sceneName)
	obs.obs_source_release(currentScene)

# A function named script_save will be called when the script is saved
#
# NOTE: This function is usually used for saving extra data (such as in this
# case, a hotkey's save data).  Settings set via the properties are saved
# automatically.
def script_save(settings):
	print("Test")

# A function named script_load will be called on startup
def script_load(settings):
	global globSettings
	globSettings = settings
	obs.obs_add_tick_callback(tick_callback)

def save(*args):
	global clicked
	
	clicked = True
	
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	items = obs.obs_scene_enum_items(obs.obs_scene_from_source(currentScene))
	transformations = getTransformationList(items)
	loc = filedialog.asksaveasfilename(filetypes=[("JSON", "*.json")], title="Save Template File", initialfile=sceneName + ".json")
	f = open(loc,'w')
	f.write(json.dumps(transformations))
	f.close()
	obs.obs_source_release(currentScene)
	return True
	
def getTransformationList(sceneitems):
	transformations = []
	for sceneitem in sceneitems:
		pos = obs.vec2()
		obs.obs_sceneitem_get_pos(sceneitem, pos)
		rot = obs.obs_sceneitem_get_rot(sceneitem)
		scale = obs.vec2()
		obs.obs_sceneitem_get_scale(sceneitem, scale)
		alignment = obs.obs_sceneitem_get_alignment(sceneitem)
		bounds = obs.vec2()
		obs.obs_sceneitem_get_bounds(sceneitem, bounds)
		boundsType = obs.obs_sceneitem_get_bounds_type(sceneitem)
		boundsAlignment = obs.obs_sceneitem_get_bounds_alignment(sceneitem)
		crop = obs.obs_sceneitem_crop()
		obs.obs_sceneitem_get_crop(sceneitem, crop)
		transformations.append({"pos": [pos.x, pos.y], "rot": rot, "scale": [scale.x, scale.y], "alignment": alignment, "bounds": [bounds.x, bounds.y], "boundsType": boundsType, "boundsAlignment": boundsAlignment, "crop": [crop.left, crop.right, crop.top, crop.bottom]})
	return transformations
