"""
演示数据生成器 - 生成多样化的模拟评论数据
"""
import random
import re
import pandas as pd
from config import PRODUCT_INFO


class DemoDataGenerator:
    """生成多样化的演示数据 """

    def __init__(self):
        # 真实评论语料库（从实际京东评论中提取的模板）
        self.real_templates = {
            "正面": [
                "东西收到了，{product_name}{feature}，比想象中要好，{positive_point}",
                "物流很快，{product_name}包装完好，{feature}{positive_point}，五星好评",
                "用了几天才来评价，{product_name}{feature}{positive_point}，物超所值",
                "性价比很高，{product_name}{feature}在这个价位算是不错的了，{positive_point}",
                "正品无疑，{product_name}{feature}{positive_point}，客服态度也很好",
                "外观漂亮，{product_name}{feature}{positive_point}，老婆很喜欢",
                "运行流畅，{product_name}{feature}{positive_point}，暂时没发现什么问题",
                "发货速度很快，隔天就收到了，{product_name}{feature}{positive_point}",
                "包装很严实，{product_name}{feature}{positive_point}，没有任何磕碰",
                "给爸妈买的，他们说{product_name}{feature}{positive_point}，操作简单",
                "第二次购买了，{product_name}{feature}{positive_point}，一如既往的好",
                "做工精细，{product_name}{feature}{positive_point}，没有毛刺",
                "手感很好，{product_name}{feature}{positive_point}，大小适中",
                "清晰度很高，{product_name}{feature}{positive_point}，看电影很爽",
                "续航能力强，{product_name}{feature}{positive_point}，一天一充足够",
                "{product_name}真的很不错，{feature}{positive_point}，推荐购买",
                "很满意的一次购物，{product_name}{feature}{positive_point}，下次还会来",
                "价格实惠，{product_name}{feature}{positive_point}，比实体店便宜多了",
                "包装很用心，{product_name}{feature}{positive_point}，送人很有面子",
                "功能齐全，{product_name}{feature}{positive_point}，操作也很简单",
                "物流给力，{product_name}{feature}{positive_point}，包装完好无损",
                "客服很有耐心，解答详细，{product_name}{feature}{positive_point}",
                "质量杠杠的，{product_name}{feature}{positive_point}，很耐用",
                "外观设计很漂亮，{product_name}{feature}{positive_point}，手感也不错",
                "运行速度很快，{product_name}{feature}{positive_point}，不卡顿",
                "很实用的一款产品，{product_name}{feature}{positive_point}，值得购买",
                "已经推荐给朋友了，{product_name}{feature}{positive_point}，都说好",
                "很惊喜，{product_name}{feature}{positive_point}，超出预期",
                "很完美，{product_name}{feature}{positive_point}，没有任何瑕疵",
                "很满意，{product_name}{feature}{positive_point}，好评",
            ],
            "中性": [
                "{product_name}还行吧，{feature}{neutral_point}，对得起这个价格",
                "物流速度一般，{product_name}{feature}{neutral_point}，没什么惊喜",
                "用了几天，{product_name}{feature}{neutral_point}，没什么大问题",
                "包装有点简陋，但{product_name}{feature}{neutral_point}，能用",
                "客服回复有点慢，不过{product_name}{feature}{neutral_point}，就这样吧",
                "和描述差不多，{product_name}{feature}{neutral_point}，中规中矩",
                "价格不算便宜，{product_name}{feature}{neutral_point}，还行",
                "发货速度还可以，{product_name}{feature}{neutral_point}，没想象中好",
                "外观还行，{product_name}{feature}{neutral_point}，但也没有特别惊艳",
                "用了几天感觉{product_name}{feature}{neutral_point}，没什么特别的感觉",
                "比实体店便宜点，{product_name}{feature}{neutral_point}，凑合用吧",
                "功能都正常，{product_name}{feature}{neutral_point}，就这样",
                "包装完整，{product_name}{feature}{neutral_point}，没啥好说的",
                "物流不快不慢，{product_name}{feature}{neutral_point}，还行",
                "暂时没发现问题，{product_name}{feature}{neutral_point}，先用着看",
                "{product_name}一般般，{feature}{neutral_point}，不惊喜也不失望",
                "还行吧，{product_name}{feature}{neutral_point}，能用就行",
                "中规中矩的产品，{product_name}{feature}{neutral_point}，没有特别之处",
                "普普通通，{product_name}{feature}{neutral_point}，没什么亮点",
                "就这样吧，{product_name}{feature}{neutral_point}，无功无过",
                "符合预期，{product_name}{feature}{neutral_point}，没惊喜",
                "还行，{product_name}{feature}{neutral_point}，给个中评",
                "一般，{product_name}{feature}{neutral_point}，不算差",
                "凑合用，{product_name}{feature}{neutral_point}，对得起价格",
                "没啥感觉，{product_name}{feature}{neutral_point}，就这样",
                "正常水平，{product_name}{feature}{neutral_point}，还行",
                "过得去，{product_name}{feature}{neutral_point}，能用",
                "没毛病，{product_name}{feature}{neutral_point}，也没惊喜",
                "就这样吧，{product_name}{feature}{neutral_point}，还行",
            ],
            "负面": [
                "太失望了！{product_name}{feature}{negative_point}，准备退货",
                "物流太慢，等了5天才到，而且{product_name}{feature}{negative_point}",
                "质量堪忧，{product_name}{feature}{negative_point}，用了两天就坏了",
                "客服态度差，问问题半天不回，{product_name}{feature}{negative_point}",
                "包装破损，{product_name}{feature}{negative_point}，有明显的划痕",
                "和描述不符，{product_name}{feature}{negative_point}，感觉被骗了",
                "价格虚高，{product_name}{feature}{negative_point}，不值这个价",
                "发热严重，{product_name}{feature}{negative_point}，烫手",
                "噪音很大，{product_name}{feature}{negative_point}，影响使用",
                "卡顿明显，{product_name}{feature}{negative_point}，根本没法用",
                "有瑕疵，{product_name}{feature}{negative_point}，像是二手的",
                "续航太差，{product_name}{feature}{negative_point}，半天就没电了",
                "做工粗糙，{product_name}{feature}{negative_point}，边角都没处理好",
                "气味很大，{product_name}{feature}{negative_point}，放了好久都散不掉",
                "系统有bug，{product_name}{feature}{negative_point}，经常闪退",
                "配送员态度恶劣，{product_name}{feature}{negative_point}，差评",
                "颜色发错了，{product_name}{feature}{negative_point}，客服还不给换",
                "千万别买，{product_name}{feature}{negative_point}，太坑了",
                "后悔死了，{product_name}{feature}{negative_point}，浪费钱",
                "差评，{product_name}{feature}{negative_point}，再也不来了",
                "太差了，{product_name}{feature}{negative_point}，没法用",
                "质量太差，{product_name}{feature}{negative_point}，用几天就坏了",
                "很失望，{product_name}{feature}{negative_point}，不值这个价",
                "太垃圾了，{product_name}{feature}{negative_point}，退货",
                "问题很多，{product_name}{feature}{negative_point}，不建议购买",
                "有质量问题，{product_name}{feature}{negative_point}，联系客服也没用",
                "包装太简陋，{product_name}{feature}{negative_point}，都压坏了",
                "物流太差，{product_name}{feature}{negative_point}，等了好久",
                "客服不理人，{product_name}{feature}{negative_point}，差评",
            ]
        }

        # 正面评价点
        self.positive_points = [
            "非常满意", "超出预期", "物美价廉", "很实用", "颜值高",
            "做工精细", "手感舒适", "运行流畅", "清晰度高", "续航持久",
            "性价比超高", "正品保证", "物流神速", "客服热情", "包装严实",
            "功能强大", "操作简单", "反应灵敏", "质量杠杠的", "物超所值",
            "没有异味", "大小合适", "安装方便", "声音清晰", "画面细腻",
            "完全不卡", "很轻便", "材质好", "很耐用", "非常喜欢",
            "很惊艳", "很完美", "很贴心", "很人性化", "很智能",
            "很稳定", "很流畅", "很丝滑", "很细腻", "很精致"
        ]

        # 中性评价点
        self.neutral_points = [
            "还行吧", "一般般", "凑合用", "无功无过", "没惊喜也没失望",
            "符合预期", "中规中矩", "普普通通", "不算差也不算好", "就这样",
            "能用", "够用", "说得过去", "没什么特别的", "还行",
            "正常水平", "一分钱一分货", "对得起价格", "没啥毛病", "暂时没发现问题",
            "过得去", "凑合", "还好", "还可以", "差不多"
        ]

        # 负面评价点
        self.negative_points = [
            "太差了", "很失望", "质量堪忧", "有瑕疵", "做工粗糙",
            "不值这个价", "和描述不符", "发热严重", "噪音大", "卡顿",
            "续航差", "容易坏", "有异味", "颜色不对", "尺寸不合适",
            "客服态度差", "物流太慢", "包装破损", "像二手的", "假货",
            "系统有bug", "经常死机", "充不进电", "信号差", "屏幕有坏点",
            "按键失灵", "接口松动", "掉漆", "生锈", "变形",
            "有划痕", "有裂纹", "有破损", "缺配件", "说明书看不懂"
        ]

        # 特征词（按类别）
        self.features = {
            "手机": ["屏幕", "电池", "相机", "系统", "运行速度", "外观", "手感", "拍照", "续航", "充电", "信号", "音质",
                     "人脸识别", "指纹解锁"],
            "笔记本": ["屏幕", "键盘", "散热", "性能", "续航", "重量", "做工", "风扇", "接口", "速度", "音响", "摄像头",
                       "触控板", "开机速度"],
            "默认": ["质量", "外观", "性能", "做工", "材质", "手感", "效果", "体验", "功能", "设计", "大小", "重量",
                     "颜色", "包装"]
        }

        # 否定表达
        self.negations = ["不", "没", "无", "非", "别", "莫", "勿", "未", "并非"]

        # 程度词
        self.degree_words = ["太", "很", "非常", "特别", "超级", "极其", "有点", "有些", "比较", "相对", "挺", "蛮",
                             "相当", "十分"]

        # 真实评论中的常见语气词和连接词
        self.fillers = ["感觉", "觉得", "总体来说", "整体来说", "说实话", "坦白说", "个人认为", "就我而言", "用了之后",
                        "打开一看", "试了一下", "看了一下", "体验下来", "使用感受"]

    def generate_realistic_comment(self, sentiment, product_name, category):
        """生成更真实的评论"""
        # 随机决定是否使用否定表达
        use_negation = random.random() < 0.15  # 15%的评论包含否定

        # 选择特征
        if category in self.features:
            feature = random.choice(self.features[category])
        else:
            feature = random.choice(self.features["默认"])

        # 选择评价点
        if sentiment == "正面":
            point = random.choice(self.positive_points)
            # 随机决定是否在前面加程度词
            if random.random() < 0.4:
                degree = random.choice(self.degree_words)
                point = degree + point
        elif sentiment == "中性":
            point = random.choice(self.neutral_points)
        else:  # 负面
            point = random.choice(self.negative_points)
            # 随机决定是否在前面加程度词
            if random.random() < 0.5:
                degree = random.choice(self.degree_words)
                point = degree + point

        # 随机选择模板
        template = random.choice(self.real_templates[sentiment])

        # 生成评论
        if use_negation and sentiment != "中性":
            # 插入否定表达，让评论更复杂
            neg = random.choice(self.negations)
            if random.random() < 0.5:
                comment = template.format(
                    product_name=product_name,
                    feature=feature,
                    positive_point=point if sentiment == "正面" else "",
                    neutral_point=point if sentiment == "中性" else "",
                    negative_point=point if sentiment == "负面" else ""
                )
                # 在合适位置插入否定
                if "感觉" in comment:
                    comment = comment.replace("感觉", f"感觉{neg}")
                elif "觉得" in comment:
                    comment = comment.replace("觉得", f"觉得{neg}")
                else:
                    comment = comment.replace("是", f"是{neg}")
            else:
                # 使用否定表达 + 正面/负面词
                if sentiment == "正面":
                    neg_point = f"{neg}是{point}" if neg == "不" else f"{neg}{point}"
                    comment = template.format(
                        product_name=product_name,
                        feature=feature,
                        positive_point=neg_point,
                        neutral_point="",
                        negative_point=""
                    )
                else:  # 负面
                    neg_point = f"{neg}是{point}" if neg == "不" else f"{neg}{point}"
                    comment = template.format(
                        product_name=product_name,
                        feature=feature,
                        positive_point="",
                        neutral_point="",
                        negative_point=neg_point
                    )
        else:
            comment = template.format(
                product_name=product_name,
                feature=feature,
                positive_point=point if sentiment == "正面" else "",
                neutral_point=point if sentiment == "中性" else "",
                negative_point=point if sentiment == "负面" else ""
            )

        # 随机插入语气词
        if random.random() < 0.3:
            filler = random.choice(self.fillers)
            # 随机位置插入
            parts = comment.split("，")
            if len(parts) > 1:
                insert_pos = random.randint(1, len(parts) - 1)
                parts.insert(insert_pos, filler)
                comment = "，".join(parts)

        # 清理多余的标点和空格
        comment = re.sub(r'\s+', '', comment)
        comment = re.sub(r'，+', '，', comment)
        comment = re.sub(r'。+', '。', comment)
        comment = re.sub(r'！+', '！', comment)

        return comment

    def generate_training_data(self, count=1500):
        """生成大量真实的训练数据"""
        texts = []
        labels = []

        # 更真实的分布
        distribution = {
            "正面": 0.6,  # 大部分评论是正面的
            "中性": 0.25,  # 中性评论较少
            "负面": 0.15  # 负面评论最少
        }

        for sentiment, ratio in distribution.items():
            num = int(count * ratio)
            for _ in range(num):
                product_id = random.choice(list(PRODUCT_INFO.keys()))
                product_info = PRODUCT_INFO[product_id]
                product_name = product_info["name"]
                category = product_info["category"]

                comment = self.generate_realistic_comment(sentiment, product_name, category)
                texts.append(comment)
                labels.append(sentiment)

        # 补全
        while len(texts) < count:
            sentiment = random.choice(["正面", "中性", "负面"])
            product_id = random.choice(list(PRODUCT_INFO.keys()))
            product_info = PRODUCT_INFO[product_id]
            product_name = product_info["name"]
            category = product_info["category"]

            comment = self.generate_realistic_comment(sentiment, product_name, category)
            texts.append(comment)
            labels.append(sentiment)

        # 打乱顺序
        combined = list(zip(texts, labels))
        random.shuffle(combined)
        texts, labels = zip(*combined)

        return list(texts), list(labels)

    def generate_dataset(self, product_id, count=50):
        """生成指定数量的评论（用于演示）"""
        product_info = PRODUCT_INFO.get(product_id, {"name": "未知商品", "category": "默认"})
        product_name = product_info["name"]
        category = product_info["category"]

        # 更真实的分布
        distribution = random.choice([
            {"正面": 0.7, "中性": 0.2, "负面": 0.1},  # 好评商品
            {"正面": 0.5, "中性": 0.3, "负面": 0.2},  # 普通商品
            {"正面": 0.3, "中性": 0.3, "负面": 0.4}  # 差评商品
        ])

        comments = []
        for sentiment, ratio in distribution.items():
            num = int(count * ratio)
            for _ in range(num):
                comment = self.generate_realistic_comment(sentiment, product_name, category)
                # 评分
                if sentiment == "正面":
                    score = random.choices([5, 4], weights=[0.8, 0.2])[0]
                elif sentiment == "中性":
                    score = random.choices([3, 4, 2], weights=[0.6, 0.3, 0.1])[0]
                else:
                    score = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

                # 时间
                days_ago = random.randint(0, 30)
                date = f"2026-03-{17 - days_ago:02d}"

                comments.append({
                    "评论内容": comment,
                    "评分": score,
                    "评论时间": date
                })

        # 补全
        while len(comments) < count:
            sentiment = random.choice(["正面", "中性", "负面"])
            comment = self.generate_realistic_comment(sentiment, product_name, category)

            if sentiment == "正面":
                score = random.randint(4, 5)
            elif sentiment == "中性":
                score = random.randint(2, 4)
            else:
                score = random.randint(1, 2)

            days_ago = random.randint(0, 30)
            date = f"2026-03-{17 - days_ago:02d}"

            comments.append({
                "评论内容": comment,
                "评分": score,
                "评论时间": date
            })

        random.shuffle(comments)
        return pd.DataFrame(comments)