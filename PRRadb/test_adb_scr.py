import subprocess
import base64

def take_screenshot_safe(filename="screenshot.png"):
    try:
        # 在设备上截图并用 base64 编码输出（避免二进制传输问题）
        result = subprocess.run(
            ["adb", "shell", "screencap -p | base64"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # 此时输出是文本（base64 字符串）
            check=True
        )

        # 获取 base64 字符串（可能包含换行，需去除）
        b64_str = result.stdout.strip()

        # 解码为原始 PNG 二进制数据
        png_data = base64.b64decode(b64_str)

        # 保存文件
        with open(filename, "wb") as f:
            f.write(png_data)

        print(f"✅ 截图已成功保存为 {filename}")

    except subprocess.CalledProcessError as e:
        print("❌ ADB 命令失败:", e.stderr)
    except Exception as e:
        print("❌ 错误:", str(e))
        print("可能原因：设备未连接、未开启 USB 调试、adb 未安装")

if __name__ == "__main__":
    take_screenshot_safe("safe_screenshot.png")