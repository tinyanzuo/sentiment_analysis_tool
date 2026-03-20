"""
GUI组件模块 - 模型训练标签页
"""
from tkinter import *
from tkinter import ttk, messagebox


class ModelTrainingTab:
    """模型训练标签页组件"""

    def __init__(self, parent, colors, app):
        self.parent = parent
        self.colors = colors
        self.app = app
        self.frame = None

        # 需要引用的app属性
        self.train_status_label = None
        self.data_info_label = None
        self.metric_labels = {}
        self.sample_labels = {}
        self.feature_text = None
        self.feature_tab_var = None
        self.start_train_btn = None
        self.train_source_var = None

    def create(self):
        """创建模型训练标签页"""
        self.frame = Frame(self.parent, bg=self.colors['white'])
        self.parent.add(self.frame, text="🤖 模型训练")

        # ========== 第一部分：训练控制面板 ==========
        control_frame = LabelFrame(self.frame, text="⚙️ 训练控制",
                                   font=('微软雅黑', 10, 'bold'),
                                   bg=self.colors['white'], padx=10, pady=10)
        control_frame.pack(fill=X, padx=10, pady=10)

        # ----- 1.1 训练数据来源选择行 -----
        source_frame = Frame(control_frame, bg=self.colors['white'])
        source_frame.pack(fill=X, pady=5)

        Label(source_frame, text="训练数据来源:", width=12, anchor=W,
              bg=self.colors['white'], font=('微软雅黑', 9)).pack(side=LEFT)

        self.train_source_var = StringVar(value="demo")

        Radiobutton(source_frame, text="演示数据(默认)", variable=self.train_source_var,
                    value="demo", bg=self.colors['white']).pack(side=LEFT, padx=5)
        Radiobutton(source_frame, text="用户上传数据", variable=self.train_source_var,
                    value="user", bg=self.colors['white']).pack(side=LEFT, padx=5)
        Radiobutton(source_frame, text="混合训练", variable=self.train_source_var,
                    value="mixed", bg=self.colors['white']).pack(side=LEFT, padx=5)

        # ----- 1.2 数据格式说明框 -----
        format_frame = Frame(control_frame, bg=self.colors['light_bg'], relief=GROOVE, bd=1)
        format_frame.pack(fill=X, pady=5, padx=5)

        format_text = """
        📌 训练数据格式要求：
        • 文件格式：Excel(.xlsx/.xls) 或 CSV(.csv)
        • 必须包含两列：'评论内容' 和 '情感分类'
        • 情感分类支持：正面/中性/负面 或 positive/neutral/negative 或 5/4/3/2/1
        """

        Label(format_frame, text=format_text, font=('微软雅黑', 9),
              bg=self.colors['light_bg'], fg=self.colors['gray'],
              justify=LEFT).pack(anchor=W, padx=10, pady=5)

        # ----- 1.3 操作按钮组 -----
        btn_frame = Frame(control_frame, bg=self.colors['white'])
        btn_frame.pack(fill=X, pady=10)

        self.app.train_btn = Button(btn_frame, text="📤 上传训练数据",
                                    command=self.app.upload_training_data,
                                    bg=self.colors['primary'], fg='white',
                                    font=('微软雅黑', 9, 'bold'), width=15)
        self.app.train_btn.pack(side=LEFT, padx=5)

        self.start_train_btn = Button(btn_frame, text="🚀 开始训练",
                                      command=self.app.start_user_training,
                                      bg=self.colors['success'], fg='white',
                                      font=('微软雅黑', 9, 'bold'), width=12)
        self.start_train_btn.pack(side=LEFT, padx=5)

        self.app.reset_model_btn = Button(btn_frame, text="🔄 重置为演示模型",
                                          command=self.app.reset_to_demo_model,
                                          bg=self.colors['warning'], fg='white',
                                          font=('微软雅黑', 9), width=15)
        self.app.reset_model_btn.pack(side=LEFT, padx=5)

        # ----- 1.4 训练状态显示 -----
        self.train_status_label = Label(control_frame, text="训练状态: 未训练 (使用演示数据)",
                                        font=('微软雅黑', 9),
                                        bg=self.colors['light_bg'], fg=self.colors['primary'],
                                        anchor=W, padx=10, pady=5, relief=GROOVE)
        self.train_status_label.pack(fill=X, pady=5)

        # ----- 1.5 当前训练数据信息 -----
        self.data_info_label = Label(control_frame, text="当前训练数据: 1500条演示数据",
                                     font=('微软雅黑', 9),
                                     bg=self.colors['white'], fg=self.colors['gray'],
                                     anchor=W)
        self.data_info_label.pack(fill=X, pady=2)

        # 保存到app对象
        self.app.train_status_label = self.train_status_label
        self.app.data_info_label = self.data_info_label
        self.app.start_train_btn = self.start_train_btn
        self.app.train_source_var = self.train_source_var

        # ========== 第二部分：模型信息展示面板 ==========
        info_panel = Frame(self.frame, bg=self.colors['white'])
        info_panel.pack(fill=BOTH, expand=True, padx=10, pady=(5, 10))

        # ----- 2.1 左侧面板：模型性能指标和训练样本分布 -----
        left_frame = Frame(info_panel, bg=self.colors['white'], width=400)
        left_frame.pack(side=LEFT, fill=Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # 左侧上部分：模型性能指标
        Label(left_frame, text="📊 模型性能指标",
              font=('微软雅黑', 11, 'bold'),
              bg=self.colors['white'], fg=self.colors['primary']).pack(anchor=W, pady=(0, 5))

        # 指标展示框架
        self.metrics_frame = Frame(left_frame, bg=self.colors['light_bg'], relief=GROOVE, bd=1)
        self.metrics_frame.pack(fill=X, pady=(0, 10))

        metrics = [
            ("数据来源", "演示数据", self.colors['info']),
            ("模型类型", "逻辑回归", self.colors['info']),
            ("准确率", "0.904", self.colors['success']),
            ("验证集准确率", "0.910", self.colors['info']),
            ("训练样本", "1500条", self.colors['primary']),
            ("特征词", "8245个", self.colors['warning'])
        ]

        for i, (label, value, color) in enumerate(metrics):
            frame = Frame(self.metrics_frame, bg=self.colors['light_bg'])
            frame.pack(fill=X, pady=5, padx=10)

            Label(frame, text=label, width=10, anchor=W,
                  bg=self.colors['light_bg'], font=('微软雅黑', 9)).pack(side=LEFT)
            value_label = Label(frame, text=value, font=('微软雅黑', 10, 'bold'),
                                bg=self.colors['light_bg'], fg=color)
            value_label.pack(side=LEFT, padx=5)
            self.metric_labels[label] = value_label

        # 左侧下部分：训练样本分布
        Label(left_frame, text="📈 训练样本分布",
              font=('微软雅黑', 11, 'bold'),
              bg=self.colors['white'], fg=self.colors['success']).pack(anchor=W, pady=(0, 5))

        self.sample_frame = Frame(left_frame, bg=self.colors['light_bg'], relief=GROOVE, bd=1)
        self.sample_frame.pack(fill=X, pady=0)

        self.sample_labels = {}
        for label, color in [("正面", self.colors['success']),
                             ("中性", self.colors['warning']),
                             ("负面", self.colors['danger'])]:
            frame = Frame(self.sample_frame, bg=self.colors['light_bg'])
            frame.pack(fill=X, pady=5, padx=10)

            Label(frame, text=label, width=6, anchor=W,
                  bg=self.colors['light_bg'], font=('微软雅黑', 9)).pack(side=LEFT)
            value_label = Label(frame, text="0条 (0.0%)", font=('微软雅黑', 9, 'bold'),
                                bg=self.colors['light_bg'], fg=color)
            value_label.pack(side=LEFT, padx=5)
            self.sample_labels[label] = value_label

        # ----- 2.2 右侧面板：特征词重要性展示 -----
        right_frame = Frame(info_panel, bg=self.colors['white'])
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        Label(right_frame, text="🔍 最重要的特征词",
              font=('微软雅黑', 11, 'bold'),
              bg=self.colors['white'], fg=self.colors['info']).pack(anchor=W, pady=(0, 5))

        # 特征词类别切换选项卡
        feature_tab_frame = Frame(right_frame, bg=self.colors['white'])
        feature_tab_frame.pack(fill=X, pady=(0, 5))

        self.feature_tab_var = StringVar(value="正面")
        Radiobutton(feature_tab_frame, text="正面特征", variable=self.feature_tab_var,
                    value="正面", command=self.app.update_feature_display,
                    bg=self.colors['white']).pack(side=LEFT, padx=5)
        Radiobutton(feature_tab_frame, text="负面特征", variable=self.feature_tab_var,
                    value="负面", command=self.app.update_feature_display,
                    bg=self.colors['white']).pack(side=LEFT, padx=5)
        Radiobutton(feature_tab_frame, text="中性特征", variable=self.feature_tab_var,
                    value="中性", command=self.app.update_feature_display,
                    bg=self.colors['white']).pack(side=LEFT, padx=5)

        # 特征词显示文本框（带滚动条）
        self.feature_text = Text(right_frame, font=('微软雅黑', 10),
                                 wrap=WORD, height=20,
                                 bg=self.colors['light_bg'])
        feature_scroll = Scrollbar(right_frame, orient=VERTICAL, command=self.feature_text.yview)
        self.feature_text.configure(yscrollcommand=feature_scroll.set)

        self.feature_text.pack(side=LEFT, fill=BOTH, expand=True)
        feature_scroll.pack(side=RIGHT, fill=Y)

        # 保存到app对象
        self.app.metric_labels = self.metric_labels
        self.app.sample_labels = self.sample_labels
        self.app.feature_text = self.feature_text
        self.app.feature_tab_var = self.feature_tab_var