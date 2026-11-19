extends Node
## Ravenmark prototype: the home coast (Keelvik, Lauvdal, Sule Ness), Copperhavn across the water, the snowy
## north, the eastern ocean and the eastern continent; interiors, a cave, NPCs, shops, a companion, a ferry,
## a museum, telescopes and the dragon.
##
## main.gd owns the world: maps (outdoor regions linked at their edges, rooms, the cave), doors, things you can
## touch, NPC placement, seasons, the clock and tide, lights and the cave darkness, travel cutscenes. story.gd owns game state and runs the dialogue
## scripts in data/content.json; ui.gd draws the HUD and menus.
##
## The world is 320x180 game pixels, drawn by a SubViewport at the window's resolution with the camera zoomed in
## by a whole number (game_scale), so every art pixel is a crisp block but things can move in 1/game_scale steps:
## scrolling and walking are smooth instead of jumping a whole block at a time. Inside the SubViewport, layer 1
## recolours every palette colour for the time of day (daynight.gdshader + art/daynight_lut.png), layer 2 is
## cave darkness, layer 3 holds light halos. It is shown through the tilt-shift shader; the HUD sits on top.

const TILE := 16
const VIEW := Vector2i(320, 180)
const UI_RATIO := 0.8                # the HUD is drawn a little smaller than the game (0.8 x its pixel scale)
const SEASONS := ["spring", "summer", "autumn", "winter"]
const WINTER := 3
const DAYS_PER_SEASON := 2           # seasons change at midnight every 2 days (Tab / 1-4 switch instantly)
## Day/night schedule (24 h): night 22-04 (6 h), dawn 04-07 (3 h), day 07-19 (12 h), dusk 19-22 (3 h).
const PHASE_START := {"dawn": 4.0, "day": 7.0, "dusk": 19.0, "night": 22.0}
const DIRS := {"up": Vector2i.UP, "down": Vector2i.DOWN, "left": Vector2i.LEFT, "right": Vector2i.RIGHT}
const START := Vector2i(55, 22)
const CAM_SMOOTH := 7.0              # camera smoothing when walking or standing
const CAM_LAG := 40.0                # the camera never trails the hero by more than this (px): it catches up faster
                                     # on the whale, so fast rides never leave the screen (180 px tall)

var story
var ui
var C: Dictionary
var meta: Dictionary
var maps := {}
var map_id := "overworld"
var M: Dictionary
var map_kind := "outdoor"
var terrain: Array = []
var map_w := 0
var map_h := 0
var blocked := {}                    # static: walls, trees, furniture
var counters := {}                   # tiles you can talk across (shop counters, market stalls)
var warps := {}                      # tile -> warp (doors, stairs, cave mouths)
var ents: Array = []                 # dynamic things on this map: NPCs, chests, signs, pickups, obstacles, ...
var dyn := {}                        # tile -> entity
var season := 1
var seasons_running := true
var hour := 9.0
var day := 0
var hours_per_second := 1.0 / 30.0   # one in-game hour every 30 s: a full day takes 12 minutes
var time_running := true
var saving_enabled := true
var cutscene := false
var loading := false
var zone_title := ""
var _tick := -1
var _npc_clock := 0.0
var _lantern_note := false
var _faded: Array = []               # sprites that are see-through, or fading back
var _fade_want := {}                 # sprites that should be see-through right now
var _fade_clock := 0.0

var viewport: SubViewport
var screen: TextureRect              # the game picture: the 320 x 180 world at a whole-number scale
var game_scale := 4                  # window pixels per game pixel (the biggest that fits the window)
var ui_scale := 3
var scale_override := 0              # debug window: 0 = fit the window
var ui_scale_override := 0
var cam_smooth := CAM_SMOOTH         # (the debug window changes these live)
var cam_lag := CAM_LAG
var debug
var world: Node2D
var ground: Sprite2D
var lowtide: Sprite2D
var ysort: Node2D
var player
var companion
var camera: Camera2D
var daynight_mat: ShaderMaterial
var dn_rect: ColorRect
var dark_rect: ColorRect
var dark_mat: ShaderMaterial
var glow_layer: CanvasLayer
var add_mat: CanvasItemMaterial
var map_nodes: Array = []
var lit_sprites: Array = []
var halos: Array = []
var windows: Array = []
var crystals: Array = []
var erne: Sprite2D
var hanging: Sprite2D
var dragon
var _last_day := -1
var _tex := {}


func _ready() -> void:
	meta = _load_json("res://game/data/sprites.json")
	story = load("res://game/scripts/story.gd").new()
	add_child(story)
	ui = load("res://game/scripts/ui.gd").new()
	add_child(ui)
	story.main = self
	story.ui = ui
	story.setup(self)
	C = story.C
	_build_view()
	ui.build(self)
	_build_world()
	get_viewport().size_changed.connect(relayout)
	_fit_window()
	relayout()
	debug = load("res://game/scripts/debug.gd").new()
	add_child(debug)
	debug.setup(self)
	var test_mode := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--autotest="):
			test_mode = a.split("=")[1]
	if test_mode != "":
		saving_enabled = false
		new_game()
		var tester = load("res://game/scripts/autotest.gd").new()
		add_child(tester)
		tester.run(self, test_mode)
	elif "--newgame" in OS.get_cmdline_user_args() or not load_game():
		new_game()


func _load_json(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func tex(path: String) -> Texture2D:
	if not _tex.has(path):
		_tex[path] = load(path)
	return _tex[path]


func busy() -> bool:
	return ui.busy() or cutscene


# ------------------------------------------------------------------ new game / save / load
func new_game() -> void:
	story.new_game()
	season = 1
	hour = 9.0
	day = 0
	player.wear_pouch = true
	player.wear_stick = false
	player.surfing = false
	player.force_mount("otter")
	ui.set_coins(story.coins)
	set_season(1, false)
	load_map("overworld", START, Vector2i.DOWN)
	on_companion_changed()
	ui.toast(story.text("intro"), 6.0)


func save_game() -> void:
	if not saving_enabled:
		return
	var d := {"story": story.to_save(), "map": map_id, "x": player.tile.x, "y": player.tile.y,
		"facing": [player.facing.x, player.facing.y], "surfing": player.surfing, "mount": player.mount_kind,
		"season": season, "hour": hour, "day": day, "pouch": player.wear_pouch, "stick": player.wear_stick}
	var f := FileAccess.open(story.SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(d))


func load_game() -> bool:
	if not FileAccess.file_exists(story.SAVE_PATH):
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(story.SAVE_PATH))
	if not (d is Dictionary) or not d.has("story"):
		return false
	story.from_save(d["story"])
	_last_day = int(d["day"])
	season = int(d["season"])
	hour = float(d["hour"])
	day = int(d["day"])
	player.wear_pouch = bool(d["pouch"])
	player.wear_stick = bool(d["stick"])
	player.force_mount(String(d["mount"]))
	ui.set_coins(story.coins)
	set_season(season, false)
	load_map(String(d["map"]), Vector2i(int(d["x"]), int(d["y"])), Vector2i(int(d["facing"][0]), int(d["facing"][1])),
		bool(d["surfing"]))
	on_companion_changed()
	ui.toast("WELCOME BACK. PRESS H FOR HELP, F9 FOR A NEW GAME.", 4.0)
	return true


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and player:
		save_game()


func ask_new_game() -> void:
	var i: int = await ui.choose(story.text("new_game"), ["YES", "NO"])
	if i == 0:
		if FileAccess.file_exists(story.SAVE_PATH):
			DirAccess.remove_absolute(story.SAVE_PATH)
		new_game()


