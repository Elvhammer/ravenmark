# RAVENMARK: World Design, Step 1

An original top-down 2D exploration game in a **pixel diorama** style.
This doc covers Step 1 only: the world map, the area table, and three sailing concepts.
Nothing is built yet. Step 2 starts after your feedback.

- **Engine (assumed):** Godot 4.3+
- **Tiles:** 16×16 px
- **Camera view:** 320×180 px, which is 20×11¼ tiles ("1 screen")
- **Region:** **Ravenmark**. The land is in the west, and the **Vidsea** sea is in the east.
- **Central lake:** **Speilmere**
- **Rivers:** the **Fossa** (highlands → lake), the **Lauva** (highlands → northern sea) and the **Breia** (lake → eastern sea)

---

## 1. World map (coarse)

The region is **800 × 400 tiles**, so it is twice as wide as it is tall.
Each character on the map covers **8 × 16 tiles**, which is about ⅖ of a screen wide and 1½ screens tall.
On a monospace font the map keeps the region's true proportions.
For a pixel-art rendering of the same map, see `docs/world_map.png`.

```
 WEST: LAND ................................... | ..................... EAST: THE VIDSEA (sea)
^^^^^^^^^^^^^^^^^^^^^^TTTTTTTTTTTTTTTTTTTT,,,,,~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
^^^^^^^^^^^^^^^=^^^^^^TTTTTTTTTTTTTTTTTTTT,,,~~~~~~~~~~~^^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
^^^^^^15^^^^^^^^===============TTTTTTTTTTT,~~~......24.......~~~~~~~o~~o~~~~~~~~~~~~~~o~~~~~~~~~~~~~
^^^^^^^#^^==*==^^^TTTTTTTTTTTTT=====*======,..~~~~~~~~~~~~~~~...~~o~~~~~o~~o~~~~~~~~~~~~~~~~~~~~~~~~
^^^^^^^^#*^,,,,#5####TTTTTTTT####16######T,=~~~~~~~~~~~~~~~~~~~~..~o~~~~~o~~~~~~~~~~~~~~~~~~~~~~~~~~
^^^^^^^^^*#[F]#,,^TTT#6###[G]TTTTTTTTTTTT[H]~~~~~~~~~~~~~~~~~~~~~~...[M]....~~~~~~~~~~~~~~~~^^,,,,,,
^^^^^^^^^19,#,,^^^TTTTTTTT*=T#7TTTTTTTTTTTTT17,~~~~~o~~o~~~~~~o~...o~~~~~~o~.28~~~~~~~~~~^,,,,,,,,,,
^^^^^^^^^*^^4^^^^""""""""*T=TTT##TTTTTTTTTTTT##T^^~~~~~~~~~o~...~~~~o~~~o~~~~~..~o~~~~~~^,,,,,,,,,,,
^^^^^^^^*=^^#^*****21****"=,,,,,,#8TTTTTTTTTTT#T,~~.....25...~~~~o~~~~~~~~~~~~~~..~|~~~,,,,,,,,,,,,,
^^^^^^^^^=^^3*^^^^,,=========,,,,TT#TTTTT#18##[I]~.~~~o~~~~~o~~~~~~~~~~~~~~~~~o~~|..~~,,,,,,,,,,,,,,
^^^,,,,,,=,,#,,,,,====="""=====,,TTT#TTT#TT======~~~~~~~~o~~~~~o~~~~~~~~~~~~~~~~~~|~.~,,,,,,,,,,,,,,
^^^,,,,,,[C]==========""*""=====,TT==[J]===TTTTTT,~~~o~~~~~~~~~~~~o~~~~~~~~~~~~~~~~~.,##30###,[O],,,
^^^,,,,,,,,,#,,""====="""""========TTT#TTTTTTTTTT,..~~~~~~o~~o~~~~~~~~~~~~o~~~~~~~~~.~,,,,,,,,,,,,,,
^^^,,,,,,,,,,2,""===20==========,TTTTT9TTTTTTTTT,~~~22~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.~,,,,,,,,,,,,,,
^^^::::::::::#,"==============,,,TTTTTT#TTTTTTT,~~~~~~..~~~~~~~~~~~~~~o~~~~~~~~~~~~~~.~,,,,,,,,,,,,,
:::::::::::::,[B]==",,,,,,,,,,,,,TTTTTT#TTTTTT,~~~~~~~~~^^~~~~~~~~~~~~~~~~~~~~~~~~~~~.~~^,,,,,,,,,,,
::::::::::::##,,##,,,,,,,,,,,,,,,TTTTTT10TTTT,~~~~~~~~~~^[L]^~~~~~~~~~~~~~~~~~~~~~~~~29~~~^,,,,,,,,,
:::::^^:^:#12,,,,,#1#,,,,,,,,,,,,TTTTTT#TTT,~~~~~~......^^^^~...~~~~~~~~~~~~~~::::~~~.~~~~~~~^^,,,,,
::::::[D]#:::,,,,,,,,##[A]#,,,,,,,,,,,#,,,~...23..~~~~~~~~~~~~~~...26..~~~~~::::^^::~.~~~~~~~~~~~~~~
:::::^^:#^^:::::::::###,,,,####11####[K],..~~~~~~~~~~~~~~~~~~~~~~~~~~~~....::::[N]^::~~~~~~~~~~~~~~~
::::::^^:13::::::#14::,,,,,,,,,,,,,,~~~~~~~~~~~~~~~o~~~~~~~~~~~~~~~~~~~~~~~::::::^^::~~~@~~~~~~~~~~~
:::::::^^^:##[E]#:::::::::,,,,,~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~::::::27~~~~~~~~~~~~~~~~
::::::::::^^::::::::::::::,,~~~~~~~~~~~~~~~~~~~o~~~~~~~o~~~~~~~~~~o~~~~~~~~~~~::::~~~~~~~~o~~~~~~~~~
::::::::::::::::::::::::::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~o~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:::::::::::::::::::::::::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

**Legend**

| Symbol | Meaning | Symbol | Meaning |
|---|---|---|---|
| `~` | sea (never freezes) | `#` | land route |
| `=` | lake or river (freezes in winter) | `.` (on sea) | sailing lane |
| `"` | reed shallows or marsh: too shallow to sail, walkable only when frozen | `*` | winter-only path or spot |
| `^` | highland, cliff, canyon wall | `o` | islet |
| `T` | forest | `\|` | Drowned Kirk |
| `,` | grassland or farmland | `@` | The Kverv |
| `:` | dry scrub, badlands, salt flats | `12` | route number |
| `[A]` | settlement (key below) | | |

