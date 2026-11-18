"""Content for the wider world (Part 3): Copperhavn, the snowy north, the eastern ocean and continent,
the ferry, the museum, telescopes, dragon landing places and the world map. Merged into content.json by
proto_content.build().

Progression (each tool opens the way to the next):
  Axe (stump, north Lauvdal) -> fallen trees -> Otter Stick (Edvin, Moonlit Grove) -> the sea south ->
  Pickaxe (Gerda, Copperhavn) -> cracked rocks + the dark cave -> Bird Bell (deep in the Sule Ness cave) ->
  the Lauvdal ravine and the chasm in the north -> Seal Flute (Inga, Fjelltarn) -> the icy fjord ->
  Whale Horn (Halla, Skarvsker) -> the open ocean -> the eastern continent -> Dragon Band (Master Lan).
"""
S = 'say'
DAY = [6, 21]

NPCS = [
    {'id': 'edvin', 'name': 'EDVIN', 'sprite': 'edvin', 'map': 'overworld', 'x': 25, 'y': 32, 'when': {'time': DAY}},
    # Copperhavn
    {'id': 'gerda', 'name': 'GERDA', 'sprite': 'gerda', 'map': 'south', 'x': 21, 'y': 16},
    {'id': 'nils', 'name': 'CAPTAIN NILS', 'sprite': 'nils', 'map': 'south', 'x': 30, 'y': 15},
    {'id': 'agnes', 'name': 'AGNES', 'sprite': 'agnes', 'map': 'museum', 'x': 7, 'y': 5},
    {'id': 'pim', 'name': 'PIM', 'sprite': 'pim', 'map': 'south', 'x': 27, 'y': 25},
    # the north
    {'id': 'inga', 'name': 'INGA', 'sprite': 'inga', 'map': 'north', 'x': 41, 'y': 24},
    {'id': 'bo', 'name': 'BO', 'sprite': 'bo', 'map': 'north', 'x': 24, 'y': 24},
    {'id': 'halla', 'name': 'OLD HALLA', 'sprite': 'halla', 'map': 'north', 'x': 79, 'y': 12},
    # the east
    {'id': 'rin', 'name': 'RIN', 'sprite': 'rin', 'map': 'east', 'x': 16, 'y': 24},
    {'id': 'kai', 'name': 'KAI', 'sprite': 'kai', 'map': 'east', 'x': 24, 'y': 31},
    {'id': 'lan', 'name': 'MASTER LAN', 'sprite': 'lan', 'map': 'east', 'x': 78, 'y': 12},
]