# ------------------------------------------------------------------ view: pixel-perfect world + tilt-shift
func _build_view() -> void:
	viewport = SubViewport.new()
	viewport.size = VIEW
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	viewport.snap_2d_transforms_to_pixel = true
	viewport.snap_2d_vertices_to_pixel = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	screen = TextureRect.new()
	screen.texture = viewport.get_texture()
	screen.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	screen.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	screen.stretch_mode = TextureRect.STRETCH_SCALE
	screen.size = Vector2(VIEW * 4)
	screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://game/shaders/tiltshift.gdshader")
	screen.material = mat
	add_child(screen)


func _fit_window() -> void:
	## on start: the biggest whole-number scale whose window fits the screen (5x = 1600 x 900 on a 1080p screen)
	if DisplayServer.get_name() == "headless" or DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_WINDOWED:
		return
	var area := DisplayServer.screen_get_usable_rect()
	var s := clampi(int(minf(area.size.x * 0.94 / VIEW.x, area.size.y * 0.94 / VIEW.y)), 2, 12)
	var size := VIEW * s
	DisplayServer.window_set_size(size)
	DisplayServer.window_set_position(area.position + (area.size - size) / 2)


func relayout() -> void:
	## the game picture at the biggest whole-number scale that fits the window, centred; the HUD over it
	var win := get_viewport().get_visible_rect().size
	game_scale = scale_override if scale_override > 0 else maxi(1, int(minf(win.x / VIEW.x, win.y / VIEW.y)))
	var px := VIEW * game_scale
	viewport.size = px                                          # render at screen resolution ...
	camera.zoom = Vector2(game_scale, game_scale)               # ... with every game pixel a game_scale block
	dn_rect.size = Vector2(px)
	dark_rect.size = Vector2(px)
	dark_mat.set_shader_parameter("px", float(game_scale))
	(screen.material as ShaderMaterial).set_shader_parameter("px", float(game_scale))
	screen.size = Vector2(px)
	screen.position = ((win - screen.size) / 2.0).floor()
	ui_scale = ui_scale_override if ui_scale_override > 0 else maxi(1, roundi(game_scale * UI_RATIO))
	ui.layout(screen.position, screen.size, ui_scale)


func _build_world() -> void:
	world = Node2D.new()
	viewport.add_child(world)
	var bg := ColorRect.new()                                   # behind small rooms
	bg.color = Color("1E1B2C")
	bg.position = Vector2(-2000, -2000)
	bg.size = Vector2(6000, 6000)
	bg.z_index = -10
	world.add_child(bg)
	ground = Sprite2D.new()
	ground.centered = false
	ground.z_index = -2                                         # below flat things at z -1 (rugs, dug holes,
	world.add_child(ground)                                     # open hedges, shadows); at 0 it hid them
	lowtide = Sprite2D.new()
	lowtide.centered = false
	lowtide.z_index = -2
	lowtide.texture = load("res://game/art/ground/lowtide.png")
	var lt: Dictionary = meta["_lowtide"]
	lowtide.position = Vector2(float(lt["x"]), float(lt["y"]))
	world.add_child(lowtide)
	ysort = Node2D.new()
	ysort.y_sort_enabled = true
	world.add_child(ysort)
	player = load("res://game/scripts/player.gd").new()
	player.main = self
	player.process_priority = -1                                # moves before main._process aims the camera
	ysort.add_child(player)
	companion = load("res://game/scripts/companion.gd").new()
	companion.visible = false
	ysort.add_child(companion)
	camera = Camera2D.new()
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = CAM_SMOOTH
	world.add_child(camera)
	camera.make_current()
	_build_layers()


func _build_layers() -> void:
	var dn_layer := CanvasLayer.new()                           # 1: recolour for the time of day (palette LUT)
	dn_layer.layer = 1
	viewport.add_child(dn_layer)
	dn_rect = ColorRect.new()
	dn_rect.size = Vector2(VIEW)
	dn_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	daynight_mat = ShaderMaterial.new()
	daynight_mat.shader = load("res://game/shaders/daynight.gdshader")
	daynight_mat.set_shader_parameter("lut", load("res://game/art/daynight_lut.png"))
	dn_rect.material = daynight_mat
	dn_layer.add_child(dn_rect)
	var dk_layer := CanvasLayer.new()                           # 2: cave darkness
	dk_layer.layer = 2
	viewport.add_child(dk_layer)
	dark_rect = ColorRect.new()
	dark_rect.size = Vector2(VIEW)
	dark_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dark_mat = ShaderMaterial.new()
	dark_mat.shader = load("res://game/shaders/darkness.gdshader")
	dark_rect.material = dark_mat
	dark_rect.visible = false
	dk_layer.add_child(dark_rect)
	glow_layer = CanvasLayer.new()                               # 3: halos around lights, following the camera
	glow_layer.layer = 3
	glow_layer.follow_viewport_enabled = true
	viewport.add_child(glow_layer)
	add_mat = CanvasItemMaterial.new()
	add_mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD


# ------------------------------------------------------------------ maps
func load_map(id: String, t: Vector2i, facing := Vector2i.DOWN, surfing := false) -> void:
	loading = true
	_clear_map()
	map_id = id
	if not maps.has(id):
		maps[id] = _load_json("res://game/data/world.json" if id == "overworld" else "res://game/data/maps/%s.json" % id)
	M = maps[id]
	map_kind = String(M.get("kind", "outdoor"))
	terrain = M["terrain"]
	map_w = int(M["width"])
	map_h = int(M["height"])
	blocked = {}
	for b in M["blocked"]:
		blocked[Vector2i(int(b[0]), int(b[1]))] = true
	warps = {}
	for w in C["warps"]:
		if w["map"] == id:
			warps[Vector2i(int(w["x"]), int(w["y"]))] = w
	counters = {}
	for o in M["objects"]:
		_spawn(String(o["kind"]), Vector2(float(o["x"]), float(o["y"])))
		if o["kind"] == "counter4":
			var ct := Vector2i((int(o["x"]) - 8) / TILE, (int(o["y"]) - 14) / TILE)
			for dx in 4:
				counters[ct + Vector2i(dx, 0)] = true
	ground.texture = tex(ground_path())
	lowtide.visible = id == "overworld"
	var mw := map_w * TILE
	var mh := map_h * TILE
	camera.limit_left = min(0, (mw - VIEW.x) / 2)
	camera.limit_right = max(mw, mw + (VIEW.x - mw) / 2)
	camera.limit_top = min(0, (mh - VIEW.y) / 2)
	camera.limit_bottom = max(mh, mh + (VIEW.y - mh) / 2)
	_lantern_note = false
	ui.hide_toast()
	refresh_entities(true)
	player.surfing = surfing
	player.facing = facing
	player.place(t)
	if surfing:
		player.fit_mount()
	_place_companion()
	camera.position = player.position + Vector2(0, -6)
	camera.reset_smoothing()
	zone_title = ""
	loading = false
	on_player_tile(t, surfing)
	_apply_time()


func _clear_map() -> void:
	for e in ents:
		_free_node(e.get("node"))
	ents = []
	dyn = {}
	_faded = []
	_fade_want = {}
	for n in map_nodes:
		_free_node(n)
	map_nodes = []
	lit_sprites = []
	windows = []
	crystals = []
	for h in halos:
		if is_instance_valid(h):
			h.queue_free()
	halos = []


func _free_node(n) -> void:
	if n == null or not is_instance_valid(n):
		return
	for h in n.get_meta("halos", []):
		if is_instance_valid(h):
			h.queue_free()
		halos.erase(h)
	if n.has_meta("lit"):
		lit_sprites.erase(n.get_meta("lit"))
	n.queue_free()


func _alias(kind: String) -> String:
	if kind == "pen":
		return {"fox": "pen_onlyowl", "owl": "pen_onlyfox"}.get(story.companion, "pen")
	return kind


func obj_tex(kind: String) -> Texture2D:
	var m: Dictionary = meta.get(kind, {})
	if m.has("seasonal") and not bool(m["seasonal"]):
		return tex("res://game/art/objects/%s.png" % String(m.get("file", kind)))
	var s: String = SEASONS[art_season()] if is_outdoor() else "summer"
	return tex("res://game/art/objects/%s_%s.png" % [kind, s])


