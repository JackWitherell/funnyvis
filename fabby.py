import glfw
import imgui
import imgui.integrations.glfw as iogl
from OpenGL.GL import *
import numpy as np
from gltfloader import GLTFScene
from camwhore import *
from iconlibrary import icon_library as ic
from save_manager import save_data, save
import time
import librosa
from audio import createAudioPlayer
from queue import Queue


audiofilename = librosa.example('nutcracker')
#load your own audio file
#audiofilename = "C:\\Users\\Jack Witherell\\Desktop\\Rory Benjamin Prophet One Shots\\RB Pluck - Recked - C.wav"
ap = createAudioPlayer(audiofilename)

move = 0.0
switches = {
    "paused": True,
    "kbd_debug": False,
    "imgui_demo": False,
    "key_operations": False,
    "program_mode": 0, # 0 - e: editor, 1 - s: sequencer, 2 - p: playback
    "current_scene": "3d",
    "pprosA": "none",
    "pprosB": "none"
    }
key_track = {
        32: {"release":[0]}, #space
        65: {"release":[0], "press":[0]}, #a through
        66: {"release":[0], "press":[0]},
        67: {"release":[0], "press":[0]},
        68: {"release":[0], "press":[0]},
        69: {"release":[0], "press":[0]},
        70: {"release":[0], "press":[0]},
        71: {"release":[0], "press":[0]},
        72: {"release":[0], "press":[0]},
        73: {"release":[0], "press":[0]},
        74: {"release":[0], "press":[0]},
        75: {"release":[0], "press":[0]},
        76: {"release":[0], "press":[0]},
        77: {"release":[0], "press":[0]},
        78: {"release":[0], "press":[0]},
        79: {"release":[0], "press":[0]},
        80: {"release":[0], "press":[0]},
        81: {"release":[0], "press":[0]},
        82: {"release":[0], "press":[0]},
        83: {"release":[0], "press":[0, 2]}, #s
        84: {"release":[0], "press":[0]},
        85: {"release":[0], "press":[0]},
        86: {"release":[0], "press":[0]},
        87: {"release":[0], "press":[0]},
        88: {"release":[0], "press":[0]},
        89: {"release":[0], "press":[0]},
        90: {"release":[0], "press":[0]}, #z
        294: {"release":[0]}, #f5
        295: {"release":[0]}, #f6
        296: {"release":[0]}, #f7
        258: {"release":[0]}, #tab
    }
key_active = {}
button_actions = {"press":{},"release":{}}
def handle_keys():
    global button_actions
    global switches
    global ap
    while(any(button_actions["press"])):
        key, event = button_actions["press"].popitem()
        if key == 83 and event["mods"] == 2: # ctrl+s:
            save(save_data)
        elif key>=65 and key<=90 and event["mods"] == 0: # any letter
            key_active.update({key: event["time"]})
    while(any(button_actions["release"])):
        key, event = button_actions["release"].popitem()
        if key == 32 and event["mods"] == 0 and event["delay"]<(save_data["key_repeat"]/1000): # spacebar:
            if(isinstance(ap, Queue)):
                ap = ap.get()
            switches["paused"] = not switches["paused"]
            ap.playpause()
        elif key>=65 and key<=90 and event["mods"] == 0: # any letter
            time_active = key_active[key]
            key_active.pop(key)
            if event["delay"]>(save_data["key_repeat"]/1000):
                # confirm selection and continue
                pass
            else:
                if key==81: # q
                    switches["current_scene"] = "3d"
                elif key==65: # a
                    #modes = ["3d", "2d", "live"]
                    switches["current_scene"] = "2d"
                elif key==90: # z
                    switches["current_scene"] = "live"
                elif key==72: # h
                    effects = ["none", "dim", "bright", "grid", "invert", "bigwave"]
                    switches["pprosA"] = effects[(effects.index(switches["pprosA"])+1)%len(effects)]
                elif key==74: # j
                    effects = ["none", "dim", "bright", "grid", "invert", "bigwave"]
                    switches["pprosB"] = effects[(effects.index(switches["pprosB"])+1)%len(effects)]
        elif key == 258 and event["mods"] == 0 and event["delay"]<(save_data["key_repeat"]/1000): # tab:
            switches["program_mode"] = 0 if switches["program_mode"]==2 else switches["program_mode"] + 1
        elif key == 294 and event["mods"] == 0 and event["delay"]<(save_data["key_repeat"]/1000): # f5:
            switches["kbd_debug"] = not switches["kbd_debug"]
        elif key == 295 and event["mods"] == 0 and event["delay"]<(save_data["key_repeat"]/1000): # f6:
            switches["imgui_demo"] = not switches["imgui_demo"]
        elif key == 296 and event["mods"] == 0 and event["delay"]<(save_data["key_repeat"]/1000): # f6:
            switches["key_operations"] = not switches["key_operations"]

