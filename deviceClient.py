#!/usr/bin/python
# -*- coding: UTF-8 -*-

# *****************************************************************************
# Copyright (c) 2017 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#   Hari hara prasad Viswanathan - Initial Contribution
# *****************************************************************************

import getopt
import time
import sys
import uuid
import threading
import time
import signal
import os
import random
import ibmiotf.device
import RPi.GPIO as GPIO
from w1thermsensor import W1ThermSensor
import itchat
from temperature import Temperature


GPIO.setmode(GPIO.BOARD)
GPIO.setup(13, GPIO.OUT)


# Global Variables
motor_up_time = time.time()
running_status = False
publish_count = 0
alert_user_name = None

def usage():
    print(
        "commandSender: Raspberry Pi-powered conveyor belt" + "\n" +
        "\n" +
        "Options: " + "\n" +
        "  -h, --help     Display help information" + "\n" +
        "  -t, --time     Time period in minutes to stop" + "\n" +
        "  -f, --file     Configuration file path" + "\n" +
        "  -i, --interval Interval to check and publish data in second" + "\n"
        )


class SetInterval:  # Timer wrapper
    def __init__(self, func, interval, max_count=0, max_time=0):
        self.max_count = max_count
        self.max_time = max_time * 60.0  # turn to minutes
        self.start_time = time.time()

        def func_wrapper():
            if (self.max_time > 0 and self.start_time + self.max_time > time.time()) or \
                    (self.max_time == 0 and (self.max_count == 0 or publish_count < self.max_count)):
                    func()
                    self.t = threading.Timer(interval, func_wrapper)
                    self.t.setDaemon(True)
                    self.t.start()
            else:
                print("Got the max detect, stop the interval")
                stop_and_exit()
        self.t = threading.Timer(interval, func_wrapper)
        self.t.setDaemon(True)
        self.t.start()
        # self.t.join()

    def cancel(self):
        print ("Cancelling the interval")
        self.t.cancel()


def start_handler():  # Turn on motor connected in pin 13
        global motor_up_time
        global running_status
        motor_up_time = time.time()
        running_status = True
        GPIO.output(13, GPIO.HIGH)
        print("starting motor")


def stop_handler():  # Turn off motor connected in pin 13
        global motor_up_time
        global running_status
        motor_up_time = time.time()
        running_status = False
        GPIO.output(13, GPIO.LOW)
        print("Stopping the motor")


def my_command_callback(cmd):  # Handle device command
    print("Command received: %s" % cmd.command)
    if cmd.command == "stop":
        stop_handler()
    if cmd.command == "start":
        start_handler()


def my_on_publish_callback():
    print("Confirmed event  received by WIoTP\n")


def get_cpu_temperature():  # Return CPU temperature as a character string
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=", "").replace("'C\n", ""))


def get_baby_temperature():  # Return air temperature as a character string
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "031724fe49ff")
    baby_temperature = round(float(sensor.get_temperature()), 2)
    temperature.add(baby_temperature)
    check_temperature()

    return baby_temperature


def get_rpm():  # Return current rpm value
    # we are generating a random value here to represent motor's r.p.m
    if not running_status:
        return 0.0
    delta = -0.1
    if (time.time() % 2) == 0:
        delta = 0.1
    rmp = random.uniform(1, 3.1) + delta
    return round(rmp, 1)


def get_ay():  # Return accelerometer value
    # we are generating a random value here to represent accelerometer
    delta = -0.05
    if (time.time() % 2) == 0:
        delta = 0.05
    ay = random.uniform(-1.0, 1.0) + delta
    return round(ay, 3)


def publish():
        global publish_count
        publish_count = publish_count + 1
        print("Send temperature to WIOIP %s" % publish_count)

        state = "false"
        if running_status:
            state = "true"
            data = {'elapsed': int(time.time() - motor_up_time),
                    'running': state,
                    'temperature': get_baby_temperature(),
                    'ay': get_ay(),
                    'rpm': get_rpm()}

            success = device_client.publishEvent(
                "sensorData",
                "json",
                {'d': data},
                qos=0,
                # on_publish=my_on_publish_callback
            )
            if not success:
                print("Not connected to WIoTP")
        else:
            print("Service is stopped")


