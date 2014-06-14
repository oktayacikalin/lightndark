#!/usr/bin/env python3
#
# Tray icon and configuration GUI.
#
# @author    Oktay Acikalin <oktay.acikalin@gmail.com>
# @copyright Oktay Acikalin
# @license   MIT (LICENSE.txt)

from gi.repository import Gtk, Gio, GLib
import sys
import configparser
from os.path import join, dirname
import signal
import logging


from update import (
    get_interface,
    get_sensor_value,
    get_display_backlight_value,
    calc_shifted_backlight_percent,
    calc_display_temperature,
    calc_display_rgb,
    calc_display_gamma_modification,
    calc_keyboard_backlight_percent,
    modify_display_backlight_value,
    modify_display_gamma_value,
    modify_keyboard_backlight_value
)


LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)-15s] [%(module)s.%(funcName)s.%(levelname)s] %(message)s'

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger('gui')


def log(message):
    logger.info(message)


class Window(Gtk.ApplicationWindow):

    def __init__(self, application):
        super(Window, self).__init__(application=application)
        self.set_title('dummy window')


class Application(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self, application_id='de.lightndark',
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)
        config_filepath = join(dirname(__file__), 'config.ini')
        config = configparser.ConfigParser()
        config.readfp(open(config_filepath))
        self.iface = get_interface()
        self.config = config
        self.manage_dsp_backlight = True
        self.manage_dsp_temperature = True
        self.manage_dsp_gamma = True
        self.manage_kbd_backlight = True
        self.last_display_backlight_percent = get_display_backlight_value(self.iface)
        self.last_display_temperature = None
        self.last_display_gamma_value = None
        self.last_keyboard_backlight_percent = None

    def show_main_window(self, widget, data=None):
        self.window.show_all()

    def tray_icon_quit(self, widget, data=None):
        self.quit()

    def tray_icon_menu(self, widget, button, time, data=None):
        menu = Gtk.Menu()

        menu_item_show_main_window = Gtk.MenuItem('Settings')
        menu_item_quit = Gtk.MenuItem('Quit')

        menu_item_show_main_window.connect('activate', self.show_main_window)
        menu_item_quit.connect('activate', self.tray_icon_quit)

        menu.append(menu_item_show_main_window)
        menu.append(menu_item_quit)

        menu.show_all()
        self.menu = menu

        icon = self.tray_icon
        menu.popup(None, None,
                   lambda w, x: icon.position_menu(menu, icon),
                   icon, 3, time)

    def update_all(self):
        # log('update_all')

        # TODO detect if display is absent or again present. When display is
        #      available again, management has to be reenabled.
        display_backlight_percent = get_display_backlight_value(self.iface)
        if self.manage_dsp_backlight:
            if self.last_display_backlight_percent != display_backlight_percent:
                log('Halting management of display backlight.')
                self.manage_dsp_backlight = False
        else:
            if self.last_display_backlight_percent is None or (
                    self.last_display_backlight_percent > display_backlight_percent - 10 and
                    self.last_display_backlight_percent < display_backlight_percent + 10):
                log('Resuming management of display backlight.')
                self.manage_dsp_backlight = True
                self.last_display_backlight_percent = None

        config = self.config
        if self.manage_dsp_backlight:
            # Modify brightness of display.
            sensor_value, sensor_value_percent = get_sensor_value(config)
            # log('Sensor value = %s; in percent = %s' % (sensor_value, sensor_value_percent))
            display_backlight_percent = calc_shifted_backlight_percent(config, sensor_value_percent)
            if self.last_display_backlight_percent != display_backlight_percent:
                # diff = display_backlight_percent - self.last_display_backlight_percent
                # diff *= 0.1
                # diff = int(diff * 100) / 100
                # log(diff)
                # if diff:
                #     display_backlight_percent = self.last_display_backlight_percent + diff
                self.last_display_backlight_percent = display_backlight_percent
                log('Ambient light sensor value: %d (%d%%)' % (sensor_value, sensor_value_percent))
                log('Calculated display backlight: %d%%' % display_backlight_percent)
                modify_display_backlight_value(self.iface, display_backlight_percent)
                # GLib.timeout_add(50, self.update_all)
        # else:
        #     if self.last_display_backlight_percent != display_backlight_percent:
        #         # self.last_display_backlight_percent = display_backlight_percent
        #         log('Current display backlight: %d%%' % display_backlight_percent)

        if self.manage_dsp_temperature:
            display_temperature = calc_display_temperature(config, display_backlight_percent)
            if self.last_display_temperature != display_temperature:
                self.last_display_temperature = display_temperature
                # Modify temperature of display.
                log('Calculated display temperature: %d' % display_temperature)
            rgb = calc_display_rgb(config, display_temperature)
        else:
            rgb = (1.0, 1.0, 1.0)

        if self.manage_dsp_gamma:
            # Apply gamma modification.
            rgb = calc_display_gamma_modification(config, rgb)

        gamma = '%f:%f:%f' % rgb
        if self.last_display_gamma_value != gamma:
            self.last_display_gamma_value = gamma
            # Modify gamma value.
            log('Calculated display gamma: %s' % gamma)
            modify_display_gamma_value(gamma)

        if self.manage_kbd_backlight:
            keyboard_backlight_percent = calc_keyboard_backlight_percent(display_backlight_percent)
            if self.last_keyboard_backlight_percent != keyboard_backlight_percent:
                self.last_keyboard_backlight_percent = keyboard_backlight_percent
                # Modify brightness of keyboard.
                log('Calculated keyboard backlight: %d%%' % keyboard_backlight_percent)
                import time
                modify_keyboard_backlight_value(self.iface, 0)
                time.sleep(0.1)
                modify_keyboard_backlight_value(self.iface, 100)
                time.sleep(0.1)
                modify_keyboard_backlight_value(self.iface, keyboard_backlight_percent)

    def update_all_tick(self):
        # log('update_tick')
        try:
            self.update_all()
        except Exception as exception:
            log(exception)
        # Makes GLib.timeout_add* repeatedly call this method.
        return True

    def tray_icon_activated(self, widget, data=None):
        self.manage_dsp_backlight = False
        self.last_display_backlight_percent = None
        self.update_all()

    def on_activate(self, data=None):
        window = Window(application=self)
        self.add_window(window)
        self.window = window

        icon = Gtk.StatusIcon()
        icon.set_from_stock(Gtk.STOCK_ABOUT)
        icon.connect('activate', self.tray_icon_activated)
        icon.connect('popup_menu', self.tray_icon_menu)
        icon.set_visible(True)
        self.tray_icon = icon

        GLib.timeout_add_seconds(1, self.update_all_tick)

    def on_deactivate(self):
        self.tray_icon.set_visible(False)
        del self.tray_icon


if __name__ == "__main__":
    # Install keyboard interrupt handler. (http://stackoverflow.com/a/16486080)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # Create application.
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