DIALOG = {
    'edvin': [
        {'if': {'not_has': 'otter_stick'}, 'do': [
            [S, 'OH! A VISITOR. NOBODY COMES THROUGH THE WOODS SINCE THE STORM BROUGHT THE TREES DOWN.'],
            [S, 'I\'M EDVIN. I\'VE KEPT OTTERS IN THIS POND FOR FIFTY YEARS. THAT ONE HAS BEEN WATCHING YOU.'],
            [S, 'TAKE MY OTTER STICK. FACE ANY WATER AND PRESS SPACE, AND SHE\'LL CARRY YOU.'],
            ['give', 'otter_stick'],
            [S, 'THE SEA SOUTH OF SULE NESS LEADS TO COPPERHAVN. MINERS, AND A MUSEUM. GO AND SEE.']]},
        {'if': {'has': 'whale_horn'}, 'do': [
            [S, 'A WHALE HORN! MY OTTER IS JEALOUS. SHE\'LL GET OVER IT.']]},
        {'do': [[S, 'THE OTTERS SAY THE SEA IS CALM TODAY. THEY ARE USUALLY RIGHT.']]},
    ],
    'gerda': [
        {'if': {'not_has': 'pickaxe'}, 'do': [
            [S, 'YOU SWAM HERE? WITH AN OTTER? WELL, I\'VE SEEN STRANGER THINGS IN THE MINE.'],
            [S, 'I\'M GERDA. MY BROTHER BJORN LEFT HIS PICK WITH ME BEFORE HE WENT NORTH. HE\'D WANT IT USED.'],
            ['give', 'pickaxe'],
            [S, 'THERE\'S A CRACKED ROCK ON THE PATH UP THE COPPER HILL. TRY IT THERE FIRST.']]},
        {'if': {'talked': 1, 'not_has': 'bird_bell'}, 'do': [
            [S, 'BJORN ALWAYS SAID THE CAVE UNDER SULE NESS RINGS LIKE A BELL WHEN THE WIND BLOWS.']]},
        {'do': [[S, 'THE COPPER MINE CLOSED YEARS AGO. NOW WE MOSTLY DIG UP STORIES.']]},
    ],
    'nils': [
        {'if': {'not_has': 'ferry_pass'}, 'do': [
            [S, 'CAPTAIN NILS. MY FERRY RUNS BETWEEN COPPERHAVN AND KEELVIK: ONE DAY HERE, THE NEXT DAY THERE.'],
            [S, 'ANYONE WHO SWIMS HERE WITH AN OTTER DESERVES A PASS. ONE CROSSING A DAY, MIND.'],
            ['give', 'ferry_pass']]},
        {'do': [['ferry_info']]},
    ],
    'pim': [
        {'if': {'talked': 1}, 'do': [
            [S, 'FROM THE TOP OF THE COPPER HILL YOU CAN SEE THE SNOW IN THE FAR NORTH. THERE\'S A TELESCOPE UP THERE.']]},
        {'do': [[S, 'I WANT TO BE A MINER. OR A CARTOGRAPHER. OR A WHALE.']]},
    ],
    'agnes': [
        {'do': [['museum']]},
    ],
    'inga': [
        {'if': {'not_has': 'seal_flute'}, 'do': [
            [S, 'YOU CAME OVER THE CHASM? ON THE ERNE\'S FEET? YOU\'RE EITHER BRAVE OR SILLY.'],
            [S, 'I\'M INGA. I KEEP THE SEALS. THE FJORD WOULD FREEZE AN OTTER\'S WHISKERS, BUT SEALS LOVE IT.'],
            [S, 'TAKE THIS FLUTE. PLAY IT IN THE COLD WATER AND A SEAL WILL CARRY YOU.'],
            ['give', 'seal_flute'],
            [S, 'FOLLOW THE FJORD NORTH AND EAST. AT SKARVSKER THE WHALES COME IN TO SING.']]},
        {'do': [[S, 'THE FJORD RUNS SOUTH TO THE RIMESTREAM, AND FROM THERE TO KEELVIK. A SEAL CAN TAKE YOU HOME.']]},
    ],
    'bo': [
        {'if': {'talked': 1}, 'do': [
            [S, 'THERE\'S A TELESCOPE ON THE SUMMIT. ON CLEAR DAYS YOU CAN SEE ALL THE WAY TO THE OTHER SIDE OF THE WORLD.']]},
        {'do': [[S, 'WELCOME TO FJELLTARN. THE TARN HASN\'T THAWED IN A HUNDRED YEARS. WE SKATE TO WORK.']]},
    ],
    'halla': [
        {'if': {'not_has': 'whale_horn'}, 'do': [
            [S, 'A SEAL BROUGHT YOU? THEN THE SEA ALREADY KNOWS YOU.'],
            [S, 'I\'M HALLA. I SING WITH THE WHALES. THEY TOLD ME SOMEONE WOULD COME LOOKING FOR THE OTHER SIDE.'],
            ['give', 'whale_horn'],
            [S, 'EAST OF KEELVIK THE WATER TURNS DEEP AND DARK. SWIM OUT THERE AND BLOW THE HORN.'],
            [S, 'NOBODY FROM HERE HAS SEEN THE FAR SIDE. THEY SAY THE LANTERNS THERE NEVER GO OUT.']]},
        {'do': [[S, 'LISTEN... THAT LOW HUM IS THE WHALES. THEY\'RE TALKING ABOUT YOU.']]},
    ],
    'rin': [
        {'if': {'talked': 1}, 'do': [
            [S, 'THE DRAGON SHRINE IS UP ON BRANDFELL, EAST OF THE JADE RIVER. THERE\'S NO BRIDGE. THERE NEVER WAS.']]},
        {'do': [[S, 'A WHALE! NOBODY HAS COME FROM THE WEST IN A HUNDRED YEARS. WELCOME TO WHITBORG!'],
                [S, 'WE THOUGHT THE WEST WAS JUST A STORY. YOUR MAP SAYS OTHERWISE.']]},
    ],
    'kai': [
        {'if': {'talked': 1}, 'do': [
            [S, 'THE OLD WAY UP BRANDFELL IS BLOCKED BY A FALLEN TREE, A CRACKED ROCK, AND A CHASM. PILGRIMS USED TO TURN BACK.']]},
        {'do': [[S, 'I MAKE THE LANTERNS. THEY NEVER GO OUT, BECAUSE I NEVER STOP MAKING THEM.']]},
    ],
    'lan': [
        {'if': {'not_has': 'dragon_band'}, 'do': [
            [S, 'YOU CROSSED A CHASM, A RIVER WITH NO BRIDGE, AND A WHOLE OCEAN TO STAND HERE.'],
            [S, 'THE DRAGON HAS BEEN WAITING FOR SOMEONE WHO WALKS THE WHOLE WORLD. WEAR THIS.'],
            ['give', 'dragon_band'],
            [S, 'IT WILL ONLY LAND WHERE YOU HAVE STOOD YOURSELF: TOWNS, AND THE OPEN CLEARINGS. AND IT NEEDS AN HOUR\'S REST.']]},
        {'do': [[S, 'THE DRAGON SLEEPS IN THE CLOUDS ABOVE BRANDFELL. IT DREAMS OF MAPS.']]},
    ],
}

