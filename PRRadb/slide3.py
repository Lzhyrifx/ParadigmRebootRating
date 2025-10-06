import uiautomator2 as u2
import time

d = u2.connect()
w = d.info['displayWidth']
x = w * 0.5
start_y = 1800
end_y = 1100  # ← 关键参数，切3首；若不够就改成 500

def fast_swipe_up():
    d.touch.down(x, start_y)
    time.sleep(0.01)
    for i in range(1, 16):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.6)
    d.touch.up(x, end_y)

fast_swipe_up()
fast_swipe_up()