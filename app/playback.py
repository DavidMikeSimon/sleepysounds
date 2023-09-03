import time
from dataclasses import dataclass
from queue import Queue, Empty
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
        super().__init__(daemon=True)

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

    def _process_commands(self):
        commands = []
        commands.append(self._command_queue.get())
        tasks_fetched = 1

        # Grab all the commands we can, because later commands may remove the
        # need to run earlier commands.
        while True:
            try:
                extra_command = self._command_queue.get_nowait()
                tasks_fetched += 1
            except Empty:
                break

            # If it's a quit command, that overrides everything, just run it
            if isinstance(extra_command, QuitCommand):
                commands = [extra_command]
                break

            # If the previous command is a start command, a stop command cancels
            # it out.
            if (
                len(commands) >= 1 and
                isinstance(commands[-1], StartCommand) and
                isinstance(extra_command, StopCommand)
            ):
                commands.pop()
            # If the previous command is a start command, another start command
            # replaces it.
            elif (
                len(commands) >= 1 and
                isinstance(commands[-1], StartCommand) and
                isinstance(extra_command, StartCommand)
            ):
                commands.pop()
                commands.append(extra_command)
            # If the previous command is a stop command, another stop command
            # can be ignored as redundant.
            elif (
                len(commands) >= 1 and
                isinstance(commands[-1], StopCommand) and
                isinstance(extra_command, StopCommand)
            ):
                pass
            # If the previous command is a stop command, and it had another
            # start command before it, a new start command can replace
            # them both.
            elif (
                len(commands) >= 2 and
                isinstance(commands[-1], StopCommand) and
                isinstance(commands[-2], StartCommand) and
                isinstance(extra_command, StartCommand)
            ):
                commands.pop()
                commands.pop()
                commands.append(extra_command)
            # Normal case
            else:
                commands.append(extra_command)

        print(f"Fetched tasks: {tasks_fetched}")

        try:
            for command in commands:
                match command:
                    case StartCommand(path):
                        self._fade_out()
                        self._fade_in(path)
                    case StopCommand():
                        self._fade_out()
                    case QuitCommand():
                        print("Playback: Quitting")
                        self._fade_out()
                        return
        finally:
            for _ in range(tasks_fetched):
                self._command_queue.task_done()

    def run(self):
        while True:
            self._process_commands()