input_log = []
button_press = {}
def key_callback(window, key, scancode, action, mods):
    if not imgui.get_io().want_capture_keyboard:
        global button_press
        global key_track
        input_log.append(f"keypress: {key=},{scancode=},{action=},{mods=}")
        if(len(input_log)>18):
            input_log.pop(0)
        # evaluate keypresses
        if action == glfw.PRESS:
            if key in key_track.keys():
                if "press" in key_track[key].keys() and mods in key_track[key]["press"]:
                    button_actions["press"].update({key:{"mods":mods,"time":time.time()}})
                if "release" in key_track[key].keys() and mods in key_track[key]["release"]:
                    button_press.update({key:{"mods":mods,"time":time.time()}})
        if action == glfw.RELEASE:
            if key in button_press:
                delay = time.time()-button_press[key]["time"]
                temp_action = button_press.pop(key)
                temp_action.update({"delay": delay})
                button_actions["release"].update({key: temp_action})

def mouse_callback(window, button, action, mods):
    if not imgui.get_io().want_capture_mouse:
        input_log.append(f"mouse: {button=},{action=},{mods=}")
        if(len(input_log)>18):
            input_log.pop(0)

def main():
    global ap
    # Initialize GLFW
    if not glfw.init():
        return
        
    # Set OpenGL version and profile
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.RESIZABLE, GL_FALSE)
    
    # Create a window and make it current
    canvas = glfw.create_window(save_data["window_width"], save_data["window_height"], "Example", None, None)
    if not canvas:
        print("Failed to build a window!")
        glfw.terminate()
        return
    glfw.set_window_pos(canvas, 20, 50)
    
    control = glfw.create_window(save_data["second_window_width"], save_data["second_window_height"], "Control", None, canvas)
    if not control:
        print("Failed to build a second window!")
        glfw.terminate()
        return
    glfw.set_window_pos(control, 20, 100+save_data["window_height"])

    glfw.make_context_current(canvas)

    # prep shaders - macos insists on validating the shaders so a VAO needs to be bound
    proofvao = glGenVertexArrays(1)
    glBindVertexArray(proofvao)
    glVertexAttribPointer(
        0, 3, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)
    from shaderlibrary import shader_collection as shadcol
    glDisableVertexAttribArray(0)

    # prep a single object
    scene = GLTFScene("primitives.gltf")
    focusNode = scene.getNode(0, 8)
    meshList = GLTFScene.meshesFromNode(focusNode)
    meshDefinition = meshList[0]["mesh"]
    meshPart = meshDefinition["primitives"][0]
    cube = scene.meshtoVAO(meshPart, shadcol["obj"].prog)
    indices = scene.getIndices(meshPart)

    # prep an offscreen buffer
    #ogfb = GLint(0)
    #glGetIntegerv(GL_FRAMEBUFFER_BINDING, ogfb)

    framebuffer = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    
    depthbuffer = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, depthbuffer)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, save_data["window_width"], save_data["window_height"])
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthbuffer)
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, save_data["window_width"], save_data["window_height"], 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != 36053):
        print("Failed to build an offscreen buffer!")
        glfw.terminate()
    glBindTexture(GL_TEXTURE_2D, 0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindRenderbuffer(GL_RENDERBUFFER, 0)
    
    
    # and a second
    framebufferb = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, framebufferb)
    
    depthbufferb = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, depthbufferb)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, save_data["window_width"], save_data["window_height"])
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthbufferb)
    textureb = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textureb)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, textureb, 0)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, save_data["window_width"], save_data["window_height"], 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != 36053):
        print("Failed to build an offscreen buffer!")
        glfw.terminate()
    glBindTexture(GL_TEXTURE_2D, 0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindRenderbuffer(GL_RENDERBUFFER, 0)
    

    # prep quad background
    screen_quad_data = np.array([
        -1.0, 1.0,   0.0, 1.0,
        -1.0, -1.0,  0.0, 0.0,
        1.0, -1.0,   1.0, 0.0,

        -1.0, 1.0,   0.0, 1.0,
        1.0, -1.0,   1.0, 0.0,
        1.0, 1.0,    1.0, 1.0
    ], dtype=np.float32)

    screenquad = glGenVertexArrays(1)
    glBindVertexArray(screenquad)
    quad_vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, quad_vbo)
    floatsize = sizeof(ctypes.c_float)*4
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, floatsize, ctypes.c_void_p(floatsize*0))
    glBufferData(GL_ARRAY_BUFFER, screen_quad_data, GL_STATIC_DRAW)

    # cleanup
    glEnableVertexAttribArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    
    # also to other buffer
    glfw.make_context_current(control)
    screenquad2 = glGenVertexArrays(1)
    glBindVertexArray(screenquad2)
    quad_vbo2 = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, quad_vbo2)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, floatsize, ctypes.c_void_p(floatsize*0))
    glBufferData(GL_ARRAY_BUFFER, screen_quad_data, GL_STATIC_DRAW)
    
    # cleanup
    glEnableVertexAttribArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    # creating an icon renderer
    icon_quad_data = np.array([
        0.0, 1.0,
        0.0, 0.0,
        1.0, 0.0,
        0.0, 1.0,
        1.0, 0.0,
        1.0, 1.0
    ], dtype=np.float32)

    glfw.make_context_current(control)
    spritequad = glGenVertexArrays(1)
    glBindVertexArray(spritequad)
    quad_vbo2 = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, quad_vbo2)
    floatsize = sizeof(ctypes.c_float)*2
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, floatsize, ctypes.c_void_p(floatsize*0))
    glBufferData(GL_ARRAY_BUFFER, icon_quad_data, GL_STATIC_DRAW)
    
    # cleanup
    glEnableVertexAttribArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    
    glfw.make_context_current(canvas)
    mainimguicontext = imgui.create_context()
    imgui.get_io().display_size = save_data["window_width"], save_data["window_height"]
    imgui.get_io().fonts.get_tex_data_as_rgba32()
    imrenderer = iogl.GlfwRenderer(canvas)
    glfw.set_key_callback(canvas, key_callback)
    glfw.set_mouse_button_callback(canvas, mouse_callback)
    glfw.make_context_current(control)
    secondimguicontext = imgui.create_context()
    imgui.set_current_context(secondimguicontext)
    imgui.get_io().display_size = save_data["second_window_width"], save_data["second_window_height"]
    imgui.get_io().fonts.get_tex_data_as_rgba32()
    imrenderer2 = iogl.GlfwRenderer(control)
    glfw.set_key_callback(control, key_callback)
    glfw.set_mouse_button_callback(control, mouse_callback)
    
    fps = 0
    framecount = 0
    global move
    sec = int(time.time())
    recent = time.time()

    # Main loop
    while (not glfw.window_should_close(canvas)) and (not glfw.window_should_close(control)):
        # Time management
        # fps, move, c_time, sec, recent, delta
        # fps - newest framerate metric
        # move - total accumulated delta time since origin time in seconds
        # c_time - current time in sec
        # sec - current time in integer sec
        # recent - last frame's time
        # delta - delta time since last frame in seconds
        c_time = time.time()
        if (int(c_time)!= sec):
            if not (isinstance(ap, Queue)):
                ap.gettime()
            sec = int(c_time)
            fps = framecount
            if not (isinstance(ap, Queue)):
                print(f"{fps} {ap.fetchtime()}")
            else:
                print(fps)
            framecount = 0
            if np.floor(move)%save_data["save_interval"]==1:
                save(save_data)
        
        framecount += 1
        delta = c_time-recent
        if not switches["paused"]:
            move += delta
        
        imgui.set_current_context(mainimguicontext)
        imrenderer.process_inputs()

        glfw.make_context_current(canvas)
        
        imgui.get_io().display_size = save_data["window_width"], save_data["window_height"]

        imgui.new_frame()
        if switches["imgui_demo"]:
            imgui.show_demo_window()
        if switches["kbd_debug"]:
            imgui.set_next_window_size(340, 380)
            imgui.begin("Keyboard Log", closable=False)
            imgui.text(str(glfw.get_cursor_pos(canvas)))
        
            keyboard = imgui.get_io().want_capture_keyboard
            mouse = imgui.get_io().want_capture_mouse
            imgui.text(f"Want to capture- {keyboard=} {mouse=}")
            for input in input_log:
                imgui.text(input)
            imgui.end()
        if switches["key_operations"]:
            imgui.set_next_window_size(340, 380)
            imgui.begin("Keys Active", closable=False)
            for k,v in key_active.items():
                imgui.text(f"{k},{v}")
            for k,v in button_actions.items():
                imgui.text(f"{k},{v}")
            imgui.end()
        
        handle_keys()
        #changed, value = imgui.slider_float("fucker", value, 0.0, 38.0)

        if(switches["current_scene"] == "3d"):
            prelim_2d(shadcol, framebuffer, screenquad, "bg")
            onto_obj(shadcol, framebuffer, cube, meshList, indices, meshPart, scene, 1.0)
            #onto_obj(shadcol, framebuffer, cube, meshList, indices, meshPart, scene, -1.0)
            #onto_obj(shadcol, framebuffer, cube, meshList, indices, meshPart, scene, -0.4)
            effect = switches["pprosA"]
            ppros(shadcol, framebufferb, texture, screenquad, effect)
            effect = switches["pprosB"]
            ppros(shadcol, framebuffer, textureb, screenquad, effect)
            #baspros(shadcol, framebufferb, texture, screenquad, "dim")
            #baspros(shadcol, framebuffer, textureb, screenquad, "bright")
            display(shadcol, texture, screenquad)
            pass
        elif(switches["current_scene"] == "2d"):
            prelim_2d(shadcol, framebuffer, screenquad, "bg")
            effect = switches["pprosA"]
            ppros(shadcol, framebufferb, texture, screenquad, effect)
            effect = switches["pprosB"]
            ppros(shadcol, framebuffer, textureb, screenquad, effect)
            #baspros(shadcol, framebufferb, texture, screenquad, "dim")
            #baspros(shadcol, framebuffer, textureb, screenquad, "bright")
            display(shadcol, texture, screenquad)
            pass
        else:
            prelim_2d(shadcol, framebuffer, screenquad, "waves")
            effect = switches["pprosA"]
            ppros(shadcol, framebufferb, texture, screenquad, effect)
            effect = switches["pprosB"]
            ppros(shadcol, framebuffer, textureb, screenquad, effect)
            #baspros(shadcol, framebufferb, texture, screenquad, "dim")
            #baspros(shadcol, framebuffer, textureb, screenquad, "bright")
            display(shadcol, texture, screenquad)
            pass

        # render imgui and finish
        if True:
            imgui.render()
            draw_data = imgui.get_draw_data()
            imrenderer.render(draw_data)
            imgui.end_frame()
            glfw.swap_buffers(canvas)
        
            glfw.make_context_current(control)

        # second window
        # setup render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        imgui.set_current_context(secondimguicontext)
        imrenderer2.process_inputs()
        imgui.new_frame()
        
        grey = (0.5, 0.5, 0.5, 1.0)
        x_width = save_data["second_window_width"]
        m_height = save_data["second_window_height"]-30

        icondraw(shadcol, spritequad, 0xFF80BEA0, 0xBCA0BE80, (x_width-((m_height+10)*3), 15), (m_height, m_height), (1.0, 0.2, 0.2, 1.0) if switches["program_mode"] == 0 else grey)
        icondraw(shadcol, spritequad, 0xFF809EA0, 0x9C82BC80, (x_width-((m_height+10)*2), 15), (m_height, m_height), (0.2, 0.8, 0.2, 1.0) if switches["program_mode"] == 1 else grey)
        icondraw(shadcol, spritequad, 0xFF80BCA2, 0xBCA0A080, (x_width-(m_height+10), 15), (m_height, m_height), (0.2, 0.2, 1.0, 1.0) if switches["program_mode"] == 2 else grey)

        kb = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
        margin = int((save_data["second_window_height"]/5)/4)
        t_height = int((save_data["second_window_height"]-(margin*4))/3)
        margin = int((save_data["second_window_height"]/5)/4)
        for r_y, row in enumerate(kb):
            for l_x, letter in enumerate(row):
                col = (1.0, 1.0, 1.0, 1.0) if switches["program_mode"] == 0 else grey
                if letter in ["q", "a", "z"]:
                    if letter == "q" and switches["current_scene"] == "3d":
                        col = (1.0, 0.0, 0.0, 1.0)
                    elif letter == "a" and switches["current_scene"] == "2d":
                        col = (0.0, 1.0, 0.0, 1.0)
                    elif letter == "z" and switches["current_scene"] == "live":
                        col = (0.0, 0.0, 1.0, 1.0)
                
                icondraw(shadcol, spritequad,
                         *ic[letter],
                         (((margin+t_height)*l_x)+margin, save_data["second_window_height"]-((margin+t_height)*(r_y+1))),
                         (t_height, t_height),
                         col)
        
        icondraw(shadcol, spritequad,
                 0xFFFFFFFF, 0xFFFFFFFF,
                 (((margin+t_height)*10)+margin, 0),
                 ((x_width-((m_height+10)*3))-(((margin+t_height)*10)+(margin*2)),
                  save_data["second_window_height"]),
                  (1.0, 0.9, 0.2, 1.0) if switches["program_mode"] == 0 else grey)
        
        imgui.set_next_window_size((x_width-((m_height+10)*3))-(((margin+t_height)*10)+(margin*2)), save_data["second_window_height"]+1)
        imgui.set_next_window_position(((margin+t_height)*10)+margin, 0)

        imgui.begin("Active View", closable=False, flags=imgui.WINDOW_NO_RESIZE+imgui.WINDOW_NO_TITLE_BAR)
        if imgui.begin_tab_bar("Tabs"):
            if imgui.begin_tab_item("keystuff").selected:
                for k,v in key_active.items():
                    imgui.text(f"{k},{v}")
                for k,v in button_actions.items():
                    imgui.text(f"{k},{v}")
                imgui.end_tab_item()
            if imgui.begin_tab_item("keystuffelse").selected:
                imgui.text(f"yes")
                imgui.end_tab_item()
            imgui.end_tab_bar()
        imgui.end()
        
        imgui.render()
        draw_data = imgui.get_draw_data()
        imrenderer2.render(draw_data)
        imgui.end_frame()
        glfw.swap_buffers(control)

        # finish
        glfw.poll_events()
        recent = c_time

    # Cleanup
    for shader in shadcol.values():
        shader.delete()
    glfw.terminate()
    if (isinstance(ap, Queue)):
        ap = ap.get()
        ap.kill()
    else:
        ap.kill()

