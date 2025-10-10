import os

import adbutils
import cv2
import uiautomator2 as u2
from rapidocr import RapidOCR
import logging
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
logging.getLogger('RapidOCR').disabled = True

engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)
LAST_DEVICE_FILE = ".used_device"

def init_device():
    try:
        adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
        devices = adb.list()

        if not devices:
            print("没有检测到任何连接的设备，请确保设备已通过ADB连接")
            exit(1)


        last_used_device = None
        if os.path.exists(LAST_DEVICE_FILE):
            with open(LAST_DEVICE_FILE, "r") as f:
                last_used_device = f.read().strip()
                print(f"检测到上次使用的设备：{last_used_device}")


        matched_device = None
        if last_used_device:
            for dev in devices:
                if dev.serial == last_used_device:
                    matched_device = dev
                    break


        if matched_device:
            print(f"自动连接上次使用的设备：{matched_device.serial}")
            d = u2.connect(matched_device.serial)
            print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
            return d


        if len(devices) == 1:
            device_id = devices[0].serial
            print(f"只检测到一个设备，自动连接: {device_id}")
            d = u2.connect(device_id)
        else:
            print("检测到多个设备，请选择要连接的设备：")
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device.serial} (状态: {device.state})")

            while True:
                try:
                    choice = int(input(f"请输入设备编号(1-{len(devices)}): "))
                    if 1 <= choice <= len(devices):
                        device_id = devices[choice - 1].serial
                        break
                    else:
                        print(f"请输入1到{len(devices)}之间的数字")
                except ValueError:
                    print("请输入有效的数字")

            d = u2.connect(device_id)

        with open(LAST_DEVICE_FILE, "w") as f:
            f.write(device_id)
        print(f"已记住当前设备：{device_id}（下次将自动连接）")

        print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d

    except ImportError:
        exit(1)
    except Exception as e:
        print(f"设备连接失败：{str(e)}")
        exit(1)


def ocr_region(image_path, region_coords):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res

