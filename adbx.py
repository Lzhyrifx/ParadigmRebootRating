import cv2
import numpy as np
import subprocess
import time

def adb_screen_stream():
    while True:
        try:
            # 使用 adb 获取屏幕截图（PNG 格式）
            result = subprocess.run(
                ["adb", "exec-out", "screencap", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                print("ADB 截图失败:", result.stderr.decode())
                break

            # 将字节流解码为图像
            img_array = np.frombuffer(result.stdout, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is not None:
                cv2.imshow("Android Screen", img)
                if cv2.waitKey(1) == ord('q'):  # 按 q 退出
                    break
            else:
                print("图像解码失败")
                time.sleep(1)

            time.sleep(0.3)  # 控制刷新频率（约 3 FPS）

        except Exception as e:
            print("错误:", e)
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    adb_screen_stream()