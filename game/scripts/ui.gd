extends Node
## HUD and menus, drawn with the game's pixel font at a whole-number scale (never blurred). Everything is laid
## out for 320 x 180 HUD pixels; on bigger screens the HUD has more room (`view`), and groups of widgets are
## pinned to the corners, the bottom edge or the middle by anchor nodes (see layout()).
## Dialogue, choices, shops and the item list are coroutines: `await ui.say(...)` returns when the player
## has read the text. In autoplay mode (autotest) text advances by itself and choices come from `queue`.

signal _done(result)

const VIEW := Vector2(320, 180)      # the size every widget position below is designed for
const CREAM := Color("F2E3B3")
const GOLD := Color("E0A256")
const INK := Color("1E1B2C")
const DIM := Color("8A8496")
const TEAL := Color("9CD0C9")
const TYPE_SPEED := 70.0             # characters per second

var main
var story
var hud: Control
var view := VIEW                     # the HUD's real size in HUD pixels (the game picture / ui scale)
var a_tr: Control                    # anchors: top right, bottom right, bottom middle, middle, dialogue
var a_br: Control
var a_low: Control
var a_mid: Control
var a_dlg: Control
var mode := ""                       # "", say, choose, list, inv, map, help
var autoplay := false
var auto_delay := 0.05
var queue: Array = []                # autoplay answers: choice indices, item ids to buy/sell, "leave"

var _glyphs := {}
var _font: Image
var _tints := {}
var _cache := {}
var _tex := {}

var banner_box: Control
var banner_time := 0.0
var badge: TextureRect
var clock_icon: TextureRect
var clock_digits: Array = []
var coins_label: TextureRect
var coins_box: Control
var hint: TextureRect
var toast_box: NinePatchRect
var toast_lines: Array = []
var toast_time := 0.0
var box: NinePatchRect
var box_lines: Array = []
var box_full: Array = []             # [texture, char x positions] per line
var box_icon: TextureRect
var box_next: TextureRect
var name_box: NinePatchRect
var name_label: TextureRect
var reveal := 0.0
var reveal_total := 0
var choice_box: NinePatchRect
var choice_cursor: TextureRect
var choice_idx := 0
var choice_n := 0
var list_box: NinePatchRect
var list_rows: Array = []
var list_idx := 0
var list_entries: Array = []
var list_kind := ""
var inv_items: Array = []
var map_box: NinePatchRect
var map_marker: Control
var map_cursor: TextureRect
var map_cursor_px := Vector2.ZERO
var map_info_label: TextureRect
var view_box: ColorRect
var view_img: TextureRect
var help_box: NinePatchRect
var fader: ColorRect


