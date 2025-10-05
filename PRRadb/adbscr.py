import uiautomator2 as u2
import time
import os


song_coords = [
    (1172, 579),  # 第一首
    (1025, 833),  # 第二首
    (881, 1081),  # 第三首
    (744, 1326),  # 第四首
    (603, 1577),  # 第五首
    (464, 1818),  # 第六首
]

# 截图保存路径（保持原目录）
screenshot_dir = "Temp/"



# ------------------- 工具函数（uiautomator2 版） -------------------
def init_device():
    """初始化设备连接（单设备自动识别，多设备需指定设备ID）"""
    try:
        # 自动连接当前唯一USB设备（多设备需用 u2.connect("设备ID")，设备ID通过 adb devices 获取）
        d = u2.connect()

        print(f"✅ 设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d
    except Exception as e:
        print(f"❌ 设备连接失败：{str(e)}")
        print("可能原因：1. USB调试未开启 2. 未授权电脑 3. 设备未连接")
        exit(1)


def tap_coordinate(d, x, y):
    """基于 uiautomator2 模拟坐标点击（比ADB更稳定）"""
    try:
        # click 方法自带坐标校验，避免无效点击
        d.click(x, y)

        print(f"🔘 已点击坐标：({x}, {y})")
    except Exception as e:
        print(f"⚠️ 点击失败：{str(e)}")


def take_screenshot(d, song_name):
    """uiautomator2 截图（直接保存本地，无需设备中间文件）"""
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        # 直接截图并保存到本地路径（支持PNG/JPG）
        success = d.screenshot(local_path)
        if success and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            print(f"📸 已保存截图：{local_path}")
        else:
            print(f"⚠️ 截图无效：{local_path}（文件为空或未生成）")
    except Exception as e:
        print(f"❌ 截图失败：{str(e)}")


# ------------------- 主逻辑（流程与原脚本一致） -------------------
if __name__ == "__main__":
    # 1. 初始化设备和目录
    d = init_device()
    os.makedirs(screenshot_dir, exist_ok=True)  # 确保保存目录存在

    # 2. 执行核心流程
    start_time = time.time()
    for idx, (x, y) in enumerate(song_coords):
        song_name = f"song_{idx + 1}"
        print(f"\n===== 处理歌曲：{song_name} =====")

        tap_coordinate(d, x, y)  # 点击歌曲
        take_screenshot(d, song_name)  # 截图

    # 3. 统计耗时
    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / len(song_coords):.2f} 秒")
    print("=" * 50)