**Settlement key:**
- **A** Kvernby
- **B** Stiltvik
- **C** Wheelfoss
- **D** Redskar
- **E** Saltbrun
- **F** Fjelltarn
- **G** Greinholt
- **H** Keelvik
- **I** Copperhavn
- **J** Bruby
- **K** Gullsand
- **L** Skarvsker
- **M** Bruholm
- **N** Brandfell
- **O** Whitborg

**The lake ring (first half of the game):**
A →1→ B →2→ C →3→4→ F →5→6→ G →7→8→ J →9→10→ K →11→ A
That is 7 settlements and 11 routes circling Speilmere.

**How the geography holds together:**
- Snowmelt from the NW highlands feeds two rivers:
  - The **the Fossa** drops over the falls at Wheelfoss into the lake.
  - The **the Lauva** runs east through the northern forest to the sea at Keelvik.
- The lake drains east through the **Breia** and reaches the sea at Copperhavn.
- The SW gets no rivers, so it is dry: scrub, a red canyon, then salt flats.
- The SE coast faces the warm shallows, so the resort is there.
- Whitborg sits at the far eastern edge of the sea, as far from Kvernby as the region allows.

---

## 2. Area table

**Sizes** are corridor width × length in screens. Sea routes are given in double screens (40×22 tiles). You sail at twice walking speed, so they take about as long as a land route of the listed size.

**Access:**
- **Walk** means reachable on foot in any season.
- **Sail** means you need the sailing mount.
- **Winter** means it is only reachable across ice.

### Settlements (15)