func build(m) -> void:
	main = m
	story = m.story
	_load_font()
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	hud = Control.new()
	hud.scale = Vector2(4, 4)
	hud.size = VIEW
	hud.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(hud)
	# widgets keep their 320 x 180 positions inside an anchor; layout() moves the anchors (draw order = this order)
	banner_box = Control.new()                                   # top left
	banner_box.position = Vector2(6, 6)
	banner_box.visible = false
	hud.add_child(banner_box)
	a_tr = _anchor()                                             # top right: season, clock, coins
	badge = _rect(a_tr, Vector2(250, 6), null)
	_build_clock()
	coins_box = Control.new()
	coins_box.position = Vector2(VIEW.x - 6 - 48, 42)
	a_tr.add_child(coins_box)
	_panel(coins_box, Vector2.ZERO, Vector2(48, 14))
	_rect(coins_box, Vector2(4, 3), tex("res://game/art/hud/hud_coin.png"))
	coins_label = _rect(coins_box, Vector2(15, 4), null)
	a_br = _anchor()                                             # bottom right: the help hint
	hint = _rect(a_br, Vector2.ZERO, text_tex("H: HELP", DIM, false))
	hint.position = Vector2(VIEW.x - hint.texture.get_width() - 4, VIEW.y - 10)
	a_low = _anchor()                                            # bottom middle: messages
	toast_box = _panel(a_low, Vector2(6, 146), Vector2(308, 28))
	toast_box.visible = false
	for i in 2:
		toast_lines.append(_rect(toast_box, Vector2(8, 6 + i * 10), null))
	a_mid = _anchor()                                            # middle: lists, the world map, help
	list_box = _panel(a_mid, Vector2(14, 8), Vector2(292, 120))
	list_box.visible = false
	map_box = _panel(a_mid, Vector2(10, 4), Vector2(300, 172))
	map_box.visible = false
	help_box = _panel(a_mid, Vector2(30, 20), Vector2(260, 140))
	help_box.visible = false
	view_box = ColorRect.new()                                   # the whole HUD: telescope view
	view_box.color = INK
	view_box.size = VIEW
	view_box.visible = false
	view_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(view_box)
	view_img = _rect(view_box, Vector2.ZERO, null)
	a_dlg = _anchor()                                            # bottom middle, on top: dialogue and choices
	choice_box = _panel(a_dlg, Vector2(200, 90), Vector2(100, 30))
	choice_box.visible = false
	choice_cursor = _rect(choice_box, Vector2(6, 6), tex("res://game/art/hud/cursor.png"))
	name_box = _panel(a_dlg, Vector2(12, 119), Vector2(40, 14))
	name_label = _rect(name_box, Vector2(6, 3), null)
	name_box.visible = false
	box = _panel(a_dlg, Vector2(6, 132), Vector2(308, 42))
	box.visible = false
	box_icon = _rect(box, Vector2(8, 12), null)
	for i in 3:
		box_lines.append(_rect(box, Vector2(8, 6 + i * 10), null))
	box_next = _rect(box, Vector2(294, 34), tex("res://game/art/hud/next.png"))
	fader = ColorRect.new()                                      # the whole HUD: fades for doors and travel
	fader.color = INK
	fader.size = VIEW
	fader.modulate.a = 0.0
	fader.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(fader)


func _anchor() -> Control:
	var c := Control.new()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(c)
	return c


func layout(origin: Vector2, size: Vector2, s: int) -> void:
	## cover the game picture (origin and size in window pixels) at s window pixels per HUD pixel
	hud.position = origin
	hud.scale = Vector2(s, s)
	view = size / float(s)
	hud.size = view
	a_tr.position = Vector2(view.x - VIEW.x, 0)
	a_br.position = view - VIEW
	a_low.position = Vector2((view.x - VIEW.x) / 2.0, view.y - VIEW.y)
	a_dlg.position = a_low.position
	a_mid.position = (view - VIEW) / 2.0
	view_box.size = view
	fader.size = view
	if view_img.texture:
		view_img.position = ((view - view_img.texture.get_size()) / 2.0 - Vector2(0, 18)).floor()


func to_hud(p: Vector2) -> Vector2:
	## a window position (mouse) in HUD pixels
	return (p - hud.position) / hud.scale.x


func tex(path: String) -> Texture2D:
	if not _tex.has(path):
		_tex[path] = load(path)
	return _tex[path]


func busy() -> bool:
	return mode != ""


# ------------------------------------------------------------------ pixel font -> textures
func _load_font() -> void:
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://game/data/font.json"))
	for ch in meta["glyphs"].keys():
		_glyphs[ch] = [int(meta["glyphs"][ch][0]), int(meta["glyphs"][ch][1])]
	_font = (load("res://game/art/hud/font.png") as Texture2D).get_image()
	_font.convert(Image.FORMAT_RGBA8)


func _tinted(c: Color) -> Image:
	var key := c.to_html()
	if not _tints.has(key):
		var im: Image = _font.duplicate()
		for y in im.get_height():
			for x in im.get_width():
				im.set_pixel(x, y, c if im.get_pixel(x, y).a > 0.5 else Color(0, 0, 0, 0))
		_tints[key] = im
	return _tints[key]


func _glyph(ch: String) -> Array:
	return _glyphs[ch] if _glyphs.has(ch) else _glyphs[" "]


func text_width(s: String) -> int:
	var w := 0
	for i in s.length():
		w += int(_glyph(s[i])[1]) + 1
	return max(0, w - 1)


