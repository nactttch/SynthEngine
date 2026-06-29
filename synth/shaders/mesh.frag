#version 330 core

in vec3 v_pos;
in vec3 v_normal;
in vec2 v_uv;

uniform vec3  u_light_dir;
uniform vec3  u_light_color;
uniform vec3  u_ambient;
uniform vec3  u_cam_pos;
uniform vec3  u_color;
uniform bool  u_has_texture;
uniform sampler2D u_texture;

// Fog
uniform bool  u_fog;
uniform float u_fog_start;
uniform float u_fog_end;
uniform vec3  u_fog_color;

out vec4 f_color;

void main() {
    vec3 N = normalize(v_normal);
    vec3 L = normalize(-u_light_dir);

    float diff  = max(dot(N, L), 0.0);
    vec3  V     = normalize(u_cam_pos - v_pos);
    vec3  H     = normalize(L + V);
    float spec  = pow(max(dot(N, H), 0.0), 32.0) * 0.4;

    vec3 base = u_has_texture ? texture(u_texture, v_uv).rgb : u_color;
    vec3 lit  = (u_ambient + diff * u_light_color + spec * u_light_color) * base;

    if (u_fog) {
        float d    = length(u_cam_pos - v_pos);
        float t    = clamp((d - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
        lit = mix(lit, u_fog_color, t);
    }

    f_color = vec4(lit, 1.0);
}
