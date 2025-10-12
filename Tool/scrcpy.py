import subprocess

def show_android_screen():
    try:
        subprocess.run(["scrcpy"], check=True)
    except subprocess.CalledProcessError as e:
        print("启动 scrcpy 失败:", e)
    except FileNotFoundError:
        print("未找到 scrcpy，请确保已安装并加入 PATH")

if __name__ == "__main__":
    show_android_screen()