import time

from function import init_device


song_coords = [
    (1110, 491),
    (1014, 744),
    (862, 1003),
    (728, 1230),
    (584, 1468),
    (427, 1735),
]

counter = 1

d = init_device()

def scr():
    global counter
    for idx, (x, y) in enumerate(song_coords):
        print(f"\n处理歌曲：{counter}")

        tap_coordinate(d, x, y)
        counter += 1
def tap_coordinate(d, x, y):
    try:
        d.click(x, y)

        print(f"已点击坐标：({x}, {y})")
    except Exception as e:
        print(f"点击失败：{str(e)}")

def slide():
    w = d.info['displayWidth']
    x = w * 0.5
    start_y = 1800
    end_y = 700

    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.2)
    d.touch.up(x, end_y)

    d.touch.down(x, start_y)
    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.6)
    d.touch.up(x, end_y)



if __name__ == "__main__":
    scr()
    slide()
    scr()
    slide()
    scr()
    slide()
    scr()
    slide()
    scr()

