import os
import signal
import subprocess
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from termcolor import colored

BOT_COMMAND = ["python", "main.py"]  # Comando per avviare il bot
process = subprocess.Popen(BOT_COMMAND)  # Avvia il bot inizialmente
debounce_time = 0.2  # Tempo di debounce in secondi
debounce_timer = None

class RestartOnChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global process, debounce_timer

        if event.is_directory or not event.src_path.endswith(".py"):
            return

        if debounce_timer is not None:
            debounce_timer.cancel()  # Cancella il debounce precedente

        debounce_timer = threading.Timer(debounce_time, self.restart_bot)
        debounce_timer.start()

    def restart_bot(self):
        global process
        print(colored(f"File Python modificato. Riavvio del bot...", "yellow"))
        process.terminate()
        process.wait()
        process = subprocess.Popen(BOT_COMMAND)

if __name__ == "__main__":
    path = "."  # Cartella del progetto
    event_handler = RestartOnChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    print(colored("Monitoraggio delle modifiche ai file .py avviato...", "green"))
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        process.terminate()

    observer.join()
