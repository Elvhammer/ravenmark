extends Node
## Scripted playthrough for testing without a person at the keyboard.
##   godot --path . -- --autotest=shots --out=/some/dir      (checks + screenshots of every feature)
##   godot --path . --write-movie tour.avi -- --autotest=tour (a recorded tour of the wider world)
##   godot --path . --write-movie day.avi -- --autotest=daylapse
## Text boxes advance on their own (ui.autoplay); answers to choices and shop picks come from ui.queue.

var main
var story
var ui
var out_dir := "user://"
var log_lines: PackedStringArray = []
var fails := 0


func run(m, mode: String) -> void:
	main = m
	story = m.story
	ui = m.ui
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	ui.autoplay = true
	main.seasons_running = false
	main.time_running = false
	main.set_time(10.0)
	await _wait(0.6)
	if mode == "shots":
		await _shots()
		await _daynight_shots()
		await _part2()
		await _second_run()
		await _part3()
	elif mode == "part3":
		await _part3()
	elif mode == "daylapse":
		await _daylapse()
	else:
		await _tour()
	log_lines.append("%d checks failed" % fails)
	print("%d checks failed" % fails)
	var f := FileAccess.open(out_dir.path_join("autotest_log.txt"), FileAccess.WRITE)
	if f:
		f.store_string("\n".join(log_lines))
	get_tree().quit()


# ------------------------------------------------------------------ helpers
func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _settle() -> void:
	var guard := 0
	while (main.player.moving or main.busy()) and guard < 2000:
		guard += 1
		await get_tree().process_frame


func _walk(dir: Vector2i, n: int) -> void:
	for i in n:
		await _settle()
		main.player.step(dir)
		await get_tree().process_frame
	await _settle()


func _teleport(t: Vector2i, facing := Vector2i.DOWN, surfing := false) -> void:
	main.player.surfing = surfing
	main.player.facing = facing
	main.player.place(t)
	main._place_companion()
	main.camera.position = main.player.position
	main.camera.reset_smoothing()
	await _wait(0.3)
	await _settle()


func _go(map_id: String, t: Vector2i, facing := Vector2i.DOWN) -> void:
	main.load_map(map_id, t, facing)
	await _wait(0.3)
	await _settle()


func _act(answers := []) -> void:
	ui.queue = answers.duplicate()
	main.player.action()
	await get_tree().process_frame
	await _settle()
	await _wait(0.05)
	await _settle()


func _check(label: String, ok: bool) -> void:
	if not ok:
		fails += 1
	log_lines.append(("PASS  " if ok else "FAIL  ") + label)
	print(("PASS  " if ok else "FAIL  ") + label)


func _shot(shot_name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return                                          # nothing is drawn without a display
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join(shot_name + ".png"))
	log_lines.append("shot  " + shot_name)


func _shot_talking(shot_name: String, answers := [], wait := 0.45) -> void:
	## act, keep the first text box up long enough for a screenshot, then let the rest play out
	ui.auto_delay = 1.2
	ui.queue = answers.duplicate()
	main.player.action()
	await _wait(wait)
	await _shot(shot_name)
	ui.auto_delay = 0.05
	await _settle()
	await _wait(0.05)
	await _settle()


func _npc_here(id: String) -> bool:
	for e in main.ents:
		if e["type"] == "npc" and e["id"] == id:
			return true
	return false