| | Name | Biome | Identity / signature feature | Connections | Access |
|---|---|---|---|---|---|
| A | **Kvernby** (start) | Farmland meadow | A farm hamlet of turf-roofed houses under one enormous windmill. Its sails sweep shadows across the whole square. | R1, R11, R14 (one-way in), Speilmere shore | Walk |
| B | **Stiltvik** | Lake shallows, reeds | A town on stilts over Speilmere's shallows. Plank streets, rowboats tied under houses, lanterns at dusk. | R1, R2, R12, Speilmere | Walk |
| C | **Wheelfoss** | West river valley | A mill town where the Fossa steps down through a dozen waterwheels. In winter the wheels freeze mid-turn. | R2, R3, R21, Speilmere shore | Walk |
| D | **Redskar** | Red canyon | A mining town carved into canyon walls, with cart rails, ladders and cranes between ledges. | R12, R13 | Walk |
| E | **Saltbrun** | Salt flats | A caravan town around one huge stone well. Striped awnings and glittering salt pans. | R13, R14 | Walk |
| F | **Fjelltarn** | Highland moor | A stone town on terraces around a mountain tarn. When the tarn freezes, you can walk to **Tarnholm**. | R4, R5, R15, R19 | Walk |
| G | **Greinholt** | Northern pine forest | A treetop village of platform houses and rope bridges. The ground holds only roots and stairs. | R6, R7, R16, R21, Speilmere (via Lykt Brook) | Walk |
| H | **Keelvik** | Forested coast, the Lauva mouth | A boatwrights' village around a vast dry dock holding a half-built ship. | R16, R17, R24 | Walk |
| I | **Copperhavn** | East coast port | A busy port city: cranes, warehouses, ferry piers and a copper-roofed customs house. **You get the Otter Stick here (otter surfing).** | R17, R18, R22, R25 | Walk |
| J | **Bruby** | Eastern forest, the Breia river | A market town built entirely along a giant covered bridge over the Breia. | R8, R9, R18, Speilmere (the Breia outflow) | Walk |
| K | **Gullsand** | Sandy SE coast | A seaside resort: striped bathing huts, a pier carousel, a boardwalk and parasols. | R10, R11, R23 | Walk |
| L | **Skarvsker** | Rocky sea island | A fishing village clinging to a rock. Fish-drying racks, red boathouses, nets and a thousand gulls. | R22, R23, R26 | Sail |
| M | **Bruholm** | Archipelago | Each house stands on its own islet, and a dozen islets are linked by plank and rope bridges. | R24, R25, R28 | Sail |
| N | **Brandfell** | Volcanic island | A hot-spring town on a smoking volcano. Steaming bathhouses, and snow never settles here. | R26, R27, R29 | Sail |
| O | **Whitborg** (finale) | Great eastern isle | A grand city of pale stone towers and terraced sea canals at the far eastern edge of the map. | R30, reached by sailing R28 or R29 to Lykt Landing | Sail |

### Routes (30)

| # | Name | Biome | Connects | Signature feature | Size | Access |
|---|---|---|---|---|---|---|
| 1 | **Hesje Lane** | Farmland, hedgerows | Kvernby ↔ Stiltvik | **Old Halmkall**, a giant scarecrow on a hill that you can see for miles | 2×4 | Walk |
| 2 | **Sivwalk** | Lake shallows | Stiltvik ↔ Wheelfoss | Boardwalks and floating reed rafts with fish traps | 1×4 | Walk |
| 3 | **Foss Rise** | Rocky gorge | Wheelfoss ↔ R4 | **Waterfall**: switchbacks beside the three-tier Storfoss | 2×4 | Walk (Icefoss Glen: Winter) |
| 4 | **Varde Moor** | Heather moor | R3 ↔ Fjelltarn | **the Listening Steins**, a ring of standing stones | 2×3 | Walk |
| 5 | **Windskar Pass** | Highland pass | Fjelltarn ↔ R6 | **the Auga**, a natural rock arch framing the whole lake below | 1×3 | Walk |
| 6 | **Furufall** | Old pine forest | R5 ↔ Greinholt | A giant fallen pine across a ravine. You walk along the trunk. | 2×3 | Walk |
| 7 | **Holeik Wood** | Broadleaf forest | Greinholt ↔ R8 | A giant hollow oak that the path goes straight through | 2×3 | Walk |
| 8 | **Kloster Hill** | Forest ruins | R7 ↔ Bruby | An overgrown ruined stone monastery. The path runs through its arches. | 2×4 | Walk |
| 9 | **Bukke Bridge** | Heath, dry gully | Bruby ↔ R10 | **Long wooden bridge**: a creaking timber trestle over the gully (a troll is said to live under it) | 1×6 | Walk |
| 10 | **Trollfall** | Wooded hills | R9 ↔ Gullsand | A giant troll turned to stone, lying across the hills. The path climbs over its arm. | 2×4 | Walk |
| 11 | **Valmue Downs** | Chalk downs, poppies | Gullsand ↔ Kvernby | A huge chalk heron cut into the hillside | 2×5 | Walk |
| 12 | **Turrway** | Dry scrub | Stiltvik ↔ Redskar | A broken stone aqueduct striding across the scrub | 2×4 | Walk |
| 13 | **Langskar** | Red canyon | Redskar ↔ Saltbrun | **Canyon** spanned by a single swaying rope bridge | 1×4 | Walk |
| 14 | **Stoneskog** | Badlands | Saltbrun ↔ Kvernby | A petrified forest of stone trees. **One-way ledges** drop toward Kvernby, so it is visible from the start but unreachable from below. | 2×4 | Walk |
| 15 | **Stjernestair** | Mountain (dead end) | Fjelltarn ↔ summit | **Old ruined tower**: the roofless Star Vakt, an observatory on the peak | 1×5 | Walk |
| 16 | **Lauvdal** | River forest | Greinholt ↔ Keelvik | A mossy stone weir with a salmon ladder. **Damholm** sits mid-river. | 2×5 | Walk (Damholm: Winter) |
| 17 | **Sule Ness** | Sea cliffs | Keelvik ↔ Copperhavn | **Lighthouse**: red-and-cream stripes on the cape | 2×4 | Walk |
| 18 | **Sluse Locks** | River, canal | Bruby ↔ Copperhavn | A flight of old lock gates. Your sailing mount uses them to reach the lake. | 2×3 | Walk |
| 19 | **Rime Gorge** | Frozen gorge | Icefoss Glen ↔ Tarnholm | Walk up the frozen the Fossa between icicle walls, past a rowing boat frozen in place | 1×5 | **Winter** |
| 20 | **Speilmere Crossing** | Central lake | Every lake shore | **Klokkeholm**, a half-sunken bell tower on an islet ringed by reeds. In winter the lake is a straight shortcut from Kvernby to Greinholt. | 6×8 | **Sail or Winter** (Klokkeholm: Winter) |
| 21 | **Lyktmyr** | Bog | Wheelfoss ↔ Greinholt | Rows of old iron lamp posts sunk in the bog. A winter shortcut that skips the highlands. | 2×6 | **Winter** |
| 22 | **Skarv Sound** | Open sea | Copperhavn ↔ Skarvsker | **the Tenn**, a ring of sea stacks | 2×3 | Sail |
| 23 | **Sol Shoals** | Warm shallows | Gullsand ↔ Skarvsker | A sunken galleon visible through clear amber water | 2×3 | Sail |
| 24 | **Rimestream** | Northern sea | Keelvik ↔ Bruholm | **the Porten**, a towering sea arch you sail through | 2×5 | Sail |
| 25 | **the Smaholms** | Islet maze | Copperhavn ↔ Bruholm | A maze of tiny islets with rope bridges and a hidden sea fort on a reef | 3×4 | Sail |
| 26 | **Brand Sound** | Volcanic sea | Skarvsker ↔ Brandfell | Steam vents and black-sand islets | 2×3 | Sail |
| 27 | **Askpath** | Volcano slopes | Brandfell ↔ crater | A crater hot-spring lake, the only freshwater that never freezes | 1×2 | Sail |
| 28 | **Drowned Kirk** | Deep sea | Bruholm ↔ Lykt Landing | The spire of a sunken stave church poking above the waves | 3×5 | Sail |
| 29 | **The Kverv** | Deep sea | Brandfell ↔ Lykt Landing | A great whirlpool whose currents drag you off course | 3×6 | Sail |
| 30 | **Lantern Way** | Tidal flats | Lykt Landing ↔ Whitborg | A long causeway lined with giant stone lanterns: the final approach | 1×4 | Sail |

