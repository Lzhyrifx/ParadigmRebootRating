import cv2
import numpy as np

# ===== 配置部分 =====
IMG_PATH = "Temp/Temp.png"  # 你的图片路径
point1 = (760, 1915)
point2 = (865, 1730)
target_color = np.array([119, 82, 133])  # BGR格式
tolerance = 50

# ===== 主逻辑 =====
img = cv2.imread(IMG_PATH)
if img is None:
    raise FileNotFoundError(f"无法读取图像：{IMG_PATH}")

# 在两点之间插值取样
num_samples = int(np.hypot(point2[0]-point1[0], point2[1]-point1[1]))
xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
ys = np.linspace(point1[1], point2[1], num_samples).astype(int)

purple_indices = []
for i, (x, y) in enumerate(zip(xs, ys)):
    b, g, r = img[y, x]
    if all(abs(c1 - c2) <= tolerance for c1, c2 in zip([b, g, r], target_color)):
        purple_indices.append(i)

# 可视化
vis = img.copy()
cv2.line(vis, point1, point2, (0, 255, 0), 2)

if purple_indices:
    start_i, end_i = purple_indices[0], purple_indices[-1]
    mid_i = (start_i + end_i) // 2
    mid_x, mid_y = int(xs[mid_i]), int(ys[mid_i])
    print(f"检测到紫色段：从索引 {start_i} 到 {end_i}")
    print(f"紫色段中心点坐标：({mid_x}, {mid_y})")
    cv2.circle(vis, (mid_x, mid_y), 4, (0, 0, 255), -1)  # 红点半径变小
else:
    print("未检测到符合条件的紫色区域。")

cv2.imwrite("purple_detect_result.png", vis)
print("结果图已保存为 purple_detect_result.png")
