import base64
import os
import subprocess
import time

def take_screenshot_safe(filename="screenshot.png"):
    scr_dir = "ADBSCR"
    os.makedirs(scr_dir, exist_ok=True)
    full_path = os.path.join(scr_dir, filename)
    try:
        result = subprocess.run(
            ["adb", "shell", "screencap -p | base64"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        b64_str = result.stdout.strip()
        png_data = base64.b64decode(b64_str)
        with open(full_path, "wb") as f:
            f.write(png_data)
        print(f"✅ 截图已成功保存为 {full_path}")
    except subprocess.CalledProcessError as e:
        print("❌ ADB 命令失败:", e.stderr)
    except Exception as e:
        print("❌ 错误:", str(e))
        print("可能原因：设备未连接、未开启 USB 调试、adb 未安装")

def get_current_package():
    """仅使用 dumpsys window displays 获取前台包名（兼容 Android 8~14）"""
    try:
        result = subprocess.run(
            ["adb", "shell", "dumpsys window displays | grep -E 'mCurrentFocus|mFocusedApp'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        output = result.stdout.strip()
        if output:
            for line in output.splitlines():
                if "mCurrentFocus=" in line or "mFocusedApp=" in line:
                    # 示例: mCurrentFocus=Window{... com.example.app/.MainActivity}
                    parts = line.split()
                    if parts:
                        last_part = parts[-1]  # 通常是 "com.example.app/.Activity"
                        if "/" in last_part and last_part.count(".") >= 1:
                            package = last_part.split("/")[0]
                            if package and "." in package:
                                return package
        return None
    except Exception as e:
        print("❌ 获取前台包名异常:", str(e))
        return None

def launch_app(package_name, activity_name=None):
    """启动指定应用"""
    try:
        if activity_name:
            cmd = ["adb", "shell", "am", "start", "-n", f"{package_name}/{activity_name}"]
        else:
            cmd = ["adb", "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ 已启动应用: {package_name}")
    except subprocess.CalledProcessError as e:
        print("❌ 启动应用失败:", e.stderr)
    except Exception as e:
        print("❌ 启动错误:", str(e))

def ensure_app_in_foreground(target_package, activity_name=None):
    """确保目标应用在前台，否则启动它"""
    current = get_current_package()
    print(f"当前前台应用包名: {current}")

    if current != target_package:
        print(f"⚠️ 当前不在 {target_package} 中，正在启动...")
        launch_app(target_package, activity_name)
        time.sleep(2)  # 等待应用启动
    else:
        print(f"✅ 已在 {target_package} 中")

# 示例：确保在微信中
if __name__ == "__main__":
    TARGET_PACKAGE = "com.tunergames.paradigmchina"  # 替换为你需要的应用包名

    ensure_app_in_foreground(TARGET_PACKAGE)

    # 截图
    take_screenshot_safe("screenshot_in_app.png")