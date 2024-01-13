import numpy as np
import imgui

import jgl

def testShader():
    tempVAO = jgl.VAO()
    tempVAO.enable()
    e = jgl.Shader("basic")
    tempVAO.disable()
    #del tempVAO
    return e

def vaoPair():
    screen_quad = np.array([
        -1.0, 1.0,
        -1.0, -1.0,
        1.0, -1.0,
        -1.0, 1.0,
        1.0, -1.0,
        1.0, 1.0
    ], dtype=np.float32)
    screenvao = jgl.VAO(jgl.Buffer(), screen_quad)
    icon_quad = np.array([
        0.0, 1.0,
        0.0, 0.0,
        1.0, 0.0,
        0.0, 1.0,
        1.0, 0.0,
        1.0, 1.0
    ], dtype=np.float32)
    iconvao = jgl.VAO(jgl.Buffer(), icon_quad)
    return screenvao, iconvao

def kbd(window, key, scancode, action, mods):
    if not imgui.get_io().want_capture_keyboard:
        print(f"{window=} {key=} {scancode=} {action=} {mods=}")

def mou(window, button, action, mods):
    if not imgui.get_io().want_capture_mouse:
        print(f"{window=} {button=} {action=} {mods=}")

def act(windowmanager, root):
    root.update({"frame": (root["frame"] + 1)})
    windowmanager[0].overlay[0].enable()
    imgui.new_frame()
    windowmanager[0].overlay[0].process_inputs()
    imgui.show_demo_window()
    pass

def draw(windowmanager, root):
        for window in windowmanager:
            window.enable()
            # render stuff
            jgl.clear()
            jgl.draw(root["screen"], root["shader"], resolution=root["size"])
            # render stuff end
            for overlay in window.overlay:
                overlay.handle()
            window.swap()
        windowmanager.poll()

def main():
    try:
        if jgl.init_gl(resizable = False) == None:
            raise(Exception("Could not initialize OpenGL."))
        jglwm = jgl.WindowManager()
        jglwm.create_window()
        jglwm[0].enable()
        basic = testShader()
        #fb = jgl.FrameBuffer()
        screenvao, iconvao = vaoPair()
        jglwm[0].register_overlay(jgl.DearImgui(jglwm[0],
                                                key_callback=kbd,
                                                mouse_callback=mou))
        should_close = jglwm.should_close()
        scene = {"frame": 0, "screen": screenvao, "shader": basic, "size": (800,600)}
        while not should_close:
            act(jglwm, scene)
            draw(jglwm, scene)
            if jglwm.should_close():
                should_close = True
                # raise(Exception("Window closed."))
    except:
        raise
    

if __name__ == "__main__":
    main()

