"""Style 'eye test' sheets: the same mock frame rendered with one knob changed.

    python3 make_style_sheets.py OUT_DIR
Writes the round 1 + round 2 sheets and baseline frames (phone-friendly
single column, each frame at 2x pixel scale).
"""
import os
import runpy
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOCK = os.path.join(HERE, 'render_ingame_mockup.py')
FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
FN = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
FH = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)

RETRO16 = ['#1E1B2C', '#3D3550', '#6E4A35', '#A8693F', '#E0A256', '#F2E3B3', '#B8483A', '#E48A73',
           '#2F4A35', '#4F7A3C', '#8DB054', '#C6D66E', '#2E5466', '#4E8C95', '#9CD0C9', '#8A8496']

ROUNDS = {
    'style_round1_colours.png': ('ROUND 1A: COLOURS', 'Same frame. Only the colours change.', [
        ('Warm & muted (current)', 'Earthy olive greens, terracotta, slate sea.', {}),
        ('Bright & lively', 'More saturated and cheerful, still not primary.',
         {'palette': {'sat': 1.5, 'val': 1.06, 'contrast': 1.08}}),
        ('Soft pastel', 'Light, airy, low contrast. Toy-box feel.',
         {'palette': {'sat': 0.7, 'lift': 0.22, 'contrast': 0.85}}),
        ('Golden hour', 'Warm late-afternoon light over everything.',
         {'palette': {'tint': (1.10, 0.96, 0.80), 'sat': 1.15, 'contrast': 1.05}}),
        ('Cool overcast', 'Muted, grey-blue, calm and moody.',
         {'palette': {'sat': 0.55, 'tint': (0.92, 0.98, 1.06), 'val': 0.9, 'contrast': 0.95}}),
        ('Retro 16-colour', 'Strict limited palette, punchy retro look.', {'quantize': RETRO16}),
    ]),
    'style_round1_detail.png': ('ROUND 1B: DETAIL & SHAPE', 'Same frame and colours. Only the drawing style changes.', [
        ('Detailed & dithered (current)', 'Speckled grass, checker-pattern shading.', {}),
        ('Medium detail', 'About half the speckles, gentler patterns.', {'detail': 'medium'}),
        ('Clean & flat', 'Big calm colour areas, very little texture.', {'detail': 'clean'}),
        ('Clean + bold outlines', 'Flat colours with dark outlines on every object.',
         {'detail': 'clean', 'outline': 'bold'}),
        ('Soft smooth shading', 'More shades of each colour, no checker patterns.', {'detail': 'smooth'}),
        ('Zoomed in (bigger pixels)', 'Camera closer: bigger pixels and player, less world.', {'zoom': 2}),
    ]),
}


def render(opts):
    g = runpy.run_path(MOCK, init_globals={'OPTS': {'art': 1, **opts}}, run_name='variant')
    return g['final'].convert('RGB')


def sheet(title, sub, variants):
    TW, TH, M, LAB, GAP = 640, 360, 20, 58, 18
    top = 92
    W = TW + 2 * M
    H = top + len(variants) * (LAB + TH + GAP) + 6
    im = Image.new('RGB', (W, H), (43, 38, 34))
    d = ImageDraw.Draw(im)
    d.text((M, 22), title, font=FH, fill=(244, 235, 216))
    d.text((M, 58), sub + ' Pick the 1 or 2 you like.', font=FN, fill=(201, 168, 120))
    y = top
    for i, (name, desc, opts) in enumerate(variants, 1):
        thumb = render(opts).resize((TW, TH), Image.NEAREST)   # exact 2x down: stays pixel-crisp
        d.rectangle([M, y + 6, M + 40, y + 46], fill=(201, 168, 120))
        d.text((M + 20, y + 26), str(i), font=FB, fill=(47, 42, 58), anchor='mm')
        d.text((M + 54, y + 8), name, font=FB, fill=(244, 235, 216))
        d.text((M + 54, y + 36), desc, font=FN, fill=(190, 178, 160))
        y += LAB
        d.rectangle([M - 3, y - 3, M + TW + 2, y + TH + 2], fill=(201, 168, 120))
        im.paste(thumb, (M, y))
        y += TH + GAP
    return im




# ---------------------------------------------------------------- round 2 (after picks: 1A=6, 1B=2 + softer outlines)
WARM16 = ['#2A1F24', '#4B3238', '#7A4B3A', '#B06A42', '#E39A55', '#F6DDAA', '#C6503B', '#EE9A78',
          '#3C4A2C', '#64783A', '#A2A84E', '#D8D178', '#35505A', '#5F8A86', '#A9CDB8', '#9C8C84']
