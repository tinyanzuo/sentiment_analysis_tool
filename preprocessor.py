# preprocessor.py
# 京东评论情感分析系统 - 文本预处理模块

import re
import jieba
from config import CN_STOPWORDS, NEGATION_WORDS, DEGREE_WORDS


class TextPreprocessor:
    """文本预处理类"""
    
    def __init__(self):
        self.stopwords = CN_STOPWORDS
        self.negation_words = NEGATION_WORDS
        self.degree_words = DEGREE_WORDS
        self.cache = {}

    def preprocess(self, text, keep_negation=True):
        """
        预处理文本
        keep_negation: 是否保留否定词（用于模型训练）
        """
        if text in self.cache:
            return self.cache[text]

        if not isinstance(text, str):
            text = str(text)

        # 清理文本，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        if not text:
            return ""

        # 分词
        words = jieba.lcut(text)

        # 处理否定词和程度词
        processed_words = []
        i = 0
        negation_scope = 0  # 否定词影响范围

        while i < len(words):
            word = words[i]

            # 检测否定词
            if word in self.negation_words:
                processed_words.append(word)
                negation_scope = 3  # 接下来的3个词都受否定影响
                i += 1
                continue

            # 如果在否定范围内，给词加上否定标记
            if negation_scope > 0:
                if len(word) > 1:  # 只标记有意义的词
                    processed_words.append("不_" + word)
                else:
                    processed_words.append(word)
                negation_scope -= 1
                i += 1
                continue

            # 检测程度词
            if word in self.degree_words and i + 1 < len(words):
                next_word = words[i + 1]
                # 如果下一个词不是停用词，组合程度词和下一个词
                if next_word not in self.stopwords:
                    processed_words.append(word + "_" + next_word)
                    i += 2
                    continue

            # 普通词，过滤停用词
            if word not in self.stopwords or word in self.degree_words:
                if len(word) > 1 or word in self.degree_words:
                    processed_words.append(word)

            i += 1

        result = ' '.join(processed_words)
        self.cache[text] = result
        return result

    def preprocess_with_negation_marker(self, text):
        """
        预处理并标记否定词（用于规则判断）
        返回：带否定标记的词语列表
        """
        if not isinstance(text, str):
            text = str(text)

        # 分词
        words = jieba.lcut(text)

        processed = []
        negated = False
        negation_range = 3  # 否定词影响的词数

        i = 0
        while i < len(words):
            word = words[i]

            # 跳过停用词
            if word in self.stopwords and word not in self.negation_words:
                i += 1
                continue

            # 检测否定词
            if word in self.negation_words:
                negated = True
                negation_count = 0
                i += 1
                continue

            # 如果处于否定范围，给词加上否定标记
            if negated and negation_count < negation_range:
                if len(word) > 1:  # 只标记有意义的词
                    processed.append("不" + word)
                negation_count += 1
            else:
                if len(word) > 1:
                    # 检测程度词
                    if word in self.degree_words and i + 1 < len(words):
                        # 程度词+情感词
                        next_word = words[i + 1]
                        if len(next_word) > 1:
                            processed.append(word + next_word)
                            i += 1
                        else:
                            processed.append(word)
                    else:
                        processed.append(word)

            i += 1

            # 重置否定状态
            if negated and negation_count >= negation_range:
                negated = False

        return processed


# 创建全局预处理器实例
preprocessor = TextPreprocessor()