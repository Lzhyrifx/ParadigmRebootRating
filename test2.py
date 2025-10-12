from rapidfuzz import fuzz, process


def custom_match(query, candidates, target_artist):
    # 存储每个候选的得分和信息
    scored_candidates = []

    for candidate in candidates:
        # 1. 基础匹配得分
        base_score = fuzz.partial_ratio(query, candidate)

        # 2. 自定义权重：曲师名完全匹配加分
        if target_artist in candidate:
            base_score += 3  # 增加权重

        # 3. 自定义权重：如果是目标曲目的特定前缀（如"И00."），额外加分
        if candidate.startswith("И00."):
            base_score += 2  # 打破平局的关键加分

        scored_candidates.append((candidate, base_score))

    # 找到最高分的候选（得分相同则按原始顺序）
    best_candidate = max(scored_candidates, key=lambda x: x[1])
    return best_candidate


# 使用示例
query = "noo iNSe-U-Ra"
candidates = ["И00.  Se-U-Ra", "Verreta  Se-U-Ra"]
target_artist = "Se-U-Ra"

best = custom_match(query, candidates, target_artist)
print(f"最佳匹配: {best[0]} (得分: {best[1]})")