# in use
def prelim_2d(shadcol, framebuffer, screenquad, shaderid):
    # setup shader
    glUseProgram(shadcol[shaderid].prog)
    if "itime" in shadcol[shaderid].uniforms:
        glUniform1f(shadcol[shaderid].uniforms["itime"], np.float32(move))
    glUniform2f(shadcol[shaderid].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
        
    # setup render
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glDisable(GL_DEPTH_TEST)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

def ppros(shadcol, framebuffer, source, screenquad, shaderid):
    # setup shader
    glUseProgram(shadcol[shaderid].prog)
    glUniform1f(shadcol[shaderid].uniforms["itime"], np.float32(move))
    glUniform2f(shadcol[shaderid].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, source)
    glUniform1i(shadcol[shaderid].uniforms["sampler"], 0)

    #setup render
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glDisable(GL_DEPTH_TEST)
    a = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if(a != 36053):
        print(a)
        glfw.terminate()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindVertexArray(0)
    glBindTexture(GL_TEXTURE_2D, 0)

def baspros(shadcol, framebuffer, source, screenquad, shaderid):
    # setup shader
    glUseProgram(shadcol[shaderid].prog)
    glUniform1f(shadcol[shaderid].uniforms["itime"], np.float32(move))
    glUniform2f(shadcol[shaderid].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, source)
    glUniform1i(shadcol[shaderid].uniforms["sampler"], 0)

    #setup render
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glDisable(GL_DEPTH_TEST)
    a = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if(a != 36053):
        print(a)
        glfw.terminate()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindVertexArray(0)
    glBindTexture(GL_TEXTURE_2D, 0)

def onto_obj(shadcol, framebuffer, cube, meshList, indices, meshPart, scene, offset):
    # setup shader
    glUseProgram(shadcol["obj"].prog)
    campos = np.array([np.sin(move)*4.0,3.0*offset,np.cos(move)*4.0])
    lookat = np.array([0.0,0.0,0.0])
    view_matrix = look_at(
        campos,
        lookat,
        np.array([0.0,1.0,0.0])
    )
    view_direction = viewdir(
        campos,
        lookat
    )
    proj_matrix = perspective_fov(40.0, 16.0/9.0, 0.1, 600.0)
    glUniformMatrix4fv(shadcol["obj"].uniforms["modelviewmat"], 1, GL_FALSE, view_matrix)
    glUniformMatrix4fv(shadcol["obj"].uniforms["projmat"], 1, GL_FALSE, proj_matrix)
    glUniform3f(shadcol["obj"].uniforms["viewdir"], *view_direction)
    
    # setup render
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glEnable(GL_DEPTH_TEST)
    glBindVertexArray(cube[0])
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indices)
    pullmat = None
    if (not ("matrix" in meshList[0])):
        pullmat = np.ndarray(shape=(4,4), buffer=np.array([1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0]))
    else:
        pullmat = meshList[0]["matrix"]
    glUniformMatrix4fv(shadcol["obj"].uniforms["objmat"], 1, GL_FALSE, pullmat)
        
    # draw
    mode = 4
    if ("mode" in meshPart):
        mode = meshPart["mode"]
    #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawElements(mode, scene.accessors[meshPart["indices"]]["count"], scene.accessors[meshPart["indices"]]["componentType"], None)
    #glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    # cleanup
    glBindVertexArray(0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

def display(shadcol, texture, screenquad):
    # setup shader
    glUseProgram(shadcol["display"].prog)
    glUniform2f(shadcol["display"].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture)
    glUniform1i(shadcol["display"].uniforms["sampler"], 0)

    # setup render
    glDisable(GL_DEPTH_TEST)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)
    glBindTexture(GL_TEXTURE_2D, 0)