func char_xs(s: String) -> Array:
	var xs := []
	var w := 0
	for i in s.length():
		w += int(_glyph(s[i])[1]) + 1
		xs.append(w)
	return xs


func text_tex(s: String, col := CREAM, shadow := true) -> Texture2D:
	var key := "%s|%s|%s" % [s, col.to_html(), shadow]
	if _cache.has(key):
		return _cache[key]
	var im := Image.create_empty(max(1, text_width(s)), 8 if shadow else 7, false, Image.FORMAT_RGBA8)
	var src := _tinted(col)
	var sh := _tinted(INK)
	var x := 0
	for i in s.length():
		var g := _glyph(s[i])
		var r := Rect2i(int(g[0]), 0, int(g[1]), 7)
		if shadow:
			im.blend_rect(sh, r, Vector2i(x, 1))
		im.blend_rect(src, r, Vector2i(x, 0))
		x += int(g[1]) + 1
	var t := ImageTexture.create_from_image(im)
	if _cache.size() > 600:
		_cache.clear()
	_cache[key] = t
	return t


func wrap_text(s: String, max_w: int) -> Array:
	var lines := []
	var cur := ""
	for word in s.split(" ", false):
		var t: String = word if cur == "" else cur + " " + word
		if text_width(t) <= max_w:
			cur = t
		else:
			if cur != "":
				lines.append(cur)
			cur = word
	if cur != "":
		lines.append(cur)
	return lines


# ------------------------------------------------------------------ widgets
func _panel(parent: Control, pos: Vector2, size: Vector2, selected := false) -> NinePatchRect:
	var p := NinePatchRect.new()
	p.texture = tex("res://game/art/hud/panel9_sel.png" if selected else "res://game/art/hud/panel9.png")
	p.patch_margin_left = 3
	p.patch_margin_right = 3
	p.patch_margin_top = 3
	p.patch_margin_bottom = 3
	p.position = pos
	p.size = size
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(p)
	return p


func _rect(parent: Control, pos: Vector2, t: Texture2D) -> TextureRect:
	var r := TextureRect.new()
	r.texture = t
	r.stretch_mode = TextureRect.STRETCH_KEEP
	r.position = pos
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(r)
	return r


func _clear(c: Control) -> void:
	for ch in c.get_children():
		ch.queue_free()


func icon_tex(item: String) -> Texture2D:
	if item == "coins":
		return tex("res://game/art/hud/hud_coin.png")
	var p := "res://game/art/hud/icon_%s.png" % item
	return tex(p) if ResourceLoader.exists(p) else null


# ------------------------------------------------------------------ HUD: banner, season, clock, coins, toast
func banner(title: String, sub := "") -> void:
	_clear(banner_box)
	var tw := text_width(title)
	_panel(banner_box, Vector2.ZERO, Vector2(tw + 16, 16))
	_rect(banner_box, Vector2(8, 4), text_tex(title, CREAM))
	var line := ColorRect.new()
	line.color = GOLD
	line.position = Vector2(8, 12)
	line.size = Vector2(tw, 1)
	banner_box.add_child(line)
	if sub != "":
		var bg := ColorRect.new()
		bg.color = INK
		bg.position = Vector2(0, 16)
		bg.size = Vector2(text_width(sub) + 10, 10)
		banner_box.add_child(bg)
		_rect(banner_box, Vector2(5, 17), text_tex(sub, GOLD, false))
	banner_box.visible = true
	banner_box.modulate.a = 1.0
	banner_time = 3.0


func set_season(sname: String) -> void:
	badge.texture = tex("res://game/art/hud/season_%s.png" % sname)
	badge.position = Vector2(VIEW.x - 6 - badge.texture.get_width(), 6)


func _build_clock() -> void:
	var clock := Control.new()
	clock.position = Vector2(VIEW.x - 6 - 42, 24)
	a_tr.add_child(clock)
	_rect(clock, Vector2.ZERO, tex("res://game/art/hud/clock_panel.png"))
	clock_icon = _rect(clock, Vector2(5, 4), null)
	var atlas: Texture2D = tex("res://game/art/hud/clock_digits.png")
	for i in 5:
		var a := AtlasTexture.new()
		a.atlas = atlas
		a.region = Rect2(60 if i == 2 else 0, 0, 6, 9)
		_rect(clock, Vector2([13, 19, 25, 28, 34][i], 4), a)
		clock_digits.append(a)


