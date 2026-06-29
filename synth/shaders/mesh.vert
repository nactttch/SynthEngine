#version 330 core

in vec3 in_position;
in vec3 in_normal;
in vec2 in_texcoord;

uniform mat4 m_model;
uniform mat4 m_view;
uniform mat4 m_proj;

out vec3 v_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world = m_model * vec4(in_position, 1.0);
    v_pos    = world.xyz;
    v_normal = mat3(transpose(inverse(m_model))) * in_normal;
    v_uv     = in_texcoord;
    gl_Position = m_proj * m_view * world;
}