# used for second window
def icondraw(shadcol, screenquad2, pA, pB, pxpos, widheight, color):
    # setup shader
    glUseProgram(shadcol["ico"].prog)
    glUniform2f(shadcol["ico"].uniforms["resolution"], save_data["second_window_width"], save_data["second_window_height"])
    glUniform1i(shadcol["ico"].uniforms["graphica"], pA)
    glUniform1i(shadcol["ico"].uniforms["graphicb"], pB)
    glUniform2i(shadcol["ico"].uniforms["spriteloc"], *pxpos)
    glUniform2i(shadcol["ico"].uniforms["spritesize"], *widheight)
    glUniform4f(shadcol["ico"].uniforms["in_color"], *color)

    # draw
    glBindVertexArray(screenquad2)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)

# should not be used
def bg2fb(shadcol, framebuffer, texture, screenquad):
    # setup shader
    glUseProgram(shadcol["bg"].prog)
    glUniform2f(shadcol["bg"].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
        
    # setup render
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glBindTexture(GL_TEXTURE_2D, texture)
    glDisable(GL_DEPTH_TEST)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindTexture(GL_TEXTURE_2D, 0)

def fb2bg(shadcol, texture, screenquad):
    # setup shader
    glUseProgram(shadcol["bgtexture"].prog)
    glUniform1f(shadcol["bgtexture"].uniforms["itime"], np.float32(move))
    glUniform2f(shadcol["bgtexture"].uniforms["resolution"], save_data["window_width"], save_data["window_height"])
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture)
    glUniform1i(shadcol["bgtexture"].uniforms["sampler"], 0)

    #setup render
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)
    glBindTexture(GL_TEXTURE_2D, 0)