func set_clock(hour: float, phase: String) -> void:
	var hh := int(hour)
	var mm := int((hour - hh) * 6.0) * 10
	for i in [0, 1, 3, 4]:
		var d: int = [hh / 10, hh % 10, 0, mm / 10, mm % 10][i]
		clock_digits[i].region = Rect2(d * 6, 0, 6, 9)
	clock_icon.texture = tex("res://game/art/hud/time_%s.png" % phase)


func set_coins(n: int) -> void:
	var t := text_tex(str(n), CREAM)
	coins_label.texture = t
	coins_label.position = Vector2(44 - t.get_width(), 4)


func toast(s: String, seconds := 3.5) -> void:
	var lines := wrap_text(s.to_upper(), 292)
	for i in 2:
		toast_lines[i].texture = text_tex(lines[i], CREAM if i == 0 else GOLD) if i < lines.size() else null
	toast_box.size.y = 28 if lines.size() > 1 else 18
	toast_box.position.y = VIEW.y - 6 - toast_box.size.y
	toast_box.visible = true
	toast_box.modulate.a = 1.0
	toast_time = seconds


func hide_toast() -> void:
	toast_time = 0.0
	toast_box.visible = false


func _process(delta: float) -> void:
	if toast_time > 0.0:
		toast_time -= delta
		toast_box.modulate.a = clamp(toast_time / 0.4, 0.0, 1.0)
		if toast_time <= 0.0:
			toast_box.visible = false
	if banner_time > 0.0:
		banner_time -= delta
		banner_box.modulate.a = clamp(banner_time / 0.5, 0.0, 1.0)
		if banner_time <= 0.0:
			banner_box.visible = false
	hint.visible = mode == "" and not toast_box.visible
	if box.visible and reveal < reveal_total:
		reveal = min(reveal_total, reveal + delta * TYPE_SPEED)
		_apply_reveal()
	box_next.visible = box.visible and mode == "say" and reveal >= reveal_total and int(Time.get_ticks_msec() / 350) % 2 == 0
	if map_box.visible and map_marker:
		map_marker.visible = int(Time.get_ticks_msec() / 300) % 3 != 0


# ------------------------------------------------------------------ dialogue box
func _show_box(who: String, lines: Array, icon := "", typewriter := true) -> void:
	hide_toast()
	box.visible = true
	name_box.visible = who != ""
	if who != "":
		name_label.texture = text_tex(who, GOLD)
		name_box.size.x = text_width(who) + 12
	var it := icon_tex(icon) if icon != "" else null
	box_icon.texture = it
	var x0 := 28 if it else 8
	box_full = []
	reveal_total = 0
	for i in 3:
		var r: TextureRect = box_lines[i]
		r.position.x = x0
		if i < lines.size():
			var t := text_tex(lines[i], CREAM)
			var a := AtlasTexture.new()
			a.atlas = t
			a.region = Rect2(0, 0, t.get_width(), t.get_height())
			r.texture = a
			box_full.append([t, char_xs(lines[i]), reveal_total])
			reveal_total += lines[i].length()
		else:
			r.texture = null
	reveal = 0.0 if (typewriter and (not autoplay or auto_delay > 0.4)) else float(reveal_total)
	_apply_reveal()


func _apply_reveal() -> void:
	for i in box_full.size():
		var t: Texture2D = box_full[i][0]
		var xs: Array = box_full[i][1]
		var start: int = box_full[i][2]
		var n := clampi(int(reveal) - start, 0, xs.size())
		var w: int = 0 if n == 0 else min(t.get_width(), int(xs[n - 1]))
		var a: AtlasTexture = box_lines[i].texture
		a.region = Rect2(0, 0, max(w, 0), t.get_height())
		box_lines[i].visible = w > 0


func _hide_box() -> void:
	box.visible = false
	name_box.visible = false


