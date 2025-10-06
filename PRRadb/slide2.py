import uiautomator2 as u2
import time

d = u2.connect()

# 起点和终点
start_x, start_y = 635, 1828
end_x, end_y = 1695, 58

# 1. 按下
d.touch.down(start_x, start_y)
time.sleep(0.1)  # 确保按下被识别（可模拟“长按”起点）

# 2. 缓慢移动到目标位置（插入多个中间点，避免跳跃）
steps = 100
for i in range(1, steps + 1):
    x = start_x + (end_x - start_x) * i / steps
    y = start_y + (end_y - start_y) * i / steps
    d.touch.move(x, y)
    time.sleep(0.001)  # 每步间隔 10ms，总移动时间约 0.3s

# 3. 到达目标后，停留一段时间（比如 1 秒）
time.sleep(0.5)

# 4. 松手
d.touch.up(end_x, end_y)