"""All story content for the Keelvik prototype -> game/data/content.json

Dialogue scripts: each NPC has a list of branches; the first branch whose `if` matches runs its `do` list.
Conditions (all must hold):
  flag / not_flag: str or list    has / not_has: item       talked: n  (talked at least n times before)
  days: n  (talked on at least n different days)           time: [from_hour, to_hour] (wraps past midnight)
  companion: fox | owl | none     fd1: keeper | caretaker | none           stage: n (this NPC's story stage)
Actions:
  [say, TEXT]  [note, TEXT]  [give, item]  [take, item]  [coins, n]  [flag, name]  [stage, n]
  [choice, PROMPT, [[LABEL, [actions]], ...]]   [confirm, PROMPT, [actions if yes]]
  [shop, id]  [sell, buyer]  [warp, map, x, y, facing]  [companion, fox|owl]  [fd1, keeper|caretaker]  [open, gate]
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'game', 'data', 'content.json')

ITEMS = {
    # traversal (key items)
    'otter_stick': ('OTTER STICK', 'EDVIN\'S CARVED DRIFTWOOD STICK. FACE WATER AND PRESS SPACE TO CALL YOUR OTTER.'),
    'seal_flute': ('SEAL FLUTE', 'A BONE FLUTE. A SEAL CARRIES YOU THROUGH ICY WATER WHERE THE OTTER WON\'T GO.'),
    'axe': ('AXE', 'TOVE\'S OLD AXE. CLEARS FALLEN TREES THAT BLOCK THE WAY.'),
    'pickaxe': ('PICKAXE', 'OLD BJORN\'S PICK, FROM COPPERHAVN. BREAKS CRACKED ROCKS.'),
    'lantern': ('LANTERN', 'OLE\'S OLD LANTERN. LIGHTS UP DARK CAVES.'),
    'cellar_key': ('CELLAR KEY', 'OPENS THE CELLAR UNDER THE KEELVIK INN.'),
    'bird_bell': ('BIRD BELL', 'RING IT AT A TALL PERCH: THE GREAT ERNE LIFTS YOU BY ITS FEET ACROSS A CHASM.'),
    'whale_horn': ('WHALE HORN', 'A HORN OF WHALEBONE. SWIM OUT TO WHERE THE WATER TURNS DEEP AND DARK: A WHALE WILL CARRY YOU ACROSS THE OPEN OCEAN.'),
    'dragon_band': ('DRAGON BAND', 'A RED AND GOLD ARMBAND. PRESS F OUTDOORS TO CALL THE DRAGON. IT FLIES YOU TO ANY LANDING PLACE YOU HAVE WALKED TO, ONCE AN HOUR.'),
    'running_shoes': ('RUNNING SHOES', 'LIGHT, SPRINGY SHOES FROM AN OLD COURIER. YOU WALK A LITTLE FASTER, FOR GOOD.'),
    'ferry_pass': ('FERRY PASS', 'CAPTAIN NILS\'S PASS. ONE FERRY CROSSING A DAY BETWEEN KEELVIK AND COPPERHAVN.'),
    'walking_stick': ('WALKING STICK', 'A SOLID STICK. PRESS R TO WEAR IT OR PUT IT AWAY.'),
    # everyday
    'bread': ('BREAD', 'A ROUND LOAF. 2 COINS ANYWHERE.'),
    'lamp_oil': ('LAMP OIL', 'A SMALL TIN OF OIL FOR LAMPS.'),
    'moon_tea': ('MOON TEA', 'NIGHT-MARKET TEA. SMELLS OF HONEY.'),
    'smoked_fish': ('SMOKED FISH', 'A GIFT FROM LIV. YOUR STOMACH APPROVES.'),
    'sea_chart': ('SEA CHART', 'A CHART OF THE HOME WATERS, FROM JOAR\'S STALL.'),
    'dragon_scale': ('DRAGON SCALE', 'A SCALE THE SIZE OF A PLATE, FROM THE FAR EAST. THE SELLER SWEARS IT\'S REAL.'),
    'ship_plans': ('SHIP PLANS', 'FULL PLANS FOR EIRIK\'S BIG SHIP.'),
    # quest / story
    'ring': ('SILVER RING', 'A WOMAN\'S RING, FOUND IN THE REEDS. SOMEONE MUST MISS IT.'),
    'knife': ('OLD KNIFE', 'A FISHING KNIFE, BURIED IN THE SAND. THE HANDLE SAYS "LIV".'),
    'tern_plank': ('TERN PLANK', 'DRIFTWOOD WITH A TERN CARVED INTO IT.'),
    'compass': ('ARVID\'S COMPASS', 'SIGVE\'S BROTHER\'S COMPASS. IT ALWAYS POINTS HOME.'),
    'amber_heart': ('AMBER HEART', 'A FIST-SIZED PIECE OF AMBER, WARM TO THE TOUCH. ONLY ONE CAN HAVE IT.'),
    # valuables (the collector buys these)
    'coin': ('OLD SILVER COIN', 'FOUND ON DAMHOLM. VERY OLD.'),
    'float': ('GLASS FLOAT', 'A FISHING FLOAT OF GREEN GLASS.'),
    'moonstone': ('MOONSTONE', 'SELMA\'S GIFT. IT GLOWS FAINTLY AT NIGHT.'),
    'lucky_hook': ('LUCKY HOOK', 'LIV\'S THANK-YOU. A BRASS HOOK.'),
    'sea_glass': ('SEA GLASS', 'BLUE SEA GLASS FROM THE FYRHOLM TIDE POOLS.'),
    'carving': ('CARVED OWL', 'ARNE\'S CARVING FROM MOSSHOLT.'),
    'ship_bell': ('SHIP\'S BELL', 'A GREEN BRONZE BELL FROM A SHIP THAT SANK LONG AGO. IT WAS IN THE INN CELLAR.'),
    'whale_tooth': ('WHALE TOOTH', 'A WHALE\'S TOOTH, SMOOTH AS SOAP. FROM THE BEACH AT SKARVSKER.'),
    'frost_crystal': ('FROST CRYSTAL', 'A CRYSTAL OF ICE THAT NEVER MELTS, FROM THE FJELLTARN SUMMIT.'),
    'jade_figure': ('JADE DRAGON', 'A LITTLE DRAGON CARVED IN JADE, FOUND IN THE MEADOWS BEYOND THE OCEAN.'),
    'old_chart': ('HALFWAY CHART', 'A SAILOR\'S CHART OF THE OPEN OCEAN, HALF WASHED AWAY. FROM THE HALFWAY ROCK.'),
}
KEY_ITEMS = ['otter_stick', 'seal_flute', 'axe', 'pickaxe', 'lantern', 'cellar_key', 'bird_bell', 'walking_stick',
             'whale_horn', 'dragon_band', 'running_shoes', 'ferry_pass']

SHOPS = {
    'store': [{'item': 'bread', 'price': 2}, {'item': 'lamp_oil', 'price': 4},
              {'item': 'ship_plans', 'price': 25000, 'if': {'flag': 'cave_treasure'}}],
    'feathers': [{'item': 'moon_tea', 'price': 3}, {'item': 'dragon_scale', 'price': 9000}],
    'charts': [{'item': 'sea_chart', 'price': 60}, {'item': 'bread', 'price': 2}],
}
BUYERS = {'collector': {'coin': 1200, 'float': 900, 'moonstone': 700, 'lucky_hook': 400, 'sea_glass': 1500,
                        'carving': 1500, 'ship_bell': 1000, 'whale_tooth': 1800, 'frost_crystal': 1600,
                        'jade_figure': 2500, 'old_chart': 2000, 'dragon_scale': 6000}}

DAY = [7, 19]
NIGHT = [21, 4]

NPCS = [
    {'id': 'marit', 'name': 'MARIT', 'sprite': 'marit', 'map': 'inn', 'x': 2, 'y': 2},
    {'id': 'halvard', 'name': 'HALVARD', 'sprite': 'halvard', 'map': 'store', 'x': 4, 'y': 2},
    {'id': 'eirik', 'name': 'EIRIK', 'sprite': 'eirik', 'map': 'workshop', 'x': 6, 'y': 3},
    {'id': 'liv', 'name': 'LIV', 'sprite': 'liv', 'map': 'overworld', 'x': 79, 'y': 27, 'when': {'time': [6, 18]}},
    {'id': 'liv_home', 'mem': 'liv', 'dialog': 'liv', 'name': 'LIV', 'sprite': 'liv', 'map': 'fisher', 'x': 4, 'y': 3,
     'when': {'time': [18, 6]}},
    {'id': 'ole', 'name': 'OLE', 'sprite': 'ole', 'map': 'overworld', 'x': 77, 'y': 51},
    {'id': 'tove', 'name': 'TOVE', 'sprite': 'tove', 'map': 'overworld', 'x': 7, 'y': 21, 'when': {'time': DAY}},
    {'id': 'hedda', 'name': 'HEDDA', 'sprite': 'hedda', 'map': 'overworld', 'x': 38, 'y': 21},
    {'id': 'selma', 'name': 'SELMA', 'sprite': 'selma', 'map': 'overworld', 'x': 24, 'y': 35, 'when': {'time': NIGHT}},
    # recurring character: Sigve moves on as his story advances
    {'id': 'sigve_0', 'mem': 'sigve', 'dialog': 'sigve', 'name': 'SIGVE', 'sprite': 'sigve', 'map': 'overworld',
     'x': 12, 'y': 20, 'when': {'stage': 0, 'time': DAY}},
    {'id': 'sigve_1', 'mem': 'sigve', 'dialog': 'sigve', 'name': 'SIGVE', 'sprite': 'sigve', 'map': 'inn',
     'x': 10, 'y': 4, 'when': {'stage': 1}},
    {'id': 'sigve_2', 'mem': 'sigve', 'dialog': 'sigve', 'name': 'SIGVE', 'sprite': 'sigve', 'map': 'overworld',
     'x': 73, 'y': 49, 'when': {'stage': 2, 'time': [6, 21]}},
    {'id': 'sigve_3', 'mem': 'sigve', 'dialog': 'sigve', 'name': 'SIGVE', 'sprite': 'sigve', 'map': 'workshop',
     'x': 9, 'y': 5, 'when': {'stage': 3}},
    # very rare wanderer + rare buyer: some days he is in one of these places, most days nowhere
    {'id': 'collector', 'name': 'AMBROSE', 'sprite': 'collector', 'rare': 0.22, 'time': [9, 20],
     'spots': [{'map': 'inn', 'x': 5, 'y': 6}, {'map': 'overworld', 'x': 27, 'y': 21},
               {'map': 'overworld', 'x': 62, 'y': 47}]},
    # night market (after dark, Keelvik square)
    {'id': 'ingrid', 'name': 'INGRID', 'sprite': 'ingrid', 'map': 'overworld', 'x': 57, 'y': 22,
     'when': {'time': [20, 4]}},
    {'id': 'joar', 'name': 'JOAR', 'sprite': 'joar', 'map': 'overworld', 'x': 61, 'y': 22,
     'when': {'time': [20, 4]}},
    # Fyrholm (lighthouse keeper's island) and Mossholt (caretaker's settlement)
    {'id': 'brit', 'name': 'BRIT', 'sprite': 'brit', 'map': 'overworld', 'x': 88, 'y': 52, 'when': {'fd1': 'keeper'}},
    {'id': 'tobias', 'name': 'TOBIAS', 'sprite': 'tobias', 'map': 'overworld', 'x': 91, 'y': 53, 'when': {'fd1': 'keeper'}},
    {'id': 'arne', 'name': 'ARNE', 'sprite': 'arne', 'map': 'overworld', 'x': 8, 'y': 47, 'when': {'fd1': 'caretaker'}},
    {'id': 'ylva', 'name': 'YLVA', 'sprite': 'ylva', 'map': 'overworld', 'x': 12, 'y': 49, 'when': {'fd1': 'caretaker'}},
]

S = 'say'
DIALOG = {
    'marit': [
        {'if': {'has': 'ring'}, 'do': [
            [S, 'MY RING! I LOST IT BY THE RIVER WEEKS AGO.'],
            [S, 'TAKE THIS KEY. THE CELLAR HAS BEEN SHUT SINCE OLD BJORN WENT NORTH. MAYBE HE LEFT SOMETHING USEFUL.'],
            ['take', 'ring'], ['give', 'cellar_key'], ['flag', 'ring_returned']]},
        {'if': {'companion': 'fox', 'not_flag': 'marit_fox'}, 'do': [
            [S, 'IS THAT A FOX? KEEP IT AWAY FROM MY HENS!'], ['flag', 'marit_fox']]},
        {'if': {'companion': 'owl', 'not_flag': 'marit_owl'}, 'do': [
            [S, 'AN OWL INDOORS... MY MOTHER SAID THAT BRINGS GOOD LUCK.'], ['flag', 'marit_owl']]},
        {'if': {'talked': 4, 'not_flag': 'marit_gift'}, 'do': [
            [S, 'YOU\'RE PRACTICALLY A REGULAR NOW. HAVE A LOAF, ON THE HOUSE.'], ['give', 'bread'], ['flag', 'marit_gift']]},
        {'if': {'flag': 'ring_returned', 'not_flag': 'cellar_seen'}, 'do': [
            [S, 'THE CELLAR DOOR IS AT THE BACK. MIND THE STAIRS.']]},
        {'if': {'talked': 1, 'not_flag': 'ring_returned'}, 'do': [
            [S, 'STILL NO SIGN OF MY RING. I WAS CUTTING REEDS ON THE SOUTH BANK OF THE LAUVA WHEN I LOST IT.']]},
        {'if': {'flag': 'ring_returned'}, 'do': [[S, 'STEW\'S ON. THE WIND\'S OFF THE SEA TONIGHT.']]},
        {'do': [[S, 'WELCOME TO THE KEELVIK INN. WARM STEW, COLD WIND.'],
                [S, 'IF YOU WANDER UP THE RIVER, KEEP AN EYE OUT FOR A SILVER RING. I LOST MINE.']]},
    ],
    'halvard': [
        {'if': {'flag': 'cave_treasure', 'not_flag': 'halvard_plans'}, 'do': [
            [S, 'HEARD YOU STRUCK IT RICH. I\'VE GOT SOMETHING NEW: EIRIK\'S FULL SHIP PLANS. PRICEY, MIND.'],
            ['flag', 'halvard_plans'], ['shop', 'store']]},
        {'do': [[S, 'HALVARD\'S GOODS. EVERYTHING A COAST-WALKER NEEDS.'], ['shop', 'store']]},
    ],
    'eirik': [
        {'if': {'has': 'ship_plans'}, 'do': [
            [S, 'THE FULL PLANS! WITH THESE SHE\'LL SAIL ONE DAY. I\'LL SEND WORD WHEN SHE\'S READY.'],
            ['take', 'ship_plans'], ['flag', 'ship_plans_given']]},
        {'if': {'flag': 'ship_plans_given'}, 'do': [[S, 'FOLLOWING THE PLANS TO THE LETTER. PATIENCE.']]},
        {'if': {'talked': 2, 'not_has': 'running_shoes'}, 'do': [
            [S, 'WHEN I WAS A BOY, A COURIER RAN FROM KEELVIK TO LAUVDAL IN NO TIME AT ALL.'],
            [S, 'WHEN HE RETIRED HE HID HIS SHOES IN THE WOODS, BY THE FLOWER FIELD EAST OF LAUVDAL. NOBODY EVER FOUND THEM.']]},
        {'if': {'talked': 1}, 'do': [
            [S, 'A SHIP THAT SIZE NEEDS PROPER PLANS. HALVARD MIGHT GET SOME, BUT NOT CHEAP.']]},
        {'do': [[S, 'THAT HULL IN THE DRY DOCK? MY LIFE\'S WORK. SHE\'LL CROSS THE VIDSEA ONE DAY.']]},
    ],
    'liv': [
        {'if': {'has': 'knife'}, 'do': [
            [S, 'MY GRANDMOTHER\'S KNIFE! WHERE DID YOU DIG THAT UP?'],
            [S, 'TAKE MY LUCKY HOOK. FAIR TRADE.'], ['take', 'knife'], ['give', 'lucky_hook'], ['flag', 'knife_returned']]},
        {'if': {'flag': 'sigve_asked', 'not_flag': 'plank_given'}, 'do': [
            [S, 'THE TERN DRIFTWOOD? IT WASHED UP BY MY DOOR. HERE, TAKE IT TO HIM.'],
            ['give', 'tern_plank'], ['flag', 'plank_given']]},
        {'if': {'days': 3, 'not_flag': 'liv_gift'}, 'do': [
            [S, 'YOU KEEP COMING BACK. I LIKE THAT. A SMOKED FISH FOR THE ROAD.'], ['give', 'smoked_fish'],
            ['flag', 'liv_gift']]},
        {'if': {'companion': 'fox', 'not_flag': 'liv_fox'}, 'do': [
            [S, 'YOUR FOX IS STARING AT MY BUCKET. FINE, ONE SPRAT.'], ['flag', 'liv_fox']]},
        {'if': {'time': [18, 6]}, 'do': [[S, 'THE NETS CAN WAIT TILL MORNING.']]},
        {'if': {'talked': 1}, 'do': [
            [S, 'THE NORTH CURRENT IS COLD ENOUGH TO STOP AN OTTER. SEALS DON\'T MIND IT.'],
            [S, 'AND MY GRANDMOTHER\'S KNIFE IS STILL OUT THERE IN THE SAND SOMEWHERE.']]},
        {'do': [[S, 'MORNING! I\'M LIV. I FISH OFF THIS PIER EVERY DAY, RAIN OR SHINE.'],
                [S, 'I LOST MY GRANDMOTHER\'S KNIFE ON THE BEACH SOUTH OF HERE. SAND EATS EVERYTHING.']]},
    ],
    'ole': [
        {'if': {'fd1': 'keeper'}, 'do': [
            ['choice', 'SHALL I ROW YOU OVER TO FYRHOLM?', [
                ['YES', [['warp', 'overworld', 85, 52, 'right']]], ['NOT NOW', []]]]]},
        {'if': {'fd1': 'caretaker'}, 'do': [
            [S, 'THE AMBER WENT TO THE FOREST, I HEAR. WELL, THE WOODS NEED LIGHT TOO.']]},
        {'if': {'has': 'amber_heart'}, 'do': [
            [S, 'IS THAT... AN AMBER HEART? MY FATHER SAID ONE COULD WAKE THE OLD BEACON ON FYRHOLM.'],
            ['confirm', 'GIVE THE AMBER HEART TO OLE? YOU CAN ONLY GIVE IT ONCE.', [
                ['take', 'amber_heart'], ['fd1', 'keeper'],
                [S, 'THE BEACON ON FYRHOLM IS SHINING AGAIN! ASK ME ANY TIME AND I\'LL ROW YOU OVER.']]]]},
        {'if': {'flag': 'lantern_given'}, 'do': [[S, 'HOW\'S THE LANTERN? IT LIT MY WAY FOR FORTY YEARS.']]},
        {'if': {'has': 'lamp_oil'}, 'do': [
            [S, 'LAMP OIL! BLESS YOU.'], [S, 'TAKE MY OLD LANTERN. YOU\'LL NEED IT MORE THAN ME.'],
            ['take', 'lamp_oil'], ['give', 'lantern'], ['flag', 'lantern_given']]},
        {'if': {'talked': 1}, 'do': [[S, 'HALVARD SELLS LAMP OIL IN KEELVIK. JUST A FEW COINS.']]},
        {'do': [[S, 'I\'M OLE. I KEEP THE LIGHT ON SULE NESS.'],
                [S, 'I\'M OUT OF LAMP OIL, AND MY KNEES WON\'T TAKE ME TO TOWN. COULD YOU BRING ME SOME?']]},
    ],
    'tove': [
        {'if': {'fd1': 'caretaker'}, 'do': [
            [S, 'THE OLD PATH TO MOSSHOLT IS OPEN. WEST FROM THE MOONLIT GROVE.']]},
        {'if': {'fd1': 'keeper'}, 'do': [
            [S, 'SO THE LIGHTHOUSE GOT IT. THE SEA AND THE FOREST ARE OLD FRIENDS, YOU KNOW.']]},
        {'if': {'has': 'amber_heart'}, 'do': [
            [S, 'AN AMBER HEART... THE OLD LINDEN AT MOSSHOLT HAS BEEN WAITING FOR ONE.'],
            ['confirm', 'GIVE THE AMBER HEART TO TOVE? YOU CAN ONLY GIVE IT ONCE.', [
                ['take', 'amber_heart'], ['fd1', 'caretaker'], ['open', 'mossholt'],
                [S, 'LISTEN... THE THICKET WEST OF THE GROVE IS PARTING. MOSSHOLT WELCOMES YOU.']]]]},
        {'if': {'talked': 1, 'not_has': 'axe'}, 'do': [
            [S, 'MY OLD AXE IS STILL STUCK IN A STUMP NORTH OF THE RIVER. TAKE THE PATH OVER THE LITTLE BRIDGE.']]},
        {'if': {'talked': 1, 'not_has': 'otter_stick'}, 'do': [
            [S, 'THE STORM BROUGHT TREES DOWN ACROSS THE PATH TO THE MOONLIT GROVE, SOUTH OF HERE. YOUR AXE WILL CLEAR THEM.'],
            [S, 'OLD EDVIN KEEPS OTTERS BY THE POND IN THE GROVE. HE COULD USE A VISIT.']]},
        {'if': {'talked': 1}, 'do': [
            [S, 'THEY SAY A HEART OF AMBER SLEEPS UNDER SULE NESS. IF YOU FIND IT, THINK OF THE FOREST.']]},
        {'do': [[S, 'I\'M TOVE. I LOOK AFTER THESE WOODS.'],
                [S, 'I LEFT MY OLD AXE IN A STUMP NORTH OF THE RIVER, OVER THE LITTLE BRIDGE. TAKE IT, IF YOU CAN USE IT.']]},
    ],
    'hedda': [
        {'if': {'companion': 'fox'}, 'do': [
            [S, 'HOW\'S MY LITTLE FOX? THEY CAN SMELL A COIN THROUGH A FOOT OF SAND.']]},
        {'if': {'companion': 'owl'}, 'do': [
            [S, 'HOW\'S MY LITTLE OWL? THEY SEE PATHS THE REST OF US WALK RIGHT PAST.']]},
        {'do': [[S, 'I\'M HEDDA. I NURSE ORPHANED ANIMALS. THESE TWO ARE READY FOR A HOME.'],
                ['choice', 'TAKE ONE WITH YOU? YOU CAN ONLY CHOOSE ONE.', [
                    ['THE FOX KIT', [['confirm', 'TAKE THE FOX? IT WILL BE YOUR COMPANION FOR GOOD.', [
                        ['companion', 'fox'],
                        [S, 'SHE\'S CURIOUS AND HAS A NOSE FOR BURIED THINGS. PRESS C TO LET HER HIDE OR FOLLOW.']]]]],
                    ['THE OWLET', [['confirm', 'TAKE THE OWL? IT WILL BE YOUR COMPANION FOR GOOD.', [
                        ['companion', 'owl'],
                        [S, 'HE NOTICES HIDDEN WAYS. PRESS C TO LET HIM HIDE OR FOLLOW.']]]]],
                    ['NOT YET', [[S, 'TAKE YOUR TIME. THEY\'RE NOT GOING ANYWHERE.']]]]]]},
    ],
    'selma': [
        {'if': {'companion': 'owl', 'not_flag': 'selma_owl'}, 'do': [
            [S, 'AN OWL! THE NIGHT\'S OWN EYES. HE LIKES YOU.'], ['flag', 'selma_owl']]},
        {'if': {'days': 2, 'not_flag': 'selma_gift'}, 'do': [
            [S, 'YOU CAME BACK UNDER THE MOON. TAKE THIS MOONSTONE.'], ['give', 'moonstone'], ['flag', 'selma_gift']]},
        {'if': {'talked': 1}, 'do': [
            [S, 'AT DAWN THE SEA PULLS BACK BELOW SULE NESS. A SANDBAR APPEARS FOR AN HOUR OR THREE.']]},
        {'do': [[S, 'SHH... I ONLY COME HERE WHEN THE MOON IS UP. I\'M SELMA.'],
                [S, 'THE STONES REMEMBER EVERY NIGHT THEY\'VE SEEN.']]},
    ],
    'sigve': [
        {'if': {'stage': 0}, 'do': [
            [S, 'HELLO, CARTOGRAPHER. I\'M SIGVE. I WALK THE COAST LOOKING FOR MY BROTHER\'S BOAT, THE LITTLE TERN.'],
            [S, 'SHE WENT DOWN IN A STORM LAST WINTER. I\'LL REST AT THE KEELVIK INN TONIGHT.'], ['stage', 1]]},
        {'if': {'stage': 1, 'has': 'tern_plank'}, 'do': [
            [S, 'THAT\'S ARVID\'S CARVING... THANK YOU.'],
            [S, 'I NEED SOME AIR. FIND ME ON SULE NESS, WHERE YOU CAN SEE THE OPEN SEA.'],
            ['take', 'tern_plank'], ['stage', 2]]},
        {'if': {'stage': 1}, 'do': [
            [S, 'A FISHER HERE, LIV, SAW DRIFTWOOD WITH A TERN CARVED ON IT. COULD YOU ASK HER FOR ME?'],
            ['flag', 'sigve_asked']]},
        {'if': {'stage': 2}, 'do': [
            [S, 'I\'VE DECIDED TO STAY IN KEELVIK. EIRIK NEEDS HANDS FOR HIS BIG SHIP.'],
            [S, 'TAKE ARVID\'S COMPASS. IT ALWAYS FOUND ITS WAY HOME. AND THIS, FOR YOUR TROUBLE.'],
            ['give', 'compass'], ['coins', 300], ['stage', 3]]},
        {'do': [[S, 'PLANING OAK ALL DAY. ARVID WOULD HAVE LAUGHED AT MY BLISTERS.']]},
    ],
    'collector': [
        {'do': [[S, 'AMBROSE, COLLECTOR OF CURIOSITIES. I PAY HANDSOMELY FOR THE RIGHT THINGS.'], ['sell', 'collector']]},
    ],
    'ingrid': [
        {'if': {'talked': 1, 'not_has': 'dragon_scale'}, 'do': [
            [S, 'THE DRAGON SCALE CAME ON A SHIP FROM THE FAR EAST, LONG AGO. NO SHIP HAS GONE BACK SINCE. PRICED LIKE A HOUSE, I KNOW.'],
            ['shop', 'feathers']]},
        {'do': [[S, 'FEATHERS, CURIOS AND MOON TEA. THE NIGHT MARKET ONLY OPENS AFTER DARK.'], ['shop', 'feathers']]},
    ],
    'joar': [
        {'do': [[S, 'CHARTS OF EVERY SHORE I\'VE SAILED. CHEAP, AS THE SEA IS FREE.'], ['shop', 'charts']]},
    ],
    'brit': [
        {'if': {'talked': 1}, 'do': [[S, 'THE TIDE POOLS ON THE WEST SHORE HOLD SEA GLASS. COLLECTORS LOVE IT.']]},
        {'do': [[S, 'WELCOME TO FYRHOLM! OLE\'S MY BROTHER. YOU WOKE OUR OLD BEACON.'],
                [S, 'THE PUFFINS NEST ON THE NORTH CLIFFS. MIND YOUR FEET.']]},
    ],
    'tobias': [
        {'if': {'days': 2, 'not_flag': 'tobias_gift'}, 'do': [
            [S, 'FOUND THIS POUCH IN A BURROW. THE PUFFINS DON\'T NEED COINS.'], ['coins', 400], ['flag', 'tobias_gift']]},
        {'do': [[S, 'I\'VE COUNTED PUFFINS HERE FOR THIRTY YEARS. TWO HUNDRED AND TWELVE TODAY.']]},
    ],
    'arne': [
        {'if': {'talked': 1, 'not_flag': 'arne_gift'}, 'do': [
            [S, 'I CARVED THIS FOR YOU, FROM A FALLEN LINDEN BRANCH.'], ['give', 'carving'], ['flag', 'arne_gift']]},
        {'do': [[S, 'WELCOME TO MOSSHOLT. FEW OUTSIDERS EVER FIND US.'],
                [S, 'TOVE SAYS YOU BROUGHT THE AMBER. THE OLD LINDEN HASN\'T HUMMED LIKE THIS IN YEARS.']]},
    ],
    'ylva': [
        {'if': {'has': 'bread', 'not_flag': 'ylva_bread'}, 'do': [
            [S, 'IS THAT BREAD? TRADE YOU! I FOUND THESE BY THE STREAM.'], ['take', 'bread'], ['coins', 150],
            ['flag', 'ylva_bread']]},
        {'do': [[S, 'THE LINDEN SANG LAST NIGHT! GRANDPA ARNE SAYS IT\'S BECAUSE OF THE AMBER.']]},
    ],
}

CHESTS = [
    {'id': 'c_seal', 'map': 'overworld', 'x': 77, 'y': 53, 'coins': 150, 'msg': 'OLE\'S RAINY-DAY MONEY? HE WON\'T MIND.'},
    {'id': 'c_coin', 'map': 'overworld', 'x': 29, 'y': 13, 'item': 'coin', 'msg': 'ONLY REACHABLE OVER THE ICE.'},
    {'id': 'c_float', 'map': 'overworld', 'x': 89, 'y': 39, 'item': 'float'},
    {'id': 'c_stick', 'map': 'overworld', 'x': 18, 'y': 8, 'item': 'walking_stick'},
    {'id': 'c_shoes', 'map': 'overworld', 'x': 36, 'y': 35, 'item': 'running_shoes',
     'msg': 'A NOTE INSIDE: "FOR WHOEVER IS CURIOUS ENOUGH TO FIND THESE. RUN WELL." - THE OLD COURIER'},
    {'id': 'c_bell', 'map': 'cave', 'x': 20, 'y': 9, 'item': 'bird_bell',
     'msg': 'FEATHERS AS LONG AS YOUR ARM ARE TIED TO THE BELL. SOMETHING ENORMOUS ANSWERS TO IT.'},
    {'id': 'c_shipbell', 'map': 'cellar', 'x': 6, 'y': 2, 'item': 'ship_bell'},
    {'id': 'c_plateau', 'map': 'overworld', 'x': 21, 'y': 1, 'coins': 3000, 'msg': 'THE OLD WATCH\'S PAYCHEST!'},
    {'id': 'c_tide', 'map': 'overworld', 'x': 81, 'y': 34, 'coins': 800, 'msg': 'THE SEA ONLY LETS YOU HERE AT DAWN.'},
    {'id': 'c_hollow', 'map': 'overworld', 'x': 39, 'y': 8, 'coins': 500},
    {'id': 'c_glade', 'map': 'overworld', 'x': 44, 'y': 40, 'coins': 500},
    {'id': 'c_fyrholm', 'map': 'overworld', 'x': 89, 'y': 56, 'coins': 600},
    {'id': 'c_mossholt', 'map': 'overworld', 'x': 13, 'y': 52, 'coins': 600},
    {'id': 'c_amber', 'map': 'cave', 'x': 23, 'y': 2, 'item': 'amber_heart',
     'msg': 'WHO SHOULD HAVE IT? THE LIGHTHOUSE KEEPER, OR THE FOREST CARETAKER?'},
    {'id': 'c_treasure', 'map': 'cave', 'x': 26, 'y': 2, 'coins': 5000, 'flag': 'cave_treasure',
     'msg': 'A SMUGGLER\'S HOARD!'},
]

SIGNS = [
    {'map': 'overworld', 'x': 51, 'y': 21, 'lines': ['KEELVIK. BOATS HAVE BEEN BUILT HERE FOR AGES.']},
    {'map': 'overworld', 'x': 44, 'y': 21, 'lines': ['LAUVDAL. WEST: GREINHOLT. EAST: KEELVIK.']},
    {'map': 'overworld', 'x': 60, 'y': 31, 'lines': ['SULE NESS LIGHTHOUSE. MIND THE LEDGES ON THE WAY DOWN.']},
    {'map': 'overworld', 'x': 14, 'y': 1, 'lines': ['THE OLD WATCH ON ERNE CLIFF.',
                                                     'FROM HERE THEY SAY YOU COULD SEE ALL OF RAVENMARK.']},
    {'map': 'overworld', 'x': 87, 'y': 54, 'lines': ['THE OLD BEACON OF FYRHOLM.', 'IT SHINES AGAIN, THANKS TO THE AMBER HEART.']},
    {'map': 'overworld', 'x': 8, 'y': 53, 'lines': ['THE OLD LINDEN.', 'ITS LEAVES HUM WHEN THE WIND IS RIGHT.']},
    {'map': 'cellar', 'x': 4, 'y': 4, 'kind': 'note', 'lines': [
        'A NOTE: "OFF NORTH. LEFT MY PICK WITH MY SISTER GERDA IN COPPERHAVN, ACROSS THE WATER TO THE SOUTH.',
        'THE CRACKED ROCK ON SULE NESS HIDES A CAVE. DON\'T GO IN WITHOUT A LIGHT. - BJORN"']},
    {'map': 'overworld', 'x': 64, 'y': 19, 'lines': ['FERRY TO COPPERHAVN.', 'ONE DAY HERE, THE NEXT DAY THERE. PASSES FROM CAPTAIN NILS.']},
]
for sg in SIGNS:
    sg.setdefault('kind', 'sign')

# obstacles: removed for good once cleared (needs: an item, a gate opened by the story, or the owl)
OBSTACLES = [
    {'id': 'tree_grove', 'map': 'overworld', 'x': 22, 'y': 26, 'kind': 'fallen_tree', 'needs': 'axe'},
    {'id': 'tree_grove2', 'map': 'overworld', 'x': 22, 'y': 28, 'kind': 'fallen_tree', 'needs': 'axe'},
    {'id': 'rock_cave_b1', 'map': 'cave', 'x': 6, 'y': 6, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
    {'id': 'rock_cave_b2', 'map': 'cave', 'x': 7, 'y': 6, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
    {'id': 'rock_cave', 'map': 'overworld', 'x': 48, 'y': 52, 'kind': 'cracked_rock', 'needs': 'pickaxe'},
    {'id': 'hedge_hollow', 'map': 'overworld', 'x': 38, 'y': 11, 'kind': 'hedge', 'needs': 'owl'},
    {'id': 'hedge_glade', 'map': 'overworld', 'x': 48, 'y': 40, 'kind': 'hedge', 'needs': 'owl'},
] + [{'id': f'thicket_{i}', 'map': 'overworld', 'x': x, 'y': y, 'kind': 'thicket', 'needs': 'gate:mossholt'}
     for i, (x, y) in enumerate([(14, 37), (15, 37), (13, 38), (14, 38)])]

PICKUPS = [   # things lying around (sparkle, or an object you take from)
    {'id': 'p_ring', 'map': 'overworld', 'x': 24, 'y': 17, 'item': 'ring', 'kind': 'sparkle'},
    {'id': 'p_seaglass', 'map': 'overworld', 'x': 86, 'y': 53, 'item': 'sea_glass', 'kind': 'sparkle'},
    {'id': 'p_axe', 'map': 'overworld', 'x': 16, 'y': 7, 'item': 'axe', 'kind': 'axe_stump'},
]

SECRETS = [   # companion abilities: the fox digs things up, the owl spots hidden ways
    {'id': 's_pouch', 'type': 'fox', 'map': 'overworld', 'x': 3, 'y': 17, 'coins': 500},
    {'id': 's_knife', 'type': 'fox', 'map': 'overworld', 'x': 73, 'y': 30, 'item': 'knife'},
    {'id': 's_hollow', 'type': 'owl', 'map': 'overworld', 'x': 38, 'y': 11, 'obstacle': 'hedge_hollow'},
    {'id': 's_glade', 'type': 'owl', 'map': 'overworld', 'x': 48, 'y': 40, 'obstacle': 'hedge_glade'},
]

PERCHES = [   # Bird Bell: from one perch the great erne carries you to the other side
    {'id': 'perch_s', 'map': 'overworld', 'x': 17, 'y': 6, 'land': [17, 1], 'face': 'up'},
    {'id': 'perch_n', 'map': 'overworld', 'x': 17, 'y': 2, 'land': [17, 7], 'face': 'down'},
]

WARPS = [   # step in direction `dir` onto (x, y) to go through
    {'map': 'overworld', 'x': 49, 'y': 9, 'dir': 'up', 'to': 'inn', 'tx': 6, 'ty': 7, 'face': 'up'},
    {'map': 'overworld', 'x': 62, 'y': 9, 'dir': 'up', 'to': 'store', 'tx': 5, 'ty': 6, 'face': 'up'},
    {'map': 'overworld', 'x': 66, 'y': 13, 'dir': 'up', 'to': 'workshop', 'tx': 5, 'ty': 6, 'face': 'up'},
    {'map': 'overworld', 'x': 49, 'y': 25, 'dir': 'up', 'to': 'fisher', 'tx': 4, 'ty': 5, 'face': 'up'},
    {'map': 'overworld', 'x': 54, 'y': 29, 'dir': 'up', 'locked': 'NOBODY HOME. THE DOOR IS LOCKED.'},
    {'map': 'overworld', 'x': 47, 'y': 52, 'dir': 'left', 'to': 'cave', 'tx': 37, 'ty': 12, 'face': 'left'},
    {'map': 'overworld', 'x': 28, 'y': 30, 'dir': 'up', 'to': 'cave', 'tx': 5, 'ty': 1, 'face': 'down'},
    {'map': 'inn', 'x': 6, 'y': 8, 'dir': 'down', 'to': 'overworld', 'tx': 49, 'ty': 10, 'face': 'down'},
    {'map': 'inn', 'x': 11, 'y': 1, 'dir': 'up', 'to': 'cellar', 'tx': 8, 'ty': 2, 'face': 'down',
     'needs': 'cellar_key', 'locked': 'THE CELLAR DOOR IS LOCKED. MARIT MUST HAVE THE KEY.', 'flag': 'cellar_seen'},
    {'map': 'cellar', 'x': 8, 'y': 1, 'dir': 'up', 'to': 'inn', 'tx': 11, 'ty': 2, 'face': 'down'},
    {'map': 'store', 'x': 5, 'y': 7, 'dir': 'down', 'to': 'overworld', 'tx': 62, 'ty': 10, 'face': 'down'},
    {'map': 'workshop', 'x': 5, 'y': 7, 'dir': 'down', 'to': 'overworld', 'tx': 66, 'ty': 14, 'face': 'down'},
    {'map': 'fisher', 'x': 4, 'y': 6, 'dir': 'down', 'to': 'overworld', 'tx': 49, 'ty': 26, 'face': 'down'},
    {'map': 'cave', 'x': 38, 'y': 12, 'dir': 'right', 'to': 'overworld', 'tx': 48, 'ty': 52, 'face': 'right'},
    {'map': 'cave', 'x': 5, 'y': 0, 'dir': 'up', 'to': 'overworld', 'tx': 28, 'ty': 31, 'face': 'down'},
]

TIMED = [   # decor that only exists at certain times (night market) / gated places
    {'kind': 'stall_a', 'map': 'overworld', 'x': 57, 'y': 23, 'when': {'time': [20, 4]}, 'block': [[56, 23], [57, 23], [58, 23]]},
    {'kind': 'stall_b', 'map': 'overworld', 'x': 61, 'y': 23, 'when': {'time': [20, 4]}, 'block': [[60, 23], [61, 23], [62, 23]]},
]

BOATS = [   # interacting with Ole's boat on Fyrholm rows you back
    {'map': 'overworld', 'x': 84, 'y': 53, 'to': 'overworld', 'tx': 78, 'ty': 53, 'face': 'down',
     'ask': 'ROW BACK TO SULE NESS?'},
]

TEXTS = {
    'intro': 'WELCOME TO KEELVIK, CARTOGRAPHER. TALK TO PEOPLE AND EXPLORE. PRESS H FOR HELP.',
    'no_otter': 'THE WATER IS TOO DEEP TO WADE INTO. IF ONLY SOMETHING COULD CARRY YOU.',
    'ocean_deep': 'THE OPEN OCEAN. WAVES TALLER THAN HOUSES, WATER BLACK AND DEEP. NOTHING YOU HAVE WILL SWIM OUT THERE.',
    'whale_on': 'YOU BLOW THE WHALE HORN. A WHALE RISES BENEATH YOU!',
    'fallen_tree': 'A FALLEN TREE BLOCKS THE PATH. AN AXE WOULD CLEAR IT.',
    'fallen_tree_cut': 'YOU CHOP THROUGH THE TRUNK AND ROLL THE LOGS ASIDE. THE PATH IS CLEAR.',
    'edge_closed': 'THE WAY ON IS TOO WILD TO CROSS.',
    'dragon_rest': 'THE DRAGON IS STILL RESTING. IT WILL ANSWER AGAIN IN %d MINUTES.',
    'dragon_indoors': 'THE DRAGON WON\'T FIT INDOORS.',
    'dragon_none': 'THE DRAGON HAS NOWHERE ELSE TO TAKE YOU YET. WALK TO NEW PLACES FIRST.',
    'dragon_call': 'YOU RAISE THE DRAGON BAND. FAR AWAY, SOMETHING LONG AND RED UNCOILS.',
    'landing_found': 'A DRAGON COULD LAND HERE.',
    'telescope': 'AN OLD BRASS TELESCOPE ON A STAND.',
    'otter_cold': 'THE OTTER SHIVERS AND TURNS BACK. THIS WATER IS TOO COLD.',
    'seal_on': 'YOU PLAY THE SEAL FLUTE. A SEAL TAKES OVER IN THE COLD WATER.',
    'frozen': 'THE WATER IS FROZEN. YOU CAN WALK ON THE ICE.',
    'reef': 'THE REEF IS TOO ROUGH TO SWIM THROUGH.',
    'shallows': 'TOO SHALLOW AND ROCKY TO SWIM. MAYBE THE TIDE WILL PULL BACK.',
    'sapling': 'A YOUNG TREE HAS GROWN RIGHT IN THE PATH. AN AXE WOULD CLEAR IT.',
    'sapling_cut': 'YOU SWING THE AXE. THE PATH IS CLEAR.',
    'cracked_rock': 'A CRACKED ROCK. A PICKAXE COULD BREAK IT.',
    'cracked_rock_cut': 'CRACK! THE ROCK BREAKS APART.',
    'thicket': 'A WALL OF THORNS. IT FEELS LIKE IT\'S GUARDING SOMETHING.',
    'hedge': 'A THICK HEDGE.',
    'dark': 'IT\'S PITCH DARK. YOU NEED A LIGHT TO GO ON.',
    'lantern_on': 'YOU LIGHT THE LANTERN.',
    'perch': 'A TALL PERCH STREAKED WITH WHITE. SOMETHING BIG ROOSTS HERE. A BIRD BELL MIGHT CALL IT.',
    'perch_ring': 'YOU RING THE BIRD BELL. THE GREAT ERNE SWOOPS DOWN!',
    'fox_sniff': 'YOUR FOX SNIFFS THE GROUND. SOMETHING IS BURIED NEARBY.',
    'fox_dig': 'YOUR FOX DIGS...',
    'owl_spot': 'YOUR OWL HOOTS. IT SPOTTED A HIDDEN WAY THROUGH!',
    'not_enough': 'NOT ENOUGH COINS.',
    'bought': 'BOUGHT!',
    'nothing_to_sell': 'NOTHING I COLLECT, I\'M AFRAID. I\'LL BE AROUND... NOW AND THEN.',
    'new_game': 'START A NEW GAME? YOUR CURRENT SAVE WILL BE ERASED.',
}

ZONES = [   # location banners; the first matching rectangle wins (map, x0, y0, x1, y1, title, subtitle)
    ['overworld', 15, 28, 33, 39, 'MOONLIT GROVE', 'DEEP IN THE WOODS'],
    ['overworld', 1, 40, 17, 57, 'MOSSHOLT', 'HIDDEN SETTLEMENT'],
    ['overworld', 82, 44, 95, 61, 'FYRHOLM', 'BEACON ISLAND'],
    ['overworld', 10, 0, 24, 2, 'ERNE CLIFF', 'THE OLD WATCH'],
    ['overworld', 36, 7, 41, 9, "OWL'S HOLLOW", 'A SECRET CLEARING'],
    ['overworld', 42, 39, 47, 41, 'FAIRY GLADE', 'A SECRET CLEARING'],
    ['overworld', 80, 34, 82, 36, 'TIDE ISLET', 'ONLY AT LOW TIDE'],
    ['overworld', 0, 0, 45, 30, 'LAUVDAL', 'ROUTE 16'],
    ['overworld', 46, 0, 73, 30, 'KEELVIK', 'BOATWRIGHT VILLAGE'],
    ['overworld', 0, 31, 95, 63, 'SULE NESS', 'ROUTE 17'],
    ['inn', 0, 0, 99, 99, 'KEELVIK INN', 'WARM STEW, COLD WIND'],
    ['cellar', 0, 0, 99, 99, 'INN CELLAR', 'MIND THE STAIRS'],
    ['store', 0, 0, 99, 99, "HALVARD'S GOODS", 'KEELVIK'],
    ['workshop', 0, 0, 99, 99, "EIRIK'S WORKSHOP", 'KEELVIK'],
    ['fisher', 0, 0, 99, 99, "LIV'S HOUSE", 'KEELVIK'],
    ['cave', 0, 0, 99, 99, 'SULE NESS CAVE', 'UNDER THE HEADLAND'],
]
SEA_ZONES = {'~': ['THE VIDSEA', 'OPEN WATER'], '!': ['RIMESTREAM', 'COLD WATER']}
MARKET = {'zone': 'KEELVIK', 'time': [20, 4], 'sub': 'NIGHT MARKET TONIGHT'}

WORLDMAP = {   # where the prototype area sits on the region map (cells of the 100 x 25 overview grid)
    'origin_cell': [42.0, 5.0], 'origin_tile': [58, 18], 'scale': [0.24, 0.083],
    'rooms': {'inn': [49, 9], 'cellar': [49, 9], 'store': [62, 9], 'workshop': [66, 13], 'fisher': [49, 25], 'cave': [38, 41]},
}


def build():
    data = {'items': {k: {'name': n, 'desc': d, 'key': k in KEY_ITEMS} for k, (n, d) in ITEMS.items()},
            'shops': SHOPS, 'buyers': BUYERS, 'npcs': NPCS, 'dialog': DIALOG, 'chests': CHESTS, 'signs': SIGNS,
            'obstacles': OBSTACLES, 'pickups': PICKUPS, 'secrets': SECRETS, 'perches': PERCHES, 'warps': WARPS,
            'timed': TIMED, 'boats': BOATS, 'texts': TEXTS, 'worldmap': WORLDMAP, 'start_coins': 30,
            'zones': ZONES, 'sea_zones': SEA_ZONES, 'market': MARKET}
    import proto_content2
    data = proto_content2.merge(data)
    with open(OUT, 'w') as f:
        json.dump(data, f, indent=1)
    return data


if __name__ == '__main__':
    d = build()
    print(len(d['npcs']), 'npcs,', len(d['dialog']), 'dialogs,', len(d['items']), 'items,', len(d['chests']), 'chests')