func say(who: String, s: String, icon := "") -> void:
	var lines := wrap_text(s.to_upper(), 272 if icon_tex(icon) else 292) if icon != "" else wrap_text(s.to_upper(), 292)
	var page := 0
	while page * 3 < max(1, lines.size()):
		_show_box(who, lines.slice(page * 3, page * 3 + 3), icon)
		mode = "say"
		if autoplay:
			while reveal < reveal_total:
				await get_tree().process_frame
			await get_tree().create_timer(auto_delay).timeout
		else:
			await _done
		page += 1
	_hide_box()
	mode = ""


func choose(prompt: String, options: Array) -> int:
	_show_box("", wrap_text(prompt.to_upper(), 292), "", false)
	_clear_choice()
	var w := 0
	for o in options:
		w = max(w, text_width(String(o).to_upper()))
	choice_box.size = Vector2(w + 24, 10 * options.size() + 10)
	choice_box.position = Vector2(VIEW.x - 8 - choice_box.size.x, box.position.y - 2 - choice_box.size.y)
	for i in options.size():
		var row := _rect(choice_box, Vector2(16, 6 + i * 10), text_tex(String(options[i]).to_upper(), CREAM))
		row.set_meta("row", true)
	choice_n = options.size()
	choice_idx = 0
	_place_choice_cursor()
	choice_box.visible = true
	mode = "choose"
	var r: int
	if autoplay:
		await get_tree().create_timer(auto_delay).timeout
		r = int(queue.pop_front()) if not queue.is_empty() else 0
	else:
		r = await _done
	choice_box.visible = false
	_hide_box()
	mode = ""
	return r


func _clear_choice() -> void:
	for c in choice_box.get_children():
		if c.has_meta("row"):
			c.queue_free()


func _place_choice_cursor() -> void:
	choice_cursor.position = Vector2(7, 6 + choice_idx * 10)


# ------------------------------------------------------------------ lists: shop, sell
func _open_list(title: String, entries: Array, kind: String) -> void:
	_clear(list_box)
	list_kind = kind
	list_entries = entries
	list_rows = []
	_rect(list_box, Vector2(8, 6), text_tex(title, GOLD))
	var cb := _rect(list_box, Vector2(0, 6), text_tex(str(story.coins), CREAM))
	cb.position.x = 292 - 8 - cb.texture.get_width()
	_rect(list_box, Vector2(cb.position.x - 11, 5), tex("res://game/art/hud/hud_coin.png"))
	for i in entries.size():
		var e: Dictionary = entries[i]
		var row := Control.new()
		row.position = Vector2(14, 20 + i * 16)
		list_box.add_child(row)
		if e["item"] != "":
			_rect(row, Vector2(0, 0), icon_tex(e["item"]))
			_rect(row, Vector2(20, 5), text_tex(story.item_name(e["item"]), CREAM))
			var pt := text_tex(str(int(e["price"])), GOLD)
			_rect(row, Vector2(262 - pt.get_width(), 5), pt)
			_rect(row, Vector2(250 - pt.get_width(), 4), tex("res://game/art/hud/hud_coin.png"))
		else:
			_rect(row, Vector2(20, 5), text_tex(e["label"], DIM))
		list_rows.append(row)
	list_box.size.y = 26 + entries.size() * 16
	list_box.visible = true
	list_idx = clampi(list_idx, 0, entries.size() - 1)
	_list_cursor()
	mode = "list"


func _list_cursor() -> void:
	for c in list_box.get_children():
		if c.has_meta("cursor"):
			c.queue_free()
	var cur := _rect(list_box, Vector2(6, 25 + list_idx * 16), tex("res://game/art/hud/cursor.png"))
	cur.set_meta("cursor", true)
	var e: Dictionary = list_entries[list_idx]
	if e["item"] != "":
		_show_box(story.item_name(e["item"]), wrap_text(String(story.C["items"][e["item"]]["desc"]), 292), "", false)
	else:
		_hide_box()


func _pick() -> int:
	mode = "list"
	if autoplay:
		await get_tree().create_timer(auto_delay).timeout
		var want = queue.pop_front() if not queue.is_empty() else "leave"
		for i in list_entries.size():
			if list_entries[i]["item"] == want:
				return i
		return -1
	return await _done