### Gated spots: visible early, reachable later

| Spot | Where | How you first see it | Unlocked by |
|---|---|---|---|
| Klokkeholm bell tower | Middle of Speilmere | From R1 and Kvernby's shore | Winter |
| Icefoss Glen | Behind Storfoss (R3) | A dark gap behind the falling water | Winter (the falls freeze into an ice stair) |
| Tarnholm | Fjelltarn's tarn | From the town terraces | Winter |
| Damholm | Mid-river on R16 | A glinting chest on the islet | Winter |
| Sunbake ledges | R14, above Kvernby | From the start town's west edge | Reach Saltbrun, then hop down |
| the Breia river path | R18 | The towpath ends at the locks | Winter (walk the frozen river) or Sail |
| Outer islets | Off R11 and R17 | From the clifftops | Sail |
| Hidden sea fort | Inside the Smaholms (R25) | A flag above the islets | Sail through a narrow channel |

### Suggested story order

1. **Kvernby** → R1 → **Stiltvik** → R2 → **Wheelfoss** → R3, R4 → **Fjelltarn** → R5, R6 → **Greinholt** → R16 → **Keelvik** → R17 → **Copperhavn** (sailing unlocked) → R18 → **Bruby** → R9, R10 → **Gullsand** → R11 → back to **Kvernby**, closing the ring.
2. Then the sea: **Skarvsker** → **Brandfell** / **Bruholm** → **Whitborg**.
3. Optional along the way:
   - the SW loop (R12–R14)
   - Stjernestair (R15)
   - the forest shortcut (R7–R8)
   - all winter content

---

## 3. Sailing

### Chosen: surf companions (otter, and a seal for cold water)

You sit on top of a small, friendly animal that is mostly under the water. Only its back, the top of its head, its eyes and its nose break the surface. It bobs and paddles in a short loop. Preview: `docs/style/surf_otter_seal.gif`.

**Key items.** These live in the backpack only and are never drawn on the hero.

