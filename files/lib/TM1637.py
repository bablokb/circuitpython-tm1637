# -----------------------------------------------------------------------------
# CircuitPython library for TM1637 quad/hex 7-segment LED displays
#
# This core of the code is from a micropython implementation from:
# https://github.com/mcauser/micropython-tm1637
#
# Adapted to CircuitPython with minor modifications by Bernhard Bablok
#
# Website: https://github.com/bablokb/circuitpython-tm1637
#
# -----------------------------------------------------------------------------

"""
MIT License
Copyright (c) 2016 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import digitalio
import time

class TM1637(object):
  """Library for quad 7-segment LED modules based on the TM1637 LED driver."""

  _CMD1   = 0x40      # data command
  _CMD2   = 0xC0      # address command
  _CMD3   = 0x80      # display control command
  _DSP_ON = 0x08      # display on
  _DELAY  = 0.000010  # 10us delay between clk/dio pulses
  _MSB    = 0x80      # decimal point or colon depending on your display

  # 0-9, a-z, blank, dash, star
  _SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')

  def __init__(self, clk, dio, brightness=7):
    if not 0 <= brightness <= 7:
      raise ValueError("Brightness out of range")
    self._brightness = brightness

    self._clk = digitalio.DigitalInOut(clk)
    self._clk.direction = digitalio.Direction.OUTPUT
    self._clk.value     = 0
    self._dio = digitalio.DigitalInOut(dio)
    self._dio.direction = digitalio.Direction.OUTPUT
    self._dio.value     = 0
    time.sleep(TM1637._DELAY)
    self._write_data_cmd()
    self._write_dsp_ctrl()

  def _start(self):
    self._dio.value = 0
    time.sleep(TM1637._DELAY)
    self._clk.value = 0
    time.sleep(TM1637._DELAY)

  def _stop(self):
    self._dio.value = 0
    time.sleep(TM1637._DELAY)
    self._clk.value = 1
    time.sleep(TM1637._DELAY)
    self._dio.value = 1

  def _write_data_cmd(self):
    # automatic address increment, normal mode
    self._start()
    self._write_byte(TM1637._CMD1)
    self._stop()

  def _write_dsp_ctrl(self):
    # display on, set brightness
    self._start()
    self._write_byte(TM1637._CMD3 | TM1637._DSP_ON | self._brightness)
    self._stop()

  def _write_byte(self, b):
    for i in range(8):
      self._dio.value = (b >> i) & 1
      time.sleep(TM1637._DELAY)
      self._clk.value = 1
      time.sleep(TM1637._DELAY)
      self._clk.value = 0
      time.sleep(TM1637._DELAY)
    self._clk.value = 0
    time.sleep(TM1637._DELAY)
    self._clk.value = 1
    time.sleep(TM1637._DELAY)
    self._clk.value = 0
    time.sleep(TM1637._DELAY)

  def brightness(self, val=None):
    """Set the display brightness 0-7."""
    # brightness 0 = 1/16th pulse width
    # brightness 7 = 14/16th pulse width
    if val is None:
      return self._brightness
    if not 0 <= val <= 7:
      raise ValueError("Brightness out of range")

    self._brightness = val
    self._write_data_cmd()
    self._write_dsp_ctrl()

  def write(self, segments, pos=0):
    """Display up to 6 segments moving right from a given position.
    The MSB in the 2nd segment controls the colon between the 2nd
    and 3rd segments."""
    if not 0 <= pos <= 5:
      raise ValueError("Position out of range")
    self._write_data_cmd()
    self._start()

    self._write_byte(TM1637._CMD2 | pos)
    for seg in segments:
      self._write_byte(seg)
    self._stop()
    self._write_dsp_ctrl()

  def encode_digit(self, digit):
    """Convert a character 0-9, a-f to a segment."""
    return TM1637._SEGMENTS[digit & 0x0f]

  def encode_string(self, string):
    """Convert an up to 4 character length string containing 0-9, a-z,
    space, dash, star to an array of segments, matching the length of the
    source string."""
    segments = bytearray(len(string))
    for i in range(len(string)):
      segments[i] = self.encode_char(string[i])
    return segments

  def encode_char(self, char):
    """Convert a character 0-9, a-z, space, dash or star to a segment."""
    o = ord(char)
    if o == 32:
      return TM1637._SEGMENTS[36] # space
    if o == 42:
      return TM1637._SEGMENTS[38] # star/degrees
    if o == 45:
      return TM1637._SEGMENTS[37] # dash
    if o >= 65 and o <= 90:
      return TM1637._SEGMENTS[o-55] # uppercase A-Z
    if o >= 97 and o <= 122:
      return TM1637._SEGMENTS[o-87] # lowercase a-z
    if o >= 48 and o <= 57:
      return TM1637._SEGMENTS[o-48] # 0-9
    raise ValueError("Character out of range: {:d} '{:s}'".format(o, chr(o)))

  def hex(self, val):
    """Display a hex value 0x0000 through 0xffff, right aligned."""
    string = '{:04x}'.format(val & 0xffff)
    self.write(self.encode_string(string))

  def number(self, num):
    """Display a numeric value -999 through 9999, right aligned."""
    # limit to range -999 to 9999
    num = max(-999, min(num, 9999))
    string = '{0: >4d}'.format(num)
    self.write(self.encode_string(string))

  def numbers(self, num1, num2, colon=True):
    """Display two numeric values -9 through 99, with leading zeros
    and separated by a colon."""
    num1 = max(-9, min(num1, 99))
    num2 = max(-9, min(num2, 99))
    segments = self.encode_string('{0:0>2d}{1:0>2d}'.format(num1, num2))
    if colon:
      segments[1] |= 0x80 # colon on
    self.write(segments)

  def temperature(self, num):
    if num < -9:
      self.show('lo') # low
    elif num > 99:
      self.show('hi') # high
    else:
      string = '{0: >2d}'.format(num)
      self.write(self.encode_string(string))
    self.write([TM1637._SEGMENTS[38], TM1637._SEGMENTS[12]], 2) # degrees C

  def show(self, string, colon=False):
    segments = self.encode_string(string)
    if len(segments) > 1 and colon:
      segments[1] |= 128
    self.write(segments[:4])

  def scroll(self, string, delay=0.25):
    segments = string if isinstance(string, list) else self.encode_string(string)
    data = [0] * 8
    data[4:0] = list(segments)
    for i in range(len(segments) + 5):
      self.write(data[0+i:4+i])
      time.sleep(delay)

# ---------------------------------------------------------------------------

class TM1637Decimal(TM1637):
  """Library for quad 7-segment LED modules based on the TM1637 LED driver.

  This class is meant to be used with decimal display modules (modules
  that have a decimal point after each 7-segment LED).
  """

  def encode_string(self, string):
    """Convert a string to LED segments.

    Convert an up to 4 character length string containing 0-9, a-z,
    space, dash, star and '.' to an array of segments, matching the length of
    the source string."""
    segments = bytearray(len(string.replace('.','')))
    j = 0
    for i in range(len(string)):
      if string[i] == '.' and j > 0:
        segments[j-1] |= TM1637._MSB
        continue
      segments[j] = self.encode_char(string[i])
      j += 1
    return segments
  
# ---------------------------------------------------------------------------

class TM1637SixDigit(TM1637):
  """
  Library for six digit, 7-segment LED modules based on the TM1637 LED driver.
  Steve Anderson (https://github.com/IrregularShed), 2023-05-22

  Six digit TM1637 displays have a pair of three digit modules with decimal points, and
  the logical order of each is reversed (to display '123456' you have to send '321654')
  """

  def digit_to_logic(self, num):
    """Convert a digit position to a logical position"""
    return (num // 3) * 3 + (2 - (num % 3))

  def encode_string(self, string):
    """Convert a string to LED segments.

    Convert a string containing 0-9, a-z, space, dash, star and '.' to an array of
    segments, matching the length of the source string."""
    segments = bytearray(len(string.replace('.', '')) + 3)
   
    j = 0
    for i in range(len(string)):
      if string[i] == '.' and j > 0:
        segments[self.digit_to_logic(j - 1)] |= TM1637._MSB
        continue
   
      segments[self.digit_to_logic(j)] = self.encode_char(string[i])
      j += 1
    return segments

  def write(self, segments, pos = 0):
    # override to ensure only 6 segments are passed to prevent things going screwy
    super().write(segments[:6], pos)

  def hex(self, val):
    """Display a hex value from 0x000000 to 0xffffff, right aligned."""
    string = '{:06x}'.format(val & 0xffffff)
    self.write(self.encode_string(string[:6]))

  def number(self, num):
    """Display an integer value from -99999 to 999999, right aligned."""
    num=max(-99999, min(num, 999999))
    string='{0: >6d}'.format(num)
    self.write(self.encode_string(string))

  def numbers(self, num1, num2, seperator = True):
    """Display two integer values of -99 to 999, with leading zeros
    and optionally separated by a decimal point."""
    num1 = max(-99, min(num1, 999))
    num2 = max(-99, min(num2, 999))
    segments = self.encode_string('{0:0>3d}{1:0>3d}'.format(num1, num2))
    if seperator:
      segments[0] |= TM1637._MSB # decimal point on third digit
    self.write(segments)

  def temperature(self, num):
    """Basic integer temperature display."""
    if num < -999:
      self.show('low') # low
    elif num > 9999:
      self.show('high') # high
    else:
      string = '{0: >4d}*C'.format(num) # degrees C
      self.write(self.encode_string(string))

  def show(self, string):
    # override to avoid four character limit
    segments = self.encode_string(string)
    self.write(segments)

  def scroll(self, string, delay = 0.25):
    # override because the digit mapping prevents the original method
    for i in range(len(string) + 1):
      self.show(string[i:])
      time.sleep(delay)
