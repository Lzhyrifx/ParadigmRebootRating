import uiautomator2 as u2
import time


def init_device():
    """初始化设备连接"""
    try:
        d = u2.connect()  # 自动连接设备
        print(f"设备连接成功: {d.device_info['model']}")
        return d
    except Exception as e:
        print(f"设备连接失败: {str(e)}")
        exit(1)


def swipe_up(d):
    """使用uiautomator2实现上滑操作"""
    # 起点坐标 (894, 1369)，终点坐标 (913, 611)
    start_x, start_y = 894, 1369
    end_x, end_y = 913, 611

    print(f"从 ({start_x}, {start_y}) 上滑到 ({end_x}, {end_y})")

    try:
        # 执行滑动操作，duration为滑动持续时间（毫秒）
        # 时间越长，滑动越平缓
        d.swipe(start_x, start_y, end_x, end_y, duration=500)
        print("上滑操作完成")
    except Exception as e:
        print(f"上滑操作失败: {str(e)}")


if __name__ == "__main__":
    d = init_device()

    # 执行上滑操作
    swipe_up(d)

    # 可以根据需要添加多次滑动
    # time.sleep(1)
    # swipe_up(d)
