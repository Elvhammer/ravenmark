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
	tile = t
	moving = true
	var tw := create_tween()
	tw.tween_property(self, "position", tile_pos(t), dur)
	tw.finished.connect(func() -> void: moving = false)


func walk_to(t: Vector2i, dur := 0.35) -> void:
	## used when the fox runs over to dig something up
	if Vector2(t - tile).length() <= 2.5:
		follow_to(t, dur)
	else:
		place(t, facing)


func _process(delta: float) -> void:
	anim += delta
	if not spr:
		return
	var f := 0
	if kind == "owl":
		f = int(anim * 6.0) % 4
	elif moving:
		f = int(anim * 10.0) % 4
	spr.frame = ROW[facing] * 4 + f
	spr.flip_h = facing == Vector2i.LEFT
