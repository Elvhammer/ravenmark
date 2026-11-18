extends Node
## Game state and story rules: items, coins, flags, NPC memory, companion, final decisions, and the small
## script language the dialogue in data/content.json is written in (see tools/proto_content.py).
## Everything here is saved; the world (main.gd) asks this node what exists and what happens.

const SAVE_PATH := "user://ravenmark_save.json"

var main
var ui
var C: Dictionary                    # content.json

var items := {}                      # item id -> count
var coins := 0
var flags := {}
var opened := {}                     # chest id -> true
var taken := {}                      # pickup id -> true
var cleared := {}                    # obstacle id -> true
var found := {}                      # companion secret id -> true
var gates := {}                      # story gate -> true (e.g. "mossholt")
var mem := {}                        # npc memory id -> {talks, days: [], stage}
var companion := ""                  # "", "fox", "owl"
var companion_visible := true
var fd1 := ""                        # "", "keeper", "caretaker"
var game_seed := 0
var force_rare := {}                 # npc id -> spot index (autotest)
var visited := {}                    # place names you have walked into (the world map shows them)
var landings := {}                   # dragon landing places found on foot
var exhibits := {}                   # items lent to the Copperhavn museum
var scopes := {}                     # telescopes looked through
var ferry_day := -1                  # the day the ferry was last ridden ...
var ferry_at := 0                    # ... and where it went
var dragon_time := -1.0              # when the dragon last flew (hours since day 0)
var pending_warp: Array = []

var npc_by_id := {}


func setup(m) -> void:
	main = m
	ui = m.ui
	C = JSON.parse_string(FileAccess.get_file_as_string("res://game/data/content.json"))
	for n in C["npcs"]:
		npc_by_id[n["id"]] = n


func new_game() -> void:
	items = {}
	for it in C.get("start_items", []):
		items[it] = 1
	coins = int(C["start_coins"])
	visited = {}
	landings = {}
	exhibits = {}
	scopes = {}
	ferry_day = -1
	ferry_at = 0
	dragon_time = -1.0
	flags = {}
	opened = {}
	taken = {}
	cleared = {}
	found = {}
	gates = {}
	mem = {}
	companion = ""
	companion_visible = true
	fd1 = ""
	game_seed = randi() % 100000


# ------------------------------------------------------------------ items + coins
func has(item: String) -> bool:
	return int(items.get(item, 0)) > 0


func count(item: String) -> int:
	return int(items.get(item, 0))


func give(item: String, n := 1) -> void:
	items[item] = count(item) + n


func take(item: String, n := 1) -> void:
	var left := count(item) - n
	if left > 0:
		items[item] = left
	else:
		items.erase(item)


func item_name(item: String) -> String:
	return String(C["items"][item]["name"]) if C["items"].has(item) else item.to_upper()


func is_key_item(item: String) -> bool:
	return C["items"].has(item) and bool(C["items"][item]["key"])


func add_coins(n: int) -> void:
	coins = max(0, coins + n)
	ui.set_coins(coins)


func text(id: String) -> String:
	return String(C["texts"].get(id, id))


# ------------------------------------------------------------------ conditions
func in_time(r: Array, h := -1.0) -> bool:
	if h < 0.0:
		h = main.hour
	var a := float(r[0])
	var b := float(r[1])
	if a <= b:
		return h >= a and h < b
	return h >= a or h < b


func _as_list(v) -> Array:
	return v if v is Array else [v]


func mem_get(id: String) -> Dictionary:
	if not mem.has(id):
		mem[id] = {"talks": 0, "days": [], "stage": 0}
	return mem[id]


func cond_ok(c: Dictionary, mem_id := "") -> bool:
	for k in c.keys():
		var v = c[k]
		match k:
			"flag":
				for f in _as_list(v):
					if not flags.has(f):
						return false
			"not_flag":
				for f in _as_list(v):
					if flags.has(f):
						return false
			"has":
				if not has(v):
					return false
			"not_has":
				if has(v):
					return false
			"time":
				if not in_time(v):
					return false
			"companion":
				if companion != String(v).replace("none", ""):
					return false
			"fd1":
				if fd1 != String(v).replace("none", ""):
					return false
			"stage":
				if int(mem_get(mem_id)["stage"]) != int(v):
					return false
			"talked":
				if int(mem_get(mem_id)["talks"]) < int(v):
					return false
			"days":
				var days: Array = mem_get(mem_id)["days"].duplicate()
				if not days.has(main.day):
					days.append(main.day)
				if days.size() < int(v):
					return false
	return true


# ------------------------------------------------------------------ NPCs: who is where, right now
func mem_key(n: Dictionary) -> String:
	return String(n.get("mem", n["id"]))


func rare_spot(n: Dictionary) -> Dictionary:
	## very rare wanderers: a daily roll decides if (and where) they turn up today
	var spots: Array = n["spots"]
	if force_rare.has(n["id"]):
		return spots[int(force_rare[n["id"]])]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%d:%s:%d" % [game_seed, n["id"], main.day])
	if rng.randf() >= float(n["rare"]):
		return {}
	return spots[rng.randi() % spots.size()]


func npc_spot(n: Dictionary) -> Dictionary:
	if n.has("rare"):
		if not in_time(n["time"]):
			return {}
		return rare_spot(n)
	if not cond_ok(n.get("when", {}), mem_key(n)):
		return {}
	return {"map": n["map"], "x": n["x"], "y": n["y"]}


