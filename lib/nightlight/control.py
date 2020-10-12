import os
import stat
import threading
import unicornhat as unicorn
unicorn.set_layout(unicorn.AUTO)
NUM_ROWS = 4
NUM_COLS = 8
def nightlight_set(red, green, blue, brightness):
    r, g, b = int(red), int(green), int(blue)    
    
    unicorn.brightness(float(brightness))

    grid = [
        [(r, g, b) for col in range(NUM_COLS)]
        for row in range(NUM_ROWS)
    ]
    unicorn.set_pixels(grid)
    return 'Nightlight configured successfully.'
def nightlight_off():
    s = threading.Thread(None,unicorn.clear)
    s.start()
    return 'Nightlight off.'
def nightlight_on():
    s = threading.Thread(None,unicorn.show)
    s.start()
    return 'Nightlight on.'