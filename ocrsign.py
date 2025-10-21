
from OCR import ocr_region


region_song_level= (624,1668,894,1911)

level = ocr_region("SCR/sign.jpg", *region_song_level)
print(level)