func npcs_on(map_id: String) -> Array:
	## [[npc, tile], ...] for every NPC standing on this map at the current time
	var out := []
	for n in C["npcs"]:
		var s := npc_spot(n)
		if not s.is_empty() and s["map"] == map_id:
			out.append([n, Vector2i(int(s["x"]), int(s["y"]))])
	return out


# ------------------------------------------------------------------ talking
func talk(n: Dictionary) -> void:
	var mk := mem_key(n)
	var m := mem_get(mk)
	var branches: Array = C["dialog"][String(n.get("dialog", n["id"]))]
	for b in branches:
		if cond_ok(b.get("if", {}), mk):
			await run(b["do"], n)
			break
	m["talks"] = int(m["talks"]) + 1
	if not m["days"].has(main.day):
		m["days"].append(main.day)


func run(acts: Array, n) -> void:
	var who: String = n["name"] if n is Dictionary else ""
	for a in acts:
		match String(a[0]):
			"say":
				await ui.say(who, a[1])
			"note":
				await ui.say("", a[1])
			"give":
				give(a[1])
				await ui.say("", "RECEIVED %s!" % item_name(a[1]), a[1])
				if is_key_item(a[1]):
					await ui.say("", C["items"][a[1]]["desc"], a[1])
			"take":
				take(a[1])
			"coins":
				add_coins(int(a[1]))
				await ui.say("", "RECEIVED %d COINS!" % int(a[1]), "coins")
			"flag":
				flags[a[1]] = true
			"stage":
				mem_get(mem_key(n))["stage"] = int(a[1])
			"choice":
				var labels := []
				for o in a[2]:
					labels.append(o[0])
				var i: int = await ui.choose(a[1], labels)
				if i >= 0:
					await run(a[2][i][1], n)
			"confirm":
				var i: int = await ui.choose(a[1], ["YES", "NO"])
				if i == 0:
					await run(a[2], n)
			"shop":
				await ui.shop(a[1])
			"sell":
				await ui.sell(a[1])
			"warp":
				pending_warp = [a[1], int(a[2]), int(a[3]), a[4]]
			"companion":
				companion = a[1]
				companion_visible = true
				main.on_companion_changed()
			"fd1":
				fd1 = a[1]
			"open":
				gates[a[1]] = true
				main.refresh_entities(true)
			"museum":
				await main.museum_talk(n)
			"ferry_info":
				await ui.say(who, main.ferry_info())
	main.save_game()


# ------------------------------------------------------------------ chests, pickups, shops
func open_chest(c: Dictionary) -> void:
	opened[c["id"]] = true
	if c.has("item"):
		give(c["item"])
		await ui.say("", "FOUND %s!" % item_name(c["item"]), c["item"])
		if is_key_item(c["item"]):
			await ui.say("", C["items"][c["item"]]["desc"], c["item"])
	if c.has("coins"):
		add_coins(int(c["coins"]))
		await ui.say("", "FOUND %d COINS!" % int(c["coins"]), "coins")
	if c.has("flag"):
		flags[c["flag"]] = true
	if c.has("msg"):
		await ui.say("", c["msg"])
	main.save_game()


func shop_entries(id: String) -> Array:
	var out := []
	for e in C["shops"][id]:
		if e.has("if") and not cond_ok(e["if"]):
			continue
		var it: String = e["item"]
		if is_key_item(it) and has(it):
			continue                                    # one of each tool is enough
		if it == "ship_plans" and (has(it) or flags.has("ship_plans_given")):
			continue
		out.append(e)
	return out


func buy(e: Dictionary) -> bool:
	if coins < int(e["price"]):
		return false
	add_coins(-int(e["price"]))
	give(e["item"])
	main.save_game()
	return true


func sell_entries(buyer: String) -> Array:
	var out := []
	var wants: Dictionary = C["buyers"][buyer]
	for it in wants.keys():
		if has(it):
			out.append({"item": it, "price": int(wants[it])})
	return out


func sell_item(e: Dictionary) -> void:
	take(e["item"])
	add_coins(int(e["price"]))
	main.save_game()


# ------------------------------------------------------------------ save / load
func to_save() -> Dictionary:
	return {"items": items, "coins": coins, "flags": flags, "opened": opened, "taken": taken, "cleared": cleared,
			"found": found, "gates": gates, "mem": mem, "companion": companion,
			"companion_visible": companion_visible, "fd1": fd1, "seed": game_seed, "visited": visited,
			"landings": landings, "exhibits": exhibits, "scopes": scopes, "ferry_day": ferry_day, "ferry_at": ferry_at,
			"dragon_time": dragon_time}


func from_save(d: Dictionary) -> void:
	items = {}
	for k in d["items"].keys():
		items[k] = int(d["items"][k])
	coins = int(d["coins"])
	flags = d["flags"]
	opened = d["opened"]
	taken = d["taken"]
	cleared = d["cleared"]
	found = d["found"]
	gates = d["gates"]
	mem = {}
	for k in d["mem"].keys():
		var m: Dictionary = d["mem"][k]
		var days := []
		for x in m["days"]:
			days.append(int(x))
		mem[k] = {"talks": int(m["talks"]), "days": days, "stage": int(m["stage"])}
	companion = d["companion"]
	companion_visible = bool(d["companion_visible"])
	fd1 = d["fd1"]
	game_seed = int(d["seed"])
	visited = d.get("visited", {})
	landings = d.get("landings", {})
	exhibits = d.get("exhibits", {})
	scopes = d.get("scopes", {})
	ferry_day = int(d.get("ferry_day", -1))
	ferry_at = int(d.get("ferry_at", 0))
	dragon_time = float(d.get("dragon_time", -1.0))
