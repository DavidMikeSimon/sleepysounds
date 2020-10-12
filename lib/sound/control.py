import subprocess

def play_sound(filename):
    subprocess.call('killall mpg123', shell=True)
    subprocess.call('mpg123 -a hw:1,0 -r 48000 -f -90000 --loop -1 '+ filename +' &', shell=True)
    return 'Playing sound: '+filename

def stop_sound():
    subprocess.call('killall mpg123', shell=True)
    return 'Stopped sound.'
