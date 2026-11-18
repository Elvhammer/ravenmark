extends Node2D
## The Cartographer: 4-direction grid movement with a smooth step, walk/run animation, ledge hops,
## surfing on the otter (Otter Stick), the seal (Seal Flute, cold water) or the whale (Whale Horn, the open
## ocean, much faster), doors, stairs and region edges. The Running Shoes make walking a little faster.
## The position is the player's feet, so the player y-sorts correctly with trees and houses.

const TILE := 16
const WALK_TIME := 0.20
const RUN_TIME := 0.11
const SURF_TIME := 0.10              # surfing is twice as fast as walking
const WHALE_TIME := 0.05             # the whale is twice as fast again
const SHOE_WALK := 0.16              # with the Running Shoes
const SHOE_RUN := 0.085
const MOUNT_OFFSET := {"otter": Vector2(-36, -38), "seal": Vector2(-36, -38), "whale": Vector2(-48, -44)}
const HOP_TIME := 0.34
const ROW := {Vector2i.DOWN: 0, Vector2i.UP: 1, Vector2i.RIGHT: 2, Vector2i.LEFT: 2}

var main
var tile := Vector2i.ZERO
var facing := Vector2i.DOWN
var moving := false
var surfing := false
var mount_kind := "otter"
var wear_pouch := true
var wear_stick := false
var running := false
var anim_clock := 0.0
var hop_offset := 0.0
var seal_hint_shown := false

var body: Sprite2D
var pouch: Sprite2D
var stick: Sprite2D
var mount: Sprite2D
var band: Sprite2D


func _ready() -> void:
	body = _sheet("res://game/art/hero/hero_body.png", Vector2(-10, -23))
	pouch = _sheet("res://game/art/hero/hero_pouch.png", Vector2(-10, -23))
	stick = _sheet("res://game/art/hero/hero_stick.png", Vector2(-10, -23))
	mount = _sheet("res://game/art/mounts/surf_otter.png", Vector2(-36, -38))
	band = _sheet("res://game/art/hero/hero_band.png", Vector2(-10, -23))
	band.z_index = 2
	pouch.z_index = 1
	mount.visible = false
	_update_frames()


func _sheet(path: String, off: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = load(path)
	s.hframes = 4
	s.vframes = 3
	s.centered = false
	s.offset = off
	add_child(s)
	return s


func tile_pos(t: Vector2i) -> Vector2:
	return Vector2(t.x * TILE + 8, t.y * TILE + 14)


func place(t: Vector2i) -> void:
	tile = t
	position = tile_pos(t)
	main.on_player_tile(tile, surfing)


# ------------------------------------------------------------------ input + movement
func _input_dir() -> Vector2i:
	if Input.is_physical_key_pressed(KEY_UP) or Input.is_physical_key_pressed(KEY_W) or Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_UP):
		return Vector2i.UP
	if Input.is_physical_key_pressed(KEY_DOWN) or Input.is_physical_key_pressed(KEY_S) or Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_DOWN):
		return Vector2i.DOWN
	if Input.is_physical_key_pressed(KEY_LEFT) or Input.is_physical_key_pressed(KEY_A) or Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_LEFT):
		return Vector2i.LEFT
	if Input.is_physical_key_pressed(KEY_RIGHT) or Input.is_physical_key_pressed(KEY_D) or Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_RIGHT):
		return Vector2i.RIGHT
	return Vector2i.ZERO


func _process(delta: float) -> void:
	running = Input.is_physical_key_pressed(KEY_SHIFT) or Input.is_joy_button_pressed(0, JOY_BUTTON_B)
	if not moving and not main.busy():
		var d := _input_dir()
		if d != Vector2i.ZERO:
			step(d)
	anim_clock += delta
	_update_frames()


func step(d: Vector2i) -> void:
	## try to move one tile in direction d (also used by the autotest)
	facing = d
	var target := tile + d
	if main.try_edge(target, d) or main.try_warp(target, d):
		return
	var c: String = main.tile_at(target)
	if surfing:
		var wk: String = main.water_kind(target)
		if c == "b":
			_say("reef")
		elif c == "l" and not main.low_tide():
			_say("shallows")
		elif wk == "ocean":
			if main.story.has("whale_horn"):
				if mount_kind != "whale":
					_set_mount("whale")
					_say("whale_on")
				_move(target, WHALE_TIME)
			else:
				_say("ocean_deep")
		elif wk == "sea" and mount_kind == "whale":
			_move(target, WHALE_TIME)
		elif wk == "cold":
			if main.story.has("seal_flute"):
				_set_mount("seal")
				if not seal_hint_shown:
					seal_hint_shown = true
					_say("seal_on")
				_move(target, SURF_TIME)
			else:
				_say("otter_cold")
		elif wk != "":
			_set_mount("otter")
			_move(target, SURF_TIME)
		elif main.can_walk(target):
			surfing = false                                   # step back onto land
			_move(target, walk_time())
		return
	if main.dark_blocks(target) and main.tile_at(target) == ".":
		_say("dark")
	elif d == Vector2i.DOWN and main.is_ledge(target) and main.can_walk(target + Vector2i.DOWN):
		_hop(target + Vector2i.DOWN)
	elif main.can_walk(target):
		_move(target, walk_time())


