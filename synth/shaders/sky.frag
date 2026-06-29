#version 330 core
in vec3 v_dir;
uniform vec3 u_sky_top;
uniform vec3 u_sky_horizon;
uniform vec3 u_sun_dir;
out vec4 f_color;
void main() {
    float t   = clamp(v_dir.y, 0.0, 1.0);
    vec3  sky = mix(u_sky_horizon, u_sky_top, pow(t, 0.45));
    float sun = max(0.0, dot(normalize(v_dir), normalize(-u_sun_dir)));
    sky += vec3(1.0, 0.95, 0.75) * pow(sun, 200.0);        // disc
    sky += vec3(1.0, 0.80, 0.50) * pow(sun,   5.0) * 0.12; // glow
    f_color = vec4(sky, 1.0);
}