# ------------------------------------------------------------------ part 1 (the original prototype checks)
func _shots() -> void:
	story.give("otter_stick")                            # part 1 tests the original prototype: otter from the start
	main.day = 1                                         # (on day 1 the ferry would be moored off the Keelvik pier)
	main.refresh_entities(true)
	await _wait(0.4)
	await _shot("01_keelvik_summer")
	ui.hide_toast()
	var before: Vector2i = main.player.tile
	await _walk(Vector2i.LEFT, 6)
	_check("walk west 6 tiles", main.player.tile == before + Vector2i(-6, 0))
	await _teleport(Vector2i(20, 19), Vector2i.RIGHT)
	await _walk(Vector2i.RIGHT, 2)
	await _wait(0.5)
	await _shot("02_lauvdal_summer")
	await _teleport(Vector2i(20, 19), Vector2i.UP)
	var t0: Vector2i = main.player.tile
	await _walk(Vector2i.DOWN, 6)
	_check("forest blocks walking south out of Lauvdal", main.player.tile.y < t0.y + 6)
	await _teleport(Vector2i(60, 32), Vector2i.DOWN)
	await _walk(Vector2i.DOWN, 2)
	_check("hop down the ledge (lands 2 tiles below it)", main.player.tile == Vector2i(60, 35))
	await _walk(Vector2i.UP, 1)
	_check("cannot climb back up the ledge", main.player.tile == Vector2i(60, 35))
	await _shot("03_sule_ness_ledges")
	await _teleport(Vector2i(71, 20), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	_check("Otter Stick: surf off the pier", main.player.surfing and main.player.tile == Vector2i(72, 20))
	await _walk(Vector2i.RIGHT, 3)
	await _wait(0.4)
	await _shot("04_surfing_otter")
	await _teleport(Vector2i(80, 13), Vector2i.UP, true)
	await _walk(Vector2i.UP, 1)
	_check("otter refuses the cold Rimestream", main.player.tile == Vector2i(80, 13))
	await _wait(0.3)
	await _shot("05_otter_refuses_cold")
	story.give("seal_flute")
	await _walk(Vector2i.UP, 2)
	_check("seal swims in cold water", main.player.tile == Vector2i(80, 11) and main.player.mount_kind == "seal")
	await _wait(0.4)
	await _shot("06_seal_in_cold_water")
	ui.hide_toast()
	main.set_season(2)
	await _teleport(Vector2i(24, 19), Vector2i.DOWN)
	await _shot("07_lauvdal_autumn")
	main.set_season(3)
	await _teleport(Vector2i(40, 19), Vector2i.UP)
	await _walk(Vector2i.UP, 3)
	_check("walk onto the frozen river in winter", main.player.tile == Vector2i(40, 16))
	await _shot("08_frozen_river_winter")
	await _teleport(Vector2i(29, 16), Vector2i.UP)
	await _walk(Vector2i.UP, 2)
	await _act()
	_check("open the chest on Damholm (only reachable over ice)", story.has("coin"))
	await _shot("09_damholm_chest")
	main.set_season(0)
	await _teleport(Vector2i(55, 22), Vector2i.DOWN)
	await _shot("10_keelvik_spring")
	main.set_season(3)
	await _wait(0.2)
	await _shot("11_keelvik_winter")
	await _teleport(Vector2i(40, 16), Vector2i.UP)
	main.set_season(0)
	_check("thaw under the player: switches to surfing", main.player.surfing)
	main.player.surfing = false
	main.set_season(1)


func _daynight_shots() -> void:
	ui.hide_toast()
	await _teleport(Vector2i(56, 13), Vector2i.DOWN)
	for pair in [[5.5, "12_keelvik_dawn"], [12.0, "13_keelvik_day"], [20.5, "14_keelvik_dusk"], [0.0, "15_keelvik_night"]]:
		main.set_time(pair[0])
		await _wait(0.15)
		await _shot(pair[1])
	_check("lights glow at night", main.light_amount() == 1.0 and main.lit_sprites[0].modulate.a == 1.0)
	main.set_time(12.0)
	_check("lights are off by day", main.light_amount() == 0.0)
	main.set_time(23.0)
	main.next_phase()
	_check("T jumps from night to dawn (04:00)", is_equal_approx(main.hour, 4.0))
	main.set_time(0.0)
	await _teleport(Vector2i(76, 50), Vector2i.RIGHT)
	await _shot("16_lighthouse_night")
	main.set_season(3)
	await _teleport(Vector2i(55, 22), Vector2i.DOWN)
	main.set_time(21.0)
	await _wait(0.15)
	await _shot("17_keelvik_winter_evening")
	main.set_season(1)
	main.set_time(23.5)
	main.time_running = true
	main.seasons_running = true
	main.day = 1
	await _wait(0.4)
	main.hours_per_second = 4.0
	await _wait(0.3)
	main.hours_per_second = 0.0
	_check("midnight after 2 days advances the season", main.season == 2)
	main.time_running = false
	main.seasons_running = false
	main.hours_per_second = 1.0 / 30.0
	main.set_season(1)
	main.day = 0


# ------------------------------------------------------------------ part 2, first playthrough (fox, forest caretaker)
func _part2() -> void:
	main.new_game()
	ui.hide_toast()
	main.set_time(10.0)
	await _wait(0.3)
	# --- doors and interiors, NPC memory, a lost item, a back room that opens later
	await _teleport(Vector2i(49, 10), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("walk through the inn door into the inn", main.map_id == "inn" and main.player.tile == Vector2i(6, 7))
	await _shot("20_inn")
	await _go("inn", Vector2i(2, 4), Vector2i.UP)
	await _shot_talking("21_talk_across_the_counter")
	_check("talk to Marit across the counter (she remembers)", int(story.mem_get("marit")["talks"]) == 1)
	await _go("inn", Vector2i(11, 2), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("cellar door is locked without the key", main.map_id == "inn")
	await _go("overworld", Vector2i(24, 19), Vector2i.UP)
	await _shot("22_ring_sparkle")
	await _walk(Vector2i.UP, 2)
	_check("find Marit's lost ring (sparkle on the river bank)", story.has("ring"))
	await _go("inn", Vector2i(2, 4), Vector2i.UP)
	await _act()
	_check("return the ring: Marit gives the cellar key", story.has("cellar_key") and not story.has("ring"))
	await _go("inn", Vector2i(11, 2), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("the cellar opens with the key", main.map_id == "cellar")
	await _go("cellar", Vector2i(4, 5), Vector2i.UP)
	await _act()
	await _go("cellar", Vector2i(6, 3), Vector2i.UP)
	await _shot("23_cellar")
	await _act()
	_check("the cellar hides an old ship's bell (a museum piece)", story.has("ship_bell"))
	story.give("pickaxe")                                # (from Gerda in Copperhavn: see part 3)
	# --- the dark cave
	await _go("overworld", Vector2i(49, 52), Vector2i.LEFT)
	await _shot("24_cracked_rock")
	await _walk(Vector2i.LEFT, 1)
	_check("cracked rock blocks the cave mouth", main.player.tile == Vector2i(49, 52))
	await _act()
	_check("the pickaxe breaks the rock for good", story.cleared.has("rock_cave"))
	await _walk(Vector2i.LEFT, 2)
	_check("walk into the Sule Ness cave", main.map_id == "cave" and main.player.tile == Vector2i(37, 12))
	await _walk(Vector2i.LEFT, 6)
	_check("without a light you cannot go deep into the cave", main.player.tile.x >= 34)
	await _shot("25_cave_dark")
	# --- economy: tide islet chest at dawn, shop, everyday item, NPC favour
	main.set_time(5.0)
	await _go("overworld", Vector2i(76, 35), Vector2i.RIGHT)
	await _shot("26_low_tide_sandbar")
	await _walk(Vector2i.RIGHT, 4)
	_check("walk the sandbar to the tide islet at dawn", main.player.tile == Vector2i(80, 35))
	await _teleport(Vector2i(81, 35), Vector2i.UP)
	var c0: int = story.coins
	await _act()
	_check("tide islet chest: 800 coins", story.coins == c0 + 800)
	main.set_time(7.5)
	await _settle()
	_check("the tide comes in: you wade back to the beach", main.player.tile == Vector2i(76, 35))
	await _teleport(Vector2i(74, 36), Vector2i.LEFT)
	main.set_time(12.0)
	await _teleport(Vector2i(76, 35), Vector2i.RIGHT)
	await _walk(Vector2i.RIGHT, 2)
	_check("at high tide the sandbar is under water", main.player.tile == Vector2i(76, 35))
	await _go("overworld", Vector2i(62, 10), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("enter Halvard's store", main.map_id == "store")
	await _go("store", Vector2i(4, 4), Vector2i.UP)
	c0 = story.coins
	ui.auto_delay = 0.6
	ui.queue = ["lamp_oil", 0, "leave"]
	main.player.action()
	await _wait(0.95)
	await _shot("27_shop")
	ui.auto_delay = 0.05
	await _settle()
	_check("buy lamp oil (4) at the store", story.has("lamp_oil") and story.coins == c0 - 4)
	story.give("axe")                                    # (from the stump north of the river: see part 3)
	_check("ship plans are not for sale yet", not _shop_has("store", "ship_plans"))
	await _go("overworld", Vector2i(77, 52), Vector2i.UP)
	await _act()
	_check("favour: lamp oil for Ole, who gives his lantern", story.has("lantern") and not story.has("lamp_oil"))
	await _go("cave", Vector2i(37, 12), Vector2i.LEFT)
	await _walk(Vector2i.LEFT, 6)
	_check("with the lantern the cave can be explored", main.player.tile == Vector2i(31, 12))
	await _shot("28_cave_lantern")
	await _teleport(Vector2i(23, 3), Vector2i.UP)
	await _act()
	_check("the cave hides the Amber Heart (rare item)", story.has("amber_heart"))
	await _teleport(Vector2i(26, 3), Vector2i.UP)
	c0 = story.coins
	await _act()
	_check("big coin reward in the cave (5000)", story.coins == c0 + 5000 and story.flags.has("cave_treasure"))
	_check("the store now stocks the 25000-coin ship plans", _shop_has("store", "ship_plans"))
	await _teleport(Vector2i(5, 1), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("the tunnel leads up to the Moonlit Grove", main.map_id == "overworld" and main.player.tile == Vector2i(28, 31))
	# --- axe: a permanent shortcut
	await _go("overworld", Vector2i(22, 25), Vector2i.DOWN)
	await _walk(Vector2i.DOWN, 1)
	_check("a young tree blocks the grove path", main.player.tile == Vector2i(22, 25))
	await _shot("29_sapling")
	await _act()
	await _walk(Vector2i.DOWN, 2)
	await _act()
	await _walk(Vector2i.DOWN, 1)
	_check("the axe clears the fallen trees for good", main.player.tile == Vector2i(22, 28) and story.cleared.has("tree_grove")
		and story.cleared.has("tree_grove2"))
	# --- time-specific NPCs and places
	main.set_time(12.0)
	_check("Selma is not in the grove by day", not _npc_on("selma", "overworld"))
	main.set_time(23.0)
	_check("Selma appears in the Moonlit Grove at night", _npc_on("selma", "overworld"))
	await _go("overworld", Vector2i(24, 36), Vector2i.UP)
	await _shot_talking("30_moonlit_grove_selma")
	main.day = 1
	await _act()
	await _act()
	_check("Selma gives a moonstone on a second night", story.has("moonstone"))
	main.day = 0
	main.set_time(21.0)
	_check("the night market opens after dark", _npc_on("ingrid", "overworld") and _npc_on("joar", "overworld"))
	await _go("overworld", Vector2i(57, 24), Vector2i.UP)
	await _shot("31_night_market")
	ui.queue = ["moon_tea", 0, "leave"]
	await _act(["moon_tea", 0, "leave"])
	_check("buy moon tea across the market stall", story.has("moon_tea"))
	ui.queue = []
	await _go("overworld", Vector2i(61, 24), Vector2i.UP)
	await _act(["sea_chart", 0, "leave"])
	_check("buy a sea chart at Joar's stall", story.has("sea_chart"))
	main.set_time(12.0)
	_check("the market is gone by day", not _npc_on("ingrid", "overworld"))
	# --- rare wanderer who buys rare things
	story.force_rare.erase("collector")
	var seen := 0
	for d in 60:
		main.day = d
		if _npc_on("collector", "overworld") or _npc_on("collector", "inn"):
			seen += 1
	_check("Ambrose the collector is rare (%d of 60 days)" % seen, seen > 3 and seen < 25)
	main.day = 0
	story.force_rare["collector"] = 1
	story.give("coin")                                   # the Damholm coin from part 1 (winter only)
	await _go("overworld", Vector2i(27, 22), Vector2i.UP)
	c0 = story.coins
	await _act(["coin", 0, "moonstone", 0, "leave"])
	_check("sell the old coin (1200) and the moonstone (700) to Ambrose", story.coins == c0 + 1900 and not story.has("coin"))
	story.force_rare.erase("collector")
	# --- a recurring character with a small story
	await _go("overworld", Vector2i(12, 21), Vector2i.UP)
	await _act()
	_check("Sigve tells his story and moves on (stage 1)", int(story.mem_get("sigve")["stage"]) == 1)
	await _go("inn", Vector2i(10, 5), Vector2i.UP)
	_check("Sigve is now resting at the inn", _npc_here("sigve_1"))
	await _act()
	await _go("overworld", Vector2i(78, 27), Vector2i.RIGHT)
	await _act()
	_check("Liv hands over the tern plank", story.has("tern_plank"))
	await _go("inn", Vector2i(10, 5), Vector2i.UP)
	await _act()
	await _go("overworld", Vector2i(73, 50), Vector2i.UP)
	_check("Sigve went out to Sule Ness", _npc_here("sigve_2"))
	c0 = story.coins
	await _act()
	_check("Sigve's thanks: his brother's compass and 300 coins", story.has("compass") and story.coins == c0 + 300)
	await _go("workshop", Vector2i(9, 6), Vector2i.UP)
	_check("Sigve settles down in Eirik's workshop", _npc_here("sigve_3"))
	# --- gifts after repeated visits
	await _go("overworld", Vector2i(78, 27), Vector2i.RIGHT)
	for d in [1, 2]:
		main.day = d
		await _act()
	_check("Liv gives smoked fish after visits on three days", story.has("smoked_fish"))
	await _go("inn", Vector2i(2, 4), Vector2i.UP)
	for i in 3:
		await _act()
	_check("Marit gives bread after four talks", story.has("bread"))
	main.day = 0
	# --- FD2: the fox
	await _go("overworld", Vector2i(38, 22), Vector2i.UP)
	await _act([0, 1])
	_check("saying NO keeps the choice open", story.companion == "")
	await _act([0, 0])
	_check("FD2: the fox kit joins you", story.companion == "fox" and main.companion.visible)
	await _teleport(Vector2i(40, 20), Vector2i.RIGHT)
	await _walk(Vector2i.RIGHT, 3)
	_check("the fox follows one tile behind", main.companion.tile == Vector2i(42, 20))
	await _shot("32_fox_follows")
	await _go("overworld", Vector2i(6, 17), Vector2i.LEFT)
	main.toggle_companion()
	_check("C hides the fox", not main.companion.visible)
	c0 = story.coins
	await _walk(Vector2i.LEFT, 1)
	await _settle()
	await _wait(1.3)
	await _settle()
	_check("a hidden fox still sniffs out buried coins (500)", story.coins == c0 + 500 and story.found.has("s_pouch"))
	main.toggle_companion()
	await _go("overworld", Vector2i(73, 33), Vector2i.UP)
	await _shot("33_fox_digs")
	await _walk(Vector2i.UP, 1)
	await _wait(1.3)
	await _settle()
	_check("the fox digs up Liv's lost knife", story.has("knife"))
	await _go("overworld", Vector2i(78, 27), Vector2i.RIGHT)
	await _act()
	_check("return the knife: Liv's lucky hook", story.has("lucky_hook") and not story.has("knife"))
	# --- FD1: the Amber Heart goes to the forest caretaker
	await _go("overworld", Vector2i(7, 22), Vector2i.UP)
	await _act([1])
	_check("declining keeps the Amber Heart", story.has("amber_heart") and story.fd1 == "")
	await _act([0])
	_check("FD1: the Amber Heart goes to Tove", story.fd1 == "caretaker" and not story.has("amber_heart"))
	await _go("overworld", Vector2i(15, 36), Vector2i.LEFT)
	await _walk(Vector2i.LEFT, 1)
	await _walk(Vector2i.DOWN, 2)
	await _walk(Vector2i.LEFT, 1)
	await _walk(Vector2i.DOWN, 2)
	_check("the thicket has parted: the trail to Mossholt is open", main.player.tile.y >= 39)
	await _go("overworld", Vector2i(8, 48), Vector2i.UP)
	await _shot("34_mossholt")
	await _act()
	await _act()
	_check("Arne in Mossholt carves an owl for you", story.has("carving"))
	_check("Fyrholm stays closed (Ole has no amber)", not _npc_on("brit", "overworld"))
	# --- world map, items, lights indoors, saving
	main.set_time(12.0)
	await _go("overworld", Vector2i(55, 22), Vector2i.DOWN)
	main.ui.open_map()
	await _wait(0.2)
	await _shot("35_world_map")
	var mk: Vector2 = main.map_marker()
	_check("world map marker is inside the map", mk.x > 0 and mk.x < 288 and mk.y > 0 and mk.y < 144)
	ui.close_menus()
	ui.open_inventory()
	await _wait(0.2)
	await _shot("36_items")
	ui.close_menus()
	main.set_time(22.0)
	await _go("inn", Vector2i(6, 6), Vector2i.UP)
	await _wait(0.2)
	await _shot("37_inn_evening")
	_check("the inn fireplace is lit", main.lit_sprites.size() > 0 and main.lit_sprites[0].modulate.a > 0.9)
	var d: Dictionary = JSON.parse_string(JSON.stringify(story.to_save()))
	var coins_before: int = story.coins
	story.coins = 0
	story.from_save(d)
	_check("save data round-trips (coins, items, memory)", story.coins == coins_before and story.has("lucky_hook")
		and int(story.mem_get("sigve")["stage"]) == 3)
	main.set_time(12.0)


func _npc_on(id: String, map_id: String) -> bool:
	for pair in story.npcs_on(map_id):
		if pair[0]["id"] == id:
			return true
	return false


func _shop_has(shop: String, item: String) -> bool:
	for e in story.shop_entries(shop):
		if e["item"] == item:
			return true
	return false


# ------------------------------------------------------------------ part 2, second playthrough (owl, lighthouse keeper)
func _second_run() -> void:
	main.new_game()
	ui.hide_toast()
	main.set_time(10.0)
	await _go("overworld", Vector2i(38, 22), Vector2i.UP)
	await _act([1, 0])
	_check("FD2: the owlet joins you instead", story.companion == "owl")
	await _shot("40_owl_and_pen")
	await _go("overworld", Vector2i(38, 13), Vector2i.UP)
	await _wait(1.0)
	await _settle()
	_check("the owl reveals a hidden way through the hedge", story.cleared.has("hedge_hollow"))
	await _walk(Vector2i.UP, 2)
	await _shot("41_owl_hidden_way")
	await _walk(Vector2i.UP, 2)
	await _teleport(Vector2i(39, 9), Vector2i.UP)
	var c0: int = story.coins
	await _act()
	_check("Owl's Hollow chest (500)", story.coins == c0 + 500)
	await _go("overworld", Vector2i(3, 18), Vector2i.UP)
	await _wait(1.0)
	await _settle()
	_check("the owl cannot dig (the fox's pouch stays hidden)", not story.found.has("s_pouch"))
	story.give("amber_heart")
	await _go("overworld", Vector2i(77, 52), Vector2i.UP)
	await _act([0])
	_check("FD1: the Amber Heart goes to Ole instead", story.fd1 == "keeper")
	await _act([0])
	await _settle()
	_check("Ole rows you to Fyrholm", main.player.tile == Vector2i(85, 52))
	await _shot("42_fyrholm")
	_check("Brit lives on Fyrholm", _npc_here("brit"))
	await _teleport(Vector2i(86, 54), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("sea glass in the Fyrholm tide pools", story.has("sea_glass"))
	await _teleport(Vector2i(85, 53), Vector2i.LEFT)
	await _act([0])
	await _settle()
	_check("the boat takes you back to Sule Ness", main.player.tile == Vector2i(78, 53))
	_check("Mossholt stays closed (no amber for the forest)", not story.gates.has("mossholt"))
	# --- the Bird Bell: an extremely expensive item that hints at the future
	story.add_coins(9000)
	main.set_time(21.0)
	await _go("overworld", Vector2i(57, 24), Vector2i.UP)
	await _act(["dragon_scale", 0, "leave"])
	_check("buy the Dragon Scale (9000), a hint of things to come", story.has("dragon_scale"))
	story.give("bird_bell")                              # (deep in the Sule Ness cave: see part 3)
	main.set_time(12.0)
	await _go("overworld", Vector2i(17, 7), Vector2i.UP)
	ui.queue = []
	main.player.action()
	await _wait(1.6)
	await _shot("43_erne_flight")
	await _settle()
	_check("the great erne carries you over the ravine", main.player.tile == Vector2i(17, 1))
	await _teleport(Vector2i(20, 1), Vector2i.RIGHT)
	c0 = story.coins
	await _act()
	_check("Erne Cliff: the old watch's paychest (3000)", story.coins == c0 + 3000)
	await _shot("44_erne_cliff")
	await _teleport(Vector2i(17, 1), Vector2i.DOWN)
	main.player.action()
	await _wait(0.4)
	await _settle()
	_check("and back across", main.player.tile == Vector2i(17, 7))


func _ent_type(t: String) -> bool:
	for e in main.ents:
		if e["type"] == t:
			return true
	return false


func _exhibit_shown(item: String) -> bool:
	for e in main.ents:
		if e["type"] == "exhibit" and e["data"]["item"] == item:
			return e["node"] != null
	return false


# ------------------------------------------------------------------ part 3: the whole progression, in order
func _part3() -> void:
	main.new_game()
	ui.hide_toast()
	main.set_time(10.0)
	main.day = 0
	await _wait(0.3)
	_check("a new game starts with no traversal items", story.items.is_empty())
	var oi: Array = main.map_info(Vector2(150, 66))
	_check("the world map: the eastern ocean is a mystery", oi[0] == "THE EASTERN OCEAN" and String(oi[1]).begins_with("THE EASTERN OCEAN. NO CHART"))
	_check("the world map: unvisited places have no name", main.map_info(main.map_px("north", Vector2(39, 26)))[0] == "???")
	main.ui.open_map()
	await _wait(0.2)
	await _shot("49_world_map_at_the_start")
	main.ui.input("right")
	_check("the map cursor moves", main.ui.map_cursor_px != main.map_marker())
	ui.close_menus()
	# --- stage 1: towns and forests -> the Axe
	await _go("overworld", Vector2i(75, 30), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	_check("without the Otter Stick you cannot swim", not main.player.surfing)
	await _go("overworld", Vector2i(22, 25), Vector2i.DOWN)
	await _walk(Vector2i.DOWN, 1)
	await _act()
	_check("fallen trees block the way to the Moonlit Grove", main.player.tile == Vector2i(22, 25) and not story.cleared.has("tree_grove"))
	await _go("overworld", Vector2i(16, 8), Vector2i.UP)
	await _shot("50_axe_in_the_stump")
	await _act()
	_check("stage 1: Tove's old axe, stuck in a stump north of the river", story.has("axe"))
	# --- stage 2: clear the fallen trees -> the Otter Stick
	await _go("overworld", Vector2i(22, 25), Vector2i.DOWN)
	await _act()
	await _walk(Vector2i.DOWN, 2)
	await _act()
	await _walk(Vector2i.DOWN, 1)
	_check("the axe clears both fallen trees", story.cleared.has("tree_grove2") and main.player.tile == Vector2i(22, 28))
	await _go("overworld", Vector2i(24, 32), Vector2i.RIGHT)
	await _act()
	_check("stage 2: Edvin gives you the Otter Stick", story.has("otter_stick"))
	await _go("overworld", Vector2i(75, 30), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	_check("now the otter carries you", main.player.surfing and main.player.mount_kind == "otter")
	# --- stage 3: across the water -> Copperhavn and the Pickaxe; the ferry; the museum
	await _teleport(Vector2i(86, 62), Vector2i.DOWN, true)
	await _walk(Vector2i.DOWN, 2)
	_check("swim off the south edge into Copperhavn bay", main.map_id == "south")
	await _wait(0.3)
	await _shot("51_copperhavn_bay")
	await _go("south", Vector2i(22, 16), Vector2i.LEFT)
	await _shot("52_copperhavn")
	await _act()
	_check("stage 3: Gerda gives you Old Bjorn's Pickaxe", story.has("pickaxe"))
	await _go("south", Vector2i(30, 16), Vector2i.UP)
	await _act()
	_check("Captain Nils gives you a ferry pass", story.has("ferry_pass"))
	await _go("south", Vector2i(44, 16), Vector2i.RIGHT)
	_check("day 1: the ferry is in Keelvik, not here", not _ent_type("ferry"))
	main.day = 1
	await _go("south", Vector2i(44, 16), Vector2i.RIGHT)
	_check("day 2: the ferry is in Copperhavn", _ent_type("ferry"))
	ui.queue = [0]
	main.player.action()
	await _wait(2.4)
	await _shot("53_ferry_crossing")
	await _settle()
	_check("the ferry crossing ends at the Keelvik pier", main.map_id == "overworld" and main.player.tile == Vector2i(71, 20))
	await _act([0])
	_check("one crossing a day: the ferry waits in Keelvik", main.map_id == "overworld" and main.ferry_stop_today() == 0)
	main.day = 2
	_check("day 3: back on schedule (Keelvik)", main.ferry_stop_today() == 0)
	main.day = 3
	_check("day 4: Copperhavn again", main.ferry_stop_today() == 1)
	main.day = 1
	story.give("float")
	await _go("south", Vector2i(26, 30), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("enter the Copperhavn museum", main.map_id == "museum")
	await _go("museum", Vector2i(7, 7), Vector2i.UP)
	await _act([0])
	_check("lend the glass float to the museum", story.exhibits.has("float") and not story.has("float"))
	_check("the float is on show on its pedestal", _exhibit_shown("float"))
	await _go("museum", Vector2i(2, 4), Vector2i.UP)
	await _act()
	await _shot("54_museum")
	await _go("south", Vector2i(23, 36), Vector2i.LEFT)
	await _walk(Vector2i.LEFT, 1)
	_check("a cracked rock blocks the Copper Hill path", main.player.tile == Vector2i(23, 36))
	await _act()
	_check("the new pickaxe breaks it", story.cleared.has("rock_hill"))
	await _go("south", Vector2i(15, 36), Vector2i.LEFT)
	ui.auto_delay = 0.8
	main.player.action()
	await _wait(2.2)
	await _shot("55_telescope_view")
	ui.auto_delay = 0.05
	await _settle()
	_check("the hill telescope shows the far north", story.scopes.has("scope_hill"))
	# --- stage 4: rocks and the dark cave -> the Bird Bell
	story.give("lantern")
	await _go("overworld", Vector2i(49, 52), Vector2i.LEFT)
	await _act()
	await _walk(Vector2i.LEFT, 2)
	_check("the pickaxe opens the Sule Ness cave", main.map_id == "cave")
	await _go("cave", Vector2i(20, 10), Vector2i.UP)
	await _act()
	_check("stage 4: the Bird Bell, deep in the cave", story.has("bird_bell"))
	# --- stage 5: chasms on the erne's feet -> the north, the Seal Flute
	await _go("overworld", Vector2i(17, 7), Vector2i.UP)
	main.player.action()
	await _wait(1.9)
	await _shot("56_hanging_from_the_erne")
	await _settle()
	_check("the erne carries you over the ravine by its feet", main.player.tile == Vector2i(17, 1))
	await _walk(Vector2i.UP, 2)
	_check("walk off Erne Cliff into the snowy north", main.map_id == "north")
	await _wait(0.4)
	await _shot("57_northern_plateau")
	await _go("north", Vector2i(17, 48), Vector2i.UP)
	main.player.action()
	await _wait(0.2)
	await _settle()
	_check("the erne lifts you over the northern chasm", main.player.tile == Vector2i(17, 42))
	await _go("north", Vector2i(40, 24), Vector2i.RIGHT)
	await _shot("58_fjelltarn")
	await _act()
	_check("stage 5: Inga gives you the Seal Flute", story.has("seal_flute"))
	await _go("north", Vector2i(47, 25), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	await _walk(Vector2i.RIGHT, 3)
	_check("the seal carries you through the icy fjord", main.player.surfing and main.player.mount_kind == "seal")
	await _shot("59_seal_in_the_fjord")
	# --- stage 6: north by seal -> the Whale Horn
	await _teleport(Vector2i(77, 16), Vector2i.UP, true)
	main.player.fit_mount()
	await _walk(Vector2i.UP, 2)
	_check("swim to the whale bay and climb onto the jetty", main.player.tile == Vector2i(77, 14) and not main.player.surfing)
	await _go("north", Vector2i(78, 12), Vector2i.RIGHT)
	await _shot("60_skarvsker")
	await _act()
	_check("stage 6: Old Halla gives you the Whale Horn", story.has("whale_horn"))
	await _go("north", Vector2i(14, 19), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("a cracked rock on the summit path", main.player.tile == Vector2i(14, 19))
	await _act()
	await _go("north", Vector2i(12, 6), Vector2i.UP)
	await _act()
	_check("the summit telescope shows the dragon shrine", story.scopes.has("scope_summit"))
	# --- stage 7: the whale across the ocean -> the eastern continent, the Dragon Band
	var consts: Dictionary = main.player.get_script().get_script_constant_map()
	_check("the whale is twice as fast as the otter", float(consts["WHALE_TIME"]) * 2.0 <= float(consts["SURF_TIME"]))
	await _go("overworld", Vector2i(75, 30), Vector2i.RIGHT)
	await _teleport(Vector2i(91, 30), Vector2i.RIGHT, true)
	main.player.force_mount("otter")
	await _walk(Vector2i.RIGHT, 2)
	_check("blow the Whale Horn where the water turns deep", main.player.mount_kind == "whale" and main.player.tile == Vector2i(93, 30))
	await _walk(Vector2i.RIGHT, 3)
	_check("the whale swims out into the eastern ocean", main.map_id == "ocean")
	await _walk(Vector2i.RIGHT, 6)
	await _shot("61_whale_on_the_ocean")
	await _teleport(Vector2i(297, 21), Vector2i.RIGHT, true)
	await _walk(Vector2i.RIGHT, 3)
	_check("across the ocean: the eastern continent", main.map_id == "east")
	await _go("east", Vector2i(17, 26), Vector2i.UP)
	await _shot("62_whitborg")
	await _go("east", Vector2i(44, 28), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	_check("the Jade River has no bridge: the otter swims it", main.player.surfing)
	await _go("east", Vector2i(69, 37), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	_check("a fallen tree on the pilgrims' way", main.player.tile == Vector2i(69, 37))
	await _act()
	await _walk(Vector2i.UP, 3)
	_check("the axe clears it", main.player.tile == Vector2i(69, 34))
	await _go("east", Vector2i(69, 25), Vector2i.UP)
	main.player.action()
	await _wait(0.2)
	await _settle()
	_check("the erne carries you over the shrine chasm", main.player.tile == Vector2i(69, 20))
	await _go("east", Vector2i(70, 16), Vector2i.RIGHT)
	await _act()
	_check("the pickaxe clears the last rock", story.cleared.has("rock_east"))
	await _go("east", Vector2i(78, 13), Vector2i.UP)
	await _shot("63_dragon_shrine")
	await _act()
	_check("stage 7: Master Lan gives you the Dragon Band", story.has("dragon_band"))
	await _wait(0.2)
	_check("the Dragon Band is worn, visibly", main.player.band.visible)
	# --- the dragon
	_check("dragon landing places are found on foot (%d)" % story.landings.size(), story.landings.size() >= 4)
	ui.auto_delay = 0.4
	ui.queue = [0]
	main.dragon_menu()
	await _wait(2.6)
	await _shot("64_dragon_flight")
	ui.auto_delay = 0.05
	await _settle()
	_check("the dragon flies you home to Keelvik", main.map_id == "overworld" and main.player.tile == Vector2i(56, 24))
	ui.queue = [0]
	main.dragon_menu()
	await _settle()
	_check("the dragon needs an hour's rest", main.map_id == "overworld" and main.player.tile == Vector2i(56, 24))
	main.set_time(main.hour + 1.1)
	ui.queue = [0]
	main.dragon_menu()
	await _wait(0.2)
	await _settle()
	_check("an hour later it flies again (to Copperhavn)", main.map_id == "south")
	# --- the Running Shoes: a secret for the curious
	await _go("overworld", Vector2i(37, 23), Vector2i.DOWN)
	var slow: float = main.player.walk_time()
	await _walk(Vector2i.DOWN, 4)
	await _walk(Vector2i.RIGHT, 1)
	await _walk(Vector2i.DOWN, 3)
	await _walk(Vector2i.LEFT, 2)
	await _walk(Vector2i.DOWN, 4)
	_check("a hidden path through the Lauvdal woods", main.player.tile == Vector2i(36, 34))
	await _shot("65_secret_clearing")
	await _act()
	_check("the Running Shoes: walking is faster for good", story.has("running_shoes") and main.player.walk_time() < slow)
	# --- the map, filled in
	main.set_time(12.0)
	await _go("overworld", Vector2i(55, 22), Vector2i.DOWN)
	main.ui.open_map()
	await _wait(0.2)
	await _shot("66_world_map_explored")
	_check("visited towns, the ferry, the museum, telescopes and landings appear on the map", main.map_places().size() >= 12)
	_check("visited places now have names", main.map_info(main.map_px("north", Vector2(39, 26)))[0] == "FJELLTARN")
	_check("the ocean is no longer a mystery", String(main.map_info(Vector2(150, 66))[1]).begins_with("THE EASTERN OCEAN. A WHALE"))
	ui.close_menus()
	var d: Dictionary = JSON.parse_string(JSON.stringify(story.to_save()))
	story.landings = {}
	story.from_save(d)
	_check("new progress is saved too (landings, exhibits, telescopes, ferry)", story.landings.size() >= 4
		and story.exhibits.has("float") and story.scopes.size() == 2 and story.ferry_day == 1)


# ------------------------------------------------------------------ video: a tour of the wider world
func _tour() -> void:
	ui.auto_delay = 1.0
	main.set_time(10.0)
	await _wait(1.0)
	ui.hide_toast()
	main.ui.open_map()
	await _wait(0.8)
	for i in 14:
		main.ui.input("right")
		await _wait(0.05)
	main.ui.map_cursor_px = Vector2(160, 66)
	main.ui._map_cursor_moved()
	await _wait(0.5)
	main.ui.input("confirm")
	await _wait(3.0)
	ui.close_menus()
	await _go("overworld", Vector2i(16, 9), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	await _act()
	await _go("overworld", Vector2i(22, 24), Vector2i.DOWN)
	await _walk(Vector2i.DOWN, 1)
	await _act()
	await _walk(Vector2i.DOWN, 2)
	await _act()
	await _walk(Vector2i.DOWN, 3)
	await _walk(Vector2i.RIGHT, 1)
	await _walk(Vector2i.DOWN, 3)
	main.player.facing = Vector2i.RIGHT
	await _act()
	story.give("ferry_pass")
	main.day = 1
	await main.warp_to("south", Vector2i(40, 16), Vector2i.RIGHT)
	await _walk(Vector2i.RIGHT, 4)
	await _act([0])
	await _wait(0.5)
	story.give("coin")
	story.give("moonstone")
	await main.warp_to("museum", Vector2i(7, 8), Vector2i.UP)
	await _walk(Vector2i.UP, 1)
	await _act([0, 0])
	await _walk(Vector2i.LEFT, 4)
	await _walk(Vector2i.UP, 2)
	main.player.facing = Vector2i.UP
	await _wait(0.6)
	await main.warp_to("overworld", Vector2i(77, 57), Vector2i.RIGHT)
	await _walk(Vector2i.RIGHT, 2)
	await _act()
	story.give("bird_bell")
	await main.warp_to("overworld", Vector2i(17, 9), Vector2i.UP)
	await _walk(Vector2i.UP, 2)
	main.player.action()
	await _wait(0.2)
	await _settle()
	await _walk(Vector2i.UP, 2)
	await _wait(0.5)
	await _walk(Vector2i.UP, 6)
	story.give("seal_flute")
	story.give("whale_horn")
	await main.warp_to("north", Vector2i(47, 25), Vector2i.RIGHT)
	main.player.action()
	await _settle()
	await _walk(Vector2i.RIGHT, 6)
	await _walk(Vector2i.UP, 4)
	await main.warp_to("overworld", Vector2i(90, 30), Vector2i.RIGHT, true)
	main.player.force_mount("otter")
	await _walk(Vector2i.RIGHT, 8)
	await _walk(Vector2i.RIGHT, 50)
	await main.warp_to("ocean", Vector2i(286, 22), Vector2i.RIGHT, true)
	main.player.force_mount("whale")
	await _walk(Vector2i.RIGHT, 18)
	await _walk(Vector2i.UP, 2)
	await _wait(0.6)
	story.give("dragon_band")
	for l in ["keelvik", "copperhavn", "fjelltarn"]:
		story.landings[l] = true
	await main.warp_to("east", Vector2i(22, 30), Vector2i.DOWN)
	await _walk(Vector2i.RIGHT, 3)
	await _wait(0.5)
	ui.auto_delay = 0.8
	ui.queue = [0]
	main.dragon_menu()
	await _wait(0.3)
	await _settle()
	await _wait(1.0)
	main.ui.open_map()
	await _wait(2.5)
	ui.close_menus()
	await _wait(0.5)


func _daylapse() -> void:
	## a full day in ~16 seconds over Keelvik
	ui.hide_toast()
	await _teleport(Vector2i(56, 13), Vector2i.DOWN)
	main.set_time(3.0)
	main.hours_per_second = 1.5
	main.time_running = true
	await _wait(16.0)
