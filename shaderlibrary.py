from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram


shader_collection = {}

class Shader:
    def __init__(self, vertex, fragment, uniforms):
        self._vtx_source = vertex
        self._frag_source = fragment
        self._uniform_names = uniforms
        self.uniforms = {}

    def comp_shader(self):
        # Compile the vertex and fragment shaders
        vertex_shader = compileShader(self._vtx_source, GL_VERTEX_SHADER)
        fragment_shader = compileShader(self._frag_source, GL_FRAGMENT_SHADER)

        # Link the vertex and fragment shaders into a shader program
        self.prog = compileProgram(vertex_shader, fragment_shader)

        # Get the location of the resolution uniform in the shader program
        return self.prog
    
    def unpack_uniforms(self):
        for uniform in self._uniform_names:
            self.uniforms.update({uniform: glGetUniformLocation(self.prog, uniform)})

    def delete(self):
        glDeleteProgram(self.prog)

    @staticmethod
    def comp_shaders(shaders):
        for shader in shaders.values():
            shader.comp_shader()
            shader.unpack_uniforms()

# template
shader_collection.update({"template":Shader("""
#version 410 core
in vec3 position;
void main()
{
    gl_Position = vec4(position, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 color = vec3(uv, 0.0);
    frag_color = vec4(color, 1.0);
}
""",
["resolution"]
)})

shader_collection.update({"bg":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 color = vec3(uv, 0.0);
    if (gl_FragCoord.x == gl_FragCoord.y){
        color = vec3(0.0,0.0,0.0);
    }
    frag_color = vec4(color, 1.0);
}
""",
["resolution"]
)})

shader_collection.update({"ico":Shader("""
#version 410 core
in vec2 position;
uniform vec2 resolution;
uniform ivec2 spriteloc;
uniform ivec2 spritesize;
out vec2 in_uv;
void main()
{
    vec2 loc = (((vec2(spriteloc)+(position*vec2(spritesize)))/resolution)*2.0)-vec2(1.0);
    gl_Position = vec4(loc, 0.0, 1.0);
    in_uv = position;
}
""", """
#version 410 core
uniform int graphica;
uniform int graphicb;
uniform vec4 in_color;
in vec2 in_uv;
out vec4 frag_color;
void main()
{
    //vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec2 uv=vec2(1.0-in_uv.x,in_uv.y);
    vec3 color = vec3(uv, 0.0);
    
    ivec2 pxcoord = ivec2(uv*9.0);
    int samp = pxcoord.x+(pxcoord.y*8)-9;
    int valuea = graphica>>samp&1;
    int valueb = graphicb>>samp&1;
    color = vec3(float(mod((pxcoord.y-1),8)>3?valuea:valueb));
    frag_color = vec4(color*in_color.rgb, 1.0);
}
""",
["resolution", "graphica", "graphicb", "spriteloc", "spritesize", "in_color"]
)})

shader_collection.update({"bgtexture":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv+vec2(sin(itime+(uv.y*30.0))/10.0, 0.0))).xyz;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

# post processing effects
shader_collection.update({"none":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv)).xyz;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

shader_collection.update({"dim":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv)).xyz-0.3;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

shader_collection.update({"bright":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv)).xyz+0.3;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

shader_collection.update({"grid":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv)).xyz;
    if ((mod(float(gl_FragCoord.x)+0.5,32.0) < 0.8)||(mod(float(gl_FragCoord.y)+0.5,32.0) < 0.8)){
        samp = vec3(0.0,0.0,0.0);
    }

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

shader_collection.update({"invert":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec3(1.0)-vec4(texture(sampler, uv)).xyz;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})

shader_collection.update({"bigwave":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
uniform float itime;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv+vec2(sin(itime+uv.x)))).xyz;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler", "itime"]
)})



shader_collection.update({"waves":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform float itime;
out vec4 frag_color;
float wave(vec2 uv, float inv_size, float period, float inv_amplitude, float x_offset, float y_offset, float flip, float speed){
    float wv = ((uv.y-y_offset)*inv_size)-(sin(((x_offset+uv.x)/period)+(speed*itime))/inv_amplitude);
    if(abs(wv)>0.4){
        wv=0.0;
    }
    return flip*wv;
}
void main()
{
    // Normalized pixel coordinates (from 0 to 1)
    vec2 uv = gl_FragCoord.xy/resolution.xy;

    //background color
    vec3 col = vec3(0.0,0.0,0.3+((uv.x+uv.y)/3.0));
    //waves
    //(uv, inverted size, period, inverted amplitude, x, y offset, flip, speed)
	col+=clamp(wave(uv,4.0,1.0,3.0,0.0,0.4,1.0,-0.1),0.0,0.4);
    col+=clamp(wave(uv,4.0,0.4,1.0,0.0,0.5,1.0,0.1),0.0,0.4);
    
	col+=clamp(wave(uv,4.0,0.2,6.0,3.0,0.3,-1.0,0.13),0.0,0.4);
    col+=clamp(wave(uv,4.0,0.15,7.0,4.0,0.4,-1.0,-0.18),0.0,0.4);

    frag_color = vec4(col, 1.0);
}
""",
["resolution", "itime"]
)})