| Item | Where you get it | What it does |
|---|---|---|
| **Otter Stick** | Copperhavn, when surfing unlocks | A carved driftwood stick that otter riders use to guide their otter. Use it facing water from any shore tile and your otter surfaces. |
| **Seal Flute** | Later. Suggested: the old sealer in Fjelltarn | Calls a seal that can swim in **cold water**. |

**Where each one can go**

| Water | Otter | Seal | On foot |
|---|---|---|---|
| Lakes and rivers (spring to autumn) | Yes | Yes | No |
| Open sea (any season; the sea never freezes) | Yes | Yes | No |
| **Cold water** | No: the otter shivers and turns back | Yes | No |
| Frozen lakes, rivers, reeds, marsh (winter) | No | No | Yes, walk on the ice |
| Reed shallows (not frozen) | No | No | No |

**Cold water** means fixed zones on the map, so the player always knows the rule:
- **Rimestream:** the cold current along the northern sea route (R24, Keelvik to Bruholm), with drifting ice floes. Bruholm stays reachable by otter through the Smaholms (R25), so the seal opens the faster northern route and hidden ice islets.
- **Fjelltarn's tarn outside winter:** cold mountain meltwater. In summer you need the seal to reach Tarnholm; in winter you can walk there on the ice.

**Equipment the hero can wear (visible on the sprite):** the **pouch** and the **walking stick**. These are separate sprite layers, drawn only when equipped.

### Shared rules

These apply to both surf companions:
- Sailing is faster than walking, about 2× walk speed.
- The camera stays at the same scale on water as on land. No zoom effects.
- The mount or skiff refuses frozen water and reed shallows.
- The sea never freezes.

### Earlier concepts (not used)

#### Concept 1: **Mossback**, the wandering island (creature)

**What it is.** A colossal, slow-blinking sea creature, broad and flat-backed. Over centuries its back has grown a tiny garden: moss, a crooked tree, a lantern post and a wicker saddle-hut where the player rides. Copperhavn's harbour folk say it has circled the Vidsea since before the city existed.

**How you call it.** Blow a clay whistle at any jetty or beach landing (marked with a striped post). Mossback surfaces with a slow bubble animation and you step on.

**How it feels.** Heavy and floaty. It takes half a second to get going, glides with a little momentum and turns wide. It cruises at about 2× walking speed.

**Diorama hook.** It is literally a moving piece of model terrain, and its back garden changes with the seasons:
- blossom in spring
- deep green in summer
- orange leaves in autumn
- a snow cap in winter, while the sea around it stays open

**At ice.** It nudges the ice edge, shakes snow off its back and won't go further.

**Art cost.** A 48×32 sprite (3×2 tiles), a 4-direction swim cycle, a dithered pixel wake and four seasonal back-garden overlays.

#### Concept 2: **The Folding Skiff** (ability / tool)

**What it is.** The boatwrights of Keelvik give you a palm-sized lacquered paper boat. Toss it onto water and it unfolds, with a 6-frame pop, into a one-person skiff with a patched sail. Step off and it folds back into your pocket. It is the most "toy" option of the three.

**How you use it.** Face water from any shore tile and press interact.

**How it feels.** Light and responsive, with no momentum. There is an optional wind layer: each season has a prevailing wind, shown by drifting pixel clouds and leaves. Sailing downwind is faster and upwind is slower, but never slower than walking. The wind can be turned off for the prototype.

**Diorama hook.**
- Sail colours can be customised.
- Later in the game, Keelvik's half-built ship could be finished as a late-game upgrade: a faster, bigger boat for the deep sea.

**At ice.** It bumps the ice and automatically folds up, which also makes clear that the ice is walkable.

**Art cost.** The lowest of the three: a 16×16 to 32×32 skiff sprite and a fold animation. This option also keeps creatures out of the traversal system entirely.

#### Concept 3: **Ferrycrab** (creature)

**What it is.** A towering hermit crab that wades the Vidsea seabed. For a shell it wears the salvaged cabin of an old ferry, with round porthole windows and a little chimney. You ride inside the cabin.

**How you call it.** Ring a ferry bell at any dock and it rises out of the water.

**How it feels.** Quick and skittering, with no momentum and a bobbing motion. It walks sideways like a crab, so the cabin always faces you, which is comic and toy-like.

**Unique mechanic.** It can crawl a few tiles up onto sand: beaches, sandbars and spits. That opens sandbar-only nooks that the other concepts can't reach. It still can't climb cliffs or enter reeds.

**Diorama hook.**
- The porthole windows glow at dusk and in winter.
- Barnacles and seaweed on the cabin change with the season.

**At ice.** Its claws skid and it backs away.

**Art cost.** The highest of the three: multi-leg walk cycles, beach-transition logic and a 48×48 sprite.

