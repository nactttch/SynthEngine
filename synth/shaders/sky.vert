#version 330 core
in vec2 in_pos;
uniform mat4 m_inv_vp;
out vec3 v_dir;
void main() {
    gl_Position = vec4(in_pos, 0.9999, 1.0);
    vec4 world  = m_inv_vp * vec4(in_pos, 1.0, 1.0);
    v_dir = normalize(world.xyz / world.w);
}
