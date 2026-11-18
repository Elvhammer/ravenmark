// Day/night colouring with a palette lookup table (LUT).
//
// The game only ever draws the 16 palette colours. Each pixel is matched to its palette entry
// (row 0 of the LUT), then replaced by that entry's colour for the current time of day
// (rows 1..96, one every 15 minutes from 00:00; neighbouring rows are blended for a smooth change).
// Colours that are NOT in the palette (lit windows, lamps, the lighthouse lamp) pass through untouched,
// so lights stay bright at night. The LUT is a plain 16 x 97 PNG and can be repainted by hand.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform sampler2D lut : filter_nearest;
uniform float time01 = 0.375;        // 0.0 = 00:00, 0.5 = 12:00

const int ROWS = 96;

void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	int best = 0;
	float bd = 1e9;
	for (int i = 0; i < 16; i++) {
		vec3 d = c - texelFetch(lut, ivec2(i, 0), 0).rgb;
		float dd = dot(d, d);
		if (dd < bd) {
			bd = dd;
			best = i;
		}
	}
	if (bd > 0.0006) {
		COLOR = vec4(c, 1.0);                       // a light source: leave it alone
	} else {
		float r = fract(time01) * float(ROWS);
		int r0 = int(floor(r));
		int r1 = (r0 + 1) % ROWS;
		vec3 a = texelFetch(lut, ivec2(best, 1 + r0), 0).rgb;
		vec3 b = texelFetch(lut, ivec2(best, 1 + r1), 0).rgb;
		COLOR = vec4(mix(a, b, fract(r)), 1.0);
	}
}