def send_alert(msg):
    # name = u"星空2017"
    name = u"家"
    global alert_user_name
    if alert_user_name is None:
        # friend = itchat.search_friends(name=name)[0]
        friend = itchat.search_chatrooms(name=u"家")[0]
        if friend:
            alert_user_name = friend.UserName
        else:
            print('Send alert failed: Can not find such friend with name %s !' % name)

    r = itchat.send(msg, toUserName=alert_user_name)
    if r:
        print ("Send alert to %s success" % name)
    else:
        print("Send alert failed: " + r['BaseResponse']['RawMsg'])


def stop_alert_client():
    itchat.dump_login_status()


def check_temperature():
    print ("Trend: %s, trend_count: %s, latest %s, normal: %s" %
           (temperature.temperature_trend,
            temperature.temperature_trend_count,
            temperature.get_latest_temperature(),
            temperature.normal_temperature))
    # first store the latest temperature
    if temperature.temperature_trend == 1\
            and temperature.temperature_trend_count >= 10\
            and temperature.get_latest_temperature() > temperature.normal_temperature + 5:
        # send_alert("Temperature goes too hot " + str(temperature.get_latest_temperature()) + u"℃")
        send_alert(u"尿了，快来换尿布！！！")
        temperature.reset_trend()
        return

    if temperature.temperature_trend == -1\
            and temperature.temperature_trend_count >= 10\
            and temperature.get_latest_temperature() < temperature.normal_temperature - 5:
        send_alert("Temperature goes too cold " + str(temperature.get_latest_temperature()) + u"℃")
        temperature.reset_trend()
        return


def signal_handler(signal, frame):
    print ('You pressed Ctrl+C!')
    # timeout.cancel()
    # # stopTimer.cancel()
    # GPIO.cleanup()
    # # Disconnect the device from the cloud
    # device_client.disconnect()
    stop_and_exit()


def stop_and_exit():
    stop_handler()
    timeout.cancel()
    # stopTimer.cancel()
    GPIO.cleanup()
    device_client.disconnect()
    stop_alert_client()
    sys.exit()

if __name__ == "__main__":
    stopTime = 0
    count = 0
    interval = 1
    config_file_path = "device.conf"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:c:i:f:", ["help", "time=", "count=", "interval=", "file="])
        # if len(opts) == 0:
        #     print("Input argument missing")
        #     GPIO.cleanup()
        #     usage()
        #     sys.exit()
        for o, a in opts:
            if o in ("-t", "--time"):
                stopTime = float(a)
                if stopTime > 5.0:
                    print(
                            "INFO: Motor will run for about %s minutes" % stopTime
                          )
            elif o in ("-c", "--count"):
                count = int(a)
                if count > 0:
                    print("INFO: Motor will stop at %s times publish" % count)
            elif o in ("-i", "--interval"):
                interval = int(a)
                if interval > 0:
                    print("INFO: Motor will check and publish data every %s seconds" % interval)
            elif o in ("-f", "--file"):
                config_file_path = a
            elif o in ("-h", "--help"):
                GPIO.cleanup()
                usage()
                sys.exit()
            else:
                print("unhandled option" + o)

    except getopt.GetoptError as err:
        print(str(err))
        GPIO.cleanup()
        usage()
        sys.exit(2)

    # Initialize the WeXin alert client, and keeps running
    itchat.auto_login(hotReload=True, enableCmdQR=2)
    itchat.run(blockThread=False)
    # itchat.run()

    # Initialize the device client.
    try:
        device_file = config_file_path
        device_options = ibmiotf.device.ParseConfigFile(device_file)
        device_client = ibmiotf.device.Client(device_options)
    except Exception as e:
            print("Caught exception connecting device: %s" % str(e))
            GPIO.cleanup()
            sys.exit()

    temperature = Temperature(normal_temperature=20, auto_adjust=True, accuracy=0.1)

    device_client.connect()
    device_client.commandCallback = my_command_callback

    timeout = SetInterval(publish, interval, count, stopTime)
    start_handler()

    # if stopTime > 0:
    #     print ("Motor will stop in %s min" % str(stopTime))
    #     stopTimer = threading.Timer(stopTime*60.0, stop_and_exit)
    #     stopTimer.start()

    signal.signal(signal.SIGINT, signal_handler)
    print ('Press Ctrl+C to exit')

    # global running_status
    while running_status:
        time.sleep(1)

