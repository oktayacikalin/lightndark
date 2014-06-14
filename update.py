#!/usr/bin/env python3
#
# Shell script for updating everything.
#
# @author    Oktay Acikalin <oktay.acikalin@gmail.com>
# @copyright Oktay Acikalin
# @license   MIT (LICENSE.txt)

import sys
import configparser
import subprocess
import csv
from os.path import join, dirname
from math import floor, ceil, cos, pi


TEMPERATURE_TABLE_FILEPATH = join(dirname(__file__), 'thirdparty', 'bbr_color.txt')


def get_interface():
    # You must initialize the gobject/dbus support for threading
    # before doing anything.
    from gi.repository import GObject
    GObject.threads_init()

    from dbus import glib
    glib.init_threads()

    # Create a session bus.
    import dbus
    bus = dbus.SessionBus()

    # Create an object that will proxy for a particular remote object.
    remote_object = bus.get_object(
        'org.gnome.SettingsDaemon',
        '/org/gnome/SettingsDaemon/Power'
    )

    # Get a particular interface
    iface = dbus.Interface(remote_object, 'org.freedesktop.DBus.Properties')

    return iface


def cosine_interpolate(y1, y2, mul):
    mul2 = (1 - cos(mul * pi)) / 2
    return y1 * (1 - mul2) + y2 * mul2


def get_sensor_value(config):
    sensor_acpi_device = config.get('sensor', 'acpi_device')
    value = int(open(sensor_acpi_device).read())
    min_value = config.getint('sensor', 'min')
    max_value = config.getint('sensor', 'max')
    percent = 100.0 / max_value * max(min_value, value)
    percent = min(100, max(0, percent))
    return value, percent


def get_display_temperature_table(config):
    cmf_value = config.get('dsp.temperature', 'cmf')
    keys = 'temperature,_,CMF,x,y,P,R,G,B,r,g,b,#rgb'.split(',')
    with open(TEMPERATURE_TABLE_FILEPATH, 'r') as csvfile:
        table = dict(
            (int(row[0]), dict(zip(keys, row)))
            for row in csv.reader(csvfile, delimiter=' ', skipinitialspace=True)
            if row[0] != '#' and row[2] == cmf_value
        )
    return table


def get_display_backlight_value(iface):
    return iface.Get('org.gnome.SettingsDaemon.Power.Screen', 'Brightness')


def calc_shifted_backlight_percent(config, percent):
    # print(percent)
    below = floor(percent / 10.0) * 10
    above = ceil(percent / 10.0) * 10
    # print((below, above))
    mul = (above - below) / 100.0 * (percent - below)
    # print(mul)
    below = config.getint('dsp.backlight', 'shift.%d' % below)
    above = config.getint('dsp.backlight', 'shift.%d' % above)
    # print((below, above))
    return int(cosine_interpolate(below, above, mul))


def calc_display_temperature(config, brightness):
    temp_min_value = config.getint('dsp.temperature', 'min')
    temp_max_value = config.getint('dsp.temperature', 'max')
    diff = temp_max_value - temp_min_value
    return temp_min_value + (diff / 100 * brightness)


def calc_display_rgb(config, value):
    temperature_table = get_display_temperature_table(config)
    temperature_data = temperature_table.get(
        value,  # exact match
        temperature_table.get(
            int(value / 100) * 100,  # near by match
            dict(R=1.0, G=1.0, B=1.0))  # no match found
    )
    # print(temperature_data)
    rgb = tuple(map(
        float,
        (temperature_data['R'],
         temperature_data['G'],
         temperature_data['B'])
    ))
    # print(rgb)
    return rgb


def calc_display_gamma_modification(config, rgb):
    mod_map = map(float, config.get('dsp.gamma', 'modification').split(','))
    rgb = tuple(rgb[pos] * mod for pos, mod in enumerate(mod_map))
    return rgb


def calc_keyboard_backlight_percent(display_backlight_percent):
    return int(min(100, max(0, 100 - display_backlight_percent)))


def modify_display_backlight_value(iface, display_backlight_percent):
    iface.Set('org.gnome.SettingsDaemon.Power.Screen', 'Brightness', display_backlight_percent)


def modify_display_gamma_value(gamma):
    subprocess.call(['xrandr', '--output', 'LVDS1', '--gamma', gamma])


def modify_keyboard_backlight_value(iface, percent):
    iface.Set('org.gnome.SettingsDaemon.Power.Keyboard', 'Brightness', percent)


def main():
    config = configparser.ConfigParser()
    config.readfp(open(sys.argv[1]))

    iface = get_interface()

    if '--display-brightness' in sys.argv or '-b' in sys.argv:
        # Modify brightness of display.
        sensor_value, sensor_value_percent = get_sensor_value(config)
        display_backlight_percent = calc_shifted_backlight_percent(config, sensor_value_percent)
        print('Ambient light sensor value: %d (%d%%)' % (sensor_value, sensor_value_percent))
        print('Calculated display backlight: %d%%' % display_backlight_percent)
        modify_display_backlight_value(iface, display_backlight_percent)
    else:
        display_backlight_percent = get_display_backlight_value(iface)
        print('Current display backlight: %d%%' % display_backlight_percent)

    if '--display-temperature' in sys.argv or '-t' in sys.argv:
        # Modify temperature of display.
        display_temperature = calc_display_temperature(config, display_backlight_percent)
        print('Calculated display temperature: %d' % display_temperature)
        rgb = calc_display_rgb(config, display_temperature)
    else:
        rgb = (1.0, 1.0, 1.0)

    if '--display-gamma' in sys.argv or '-g' in sys.argv:
        rgb = calc_display_gamma_modification(config, rgb)

    gamma = '%f:%f:%f' % rgb
    print('Calculated display gamma: %s' % gamma)
    modify_display_gamma_value(gamma)

    if '--keyboard-backlight' in sys.argv or '-k' in sys.argv:
        # Modify brightness of keyboard.
        keyboard_backlight_percent = calc_keyboard_backlight_percent(display_backlight_percent)
        print('Calculated keyboard backlight: %d%%' % keyboard_backlight_percent)
        # First initiate a workaround for lazy keyboard backlight logic.
        modify_keyboard_backlight_value(iface, 50)
        modify_keyboard_backlight_value(iface, 0)
        # Now set correct value.
        modify_keyboard_backlight_value(iface, keyboard_backlight_percent)


if __name__ == '__main__':
    main()
