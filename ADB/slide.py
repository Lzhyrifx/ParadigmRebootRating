import uiautomator2 as u2
import time
import os


d = u2.connect()


def slide(d):
    w = d.info['displayWidth']
    x = w * 0.5
    start_y = 1800
    end_y = 700

    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.2)
    d.touch.up(x, end_y)


    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.6)

for i in range(5):
    slide(d)