def obj(shadcol, cube, meshList, indices, meshPart, scene):
    # setup shader
    glUseProgram(shadcol["obj"].prog)
    campos = np.array([np.sin(move)*4.0,3.0,np.cos(move)*4.0])
    lookat = np.array([0.0,0.0,0.0])
    view_matrix = look_at(
        campos,
        lookat,
        np.array([0.0,1.0,0.0])
    )
    view_direction = viewdir(
        campos,
        lookat
    )
    proj_matrix = perspective_fov(40.0, 16.0/9.0, 0.1, 600.0)
    glUniformMatrix4fv(shadcol["obj"].uniforms["modelviewmat"], 1, GL_FALSE, view_matrix)
    glUniformMatrix4fv(shadcol["obj"].uniforms["projmat"], 1, GL_FALSE, proj_matrix)
    glUniform3f(shadcol["obj"].uniforms["viewdir"], *view_direction)

    # setup render
    glEnable(GL_DEPTH_TEST)
    glBindVertexArray(cube[0])
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indices)
    pullmat = None
    if (not ("matrix" in meshList[0])):
        pullmat = np.ndarray(shape=(4,4), buffer=np.array([1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0]))
    else:
        pullmat = meshList[0]["matrix"]
    glUniformMatrix4fv(shadcol["obj"].uniforms["objmat"], 1, GL_FALSE, pullmat)
        
    # draw
    mode = 4
    if ("mode" in meshPart):
        mode = meshPart["mode"]
    #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawElements(mode, scene.accessors[meshPart["indices"]]["count"], scene.accessors[meshPart["indices"]]["componentType"], None)
    #glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # cleanup
    glBindVertexArray(0)

def overl(shadcol, screenquad, shaderid):
    # setup shader
    glUseProgram(shadcol[shaderid].prog)
    glUniform2f(shadcol[shaderid].uniforms["resolution"], save_data["window_width"], save_data["window_height"])

    # setup render
    glDisable(GL_DEPTH_TEST)

    # draw
    glBindVertexArray(screenquad)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # cleanup
    glBindVertexArray(0)

if __name__ == '__main__':
    try:
        main()
    except:
        if (isinstance(ap, Queue)):
            ap = ap.get()
            ap.kill()
        else:
            ap.kill()
        raise


#1. get pixel coordinates working for specifying object/window locations
#2. ask about uv mapping
#3. ask about texture loading and applying
#4. ask about texture generation