import obspython as obs
import math
import json
import os
import sys
import io
import time
import subprocess
import pexpect
import tkinter as tk
import threading
from tkinter import *
from tkinter import filedialog

class App(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self.start()

	def callback(self):
		self.root.withdraw()

	def show(self):
		self.root.update()
		self.root.deiconify()

	def run(self):
		self.root = tk.Tk()
		self.root.title("Template Switcher")
		self.visible = False
		self.visToggled = False
		self.root.withdraw()
		self.quitted = False
		self.root.protocol("WM_DELETE_WINDOW", self.callback)

		self.quitting = False

		self.scene = StringVar()
		self.scene.set("Scene")
		self.scene.trace("w", self.sceneUpdate)

		self.scenes = ("Scene")

		#self.root.minsize(width=400, height=300)
		self.root.resizable(width=False, height=False)

		row = 0

		durLabel = Label(self.root, text="Transition Time (ms)")
		durLabel.grid(row=row, column=0)

		self.duration = StringVar()
		self.duration.set(str(200))
		self.durEntry = Entry(self.root, textvariable=self.duration)
		self.durEntry.grid(row=row,column=1, columnspan=2)
		self.duration.trace("w", self.durUpdate)

		row += 1

		self.selection = tk.OptionMenu(self.root, self.scene, self.scenes)
		self.selection.grid(row=row, columnspan=3, sticky=N+E+S+W)

		row += 1

		self.list = Listbox(self.root, selectmode=SINGLE)

		self.list.grid(row=row, column=0, rowspan=2,
				   columnspan=2, sticky=N+E+S+W)

		self.list.insert('end', 'test')

		add = Button(self.root, text="Add", command=self.add)
		add.grid(row=row, column=2, sticky=N+E+S+W)

		row += 1

		remove = Button(self.root, text="Remove", command=self.remove)
		remove.grid(row=row, column=2, sticky=N+E+S+W)

		row += 1

		save = Button(self.root, text="Save Current Layout as Template", command=self.save)
		save.grid(row=row, column=0, columnspan=3, sticky=N+E+S+W)

		row += 1

		switch = Button(self.root, text="Switch to Selected", command=self.switch)
		switch.grid(row=row, column=0, columnspan=3, sticky=N+E+S+W)

		self.root.after(16, self.loop)
		self.root.mainloop()

	def loop(self):
		if self.quitting == False:
			if self.visToggled:
				self.visToggled = False
				if self.visible:
					self.root.deiconify()
				else:
					self.root.withdraw()
			self.root.after(16, self.loop)
		else:
			self.root.destroy()
			self.quitted = True

	def quit(self):
		self.quitting = True

	def add(self):
		global globSettings
		loc = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="Open Template File")
		templates = obs.obs_data_get_array(globSettings, "templates" + self.scene.get())
		if templates == None:
			template = obs.obs_data_array_create()
			obs.obs_data_set_array(globSettings, "templates" + self.scene.get(), template)
		new = obs.obs_data_create()
		length = obs.obs_data_array_count(templates) + 1
		obs.obs_data_set_string(new, "id", str(length))
		obs.obs_data_set_string(new, "name", os.path.basename(loc))
		obs.obs_data_set_string(new, "loc", loc)
		obs.obs_data_array_push_back(templates, new)
		obs.obs_data_release(new)
		obs.obs_data_array_release(templates)
		self.list.insert('end', str(length) + ". " + os.path.basename(loc))

	def remove(self):
		global globSettings
		selection = self.list.curselection()
		if selection != "":
			templates = obs.obs_data_get_array(globSettings, "templates" + self.scene.get())
			obs.obs_data_array_erase(templates, selection[0])
			length = obs.obs_data_array_count(templates)
			for i in range(selection[0], length):
				item = obs.obs_data_array_item(templates, i)
				obs.obs_data_set_string(item, "id", str(i+1))
				obs.obs_data_release(item)
			obs.obs_data_array_release(templates)
		self.update()


	def save(self):
		currentScene = obs.obs_frontend_get_current_scene()
		sceneName = obs.obs_source_get_name(currentScene)
		sceneObject = obs.obs_scene_from_source(currentScene)
		items = obs.obs_scene_enum_items(sceneObject)
		transformations = getTransformationList(items)
		loc = filedialog.asksaveasfilename(filetypes=[("JSON", "*.json")], defaultextension=".json", title="Save Template File", initialfile=sceneName + ".json")
		f = open(loc,'w')
		f.write(json.dumps(transformations))
		f.close()
		obs.obs_scene_release(sceneObject)
		obs.obs_source_release(currentScene)

	def switch(self):
		global globSettings
		selection = self.list.curselection()
		if selection != "":
			templates = obs.obs_data_get_array(globSettings, "templates" + self.scene.get())
			item = obs.obs_data_array_item(templates, selection[0])
			loc = obs.obs_data_get_string(item, "loc")
			obs.obs_data_release(item)
			obs.obs_data_array_release(templates)
			start_animation(loc)

	def update(self):
		global globSettings

		self.selection['menu'].delete(0, 'end')
		for choice in self.scenes:
			self.selection['menu'].add_command(label=choice, command=tk._setit(self.scene, choice))
		stored = obs.obs_data_get_string(globSettings, "scene")
		if stored in self.scenes:
			self.scene.set(stored)
		else:
			self.scene.set(self.scenes[0])

		self.list.delete(0, self.list.index('end'))

		self.duration.set(obs.obs_data_get_int(globSettings, "duration"))

		templates = obs.obs_data_get_array(globSettings, "templates" + self.scene.get())
		if templates == None:
			template = obs.obs_data_array_create()
			obs.obs_data_set_array(globSettings, "templates" + self.scene.get(), template)
		length = obs.obs_data_array_count(templates)
		for i in range(length):
			item = obs.obs_data_array_item(templates, i)
			self.list.insert('end', obs.obs_data_get_string(item, "id") + ". " + obs.obs_data_get_string(item, "name"))
			obs.obs_data_release(item)

		obs.obs_data_array_release(templates)


	def sceneUpdate(self, *args):
		global globSettings
		obs.obs_data_set_string(globSettings, "scene", self.scene.get())
		self.update()

	def durUpdate(self, *args):
		global globSettings
		if self.duration.get().isdigit():
			obs.obs_data_set_int(globSettings, "duration", int(self.duration.get()))
		else:
			self.duration.set(str(obs.obs_data_get_int(globSettings, "duration")))