func shop(id: String) -> void:
	var titles := {"store": "HALVARD'S GOODS", "feathers": "FEATHERS AND BELLS", "charts": "CHARTS AND MAPS"}
	list_idx = 0
	while true:
		var entries: Array = story.shop_entries(id)
		var rows := entries.duplicate()
		rows.append({"item": "", "label": "LEAVE"})
		_open_list(titles.get(id, "SHOP"), rows, "shop")
		var i := await _pick()
		if i < 0 or i >= entries.size():
			break
		var e: Dictionary = entries[i]
		list_box.visible = false
		var yes := await choose("BUY %s FOR %d COINS?" % [story.item_name(e["item"]), int(e["price"])], ["YES", "NO"])
		if yes == 0:
			if story.buy(e):
				await say("", "BOUGHT %s!" % story.item_name(e["item"]), e["item"])
			else:
				await say("", story.text("not_enough"))
	list_box.visible = false
	_hide_box()
	mode = ""


func sell(buyer: String) -> void:
	list_idx = 0
	while true:
		var entries: Array = story.sell_entries(buyer)
		if entries.is_empty():
			await say("AMBROSE", story.text("nothing_to_sell"))
			break
		var rows := entries.duplicate()
		rows.append({"item": "", "label": "NOTHING TODAY"})
		_open_list("AMBROSE WILL PAY", rows, "sell")
		var i := await _pick()
		if i < 0 or i >= entries.size():
			break
		var e: Dictionary = entries[i]
		list_box.visible = false
		var yes := await choose("SELL %s FOR %d COINS?" % [story.item_name(e["item"]), int(e["price"])], ["YES", "NO"])
		if yes == 0:
			story.sell_item(e)
			await say("AMBROSE", "A FINE PIECE. PLEASURE DOING BUSINESS.")
	list_box.visible = false
	_hide_box()
	mode = ""


# ------------------------------------------------------------------ item list (I)
func open_inventory() -> void:
	_clear(list_box)
	inv_items = []
	for k in story.C["items"].keys():                     # content order: tools first, then the rest
		if story.has(k):
			inv_items.append(k)
	_rect(list_box, Vector2(8, 6), text_tex("ITEMS", GOLD))
	var cb := _rect(list_box, Vector2(0, 6), text_tex(str(story.coins), CREAM))
	cb.position.x = 292 - 8 - cb.texture.get_width()
	_rect(list_box, Vector2(cb.position.x - 11, 5), tex("res://game/art/hud/hud_coin.png"))
	var cols := 12
	for i in inv_items.size():
		var p := Vector2(10 + (i % cols) * 23, 20 + (i / cols) * 22)
		var cell := _panel(list_box, p, Vector2(22, 22))
		cell.set_meta("cell", i)
		_rect(cell, Vector2(3, 3), icon_tex(inv_items[i]))
		if story.count(inv_items[i]) > 1:
			_rect(cell, Vector2(14, 13), text_tex(str(story.count(inv_items[i])), CREAM))
	list_box.size.y = 28 + max(1, (inv_items.size() + cols - 1) / cols) * 22
	if inv_items.is_empty():
		_rect(list_box, Vector2(10, 22), text_tex("NOTHING YET.", DIM))
	list_box.visible = true
	list_idx = 0
	_inv_select()
	mode = "inv"


func _inv_select() -> void:
	for c in list_box.get_children():
		if c.has_meta("cell"):
			c.texture = tex("res://game/art/hud/panel9_sel.png" if c.get_meta("cell") == list_idx else "res://game/art/hud/panel9.png")
	if inv_items.is_empty():
		_hide_box()
		return
	var k: String = inv_items[list_idx]
	_show_box(story.item_name(k), wrap_text(String(story.C["items"][k]["desc"]), 292), "", false)


func close_menus() -> void:
	list_box.visible = false
	map_box.visible = false
	help_box.visible = false
	_hide_box()
	mode = ""


