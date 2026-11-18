extends Node2D
## The dragon summoned by the Dragon Band: a long, Chinese-style dragon. The head flies along a curve; the body
## segments follow the exact path the head took, with a gentle sideways wave, so the whole length snakes
## through the sky. The rider (you) sits just behind the head.

const SEGMENTS := 24
const GAP := 6.5
const WAVE := 4.0

var head: Sprite2D
var segs: Array = []
var legs: Array = []
var tail: Sprite2D
var rider: Sprite2D
var shadow: Sprite2D
var trail: Array = []                # head positions, newest first
var t := 0.0


func _ready() -> void:
	z_index = 45
	shadow = Sprite2D.new()
	shadow.texture = load("res://game/art/companions/erne_shadow.png")
	shadow.modulate.a = 0.35
	shadow.z_index = -46
	add_child(shadow)
	tail = Sprite2D.new()
	tail.texture = load("res://game/art/companions/dragon_tail.png")
	add_child(tail)
	var leg_tex: Texture2D = load("res://game/art/companions/dragon_leg.png")
	for i in range(SEGMENTS - 1, -1, -1):                        # back to front, so the head draws on top
		var s := Sprite2D.new()
		s.texture = load("res://game/art/companions/dragon_seg_%s.png" % ("a" if i % 2 == 0 else "b"))
		add_child(s)
		segs.push_front(s)
		if i in [4, 5, 15, 16]:
			var l := Sprite2D.new()
			l.texture = leg_tex
			l.position = Vector2(0, 6)
			s.add_child(l)
			l.show_behind_parent = true
			legs.append(l)
	rider = Sprite2D.new()
	rider.texture = load("res://game/art/hero/hero_body.png")
	rider.hframes = 4
	rider.vframes = 3
	rider.frame = 4
	rider.offset = Vector2(0, -12)
	rider.visible = false
	add_child(rider)
	head = Sprite2D.new()
	head.texture = load("res://game/art/companions/dragon_head.png")
	add_child(head)


func start(pos: Vector2) -> void:
	head.position = pos
	trail = []
	for i in SEGMENTS * 4 + 8:
		trail.append(pos + Vector2(-i * 2.0, -i * 1.2))
	_layout()


func fly_to(target: Vector2, dur: float, ctrl: Vector2) -> void:
	var p0: Vector2 = head.position
	var tw := create_tween()
	var step := func(k: float) -> void:
		var e := k * k * (3.0 - 2.0 * k)
		head.position = p0.lerp(ctrl, e).lerp(ctrl.lerp(target, e), e)
	tw.tween_method(step, 0.0, 1.0, dur)
	await tw.finished


func show_rider(on: bool) -> void:
	rider.visible = on


func _process(delta: float) -> void:
	t += delta
	if trail.is_empty() or head.position.distance_to(trail[0]) >= 1.0:
		trail.push_front(head.position)
		if trail.size() > 400:
			trail.resize(400)
	_layout()


func _point_at(dist: float) -> Array:
	## [position, direction] at a distance along the trail behind the head
	var acc := 0.0
	for i in range(1, trail.size()):
		var a: Vector2 = trail[i - 1]
		var b: Vector2 = trail[i]
		var seg := a.distance_to(b)
		if acc + seg >= dist and seg > 0.0:
			var k := (dist - acc) / seg
			return [a.lerp(b, k), (a - b).normalized()]
		acc += seg
	var last: Vector2 = trail[trail.size() - 1]
	return [last, Vector2.RIGHT]


func _layout() -> void:
	var hd := Vector2.RIGHT
	if trail.size() > 3:
		hd = (trail[0] - trail[3]).normalized() if trail[0] != trail[3] else Vector2.RIGHT
	head.rotation = hd.angle()
	head.flip_v = hd.x < 0                                       # keep the head the right way up
	for i in segs.size():
		var pd: Array = _point_at(10.0 + i * GAP)
		var side: Vector2 = Vector2(-pd[1].y, pd[1].x)
		var w: float = sin(t * 6.0 - i * 0.55) * WAVE * minf(1.0, i / 4.0)
		segs[i].position = pd[0] + side * w
		segs[i].scale = Vector2.ONE * (1.0 - 0.35 * float(i) / segs.size())
	var tp: Array = _point_at(10.0 + segs.size() * GAP)
	tail.position = tp[0]
	tail.rotation = (tp[1] as Vector2).angle()
	rider.position = segs[1].position
	rider.frame = 4 if hd.y < 0 else 0
	shadow.position = head.position + Vector2(0, 46)
	shadow.global_position = head.global_position + Vector2(0, 46)
