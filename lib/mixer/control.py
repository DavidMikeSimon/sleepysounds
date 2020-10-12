import os

def change_volume(set_volume):
    set_vol_cmd = 'amixer -c1 set Speaker playback {volume}% > /dev/null'.format(volume=set_volume)
    os.system(set_vol_cmd)  # set volume
    os.system('alsactl store > /dev/null')
    return 'Changed volume'