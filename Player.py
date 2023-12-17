import machine
from machine import UART
music_name = None
player_uart = UART(1, 9600, tx=26, rx=27)

finger_wav_dict = {"请放手指": '00100',
                   "采集成功,请重新放手指": '00101',
                   "请求超时": '00102',
                   "指纹录入成功": '00103'
                   }


def volume_set(volume=31):
    player_uart.write(b'AF:{}'.format(volume))

def play_music(music_name):
    player_uart.write(b'A7:{}'.format(music_name))

def play_music_finger(music_name):
    if music_name in finger_wav_dict:
        play_music(finger_wav_dict[music_name])


volume_set()
