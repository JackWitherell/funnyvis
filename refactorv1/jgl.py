import ctypes
import json
import os

import glfw
import imgui
import imgui.integrations.glfw as iogl
import OpenGL.GL as gl
import OpenGL.GL.shaders as gl_shaders

def init_gl(version="4.1", resizable=True):
    if not glfw.init():
        return None
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.RESIZABLE, gl.GL_TRUE if resizable else gl.GL_FALSE)
    return "👍"

def clear():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

def draw(vao, shader, resolution=(800,600)):
    shader.enable()
    for uniform in shader.meta["uniforms"].keys():
        uniform_type = shader.meta["uniforms"][uniform]["type"]
        if uniform_type == "vec2":
            gl.glUniform2f(shader.meta["uniforms"][uniform]["location"], *resolution)
        elif uniform_type == "float":
            gl.glUniform1f(uniform, shader.meta["uniforms"][uniform + "_value"])
        elif uniform_type == "int":
            gl.glUniform1i(uniform, shader.meta["uniforms"][uniform + "_value"])
        elif uniform_type == "mat4":
            gl.glUniformMatrix4fv(shader.meta["uniforms"][uniform], 1, gl.GL_FALSE, shader.meta["uniforms"][uniform + "_value"])
    #glUniform2f(shader.meta["uniforms"], save_data["window_width"], save_data["window_height"])
    vao.bind()
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
    vao.unbind()

class Window:
    def __init__(self, size, title, parent):
        self.index = glfw.create_window(
            *size, title,
            None,
            parent
        )
        self.overlay = []
    
    def enable(self):
        glfw.make_context_current(self.index)
    
    def set_position(self, loc):
        glfw.set_window_pos(self.index, *loc)
    
    def should_close(self):
        return glfw.window_should_close(self.index)
    
    def register_overlay(self, overlay):
        self.overlay.append(overlay)
    
    def swap(self):
        glfw.swap_buffers(self.index)

class WindowManager:
    def __init__(self):
        self.window_holder = []
    
    def create_window(self,
                      size=(800, 600),
                      loc=(20, 80), title="OpenGL Window"):
        root_canvas = None if not self.window_holder else self.window_holder[0]
        current_window = Window(size, title, root_canvas)
        if not current_window.index:
            glfw.terminate()
            raise(Exception("Could not create window"))
        self.window_holder.append(current_window)
        current_window.set_position(loc)
    
    def __getitem__(self, index):
        return self.window_holder[index]
    
    def __len__(self):
        return len(self.window_holder)
    
    def should_close(self):
        for window in self.window_holder:
            if window.should_close():
                return True
        return False
    
    def poll(self):
        glfw.poll_events()

class Buffer:
    def __init__(self):
        self.index = gl.glGenBuffers(1)
    
    def bind(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.index)
    
    def unbind(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    
    def __del__(self):
        gl.glDeleteBuffers(1, [self.index])

class VAO:
    def __init__(self, buffer=None, data=None):
        self.index = gl.glGenVertexArrays(1)
        self.bind()
        if buffer != None:
            self.buffer = buffer
            self.buffer.bind()
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, ctypes.c_void_p(0))
            gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
            gl.glEnableVertexAttribArray(0)
            self.buffer.unbind()
        else:
            gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        self.disable()
    
    def enable(self):
        gl.glEnableVertexAttribArray(self.index)
        self.enabled = True
    
    def disable(self):
        gl.glDisableVertexAttribArray(self.index)
        self.enabled = False
    
    def bind(self):
        gl.glBindVertexArray(self.index)
    
    def unbind(self):
        gl.glBindVertexArray(0)
    
    def __del__(self):
        gl.glDeleteVertexArrays(1, [self.index])
        if hasattr(self, 'buffer'):
            del self.buffer

class Shader:
    def __init__(self, identity):
        validate = {
            './shaders':
                "Could not find shaders directory",
            f'./shaders/{identity}':
                f"Could not find shader {identity}.",
            f'./shaders/{identity}/meta.json':
                f"Could not find metadata for shader \"{identity}\".",
            f'./shaders/{identity}/fragment.glsl':
                f"Could not find fragment shader for shader {identity}.",
            f'./shaders/{identity}/vertex.glsl':
                f"Could not find vertex shader for shader {identity}."
        }
        for path in validate.keys():
            if not os.path.exists(path):
                raise(Exception(validate[path]))

        self.meta = json.load(open(f'./shaders/{identity}/meta.json'))
        vertex_shader_source = open(f'./shaders/{identity}/vertex.glsl').read()
        fragment_shader_source = open(f'./shaders/{identity}/fragment.glsl').read()
        vert = gl_shaders.compileShader(vertex_shader_source, gl.GL_VERTEX_SHADER)
        frag = gl_shaders.compileShader(fragment_shader_source, gl.GL_FRAGMENT_SHADER)
        self.prog = gl_shaders.compileProgram(vert, frag)
        for uniform in self.meta["uniforms"].keys():
            self.meta["uniforms"][uniform].update({"location": gl.glGetUniformLocation(self.prog, uniform)})
    
    def enable(self):
        gl.glUseProgram(self.prog)
    
    def __del__(self):
        gl.glDeleteProgram(self.prog)

class Texture:
    def __init__(self):
        self.index = gl.glGenTextures(1)
        
    def enable(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.index)

    def disable(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def filter_on(self):
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    
    def __del__(self):
        gl.glDeleteTextures(1, [self.index])

class DepthBuffer:
    def __init__(self, size=(800,600)):
        self.index = gl.glGenRenderbuffers(1)
        self.enable()
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, *size)
        self.disable()
    
    def enable(self):
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.index)
    
    def disable(self):
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
    
    def __del__(self):
        gl.glDeleteRenderbuffers(1, [self.index])

class FrameBuffer:
    def __init__(self, size=(800,600)):
        self.index = gl.glGenFramebuffers(1)
        self.enable()
        self.depth_buffer = DepthBuffer(size)
        self.depth_buffer.enable()
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, 
                                     gl.GL_RENDERBUFFER, self.depth_buffer.index)
        self.texture = Texture()
        self.texture.enable()
        self.texture.filter_on()
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                  gl.GL_TEXTURE_2D, self.texture.index, 0)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, *size, 0, gl.GL_RGB,
                        gl.GL_UNSIGNED_BYTE, None)
        clear()
        if(gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != 36053):
            glfw.terminate()
            raise(Exception("Could not create framebuffer."))
        self.texture.disable()
        self.disable()
        self.depth_buffer.disable()

    def enable(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.index)
    
    def disable(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    
    def __del__(self):
        gl.glDeleteFramebuffers(1, [self.index])
        del self.depth_buffer
        del self.texture

class DearImgui:
    def __init__(self, context, size=(800,600), key_callback=None, mouse_callback=None):
        context.enable()
        self.index = imgui.create_context()
        self.size = size
        imgui.get_io().display_size = size[0], size[1]
        imgui.get_io().fonts.get_tex_data_as_rgba32()
        self.renderer = iogl.GlfwRenderer(context.index)
        if key_callback == None or mouse_callback == None:
            raise(Exception("DearImgui requires key and mouse callbacks."))
        glfw.set_key_callback(context.index, key_callback)
        glfw.set_mouse_button_callback(context.index, mouse_callback)

    def process_inputs(self):
        self.renderer.process_inputs()
    
    def enable(self):
        imgui.set_current_context(self.index)
    
    def handle(self):
        imgui.render()
        draw_data = imgui.get_draw_data()
        self.renderer.render(draw_data)
        imgui.end_frame()