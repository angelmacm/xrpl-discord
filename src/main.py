# watch_bot.py
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import sleep

class Watcher:
    DIRECTORY_TO_WATCH = "."

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.event_type in ('modified', 'created', 'deleted', 'moved'):
            print(f"Change detected: {event.src_path} - {event.event_type}")
            subprocess.call(["pkill", "-f", "bot.py"])
            subprocess.Popen(["python", "discordBot.py"])

if __name__ == '__main__':
    w = Watcher()
    w.run()
