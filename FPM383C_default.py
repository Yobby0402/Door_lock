import binascii
import machine
import time
from machine import Pin


class FPM383C:
    """
    This class is used to control FPM383C, but only has the basic functions of auto-registration, auto-authentication, and light control lights
    Attributes:
        en_pin(Pin): This Pin is used to control the power supply of the FPM383C. Low level to open the FPM383C.
        model_status(bool): This is used to check if the FPM383C is OPEN or not.
    """
    
    def __init__(self, uart_obj, en=None, touch_out=None, device_address=None):
        if isinstance(uart_obj, machine.UART):
            self.uart = uart_obj
        else:
            raise TypeError("UART object required!")
        
        self.model_status = False
        if en is not None:
            self.en = en
            self.en_pin = Pin(self.en, Pin.OUT)
            self.en_pin.value(1)  # According to the user manual, this module is best equipped with a separate power supply circuit and uses MOS-FET to control the power supply
            self.model_init()
        else:
            self.en = None
            self.model_status = True
        
        if touch_out is not None:
            self.touch_out = touch_out
            self.touch_out_pin = Pin(self.touch_out, Pin.IN)
        
        self._header = bytearray([239, 1])
        if device_address is None:
            self._device_address = bytearray([255, 255, 255, 255])
        else:
            self._device_address = bytearray(device_address)
        
        self._all_para_data = ''
        self._write_conclusions = b''
        self._write_list = []
        
        self.sys_para_list = ['EnrollTimes', 'FingerprintTemplateSize', 'FingerprintLibrary', 'ScoreLevelCode',
                              'DeviceAddressH', 'DeviceAddressL', 'DataPackageSize', 'BaudRate']
        self._sys_para_dic = {}
        
        self._write_params = 0
        self._sum = 0
        
        self.confirmation_code = {'00': "OK",
                                  '01': "Packet received error",
                                  '02': "No finger on sensor",
                                  '03': "Failed to enter fingerprint image",
                                  '04': "The fingerprint image is too dry or too light to be featured",
                                  '05': "Fingerprint images are too wet and too pasty to be featured",
                                  '06': "Fingerprint images are to messy to be featured",
                                  '07': "The fingerprint image is normal, but the feature points are too few (or too small) to produce features",
                                  '08': "Fingerprints do not match",
                                  '09': "No fingerprints were found",
                                  '0a': "Feature merge failed",
                                  '0b': "The address sequence number is outside the scope of the fingerprint database",
                                  '0c': "Reading templates from the fingerprint library is incorrect or invalid",
                                  '0d': "Failed to upload feature",
                                  '0e': "The module cannot receive subsequent packets",
                                  '0f': "Failed to upload image",
                                  '10': "Failed to delete template",
                                  '11': "Failed to empty the fingerprint vault",
                                  '12': "Cannot enter a low-power state",
                                  '13': "The password is incorrect",
                                  '14': "System reset failed",
                                  '15': "There is no valid original map in the buffer to produce an image",
                                  '16': "Online upgrade failed",
                                  '17': "Residual fingerprints or finger movements between acquisitions",
                                  '18': "Error reading or writing FLASH",
                                  '19': "Random number generation failed",
                                  '1a': "Invalid register number",
                                  '1b': "The register setting is incorrect",
                                  '1c': "Notepad page number specified incorrectly",
                                  '1d': "The port operation failed",
                                  '1e': "Auto enroll failed",
                                  '1f': "The fingerprint library is full",
                                  '20': "The device address is wrong",
                                  '21': "Wrong password",
                                  '22': "The fingerprint template is not empty",
                                  '23': "The fingerprint template is empty",
                                  '24': "The fingerprint library is empty",
                                  '25': "The number of entries is set incorrectly",
                                  '26': "Timeout",
                                  '27': "Fingerprint already exists",
                                  '28': "Fingerprint features are associated",
                                  '29': "Sensor initialization failed",
                                  '2a': "The module information is not empty",
                                  '2b': "The module information is empty",
                                  '2c': "OTP operation failed",
                                  '2d': "Key generation failed",
                                  '2e': "The key does not exist",
                                  '2f': "Security algorithm execution failed",
                                  '30': "The security algorithm encryption and decryption results are incorrect",
                                  '31': "The functionality does not match the encryption level",
                                  '32': "The key is locked",
                                  '33': "The image area is too small"}
        
    def model_init(self):
        """
        This function is called when you have been equipped with a separate power supply circuit and use a pin to control the device's power.
        :return:True or False
        """
        self.en_pin.value(0)
        time.sleep_ms(10)
        if self.uart.any():
            if binascii.hexlify(self.uart.read()) != b'55':
                print('Failed to initialize!')
                self.model_status = False
            else:
                print('Initialized!')
                self.model_status = True
    
    def read_sys_para(self, para_name=None):
        """
        Read the basic parameters of the module (baud rate, packet size, etc.).
        :param para_name: The name of the parameter to read.
        :return: all the system parameter or one of them
        """
        if para_name not in self.sys_para_list:
            raise ValueError('Parameter must be one of{}'.format(self.sys_para_list))
        self._write_conclusions = self._header + self._device_address + b'\x01\x00\x03\x0f\x00\x13'
        self.uart.write(self._write_conclusions)
        time.sleep_ms(1)
        if self.uart.any():
            self._all_para_data = binascii.hexlify(self.uart.read())[22:]
        if self._all_para_data[0:2] != '00':
            print(self.confirmation_code[self._all_para_data[0:2]])
            return 'Error'
        else:
            for i in range(len(self.sys_para_list)):
                self._sys_para_dic[self.sys_para_list[i]] = self._all_para_data[i*2+2:i*2+4]
            if para_name is None:
                return self._sys_para_dic
            else:
                return self._sys_para_dic[para_name]

    def cancel_direction(self):
        """
        Cancels the direction of the auto-enrollment or auto-identification.
        :return:
        """
        self._write_list = [1, 0, 3, 48, 52]
        self.uart.write(self._header+self._device_address+bytearray(self._write_list))
        
    def auto_enroll(self, ID_number, enroll_times, fp_id, abc=0, apc=0, ksr=0, oid=0, fdr=0, afl=0):
        """
        This method is to automatically enroll one fingerprint.
        :param ID_number: ID number to enroll.
        :param abc:Acquisition backlight control bits.0:solid LED,1:Off LED after acquisition.
        :param apc:Acquisition preprocessing control bits.0:Close preprocessing,1:Open preprocessing.
        :param ksr:Key steps return.0:Return,1:No need to return.
        :param oid:Allow to override the ID number.0:Not allowed,1:Allow.
        :param fdr:Fingerprint duplicate registration.
        :param afl:Ask your finger to leave.
        :param enroll_times:The number of repetitions, up to a maximum of 4
        :param fp_id:The ID number to be entered into the fingerprint.
        :return:None
        """
        self._write_list = []
        self._write_params = int(f"0000000000{afl}{fdr}{oid}{ksr}{apc}{abc}", 2)
        self._sum = 49+ID_number+enroll_times+self._write_params
        self._write_conclusions = self._header + self._device_address + b'\x31'+bytearray([0, ID_number, enroll_times, self._write_params, self._sum])
        print('Auto Enrollment Start! Sending:' + str(self._write_conclusions))
        while not self.uart.any():
            pass
        