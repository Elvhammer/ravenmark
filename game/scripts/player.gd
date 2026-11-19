extends Node2D
## The Cartographer: 4-direction grid movement with a smooth step, walk/run animation, ledge hops,
## surfing on the otter (Otter Stick), the seal (Seal Flute, cold water) or the whale (Whale Horn, the open
## ocean, much faster), doors, stairs and region edges. The Running Shoes make walking a little faster.
## The position is the player's feet, so the player y-sorts correctly with trees and houses.
## Every tap counts: main.gd passes each direction key press to queue_tap(), so a tap that starts and ends
## during a step is remembered and walked as soon as the step ends. Holding a key keeps walking as before.

const TILE := 16
## Seconds per tile at speed 1.0. Every step lasts its time / MOVE_SPEED, so one number speeds up or slows down
## all movement and keeps the ratios: surfing twice walking, the whale twice the otter.
const WALK_TIME := 0.10
const RUN_TIME := 0.055
const SURF_TIME := 0.05              # otter and seal
const WHALE_TIME := 0.025            # the whale
const SURF_START_TIME := 0.125       # stepping off the shore onto the animal
const SHOE_WALK := 0.08              # with the Running Shoes
const SHOE_RUN := 0.0425
const HOP_TIME := 0.17               # a ledge hop (two tiles)
const MOVE_SPEED := 0.7              # 30% slower than the times above: walking 0.143 s per tile
const MOUNT_OFFSET := {"otter": Vector2(-36, -38), "seal": Vector2(-36, -38), "whale": Vector2(-48, -44)}
const STRIDE_SPLIT := 0.09           # steps at least this long show a stride, then stand; quicker ones hold the stride
const ROW := {Vector2i.DOWN: 0, Vector2i.UP: 1, Vector2i.RIGHT: 2, Vector2i.LEFT: 2}
const TAP_MAX := 4                   # taps remembered at once (mashing a key never runs away with you)

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
var taps: Array[Vector2i] = []       # direction taps not walked yet, oldest first
var speed_scale := MOVE_SPEED        # the debug window (F1) changes these two live
var times := {"walk": WALK_TIME, "run": RUN_TIME, "surf": SURF_TIME, "whale": WHALE_TIME,
	"surf_start": SURF_START_TIME, "shoe_walk": SHOE_WALK, "shoe_run": SHOE_RUN, "hop": HOP_TIME}
var _from := Vector2.ZERO            # the step under way: start and end (pixels), length and time so far
var _to := Vector2.ZERO
var _dur := 0.1
var _t := 0.0
var _hopping := false
var _carry := 0.0                    # time left over when a step ends, so the next step keeps an even pace
var _foot := 0                       # which foot leads (frame 1 or 3); swaps every step

var body: Sprite2D
var pouch: Sprite2D
var stick: Sprite2D
var mount: Sprite2D
var band: Sprite2D


func _ready() -> void:
	body = _sheet("res://game/art/hero/hero_body.png", Vector2(-10, -23))
	pouch = _sheet("res://game/art/hero/hero_pouch.png", Vector2(-10, -23))
	stick = _sheet("res://game/art/hero/hero_stick.png", Vector2(-10, -23))
	band = _sheet("res://game/art/hero/hero_band.png", Vector2(-10, -23))
	mount = _sheet("res://game/art/mounts/surf_otter.png", Vector2(-36, -38))
	## Gear stacks by child order (body, pouch, stick, band), never by z_index: a raised z_index drew the pouch
	## and band over trees the hero walks behind, and the stick's z -1 hid it under the ground.
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
	moving = false                                        # (a teleport ends any step under way)
	_hopping = false
	hop_offset = 0.0
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


func queue_tap(d: Vector2i) -> void:
	## a direction key went down: it counts as one step even if it is let go before the current step ends
	if taps.size() < TAP_MAX:
		taps.append(d)


func _process(delta: float) -> void:
	running = Input.is_physical_key_pressed(KEY_SHIFT) or Input.is_joy_button_pressed(0, JOY_BUTTON_B)
	if moving:
		_t += delta
		_follow_path()
		if _t >= _dur:
			_carry = minf(_t - _dur, delta)
			_arrived()
	if main.busy():
		taps.clear()                                      # no stale steps after a door, a text box or a menu
	elif not moving:
		var d := _input_dir()
		if not taps.is_empty():
			d = taps.pop_front()                          # a remembered tap first, then whatever is held
		if d != Vector2i.ZERO:
			step(d)                                       # (starts in this same frame: no pause between steps)
	_carry = 0.0
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
				_move(target, step_time("whale"))
			else:
				_say("ocean_deep")
		elif wk == "sea" and mount_kind == "whale":
			_move(target, step_time("whale"))
		elif wk == "cold":
			if main.story.has("seal_flute"):
				_set_mount("seal")
				if not seal_hint_shown:
					seal_hint_shown = true
					_say("seal_on")
				_move(target, step_time("surf"))
			else:
				_say("otter_cold")
		elif wk != "":
			_set_mount("otter")
			_move(target, step_time("surf"))
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


func step_time(kind: String) -> float:
	## seconds for one step of this kind right now
	return float(times[kind]) / speed_scale


func walk_time() -> float:
	var shoes: bool = main.story.has("running_shoes")
	if running:
		return step_time("shoe_run" if shoes else "run")
	return step_time("shoe_walk" if shoes else "walk")


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
	_move(front, step_time("surf_start"))


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
	_begin(t, dur, false)


func _hop(t: Vector2i) -> void:
	## one-way ledge: jump over the ledge tile and land two tiles down
	_begin(t, step_time("hop"), true)


func _begin(t: Vector2i, dur: float, hop: bool) -> void:
	## start a step; _process moves it along (no tween, so a step ends and the next begins in the same frame)
	moving = true
	var from := tile
	tile = t
	main.on_player_step(from, t, dur)
	_from = tile_pos(from)
	_to = tile_pos(t)
	_dur = dur
	_t = _carry
	_hopping = hop
	_foot = 1 - _foot
	_follow_path()


func speed() -> float:
	## pixels per second right now (the camera catches up faster when you go faster)
	if not moving:
		return 0.0
	return TILE * (2.0 if _hopping else 1.0) / _dur


func _follow_path() -> void:
	## smooth: the world renders at screen resolution, so a position between two game pixels lands on a screen
	## pixel and the hero glides with the camera instead of jumping a whole (5x) block against the ground
	var k := clampf(_t / _dur, 0.0, 1.0)
	position = _from.lerp(_to, k)
	hop_offset = -sin(PI * k) * 9.0 if _hopping else 0.0


func _arrived() -> void:
	moving = false
	_hopping = false
	position = _to
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
	## Walk frames follow the step, not a clock: frames 0 and 2 stand, 1 and 3 stride (left / right foot).
	## Each step shows one stride (feet alternating step by step), then stands for its second half, so it
	## always ends standing and a pose is never on screen for just a frame or two.
	var f := 0
	if moving and (_hopping or _dur < STRIDE_SPLIT or _t < _dur * 0.5):
		f = 1 + 2 * _foot
	for s in [body, pouch, stick, band]:
		s.frame = row * 4 + f
		s.flip_h = flip
		s.position.y = hop_offset
	stick.show_behind_parent = facing != Vector2i.UP      # slung on the back: in front only when seen from behind
