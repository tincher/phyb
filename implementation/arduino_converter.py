import cli_ui
from serial import Serial
from pretty_prints import *

def read_from_arduino(arduino_path, count=5, baud=57600):
    '''Reads from the arduino, cancelling on ctrl-c

    Parameters
    ----------
    arduino_path : string
        Path to the arduino.
    count : int
        Number of executions (the default is 5).
    baud : int
        Baud-rate to use to communicate with the arduino (the default is 57600).

    Returns
    -------
    array_like
        All received data for each execution.
    '''
    accel_setting = 2
    gyro_setting = 1
    converter = ArduinoConverter(accel_setting, gyro_setting)

    current_exercise = []
    for i in range(count):
        current_run = []
        try:
            with Serial(arduino_path, baud, timeout=10, write_timeout=5) as my_serial:
                while True:
                    line = my_serial.readline()
                    result = converter.convert(line)
                    if result == ['ST passed']:
                        print_circle(cli_ui.green)
                    elif result == ['ST failed']:
                        print('Sensor self-test failed!')
                        exit()
                    elif result == ['ST init']:
                        pass
                    elif result is not None:
                        current_run.append(result)
        except KeyboardInterrupt:
            current_exercise.append(current_run)
    return current_exercise


class ArduinoConverter:
    '''Converts the received data to a usable format.

    Parameters
    ----------
    accel_setting : int
        Setting of the acceleration sensor (the default is 2).
    gyro_setting : type
        Setting of the gyroscope sensor (the default is 1).

    Attributes
    ----------
    fts : array_like
        Results of the self test calculation.
    testing : bool
        Set if self-test is currently going in progress
    last_data : array_like
        Last received and converted data.
    accel_setting
    gyro_setting

    '''
    def __init__(self, accel_setting=2, gyro_setting=1):
        self.accel_setting = accel_setting
        self.gyro_setting = gyro_setting
        self.fts = []
        self.testing = False
        self.last_data = []

    def init_self_test(self, values):
        '''Initializes the self test procedure.

        Parameters
        ----------
        values : array_like
            Values of the self test timestep.

        Returns
        -------
        None
        '''
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
        '''End of the self test procedure.

        Parameters
        ----------
        values : array_like
            Values of the first time step after the self test timestep.

        Returns
        -------
        bool
            True if the self test is passed.
        '''
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
        '''Calculates the difference between the 2 data points.

        Parameters
        ----------
        st_enabled_data : array_like
            Data point with self test enabled.
        st_disabled_data : type
            Data point with self test disabled.

        Returns
        -------
        array_like
            Data point with the element-wise difference.
        '''
        result = []
        for enabled_data, disabled_data in zip(st_enabled_data, st_disabled_data):
            result.append(enabled_data - disabled_data)
        return result

    def convert(self, raw_data):
        '''Convert the received data to 6-dimensional data point.

        Parameters
        ----------
        raw_data : string
            The string data received from the arduino.

        Returns
        -------
        array_like
            The data point or a list with a single string carrying self-test information progress.
        '''
        values = raw_data.decode().replace('\n', '').split(' ')
        if values[0] == 'D':
            try:
                data = list(map(int, values[1:]))
                if self.testing:
                    self_test_passed = self.finish_self_test(data)
                    self.testing = False
                    return ['ST passed'] if self_test_passed else ['ST failed']
                self.last_data = data
                return data
            except Exception as e:
                # dismissed because of asynchronicity
                pass
        elif values[0] == 'S':
            data = list(map(int, values[1:]))
            self.init_self_test(data)
            return ['ST init']
