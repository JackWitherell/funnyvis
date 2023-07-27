import pyaudio
import threading
import pathlib
import subprocess
import wave
import os
from queue import Queue
import librosa

if not os.path.isdir("audio"):
    os.mkdir('audio')
    
def createAudioPlayer(filename):
    queue = Queue()
    def createReal(queuee, filename):
        queuee.put(AudioPlayback(filename))
    threading.Thread(target = createReal, args = (queue, filename)).start()
    return queue

class AudioPlayback:
    def __init__(self, filename):
        filepath = pathlib.Path(filename)
        self.filename = filepath.stem+".wav"
        # convert and store file into library if it's not loaded already
        if not os.path.isfile("audio/"+self.filename):
            if(subprocess.run(["ffmpeg", "-i", filename, "audio/"+self.filename]).returncode==0):
                print("successfully loaded audio file!")
        self.librosawaveform, self.librosasamplerate = librosa.load("audio/"+self.filename)
        self.playcontrol = False
        self.threadcmds = Queue()
        self.returns = Queue()
        def playback(threadcmds, threadreturn):
            inaudioplaying = False
            kill = False
            with wave.open("audio/"+self.filename, 'rb') as wavefile:
                def callback(indata, framecount, timeinfo, status):
                    data = wavefile.readframes(framecount)
                    return (data, pyaudio.paContinue)
                p = pyaudio.PyAudio()
                stream = p.open(format = pyaudio.paInt16,
                                channels=wavefile.getnchannels(),
                                rate=wavefile.getframerate(),
                                output=True,
                                stream_callback=callback)
                
                stream.stop_stream()
                while not kill:
                    try:
                        cmd = threadcmds.get(timeout=30)
                        if cmd:
                            if cmd == "playpause":
                                if inaudioplaying == False:
                                    inaudioplaying = True
                                    stream.start_stream()
                                elif inaudioplaying == True:
                                    inaudioplaying = False
                                    stream.stop_stream()
                            elif cmd == "time":
                                threadreturn.put(stream.get_time())
                            elif cmd == "kill":
                                kill = True
                    except:
                        pass
                stream.close()
                p.terminate()
        self.thread = threading.Thread(target = playback, args = (self.threadcmds, self.returns))
        self.thread.start()
    def playpause(self):
        self.playcontrol = not self.playcontrol
        self.threadcmds.put("playpause")
    def gettime(self):
        self.threadcmds.put("time")
    def fetchtime(self):
        return self.returns.get()
    def kill(self):
        self.threadcmds.put("kill")