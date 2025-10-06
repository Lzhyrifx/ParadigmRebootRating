import subprocess
import os
from datetime import datetime


class AScreenCapScreenshot:
    def __init__(self, adb_path='adb', ascreencap_path=None, device_id=None):
        """
        初始化aScreenCap截图工具

        参数:
            adb_path: ADB工具的路径，默认为'adb'（如果已加入环境变量）
            ascreencap_path: aScreenCap_nc在电脑上的路径，None表示已安装到设备
            device_id: 特定设备的ID，用于多设备连接时指定目标设备
        """
        self.adb_path = adb_path
        self.ascreencap_path = ascreencap_path
        self.device_binary = '/data/local/tmp/ascreencap_nc'  # 设备上的默认路径
        self.device_id = "3a248b9b"  # 新增：设备ID

    def _build_adb_command(self, command_parts):
        """构建ADB命令，处理多设备情况"""
        adb_cmd = [self.adb_path]
        # 如果指定了设备ID，添加设备参数
        if self.device_id:
            adb_cmd.extend(['-s', self.device_id])
        adb_cmd.extend(command_parts)
        return adb_cmd

    def check_adb(self):
        """检查ADB是否可用"""
        try:
            subprocess.check_output(
                [self.adb_path, '--version'],
                stderr=subprocess.STDOUT,
                text=True
            )
            return True
        except Exception as e:
            print(f"ADB不可用，请检查ADB路径是否正确: {e}")
            return False

    def list_devices(self):
        """列出所有连接的设备"""
        try:
            result = subprocess.check_output(
                [self.adb_path, 'devices'],
                stderr=subprocess.STDOUT,
                text=True
            )

            devices = []
            for line in result.splitlines():
                if 'device' in line and not 'List of devices' in line:
                    device_id = line.split('\t')[0].strip()
                    devices.append(device_id)

            return devices
        except Exception as e:
            print(f"列出设备时出错: {e}")
            return []

    def check_device(self):
        """检查设备是否已连接并可用"""
        if not self.check_adb():
            return False

        devices = self.list_devices()

        if len(devices) == 0:
            print("未检测到任何连接的Android设备")
            return False

        # 多设备情况且未指定设备ID
        if len(devices) > 1 and not self.device_id:
            print("检测到多个设备，请指定设备ID:")
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device}")
            return False

        # 检查指定的设备是否存在
        if self.device_id and self.device_id not in devices:
            print(f"指定的设备ID {self.device_id} 未找到")
            return False

        return True

    def push_binary(self):
        """将aScreenCap_nc推送到设备并设置权限"""
        if not self.ascreencap_path or not os.path.exists(self.ascreencap_path):
            return True

        try:
            # 使用新的命令构建方法
            subprocess.check_output(
                self._build_adb_command(['push', self.ascreencap_path, self.device_binary]),
                stderr=subprocess.STDOUT,
                text=True
            )

            # 设置执行权限
            subprocess.check_output(
                self._build_adb_command(['shell', 'chmod', '755', self.device_binary]),
                stderr=subprocess.STDOUT,
                text=True
            )
            return True
        except Exception as e:
            print(f"推送aScreenCap_nc到设备时出错: {e}")
            return False

    def take_screenshot(self, output_path=None, rotation=0):
        """
        截取设备屏幕并保存到本地

        参数:
            output_path: 输出文件路径，None则使用当前时间作为文件名
            rotation: 旋转角度，0-3分别代表0°、90°、180°、270°

        返回:
            成功则返回保存的文件路径，失败则返回None
        """
        if not self.check_device():
            return None

        # 如果指定了本地文件，推送至设备
        if self.ascreencap_path and not self.push_binary():
            return None

        # 确定输出文件路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"screenshot_{timestamp}.png"

        try:
            # 构建命令，支持旋转参数和设备指定
            command = self._build_adb_command(['shell', f'{self.device_binary} -r {rotation}'])

            # 执行命令并将输出保存为图片
            with open(output_path, 'wb') as f:
                process = subprocess.Popen(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE
                )

                # 等待命令完成并检查错误
                _, error = process.communicate()
                if process.returncode != 0:
                    error_msg = error.decode('utf-8', errors='ignore')
                    print(f"截图失败: {error_msg}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return None

            # 验证文件是否有效
            if os.path.getsize(output_path) < 1024:  # 小于1KB可能是无效文件
                print("生成的截图文件可能无效")
                os.remove(output_path)
                return None

            print(f"截图已成功保存至: {os.path.abspath(output_path)}")
            return output_path

        except Exception as e:
            print(f"执行截图时出错: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None


if __name__ == "__main__":
    # 列出所有设备
    screencap = AScreenCapScreenshot()
    devices = screencap.list_devices()

    if len(devices) > 0:
        print("检测到以下设备:")
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device}")

        # 选择设备
        if len(devices) > 1:
            try:
                choice = int(input("请输入设备编号选择要操作的设备: ")) - 1
                selected_device = devices[choice]
            except (ValueError, IndexError):
                print("无效的选择，使用第一个设备")
                selected_device = devices[0]
        else:
            selected_device = devices[0]

        # 初始化截图工具并截图
        screenshotter = AScreenCapScreenshot(
            adb_path='adb',
            # ascreencap_path='/path/to/your/ascreencap_nc',  # 本地aScreenCap_nc路径
            device_id=selected_device
        )

        # 截取屏幕
        screenshotter.take_screenshot(rotation=0)
    else:
        print("没有检测到任何连接的设备")