# ------------------------------------------------------------------ world map (M)
func open_map() -> void:
	## the world map: what you have found so far, where you are, and a cursor to look around (arrows or mouse)
	_clear(map_box)
	var open: bool = main.east_revealed()
	_rect(map_box, Vector2(6, 6), tex("res://game/art/hud/worldmap_%s.png" % ("open" if open else "fog")))
	var placed: Array = []
	var places: Array = main.map_places()
	for p in places:
		var ic := _rect(map_box, Vector2(6, 6) + p["px"] - Vector2(3, 3), tex("res://game/art/hud/mapicon_%s.png" % p["icon"]))
		ic.set_meta("place", true)
		placed.append(Rect2(ic.position, Vector2(7, 7)))
	for p in places:
		if not p["label"]:
			continue
		var t := text_tex(p["name"], CREAM)
		var px: Vector2 = Vector2(6, 6) + p["px"]
		var w := t.get_width()
		var spots := [Vector2(px.x + 5, px.y - 4), Vector2(px.x - 5 - w, px.y - 4), Vector2(px.x - w / 2.0, px.y + 5),
			Vector2(px.x - w / 2.0, px.y - 13), Vector2(px.x + 5, px.y + 5), Vector2(px.x - 5 - w, px.y + 5),
			Vector2(px.x + 5, px.y - 13), Vector2(px.x - 5 - w, px.y - 13), Vector2(px.x - w / 2.0, px.y + 13)]
		var best: Vector2 = spots[0]
		for sp in spots:
			var r := Rect2(sp, Vector2(w, 8))
			var free: bool = r.position.x >= 6 and r.end.x <= 294 and r.position.y >= 6 and r.end.y <= 150
			for o in placed:
				if r.grow(1).intersects(o):
					free = false
			if free:
				best = sp
				break
		placed.append(Rect2(best, Vector2(w, 8)))
		var plate := ColorRect.new()                      # a dark plate so names read on snow and sand
		plate.color = INK
		plate.position = best - Vector2(1, 1)
		plate.size = Vector2(w + 2, 10)
		map_box.add_child(plate)
		_rect(map_box, best, t)
	map_marker = Control.new()
	map_marker.position = Vector2(6, 6) + main.map_marker()
	map_box.add_child(map_marker)
	var dot := ColorRect.new()
	dot.color = Color("B8483A")
	dot.position = Vector2(-2, -2)
	dot.size = Vector2(5, 5)
	map_marker.add_child(dot)
	var dot2 := ColorRect.new()
	dot2.color = CREAM
	dot2.position = Vector2(-1, -1)
	dot2.size = Vector2(3, 3)
	map_marker.add_child(dot2)
	map_cursor = _rect(map_box, Vector2.ZERO, tex("res://game/art/hud/map_cursor.png"))
	map_cursor_px = main.map_marker()
	map_info_label = _rect(map_box, Vector2(8, 152), null)
	var hint2 := text_tex("ARROWS / CLICK: LOOK   SPACE: READ   M: CLOSE", DIM, false)
	_rect(map_box, Vector2(292 - hint2.get_width(), 162), hint2)
	_map_cursor_moved()
	map_box.visible = true
	mode = "map"


func _map_cursor_moved() -> void:
	map_cursor_px = map_cursor_px.clamp(Vector2(1, 1), Vector2(286, 142))
	map_cursor.position = Vector2(6, 6) + map_cursor_px - Vector2(4, 4)
	var info: Array = main.map_info(map_cursor_px)
	var near := ""
	if map_cursor_px.distance_to(main.map_marker()) < 4.0:
		near = "YOU ARE HERE: "
	var title: String = near + String(info[0])
	map_info_label.texture = text_tex(title, GOLD) if title != "" else null


func map_click(p: Vector2) -> void:
	## mouse: p is a window position
	if mode == "map_text":
		input("confirm")
		return
	map_cursor_px = to_hud(p) - a_mid.position - map_box.position - Vector2(6, 6)
	_map_cursor_moved()
	input("confirm")


func _map_read() -> void:
	var info: Array = main.map_info(map_cursor_px)
	var text: String = info[1] if String(info[1]) != "" else String(info[0])
	if text == "":
		return
	_show_box("", wrap_text(text.to_upper(), 292).slice(0, 3), "", false)
	mode = "map_text"