func walk_time() -> float:
	var shoes: bool = main.story.has("running_shoes")
	if running:
		return SHOE_RUN if shoes else RUN_TIME
	return SHOE_WALK if shoes else WALK_TIME


func action() -> void:
	## Space / Z / Enter: read signs, open chests, or call the otter when facing water
	if moving or main.busy():
		return
	var front := tile + facing
	if main.interact(front):
		return
	if surfing:
		return
	var c: String = main.tile_at(front)
	if main.is_outdoor() and c == "l" and not main.low_tide():
		_say("shallows")
		return
	if main.is_outdoor() and c == "b":
		_say("reef")
		return
	var st = main.story
	var wk: String = main.water_kind(front)
	if wk == "ocean":
		if st.has("whale_horn"):
			_start_surf(front, "whale")
			_say("whale_on")
		else:
			_say("ocean_deep")
	elif wk == "cold":
		if st.has("seal_flute"):
			_start_surf(front, "seal")
		else:
			_say("otter_cold" if st.has("otter_stick") else "no_otter")
	elif wk != "":
		if st.has("otter_stick"):
			_start_surf(front, "otter")
		elif wk == "sea" and st.has("whale_horn"):
			_start_surf(front, "whale")
		else:
			_say("no_otter")
	elif main.is_outdoor() and c in ["=", "\""] and main.is_winter():
		_say("frozen")


func _start_surf(front: Vector2i, kind: String) -> void:
	surfing = true
	_set_mount(kind)
	_move(front, 0.25)


func fit_mount() -> void:
	## arriving on water from another region: the right animal for this water
	match main.water_kind(tile):
		"ocean":
			_set_mount("whale")
		"cold":
			_set_mount("seal")
		"sea":
			if mount_kind != "whale":
				_set_mount("otter")
		_:
			_set_mount("otter")


func _say(id: String) -> void:
	main.ui.toast(main.story.text(id))


func _move(t: Vector2i, dur: float) -> void:
	moving = true
	var from := tile
	tile = t
	main.on_player_step(from, t, dur)
	var tw := create_tween()
	tw.tween_property(self, "position", tile_pos(t), dur)
	tw.finished.connect(_arrived)


func _hop(t: Vector2i) -> void:
	## one-way ledge: jump over the ledge tile and land two tiles down
	moving = true
	main.on_player_step(tile, t, HOP_TIME)
	tile = t
	var start := position
	var end := tile_pos(t)
	var arc := func(k: float) -> void:
		position = start.lerp(end, k)
		hop_offset = -sin(PI * k) * 9.0
	var tw := create_tween()
	tw.tween_method(arc, 0.0, 1.0, HOP_TIME)
	tw.finished.connect(_arrived)


func _arrived() -> void:
	moving = false
	hop_offset = 0.0
	main.update_companion_visibility()
	main.on_player_tile(tile, surfing)


func on_season_changed() -> void:
	## winter freezes rivers under a surfing player; spring thaws them under a walking one
	if not main.is_outdoor():
		return
	if surfing and main.tile_at(tile) == "=" and main.is_winter():
		surfing = false
	elif not surfing and not main.can_walk(tile):
		if main.water_kind(tile) != "":
			surfing = true
			_set_mount("otter")
		else:
			for r in range(1, 6):
				for dy in range(-r, r + 1):
					for dx in range(-r, r + 1):
						var t := tile + Vector2i(dx, dy)
						if main.can_walk(t):
							place(t)
							return


func force_mount(kind: String) -> void:
	mount_kind = kind
	mount.texture = load("res://game/art/mounts/surf_%s.png" % kind)
	mount.offset = MOUNT_OFFSET[kind]


func _set_mount(kind: String) -> void:
	if kind != mount_kind:
		mount_kind = kind
		mount.texture = load("res://game/art/mounts/surf_%s.png" % kind)
		mount.offset = MOUNT_OFFSET[kind]


# ------------------------------------------------------------------ animation
func _update_frames() -> void:
	var row: int = ROW[facing]
	var flip := facing == Vector2i.LEFT
	mount.visible = surfing
	body.visible = not surfing
	pouch.visible = wear_pouch and not surfing
	stick.visible = wear_stick and not surfing
	band.visible = not surfing and main != null and main.story != null and main.story.has("dragon_band")
	if surfing:
		mount.frame = row * 4 + int(anim_clock * 5.0) % 4
		mount.flip_h = flip
		return
	var f := 0
	if moving:
		f = int(anim_clock * (12.0 if running else 8.0)) % 4
	for s in [body, pouch, stick, band]:
		s.frame = row * 4 + f
		s.flip_h = flip
		s.position.y = hop_offset
	stick.z_index = 1 if facing == Vector2i.UP else -1
