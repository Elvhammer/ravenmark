// Darkness for caves: everything is dark except around light points (the lantern, cave mouths, crystals).
// Light falls off in a few dithered steps so it keeps the pixel-art look.
shader_type canvas_item;

uniform vec3 lights[16];             // x, y in viewport pixels, radius in pixels
uniform int count = 0;
uniform vec4 shade : source_color = vec4(0.07, 0.06, 0.12, 1.0);

const float BAYER[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void fragment() {
	vec2 p = floor(SCREEN_UV / SCREEN_PIXEL_SIZE);
	float lit = 0.0;
	for (int i = 0; i < 16; i++) {
		if (i >= count) {
			break;
		}
		float d = distance(p, lights[i].xy) / max(lights[i].z, 1.0);
		lit = max(lit, 1.0 - d);
	}
	int bx = int(mod(p.x, 4.0));
	int by = int(mod(p.y, 4.0));
	float th = (BAYER[by * 4 + bx] / 16.0 - 0.5) * 0.12;
	float v = lit + th;
	float a = 0.94;
	if (v > 0.42) {
		a = 0.0;
	} else if (v > 0.22) {
		a = 0.35;
	} else if (v > 0.06) {
		a = 0.7;
	}
	COLOR = vec4(shade.rgb, a);
}