func _spawn(kind: String, pos: Vector2, keep := true) -> Sprite2D:
	kind = _alias(kind)
	var s := Sprite2D.new()
	var m: Dictionary = meta[kind]
	s.centered = false
	s.position = pos
	s.offset = Vector2(-float(m["ox"]), -float(m["oy"]))
	s.texture = obj_tex(kind)
	s.set_meta("kind", kind)
	if m.get("flat", false):
		s.z_index = -1
	ysort.add_child(s)
	if keep:
		map_nodes.append(s)
	_add_lights(s, kind)
	if kind == "window":
		windows.append(s)
	if kind == "crystal":
		crystals.append(s)
	return s


func _add_lights(s: Sprite2D, kind: String) -> void:
	var m: Dictionary = meta[kind]
	if not m.has("lights"):
		return
	var lit := Sprite2D.new()
	lit.centered = false
	lit.offset = s.offset
	lit.texture = tex("res://game/art/objects/%s_lit.png" % kind)
	s.add_child(lit)
	lit_sprites.append(lit)
	s.set_meta("lit", lit)
	var hs := []
	for l in m["lights"]:
		var h := Sprite2D.new()
		h.texture = tex("res://game/art/objects/halo_%s.png" % l[2])
		h.position = s.position + Vector2(float(l[0]), float(l[1]))
		h.material = add_mat
		glow_layer.add_child(h)
		halos.append(h)
		hs.append(h)
	s.set_meta("halos", hs)


func _set_kind(s: Sprite2D, kind: String) -> void:
	var m: Dictionary = meta[kind]
	s.set_meta("kind", kind)
	s.offset = Vector2(-float(m["ox"]), -float(m["oy"]))
	s.texture = obj_tex(kind)


func tile_pos(t: Vector2i) -> Vector2:
	return Vector2(t.x * TILE + 8, t.y * TILE + 14)


func _vec(a) -> Vector2i:
	return Vector2i(int(a[0]), int(a[1]))


# ------------------------------------------------------------------ dynamic things: build + refresh
func _ent(type: String, data: Dictionary, tiles: Array, node: Node2D, block := true) -> Dictionary:
	var e := {"type": type, "data": data, "tiles": tiles, "node": node, "block": block, "id": String(data.get("id", ""))}
	ents.append(e)
	return e


func _rebuild_dyn() -> void:
	dyn = {}
	for e in ents:
		for t in e["tiles"]:
			dyn[t] = e


func refresh_entities(full := false) -> void:
	## (re)builds what can change: everything on map load, otherwise only NPCs and night-market stalls
	if full:
		for e in ents:
			_free_node(e.get("node"))
		ents = []
		_build_static_ents()
	_refresh_people(full)
	_rebuild_dyn()


func _build_static_ents() -> void:
	for c in C["chests"]:
		if c["map"] != map_id:
			continue
		var t := Vector2i(int(c["x"]), int(c["y"]))
		var s := _spawn("chest_open" if story.opened.has(c["id"]) else "chest", tile_pos(t), false)
		_ent("chest", c, [t], s)
	for sg in C["signs"]:
		if sg["map"] != map_id:
			continue
		var t := Vector2i(int(sg["x"]), int(sg["y"]))
		var s := _spawn(String(sg["kind"]), tile_pos(t), false)
		_ent("sign", sg, [t], s)
	for p in C["pickups"]:
		if p["map"] != map_id:
			continue
		var t := Vector2i(int(p["x"]), int(p["y"]))
		var got: bool = story.taken.has(p["id"])
		if p["kind"] == "sparkle":
			if not got:
				_ent("pickup", p, [t], _sparkle(t), false)
		else:
			_ent("pickup", p, [t], _spawn(String(p["kind"]) + ("_empty" if got else ""), tile_pos(t), false))
	for o in C["obstacles"]:
		if o["map"] != map_id:
			continue
		var t := Vector2i(int(o["x"]), int(o["y"]))
		var gone: bool = story.cleared.has(o["id"]) or (String(o["needs"]).begins_with("gate:") and story.gates.has(String(o["needs"]).substr(5)))
		if gone and o["kind"] == "hedge":
			var hs := _spawn("hedge_open", tile_pos(t), false)
			hs.z_index = -1                                 # you walk through the gap
			_ent("obstacle", o, [t], hs, false)
		elif not gone:
			_ent("obstacle", o, [t], _spawn(String(o["kind"]), tile_pos(t), false))
	for p in C["perches"]:
		if p["map"] == map_id:
			var t := Vector2i(int(p["x"]), int(p["y"]))
			_ent("perch", p, [t], _spawn("perch", tile_pos(t), false))
	for b in C["boats"]:
		if b["map"] == map_id:
			_ent("boat", b, [Vector2i(int(b["x"]), int(b["y"]))], null)
	for s in C["secrets"]:
		if s["map"] == map_id and s["type"] == "fox" and story.found.has(s["id"]):
			_dig_hole(Vector2i(int(s["x"]), int(s["y"])))
	for t in C["telescopes"]:
		if t["map"] == map_id:
			var tt := Vector2i(int(t["x"]), int(t["y"]))
			_ent("telescope", t, [tt], _spawn("telescope", tile_pos(tt), false))
	var stops: Array = C["ferry"]["stops"]
	for i in stops.size():
		var st: Dictionary = stops[i]
		if st["map"] == map_id and ferry_stop_today() == i and map_id != "crossing":
			var tiles := []
			for b in st["tiles"]:
				tiles.append(_vec(b))
			var fs := _spawn("ferry", tile_pos(Vector2i(int(st["x"]), int(st["y"]))), false)
			var fd := st.duplicate()
			fd["idx"] = i
			_ent("ferry", fd, tiles, fs)
	if map_id == C["museum"]["map"]:
		for ex in C["museum"]["exhibits"]:
			var et := Vector2i(int(ex["x"]), int(ex["y"]))
			var node: Sprite2D = null
			if story.exhibits.has(ex["item"]):
				node = Sprite2D.new()
				node.texture = ui.icon_tex(ex["item"])
				node.centered = false
				node.position = tile_pos(et) + Vector2(0, 1)
				node.offset = Vector2(-8, -29)
				node.set_meta("fixed", true)
				ysort.add_child(node)
			_ent("exhibit", ex, [et], node)


func _sparkle(t: Vector2i) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex("res://game/art/objects/sparkle.png")
	s.hframes = 3
	s.position = Vector2(t.x * TILE + 8, t.y * TILE + 10)
	s.set_meta("fixed", true)
	s.set_meta("sparkle", true)
	ysort.add_child(s)
	return s


func _dig_hole(t: Vector2i) -> void:
	var s := Sprite2D.new()
	s.texture = tex("res://game/art/objects/dig_hole.png")
	s.position = Vector2(t.x * TILE + 8, t.y * TILE + 10)
	s.z_index = -1
	s.set_meta("fixed", true)
	ysort.add_child(s)
	map_nodes.append(s)


func _on_screen(t: Vector2i) -> bool:
	var p := tile_pos(t)
	var c := camera.get_screen_center_position()
	return abs(p.x - c.x) < VIEW.x / 2.0 + 24 and abs(p.y - c.y) < VIEW.y / 2.0 + 40


