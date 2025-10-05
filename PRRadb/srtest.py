import time
import os
import subprocess

# 歌曲坐标（与原脚本保持一致）
song_coords = [
    (1172, 579),  # 第一首
    (1025, 833),  # 第二首
    (881, 1081),  # 第三首
    (744, 1326),  # 第四首
    (603, 1577),  # 第五首
    (464, 1818),  # 第六首
]

# 截图保存路径
screenshot_dir = "Temp/"

# MaaTouch 相关配置
MATOUCH_PACKAGE = "com.shxyke.MaaTouch"
MATOUCH_SERVICE = f"{MATOUCH_PACKAGE}/.App"


def init_device():
    """初始化设备，检查ADB连接并启动MaaTouch服务"""
    try:
        # 检查设备是否在线
        subprocess.check_output(
            ["adb", "get-state"],
            stderr=subprocess.STDOUT,
            text=True
        )

        # 启动MaaTouch服务（需要提前安装MaaTouch APK）
        subprocess.run(
            ["adb", "shell", "app_process", "/system/bin", f"{MATOUCH_SERVICE}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("✅ MaaTouch服务启动成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 设备初始化失败：{e.output}")
        print("可能原因：1. 设备未连接 2. MaaTouch未安装 3. 未授予root权限")
        return False


def send_maatouch_command(cmd):
    """通过ADB发送指令到MaaTouch"""
    try:
        # 通过ADB管道发送指令
        process = subprocess.Popen(
            ["adb", "shell", "nc", "localhost", "1111"],  # 假设MaaTouch监听1111端口
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 发送指令并提交
        process.stdin.write(f"{cmd}\nc\n")
        process.stdin.flush()
        time.sleep(0.1)  # 等待指令执行
        process.stdin.close()
        return True
    except Exception as e:
        print(f"⚠️ 指令发送失败：{str(e)}")
        return False


def tap_coordinate(x, y):
    """使用MaaTouch模拟点击坐标"""
    # MaaTouch点击指令：按下(d) -> 抬起(u)
    cmd = f"d 0 {x} {y} 1\nu 0"
    if send_maatouch_command(cmd):
        print(f"🔘 已点击坐标：({x}, {y})")
    else:
        print(f"⚠️ 点击坐标({x}, {y})失败")


def take_screenshot(song_name):
    """使用ADB截图（MaaTouch无截图功能，复用ADB原生方法）"""
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        # 先保存到设备临时目录
        device_path = f"/sdcard/{song_name}.png"
        subprocess.run(
            ["adb", "shell", "screencap", "-p", device_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # 拉取到本地
        subprocess.run(
            ["adb", "pull", device_path, local_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # 删除设备上的临时文件
        subprocess.run(["adb", "shell", "rm", device_path])
        print(f"📸 已保存截图：{local_path}")
    except Exception as e:
        print(f"❌ 截图失败：{str(e)}")


if __name__ == "__main__":
    # 1. 初始化设备和目录
    if not init_device():
        exit(1)
    os.makedirs(screenshot_dir, exist_ok=True)

    # 2. 执行核心流程
    start_time = time.time()
    for idx, (x, y) in enumerate(song_coords):
        song_name = f"song_{idx + 1}"
        print(f"\n===== 处理歌曲：{song_name} =====")

        tap_coordinate(x, y)  # 点击歌曲
        time.sleep(0.5)  # 等待界面响应
        take_screenshot(song_name)  # 截图
        time.sleep(0.5)  # 等待截图完成

    # 3. 统计耗时
    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / len(song_coords):.2f} 秒")
    print("=" * 50)