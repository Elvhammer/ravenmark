// Tilt-shift: blur only the top and bottom bands of the screen; the middle stays pixel-sharp.
// Steps are measured in game pixels (TEXTURE_PIXEL_SIZE), so the blur is visible on the 320x180 image.
shader_type canvas_item;

uniform float band = 0.24;          // fraction of the screen height blurred at the top and at the bottom
uniform float strength = 2.2;       // blur reach in game pixels at the very edge

void fragment() {
	float y = UV.y;
	float a = max(clamp((band - y) / band, 0.0, 1.0), clamp((y - (1.0 - band)) / band, 0.0, 1.0));
	a = pow(a, 1.3);
	vec4 sharp = texture(TEXTURE, UV);
	if (a < 0.01) {
		COLOR = sharp;
	} else {
		vec4 acc = vec4(0.0);
		float wsum = 0.0;
		float stp = strength * a / 3.0;
		for (int i = -3; i <= 3; i++) {
			for (int j = -3; j <= 3; j++) {
				float w = exp(-float(i * i + j * j) / 8.0);
				acc += texture(TEXTURE, UV + vec2(float(i), float(j)) * stp * TEXTURE_PIXEL_SIZE) * w;
				wsum += w;
			}
		}
		COLOR = mix(sharp, acc / wsum, min(1.0, a * 1.4));
	}
}
