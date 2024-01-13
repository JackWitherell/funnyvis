#version 410 core
uniform vec2 resolution;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 color = vec3(uv, 0.0);
    if (gl_FragCoord.x == gl_FragCoord.y){
        color = vec3(0.0, 1.0, 0.9843);
    }
    frag_color = vec4(color, 1.0);
}
