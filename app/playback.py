import time
from dataclasses import dataclass
from queue import Queue
from threading import Thread

from just_playback import Playback

@dataclass(frozen=True)
class StartCommand:
    path: str 

@dataclass(frozen=True)
class StopCommand:
    pass

@dataclass(frozen=True)
class QuitCommand:
    pass

PlaybackCommand = StartCommand | StopCommand

FADE_OUT_TIME = 1.0
FADE_IN_TIME = 1.0
FADE_STEPS = 50
POST_FADE_OUT_DELAY_TIME = 0.2

class PlaybackThread(Thread):
    _command_queue: Queue[PlaybackCommand]
    _playback: Playback
    _is_playing: bool

    def __init__(self, command_queue: Queue[PlaybackCommand]):
        self._command_queue = command_queue
        self._playback = Playback()
        self._playback.loop_at_end(True)
        self._is_playing = False
        super().__init__()

    def _fade_in(self, path: str):
        print(f"Playback: Starting {path}")
        self._playback.set_volume(0.0)
        self._playback.load_file(path)
        self._playback.play()
        for i in range(FADE_STEPS):
            self._playback.set_volume(float(i)/FADE_STEPS)
            time.sleep(FADE_IN_TIME / FADE_STEPS)
        self._is_playing = True
        print(f"Playback: Started {path}")

    def _fade_out(self):
        if not self._is_playing:
            return
        print("Playback: Stopping")
        for i in range(FADE_STEPS):
            self._playback.set_volume(1.0 - float(i)/FADE_STEPS)
            time.sleep(FADE_OUT_TIME / FADE_STEPS)
        time.sleep(POST_FADE_OUT_DELAY_TIME)
        self._playback.stop()
        self._is_playing = False
        print("Playback: Stopped")

    def run(self):
        while True:
            command = self._command_queue.get()
            match command:
                case StartCommand(path):
                    self._fade_out()
                    self._fade_in(path)
                case StopCommand():
                    self._fade_out()
                case QuitCommand():
                    print("Playback: Quitting")
                    self._fade_out()
                    self._command_queue.task_done()
                    return
            self._command_queue.task_done()
