import binascii
import machine
import time
from machine import Pin, UART
import Player


class FPM383C:
    """
    This class is used to control FPM383C, but only has the basic functions of auto-registration, auto-authentication, and light control lights
    Attributes:
        en_pin(Pin): This Pin is used to control the power supply of the FPM383C. Low level to open the FPM383C.
        model_status(bool): This is used to check if the FPM383C is OPEN or not.
    """
    
    def __init__(self, uart_obj, en=None, touch_out=None, device_address=None):
        self._result_dict_list = None
        self._current_message = None
        self._result_dict = None
        self._received_confirmation_code = None
        self.player = Player
        if isinstance(uart_obj, machine.UART):
            self.uart = uart_obj
        else:
            raise TypeError("UART object required!")
        
        self.model_status = False
        if en is not None:
            self.en = en
            self.en_pin = Pin(self.en, Pin.OUT)
            self.en_pin.value(
                1)  # According to the user manual, this module is best equipped with a separate power supply circuit and uses MOS-FET to control the power supply
            self.model_init()
        else:
            self.en = None
            self.model_status = True
        
        if touch_out is not None:
            self.touch_out = touch_out
            self.touch_out_pin = Pin(self.touch_out)
        
        self._header = bytearray([239, 1])
        if device_address is None:
            self._device_address = bytearray([255, 255, 255, 255])
        else:
            self._device_address = bytearray(device_address)
        
        self._all_para_data = ''
        self._write_conclusions = b''
        self._write_list = []
        
        self._sys_para_list = ['EnrollTimes', 'FingerprintTemplateSize', 'FingerprintLibrary', 'ScoreLevelCode',
                               'DeviceAddressH', 'DeviceAddressL', 'DataPackageSize', 'BaudRate']
        self._sys_para_dic = {}
        
        self._write_params = 0
        self._sum = 0
        
        self._confirmation_code = {'00': "OK",
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
        
        self._confirmation_code_cn = {'00': "操作成功",
                                      '01': "数据包接收错误",
                                      '02': "传感器上没有手指",
                                      '03': "无法输入指纹图像",
                                      '04': "指纹图像过干或过浅，无法提取特征",
                                      '05': "指纹图像过湿或过粘，无法提取特征",
                                      '06': "指纹图像混乱，无法提取特征",
                                      '07': "指纹图像正常，但特征点过少（或过小），无法生成特征",
                                      '08': "指纹不匹配",
                                      '09': "未找到指纹",
                                      '0a': "特征合并失败",
                                      '0b': "地址序列号超出指纹数据库范围",
                                      '0c': "从指纹库读取模板错误或无效",
                                      '0d': "上传特征失败",
                                      '0e': "模块无法接收后续数据包",
                                      '0f': "上传图像失败",
                                      '10': "删除模板失败",
                                      '11': "清空指纹库失败",
                                      '12': "无法进入低功耗状态",
                                      '13': "密码错误",
                                      '14': "系统重置失败",
                                      '15': "缓冲区中没有有效原始地图以生成图像",
                                      '16': "在线升级失败",
                                      '17': "采集间有残留指纹或手指移动",
                                      '18': "读写FLASH错误",
                                      '19': "随机数生成失败",
                                      '1a': "无效的寄存器编号",
                                      '1b': "寄存器设置不正确",
                                      '1c': "记事本页码指定不正确",
                                      '1d': "端口操作失败",
                                      '1e': "自动注册失败",
                                      '1f': "指纹库已满",
                                      '20': "设备地址错误",
                                      '21': "密码错误",
                                      '22': "指纹模板不为空",
                                      '23': "指纹模板为空",
                                      '24': "指纹库为空",
                                      '25': "条目数量设置不正确",
                                      '26': "超时",
                                      '27': "指纹已存在",
                                      '28': "指纹特征已关联",
                                      '29': "传感器初始化失败",
                                      '2a': "模块信息不为空",
                                      '2b': "模块信息为空",
                                      '2c': "OTP操作失败",
                                      '2d': "密钥生成失败",
                                      '2e': "密钥不存在",
                                      '2f': "安全算法执行失败",
                                      '30': "安全算法加解密结果不正确",
                                      '31': "功能与加密级别不匹配",
                                      '32': "密钥已锁定",
                                      '33': "图像区域太小"}
        
        self._auto_enroll_conformation_code = {'00': 'Success',
                                               '01': 'Failure',
                                               '07': 'Generate template Failure',
                                               '0a': 'Merge Template Failure',
                                               '0b': 'ID number out of range',
                                               '1f': 'Fingerprint library is full',
                                               '22': 'Fingerprint template is not empty',
                                               '25': 'Wrong enroll times',
                                               '26': 'Timeout',
                                               '27': 'Fingerprint has exist',
                                               '31': "The functionality does not match the encryption level"
                                               }
        
        self._auto_enroll_conformation_code_cn = {'00': '成功',
                                                  '01': '失败',
                                                  '07': '生成特征失败',
                                                  '0a': '合并模板失败',
                                                  '0b': 'ID号超出范围',
                                                  '1f': '指纹库已满',
                                                  '22': '指纹模板非空',
                                                  '25': '录入次数设置错误',
                                                  '26': '超时',
                                                  '27': '指纹已存在',
                                                  '31': "功能与加密等级不匹配"
                                                  }
        
        self._auto_enroll_param1 = {'00': 'Fingerprint legitimacy detection',
                                    '01': 'Get image',
                                    '02': 'Generate template',
                                    '03': 'Determine finger leaving',
                                    '04': 'Merge template',
                                    '05': 'Registered inspection',
                                    '06': 'Restore template'
                                    }
        
        self._auto_enroll_param1_cn = {'00': '指纹合法性检测',
                                       '01': '获取图像',
                                       '02': '生产特征',
                                       '03': '判断手指离开',
                                       '04': '合并模板',
                                       '05': '注册检验',
                                       '06': '存储模板'
                                       }
        
        self._auto_enroll_param2 = {'00': 'Fingerprint legitimacy detection',
                                    'f0': 'Merge template',
                                    'f1': 'Check that the finger is registered',
                                    'f2': 'Restore Template'
                                    }
        
        self._auto_enroll_param2_cn = {'00': '指纹合法性检测',
                                       'f0': '合并模板',
                                       'f1': '检验该手指是否已经注册',
                                       'f2': '存储模板'
                                       }
        
        self._auto_identify_param = {'00': 'Fingerprint legitimacy detection',
                                     '01': 'Get image',
                                     '05': 'Registered fingerprint matching'
                                     }
        
        self._auto_identify_param_cn = {'00': '指纹合法性检测',
                                        '01': '获取图像',
                                        '05': '已注册指纹搜索'
                                        }
    
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
        if para_name not in self._sys_para_list:
            raise ValueError('Parameter must be one of{}'.format(self._sys_para_list))
        self._write_conclusions = self._header + self._device_address + b'\x01\x00\x03\x0f\x00\x13'
        self.uart.write(self._write_conclusions)
        time.sleep_ms(1)
        if self.uart.any():
            self._all_para_data = binascii.hexlify(self.uart.read()).decode()[22:]
        if self._all_para_data[0:2] != '00':
            print(self._confirmation_code[self._all_para_data[0:2]])
            return 'Error'
        else:
            for i in range(len(self._sys_para_list)):
                self._sys_para_dic[self._sys_para_list[i]] = self._all_para_data[i * 2 + 2:i * 2 + 4]
            if para_name is None:
                return self._sys_para_dic
            else:
                return self._sys_para_dic[para_name]
    
    def cancel_direction(self):
        """
        Cancels the direction of the auto-enrollment or auto-identification.
        :return:
        """
        self._write_list = [1, 0, 3, 48, 0, 52]
        self.uart.write(self._header + self._device_address + bytearray(self._write_list))
    
    def model_sleep(self):
        self._write_list = [1, 0, 3, 51, 0, 55]
        self.uart.write(self._header + self._device_address + bytearray(self._write_list))
        print(binascii.hexlify(self.uart.read()).decode())
    
    def auto_enroll(self, id_number, enroll_times=6, abc=0, apc=0, ksr=0, oid=1, fdr=0, afl=0):
        """
        This method is to automatically enroll one fingerprint.
        :param id_number: ID number to enroll.
        :param abc:Acquisition backlight control bits.0:solid LED,1:Off LED after acquisition.
        :param apc:Acquisition preprocessing control bits.0:Close preprocessing,1:Open preprocessing.
        :param ksr:Key steps return.0:Return,1:No need to return.
        :param oid:Allow to override the ID number.0:Not allowed,1:Allow.
        :param fdr:Fingerprint duplicate registration.
        :param afl:Ask your finger to leave.
        :param enroll_times:The number of repetitions, up to a maximum of 6
        :return:None
        """
        self._write_list = []
        self._result_dict = {}
        self._result_dict_list = []
        self._write_params = int(f"{afl}{fdr}{oid}{ksr}{apc}{abc}", 2)
        self._sum = 58 + id_number + enroll_times + self._write_params
        self._write_conclusions = self._header + self._device_address + b'\x01\x00\x08\x31' + bytearray(
            [0, id_number, enroll_times, 0, self._write_params]) + self._sum.to_bytes(2, 'big')
        print('Auto Enrollment Start! Sending:' + str(binascii.hexlify(self._write_conclusions)))
        # print(bytes(self._write_conclusions))
        self.uart.write(bytes(self._write_conclusions))
        while True:
            try:
                self._current_message = binascii.hexlify(self.uart.read(14)).decode()
                print(self._current_message)
                self._result_dict = {'header': self._current_message[0:4],
                                     'device_address': self._current_message[4:12],
                                     'package_identification': self._current_message[12:14],
                                     'package_length': self._current_message[14:18],
                                     'conformation_code': self._current_message[18:20],
                                     'param1': self._current_message[20:22],
                                     'param2': self._current_message[22:24],
                                     'check_sum': self._current_message[24:28]
                                     }
                if self._result_dict['param2'] in self._auto_enroll_param2_cn:
                    self._result_dict_list.append(self._auto_enroll_param2_cn[self._result_dict['param2']] +
                                                  self._auto_enroll_param1_cn[self._result_dict['param1']] +
                                                  self._auto_enroll_conformation_code_cn[
                                                      self._result_dict['conformation_code']])
                    if self._result_dict['param2'] == '00':
                        self.player.play_music_finger('请放手指')
                else:
                    self._result_dict_list.append('第{}次注册'.format(self._result_dict['param2']) +
                                                  self._auto_enroll_param1_cn[self._result_dict['param1']] +
                                                  self._auto_enroll_conformation_code_cn[
                                                      self._result_dict['conformation_code']])
                    self.player.play_music_finger('采集成功,请重新放手指')
            except OSError:
                break
            except TypeError:
                break
            except KeyError:
                self._result_dict_list.append('模组状态异常')
        self.player.play_music_finger('指纹录入成功')
        return self._result_dict_list
    
    def auto_identify(self, level=0, abc=0, apc=0, ksr=0):
        self._write_list = []
        self._result_dict = {}
        self._result_dict_list = []
        self._write_params = int(f"{ksr}{apc}{abc}", 2)
        self._sum = 59 + 255 + 255 + level + self._write_params
        print(self._sum.to_bytes(2, 'big'))
        self._write_conclusions = self._header + self._device_address + b'\x01\x00\x08\x32' + bytearray(
            [level, 255, 255, 0, self._write_params]) + self._sum.to_bytes(2, 'big')
        print('Auto Identify Start! Sending:' + str(binascii.hexlify(self._write_conclusions)))
        print(bytes(self._write_conclusions))
        self.uart.write(bytes(self._write_conclusions))
        while True:
            try:
                self._current_message = binascii.hexlify(self.uart.read(17)).decode()
                print(self._current_message)
                self._result_dict = {'header': self._current_message[0:4],
                                     'device_address': self._current_message[4:12],
                                     'package_identification': self._current_message[12:14],
                                     'package_length': self._current_message[14:18],
                                     'conformation_code': self._current_message[18:20],
                                     'param': self._current_message[20:22],
                                     'ID_number': self._current_message[22:26],
                                     'grade': self._current_message[26:30],
                                     'checksum': self._current_message[30:34]
                                     }
                print(self._result_dict)
                if self._result_dict['param'] in self._auto_identify_param_cn:
                    print(self._auto_identify_param_cn[self._result_dict['param']] +
                                                  self._confirmation_code_cn[
                                                      self._result_dict['conformation_code']])
            except OSError:
                break
            except TypeError:
                break
            except KeyError:
                self._result_dict_list.append('模组状态异常')
        return self._result_dict_list


if __name__ == '__main__':
    u = machine.UART(2, 57600, rx=17, tx=16, timeout=20000)
    f = FPM383C(u)
