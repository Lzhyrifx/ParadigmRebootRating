import cv2


def get_coordinates(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        scale_factor = param['scale_factor']
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)

        if 0 <= orig_x < param['orig_width'] and 0 <= orig_y < param['orig_height']:
            pixel_color = param['original_image'][orig_y, orig_x]
            b, g, r = pixel_color

            print(f"显示窗口坐标: ({x}, {y})")
            print(f"原图实际坐标: ({orig_x}, {orig_y})")
            print(f"RGB颜色: ({r}, {g}, {b})")
            print(f"BGR颜色: ({b}, {g}, {r})")
            print("-" * 30)

            param['points'].append((orig_x, orig_y))

            cv2.circle(param['display_img'], (x, y), 5, (0, 0, 255), -1)

            text = f"({orig_x},{orig_y}) RGB:({r},{g},{b})"
            cv2.putText(param['display_img'], text, (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow('Image', param['display_img'])

            if len(param['points']) >= 2:
                print(f"\n已选择 {len(param['points'])} 个点")
                if len(param['points']) == 4:
                    print("已获取4个点坐标：")
                    for i, (px, py) in enumerate(param['points']):
                        # 获取每个点的颜色
                        point_color = param['original_image'][py, px]
                        b, g, r = point_color
                        print(f"点{i + 1}: ({px}, {py}) - RGB:({r}, {g}, {b})")




''''''
image_path = 'SCR/n002.jpg'
''''''




original_image = cv2.imread(image_path)


img_height, img_width = original_image.shape[:2]
print(f"原图尺寸: {img_width} x {img_height}")

screen_width = 1920
screen_height = 1080

scale_factor = min(screen_width / img_width, screen_height / img_height, 1.0)
new_width = int(img_width * scale_factor)
new_height = int(img_height * scale_factor)

display_img = cv2.resize(original_image, (new_width, new_height))
print(f"显示尺寸: {new_width} x {new_height}, 缩放比例: {scale_factor:.2f}")

cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Image', new_width, new_height)

params = {
    'scale_factor': scale_factor,
    'points': [],
    'display_img': display_img,
    'original_image': original_image,
    'orig_width': img_width,
    'orig_height': img_height
}

cv2.setMouseCallback('Image', get_coordinates, param=params)

while True:
    cv2.imshow('Image', display_img)
    key = cv2.waitKey(1) & 0xFF
    if cv2.getWindowProperty('Image', cv2.WND_PROP_VISIBLE) < 1:
        break
    if key == ord('q'):
        break
    elif key == ord('r'):
        params['points'] = []
        display_img = cv2.resize(original_image, (new_width, new_height))
        params['display_img'] = display_img
        print("已重置所有点")
    elif key == ord('c'):
        if params['points']:
            print("\n当前所有点的颜色信息：")
            for i, (px, py) in enumerate(params['points']):
                if 0 <= px < img_width and 0 <= py < img_height:
                    pixel_color = original_image[py, px]
                    b, g, r = pixel_color
                    print(f"点{i + 1}: ({px}, {py}) - RGB:({r}, {g}, {b})")
                else:
                    print(f"点{i + 1}: ({px}, {py}) - 坐标超出图像范围")

cv2.destroyAllWindows()


if params['points']:
    for i, (x, y) in enumerate(params['points']):
        if 0 <= x < img_width and 0 <= y < img_height:
            pixel_color = original_image[y, x]
            b, g, r = pixel_color
            print(f"点{i + 1}: ({x}, {y}) - RGB:({r}, {g}, {b})")