These three concepts and the four larger mounts in `docs/style/mount_options.png` were explored first and set aside in favour of the surf companions above.

---

## 4. Season rules

| Season | Land palette | Water |
|---|---|---|
| Spring | Fresh sage greens, pink and white blossom on fruit trees, muddy paths | Lakes and rivers flowing |
| Summer | Deep olive greens, golden fields, dusty paths | Flowing |
| Autumn | Orange, rust and red trees, straw-coloured grass, leaf litter | Flowing |
| Winter | Snow on ground, roofs and treetops; dark evergreens show through | **Lake, rivers, tarn, reeds and marsh freeze solid and are walkable.** The sea never freezes, and Brandfell's crater lake never freezes. |

- The seasons cycle with play time. The length is tunable, with 20 minutes per season as a starting point.
- A debug key switches the season instantly.

**Starting palette:** warm, toy-like and deliberately away from primary green and blue.

| Use | Colours |
|---|---|
| Summer grass | `#7E8F4A` / `#97A55A` |
| Autumn trees | `#C46A3A` / `#D9933F` / `#9E4430` |
| Sea | `#3F5E62` / `#557A76`, foam `#DCD2B6` |
| Lake | `#5F887C` (greener than the sea), ice `#B9CCC4` |
| Snow | `#ECE6D8`, shade `#B8B3C6` |
| Path | `#C9A878` |
| Shadow | `#2F2A3A` with 50% checker dither |

---

## Day and night

A 24-hour clock runs alongside the seasons: **night 22:00-04:00 (6 h), dawn 04:00-07:00 (3 h), day 07:00-19:00 (12 h), dusk 19:00-22:00 (3 h)**. One in-game hour lasts 30 seconds, so a full day takes 12 minutes, and seasons change at midnight every 2 days.

Colouring uses a **palette lookup table**. The game only draws the 16 palette colours, so the table says, for each of them, which colour it becomes at each time of day (one row every 15 minutes; neighbouring rows blend smoothly). This keeps the retro look at night (each colour gets a chosen moonlit version instead of everything being darkened together), costs almost nothing to run, and the table is a small image anyone can repaint. Lit windows, lamps and the lighthouse use colours outside the palette, so the table leaves them bright, with a soft glow around them.

## 5. Proposed Step 2 slice (for your approval)

I propose **Keelvik + R16 Lauvdal (west) + R17 Sule Ness (south) + the coast along Sule Ness, up to the edge of the cold Rimestream**. This one slice exercises every feature you asked for:

- **Town:** a boatwright village with a dry dock, jetties and a spot to launch your otter.
- **Lauvdal:** a forest river with a weir. It shows the autumn colours, the river freezing, and Damholm, which you can only reach in winter.
- **Sule Ness:** cliffs, a lighthouse, one-way ledges and an islet you can see but not reach.
- **Coast and sea:** otter surfing, the sea staying open in winter, and the otter turning back at the cold Rimestream.

Planned technical approach (Godot 4):
- **Pixel-perfect rendering:** integer scaling only, and no camera zoom effects.
- **Tilt-shift:** a screen shader that blurs only the top and bottom bands.
- **Shadows:** dithered pixel drop shadows.
- **Seasons:** a palette-swap shader recolours tiles and sprites.
- **Movement:** grid movement with smooth tweened steps, walk and run cycles, and ledge hops.

**Decided so far:**
- **Look:** retro 16-colour palette, medium detail, soft coloured outlines (see `docs/style/v2_*.png`).
- **Hero:** the Cartographer, with the pouch and walking stick as optional visible equipment.
- **Sailing:** surf companions, an otter via the Otter Stick and a seal via the Seal Flute for cold water.
- **Names:** Norwegian-sounding throughout.
- **Camera:** same scale on land and water, no zoom effects.
- **Step 2 slice:** Keelvik with Lauvdal (R16), Sule Ness (R17) and its coast.

---

## Part 2, increment 1: systems + one working example of each

Everything from the Part 2 brief now exists in the prototype area (Keelvik, Lauvdal, Sule Ness and the
coast). Later increments add regions and more content on the same systems.

### Content is data
All story content lives in `game/data/content.json`, generated by `tools/proto_content.py`. Each NPC has a
list of dialogue branches; the first branch whose conditions hold runs. Conditions: flags, items held,
times talked, distinct days talked, time of day, companion, final decision 1, story stage. Actions: say,
give/take items, coins, flags, stage, choices, yes/no confirmations, shops, selling, warps, companion,
final decision, opening a gate. This is how memory, gifts after repeated visits, lost-item returns and
the recurring character are written, without code.

