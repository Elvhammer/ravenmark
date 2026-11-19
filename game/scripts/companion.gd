extends Node2D
## The companion (fox or owl) follows one tile behind the player, stepping into the tile the player left.
## The owl flutters along even over water; the fox waits on land while the player surfs.

const TILE := 16
const ROW := {Vector2i.DOWN: 0, Vector2i.UP: 1, Vector2i.RIGHT: 2, Vector2i.LEFT: 2}

var kind := "fox"
var tile := Vector2i.ZERO
var facing := Vector2i.DOWN
var moving := false
var shown := true                    # C toggles this; abilities work either way
var anim := 0.0
var spr: Sprite2D
var _from := Vector2.ZERO           # the step under way: from, to, its length, time so far, which paw leads
var _to := Vector2.ZERO
var _dur := 0.1
var _t := 0.0
var _foot := 0


func _ready() -> void:
	process_priority = -1                                 # moves before main._process aims the camera, like the hero


func setup(k: String) -> void:
	kind = k
	if spr:
		spr.queue_free()
	spr = Sprite2D.new()
	spr.texture = load("res://game/art/companions/%s.png" % k)
	spr.hframes = 4
	spr.vframes = 3
	spr.centered = false
	spr.offset = Vector2(-10, -14) if k == "fox" else Vector2(-10, -21)
	add_child(spr)


func tile_pos(t: Vector2i) -> Vector2:
	return Vector2(t.x * TILE + 8, t.y * TILE + 14)


func place(t: Vector2i, f := Vector2i.DOWN) -> void:
	tile = t
	facing = f
	moving = false
	position = tile_pos(t)


func follow_to(t: Vector2i, dur: float) -> void:
	var d := t - tile
	if d == Vector2i.ZERO:
		return
	if abs(d.x) + abs(d.y) > 2:
		place(t, facing)
		return
	facing = Vector2i(sign(d.x), 0) if abs(d.x) >= abs(d.y) else Vector2i(0, sign(d.y))
	_from = tile_pos(tile)                                # (the player's next step can start before this one's
	_to = tile_pos(t)                                     #  last frame: start from the tile, not from mid-step)
	tile = t
	moving = true
	_dur = dur
	_t = 0.0
	_foot = 1 - _foot


func walk_to(t: Vector2i, dur := 0.35) -> void:
	## used when the fox runs over to dig something up
	if Vector2(t - tile).length() <= 2.5:
		follow_to(t, dur)
	else:
		place(t, facing)


func _process(delta: float) -> void:
	anim += delta
	var stride := false
	if moving:                                            # smooth (sub-pixel) glide, in step with the hero
		_t += delta
		position = _from.lerp(_to, clampf(_t / _dur, 0.0, 1.0))
		stride = _dur < 0.09 or _t < _dur * 0.5
		if _t >= _dur:
			moving = false
	if not spr:
		return
	var f := 0
	if kind == "owl":
		f = int(anim * 6.0) % 4                           # the owlet's wings beat all the time
	elif stride:
		## like the hero: frames follow the step (0/2 stand, 1/3 stride), so no pose flashes for a frame
		f = 1 + 2 * _foot
	spr.frame = ROW[facing] * 4 + f
	spr.flip_h = facing == Vector2i.LEFT