CHESTS = [
    {'id': 'c_hill', 'map': 'south', 'x': 18, 'y': 39, 'coins': 400},
    {'id': 'c_plateau_n', 'map': 'north', 'x': 24, 'y': 51, 'coins': 300},
    {'id': 'c_skarvsker', 'map': 'north', 'x': 87, 'y': 9, 'coins': 1000},
    {'id': 'c_shrine', 'map': 'east', 'x': 85, 'y': 12, 'coins': 2000, 'msg': 'A PILGRIM\'S OFFERING, LEFT FOR WHOEVER MADE IT UP HERE.'},
]

SIGNS = [
    {'map': 'south', 'x': 33, 'y': 20, 'lines': ['COPPERHAVN. THE MINE IS CLOSED. THE MUSEUM IS OPEN.']},
    {'map': 'south', 'x': 43, 'y': 15, 'lines': ['FERRY TO KEELVIK.', 'ONE DAY HERE, THE NEXT DAY THERE. PASSES FROM CAPTAIN NILS.']},
    {'map': 'north', 'x': 19, 'y': 41, 'lines': ['FJELLTARN. MIND THE ICE.']},
    {'map': 'east', 'x': 18, 'y': 26, 'lines': ['WHITBORG, HARBOUR OF LANTERNS.']},
    {'map': 'east', 'x': 70, 'y': 38, 'lines': ['THE PILGRIM\'S WAY TO BRANDFELL.']},
]
for _s in SIGNS:
    _s['kind'] = 'sign'