func _refresh_people(full: bool) -> void:
	## NPCs and market stalls come and go with the clock and the story; off-screen only, unless the map reloads
	var want := {}
	for pair in story.npcs_on(map_id):
		want[pair[0]["id"]] = pair
	for e in ents.duplicate():
		if e["type"] != "npc":
			continue
		var id: String = e["id"]
		var stay: bool = want.has(id) and want[id][1] == e["tiles"][0]
		if not stay and (full or not _on_screen(e["tiles"][0])):
			_free_node(e["node"])
			ents.erase(e)
		elif want.has(id):
			want.erase(id)
		else:
			want.erase(id)
	for id in want.keys():
		var n: Dictionary = want[id][0]
		var t: Vector2i = want[id][1]
		if t == player.tile or (not full and _on_screen(t)):
			continue
		var s := Sprite2D.new()
		s.texture = tex("res://game/art/npcs/%s.png" % n["sprite"])
		s.hframes = 3
		s.centered = false
		s.offset = Vector2(-10, -23)
		s.position = tile_pos(t)
		s.set_meta("fixed", true)
		ysort.add_child(s)
		_ent("npc", n, [t], s)
	for i in C["timed"].size():
		var td: Dictionary = C["timed"][i]
		if td["map"] != map_id:
			continue
		var on: bool = story.cond_ok(td["when"])
		var cur = null
		for e in ents:
			if e["type"] == "stall" and e["data"] == td:
				cur = e
		var t := Vector2i(int(td["x"]), int(td["y"]))
		if on and cur == null and (full or not _on_screen(t)):
			var tiles := []
			for b in td["block"]:
				tiles.append(_vec(b))
			_ent("stall", td, tiles, _spawn(String(td["kind"]), tile_pos(t), false))
		elif not on and cur != null and (full or not _on_screen(t)):
			_free_node(cur["node"])
			ents.erase(cur)


func npc_at(t: Vector2i):
	var e = dyn.get(t)
	return e if e != null and e["type"] == "npc" else null


func _face_npc(e: Dictionary, d: Vector2i) -> void:
	var s: Sprite2D = e["node"]
	s.frame = {Vector2i.DOWN: 0, Vector2i.UP: 1, Vector2i.RIGHT: 2, Vector2i.LEFT: 2}[d]
	s.flip_h = d == Vector2i.LEFT


func emote(target: Node2D, kind: String, secs := 1.2, y := -36.0) -> void:
	var s := Sprite2D.new()
	s.texture = tex("res://game/art/hud/emote_%s.png" % kind)
	s.position = Vector2(0, y)
	s.z_index = 20
	target.add_child(s)
	var gone := func() -> void:
		if is_instance_valid(s):
			s.queue_free()
	get_tree().create_timer(secs).timeout.connect(gone)


# ------------------------------------------------------------------ seasons
func set_season(i: int, announce := true) -> void:
	season = i
	ui.set_season(SEASONS[i])
	if not is_outdoor() or not ground:
		return
	ground.texture = tex(ground_path())
	for s in map_nodes + ents.map(func(e): return e.get("node")):
		if s != null and is_instance_valid(s) and not s.has_meta("fixed") and s.has_meta("kind"):
			s.texture = obj_tex(s.get_meta("kind"))
	if player and announce:
		player.on_season_changed()


func is_winter() -> bool:
	return art_season() == WINTER


func is_outdoor() -> bool:
	return map_kind == "outdoor"


func art_season() -> int:
	## the north is always winter; the open sea is drawn once (summer)
	return int(M["season_lock"]) if M.has("season_lock") else season


func ground_path() -> String:
	if not is_outdoor():
		return "res://game/art/rooms/%s.png" % map_id
	if map_id == "overworld":
		return "res://game/art/ground/ground_%s.png" % SEASONS[art_season()]
	return "res://game/art/ground/%s_%s.png" % [map_id, SEASONS[art_season()]]


# ------------------------------------------------------------------ day / night, tide
func set_time(h: float) -> void:
	hour = fposmod(h, 24.0)
	_apply_time()
	_time_tick(true)


func phase() -> String:
	if hour >= 22.0 or hour < 4.0:
		return "night"
	if hour < 7.0:
		return "dawn"
	if hour < 19.0:
		return "day"
	return "dusk"


func light_amount() -> float:
	## how strongly windows and lamps glow: off by day, on through the night
	if hour >= 7.0 and hour < 19.0:
		return 0.0
	if hour >= 19.0:
		return smoothstep(19.5, 21.0, hour)
	if hour >= 4.0:
		return 1.0 - smoothstep(5.0, 6.75, hour)
	return 1.0


func next_phase() -> void:
	var order := ["dawn", "day", "dusk", "night"]
	set_time(PHASE_START[order[(order.find(phase()) + 1) % 4]])


func low_tide() -> bool:
	return hour >= 4.0 and hour < 7.0


func _apply_time() -> void:
	var indoor := not is_outdoor()
	daynight_mat.set_shader_parameter("time01", 0.5 if indoor else hour / 24.0)
	var la := 1.0 if indoor else light_amount()
	for s in lit_sprites:
		if is_instance_valid(s):
			s.modulate.a = la
	var t := Time.get_ticks_msec() * 0.006
	for i in halos.size():
		if is_instance_valid(halos[i]):
			halos[i].modulate.a = la * (0.9 + 0.1 * sin(t + i * 1.7))      # a gentle flicker
	var night_out := light_amount() > 0.5
	for w in windows:
		if is_instance_valid(w) and w.get_meta("kind") != ("window_night" if night_out else "window"):
			_set_kind(w, "window_night" if night_out else "window")
	if lowtide.visible:
		var a := 0.0
		if low_tide():
			a = min(clamp((hour - 4.0) / 0.25, 0.0, 1.0), clamp((7.0 - hour) / 0.25, 0.0, 1.0))
		lowtide.modulate.a = a
	ui.set_clock(hour, phase())
	_update_darkness()


func _time_tick(force := false) -> void:
	var q := int(hour * 4.0)
	if q == _tick and not force:
		return
	_tick = q
	if loading or map_nodes.is_empty() and ents.is_empty():
		return
	if day != _last_day:
		_last_day = day
		refresh_entities(true)
	else:
		refresh_entities(false)
	if map_id == "overworld" and not low_tide() and not cutscene:      # the tide comes back in
		var t: Vector2i = player.tile
		if tile_at(t) == "l" or (t.x >= 77 and t.x <= 83 and t.y >= 33 and t.y <= 37):
			_tide_rescue()


func _tide_rescue() -> void:
	player.surfing = false
	player.place(Vector2i(76, 35))
	_place_companion()
	await ui.say("", "THE TIDE COMES RUSHING IN. YOU WADE BACK TO THE BEACH, SOAKED TO THE KNEES.")


# ------------------------------------------------------------------ cave darkness
func is_dark() -> bool:
	return bool(M.get("dark", false))


func _in_lit_zone(t: Vector2i) -> bool:
	for z in M.get("lit_zones", []):
		if Vector2(t - Vector2i(int(z[0]), int(z[1]))).length() <= float(z[2]):
			return true
	return false


func dark_blocks(t: Vector2i) -> bool:
	return is_dark() and not story.has("lantern") and not _in_lit_zone(t)


func _update_darkness() -> void:
	dark_rect.visible = is_dark()
	if not is_dark():
		return
	var xf := viewport.get_canvas_transform().scaled(Vector2.ONE / float(game_scale))   # world -> game pixels on screen
	var pts := PackedVector3Array()
	if story.has("lantern"):
		var p: Vector2 = xf * (player.position + Vector2(0, -8))
		pts.append(Vector3(p.x, p.y, 64.0 + 2.0 * sin(Time.get_ticks_msec() * 0.004)))
	for z in M.get("lit_zones", []):
		var p: Vector2 = xf * (tile_pos(Vector2i(int(z[0]), int(z[1]))) - Vector2(0, 6))
		pts.append(Vector3(p.x, p.y, float(z[2]) * TILE + 10.0))
	for c in crystals:
		if pts.size() < 16:
			var p: Vector2 = xf * (c.position - Vector2(0, 6))
			pts.append(Vector3(p.x, p.y, 26.0))
	while pts.size() < 16:
		pts.append(Vector3(-999, -999, 1))
	dark_mat.set_shader_parameter("lights", pts)
	dark_mat.set_shader_parameter("count", 16)


