# dimension_analyzer.py
# 京东评论情感分析系统 - 多维度情感分析器

from config import DIMENSION_KEYWORDS


class MultiDimensionAnalyzer:
    """多维度情感分析器"""

    def __init__(self):
        self.dimensions = list(DIMENSION_KEYWORDS.keys())
        self.lexicon = DIMENSION_KEYWORDS

    def analyze(self, text):
        """
        对单条评论进行多维度分析
        返回：字典，包含各维度的情感倾向和置信度
        """
        results = {}

        for dimension in self.dimensions:
            pos_words = self.lexicon[dimension]["正面"]
            neg_words = self.lexicon[dimension]["负面"]
            neu_words = self.lexicon[dimension]["中性"]

            # 查找匹配的关键词
            found_pos = [w for w in pos_words if w in text]
            found_neg = [w for w in neg_words if w in text]
            found_neu = [w for w in neu_words if w in text]

            pos_count = len(found_pos)
            neg_count = len(found_neg)
            neu_count = len(found_neu)

            # 计算情感倾向
            if pos_count > 0 or neg_count > 0 or neu_count > 0:
                if pos_count > neg_count and pos_count > neu_count:
                    sentiment = "正面"
                    confidence = pos_count / (pos_count + neg_count + neu_count)
                elif neg_count > pos_count and neg_count > neu_count:
                    sentiment = "负面"
                    confidence = neg_count / (pos_count + neg_count + neu_count)
                elif neu_count > 0:
                    sentiment = "中性"
                    confidence = neu_count / (pos_count + neg_count + neu_count)
                else:
                    sentiment = "未提及"
                    confidence = 0

                results[dimension] = {
                    "sentiment": sentiment,
                    "confidence": round(confidence, 2),
                    "keywords": {
                        "正面": found_pos,
                        "负面": found_neg,
                        "中性": found_neu
                    },
                    "counts": {
                        "正面": pos_count,
                        "负面": neg_count,
                        "中性": neu_count
                    }
                }
            else:
                results[dimension] = {
                    "sentiment": "未提及",
                    "confidence": 0,
                    "keywords": {"正面": [], "负面": [], "中性": []},
                    "counts": {"正面": 0, "负面": 0, "中性": 0}
                }

        return results

    def analyze_batch(self, texts):
        """批量分析"""
        results = []
        for text in texts:
            results.append(self.analyze(text))
        return results

    def get_dimension_stats(self, df, comment_col='评论内容'):
        """获取各维度的统计信息"""
        if df is None or df.empty:
            return None

        dimension_stats = {}

        # 初始化统计
        for dim in self.dimensions:
            dimension_stats[dim] = {
                "正面": 0,
                "中性": 0,
                "负面": 0,
                "未提及": 0,
                "总提及": 0,
                "正面率": 0,
                "负面率": 0,
                "好评率": 0
            }

        # 逐条分析
        for text in df[comment_col]:
            results = self.analyze(text)
            for dim, result in results.items():
                if result["sentiment"] != "未提及":
                    dimension_stats[dim][result["sentiment"]] += 1
                    dimension_stats[dim]["总提及"] += 1
                else:
                    dimension_stats[dim]["未提及"] += 1

        # 计算比率
        total_comments = len(df)
        for dim in self.dimensions:
            total_mentioned = dimension_stats[dim]["总提及"]
            if total_mentioned > 0:
                dimension_stats[dim]["正面率"] = round(dimension_stats[dim]["正面"] / total_mentioned * 100, 2)
                dimension_stats[dim]["负面率"] = round(dimension_stats[dim]["负面"] / total_mentioned * 100, 2)
                dimension_stats[dim]["好评率"] = round(dimension_stats[dim]["正面"] / total_comments * 100, 2)

        return dimension_stats