app = App()

globSettings = None

animationRunning = False
animationInfo = {
	'initial': [],
	'destination': [],
	'animTime': math.inf,
	'stopTime': 10000,
	'animScene': None
}

def easeInOutQuad(t, b, c, d):
	t /= d/2
	if t < 1:
		return c/2*t*t + b
	t-=1
	return -c/2 * (t*(t-2) - 1) + b

def script_tick(tick):
	global globSettings
	global animationInfo
	global animationRunning
	global app
	global currentScene

	if animationRunning:
		animationInfo["animTime"] += tick
		animationInfo["animTime"] = min(animationInfo["animTime"], animationInfo["stopTime"])
		scaleFactor = easeInOutQuad(animationInfo["animTime"] / animationInfo["stopTime"], 0, 1, 1)

		animScene = animationInfo["animScene"]
		initial = animationInfo["initial"]
		destination = animationInfo["destination"]

		result = []
		sceneObject = obs.obs_scene_from_source(animScene)
		if obs.obs_source_get_name(animScene) in obs.obs_frontend_get_scene_names():
			items = obs.obs_scene_enum_items(sceneObject)
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
			obs.sceneitem_list_release(items)

		#obs.obs_scene_release(sceneObject)

		if animationInfo["animTime"] == animationInfo["stopTime"]:
			obs.obs_source_release(animScene)
			animationInfo["animScene"] = None
			animationRunning = False

def start_animation(info):
	global animationInfo
	global globSettings
	global animationRunning

	animationInfo["animTime"] = 0
	animationInfo["stopTime"] = obs.obs_data_get_int(globSettings, "duration")/1000

	f = open(info,'r')
	animationInfo["destination"] = json.loads(f.read())
	f.close()

	animationInfo["animScene"] = obs.obs_get_source_by_name(obs.obs_data_get_string(globSettings, "scene"))

	sceneObject = obs.obs_scene_from_source(animationInfo["animScene"])
	items = obs.obs_scene_enum_items(sceneObject)
	animationInfo["initial"] = getTransformationList(items)

	animationRunning = True

	#obs.obs_scene_release(sceneObject)

# ------------------------------------------------------------

# A function named script_properties defines the properties that the user can
# change for the entire script module itself
def script_properties():
	global globSettings

	props = obs.obs_properties_create()
	obs.obs_properties_add_button(props, "open", "Open GUI", open_gui)
	return props

def open_gui(*args):
	global app
	app.show()
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	obs.obs_source_release(currentScene)
	scenes = obs.obs_frontend_get_scene_names()
	result = []
	if scenes is not None:
		for scene in scenes:
			result.append(scene)
	app.scenes = tuple(result)
	app.scene.set(sceneName)
	app.update()

# a function name script_description returns the description shown to the user
def script_description():
	return "Allows for smooth switching between user made templates, within a scene\n\nMade by Dillon (VodBox)"

# A function named script_update will be called when settings are changed
def script_update(settings):
	global globSettings

	globSettings = settings

# A function named script_defaults will be called to set the default settings
def script_defaults(settings):
	obs.obs_data_set_default_int(globSettings, "duration", 200)
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	obs.obs_data_set_string(settings, "scene", sceneName)
	obs.obs_source_release(currentScene)

# A function named script_load will be called on startup
def script_load(settings):
	global globSettings
	globSettings = settings

def script_unload():
	global app
	global globSettings
	global animationInfo

	if animationInfo["animScene"] != None:
		obs.obs_source_release(animationInfo["animScene"])

	app.quit()
	while app.quitted == False:
		pass

	obs.obs_data_release(globSettings)

	return

def save(*args):
	currentScene = obs.obs_frontend_get_current_scene()
	sceneName = obs.obs_source_get_name(currentScene)
	sceneObject = obs.obs_scene_from_source(currentScene)
	items = obs.obs_scene_enum_items(sceneObject)
	transformations = getTransformationList(items)
	loc = filedialog.asksaveasfilename(filetypes=[("JSON", "*.json")], title="Save Template File", initialfile=sceneName + ".json")
	f = open(loc,'w')
	f.write(json.dumps(transformations))
	f.close()
	#obs.obs_scene_release(sceneObject)
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
		obs.obs_sceneitem_release(sceneitem)
	return transformations