### World
| Feature | Example in this increment |
| --- | --- |
| Position on the world map | M: blinking dot on the region map (rooms map to their building) |
| Normal travel between towns | Keelvik, Lauvdal, Sule Ness, Mossholt, Fyrholm (all on foot / by water / by boat) |
| Interiors with NPCs and items | Inn, store, workshop, Liv's house |
| Back rooms that open later | Inn cellar (key from Marit after returning her ring) |
| Tunnels between regions | Sule Ness cave -> tunnel -> Moonlit Grove |
| Obstacles removed for good | Young tree (axe), cracked rock (pickaxe), thicket (FD1), hedges (owl) |

### Traversal items
Axe (store, 120), Pickaxe (cellar), Lantern (Ole, for lamp oil), Cellar Key (Marit), Otter Stick (start),
Seal Flute (chest), Bird Bell (night market, 8000: the great erne flies you over the Lauvdal ravine).

### Economy
Clue items (ring, knife, amber), favour chains (Sigve, Ole), special shops (night market stalls),
cheap everyday items (bread 2, lamp oil 4, moon tea 3), expensive items that hint at the future
(Bird Bell 8000, ship plans 25000), big rewards later (cave 5000, Erne Cliff 3000), a rare buyer
(Ambrose, about 1 day in 5, pays 400-1500), and a store that stocks more after the cave treasure.

### NPCs
16 NPCs. Recurring traveller: Sigve (4 stages, moves Lauvdal -> inn -> Sule Ness -> workshop).
Very rare wanderer: Ambrose. Gifts after repeated visits: Marit, Liv, Selma, Tobias, Arne.
Memory: most NPCs say something new on the second talk. Lost items: Marit's ring, Liv's knife.
NPCs only move while off screen, so nobody pops in or out in front of you.

### Time-specific places
Night market 20:00-04:00 (two stalls with lanterns), low-tide sandbar 04:00-07:00 (the sea pulls back;
stranded players wade back when the tide turns), Selma in the Moonlit Grove 21:00-04:00.

### Final decisions
FD1: the Amber Heart (one per game) goes to Ole (Fyrholm opens: island, beacon, two islanders) or Tove
(Mossholt opens: hidden settlement, two villagers). FD2: fox (digs up buried coins and items) or owl (shows
hidden ways through hedges). Both ask for confirmation, both are permanent, both are saved. The companion
follows one tile behind; C hides it and the ability still works. The pen at Hedda's keeps the other animal.

### Testing
`--autotest=shots` plays two full games (fox + caretaker, owl + keeper) and checks 86 things, from walking
and surfing to every quest step, shop, choice and the save data. Screenshots: docs/prototype/2x-4x_*.png.

---

## Part 3: the wider world

### Traversal progression (each item opens the way to the next)
| Stage | Item | Found | Opens |
| --- | --- | --- | --- |
| 1 | Axe | stump in the north Lauvdal woods | fallen trees on the path to the Moonlit Grove |
| 2 | Otter Stick | Edvin, Moonlit Grove pond | rivers + sea: swim south off the map to Copperhavn |
| 3 | Pickaxe | Gerda, Copperhavn | cracked rocks: Sule Ness cave (both mouths), Copper Hill lookout, summit path |
| 4 | Bird Bell | deep in the Sule Ness cave (lantern needed) | perch-to-perch hops over chasms, hanging from the erne's feet: the Lauvdal ravine, then the north |
| 5 | Seal Flute | Inga, Fjelltarn | icy water: the frozen fjord (and the Rimestream back home) |
| 6 | Whale Horn | Old Halla, Skarvsker (whale bay, sea access only) | the open ocean (deep water east of Keelvik) -> the eastern continent |
| 7 | Dragon Band | Master Lan, Brandfell shrine (needs river, fallen tree, chasm, rock: every earlier tool) | dragon flight between discovered landing places, once per in-game hour |

`tools/check_progression.py` floods every map with growing item sets (seasons and tide assumed favourable,
so a season trick cannot skip a stage) and fails if any item becomes reachable out of order. Current result:
PROGRESSION OK, with the Running Shoes reachable from the start as an optional secret.

### Regions (medium size)
- Home coast (96 x 64): Keelvik, Lauvdal, Sule Ness. Unchanged except: open ocean strip on the east edge,
  a hidden forest path (Running Shoes), the grove path now blocked by two fallen trees.
- Copperhavn (96 x 48): copper town on a bay, ferry pier, museum, Copper Hill with a telescope. Reached by
  sea from the home coast's south-east edge.
- The north (96 x 64, always winter): snowy plateau above Erne Cliff, a chasm (perches), Fjelltarn on its
  frozen tarn, the summit lookout, the long icy fjord and the whale bay of Skarvsker.
