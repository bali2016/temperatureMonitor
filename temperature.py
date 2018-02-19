import time


class Temperature:
    total = 5  # only keep 5 temperatures history in cache

    def __init__(self, normal_temperature=30, auto_adjust=True, accuracy=0, storage=None):
        self.temperature_history = []
        self.temperature_trend = 0  # 0: temperature keeps the same;  -1: down, 1: up
        self.temperature_trend_count = 0  # the count of trend keeps in one state.
        self.normal_temperature = normal_temperature
        self.__normal_temperature_auto_adjust = auto_adjust
        self.__auto_normal_temperature = 0
        self.__auto_normal_temperature_number = 0
        self.__auto_normal_temperature_length = 50  # Continuously detect length
        self.accuracy = accuracy
        self.temperature_storage = storage if storage else "./temperature_records"

    def add(self, temperature):
        # Store the temperature
        self.temperature_history.append(temperature)
        with open(self.temperature_storage, 'a') as f:
            f.write(str(temperature) + " " + time.strftime("%H:%M:%S") + " \n")

        if len(self.temperature_history) > self.total:
            del self.temperature_history[0]  # delete the first one in the cache

            # Check the temperature trend
            last_avg_temperature = sum(self.temperature_history[:-1]) / (self.total - 1)
            # print self.temperature_history, last_avg_temperature
            if temperature > last_avg_temperature + self.accuracy:
                if self.temperature_trend == 1:
                    self.temperature_trend_count += 1
                else:
                    self.temperature_trend = 1
                    self.temperature_trend_count = 1

                self.__reset_auto_adjust_normal_temperature()  # reset the auto normal adjust
            elif temperature < last_avg_temperature - self.accuracy:
                if self.temperature_trend == -1:
                    self.temperature_trend_count += 1
                else:
                    self.temperature_trend = -1
                    self.temperature_trend_count = 1

                self.__reset_auto_adjust_normal_temperature()  # reset the auto normal adjust
            else:
                if self.temperature_trend == 0:
                    self.temperature_trend_count += 1
                else:
                    self.temperature_trend = 0
                    self.temperature_trend_count = 1

                if self.__normal_temperature_auto_adjust:
                    self.__auto_adjust_normal_temperature(temperature)

    def get_latest_temperature(self):
        return self.temperature_history[-1]

    def reset_trend(self):
        self.temperature_trend = 0
        self.temperature_trend_count = 0

    def __auto_adjust_normal_temperature(self, temperature):
        # If the temperature continually keeps in trend 1 for more than 10 times, then set the
        # normal temperature to the average of the 10 temperatures
        self.__auto_normal_temperature += temperature
        self.__auto_normal_temperature_number += 1
        # print ('__auto_normal_temperature_number: %s' % self.__auto_normal_temperature_number)
        if self.__auto_normal_temperature_number >= self.__auto_normal_temperature_length:
            self.normal_temperature = round(self.__auto_normal_temperature / self.__auto_normal_temperature_length, 2)
            print ('Info: Resetting normal temperature to %s' % self.normal_temperature)
            self.__reset_auto_adjust_normal_temperature()

    def __reset_auto_adjust_normal_temperature(self):
        self.__auto_normal_temperature_number = 0
        self.__auto_normal_temperature = 0
