import multiprocessing
from rain_mixing.frontend.Window import Window

if __name__ == "__main__":
    multiprocessing.freeze_support()

    print("Loading files...")
    Window().mainloop()
