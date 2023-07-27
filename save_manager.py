import json
import os

#default configuration of save data
save_data = {
    "save_interval":90,
    "window_width":1280,
    "window_height":720,
    "second_window_width":800,
    "second_window_height":120,
    "key_repeat":180,
}

if(not os.path.isfile("save")):
    print("storage not found!")
else:
    with open('save', 'r') as save_file:
        loaded_data = json.load(save_file)
        save_data.update(loaded_data)

# loads save data, patching over the default configuration above
def save(save_this):
    with open('save', 'w') as save_file:
        json.dump(save_this, save_file, indent=2)
        print("Saved Data!")
