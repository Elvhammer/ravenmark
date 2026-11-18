RAVENMARK - playable prototype, Part 3: the wider world
=====================================================

HOW TO PLAY
  1. Unzip anywhere.
  2. Open Godot 4.3 or newer > Import > select ravenmark/project.godot
     (newer 4.x versions may offer to convert the project: say yes).
  3. Press F5 (or the Play button). The first import takes a few seconds.
  The game saves by itself (doors, talks, chests, travel, quitting). F9 starts a new game.
  NOTE: the item order changed in this version. If you played the previous version, press F9 once
  so you start fresh (old saves still load, but you would keep items that are now found elsewhere).

CONTROLS
  Arrows / WASD       move (one tile per step)          Shift      run
  Space / Z / Enter   talk, read, open, use, surf        X / Esc    back / close
  I                   items                              M          world map (arrows or mouse to look, Space to read)
  F                   call the dragon (once you have the Dragon Band)
  C                   companion: follow / hide           E / R      pouch / walking stick
  T                   jump to the next time of day       Tab, 1-4   change season
  F9                  new game                           H          help
  Tools are used by themselves: walk up to a fallen tree with the axe, or a cracked rock with the pickaxe,
  and press Space. Face water and press Space to swim.

THE TRAVERSAL ITEMS, IN ORDER
  You start with nothing. Each item opens the way to the next one; nothing is numbered, you just find them.

  #  Item          Where you find it                               What it opens
  1  Axe           a stump in the woods north of Lauvdal            fallen trees (the path to the Moonlit Grove)
  2  Otter Stick   Edvin, by the pond in the Moonlit Grove          rivers and the sea: swim south to Copperhavn
  3  Pickaxe       Gerda in Copperhavn, across the water             cracked rocks: the Sule Ness cave, the hill lookout
  4  Bird Bell     deep in the Sule Ness cave (bring a lantern)      chasms: the erne lifts you by its feet from perch
                                                                     to perch, over the Lauvdal ravine to the snowy north
  5  Seal Flute    Inga in Fjelltarn, the village on the frozen tarn icy water: the frozen fjord
  6  Whale Horn    Old Halla at Skarvsker, the whale bay (north,     the open ocean east of Keelvik: a fast whale
                   by seal)                                          carries you across to the eastern continent
  7  Dragon Band   Master Lan at the dragon shrine on Brandfell      worn on your arm; press F: a long red dragon flies
                   (the eastern continent)                           you to any landing place you have walked to,
                                                                     once per in-game hour

  Optional: the Running Shoes (a secret: look for a gap in the trees near the flower field east of
  Lauvdal) make you walk a little faster for good.

WHAT'S NEW IN THIS VERSION
  - The world is about three times bigger: Copperhavn (south, across the water), the snowy north
    (Fjelltarn and the whale bay of Skarvsker), the eastern ocean and the eastern continent (Whitborg,
    harbour of lanterns, and the dragon shrine). The east has its own look: blossom trees, terracotta
    roads, red roofs and stone lanterns.
  - Regions join at their edges: walk or swim off the map edge where the land or sea carries on.
  - The whale: blow the horn where the water turns deep and dark (the far east of the home coast).
    It swims twice as fast as the otter and seal, with its own animation (it spouts, and its tail rises).
  - The dragon: a long Chinese-style dragon snakes down, picks you up and flies you to a landing place.
    Landing places are the towns and a few clearings; they only appear after you have been there on foot.
  - The erne now carries you hanging from its feet, for short hops over chasms.
  - The ferry between Keelvik and Copperhavn: day 1 it is in Keelvik, day 2 in Copperhavn, and so on.
    One crossing a day; after a ride it waits at the far end for the rest of the day. Captain Nils in
    Copperhavn gives you a pass.
  - The Copperhavn museum: lend Agnes the unusual things you find and they go on show. The empty plaques
    say what she is still looking for. (Ambrose the collector would pay you for some of them instead...)
  - Telescopes at three high places (Sule Ness headland, Copper Hill, Fjelltarn summit) show you places
    far away that you will later recognise.
  - The world map fills in as you explore: undiscovered places have no name, visited towns get a name and
    an icon, and so do caves, the ferry, the museum, telescopes and dragon landing places. The eastern
    ocean fades out to the east until you have the Whale Horn (look at it on the map...).
  Everything from the earlier versions is still there: seasons, day/night, the tide, the night market,
  the two big choices (amber heart, fox or owl), shops and the NPC stories.

WHERE TO START (no spoilers)
  Talk to everyone in Keelvik and Lauvdal. Tove in Lauvdal knows where to find an axe.
  Press T a few times: different people are about at night, and the sea does odd things at dawn.

FOLDERS
  game/              the Godot game
      scripts/main.gd    world: maps, region edges, doors, NPC placement, lights, tide, cave darkness,
                         the ferry, the museum, telescopes, the erne and the dragon, world map data
      scripts/story.gd   game state, saving, and the dialogue/quest script interpreter
      scripts/ui.gd      pixel-font HUD, dialogue, choices, shops, items, world map, telescope view
      scripts/dragon.gd  the flying dragon (a head and a chain of body segments following its path)
      data/content.json  all NPCs, dialogue, items, shops, chests, doors, ferry, museum, landings (generated)
  tools/             Python scripts that generate the content, maps and art (Godot ignores this folder)
      proto_content.py + proto_content2.py   NPCs, dialogue, items, quests, the wider world -> content.json
      proto_map.py       the home coast                               -> game/data/world.json
      proto_regions.py   Copperhavn, the north, the ocean, the east   -> game/data/maps/*.json
      proto_rooms.py     interiors and the cave                       -> game/data/maps/*.json
      proto_build.py     all game art (+ proto_art2.py, proto_art3.py) -> game/art/*
      check_progression.py   proves the item order: floods every map with growing sets of items
      (needs Python 3 with Pillow + numpy: cd tools && python3 proto_content.py && python3 proto_build.py)
  docs/              design doc, style exploration, prototype screenshots + videos

TESTING WITHOUT A KEYBOARD
  godot --path . -- --autotest=shots --out=SOME_FOLDER   plays through everything + screenshots
  godot --path . -- --autotest=part3 --out=SOME_FOLDER   only the new progression (start to dragon)
  godot --path . --write-movie tour.avi --fixed-fps 30 -- --autotest=tour
