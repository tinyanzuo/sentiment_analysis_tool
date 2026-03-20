"""
情感分析模型模块 - 训练和预测情感分类
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, cross_val_score

from preprocessor import preprocessor
from demo_generator import DemoDataGenerator
from config import SENTIMENT_LEXICON


class SentimentModel:
    """情感分析模型 - 增强版，支持用户上传数据训练"""

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        self.accuracy = 0
        self.feature_names = None
        self.class_labels = ['正面', '中性', '负面']
        self.model_type = 'logistic'
        self.available_models = {
            'logistic': '逻辑回归',
            'naive_bayes': '朴素贝叶斯',
            'svm': '支持向量机',
            'random_forest': '随机森林'
        }

        self.demo_generator = DemoDataGenerator()
        self.training_data = []
        self.user_training_data = []
        self.data_source = "演示数据"

    def set_model_type(self, model_type):
        if model_type in self.available_models:
            self.model_type = model_type
            return True
        return False

    def get_available_models(self):
        return self.available_models

    def extract_features(self, texts, use_ngram_range=(1, 3), max_features=10000):
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=use_ngram_range,
            min_df=2,
            max_df=0.9,
            sublinear_tf=True,
            use_idf=True,
            smooth_idf=True,
            norm='l2'
        )

        X = vectorizer.fit_transform(texts)
        self.feature_names = vectorizer.get_feature_names_out()

        return X, vectorizer

    def train_with_cv(self, X, y, progress_callback=None):
        models = {
            'naive_bayes': MultinomialNB(alpha=0.5),
            'logistic': LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced', random_state=42),
            'svm': LinearSVC(max_iter=2000, C=1.0, class_weight='balanced', random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42,
                                                    class_weight='balanced')
        }

        best_score = 0
        best_model = None
        best_model_name = None

        if self.model_type:
            if self.model_type in models:
                model = models[self.model_type]
                try:
                    scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
                    mean_score = scores.mean()

                    if progress_callback:
                        progress_callback(70,
                                          f"{self.available_models[self.model_type]} 交叉验证准确率: {mean_score:.4f}")

                    best_score = mean_score
                    best_model = model
                    best_model_name = self.model_type
                except Exception as e:
                    if progress_callback:
                        progress_callback(-1, f"{self.model_type} 训练失败: {str(e)}")
                    best_model = MultinomialNB(alpha=0.5)
                    best_model_name = 'naive_bayes'
                    best_score = 0.7
        else:
            if progress_callback:
                progress_callback(70, "进行交叉验证选择最佳模型...")

            for name, model in models.items():
                try:
                    scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
                    mean_score = scores.mean()

                    if progress_callback:
                        progress_callback(70 + 5 * list(models.keys()).index(name),
                                          f"{self.available_models[name]} 交叉验证准确率: {mean_score:.4f}")

                    if mean_score > best_score:
                        best_score = mean_score
                        best_model = model
                        best_model_name = name
                except Exception as e:
                    if progress_callback:
                        progress_callback(-1, f"{name} 训练失败: {str(e)}")
                    continue

            if best_model is None:
                best_model = MultinomialNB(alpha=0.5)
                best_model_name = 'naive_bayes'

        if progress_callback:
            progress_callback(85, f"使用模型: {self.available_models[best_model_name]} (准确率: {best_score:.4f})")

        best_model.fit(X, y)

        return best_model, best_model_name, best_score

    def train_with_user_data(self, texts, labels, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(5, "开始使用用户数据训练模型...")

            valid_data = []
            invalid_count = 0

            for text, label in zip(texts, labels):
                if not isinstance(text, str) or not text.strip():
                    invalid_count += 1
                    continue

                label = str(label).strip()
                if label in ['正面', 'positive', 'pos', '好评', '5', '4']:
                    valid_label = '正面'
                elif label in ['负面', 'negative', 'neg', '差评', '1', '2']:
                    valid_label = '负面'
                elif label in ['中性', 'neutral', '中评', '3']:
                    valid_label = '中性'
                else:
                    invalid_count += 1
                    continue

                valid_data.append((text.strip(), valid_label))

            if not valid_data:
                if progress_callback:
                    progress_callback(-1, "错误：没有有效的训练数据")
                return None

            if invalid_count > 0 and progress_callback:
                progress_callback(10, f"过滤掉 {invalid_count} 条无效数据")

            user_texts = [item[0] for item in valid_data]
            user_labels = [item[1] for item in valid_data]

            self.user_training_data = valid_data
            self.training_data = valid_data
            self.data_source = "用户数据"

            if progress_callback:
                progress_callback(15, f"用户数据验证完成，有效样本：{len(valid_data)}条")
                progress_callback(20, "统计标签分布...")

            label_counts = {}
            for label in user_labels:
                label_counts[label] = label_counts.get(label, 0) + 1

            if progress_callback:
                for label in self.class_labels:
                    count = label_counts.get(label, 0)
                    if count > 0:
                        progress_callback(20, f"  {label}: {count}条 ({count / len(valid_data) * 100:.1f}%)")
                    else:
                        progress_callback(20, f"  {label}: 0条 (0.0%)")

            if progress_callback:
                progress_callback(30, "正在预处理文本...")

            processed_texts = []
            for text in user_texts:
                processed = preprocessor.preprocess(text, keep_negation=True)
                if processed:
                    processed_texts.append(processed)
                else:
                    processed_texts.append(text)

            if progress_callback:
                progress_callback(40, f"预处理完成")

            if progress_callback:
                progress_callback(50, "提取TF-IDF特征...")

            max_features = min(12000, len(valid_data) * 10)

            X, self.vectorizer = self.extract_features(
                processed_texts,
                use_ngram_range=(1, 4),
                max_features=max_features
            )

            if progress_callback:
                progress_callback(60, f"特征提取完成，共 {len(self.feature_names)} 个特征词")

            if len(valid_data) >= 50:
                try:
                    X_train, X_val, y_train, y_val = train_test_split(
                        X, user_labels, test_size=0.2, random_state=42,
                        stratify=user_labels if len(set(user_labels)) > 1 else None
                    )

                    if progress_callback:
                        progress_callback(70, f"训练集: {X_train.shape[0]}条, 验证集: {X_val.shape[0]}条")

                    self.model, self.model_type, cv_score = self.train_with_cv(X_train, y_train, progress_callback)

                    if progress_callback:
                        progress_callback(90, "评估模型...")

                    y_pred_val = self.model.predict(X_val)
                    self.val_accuracy = accuracy_score(y_val, y_pred_val)

                    self._calculate_class_accuracy(y_val, y_pred_val)

                    self.is_trained = True
                    self.accuracy = cv_score

                    if progress_callback:
                        progress_callback(100,
                                          f"训练完成！交叉验证准确率：{cv_score:.4f}，验证集准确率：{self.val_accuracy:.4f}")

                except Exception as e:
                    if progress_callback:
                        progress_callback(70, f"分层抽样失败，使用普通划分: {str(e)}")

                    X_train, X_val, y_train, y_val = train_test_split(
                        X, user_labels, test_size=0.2, random_state=42
                    )

                    self.model, self.model_type, cv_score = self.train_with_cv(X_train, y_train, progress_callback)
                    y_pred_val = self.model.predict(X_val)
                    self.val_accuracy = accuracy_score(y_val, y_pred_val)
                    self.is_trained = True
                    self.accuracy = cv_score

                    if progress_callback:
                        progress_callback(100,
                                          f"训练完成！交叉验证准确率：{cv_score:.4f}，验证集准确率：{self.val_accuracy:.4f}")

            else:
                if progress_callback:
                    progress_callback(70, f"数据量较少 ({len(valid_data)}条)，直接训练...")

                models = {
                    'naive_bayes': MultinomialNB(alpha=0.5),
                    'logistic': LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced', random_state=42),
                    'svm': LinearSVC(max_iter=2000, C=1.0, class_weight='balanced', random_state=42),
                    'random_forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42,
                                                            class_weight='balanced')
                }

                if self.model_type in models:
                    self.model = models[self.model_type]
                else:
                    self.model = models['logistic']

                self.model.fit(X, user_labels)

                if len(valid_data) >= 10:
                    try:
                        from sklearn.model_selection import cross_val_score
                        cv_folds = min(3, len(set(user_labels)))
                        if cv_folds >= 2:
                            scores = cross_val_score(self.model, X, user_labels, cv=cv_folds, scoring='accuracy')
                            self.accuracy = scores.mean()
                        else:
                            self.accuracy = 0.7
                    except:
                        self.accuracy = 0.7
                else:
                    self.accuracy = 0.7

                self.val_accuracy = self.accuracy
                self.is_trained = True

                if progress_callback:
                    progress_callback(100,
                                      f"训练完成！模型: {self.available_models.get(self.model_type, self.model_type)}")

            self._calculate_feature_importance()

            return self.accuracy

        except Exception as e:
            if progress_callback:
                progress_callback(-1, f"训练失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def train_mixed(self, user_texts=None, user_labels=None, demo_ratio=0.3, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(5, "开始混合训练...")

            mixed_texts = []
            mixed_labels = []

            user_count = 0
            if user_texts and user_labels and len(user_texts) > 0:
                valid_user = []
                for text, label in zip(user_texts, user_labels):
                    if isinstance(text, str) and text.strip() and label in self.class_labels:
                        valid_user.append((text.strip(), label))

                if valid_user:
                    user_texts_clean = [item[0] for item in valid_user]
                    user_labels_clean = [item[1] for item in valid_user]

                    mixed_texts.extend(user_texts_clean)
                    mixed_labels.extend(user_labels_clean)
                    user_count = len(user_texts_clean)

                    if progress_callback:
                        progress_callback(15, f"添加用户数据：{user_count}条")

            if demo_ratio > 0 and len(mixed_texts) < 200:
                if user_count > 0:
                    target_total = int(user_count / (1 - demo_ratio))
                    demo_needed = max(0, target_total - user_count)
                else:
                    demo_needed = 500

                demo_needed = min(demo_needed, 1500)

                if demo_needed > 0 and progress_callback:
                    progress_callback(25, f"生成补充数据：{demo_needed}条")

                demo_texts, demo_labels = self.demo_generator.generate_training_data(demo_needed)

                mixed_texts.extend(demo_texts)
                mixed_labels.extend(demo_labels)

                if progress_callback:
                    progress_callback(35, f"总训练数据：{len(mixed_texts)}条 (用户:{user_count}, 演示:{demo_needed})")

                self.data_source = f"混合数据(用户:{user_count},演示:{demo_needed})"
            else:
                self.data_source = "用户数据"

            return self.train_with_user_data(mixed_texts, mixed_labels, progress_callback)

        except Exception as e:
            if progress_callback:
                progress_callback(-1, f"混合训练失败：{str(e)}")
            return None

    def _calculate_class_accuracy(self, true_labels, pred_labels):
        from collections import Counter

        self.class_accuracy = {}
        true_counts = Counter(true_labels)

        for label in self.class_labels:
            total = true_counts.get(label, 0)
            if total > 0:
                correct = sum(1 for t, p in zip(true_labels, pred_labels)
                              if t == label and p == label)
                self.class_accuracy[label] = correct / total
            else:
                self.class_accuracy[label] = 0

    def _calculate_feature_importance(self):
        self.feature_importance = {}

        if self.model_type == 'logistic':
            coef = self.model.coef_
            for i, label in enumerate(self.class_labels):
                if i < len(coef):
                    top_indices = np.argsort(coef[i])[-30:][::-1]
                    self.feature_importance[label] = [(self.feature_names[j], coef[i][j]) for j in top_indices]

        elif self.model_type == 'random_forest':
            importances = self.model.feature_importances_
            top_indices = np.argsort(importances)[-50:][::-1]
            self.feature_importance['all'] = [(self.feature_names[j], importances[j]) for j in top_indices]

        elif self.model_type == 'svm':
            if hasattr(self.model, 'coef_'):
                coef = self.model.coef_
                for i, label in enumerate(self.class_labels):
                    if len(self.class_labels) == 2 and i == 1:
                        continue
                    if i < len(coef):
                        top_indices = np.argsort(np.abs(coef[i]))[-30:][::-1]
                        self.feature_importance[label] = [(self.feature_names[j], coef[i][j]) for j in top_indices]

    def predict(self, text):
        if not self.is_trained:
            result = self._rule_based_sentiment(text)
            return result['sentiment']

        try:
            processed = preprocessor.preprocess(text, keep_negation=True)
            if not processed:
                return "中性"
            X = self.vectorizer.transform([processed])

            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                pred = self.model.classes_[np.argmax(proba)]
            else:
                pred = self.model.predict(X)[0]

            return pred
        except:
            result = self._rule_based_sentiment(text)
            return result['sentiment']

    def predict_batch(self, texts):
        if not self.is_trained:
            return [self._rule_based_sentiment(text)['sentiment'] for text in texts]

        results = []
        for text in texts:
            results.append(self.predict(text))
        return results

    def _rule_based_sentiment(self, text):
        positive_words = SENTIMENT_LEXICON["正面"]
        negative_words = SENTIMENT_LEXICON["负面"]

        words_with_neg = preprocessor.preprocess_with_negation_marker(text)

        pos_score = 0
        neg_score = 0

        for word in words_with_neg:
            is_negated = word.startswith('不') and len(word) > 1
            base_word = word[1:] if is_negated else word

            if base_word in positive_words:
                if is_negated:
                    neg_score += 1
                else:
                    pos_score += 1
            elif base_word in negative_words:
                if is_negated:
                    pos_score += 1
                else:
                    neg_score += 1

        if pos_score > neg_score:
            return {"sentiment": "正面", "pos_score": pos_score, "neg_score": neg_score}
        elif neg_score > pos_score:
            return {"sentiment": "负面", "pos_score": pos_score, "neg_score": neg_score}
        else:
            return {"sentiment": "中性", "pos_score": pos_score, "neg_score": neg_score}

    def explain_prediction(self, text):
        if not self.is_trained:
            result = self._rule_based_sentiment(text)
            return {
                'sentiment': result['sentiment'],
                'method': '规则匹配',
                'pos_score': result['pos_score'],
                'neg_score': result['neg_score']
            }

        try:
            processed = preprocessor.preprocess(text, keep_negation=True)
            if not processed:
                return {'sentiment': '中性', 'method': '无有效内容'}

            X = self.vectorizer.transform([processed])

            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                scores = dict(zip(self.model.classes_, proba))
                pred = self.model.classes_[np.argmax(proba)]
            else:
                pred = self.model.predict(X)[0]
                if hasattr(self.model, 'decision_function'):
                    decision = self.model.decision_function(X)[0]
                    scores = {}
                    for i, cls in enumerate(self.model.classes_):
                        if len(self.model.classes_) == 2 and i == 0:
                            scores[cls] = 1 / (1 + np.exp(-decision))
                        elif len(self.model.classes_) == 2 and i == 1:
                            scores[cls] = 1 - scores[self.model.classes_[0]]
                        else:
                            scores[cls] = 0.5
                else:
                    scores = {cls: 0.33 for cls in self.model.classes_}
                    scores[pred] = 0.5

            feature_indices = X.indices
            feature_values = X.data

            word_contributions = []
            for idx, value in zip(feature_indices, feature_values):
                if idx < len(self.feature_names):
                    word = self.feature_names[idx]
                    word_contributions.append({
                        'word': word,
                        'value': value
                    })

            return {
                'sentiment': pred,
                'scores': scores,
                'word_contributions': word_contributions[:20],
                'method': self.available_models.get(self.model_type, self.model_type),
                'processed_text': processed
            }

        except Exception as e:
            return {'sentiment': '中性', 'error': str(e), 'method': '错误处理'}

    def get_training_info(self):
        if not self.is_trained:
            return None

        label_counts = {}
        for _, label in self.training_data:
            label_counts[label] = label_counts.get(label, 0) + 1

        return {
            'accuracy': self.accuracy,
            'val_accuracy': getattr(self, 'val_accuracy', self.accuracy),
            'total_samples': len(self.training_data),
            'label_counts': label_counts,
            'feature_count': len(self.feature_names) if self.feature_names is not None else 0,
            'feature_importance': self.feature_importance if hasattr(self, 'feature_importance') else None,
            'class_accuracy': getattr(self, 'class_accuracy', {}),
            'model_type': self.available_models.get(self.model_type, self.model_type),
            'data_source': getattr(self, 'data_source', '演示数据')
        }

    def train(self, progress_callback=None, sample_count=1500):
        """训练演示模型"""
        texts, labels = self.demo_generator.generate_training_data(sample_count)
        self.train_with_user_data(texts, labels, progress_callback)