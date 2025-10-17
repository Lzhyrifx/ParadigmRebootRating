import os
import cv2
import numpy as np
from ADB.function import init_device

# ========== 配置 ==========
temp_dir = "Temp"
point1 = (1437, 739)
point2 = (1615, 437)
reference_point = (1526, 588)
y_threshold = 30

# ========== 截图函数 ==========
def temp_screenshot(d, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    local_path = os.path.join(temp_dir, "Temp.png")
    try:
        d.screenshot(local_path)
        if os.path.exists(local_path):
            print(f"已保存截图：{local_path}")
            return local_path
        else:
            print(f"截图文件未生成：{local_path}")
            return None
    except Exception as e:
        print(f"截图失败：{str(e)}")
        return None

# ========== 滑动函数 ==========
def re_slide(d, start_xy, end_xy, steps=10):
    sx, sy = map(int, start_xy)
    ex, ey = map(int, end_xy)
    d.touch.down(sx, sy)
    for i in range(1, steps + 1):
        x = int(sx + (ex - sx) * i / steps)
        y = int(sy + (ey - sy) * i / steps)
        d.touch.move(x, y)
    d.touch.up(ex, ey)
    d.click(cx, cy)

# ========== 初始化与截图 ==========
d = init_device()
cx = d.info['displayWidth'] * 0.5
cy = d.info['displayHeight'] * 0.5
IMG_PATH = temp_screenshot(d, temp_dir)
img = cv2.imread(IMG_PATH)
if img is None:
    raise FileNotFoundError(f"无法读取图像：{IMG_PATH}")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_purple = np.array([125, 40, 40])
upper_purple = np.array([155, 255, 255])

num_samples = max(int(np.hypot(point2[0]-point1[0], point2[1]-point1[1]) / 2), 1)
xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
ys = np.linspace(point1[1], point2[1], num_samples).astype(int)

mask = cv2.inRange(hsv, lower_purple, upper_purple)
purple_indices = [i for i, (x, y) in enumerate(zip(xs, ys)) if mask[y, x] > 0]

# ========== 可视化 ==========
vis = img.copy()
cv2.line(vis, point1, point2, (0, 255, 0), 2)
song_coords = [
    (1110, 491),
    (1014, 744),
    (862, 1003),
    (728, 1230),
    (584, 1468),
    (427, 1735),
]
for x, y in song_coords:
    cv2.circle(vis, (x, y), 6, (255, 0, 255), -1)

# ========== 紫色中心检测 ==========
if purple_indices:
    # 拆分为连续段并选择最长段
    segments = np.split(purple_indices, np.where(np.diff(purple_indices) > 1)[0] + 1)
    main_segment = max(segments, key=len)
    start_i, end_i = main_segment[0], main_segment[-1]
    mid_i = (start_i + end_i) // 2
    mid_x, mid_y = int(xs[mid_i]), int(ys[mid_i])

    print(f"中心点坐标：({mid_x}, {mid_y})")
    y_distance = mid_y - reference_point[1]
    print(f"与参考点 {reference_point} 的 y 轴距离：{y_distance}")

    if abs(y_distance) > y_threshold:
        if y_distance > 0:
            print("检测到偏下")
            slide_scale = 1.5
        else:
            print("检测到偏上")
            slide_scale = 1.2

        delta_y = reference_point[1] - mid_y
        end_y = int(mid_y + delta_y * slide_scale)
        print(f"回正：从 ({mid_x}, {mid_y}) 到 ({mid_x}, {end_y})，倍率={slide_scale}")
        re_slide(d, (mid_x, mid_y), (mid_x, end_y))

    # 可视化中心点与参考点
    cv2.circle(vis, (mid_x, mid_y), 4, (0, 0, 255), -1)
    cv2.circle(vis, reference_point, 4, (255, 0, 0), -1)
    cv2.line(vis, (mid_x, mid_y), reference_point, (255, 255, 0), 1)
else:
    print("未检测到符合条件的紫色区域")

cv2.imwrite("purple_detect_result.png", vis)
print("检测结果已保存 -> purple_detect_result.png")