BASE = {'quantize': RETRO16, 'detail': 'medium', 'outline': 'soft'}
ROUND2 = {
    'style_round2.png': ('ROUND 2: FINE-TUNING', 'Your picks + one change each.', [
        ('Your picks (new baseline)', 'Retro 16-colour, medium detail, soft coloured outlines.', BASE),
        ('No outlines', 'Objects separated by shading only.', {**BASE, 'outline': 'none'}),
        ('Warmer retro palette', 'A different 16 colours: browns and warm reds.', {**BASE, 'quantize': WARM16}),
        ('Taller hero', 'Less chibi: longer body and legs.', {**BASE, 'hero': 'tall'}),
        ('Stronger miniature effect', 'More blur at top and bottom. Feels more like a model.', {**BASE, 'tilt': 'strong'}),
        ('Purple-tinted shadows', 'Shadows shift toward purple instead of just darker.',
         {**BASE, 'shadow_tint': (0.86, 0.78, 1.18)}),
    ]),
}


def baseline(scene, path):
    render({**BASE, 'scene': scene}).save(path)


def equip_sheet(path):
    """the hero with each equipment combination (items are separate layers, drawn only when worn)"""
    combos = [('Nothing equipped', ()), ('Pouch', ('pouch',)), ('Walking stick', ('stick',)), ('Pouch + stick', ('pouch', 'stick'))]
    tiles = []
    for label, eq in combos:
        img = render({**BASE, 'scene': 'fennick', 'art': 2, 'equip': eq})
        tiles.append((label, img.crop((588, 284, 700, 404)).resize((224, 240), Image.NEAREST)))
    W = 2 * 224 + 3 * 20
    im = Image.new('RGB', (W, 2 * (240 + 40) + 70), (43, 38, 34))
    d = ImageDraw.Draw(im)
    d.text((20, 18), 'Equipment layers', font=FH, fill=(244, 235, 216))
    for i, (label, t) in enumerate(tiles):
        x, y = 20 + (i % 2) * 244, 70 + (i // 2) * 280
        d.text((x, y), label, font=FN, fill=(201, 168, 120))
        im.paste(t, (x, y + 24))
    im.save(path)


MOUNT_OPTIONS = [
    ('turtle', 'A  Sea turtle', 'Calm giant turtle, plated shell with moss. Steady and friendly.'),
    ('whale', 'B  Whale', 'Huge gentle whale: you ride its back, it spouts. Best sense of scale.'),
    ('manta', 'C  Manta ray', 'Wide ray gliding flat on the surface. Sleek, feels the fastest.'),
    ('crab', 'D  Ferrycrab', 'Giant hermit crab wearing an old ferry cabin. Quirky, can climb beaches.'),
]


def mount_sheet(path, out_dir=None):
    """close-ups (4x, closer than in game) of each sailing mount option in the same sea spot"""
    TW, TH, M, LAB, GAP, top = 640, 360, 20, 58, 18, 92
    im = Image.new('RGB', (TW + 2 * M, top + len(MOUNT_OPTIONS) * (LAB + TH + GAP) + 6), (43, 38, 34))
    d = ImageDraw.Draw(im)
    d.text((M, 22), 'SAILING MOUNT OPTIONS', font=FH, fill=(244, 235, 216))
    d.text((M, 58), 'Same spot at sea. Shown 2x closer than in game. Pick one.', font=FN, fill=(201, 168, 120))
    y = top
    for key, name, desc in MOUNT_OPTIONS:
        full = render({**BASE, 'scene': 'sea', 'art': 2, 'mount': key})
        if out_dir:
            full.save(os.path.join(out_dir, f'mount_{key}.png'))
        thumb = full.crop((480, 262, 800, 442)).resize((TW, TH), Image.NEAREST)
        d.text((M, y + 8), name, font=FB, fill=(244, 235, 216))
        d.text((M, y + 36), desc, font=FN, fill=(190, 178, 160))
        y += LAB
        d.rectangle([M - 3, y - 3, M + TW + 2, y + TH + 2], fill=(201, 168, 120))
        im.paste(thumb, (M, y))
        y += TH + GAP
    im.save(path)


def shot(scene, path, **extra):
    """current look: baseline style + redrawn objects and the new hero (art 2)"""
    render({**BASE, 'scene': scene, 'art': 2, **extra}).save(path)


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    for fname, (title, sub, variants) in {**ROUNDS, **ROUND2}.items():
        p = os.path.join(out_dir, fname)
        sheet(title, sub, variants).save(p)
        print('saved', p)
    for scene in ('fennick', 'canyon'):
        p = os.path.join(out_dir, f'baseline_{scene}.png')
        baseline(scene, p)
        print('saved', p)
    for scene in ('fennick', 'canyon', 'sea', 'snow', 'forest'):
        p = os.path.join(out_dir, f'v2_{scene}.png')
        shot(scene, p)
        print('saved', p)
    equip_sheet(os.path.join(out_dir, 'v2_equipment.png'))
    mount_sheet(os.path.join(out_dir, 'mount_options.png'), out_dir)
