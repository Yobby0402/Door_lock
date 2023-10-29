import machine
from machine import Pin, UART


class FPM383C:
    """
    This class is used to control the FPM383C fingerprint module.
    """
    
    def __init__(self, uart_obj, en=None, touch_out=None, enroll_time=1):
        if isinstance(uart_obj, machine.UART):
            self.uart = uart_obj
        else:
            raise TypeError("UART object required!")
        
        if en is not None:
            self.en = en
            self.en_pin = Pin(self.en, Pin.OUT)
            self.en_pin.value(1)  # According to the user manual, this module is best equipped with a separate power supply circuit and uses MOSFET to control the power supply
        if touch_out is not None:
            self.touch_out = touch_out
            self.touch_out_pin = Pin(self.touch_out, Pin.IN)
        
        self.enroll_time = enroll_time
        
        self.header = b'\xef\x01'
        self.device_address = b'\xff\xff\xff\xff'
        
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
                                  '33': "The image area is too small"
                                  }  # Confirmation code definition
        # IPL:Instruction pack length
        # APL:Answer pack length
        # IC: Answer code
        # CC: Confirmation code
        # PC: Parameter content
        # FD: Function description
        
        self.generic_instructions = {'GetImage': {'IPL': b'\x00\x03', 'APL': b'\x00\x03', 'IC': b'\x01', 'CC': ['00', '01', '02'], 'FD': "When verifying the fingerprint, the finger is probed, and the fingerprint image is entered into the image buffer after detection"},
                                     'GenChar': {'IPL': b'\x00\x03', 'APL': b'\x00\x04',
                                                 'IC': b'\x02', 'CC': ['00', '01', '06', '07', '08', '0a', '15', '28'],
                                                 'FD': "Generate a fingerprint signature file from the original image in the image buffer and store it in the template buffer"},
                                     'Match': {'IPL': b'\x00\x03', 'APL': b'\x00\x05',
                                               'IC': b'\x03', 'CC': ['00', '01', '08', '31'],
                                               'FD': "This function is supported for accurate comparison of signature files or templates in the template buffer, as shown in Table 2-1 when the encryption level is set to 0 or 1"},
                                     'Search': {'IPL': b'\x00\x08', 'APL': b'\x00\x07',
                                                'IC': b'\x04', 'CC': ['00', '01', '09', '17', '31'],
                                                'FD': "Search for all or part of the fingerprint library with signatures in the template buffer. If searched, the page number is returned.This feature is supported if the encryption level is set to 0 or 1 in Table 2-1"},
                                     'RegModel': {'IPL': b'\x00\x03',
                                                  'APL': b'\x00\x03', 'IC': b'\x05', 'CC': ['00', '01', '0a'],
                                                  'FD': "After fusing the signature files, a template is generated, and the result is stored in the template buffer."},
                                     'StoreChar': {'IPL': b'\x00\x06',
                                                   'APL': b'\x00\x03', 'IC': b'\x06',
                                                   'CC': ['00', '01', '0b', '18', '31'],
                                                   'FD': "When verifying the fingerprint, the finger is probed, and the fingerprint image is entered into the image buffer after detection"},
                                     'LoadChar': {'IPL': b'\x00\x06',
                                                  'APL': b'\x00\x03', 'IC': b'\x07', 'CC': ['00', '01', '0c', '0b'],
                                                  'FD': "Reads the fingerprint template with the specified ID number in the flash database into the template buffer"},
                                     'UpChar': {'IPL': b'\x00\x04', 'APL': b'\x00\x03',
                                                'IC': b'\x08', 'CC': ['00', '01', '0d', '31'],
                                                'FD': "Upload the template file saved in the template buffer to the master. This function is supported if the encryption level is set to 0 in Table 2-1."},
                                     'DownChar': {'IPL': b'\x00\x04',
                                                  'APL': b'\x00\x03', 'IC': b'\x09', 'CC': ['00', '01', '0e', '31'],
                                                  'FD': "The master downloads the template to a template buffer of the module. This feature is supported when the encryption level is set to 0 in Table 2-1."},
                                     'DeleteChar': {'IPL': b'\x00\x07',
                                                    'APL': b'\x00\x03', 'IC': b'\x0c', 'CC': ['00', '01', '02'],
                                                    'FD': "Deletes the specified ID in the Flash database."},
                                     'Empty': {'IPL': b'\x00\x03', 'APL': b'\x00\x03',
                                               'IC': b'\x0d', 'CC': ['00', '01', '11'],
                                               'FD': "Delete all fingerprints in the Flash database."},
                                     'WriteReg': {'IPL': b'\x00\x05',
                                                  'APL': b'\x00\x03', 'IC': b'\x0e',
                                                  'CC': ['00', '01', '18', '1a', '1b'],
                                                  'FD': "Write the module register."},
                                     'ReadSysPara': {'IPL': b'\x00\x03',
                                                     'APL': b'\x00\x13', 'IC': b'\x0f', 'CC': ['00', '01'],
                                                     'FD': "Read the basic parameters of the module (baud rate, packet size, etc.)."},
                                     'ReadINFpage': {'IPL': b'\x00\x03',
                                                     'APL': b'\x00\x03', 'IC': b'\x16', 'CC': ['00', '01', '0d'],
                                                     'FD': "Read the parameter page (512bytes) where the FLASH Information Page is located."},
                                     'BurnCode': {'IPL': b'\x00\x04',
                                                  'APL': b'\x00\x03', 'IC': b'\x1a',
                                                  'CC': ['00', '01', '0e'],
                                                  'FD': "The master sends a wipe code command, and the module will enter the upgrade mode after replying."},
                                     'ValidTemplateNum': {'IPL': b'\x00\x05',
                                                          'APL': b'\x00\x05', 'IC': b'\x1d',
                                                          'CC': ['00', '01'],
                                                          'FD': "Read the number of valid templates."},
                                     'ReadIndexTable': {'IPL': b'\x00\x04',
                                                        'APL': b'\x00\x23', 'IC': b'\x1f', 'CC': ['00', '01', '0b'],
                                                        'FD': "Read the number of indexes for the entry template."},
                                     'GetEnrollImage': {'IPL': b'\x00\x03',
                                                        'APL': b'\x00\x03', 'IC': b'\x29', 'CC': ['00', '01', '02'],
                                                        'FD': "When registering a fingerprint, the finger is probed, and the fingerprint image is entered into the image buffer after detection."},
                                     'Sleep': {'IPL': b'\x00\x03',
                                               'APL': b'\x00\x03', 'IC': b'\x33', 'CC': ['00', '01'],
                                               'FD': "Set the sensor into sleep mode."},
                                     }
        
        self.model_instructions = {'Cancel': {'IPL': b'\x00\x03', 'APL': b'\x03', 'IC': '\x30', 'CC': ['00', '01', '31'],
                                              'FD': 'Cancel auto-enrollment templates and auto-verify fingerprints. This feature is supported if the encryption level is set to 0 or 1 in Table 2-1.'},
                                   'AutoEnroll': {'IPL': b'\x00\x08', 'APL': b'\x05', 'IC': '\x31',
                                                  'CC': ['00', '01', '07', '0a', '0b', '1f', '22', '25', '26', '27', '31'],
                                                  'FD': 'One-stop fingerprint registration, including functions such as collecting fingerprints, generating features, combining templates, and storing templates. This feature is supported if the encryption level is set to 0 or 1 in Table 2-1.'},
                                   'AutoIdentify': {'IPL': b'\x00\x08', 'APL': b'\x08', 'IC': '\x32',
                                                    'CC': ['00', '01', '07', '09', '0b', '17', '23', '24', '26', '27', '31'],
                                                    'FD': 'One-stop fingerprint registration,including'}
                                   }
        