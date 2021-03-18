import cli_ui
from serial import Serial
from pretty_prints import *


def read_from_arduino(count=5, baud=57600):
    accel_setting = 2
    gyro_setting = 1
    converter = ArduinoConverter(accel_setting, gyro_setting)

    current_exercise = []
    for i in range(count):
        current_run = []
        try:
            with Serial('/dev/cu.usbserial-1420', baud, timeout=10, write_timeout=5) as my_serial:
                while True:
                    line = my_serial.readline()
                    result = converter.convert(line)
                    if result == 'ST passed':
                        print_circle(cli_ui.green)
                    elif result == 'ST failed':
                        print('Sensor self-test failed!')
                        exit()
                    elif result is not None:
                        current_run.append(result)
        except KeyboardInterrupt:
            current_exercise.append(current_run)
    return current_exercise


class ArduinoConverter:
    def __init__(self, accel_setting=2, gyro_setting=1):
        self.accel_setting = accel_setting
        self.gyro_setting = gyro_setting
        self.fts = []
        self.testing = False
        self.last_data = []

    def convert_accel_gyro(self, data):
        result = []
        for i, elem in enumerate(data):
            if i < 3:
                # in g
                result.append(elem / (16384 / (2 ** self.accel_setting)))
            else:
                # in grad pro sekunde
                result.append(elem / (131 / (2 ** self.gyro_setting)))
        return result

    def init_self_test(self, values):
        self.fts = []
        prefactor = -25
        for index, value in enumerate(values):
            if value == 0:
                continue
            if index < 3:
                prefactor = prefactor * (-1)
                self.fts.append(prefactor * 131 * (1.046 ** (value - 1)))
            else:
                self.fts.append(4096 * 0.34 * ((0.92 * 0.34) ** ((value - 1) / ((2 ** 5) - 2))))
        self.testing = True

    def finish_self_test(self, values):
        st_response = self.calc_diff_from_outputs(self.last_data, values)
        result = []
        for i, elem in enumerate(st_response):
            result.append((st_response[i] - self.fts[i]) / self.fts[i])
        if any(map(lambda x: not (-14 <= x <= 14), result)):
            return False
        self.testing = False
        return True

    @staticmethod
    def calc_diff_from_outputs(st_enabled_data, st_disabled_data):
        result = []
        for enabled_data, disabled_data in zip(st_enabled_data, st_disabled_data):
            result.append(enabled_data - disabled_data)
        return result

    def convert(self, raw_data):
        values = raw_data.decode().replace('\n', '').split(' ')
        if values[0] == 'D':
            try:
                data = list(map(int, values[1:]))
                if self.testing:
                    self_test_passed = self.finish_self_test(data)
                    self.testing = False
                    return 'ST passed' if self_test_passed else 'ST failed'
                self.last_data = data
                return data
            except Exception as e:
                # print('dismiss bc async')
                pass
        elif values[0] == 'S':
            data = list(map(int, values[1:]))
            self.init_self_test(data)
