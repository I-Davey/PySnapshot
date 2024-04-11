import tkinter as tk
import threading
import time
import asyncio
from snapshot import SnapshotConnection
import queue  # Add this import

# Define your Tkinter popup class
class OffWhitePopup:
    def __init__(self, root, update_queue):
        self.root = root
        self.update_queue = update_queue 
        self.root.title("Off White Popup")
        self.root.geometry("300x200")
        self.bg_color = "#F5F5F5"  # Off-white color

        self.popup_label = tk.Label(root, text="No Color Set", bg=self.bg_color)
        self.popup_label.pack(fill=tk.BOTH, expand=True)


    def handle_clipboard(self, e):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.popup_label.cget("text"))

    def set_background_color(self, color):
        self.popup_label.config(text=color[1])
        #make popuo selectable so i can copy the color
        self.popup_label.bind("<Button-1>",  self.handle_clipboard)

        

        self.popup_label.config(bg=color[0])

    def check_update_queue(self):
        try:
            while True:  # Process all available items in the queue
                color = self.update_queue.get_nowait()
                self.set_background_color(color)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_update_queue) 








def start_asyncio_loop(asyncio_loop):
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_forever()

async def main_bluetooth_code(update_queue):
    snapshot = await SnapshotConnection.create()
    if snapshot:
        print("Battery level:", await snapshot.read_battery_level())
        await snapshot.subscribe_to_notifications()
        # Example: Send a color update to the queue
        # In reality, this should be replaced with actual data handling logic
        #r,g,b with o.2s delay
        update_queue.put(["#FF0000", "red"])
        await asyncio.sleep(0.2)
        update_queue.put(["#00FF00", "green"])
        await asyncio.sleep(0.2)
        update_queue.put(["#0000FF", "blue"])
        await asyncio.sleep(0.2)
        while True:
            await asyncio.sleep(2)
            if len(snapshot.parsed_data) > 0:
                data = snapshot.parsed_data[-1]
                update_queue.put(data)
                          

def main():
    print("starting")
    update_queue = queue.Queue()
    root = tk.Tk()
    off_white_popup = OffWhitePopup(root, update_queue)
    off_white_popup.check_update_queue()  # Start checking the queue

    # Setup and start the asyncio event loop in a separate thread
    asyncio_loop = asyncio.new_event_loop()
    asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(asyncio_loop,))
    asyncio_thread.start()

    # Schedule the asyncio tasks from the main thread
    asyncio.run_coroutine_threadsafe(main_bluetooth_code(update_queue), asyncio_loop)

    # Start the Tkinter main loop
    root.mainloop()

    # Clean up: Stop the asyncio loop
    asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
    asyncio_thread.join()

if __name__ == "__main__":
    main()