OBSTACLES = [
    {'id': 'rock_hill', 'map': 'south', 'x': 22, 'y': 36, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
    {'id': 'rock_summit', 'map': 'north', 'x': 14, 'y': 18, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
    {'id': 'tree_east', 'map': 'east', 'x': 69, 'y': 36, 'kind': 'fallen_tree', 'needs': 'axe'},
    {'id': 'rock_east', 'map': 'east', 'x': 71, 'y': 16, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
]

PICKUPS = [
    {'id': 'p_crystal', 'map': 'north', 'x': 7, 'y': 8, 'item': 'frost_crystal', 'kind': 'sparkle'},
    {'id': 'p_tooth', 'map': 'north', 'x': 84, 'y': 13, 'item': 'whale_tooth', 'kind': 'sparkle'},
    {'id': 'p_jade', 'map': 'east', 'x': 40, 'y': 6, 'item': 'jade_figure', 'kind': 'sparkle'},
    {'id': 'p_chart', 'map': 'ocean', 'x': 152, 'y': 21, 'item': 'old_chart', 'kind': 'sparkle'},
]

PERCHES = [
    {'id': 'perch_ns', 'map': 'north', 'x': 17, 'y': 47, 'land': [17, 42], 'face': 'up'},
    {'id': 'perch_nn', 'map': 'north', 'x': 17, 'y': 43, 'land': [17, 48], 'face': 'down'},
    {'id': 'perch_es', 'map': 'east', 'x': 69, 'y': 24, 'land': [69, 20], 'face': 'up'},
    {'id': 'perch_en', 'map': 'east', 'x': 69, 'y': 21, 'land': [69, 25], 'face': 'down'},
]

WARPS = [
    {'map': 'south', 'x': 26, 'y': 29, 'dir': 'up', 'to': 'museum', 'tx': 7, 'ty': 8, 'face': 'up'},
    {'map': 'museum', 'x': 7, 'y': 9, 'dir': 'down', 'to': 'south', 'tx': 26, 'ty': 30, 'face': 'down'},
    {'map': 'south', 'x': 19, 'y': 14, 'dir': 'up', 'locked': 'GERDA\'S HOUSE. IT SMELLS OF COPPER POLISH AND COFFEE.'},
]

ZONES = [
    ['south', 10, 34, 21, 42, 'COPPER HILL', 'THE LOOKOUT'],
    ['south', 0, 0, 59, 47, 'COPPERHAVN', 'COPPER TOWN BY THE SEA'],
    ['museum', 0, 0, 99, 99, 'COPPERHAVN MUSEUM', 'CURIOSITIES OF THE COAST'],
    ['north', 2, 2, 19, 18, 'FJELLTARN SUMMIT', 'THE LOOKOUT'],
    ['north', 4, 47, 33, 63, 'NORTHERN PLATEAU', 'THE EDGE OF THE SNOW'],
    ['north', 60, 0, 95, 17, 'SKARVSKER', 'WHERE THE WHALES SING'],
    ['north', 0, 0, 59, 46, 'FJELLTARN', 'VILLAGE ON THE TARN'],
    ['ocean', 140, 14, 160, 26, 'HALFWAY ROCK', 'THE MIDDLE OF NOWHERE'],
    ['ocean', 0, 0, 299, 39, 'THE EASTERN OCEAN', 'DEEP WATER'],
    ['east', 60, 0, 95, 23, 'BRANDFELL', 'THE DRAGON SHRINE'],
    ['east', 0, 0, 43, 63, 'WHITBORG', 'HARBOUR OF LANTERNS'],
    ['east', 44, 0, 95, 63, 'THE JADE MEADOWS', 'BEYOND THE RIVER'],
]

SEA_ZONES = {
    'overworld': {'~': ['THE VIDSEA', 'OPEN WATER'], '!': ['RIMESTREAM', 'COLD WATER'], 'O': ['THE EASTERN OCEAN', 'DEEP WATER']},
    'south': {'~': ['COPPER BAY', 'OPEN WATER']},
    'north': {'!': ['THE FROZEN FJORD', 'ICY WATER']},
    'ocean': {'O': ['THE EASTERN OCEAN', 'DEEP WATER']},
    'east': {'O': ['WHITBORG HARBOUR', 'CALM WATER'], '~': ['WHITBORG HARBOUR', 'CALM WATER']},
}

TEXTS = {
    'whale_far': 'THE WHALE SURGES AHEAD. THE COAST BEHIND YOU SHRINKS TO A LINE.',
    'ferry_gone': 'THE FERRY IS AT %s TODAY.',
    'ferry_no_pass': 'A DECKHAND: "PASSENGERS NEED A PASS FROM CAPTAIN NILS. HE LIVES IN COPPERHAVN, ACROSS THE WATER."',
    'ferry_used': 'THE FERRY HAS MADE ITS CROSSING FOR TODAY. IT SAILS AGAIN TOMORROW.',
    'ferry_ask': 'ALL ABOARD FOR %s?',
    'ferry_today': 'TODAY THE FERRY IS AT %s. TOMORROW IT SAILS TO %s, AND THEN BACK AGAIN, DAY AFTER DAY.',
    'museum_intro': 'WELCOME TO THE COPPERHAVN MUSEUM. I\'M AGNES, THE CURATOR. WE COLLECT THE UNUSUAL.',
    'museum_lend': 'WOULD YOU LEND THE MUSEUM YOUR %s? (AMBROSE THE COLLECTOR WOULD PAY YOU FOR IT, MIND.)',
    'museum_thanks': 'WONDERFUL! I\'LL PUT IT ON DISPLAY RIGHT AWAY.',
    'museum_count': 'THE MUSEUM NOW HAS %d OF %d EXHIBITS. THE EMPTY PLAQUES SAY WHAT WE\'RE STILL LOOKING FOR.',
    'museum_full': 'EVERY PEDESTAL IS FULL. THIS IS THE FINEST LITTLE MUSEUM ON THE COAST, THANKS TO YOU.',
    'museum_nothing': 'NOTHING NEW TODAY? THE EMPTY PLAQUES SAY WHAT WE\'RE STILL LOOKING FOR.',
    'map_ocean': 'THE EASTERN OCEAN. NO CHART GOES FURTHER. THE WATER IS TOO DEEP FOR ANCHORS, AND ON CLEAR NIGHTS, FAR OUT, SAILORS SWEAR THEY SEE LANTERNS FLOATING ON THE HORIZON.',
    'map_ocean_known': 'THE EASTERN OCEAN. A WHALE KNOWS THE WAY ACROSS.',
    'map_unknown': '???',
    'map_uncharted': 'UNCHARTED.',
}

# ferry: day 0, 2, 4... at stop 0 (Keelvik); day 1, 3, 5... at stop 1 (Copperhavn)
FERRY = {'pass': 'ferry_pass', 'captain': 'CAPTAIN NILS', 'stops': [
    {'name': 'KEELVIK', 'map': 'overworld', 'x': 73, 'y': 20, 'tiles': [[72, 20], [73, 20], [74, 20]], 'land': [71, 20],
     'face': 'left'},
    {'name': 'COPPERHAVN', 'map': 'south', 'x': 46, 'y': 16, 'tiles': [[45, 16], [46, 16], [47, 16]], 'land': [44, 16],
     'face': 'left'}]}

MUSEUM = {'map': 'museum', 'exhibits': [
    {'item': 'coin', 'x': 2, 'y': 3, 'where': 'FROM DAMHOLM, AN ISLET YOU CAN ONLY WALK TO OVER THE WINTER ICE.',
     'hint': 'SOMETHING OLD AND SILVER, FROM AN ISLAND YOU CAN ONLY WALK TO IN WINTER.'},
    {'item': 'float', 'x': 4, 'y': 3, 'where': 'FROM AN ISLET OFF THE KEELVIK COAST.',
     'hint': 'A BALL OF GREEN GLASS THAT ONCE HELD UP A FISHING NET, FROM AN ISLET OFF KEELVIK.'},
    {'item': 'moonstone', 'x': 6, 'y': 3, 'where': 'A GIFT FROM SELMA OF THE MOONLIT GROVE.',
     'hint': 'A STONE THAT GLOWS UNDER THE MOON. ASK THE ONE WHO ONLY COMES OUT AT NIGHT.'},
    {'item': 'ship_bell', 'x': 9, 'y': 3, 'where': 'FROM THE CELLAR OF THE KEELVIK INN.',
     'hint': 'A SHIP\'S BELL. INNS KEEP STRANGE THINGS IN THEIR CELLARS.'},
    {'item': 'compass', 'x': 11, 'y': 3, 'where': 'ARVID\'S COMPASS, GIVEN BY HIS BROTHER SIGVE.',
     'hint': 'A COMPASS THAT ALWAYS POINTS HOME. A TRAVELLER LOOKING FOR HIS BROTHER\'S BOAT HAS ONE.'},
    {'item': 'dragon_scale', 'x': 13, 'y': 3, 'where': 'BOUGHT AT THE KEELVIK NIGHT MARKET, FOR A FORTUNE.',
     'hint': 'A DRAGON\'S SCALE. THE NIGHT MARKET IN KEELVIK SELLS ONE, FOR A FORTUNE.'},
    {'item': 'frost_crystal', 'x': 2, 'y': 6, 'where': 'FROM THE TOP OF THE FJELLTARN SUMMIT.',
     'hint': 'ICE THAT NEVER MELTS, FROM THE HIGHEST POINT IN THE NORTH.'},
    {'item': 'whale_tooth', 'x': 4, 'y': 6, 'where': 'FROM THE BEACH AT SKARVSKER, WHERE THE WHALES SING.',
     'hint': 'A WHALE\'S TOOTH, FROM THE BAY WHERE THE WHALES SING.'},
    {'item': 'old_chart', 'x': 11, 'y': 6, 'where': 'FROM THE HALFWAY ROCK, IN THE MIDDLE OF THE EASTERN OCEAN.',
     'hint': 'A CHART OF THE OPEN OCEAN. ONLY A WHALE COULD TAKE YOU WHERE IT WAS LOST.'},
    {'item': 'jade_figure', 'x': 13, 'y': 6, 'where': 'FROM THE JADE MEADOWS, ON THE FAR SIDE OF THE OCEAN.',
     'hint': 'SOMETHING CARVED IN JADE, FROM BEYOND THE OCEAN.'},
]}

TELESCOPES = [
    {'id': 'scope_sule', 'map': 'overworld', 'x': 80, 'y': 57, 'view': 'scope_sule', 'place': 'WHITBORG',
     'caption': 'FAR TO THE EAST, BEYOND THE OPEN OCEAN: A HARBOUR FULL OF RED LANTERNS. NO MAP SHOWS IT.'},
    {'id': 'scope_hill', 'map': 'south', 'x': 14, 'y': 36, 'view': 'scope_hill', 'place': 'FJELLTARN',
     'caption': 'FAR TO THE NORTH: A VILLAGE ON A FROZEN LAKE, UNDER WHITE MOUNTAINS. HOW WOULD YOU EVER GET THERE?'},
    {'id': 'scope_summit', 'map': 'north', 'x': 12, 'y': 5, 'view': 'scope_summit', 'place': 'BRANDFELL',
     'caption': 'FAR AWAY TO THE EAST, ACROSS THE OCEAN: A TEMPLE ON A MOUNTAIN. SOMETHING LONG AND RED IS COILED AROUND IT.'},
]
VIEWS = {   # what each telescope shows: map, centre tile (rendered in proto_art3.py)
    'scope_sule': ['east', 18, 23], 'scope_hill': ['north', 31, 22], 'scope_summit': ['east', 78, 9],
}

LANDINGS = [   # dragon landing places: discovered by walking to them
    {'id': 'keelvik', 'name': 'KEELVIK', 'map': 'overworld', 'x': 56, 'y': 24},
    {'id': 'copperhavn', 'name': 'COPPERHAVN', 'map': 'south', 'x': 27, 'y': 19},
    {'id': 'fjelltarn', 'name': 'FJELLTARN', 'map': 'north', 'x': 39, 'y': 26},
    {'id': 'skarvsker', 'name': 'SKARVSKER', 'map': 'north', 'x': 79, 'y': 11},
    {'id': 'whitborg', 'name': 'WHITBORG', 'map': 'east', 'x': 23, 'y': 31},
    {'id': 'shrine', 'name': 'DRAGON SHRINE', 'map': 'east', 'x': 78, 'y': 14},
]

WORLDMAP = {   # world map (M): where each region sits on the 288 x 144 map image
    'size': [288, 144],
    'regions': {'north': [32, 4, 64, 42.67], 'overworld': [32, 46.67, 64, 42.67], 'south': [58.67, 89.33, 64, 32],
                'ocean': [96, 52.67, 112, 26.67], 'east': [208, 46, 64, 42.67]},
    'rooms': {'inn': ['overworld', 49, 9], 'cellar': ['overworld', 49, 9], 'store': ['overworld', 62, 9],
              'workshop': ['overworld', 66, 13], 'fisher': ['overworld', 49, 25], 'cave': ['overworld', 47, 52],
              'museum': ['south', 26, 29], 'crossing': ['overworld', 80, 30]},
    'places': [   # icons appear once the zone has been visited (or the telescope used / landing found)
        {'name': 'KEELVIK', 'icon': 'town', 'map': 'overworld', 'x': 57, 'y': 17, 'zone': 'KEELVIK'},
        {'name': 'MOSSHOLT', 'icon': 'town', 'map': 'overworld', 'x': 9, 'y': 48, 'zone': 'MOSSHOLT'},
        {'name': 'FYRHOLM', 'icon': 'town', 'map': 'overworld', 'x': 89, 'y': 52, 'zone': 'FYRHOLM'},
        {'name': 'SULE NESS CAVE', 'icon': 'cave', 'map': 'overworld', 'x': 47, 'y': 52, 'zone': 'SULE NESS CAVE'},
        {'name': 'KEELVIK FERRY', 'icon': 'ferry', 'map': 'overworld', 'x': 73, 'y': 20, 'zone': 'KEELVIK'},
        {'name': 'COPPERHAVN', 'icon': 'town', 'map': 'south', 'x': 25, 'y': 18, 'zone': 'COPPERHAVN'},
        {'name': 'COPPERHAVN FERRY', 'icon': 'ferry', 'map': 'south', 'x': 46, 'y': 16, 'zone': 'COPPERHAVN'},
        {'name': 'COPPERHAVN MUSEUM', 'icon': 'museum', 'map': 'south', 'x': 26, 'y': 30, 'zone': 'COPPERHAVN MUSEUM'},
        {'name': 'FJELLTARN', 'icon': 'town', 'map': 'north', 'x': 33, 'y': 24, 'zone': 'FJELLTARN'},
        {'name': 'SKARVSKER', 'icon': 'town', 'map': 'north', 'x': 77, 'y': 9, 'zone': 'SKARVSKER'},
        {'name': 'HALFWAY ROCK', 'icon': 'cave', 'map': 'ocean', 'x': 150, 'y': 20, 'zone': 'HALFWAY ROCK'},
        {'name': 'WHITBORG', 'icon': 'town', 'map': 'east', 'x': 23, 'y': 28, 'zone': 'WHITBORG'},
        {'name': 'DRAGON SHRINE', 'icon': 'shrine', 'map': 'east', 'x': 78, 'y': 10, 'zone': 'BRANDFELL'},
    ],
}


def merge(data):
    """add the wider world to the content dictionary built by proto_content.py"""
    data['npcs'] += NPCS
    data['dialog'].update(DIALOG)
    data['chests'] += CHESTS
    data['signs'] += SIGNS
    data['obstacles'] += OBSTACLES
    data['pickups'] += PICKUPS
    data['perches'] += PERCHES
    data['warps'] += WARPS
    data['zones'] = ZONES[:3] + data['zones'] + ZONES[3:]
    data['sea_zones'] = SEA_ZONES
    data['texts'].update(TEXTS)
    data['ferry'] = FERRY
    data['museum'] = MUSEUM
    data['telescopes'] = TELESCOPES
    data['views'] = VIEWS
    data['landings'] = LANDINGS
    data['worldmap'] = WORLDMAP
    data['start_items'] = []
    data['progression'] = ['axe', 'otter_stick', 'pickaxe', 'bird_bell', 'seal_flute', 'whale_horn', 'dragon_band']
    return data