- The eastern ocean (300 x 40): whale-only deep water, skerries, the Halfway Rock, a wreck.
- The eastern continent (96 x 64): Whitborg, the Jade River (no bridge), the pilgrims' way up Brandfell to
  the dragon shrine. Distinct scenery: blossom trees, terracotta roads, red-roofed houses, stone lanterns,
  red sandstone mountains.

### Systems
- Region edges: each outdoor map lists linked edge spans; stepping off the edge loads the next map at the
  matching tile, keeping your mount. Water you can't swim stops you at the edge.
- Whale: mount on deep ocean tiles (and open sea once riding), 0.025 s per tile (otter and seal 0.05).
- Dragon: F opens a list of landing places found on foot (6: Keelvik, Copperhavn, Fjelltarn, Skarvsker,
  Whitborg, the shrine); one flight per in-game hour. The dragon is a head plus 24 segments that follow the
  head's own path with a travelling wave.
- Ferry: alternates Keelvik (even days) / Copperhavn (odd days); one ride a day; after a ride it stays at
  the destination for the rest of the day, then resumes the schedule. Short animated crossing.
- Museum: ten pedestals; lend finds to the curator; each shows its exhibit and a plaque. Empty plaques
  give hints. Every exhibit can be found in one playthrough.
- Telescopes: three lookouts show a framed, round view of a far place (Whitborg, Fjelltarn, the shrine
  with the dragon coiled around it), drawn from the real map so you recognise it later.
- World map: drawn from the real maps; undiscovered places are "???", visited towns get names and icons;
  icons for caves, ferry stops, the museum, telescopes and (with the band) landing places; the ocean fades
  out to the east until the Whale Horn, and selecting it shows a mysterious note.
- Movement speed: every step lasts its base time / MOVE_SPEED (0.7, i.e. 30% slower than the base times).
  Base times: walk 0.10, run 0.055, otter/seal 0.05, whale 0.025, ledge hop 0.17, onto an animal 0.125,
  Running Shoes 0.08 / 0.0425. So walking is 0.143 s per tile; surfing stays twice walking speed and the whale
  twice the otter. (History: 0.20 s walking at first, halved, then slowed 30%.)
- Screen: the 320 x 180 game is shown at the biggest whole-number scale that fits the window, centred. On start
  the window is sized to the biggest scale that fits the screen (5x = 1600 x 900 on a 1080p screen), and it
  refits when resized. The HUD uses 0.8 x the game scale (rounded), so it is a little smaller than the world;
  its widgets keep their 320 x 180 positions and are pinned to corners, the bottom or the middle.
- Rendering: the world is still 320 x 180 game pixels, but the SubViewport renders it at the screen size with
  the camera zoomed by the game scale. Every art pixel stays a crisp 5 x 5 block (nearest filtering), but the
  camera, hero and companion can sit between game pixels, so scrolling and walking move in 1-screen-pixel steps
  instead of jumping a whole 5-pixel block (which looked like new rows "spawning in" unevenly at the edges, and
  made the hero vibrate against the ground when hero and camera rounded differently). The cave darkness dither
  and the tilt-shift blur are scaled to work in game pixels, so they look the same at every scale.
- Debug window (F1): live sliders for movement speed and step times, camera smoothing and lag, game and UI
  scale, tilt-shift, the hour and clock speed; "Copy values" puts them on the clipboard. Nothing is saved.
- Camera: smoothing 7, raised while you move fast so the camera never trails the hero by more than 40 px
  (otherwise the whale would carry you off screen).
- Layers: the hero's gear stacks by child order (body, pouch, stick, band), not z_index, so it hides behind trees
  with the hero; the stick goes behind the body unless you face up. The ground sits at z -2, under flat things
  at z -1 (rugs, dug holes, open hedge gaps, the erne and dragon shadows), which the ground used to cover.
- Trees and roofs in front of the hero fade to see-through over 0.15 s instead of popping.
- Running Shoes: walk 0.08 s / run 0.0425 s per tile instead of 0.10 / 0.055.
- Walk animation follows the step, not a clock: each step shows one stride (left and right foot alternate step by
  step) and then the standing frame for its second half; steps shorter than 0.09 s hold the stride. The fox does
  the same. The hero and companion glide smoothly (sub-pixel, see Rendering) and move before the camera
  follows them each frame, so they hold still relative to the camera instead of lagging it by a frame.
- Input: every direction tap counts. Each key press (or d-pad press) is remembered, up to 4 at a time, and
  walked as soon as the current step ends, so a tap let go mid-step is never lost. Holding a key walks on as
  before and stops after the step under way. Remembered taps are dropped when a door, text box or menu takes
  over. `--autotest=input` sends real key events to check this (also run at the end of `--autotest=shots`).
