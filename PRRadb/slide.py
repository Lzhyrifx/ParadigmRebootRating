import os
import time

# 发送按下事件
os.system("adb shell input touchscreen down 894 1369")
time.sleep(0.1)

# 分步滑动
steps = 50
for i in range(1, steps+1):
    curr_x = 894 + (913 - 894) * i / steps
    curr_y = 1369 + (611 - 1369) * i / steps
    os.system(f"adb shell input touchscreen move {curr_x} {curr_y}")
    time.sleep(0.01)

# 停留后松开
time.sleep(0.5)
os.system("adb shell input touchscreen up")