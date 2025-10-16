
from function import ocr_region


region_song_level= (624,1668,894,1911)

level = ocr_region("Temp/test.png", *region_song_level)
print(level)