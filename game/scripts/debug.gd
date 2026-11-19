extends CanvasLayer
## F1: a debug window with sliders for testing in real time (movement, camera, screen, time).
## Changes apply at once and are not saved. "Copy" puts every value on the clipboard, so good settings can be
## made the new defaults; "Reset" puts back the values the game started with.

var main
var _rows: Array = []                # {slider, label, get, set, fmt, default}
var _hour: HSlider
var _hour_label: Label
var _hour_drag := false
var _fps: Label


func setup(m) -> void:
	main = m
	layer = 50
	visible = false
	var panel := PanelContainer.new()
	panel.position = Vector2(8, 8)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.08, 0.07, 0.12, 0.88)
	bg.set_content_margin_all(10)
	bg.set_corner_radius_all(4)
	panel.add_theme_stylebox_override("panel", bg)
	add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	panel.add_child(box)
	var head := HBoxContainer.new()
	box.add_child(head)
	head.add_child(_label("DEBUG  (F1 to close)", 130))
	_fps = _label("", 60)
	head.add_child(_fps)

	var p = main.player
	var mat: ShaderMaterial = main.screen.material
	_section(box, "Movement")
	_row(box, "Speed x", 0.2, 2.0, 0.05, "%.2f", func(): return p.speed_scale, func(v): p.speed_scale = v)
	for k in ["walk", "run", "surf", "whale", "hop"]:
		_row(box, "%s s/tile" % k.capitalize(), 0.01, 0.5, 0.005, "%.3f",
			func(): return p.times[k], func(v): p.times[k] = v)
	_section(box, "Camera")
	_row(box, "Smoothing", 1.0, 30.0, 0.5, "%.1f", func(): return main.cam_smooth, func(v): main.cam_smooth = v)
	_row(box, "Max lag px", 4.0, 120.0, 1.0, "%d", func(): return main.cam_lag, func(v): main.cam_lag = v)
	_section(box, "Screen")
	_row(box, "Game scale", 0.0, 10.0, 1.0, "fit|%d", func(): return main.scale_override, _set_game_scale)
	_row(box, "UI scale", 0.0, 10.0, 1.0, "auto|%d", func(): return main.ui_scale_override, _set_ui_scale)
	_row(box, "Tilt band", 0.0, 0.5, 0.01, "%.2f", func(): return _param(mat, "band", 0.24),
		func(v): mat.set_shader_parameter("band", v))
	_row(box, "Tilt blur", 0.0, 6.0, 0.1, "%.1f", func(): return _param(mat, "strength", 2.2),
		func(v): mat.set_shader_parameter("strength", v))
	_section(box, "Time")
	var hr: Dictionary = _row(box, "Hour", 0.0, 23.99, 0.25, "%.2f", func(): return main.hour, func(v): main.set_time(v))
	_hour = hr["slider"]
	_hour_label = hr["label"]
	_hour.drag_started.connect(func(): _hour_drag = true)
	_hour.drag_ended.connect(func(_changed): _hour_drag = false)
	_row(box, "Clock speed x", 0.0, 30.0, 0.5, "%.1f", func(): return main.hours_per_second * 30.0,
		func(v): main.hours_per_second = v / 30.0)

	var buttons := HBoxContainer.new()
	box.add_child(buttons)
	buttons.add_child(_button("Reset", _reset))
	buttons.add_child(_button("Copy values", _copy))


func toggle() -> void:
	visible = not visible
	if visible:
		for r in _rows:
			_show(r, r["get"].call())


func _process(_delta: float) -> void:
	if not visible:
		return
	_fps.text = "%d fps" % Engine.get_frames_per_second()
	if not _hour_drag:                                    # the clock keeps running: follow it
		_hour.set_value_no_signal(main.hour)
		_hour_label.text = "%.2f" % main.hour


# ------------------------------------------------------------------ building blocks
func _label(t: String, w: float) -> Label:
	var l := Label.new()
	l.text = t
	l.custom_minimum_size.x = w
	l.add_theme_font_size_override("font_size", 13)
	return l


func _section(box: VBoxContainer, t: String) -> void:
	var l := _label(t.to_upper(), 0)
	l.add_theme_color_override("font_color", Color("E0A256"))
	box.add_child(l)


func _row(box: VBoxContainer, title: String, lo: float, hi: float, stp: float, fmt: String,
		getter: Callable, setter: Callable) -> Dictionary:
	var h := HBoxContainer.new()
	box.add_child(h)
	h.add_child(_label(title, 110))
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = stp
	s.custom_minimum_size = Vector2(150, 16)
	s.focus_mode = Control.FOCUS_NONE                    # arrow keys keep walking the hero, not moving sliders
	h.add_child(s)
	var val := _label("", 50)
	h.add_child(val)
	var r := {"slider": s, "label": val, "get": getter, "set": setter, "fmt": fmt, "default": getter.call()}
	_rows.append(r)
	_show(r, r["default"])
	s.value_changed.connect(func(v: float) -> void:
		setter.call(v)
		_show(r, v, false)
	)
	return r


func _show(r: Dictionary, v: float, move_slider := true) -> void:
	if move_slider:
		r["slider"].set_value_no_signal(v)
	var fmt: String = r["fmt"]
	if "|" in fmt:                                        # "fit|%d": the word for 0, a format otherwise
		var parts := fmt.split("|")
		r["label"].text = parts[0] if v == 0.0 else parts[1] % v
	else:
		r["label"].text = fmt % v


func _button(t: String, f: Callable) -> Button:
	var b := Button.new()
	b.text = t
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 13)
	b.pressed.connect(f)
	return b


func _set_game_scale(v: float) -> void:
	main.scale_override = int(v)                          # 0: the biggest that fits the window
	main.relayout()


func _set_ui_scale(v: float) -> void:
	main.ui_scale_override = int(v)                       # 0: 0.8 x the game scale
	main.relayout()


func _param(mat: ShaderMaterial, key: String, fallback: float) -> float:
	var v = mat.get_shader_parameter(key)
	return fallback if v == null else float(v)


func _reset() -> void:
	for r in _rows:
		if r["slider"] == _hour:
			continue                                      # (the time of day is not a setting)
		r["set"].call(r["default"])
		_show(r, r["default"])


func _copy() -> void:
	var lines: PackedStringArray = []
	for r in _rows:
		var name_label: Label = r["slider"].get_parent().get_child(0)
		lines.append("%s = %s" % [name_label.text, r["label"].text])
	DisplayServer.clipboard_set("\n".join(lines))
	main.ui.toast("DEBUG VALUES COPIED TO THE CLIPBOARD.", 2.0)
