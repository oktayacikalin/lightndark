# Light'n'Dark
A desktop tool which **monitors your ambient light sensor (ALS) to always calculate the optimal display backlight, color temperature and keyboard backlight for your current environment**. The goal is to reduce strain on your eyes while working in several different, especially darker environments.

## What it "fixes"
* The sun shines outside, but you prefer a rather dimmed room where strong backlight and cold colors will hurt your eyes and concentration.
* It's 3 a.m., but your room is properly illuminated and a lack of backlight will hurt your eyes and concentration.

And what if you just don't need a specific feature? Turn it off.

## Features
* Monitor the actual ambient light sensor instead of just betting on the usual day-night-cycle.
* Adapt display backlight using a customizable ramp. The ramp is counted in 10% steps. Intermediate values get interpolated using a cosine algo.
* Display backlight can be manually overridden, the rest will adapt automatically.
* Adapt display gamma (amount of red color) according to calculated backlight value.
* Alter display gamma (rgb) for overbright displays. This can also shift your overly blue or green display a bit into a neutral colorspace.
* Adapt keyboard backlight according to the calculated display backlight value.
* Uses the D-Bus interface for communicating with your Gnome desktop. (no admin rights necessary)

## Requirements
* Python 3
* Installed als.ko kernel module (see thirdparty/als)
* Gnome desktop environment (tested with Gnome Shell)

## Installation
TODO

## Configuration
All recommendations below are based on a 400 nit display of a Samsung ATIV Book 9. If your display is darker or brighter you should start by altering the sensor.max value first.

It would be really nice if you would send me your config.ini so that others don't have to tinker around too much. Please also spent some words on your usual workplace scenario (e.g. indoors or outdoors, with or without lights, direct or indirect lights, warm or cold lights, bright or dark room etc.).

## Variables of the config.ini
* `sensor.min` Should be 0. Higher values will prevent from detecting pitch black.
* `sensor.max` Should be 500, if you normally get 300 indoors and 3230 outdoors without direct sun light.
* `sensor.acpi_device` Full path to the ALS kernel module ALI API.
* `dsp.backlight.shift.*` Backlight ramp. Left are measured values, right are wanted values. You can alter this to your liking. I prefer pitch black, a plateau for 50, one for 80 and finally full backlight. Values on the left have to be in steps of 10 percent and are mandatory. All values have to be in the range from 0 to 100 percent. Values inbetween get automatically calculated using a smooth interpolation algo.
* `dsp.temperature.min` Minimum value in Kelvin. I.e. 4500 is not too red but warm.
* `dsp.temperature.max` Maximum value in Kelvin. I.e. 6500 is the normal color temperature.
* `dsp.temperature.cmf` Either CIE 1931 2 degree CMFs with Judd Vos corrections or CIE 1964 10 degree CMFs. See thirdparty/bbr_color.txt for details.
* `dsp.gamma.modification` Relative gamma modificator which the display color will be calculated against. Use this to fix overbright or false colored (too red, too green, too blue) displays. E.g. 0.9,0.9,0.9 slightly darkens the calculated display colors. This might also let overbright displays look more sharp and reduce bluriness. 1.0,0.9,0.9 would reduce green and blue values and make the display look more warm. You get the idea...

## References / thanks go to:
* ALS kernel module: https://github.com/victorenator/als.git
* Color temperature: http://www.vendian.org/mncharity/dir3/blackbody/
* Cosine algo: http://paulbourke.net/miscellaneous/interpolation/
* Standard ALS spec: http://msdn.microsoft.com/en-us/library/windows/hardware/Dn613947(v=vs.85).aspx
* [RedShift](http://jonls.dk/redshift/), [f.lux](https://justgetflux.com/) and others for the ideas of altering display backlight and gamma.
