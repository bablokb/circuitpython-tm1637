import time
import TM1637
import board

if __name__ == "__main__":
  CLK = board.D6
  DIO = board.D13
  display = TM1637.TM1637(CLK, DIO)
  display.hex(0xbeef)
  time.sleep(5)
  while True:
    t = time.localtime()
    display.numbers(t.tm_hour,t.tm_min)
    time.sleep(60-(t.tm_sec%60))
