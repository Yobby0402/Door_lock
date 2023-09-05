import machine
from machine import Pin


class Encoder:
    def __init__(self, encoder_a_pin_number=32, encoder_b_pin_number=33):
        self.encoder_pin_list = [Pin(encoder_a_pin_number, Pin.IN), Pin(encoder_b_pin_number, Pin.IN)]
        self.encoder_flag_list = [False, False]
        self.rotate_direction_list = ['clockwise', 'counter-clockwise']
        self.direction = ''
        self.state_list = []
    
    def callback_handler(self, pin):
        pin_index = self.encoder_pin_list.index(pin)
        print(pin_index)
        for i in range(2):
            self.state_list.append(self.encoder_pin_list[i].value())
            
        
        self.direction = self.rotate_direction_list[self.state_list[0]]