shader_collection.update({"obj":Shader("""
#version 410 core
in vec3 position;
in vec3 normal;
uniform mat4 modelviewmat;
uniform mat4 projmat;
uniform mat4 objmat;
out vec3 vnormal;

void main()
{
    gl_Position = (projmat*modelviewmat*objmat*vec4(position, 1.0));
    vnormal = (vec4(normal, 0.0)).xyz;
}
""", """
#version 410 core
uniform vec2 resolution;
uniform vec3 viewdir;
in vec3 vnormal;
out vec4 frag_color;
void main()
{
    vec3 color = vec3(0.5,0.5,0.5);
    //color=color+(dot(normalize(vec3(9.0, 2.0, 5.0)),vnormal)*0.4);
    //color=trunc(color*3.0)/3.0;
    //color=sign(vnormal);
    //color= normalize(viewdir.xzy);

    vec3 viewDirection = viewdir;

    vec3 lightDirection = normalize(vec3(9.0, 2.0, 5.0));

    float vDotN = dot(viewDirection,vnormal);
    float lDotN = dot(lightDirection,vnormal);

    float cosThetaI = lDotN;

    float thetaR = acos(vDotN);
    float thetaI = acos(cosThetaI);

    float cosPhiDiff = dot(
        normalize(viewDirection - vnormal * vDotN),
        normalize(lightDirection - vnormal * lDotN));

    float alpha = max(thetaI, thetaR);
    float beta = min(thetaI, thetaR);

    float roughness = 1.0;

    float sigma2 = roughness * roughness;

    float a = 1.0 - 0.5 * sigma2 / (sigma2 + 0.33);
    float b = 0.45 * sigma2 / (sigma2 + 0.09);

    float val = clamp(cosThetaI,0.0,1.0) * (a + (b * clamp(cosPhiDiff,0.0,1.0) * sin(alpha) * tan(beta)));

    color = vec3(val);
    
    if(viewdir.x>(vnormal.y+100.0)){color=vnormal;}
    frag_color = vec4(color, 1.0);
}
""",
["modelviewmat", "projmat", "objmat", "viewdir"]
)})

shader_collection.update({"overl":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 color = vec3(uv, 0.0);
    if (mod(gl_FragCoord.x,2.0)<0.8){
        discard;
    }
    frag_color = vec4(color, 1.0);
}
""",
["resolution"]
)})

shader_collection.update({"display":Shader("""
#version 410 core
in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
""", """
#version 410 core
uniform vec2 resolution;
uniform sampler2D sampler;
out vec4 frag_color;
void main()
{
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 samp = vec4(texture(sampler, uv)).xyz;

    frag_color = vec4(samp, 1.0);
}
""",
["resolution", "sampler"]
)})

Shader.comp_shaders(shader_collection)


# garbage

fragment_shader_source = """
#version 410 core
uniform vec2 resolution;
in vec3 vnormal;
void main()
{
    vec3 color = vec3(0.5,0.5,0.5);
    color=color+(dot(normalize(vec3(9.0, 2.0, 5.0)),vnormal)*0.4);
    color=trunc(color*3.0)/3.0;
    gl_FragColor = vec4(color, 1.0);
}
"""