# ------------------------------------------------------------------ world queries (used by the player)
func tile_at(t: Vector2i) -> String:
	if t.x < 0 or t.y < 0 or t.x >= map_w or t.y >= map_h:
		return "X"
	return String(terrain[t.y])[t.x]


func can_walk(t: Vector2i) -> bool:
	if blocked.has(t):
		return false
	var e = dyn.get(t)
	if e != null and e["block"]:
		return false
	var c := tile_at(t)
	if not is_outdoor():
		return c == "."
	if c in [",", ":", ".", "w", "f", "t"]:
		return true
	if c in ["=", "\""] and is_winter():
		return true                                       # frozen river and reeds
	if c == "l" and low_tide():
		return true                                       # the sandbar at low tide
	return false


func water_kind(t: Vector2i) -> String:
	if not is_outdoor() or blocked.has(t) or dyn.has(t):
		return ""
	match tile_at(t):
		"O":
			return "ocean"
		"=":
			return "" if is_winter() else "fresh"
		"~":
			return "sea"
		"!":
			return "cold"
	return ""


func is_ledge(t: Vector2i) -> bool:
	return is_outdoor() and tile_at(t) == "v"


func try_warp(t: Vector2i, d: Vector2i) -> bool:
	## doors, stairs and cave mouths: stepping onto them in their direction takes you through
	if not warps.has(t):
		return false
	var w: Dictionary = warps[t]
	if DIRS[w["dir"]] != d:
		return false
	if (w.has("needs") and not story.has(w["needs"])) or not w.has("to"):
		ui.say("", w["locked"])
		return true
	if w.has("flag"):
		story.flags[w["flag"]] = true
	warp_to(String(w["to"]), Vector2i(int(w["tx"]), int(w["ty"])), DIRS[w["face"]])
	return true


func warp_to(id: String, t: Vector2i, facing: Vector2i, surfing := false) -> void:
	cutscene = true
	await ui.fade(1.0)
	load_map(id, t, facing, surfing)
	await ui.fade(0.0)
	cutscene = false
	save_game()


# ------------------------------------------------------------------ interacting (Space / Z / Enter)
func interact(front: Vector2i) -> bool:
	var e = dyn.get(front)
	var beyond = npc_at(front + player.facing)
	if beyond != null and (counters.has(front) or (e != null and e["type"] == "stall")):
		e = beyond                                         # talk across a counter or a market stall
	if e == null:
		return false
	match String(e["type"]):
		"npc":
			_talk(e)
		"chest":
			_open_chest(e)
		"sign":
			_read(e)
		"pickup":
			_pick_up(e)
		"obstacle":
			_use_on(e)
		"perch":
			_perch(e)
		"boat":
			_boat(e)
		"ferry":
			_ferry(e)
		"exhibit":
			_plaque(e)
		"telescope":
			_telescope(e)
		_:
			return false
	return true


func _talk(e: Dictionary) -> void:
	_face_npc(e, -player.facing)
	await story.talk(e["data"])
	if not story.pending_warp.is_empty():
		var w: Array = story.pending_warp
		story.pending_warp = []
		await warp_to(String(w[0]), Vector2i(int(w[1]), int(w[2])), DIRS[w[3]])
	refresh_entities(false)
	save_game()


func _open_chest(e: Dictionary) -> void:
	if story.opened.has(e["id"]):
		await ui.say("", "THE CHEST IS EMPTY.")
		return
	_set_kind(e["node"], "chest_open")
	await story.open_chest(e["data"])


func _read(e: Dictionary) -> void:
	for line in e["data"]["lines"]:
		await ui.say("", line)


func _pick_up(e: Dictionary) -> void:
	var p: Dictionary = e["data"]
	if story.taken.has(p["id"]):
		await ui.say("", "NOTHING ELSE HERE.")
		return
	story.taken[p["id"]] = true
	story.give(p["item"])
	if p["kind"] == "sparkle":
		_free_node(e["node"])
		ents.erase(e)
		_rebuild_dyn()
	else:
		_set_kind(e["node"], String(p["kind"]) + "_empty")
	await ui.say("", "FOUND %s!" % story.item_name(p["item"]), p["item"])
	await ui.say("", story.C["items"][p["item"]]["desc"], p["item"])
	save_game()


func _use_on(e: Dictionary) -> void:
	var o: Dictionary = e["data"]
	var needs: String = o["needs"]
	var kind: String = o["kind"]
	if story.C["items"].has(needs) and story.has(needs):
		story.cleared[o["id"]] = true
		_poof(e["node"].position)
		_free_node(e["node"])
		ents.erase(e)
		_rebuild_dyn()
		await ui.say("", story.text(kind + "_cut"), needs)
		save_game()
	else:
		await ui.say("", story.text(kind))


func _poof(pos: Vector2) -> void:
	for i in 6:
		var s := Sprite2D.new()
		s.texture = tex("res://game/art/objects/sparkle.png")
		s.hframes = 3
		s.frame = 1
		s.position = pos + Vector2(0, -8)
		s.z_index = 15
		world.add_child(s)
		var tw := s.create_tween()
		var dir := Vector2.from_angle(i * TAU / 6.0) * 14.0
		tw.tween_property(s, "position", s.position + dir, 0.35)
		tw.parallel().tween_property(s, "modulate:a", 0.0, 0.35)
		tw.finished.connect(s.queue_free)


func _boat(e: Dictionary) -> void:
	var b: Dictionary = e["data"]
	var i: int = await ui.choose(b["ask"], ["YES", "NO"])
	if i == 0:
		await warp_to(String(b["to"]), Vector2i(int(b["tx"]), int(b["ty"])), DIRS[b["face"]])


# ------------------------------------------------------------------ the great erne (Bird Bell)
func _perch(e: Dictionary) -> void:
	if not story.has("bird_bell"):
		await ui.say("", story.text("perch"))
		return
	await ui.say("", story.text("perch_ring"), "bird_bell")
	await fly(e["data"])


