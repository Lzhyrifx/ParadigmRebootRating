from rapidfuzz import fuzz

# 模拟你的情况
ocr_text = " CSe-U-Ra"  # 曲名为空，只有艺术家
compare_text = "И00. Se-U-Ra"

score = fuzz.partial_ratio(ocr_text, compare_text)
print(f"匹配分数: {score}")  # 应该接近94.1