func show_view(t: Texture2D, caption: String) -> void:
	## through the telescope: a round view of somewhere far away
	view_box.visible = true
	view_img.texture = t
	view_img.position = ((view - t.get_size()) / 2.0 - Vector2(0, 18)).floor()
	var lines := wrap_text(caption.to_upper(), 292)
	var page := 0
	while page * 3 < max(1, lines.size()):
		_show_box("", lines.slice(page * 3, page * 3 + 3), "", true)
		mode = "say"
		if autoplay:
			while reveal < reveal_total:
				await get_tree().process_frame
			await get_tree().create_timer(max(auto_delay, 0.3)).timeout
		else:
			await _done
		page += 1
	_hide_box()
	view_box.visible = false
	mode = ""


# ------------------------------------------------------------------ help (H)
func open_help() -> void:
	_clear(help_box)
	var lines := ["CONTROLS", "ARROWS / WASD   MOVE", "SHIFT           RUN", "SPACE / Z       TALK, READ, USE, SURF",
		"X / ESC         BACK", "I               ITEMS", "M               WORLD MAP", "C               COMPANION SHOW / HIDE",
		"E / R           POUCH / WALKING STICK", "F               CALL THE DRAGON (DRAGON BAND)",
		"T               NEXT TIME OF DAY", "TAB / 1-4       SEASON",
		"F9              NEW GAME", "F1              DEBUG SLIDERS", "H               CLOSE HELP"]
	var w := 0
	for l in lines:
		w = max(w, text_width(l))
	help_box.size = Vector2(w + 16, 12 + 10 * lines.size())
	help_box.position = (VIEW - help_box.size) / 2.0
	for i in lines.size():
		_rect(help_box, Vector2(8, 6 + i * 10), text_tex(lines[i], GOLD if i == 0 else CREAM))
	help_box.visible = true
	mode = "help"


# ------------------------------------------------------------------ fades (doors, boats, the erne)
func fade(to: float, secs := 0.18) -> void:
	var tw := create_tween()
	tw.tween_property(fader, "modulate:a", to, secs)
	await tw.finished


# ------------------------------------------------------------------ input while a menu or text is open
func input(a: String) -> void:
	match mode:
		"say":
			if a in ["confirm", "cancel"]:
				if reveal < reveal_total:
					reveal = reveal_total
					_apply_reveal()
				else:
					_done.emit(0)
		"choose":
			if a == "up":
				choice_idx = (choice_idx + choice_n - 1) % choice_n
				_place_choice_cursor()
			elif a == "down":
				choice_idx = (choice_idx + 1) % choice_n
				_place_choice_cursor()
			elif a == "confirm":
				_done.emit(choice_idx)
			elif a == "cancel":
				_done.emit(choice_n - 1 if choice_n > 1 else -1)
		"list":
			if a == "up":
				list_idx = (list_idx + list_entries.size() - 1) % list_entries.size()
				_list_cursor()
			elif a == "down":
				list_idx = (list_idx + 1) % list_entries.size()
				_list_cursor()
			elif a == "confirm":
				_done.emit(list_idx)
			elif a == "cancel":
				_done.emit(-1)
		"inv":
			if inv_items.size() > 0 and a in ["left", "right", "up", "down"]:
				var step: int = {"left": -1, "right": 1, "up": -12, "down": 12}[a]
				list_idx = clampi(list_idx + step, 0, inv_items.size() - 1)
				_inv_select()
			elif a in ["cancel", "items", "confirm"]:
				close_menus()
		"map":
			if a in ["cancel", "map"]:
				close_menus()
			elif a == "confirm":
				_map_read()
			elif a in ["left", "right", "up", "down"]:
				map_cursor_px += {"left": Vector2(-4, 0), "right": Vector2(4, 0), "up": Vector2(0, -4), "down": Vector2(0, 4)}[a]
				_map_cursor_moved()
		"map_text":
			if a in ["confirm", "cancel", "map"]:
				_hide_box()
				mode = "map"
		"help":
			if a in ["cancel", "help", "confirm"]:
				close_menus()