func fly(p: Dictionary) -> void:
	cutscene = true
	var land := _vec(p["land"])
	var dir: Vector2i = DIRS[p["face"]]
	erne = Sprite2D.new()
	erne.texture = tex("res://game/art/companions/erne_carry.png")
	erne.hframes = 4
	erne.z_index = 40
	var sh := Sprite2D.new()
	sh.texture = tex("res://game/art/companions/erne_shadow.png")
	sh.modulate.a = 0.45
	sh.z_index = -1
	world.add_child(sh)
	world.add_child(erne)
	var from: Vector2 = player.position + Vector2(0, -170)
	erne.position = from
	erne.rotation = PI                                       # swooping down the screen towards you
	sh.position = from + Vector2(0, 40)
	var t1 := create_tween()
	t1.tween_property(erne, "position", player.position + Vector2(0, -10), 0.9).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	t1.parallel().tween_property(sh, "position", player.position + Vector2(0, 10), 0.9)
	await t1.finished
	player.visible = false
	companion.visible = false
	hanging = Sprite2D.new()                                 # you, hanging from its talons
	hanging.texture = tex("res://game/art/hero/hero_body.png")
	hanging.hframes = 4
	hanging.vframes = 3
	hanging.frame = 0
	hanging.centered = false
	hanging.offset = Vector2(-10, -2)
	hanging.z_index = 39
	world.add_child(hanging)
	erne.rotation = 0.0 if dir == Vector2i.UP else PI
	var to := tile_pos(land) + Vector2(0, -24)
	var t2 := create_tween()
	t2.tween_property(erne, "position", to, 1.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	t2.parallel().tween_property(sh, "position", to + Vector2(0, 26), 1.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await t2.finished
	hanging.queue_free()
	hanging = null
	player.facing = dir
	player.place(land)
	player.visible = true
	_place_companion()
	var away := to + Vector2(dir) * 220.0 + Vector2(0, -60)
	var t3 := create_tween()
	t3.tween_property(erne, "position", away, 0.9).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	t3.parallel().tween_property(sh, "modulate:a", 0.0, 0.6)
	await t3.finished
	erne.queue_free()
	sh.queue_free()
	erne = null
	cutscene = false
	save_game()


# ------------------------------------------------------------------ companion: following, fox nose, owl eyes
func on_companion_changed() -> void:
	for s in map_nodes:
		if is_instance_valid(s) and String(s.get_meta("kind", "")).begins_with("pen"):
			_set_kind(s, _alias("pen"))
	if story.companion == "":
		companion.visible = false
		return
	if companion.kind != story.companion or companion.spr == null:
		companion.setup(story.companion)
	_place_companion()


func _place_companion() -> void:
	if story.companion == "":
		companion.visible = false
		return
	var behind: Vector2i = player.tile - player.facing
	companion.place(behind if can_walk(behind) or story.companion == "owl" else player.tile, player.facing)
	update_companion_visibility()


func update_companion_visibility() -> void:
	companion.visible = story.companion != "" and story.companion_visible and player.visible \
		and not (story.companion == "fox" and player.surfing)


func on_player_step(from: Vector2i, to: Vector2i, dur: float) -> void:
	if story.companion != "":
		if story.companion == "fox" and (player.surfing or not can_walk(from)):
			companion.place(to if not player.surfing else from, player.facing)
		else:
			companion.follow_to(from, dur)
		update_companion_visibility()


func toggle_companion() -> void:
	if story.companion == "":
		ui.toast("NO COMPANION YET. HEDDA IN LAUVDAL LOOKS AFTER ORPHANED ANIMALS.")
		return
	story.companion_visible = not story.companion_visible
	update_companion_visibility()
	var who := "FOX" if story.companion == "fox" else "OWL"
	ui.toast(("YOUR %s FOLLOWS YOU AGAIN." % who) if story.companion_visible else
		("YOUR %s IS HIDING. IT STILL HELPS YOU." % who))
	save_game()


func _check_secrets(t: Vector2i) -> void:
	if story.companion == "":
		return
	for s in C["secrets"]:
		if s["map"] != map_id or story.found.has(s["id"]) or s["type"] != story.companion:
			continue
		var st := Vector2i(int(s["x"]), int(s["y"]))
		if max(abs(st.x - t.x), abs(st.y - t.y)) <= 2:
			if s["type"] == "fox":
				_fox_dig(s, st)
			else:
				_owl_reveal(s)
			return


func _fox_dig(s: Dictionary, st: Vector2i) -> void:
	story.found[s["id"]] = true
	cutscene = true
	var shown: bool = companion.visible
	if shown:
		companion.walk_to(st, 0.3)
		await get_tree().create_timer(0.35).timeout
	emote(companion if shown else player, "sniff", 1.0, -24.0 if shown else -36.0)
	await get_tree().create_timer(0.9).timeout
	_dig_hole(st)
	cutscene = false
	await ui.say("", story.text("fox_sniff"))
	if s.has("coins"):
		story.add_coins(int(s["coins"]))
		await ui.say("", "YOUR FOX DUG UP A POUCH WITH %d COINS!" % int(s["coins"]), "coins")
	if s.has("item"):
		story.give(s["item"])
		await ui.say("", "YOUR FOX DUG UP %s!" % story.item_name(s["item"]), s["item"])
		await ui.say("", story.C["items"][s["item"]]["desc"], s["item"])
	_place_companion()
	save_game()


func _owl_reveal(s: Dictionary) -> void:
	story.found[s["id"]] = true
	story.cleared[s["obstacle"]] = true
	for e in ents:
		if e["type"] == "obstacle" and e["id"] == s["obstacle"]:
			_set_kind(e["node"], "hedge_open")
			e["node"].z_index = -1
			e["block"] = false
	_rebuild_dyn()
	emote(companion if companion.visible else player, "music", 1.2, -30.0 if companion.visible else -36.0)
	await ui.say("", story.text("owl_spot"))
	save_game()


# ------------------------------------------------------------------ arriving on a tile
func zone_for(t: Vector2i, surfing: bool) -> Array:
	var sz: Dictionary = C["sea_zones"].get(map_id, {})
	if surfing and sz.has(tile_at(t)):
		return sz[tile_at(t)]
	for z in C["zones"]:
		if z[0] == map_id and t.x >= int(z[1]) and t.y >= int(z[2]) and t.x <= int(z[3]) and t.y <= int(z[4]):
			var sub: String = z[6]
			var mk: Dictionary = C["market"]
			if z[5] == mk["zone"] and story.in_time(mk["time"]):
				sub = mk["sub"]
			return [z[5], sub]
	return []


func on_player_tile(t: Vector2i, surfing: bool) -> void:
	if loading:
		return
	var z := zone_for(t, surfing)
	if not z.is_empty() and z[0] != zone_title:
		zone_title = z[0]
		ui.banner(z[0], z[1])
	if not z.is_empty():
		story.visited[z[0]] = true
	_check_landings(t)
	if is_dark() and story.has("lantern") and not _lantern_note:
		_lantern_note = true
		ui.toast(story.text("lantern_on"))
	var e = dyn.get(t)
	if e != null and e["type"] == "pickup" and not story.taken.has(e["id"]):
		_pick_up(e)
		return
	_check_secrets(t)


# ------------------------------------------------------------------ regions: stepping off a map edge
func _map_data(id: String) -> Dictionary:
	if not maps.has(id):
		maps[id] = _load_json("res://game/data/world.json" if id == "overworld" else "res://game/data/maps/%s.json" % id)
	return maps[id]


func try_edge(t: Vector2i, d: Vector2i) -> bool:
	## off the edge of a region: into the next region where the edge is linked, otherwise nowhere
	if t.x >= 0 and t.y >= 0 and t.x < map_w and t.y < map_h:
		return false
	var side := "top" if t.y < 0 else ("bottom" if t.y >= map_h else ("left" if t.x < 0 else "right"))
	for e in M.get("edges", []):
		var c: int = t.x if side in ["top", "bottom"] else t.y
		if e["side"] != side or c < int(e["a"]) or c > int(e["b"]):
			continue
		var to: String = e["to"]
		var T := _map_data(to)
		var sh := int(e["shift"])
		var nt := Vector2i(0, t.y + sh)
		match side:
			"top":
				nt = Vector2i(t.x + sh, int(T["height"]) - 1)
			"bottom":
				nt = Vector2i(t.x + sh, 0)
			"left":
				nt = Vector2i(int(T["width"]) - 1, t.y + sh)
		var ch: String = String(T["terrain"][nt.y])[nt.x]
		if player.surfing:
			if not ch in ["~", "=", "!", "O"]:
				return true
			if ch == "!" and not story.has("seal_flute"):
				ui.toast(story.text("otter_cold"))
				return true
			if ch == "O" and not story.has("whale_horn"):
				ui.toast(story.text("ocean_deep"))
				return true
		elif not ch in [",", ":", ".", "w", "f"]:
			return true
		warp_to(to, nt, d, player.surfing)
		return true
	return true


# ------------------------------------------------------------------ the ferry (Keelvik <-> Copperhavn, alternate days)
func ferry_stop_today() -> int:
	## day 0, 2, 4... at Keelvik, 1, 3, 5... at Copperhavn; after a ride it stays where it went for the day
	if story.ferry_day == day:
		return story.ferry_at
	return day % 2


func _ferry(e: Dictionary) -> void:
	var f: Dictionary = C["ferry"]
	var here: int = int(e["data"]["idx"])
	var stops: Array = f["stops"]
	if not story.has(f["pass"]):
		await ui.say("", story.text("ferry_no_pass"))
		return
	if story.ferry_day == day:
		await ui.say(f["captain"], story.text("ferry_used"))
		return
	var dest := 1 - here
	var i: int = await ui.choose(story.text("ferry_ask") % stops[dest]["name"], ["YES", "NO"])
	if i == 0:
		await ferry_ride(dest)


func ferry_info() -> String:
	var stops: Array = C["ferry"]["stops"]
	var today: int = ferry_stop_today()
	return story.text("ferry_today") % [stops[today]["name"], stops[(day + 1) % 2]["name"]]


func ferry_ride(to_i: int) -> void:
	cutscene = true
	var stops: Array = C["ferry"]["stops"]
	await ui.fade(1.0)
	load_map("crossing", Vector2i(3, 6), Vector2i.RIGHT)
	player.visible = false
	companion.visible = false
	var boat := _spawn("ferry", tile_pos(Vector2i(3, 6)), false)
	var rider := Sprite2D.new()                              # you, on deck
	rider.texture = tex("res://game/art/hero/hero_body.png")
	rider.hframes = 4
	rider.vframes = 3
	rider.frame = 8
	rider.centered = false
	rider.offset = Vector2(-10, -23)
	rider.position = Vector2(10, -6)
	boat.add_child(rider)
	camera.reset_smoothing()
	await ui.fade(0.0)
	var end := tile_pos(Vector2i(40, 6))
	var tw := create_tween()
	tw.tween_property(boat, "position", end, 4.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.parallel().tween_property(player, "position", end, 4.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	var bob := func(k: float) -> void:
		rider.position.y = -6 + round(sin(k * 18.0))
	tw.parallel().tween_method(bob, 0.0, 1.0, 4.5)
	await tw.finished
	await ui.fade(1.0)
	boat.queue_free()
	story.ferry_day = day
	story.ferry_at = to_i
	var st: Dictionary = stops[to_i]
	player.visible = true
	load_map(String(st["map"]), _vec(st["land"]), DIRS[st["face"]])
	await ui.fade(0.0)
	cutscene = false
	save_game()


# ------------------------------------------------------------------ the museum
func _plaque(e: Dictionary) -> void:
	var ex: Dictionary = e["data"]
	if story.exhibits.has(ex["item"]):
		await ui.say("", "%s. %s" % [story.item_name(ex["item"]), ex["where"]], ex["item"])
	else:
		await ui.say("", "AN EMPTY PEDESTAL. THE PLAQUE READS: WANTED - " + String(ex["hint"]))


func museum_talk(n: Dictionary) -> void:
	var who: String = n["name"]
	if int(story.mem_get(story.mem_key(n))["talks"]) == 0:
		await ui.say(who, story.text("museum_intro"))
	var gave := false
	for ex in C["museum"]["exhibits"]:
		var it: String = ex["item"]
		if story.has(it) and not story.exhibits.has(it):
			var i: int = await ui.choose(story.text("museum_lend") % story.item_name(it), ["YES", "NO"])
			if i == 0:
				story.take(it)
				story.exhibits[it] = true
				gave = true
				refresh_entities(true)
				await ui.say(who, story.text("museum_thanks"), it)
	var have: int = story.exhibits.size()
	var total: int = C["museum"]["exhibits"].size()
	if have >= total:
		await ui.say(who, story.text("museum_full"))
	elif gave:
		await ui.say(who, story.text("museum_count") % [have, total])
	else:
		await ui.say(who, story.text("museum_nothing"))


# ------------------------------------------------------------------ telescopes
func _telescope(e: Dictionary) -> void:
	var t: Dictionary = e["data"]
	await ui.say("", story.text("telescope"))
	story.scopes[t["id"]] = true
	await ui.show_view(tex("res://game/art/views/%s.png" % t["view"]), t["caption"])
	save_game()


# ------------------------------------------------------------------ the dragon (Dragon Band)
func _check_landings(t: Vector2i) -> void:
	for l in C["landings"]:
		if l["map"] == map_id and not story.landings.has(l["id"]) and max(abs(int(l["x"]) - t.x), abs(int(l["y"]) - t.y)) <= 3:
			story.landings[l["id"]] = true
			if story.has("dragon_band"):
				ui.toast(story.text("landing_found"))


func hours_now() -> float:
	return day * 24.0 + hour


func dragon_menu() -> void:
	if not story.has("dragon_band") or busy():
		return
	if not is_outdoor() or map_id == "crossing":
		ui.toast(story.text("dragon_indoors"))
		return
	if story.dragon_time >= 0.0 and hours_now() - story.dragon_time < 1.0:
		var mins := int(ceil((1.0 - (hours_now() - story.dragon_time)) * 60.0))
		ui.toast(story.text("dragon_rest") % mins)
		return
	var opts := []
	for l in C["landings"]:
		var here: bool = l["map"] == map_id and max(abs(int(l["x"]) - player.tile.x), abs(int(l["y"]) - player.tile.y)) <= 4
		if story.landings.has(l["id"]) and not here:
			opts.append(l)
	if opts.is_empty():
		ui.toast(story.text("dragon_none"))
		return
	var names := []
	for l in opts:
		names.append(l["name"])
	names.append("NOT NOW")
	await ui.say("", story.text("dragon_call"), "dragon_band")
	var i: int = await ui.choose("WHERE SHALL THE DRAGON FLY?", names)
	if i < 0 or i >= opts.size():
		return
	await dragon_fly(opts[i])


func dragon_fly(l: Dictionary) -> void:
	cutscene = true
	dragon = load("res://game/scripts/dragon.gd").new()
	world.add_child(dragon)
	var p: Vector2 = player.position
	dragon.start(p + Vector2(-280, -170))
	await dragon.fly_to(p + Vector2(0, -14), 1.6, p + Vector2(-60, 60))       # swoops down to you
	player.visible = false
	companion.visible = false
	player.surfing = false
	dragon.show_rider(true)
	await dragon.fly_to(p + Vector2(220, -280), 1.3, p + Vector2(140, 30))   # and climbs away
	await ui.fade(1.0)
	var dest := Vector2i(int(l["x"]), int(l["y"]))
	load_map(String(l["map"]), dest, Vector2i.DOWN)
	player.visible = false
	companion.visible = false
	var q: Vector2 = tile_pos(dest)
	dragon.start(q + Vector2(-260, -220))
	camera.position = dragon.head.position
	camera.reset_smoothing()
	await ui.fade(0.0)
	await dragon.fly_to(q + Vector2(0, -14), 1.8, q + Vector2(-140, 40))     # circles in and lands
	dragon.show_rider(false)
	player.visible = true
	_place_companion()
	await dragon.fly_to(q + Vector2(280, -240), 1.1, q + Vector2(140, -20))
	dragon.queue_free()
	dragon = null
	camera.reset_smoothing()
	story.dragon_time = hours_now()
	cutscene = false
	save_game()


# ------------------------------------------------------------------ the world map (M): what you have discovered
func east_revealed() -> bool:
	return story.has("whale_horn") or story.visited.has("WHITBORG")


func map_px(mid: String, t: Vector2) -> Vector2:
	var r: Array = C["worldmap"]["regions"][mid]
	var T := _map_data(mid)
	return Vector2(float(r[0]) + (t.x + 0.5) * float(r[2]) / float(T["width"]),
		float(r[1]) + (t.y + 0.5) * float(r[3]) / float(T["height"]))


func map_marker() -> Vector2:
	if C["worldmap"]["regions"].has(map_id):
		return map_px(map_id, Vector2(player.tile))
	var rm: Array = C["worldmap"]["rooms"].get(map_id, ["overworld", START.x, START.y])
	return map_px(String(rm[0]), Vector2(float(rm[1]), float(rm[2])))


func map_info(px: Vector2) -> Array:
	## [name, longer text] for a point on the world map; undiscovered places have no name yet
	var regs: Dictionary = C["worldmap"]["regions"]
	var oc: Array = regs["ocean"]
	for mid in regs.keys():
		var r: Array = regs[mid]
		if px.x < float(r[0]) or px.y < float(r[1]) or px.x >= float(r[0]) + float(r[2]) or px.y >= float(r[1]) + float(r[3]):
			continue
		if (mid == "ocean" or mid == "east") and not east_revealed():
			return ["THE EASTERN OCEAN", story.text("map_ocean")]
		var T := _map_data(mid)
		var tt := Vector2i(int((px.x - float(r[0])) * float(T["width"]) / float(r[2])),
			int((px.y - float(r[1])) * float(T["height"]) / float(r[3])))
		tt = tt.clamp(Vector2i.ZERO, Vector2i(int(T["width"]) - 1, int(T["height"]) - 1))
		var ch: String = String(T["terrain"][tt.y])[tt.x]
		var title := ""
		var sz: Dictionary = C["sea_zones"].get(mid, {})
		if sz.has(ch):
			title = sz[ch][0]
		else:
			for z in C["zones"]:
				if z[0] == mid and tt.x >= int(z[1]) and tt.y >= int(z[2]) and tt.x <= int(z[3]) and tt.y <= int(z[4]):
					title = z[5]
					break
		if mid == "ocean":
			return [title, story.text("map_ocean_known")]
		if title == "":
			return ["", ""]
		return [title, ""] if story.visited.has(title) else ["???", ""]
	if not east_revealed() and px.x >= float(oc[0]) and px.y >= float(oc[1]) - 10 and px.y <= float(oc[1]) + float(oc[3]) + 10:
		return ["THE EASTERN OCEAN", story.text("map_ocean")]
	return [story.text("map_uncharted"), ""]


func map_places() -> Array:
	var out := []
	for p in C["worldmap"]["places"]:
		if story.visited.has(p["zone"]) and (p["map"] != "east" or east_revealed()):
			out.append({"px": map_px(String(p["map"]), Vector2(float(p["x"]), float(p["y"]))), "icon": p["icon"],
				"name": p["name"], "label": p["icon"] == "town"})
	for t in C["telescopes"]:
		if story.scopes.has(t["id"]):
			out.append({"px": map_px(String(t["map"]), Vector2(float(t["x"]), float(t["y"]))), "icon": "scope",
				"name": "TELESCOPE", "label": false})
	if story.has("dragon_band"):
		for l in C["landings"]:
			if story.landings.has(l["id"]):
				out.append({"px": map_px(String(l["map"]), Vector2(float(l["x"]), float(l["y"]))) + Vector2(4, -4),
					"icon": "dragon", "name": l["name"], "label": false})
	return out


# ------------------------------------------------------------------ loop + keys
func _process(delta: float) -> void:
	if dragon:
		camera.position = dragon.head.position + Vector2(0, 16)
	elif erne:
		erne.frame = int(Time.get_ticks_msec() / 110) % 4
		camera.position = erne.position + Vector2(0, 10)
		if hanging:
			hanging.position = erne.position + Vector2(0, 6)
			hanging.rotation = 0.12 * sin(Time.get_ticks_msec() * 0.006)
	else:
		camera.position = player.position + Vector2(0, -6)
	# smoothing trails a moving target by speed / smoothing: raise it so the trail stays within CAM_LAG
	camera.position_smoothing_speed = maxf(cam_smooth, player.speed() / cam_lag)
	if time_running and not busy():
		hour += delta * hours_per_second
		if hour >= 24.0:
			hour -= 24.0
			day += 1
			if seasons_running and day % DAYS_PER_SEASON == 0:
				set_season((season + 1) % 4)
	_apply_time()
	_time_tick()
	var ms := Time.get_ticks_msec()
	for e in ents:
		var n = e.get("node")
		if n != null and is_instance_valid(n) and n.has_meta("sparkle"):
			n.frame = [2, 1, 0, 1, 2, 2, 2, 2][int(ms / 120 + e["tiles"][0].x) % 8]
	_fade_clock -= delta
	if _fade_clock <= 0.0:
		_fade_clock = 0.08
		_update_occluders()
	_fade_step(delta)
	_npc_clock -= delta
	if _npc_clock <= 0.0:
		_npc_clock = 1.6
		if not busy():
			for e in ents:
				if e["type"] == "npc" and randf() < 0.3:
					_face_npc(e, [Vector2i.DOWN, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP][randi() % 5])


func _update_occluders() -> void:
	## trees and roofs in front of the player turn see-through, so you never lose sight of yourself
	_fade_want = {}
	if not player.visible:
		return
	var p: Vector2 = player.position + Vector2(0, -10)
	for s in map_nodes:
		if not is_instance_valid(s) or s.z_index < 0 or s.texture == null:
			continue
		if s.position.y <= player.position.y + 1 or s.position.y - player.position.y > 90:
			continue
		if abs(s.position.x - p.x) > 70:
			continue
		var r := Rect2(s.position + s.offset, s.texture.get_size())
		if r.has_point(p) or r.has_point(p + Vector2(0, -8)):
			_fade_want[s] = true
			if not _faded.has(s):
				_faded.append(s)


func _fade_step(delta: float) -> void:
	## see-through trees and roofs fade over 0.15 s instead of popping (with quick steps they popped a lot)
	var keep: Array = []
	for s in _faded:
		if not is_instance_valid(s):
			continue
		var want: bool = _fade_want.has(s)
		s.modulate.a = move_toward(s.modulate.a, 0.55 if want else 1.0, delta * 3.0)
		if want or s.modulate.a < 1.0:
			keep.append(s)
	_faded = keep


func _key_action(k: int) -> String:
	match k:
		KEY_UP, KEY_W:
			return "up"
		KEY_DOWN, KEY_S:
			return "down"
		KEY_LEFT, KEY_A:
			return "left"
		KEY_RIGHT, KEY_D:
			return "right"
		KEY_SPACE, KEY_ENTER, KEY_KP_ENTER, KEY_Z:
			return "confirm"
		KEY_X, KEY_ESCAPE, KEY_BACKSPACE:
			return "cancel"
		KEY_I:
			return "items"
		KEY_M:
			return "map"
		KEY_H:
			return "help"
	return ""


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and ui.mode in ["map", "map_text"]:
		ui.map_click(event.position)
		return
	if event is InputEventJoypadButton and event.pressed and not busy():
		var pd: Vector2i = {JOY_BUTTON_DPAD_UP: Vector2i.UP, JOY_BUTTON_DPAD_DOWN: Vector2i.DOWN,
			JOY_BUTTON_DPAD_LEFT: Vector2i.LEFT, JOY_BUTTON_DPAD_RIGHT: Vector2i.RIGHT}.get(event.button_index, Vector2i.ZERO)
		if pd != Vector2i.ZERO:
			player.queue_tap(pd)
		return
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	var k: int = event.physical_keycode
	if k == KEY_F1:
		debug.toggle()                                    # the debug sliders, any time
		return
	if ui.busy():
		var a := _key_action(k)
		if a != "":
			ui.input(a)
		return
	if cutscene:
		return
	var dir := _key_action(k)
	if DIRS.has(dir):
		player.queue_tap(DIRS[dir])                       # every tap counts, even one let go mid-step
		return
	match k:
		KEY_TAB:
			set_season((season + 1) % 4)
		KEY_1, KEY_2, KEY_3, KEY_4:
			set_season(k - KEY_1)
		KEY_T:
			next_phase()
		KEY_E:
			player.wear_pouch = not player.wear_pouch
		KEY_R:
			if story.has("walking_stick"):
				player.wear_stick = not player.wear_stick
		KEY_C:
			toggle_companion()
		KEY_H:
			ui.open_help()
		KEY_I:
			ui.open_inventory()
		KEY_M:
			ui.open_map()
		KEY_F9:
			ask_new_game()
		KEY_F:
			dragon_menu()
		KEY_SPACE, KEY_ENTER, KEY_KP_ENTER, KEY_Z:
			player.action()
