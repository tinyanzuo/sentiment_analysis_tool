"""
GUI界面模块 - 主应用程序界面
"""
import os
import threading
import queue
import pandas as pd
from tkinter import *
from tkinter import ttk, filedialog, messagebox


from config import PRODUCT_INFO, COOKIE_FILE
from selenium_crawler import JDSeleniumCrawler
from demo_generator import DemoDataGenerator
from sentiment_model import SentimentModel
from dimension_analyzer import MultiDimensionAnalyzer
from visualizer import analyze_ratio, show_chart


class JDSentimentAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("京东评论情感分析工具 v13.0 (支持用户数据训练)")
        self.root.geometry("1400x900")

        self.df = None
        self.result_df = None
        self.crawler = JDSeleniumCrawler()
        self.demo_generator = DemoDataGenerator()
        self.model = SentimentModel()
        self.dimension_analyzer = MultiDimensionAnalyzer()
        self.model_trained = False
        self.queue = queue.Queue()

        self.setup_styles()
        self.create_widgets()
        self.check_queue()

        # 启动时自动训练演示模型（不阻塞界面）
        self.status_label.config(text="正在初始化演示模型（约10秒）...")
        threading.Thread(target=self._init_demo_model, daemon=True).start()

        self.check_selenium_status()

    def _init_demo_model(self):
        """后台初始化演示模型"""
        try:
            # 生成500条演示数据快速训练
            texts, labels = self.demo_generator.generate_training_data(500)
            self.model.train_with_user_data(texts, labels)
            self.model_trained = True
            self.model.is_trained = True
            self.model.data_source = "演示数据"
            # 更新UI
            self.queue.put(('train_complete', 'demo'))
            self.queue.put(('info', "演示模型初始化完成，可直接进行情感分析"))
        except Exception as e:
            self.queue.put(('info', f"演示模型初始化失败，将使用规则判断: {str(e)}"))

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#f44336',
            'info': '#9C27B0',
            'gray': '#9e9e9e',
            'light_bg': '#f5f5f5',
            'white': '#ffffff'
        }

        style.configure('Title.TLabel', font=('微软雅黑', 12, 'bold'))
        style.configure('Heading.TLabel', font=('微软雅黑', 11, 'bold'))
        style.configure('Status.TLabel', font=('微软雅黑', 9))

        style.configure('Primary.TButton', font=('微软雅黑', 9), background=self.colors['primary'])
        style.configure('Success.TButton', font=('微软雅黑', 9), background=self.colors['success'])
        style.configure('Warning.TButton', font=('微软雅黑', 9), background=self.colors['warning'])
        style.configure('Danger.TButton', font=('微软雅黑', 9), background=self.colors['danger'])
        style.configure('Info.TButton', font=('微软雅黑', 9), background=self.colors['info'])

    def check_selenium_status(self):
        def check():
            success, msg = self.crawler.check_selenium()
            if success:
                self.queue.put(('info', "Selenium就绪"))
                self.selenium_status_label.config(text="● Selenium: 就绪", fg='green')
            else:
                self.queue.put(('info', f"Selenium未就绪: {msg}"))
                self.selenium_status_label.config(text="● Selenium: 未就绪", fg='red')

        threading.Thread(target=check, daemon=True).start()

    def create_widgets(self):
        main = Frame(self.root, bg=self.colors['light_bg'])
        main.pack(fill=BOTH, expand=True, padx=10, pady=10)

        title_frame = Frame(main, bg=self.colors['primary'], height=40)
        title_frame.pack(fill=X, pady=(0, 10))
        title_frame.pack_propagate(False)

        title_label = Label(title_frame, text="京东商品评论情感分析系统",
                            font=('微软雅黑', 14, 'bold'),
                            bg=self.colors['primary'], fg='white')
        title_label.pack(expand=True)

        input_frame = LabelFrame(main, text="📥 数据获取",
                                 font=('微软雅黑', 10, 'bold'),
                                 bg=self.colors['white'], padx=10, pady=10)
        input_frame.pack(fill=X, pady=5)

        row1 = Frame(input_frame, bg=self.colors['white'])
        row1.pack(fill=X, pady=5)

        Label(row1, text="商品ID:", width=8, bg=self.colors['white']).pack(side=LEFT)
        self.id_entry = Entry(row1, width=25, font=('微软雅黑', 9))
        self.id_entry.pack(side=LEFT, padx=5)
        self.id_entry.insert(0, "100243302695")

        Label(row1, text="快捷选择:", width=8, bg=self.colors['white']).pack(side=LEFT, padx=(20, 0))
        self.id_combo = ttk.Combobox(row1, values=list(PRODUCT_INFO.keys()), width=18)
        self.id_combo.pack(side=LEFT, padx=5)
        self.id_combo.bind('<<ComboboxSelected>>', self.on_select)

        Label(row1, text="数量:", width=4, bg=self.colors['white']).pack(side=LEFT, padx=(20, 0))
        self.count_entry = Entry(row1, width=8, font=('微软雅黑', 9))
        self.count_entry.pack(side=LEFT, padx=5)
        self.count_entry.insert(0, "100")

        row2 = Frame(input_frame, bg=self.colors['white'])
        row2.pack(fill=X, pady=10)

        mode_frame = Frame(row2, bg=self.colors['white'], relief=GROOVE, bd=1)
        mode_frame.pack(side=LEFT, padx=5)

        Label(mode_frame, text=" 模式选择 ", font=('微软雅黑', 9),
              bg=self.colors['gray'], fg='white').pack(side=LEFT, padx=5, pady=2)

        self.mode_var = StringVar(value="demo")
        Radiobutton(mode_frame, text="演示模式", variable=self.mode_var, value="demo",
                    bg=self.colors['white']).pack(side=LEFT, padx=10)
        Radiobutton(mode_frame, text="Selenium爬虫", variable=self.mode_var, value="selenium",
                    bg=self.colors['white']).pack(side=LEFT, padx=10)

        btn_frame = Frame(row2, bg=self.colors['white'])
        btn_frame.pack(side=RIGHT)

        self.crawl_btn = Button(btn_frame, text="▶ 开始获取",
                                command=self.start_crawl,
                                bg=self.colors['success'], fg='white',
                                font=('微软雅黑', 9, 'bold'), width=10)
        self.crawl_btn.pack(side=LEFT, padx=2)

        Button(btn_frame, text="📤 上传文件", command=self.upload_file,
               bg=self.colors['primary'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        Button(btn_frame, text="🗑️ 清空", command=self.clear_data,
               bg=self.colors['gray'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        row3 = Frame(input_frame, bg=self.colors['white'])
        row3.pack(fill=X, pady=5)

        Label(row3, text="进度:", bg=self.colors['white']).pack(side=LEFT)
        self.progress = ttk.Progressbar(row3, length=200, mode='determinate')
        self.progress.pack(side=LEFT, padx=5)

        self.status_label = Label(row3, text="就绪", fg=self.colors['primary'],
                                  bg=self.colors['white'], width=30, anchor=W)
        self.status_label.pack(side=LEFT, padx=10)

        self.selenium_status_label = Label(row3, text="● Selenium: 检查中...",
                                           fg='orange', bg=self.colors['white'])
        self.selenium_status_label.pack(side=LEFT, padx=20)

        Button(row3, text="清除登录", command=self.clear_login,
               bg=self.colors['warning'], fg='white',
               font=('微软雅黑', 8), width=8).pack(side=RIGHT, padx=2)

        tool_frame = Frame(main, bg=self.colors['white'], height=50)
        tool_frame.pack(fill=X, pady=5)
        tool_frame.pack_propagate(False)

        left_tools = Frame(tool_frame, bg=self.colors['white'])
        left_tools.pack(side=LEFT, padx=5, pady=8)

        self.analyze_btn = Button(left_tools, text="🧠 开始情感分析",
                                  command=self.start_analyze,
                                  bg=self.colors['success'], fg='white',
                                  font=('微软雅黑', 9, 'bold'), width=15,
                                  state=NORMAL)  # 始终可用
        self.analyze_btn.pack(side=LEFT, padx=2)

        Button(left_tools, text="📊 维度分析", command=self.show_dimension_analysis,
               bg=self.colors['info'], fg='white',
               font=('微软雅黑', 9), width=12).pack(side=LEFT, padx=2)

        Button(left_tools, text="📈 图表统计", command=self.show_chart,
               bg=self.colors['warning'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        Label(left_tools, text="模型:", bg=self.colors['white'], font=('微软雅黑', 9)).pack(side=LEFT, padx=(20, 2))
        self.model_var = StringVar(value="logistic")
        self.model_combo = ttk.Combobox(left_tools, textvariable=self.model_var, width=12, state="readonly")
        self.model_combo['values'] = ['logistic', 'naive_bayes', 'svm', 'random_forest']
        self.model_combo.pack(side=LEFT, padx=2)
        self.model_combo.bind('<<ComboboxSelected>>', self.on_model_selected)

        right_tools = Frame(tool_frame, bg=self.colors['white'])
        right_tools.pack(side=RIGHT, padx=5, pady=8)

        Button(right_tools, text="🔍 诊断选中", command=self.explain_selected,
               bg=self.colors['info'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        Button(right_tools, text="📋 批量诊断", command=self.batch_diagnose,
               bg=self.colors['primary'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        Button(right_tools, text="📥 导出Excel", command=self.export_excel,
               bg=self.colors['success'], fg='white',
               font=('微软雅黑', 9), width=10).pack(side=LEFT, padx=2)

        self.count_label = Label(tool_frame, text="总评论: 0",
                                 font=('微软雅黑', 10, 'bold'),
                                 bg=self.colors['primary'], fg='white',
                                 padx=15, pady=2)
        self.count_label.pack(side=RIGHT, padx=10)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=BOTH, expand=True, pady=5)

        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('微软雅黑', 9), padding=[10, 2])

        self.create_data_tab()
        self.create_stats_tab()
        self.create_dimension_tab()
        self.create_model_tab()

    def on_model_selected(self, event):
        selected_model = self.model_var.get()
        self.model.set_model_type(selected_model)
        self.status_label.config(text=f"已选择模型: {self.model.available_models[selected_model]}")
        if self.model.is_trained:
            if messagebox.askyesno("提示", "是否使用新选择的模型重新训练？"):
                self.start_training()

    def create_data_tab(self):
        self.data_frame = Frame(self.notebook, bg=self.colors['white'])
        self.notebook.add(self.data_frame, text="📋 评论数据")

        columns = ('评论内容', '评分', '情感分类', '评论时间')
        self.tree = ttk.Treeview(self.data_frame, columns=columns, show='headings', height=18)

        col_configs = [
            ('评论内容', 500, 'w'),
            ('评分', 60, 'center'),
            ('情感分类', 100, 'center'),
            ('评论时间', 150, 'center')
        ]

        for col, width, anchor in col_configs:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(self.data_frame, orient=VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self.data_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.data_frame.grid_rowconfigure(0, weight=1)
        self.data_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self.show_explanation_popup)

    def create_stats_tab(self):
        self.stats_frame = Frame(self.notebook, bg=self.colors['white'])
        self.notebook.add(self.stats_frame, text="📊 统计分析")

        left_frame = Frame(self.stats_frame, bg=self.colors['white'], width=400)
        left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)
        left_frame.pack_propagate(False)

        right_frame = Frame(self.stats_frame, bg=self.colors['white'])
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        Label(left_frame, text="📌 情感分布统计",
              font=('微软雅黑', 11, 'bold'),
              bg=self.colors['white'], fg=self.colors['primary']).pack(anchor=W, pady=5)

        columns = ('情感类型', '评论数量', '占比(%)')
        self.stats_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=120, anchor='center')

        stats_vsb = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_vsb.set)

        self.stats_tree.pack(side=LEFT, fill=BOTH, expand=True)
        stats_vsb.pack(side=RIGHT, fill=Y)

        Label(right_frame, text="⚡ 快速操作",
              font=('微软雅黑', 11, 'bold'),
              bg=self.colors['white'], fg=self.colors['success']).pack(anchor=W, pady=5)

        btn_grid = Frame(right_frame, bg=self.colors['white'])
        btn_grid.pack(fill=X, pady=10)

        buttons = [
            ("📈 显示详细图表", self.show_chart, self.colors['info']),
            ("📥 导出统计报表", self.export_excel, self.colors['success']),
            ("🔄 刷新统计", self.update_stats, self.colors['primary']),
            ("📊 维度分析", self.show_dimension_analysis, self.colors['warning'])
        ]

        for i, (text, cmd, color) in enumerate(buttons):
            btn = Button(btn_grid, text=text, command=cmd,
                         bg=color, fg='white', font=('微软雅黑', 9),
                         width=15, height=2)
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky='ew')
            btn_grid.grid_columnconfigure(i % 2, weight=1)

    def create_dimension_tab(self):
        self.dimension_frame = Frame(self.notebook, bg=self.colors['white'])
        self.notebook.add(self.dimension_frame, text="📏 维度分析")

        tool_bar = Frame(self.dimension_frame, bg=self.colors['light_bg'], height=40)
        tool_bar.pack(fill=X, padx=5, pady=5)
        tool_bar.pack_propagate(False)

        Button(tool_bar, text="🔄 刷新维度分析", command=self.update_dimension_analysis,
               bg=self.colors['info'], fg='white',
               font=('微软雅黑', 9), width=15).pack(side=LEFT, padx=5, pady=5)

        Button(tool_bar, text="📊 导出维度报表", command=self.export_dimension_report,
               bg=self.colors['success'], fg='white',
               font=('微软雅黑', 9), width=15).pack(side=LEFT, padx=5, pady=5)

        Label(tool_bar, text="双击维度行查看详细评论",
              font=('微软雅黑', 9, 'italic'),
              bg=self.colors['light_bg'], fg=self.colors['gray']).pack(side=RIGHT, padx=10)

        columns = ('维度', '正面数', '中性数', '负面数', '未提及', '好评率', '差评率')
        self.dim_tree = ttk.Treeview(self.dimension_frame, columns=columns, show='headings', height=12)

        col_widths = [120, 70, 70, 70, 70, 100, 100]
        for col, width in zip(columns, col_widths):
            self.dim_tree.heading(col, text=col)
            self.dim_tree.column(col, width=width, anchor='center')

        dim_vsb = ttk.Scrollbar(self.dimension_frame, orient=VERTICAL, command=self.dim_tree.yview)
        dim_hsb = ttk.Scrollbar(self.dimension_frame, orient=HORIZONTAL, command=self.dim_tree.xview)
        self.dim_tree.configure(yscrollcommand=dim_vsb.set, xscrollcommand=dim_hsb.set)

        self.dim_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        dim_vsb.pack(side=RIGHT, fill=Y)
        dim_hsb.pack(side=BOTTOM, fill=X)

        self.dim_tree.bind('<Double-1>', self.show_dimension_comments)

        info_frame = Frame(self.dimension_frame, bg=self.colors['light_bg'], height=60)
        info_frame.pack(fill=X, padx=5, pady=5)
        info_frame.pack_propagate(False)

        info_text = """
        📌 维度说明：基于关键词匹配技术，自动识别评论中涉及的各个维度
        发货速度 | 物流速度 | 客服态度 | 包装质量 | 商品质量 | 性价比
        """
        Label(info_frame, text=info_text, font=('微软雅黑', 9),
              bg=self.colors['light_bg'], fg=self.colors['gray'],
              justify=LEFT).pack(anchor=W, padx=10, pady=10)

    def create_model_tab(self):
        """创建模型信息标签页 - 添加训练数据上传功能"""
        from gui_components import ModelTrainingTab

        # 创建模型训练标签页组件
        self.model_tab = ModelTrainingTab(self.notebook, self.colors, self)
        self.model_tab.create()

    def on_select(self, event):
        selected = self.id_combo.get()
        if selected in PRODUCT_INFO:
            self.id_entry.delete(0, END)
            self.id_entry.insert(0, selected)

    def clear_login(self):
        if os.path.exists(COOKIE_FILE):
            os.remove(COOKIE_FILE)
            messagebox.showinfo("成功", "登录状态已清除")
        else:
            messagebox.showinfo("提示", "没有保存的登录状态")

    def start_training(self):
        """开始训练演示模型"""

        def train():
            def progress_cb(value, msg):
                self.queue.put(('train_progress', (value, msg)))

            # 生成1500条演示数据
            texts, labels = self.demo_generator.generate_training_data(1500)
            self.model.train_with_user_data(texts, labels, progress_cb)
            self.queue.put(('train_complete', 'demo'))

        self.status_label.config(text="初始化模型（生成1500条训练数据）...")
        threading.Thread(target=train, daemon=True).start()

    def start_crawl(self):
        mode = self.mode_var.get()
        product_id = self.id_entry.get().strip()

        if not product_id:
            messagebox.showwarning("提示", "请输入商品ID")
            return

        try:
            target_count = int(self.count_entry.get())
            if target_count < 1:
                target_count = 100
            elif target_count > 1000:
                if not messagebox.askyesno("提示", f"爬取{target_count}条可能需要较长时间，是否继续？"):
                    return
        except:
            target_count = 100

        self.crawl_btn.config(state=DISABLED, text="获取中...")
        self.progress['value'] = 0

        def crawl():
            try:
                if mode == 'demo':
                    self.queue.put(('progress_msg', f"生成{target_count}条演示数据..."))
                    df = self.demo_generator.generate_dataset(product_id, target_count)
                    self.queue.put(('data_loaded', df))
                else:
                    self.queue.put(('progress_msg', f"爬取商品{product_id}的评论..."))
                    df = self.crawler.crawl(product_id, target_count,
                                            lambda msg: self.queue.put(('progress_msg', msg)))

                    if df is not None and not df.empty:
                        self.queue.put(('data_loaded', df))
                    else:
                        self.queue.put(('info', "爬虫未获取到数据"))

            except Exception as e:
                self.queue.put(('error', f"获取失败：{str(e)}"))

        threading.Thread(target=crawl, daemon=True).start()

    def upload_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel", "*.xlsx *.xls"), ("CSV", "*.csv")]
        )
        if not path:
            return

        def load():
            try:
                if path.endswith('.csv'):
                    df = pd.read_csv(path, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(path)

                if '评论内容' not in df.columns:
                    for col in ['评论', 'content', '内容']:
                        if col in df.columns:
                            df.rename(columns={col: '评论内容'}, inplace=True)
                            break

                self.queue.put(('data_loaded', df))
            except Exception as e:
                self.queue.put(('error', f"读取失败：{str(e)}"))

        threading.Thread(target=load, daemon=True).start()

    def start_analyze(self):
        """开始情感分析"""
        if self.df is None or self.df.empty:
            messagebox.showwarning("提示", "请先获取数据")
            return

        # 检查模型是否已训练
        if not self.model.is_trained:
            result = messagebox.askyesno("模型未就绪",
                                         "演示模型尚未初始化完成，将使用规则判断（准确率较低）。\n是否继续？\n\n" +
                                         "选择'是'：立即分析（使用规则）\n" +
                                         "选择'否'：等待模型初始化完成")
            if not result:
                return

        self.analyze_btn.config(state=DISABLED, text="分析中...")
        self.progress['value'] = 0

        def analyze():
            try:
                texts = self.df['评论内容'].tolist()
                self.queue.put(('progress_msg', f"开始分析 {len(texts)} 条评论..."))

                sentiments = self.model.predict_batch(texts)

                result_df = self.df.copy()
                result_df['情感分类'] = sentiments

                self.queue.put(('analyze_complete', result_df))
            except Exception as e:
                self.queue.put(('error', f"分析失败：{str(e)}"))

        threading.Thread(target=analyze, daemon=True).start()

    def explain_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一条评论")
            return

        item = self.tree.item(selection[0])
        values = item['values']
        comment = values[0]
        if len(comment) > 60 and '...' in comment:
            if self.result_df is not None:
                for _, row in self.result_df.iterrows():
                    if row['评论内容'].startswith(comment.replace('...', '')):
                        comment = row['评论内容']
                        break

        explanation = self.model.explain_prediction(comment)
        dimension_result = self.dimension_analyzer.analyze(comment)
        self.show_explanation_window(comment, explanation, dimension_result)

    def batch_diagnose(self):
        if self.result_df is None or self.result_df.empty:
            messagebox.showinfo("提示", "没有数据可供诊断")
            return

        diag_win = Toplevel(self.root)
        diag_win.title("批量诊断结果")
        diag_win.geometry("800x600")

        text_area = Text(diag_win, font=('微软雅黑', 10), wrap=WORD)
        scrollbar = Scrollbar(diag_win, orient=VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)

        text_area.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=RIGHT, fill=Y)

        text_area.insert('end', "🔍 可疑评论诊断报告\n", 'title')
        text_area.insert('end', "=" * 60 + "\n\n")

        suspicious_count = 0

        for idx, row in self.result_df.iterrows():
            comment = row['评论内容']
            pred_sentiment = row['情感分类']

            explanation = self.model.explain_prediction(comment)

            is_suspicious = False
            reasons = []

            strong_neg = ['差', '烂', '垃圾', '问题', '坏', '退货', '破损']
            found_neg = [w for w in strong_neg if w in comment]
            if found_neg and pred_sentiment == '正面':
                is_suspicious = True
                reasons.append(f"包含强负面词{found_neg}但被判断为正面")

            strong_pos = ['好', '棒', '满意', '推荐', '值', '不错']
            found_pos = [w for w in strong_pos if w in comment]
            if found_pos and pred_sentiment == '负面':
                is_suspicious = True
                reasons.append(f"包含强正面词{found_pos}但被判断为负面")

            if is_suspicious:
                suspicious_count += 1
                text_area.insert('end', f"【可疑评论 #{suspicious_count}】\n")
                text_area.insert('end', f"评论：{comment[:100]}...\n")
                text_area.insert('end', f"预测结果：{pred_sentiment}\n")
                text_area.insert('end', f"可疑原因：{', '.join(reasons)}\n")

                if 'scores' in explanation:
                    text_area.insert('end',
                                     f"概率分布：正面{explanation['scores']['正面']:.2f}，中性{explanation['scores']['中性']:.2f}，负面{explanation['scores']['负面']:.2f}\n")

                text_area.insert('end', "-" * 50 + "\n\n")

        if suspicious_count == 0:
            text_area.insert('end', "✓ 未发现可疑评论，所有预测看起来合理！\n")

        text_area.tag_configure('title', font=('微软雅黑', 12, 'bold'), foreground='#2c3e50')
        text_area.config(state=DISABLED)

    def show_dimension_analysis(self):
        if self.result_df is None or self.result_df.empty:
            messagebox.showinfo("提示", "请先进行情感分析")
            return

        self.update_dimension_analysis()
        self.notebook.select(2)

    def update_dimension_analysis(self):
        if self.result_df is None or self.result_df.empty:
            return

        for item in self.dim_tree.get_children():
            self.dim_tree.delete(item)

        dimension_stats = self.dimension_analyzer.get_dimension_stats(self.result_df)

        if not dimension_stats:
            return

        for dim, stats in dimension_stats.items():
            tags = ()
            if stats['正面率'] > stats['负面率']:
                tags = ('positive',)
            elif stats['负面率'] > stats['正面率']:
                tags = ('negative',)

            self.dim_tree.insert('', 'end', values=(
                dim,
                stats['正面'],
                stats['中性'],
                stats['负面'],
                stats['未提及'],
                f"{stats['正面率']:.1f}%",
                f"{stats['负面率']:.1f}%"
            ), tags=tags)

        self.dim_tree.tag_configure('positive', background='#e8f5e8')
        self.dim_tree.tag_configure('negative', background='#ffe8e8')

        self.current_dimension_stats = dimension_stats

    def show_dimension_comments(self, event):
        selection = self.dim_tree.selection()
        if not selection:
            return

        item = self.dim_tree.item(selection[0])
        values = item['values']
        dimension = values[0]

        win = Toplevel(self.root)
        win.title(f"【{dimension}】相关评论")
        win.geometry("800x500")

        notebook = ttk.Notebook(win)
        notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        pos_frame = Frame(notebook)
        notebook.add(pos_frame, text=f"正面 ({self.current_dimension_stats[dimension]['正面']})")

        pos_text = Text(pos_frame, font=('微软雅黑', 10), wrap=WORD)
        pos_scroll = Scrollbar(pos_frame, orient=VERTICAL, command=pos_text.yview)
        pos_text.configure(yscrollcommand=pos_scroll.set)

        pos_text.pack(side=LEFT, fill=BOTH, expand=True)
        pos_scroll.pack(side=RIGHT, fill=Y)

        neg_frame = Frame(notebook)
        notebook.add(neg_frame, text=f"负面 ({self.current_dimension_stats[dimension]['负面']})")

        neg_text = Text(neg_frame, font=('微软雅黑', 10), wrap=WORD)
        neg_scroll = Scrollbar(neg_frame, orient=VERTICAL, command=neg_text.yview)
        neg_text.configure(yscrollcommand=neg_scroll.set)

        neg_text.pack(side=LEFT, fill=BOTH, expand=True)
        neg_scroll.pack(side=RIGHT, fill=Y)

        neu_frame = Frame(notebook)
        notebook.add(neu_frame, text=f"中性 ({self.current_dimension_stats[dimension]['中性']})")

        neu_text = Text(neu_frame, font=('微软雅黑', 10), wrap=WORD)
        neu_scroll = Scrollbar(neu_frame, orient=VERTICAL, command=neu_text.yview)
        neu_text.configure(yscrollcommand=neu_scroll.set)

        neu_text.pack(side=LEFT, fill=BOTH, expand=True)
        neu_scroll.pack(side=RIGHT, fill=Y)

        for idx, row in self.result_df.iterrows():
            comment = row['评论内容']
            result = self.dimension_analyzer.analyze(comment)

            if result[dimension]['sentiment'] != '未提及':
                sentiment = result[dimension]['sentiment']
                keywords = result[dimension]['keywords'][sentiment]
                keyword_text = f" [关键词: {' '.join(keywords)}]" if keywords else ""

                if sentiment == '正面':
                    pos_text.insert('end', f"• {comment}{keyword_text}\n\n")
                elif sentiment == '负面':
                    neg_text.insert('end', f"• {comment}{keyword_text}\n\n")
                else:
                    neu_text.insert('end', f"• {comment}{keyword_text}\n\n")

        pos_text.config(state=DISABLED)
        neg_text.config(state=DISABLED)
        neu_text.config(state=DISABLED)

    def export_dimension_report(self):
        if self.result_df is None or self.result_df.empty:
            messagebox.showinfo("提示", "没有数据可供导出")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        if not path:
            return

        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                self.result_df.to_excel(writer, sheet_name='原始数据', index=False)

                stats = analyze_ratio(self.result_df)
                stats.to_excel(writer, sheet_name='情感统计', index=False)

                dimension_stats = self.dimension_analyzer.get_dimension_stats(self.result_df)
                dim_rows = []
                for dim, st in dimension_stats.items():
                    dim_rows.append({
                        '维度': dim,
                        '正面数': st['正面'],
                        '中性数': st['中性'],
                        '负面数': st['负面'],
                        '未提及': st['未提及'],
                        '总提及': st['总提及'],
                        '正面率(%)': st['正面率'],
                        '负面率(%)': st['负面率'],
                        '好评率(%)': st['好评率']
                    })
                pd.DataFrame(dim_rows).to_excel(writer, sheet_name='维度统计', index=False)

                for dim in dimension_stats.keys():
                    dim_comments = []
                    for idx, row in self.result_df.iterrows():
                        result = self.dimension_analyzer.analyze(row['评论内容'])
                        if result[dim]['sentiment'] != '未提及':
                            dim_comments.append({
                                '评论内容': row['评论内容'],
                                '情感分类': row['情感分类'],
                                '维度情感': result[dim]['sentiment'],
                                '维度关键词': ','.join(result[dim]['keywords'][result[dim]['sentiment']])
                            })
                    if dim_comments:
                        pd.DataFrame(dim_comments).to_excel(writer, sheet_name=f'{dim}详情', index=False)

            messagebox.showinfo("成功", f"维度报告已导出到：{path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def show_explanation_popup(self, event):
        self.explain_selected()

    def show_explanation_window(self, comment, explanation, dimension_result=None):
        win = Toplevel(self.root)
        win.title("情感分析诊断报告")
        win.geometry("850x750")

        notebook = ttk.Notebook(win)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)

        diag_frame = Frame(notebook)
        notebook.add(diag_frame, text="诊断结果")

        Label(diag_frame, text="📝 评论内容：", font=('微软雅黑', 10, 'bold')).pack(anchor=W, padx=10, pady=5)
        comment_text = Text(diag_frame, height=4, width=70, font=('微软雅黑', 10), wrap=WORD)
        comment_text.pack(padx=10, pady=5, fill=X)
        comment_text.insert('1.0', comment)
        comment_text.config(state=DISABLED)

        result_frame = Frame(diag_frame)
        result_frame.pack(fill=X, padx=10, pady=10)

        Label(result_frame, text="🎯 预测结果：", font=('微软雅黑', 10, 'bold')).pack(side=LEFT)

        pred = explanation.get('sentiment', '未知')
        if pred == '正面':
            color = 'green'
        elif pred == '负面':
            color = 'red'
        else:
            color = 'orange'

        Label(result_frame, text=pred, font=('微软雅黑', 12, 'bold'),
              fg=color).pack(side=LEFT, padx=10)

        Label(result_frame, text=f"（{explanation.get('method', '规则匹配')}）",
              font=('微软雅黑', 9)).pack(side=LEFT)

        if 'scores' in explanation:
            score_frame = LabelFrame(diag_frame, text="📊 概率分布", font=('微软雅黑', 10, 'bold'))
            score_frame.pack(fill=X, padx=10, pady=10)

            for label, score in explanation['scores'].items():
                frame = Frame(score_frame)
                frame.pack(fill=X, padx=10, pady=2)

                Label(frame, text=f"{label}：", width=6).pack(side=LEFT)

                progress_width = int(score * 200)
                if label == '正面':
                    bar_color = 'green'
                elif label == '负面':
                    bar_color = 'red'
                else:
                    bar_color = 'orange'

                progress_canvas = Canvas(frame, width=200, height=20, bg='#e0e0e0')
                progress_canvas.pack(side=LEFT, padx=5)
                progress_canvas.create_rectangle(0, 0, progress_width, 20, fill=bar_color, width=0)

                Label(frame, text=f"{score:.2f}").pack(side=LEFT)

        if dimension_result:
            dim_frame = Frame(notebook)
            notebook.add(dim_frame, text="维度分析")

            dim_columns = ('维度', '情感倾向', '置信度', '关键词')
            dim_tree = ttk.Treeview(dim_frame, columns=dim_columns, show='headings', height=10)

            for col in dim_columns:
                dim_tree.heading(col, text=col)

            dim_tree.column('维度', width=120)
            dim_tree.column('情感倾向', width=100)
            dim_tree.column('置信度', width=80)
            dim_tree.column('关键词', width=300)

            dim_vsb = ttk.Scrollbar(dim_frame, orient=VERTICAL, command=dim_tree.yview)
            dim_tree.configure(yscrollcommand=dim_vsb.set)

            dim_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
            dim_vsb.pack(side=RIGHT, fill=Y)

            for dim, result in dimension_result.items():
                if result['sentiment'] != '未提及':
                    if result['sentiment'] == '正面':
                        tag = 'positive'
                    elif result['sentiment'] == '负面':
                        tag = 'negative'
                    else:
                        tag = 'neutral'

                    keywords = result['keywords'][result['sentiment']]
                    keyword_str = ' '.join(keywords) if keywords else '-'

                    dim_tree.insert('', 'end', values=(
                        dim,
                        result['sentiment'],
                        f"{result['confidence']:.2f}",
                        keyword_str
                    ), tags=(tag,))

            dim_tree.tag_configure('positive', background='#e8f5e8')
            dim_tree.tag_configure('negative', background='#ffe8e8')
            dim_tree.tag_configure('neutral', background='#fff4e8')

            if not dim_tree.get_children():
                Label(dim_frame, text="未匹配到任何维度关键词", font=('微软雅黑', 12)).pack(pady=20)

        word_frame = Frame(notebook)
        notebook.add(word_frame, text="词语贡献分析")

        columns = ('词语', '权重', '贡献度')
        tree = ttk.Treeview(word_frame, columns=columns, show='headings', height=20)

        tree.heading('词语', text='词语')
        tree.heading('权重', text='TF-IDF权重')
        tree.heading('贡献度', text='贡献度')

        tree.column('词语', width=200)
        tree.column('权重', width=100)
        tree.column('贡献度', width=150)

        vsb = ttk.Scrollbar(word_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        vsb.pack(side=RIGHT, fill=Y)

        if 'word_contributions' in explanation:
            for wc in explanation['word_contributions']:
                tree.insert('', 'end', values=(
                    wc['word'],
                    f"{wc['value']:.3f}",
                    f"{wc['value']:.3f}"
                ))

    def check_queue(self):
        try:
            while True:
                task, data = self.queue.get_nowait()

                if task == 'train_progress':
                    value, msg = data
                    self.progress['value'] = value
                    self.status_label.config(text=msg)

                elif task == 'train_complete':
                    data_source = data if data else 'demo'
                    self.model_trained = True
                    self.model.is_trained = True  # 确保模型状态为已训练

                    # 情感分析按钮始终可用
                    self.analyze_btn.config(state=NORMAL, text="🧠 开始情感分析")
                    if hasattr(self, 'start_train_btn'):
                        self.start_train_btn.config(state=NORMAL, text="🚀 开始训练")

                    self.update_model_info()

                    if data_source == 'user':
                        self.status_label.config(text=f"用户数据训练完成，准确率：{self.model.accuracy:.4f}")
                        self.train_status_label.config(text=f"训练完成！使用用户数据，准确率：{self.model.accuracy:.4f}",
                                                       fg=self.colors['success'])
                    elif data_source == 'mixed':
                        self.status_label.config(text=f"混合训练完成，准确率：{self.model.accuracy:.4f}")
                        self.train_status_label.config(text=f"训练完成！使用混合数据，准确率：{self.model.accuracy:.4f}",
                                                       fg=self.colors['success'])
                    else:
                        self.status_label.config(text="演示模型就绪，可直接进行情感分析")
                        self.train_status_label.config(text="演示模型已就绪（可直接使用）", fg=self.colors['success'])

                elif task == 'progress_msg':
                    self.status_label.config(text=data)

                elif task == 'data_loaded':
                    self.df = data
                    self.show_data(data)
                    self.progress['value'] = 100
                    self.status_label.config(text=f"加载 {len(data)} 条评论")
                    self.count_label.config(text=f"总评论: {len(data)}")
                    self.crawl_btn.config(state=NORMAL, text="▶ 开始获取")

                    # 提示用户可以分析
                    if self.model.is_trained:
                        messagebox.showinfo("提示", f"数据加载完成！共{len(data)}条评论\n点击'开始情感分析'即可分析。")
                    else:
                        messagebox.showinfo("提示", "数据加载完成。演示模型正在初始化，稍后即可分析。")

                elif task == 'analyze_complete':
                    self.result_df = data
                    self.show_data(data)
                    self.update_stats()
                    self.update_dimension_analysis()
                    self.analyze_btn.config(state=NORMAL, text="🧠 开始情感分析")
                    self.progress['value'] = 100
                    self.status_label.config(text="分析完成")
                    messagebox.showinfo("完成", f"分析完成！共{len(data)}条评论")

                elif task == 'error':
                    messagebox.showerror("错误", data)
                    self.status_label.config(text="错误")
                    self.progress['value'] = 0
                    self.crawl_btn.config(state=NORMAL, text="▶ 开始获取")
                    self.analyze_btn.config(state=NORMAL, text="🧠 开始情感分析")
                    if hasattr(self, 'start_train_btn'):
                        self.start_train_btn.config(state=NORMAL, text="🚀 开始训练")

                elif task == 'info':
                    messagebox.showinfo("信息", data)

        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def show_data(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for _, row in df.iterrows():
            content = str(row['评论内容'])
            if len(content) > 60:
                content = content[:60] + '...'

            sentiment = row.get('情感分类', '')
            if sentiment == '正面':
                tag = 'positive'
            elif sentiment == '负面':
                tag = 'negative'
            else:
                tag = 'neutral'

            values = (
                content,
                row.get('评分', ''),
                sentiment,
                row.get('评论时间', '')
            )
            self.tree.insert('', 'end', values=values, tags=(tag,))

        self.tree.tag_configure('positive', background='#e8f5e8')
        self.tree.tag_configure('negative', background='#ffe8e8')
        self.tree.tag_configure('neutral', background='#fff4e8')

    def update_stats(self):
        if self.result_df is None:
            return

        stats = analyze_ratio(self.result_df)

        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        for _, row in stats.iterrows():
            self.stats_tree.insert('', 'end', values=(
                row['情感类型'],
                row['评论数量'],
                f"{row['占比(%)']}%"
            ))

    def show_chart(self):
        if self.result_df is None:
            messagebox.showwarning("提示", "请先进行分析")
            return

        stats = analyze_ratio(self.result_df)
        dimension_stats = self.dimension_analyzer.get_dimension_stats(
            self.result_df) if self.result_df is not None else None
        show_chart(stats, dimension_stats=dimension_stats, current_df=self.result_df)

    def export_excel(self):
        if self.result_df is None:
            messagebox.showwarning("提示", "无数据")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        if path:
            try:
                self.result_df.to_excel(path, index=False)
                messagebox.showinfo("成功", f"导出成功：{path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def clear_data(self):
        if messagebox.askyesno("确认", "确定清空所有数据？"):
            self.df = None
            self.result_df = None
            for item in self.tree.get_children():
                self.tree.delete(item)
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            for item in self.dim_tree.get_children():
                self.dim_tree.delete(item)
            self.count_label.config(text="总评论: 0")
            self.status_label.config(text="已清空")

    def upload_training_data(self):
        path = filedialog.askopenfilename(
            title="选择训练数据文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not path:
            return

        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path, encoding='utf-8-sig')
            else:
                df = pd.read_excel(path)

            preview_win = Toplevel(self.root)
            preview_win.title("数据预览")
            preview_win.geometry("800x500")

            Label(preview_win, text="请确认数据列映射关系",
                  font=('微软雅黑', 12, 'bold')).pack(pady=10)

            preview_frame = Frame(preview_win)
            preview_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

            columns = list(df.columns)
            preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)

            for col in columns:
                preview_tree.heading(col, text=col)
                preview_tree.column(col, width=150, anchor='w')

            for i, row in df.head(10).iterrows():
                values = [str(row[col])[:50] for col in columns]
                preview_tree.insert('', 'end', values=values)

            preview_tree.pack(side=LEFT, fill=BOTH, expand=True)

            vsb = ttk.Scrollbar(preview_frame, orient=VERTICAL, command=preview_tree.yview)
            preview_tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side=RIGHT, fill=Y)

            mapping_frame = Frame(preview_win)
            mapping_frame.pack(fill=X, padx=10, pady=10)

            Label(mapping_frame, text="评论内容列:", font=('微软雅黑', 9)).pack(side=LEFT, padx=5)
            content_col_var = StringVar(value=df.columns[0] if len(df.columns) > 0 else "")
            content_col_combo = ttk.Combobox(mapping_frame, textvariable=content_col_var,
                                             values=list(df.columns), width=20)
            content_col_combo.pack(side=LEFT, padx=5)

            Label(mapping_frame, text="情感分类列:", font=('微软雅黑', 9)).pack(side=LEFT, padx=5)
            sentiment_col_var = StringVar(value=df.columns[1] if len(df.columns) > 1 else "")
            sentiment_col_combo = ttk.Combobox(mapping_frame, textvariable=sentiment_col_var,
                                               values=list(df.columns), width=20)
            sentiment_col_combo.pack(side=LEFT, padx=5)

            def confirm_mapping():
                content_col = content_col_var.get()
                sentiment_col = sentiment_col_var.get()

                if not content_col or not sentiment_col:
                    messagebox.showerror("错误", "请选择列映射")
                    return

                texts = df[content_col].tolist()
                raw_labels = df[sentiment_col].tolist()

                converted_texts = []
                converted_labels = []
                conversion_stats = {'正面': 0, '中性': 0, '负面': 0, '无效': 0}

                for text, label in zip(texts, raw_labels):
                    if not isinstance(text, str) or not text.strip():
                        conversion_stats['无效'] += 1
                        continue

                    label_str = str(label).strip().lower()

                    if label_str in ['正面', 'positive', 'pos', '好评', '5', '5.0', '4', '4.0']:
                        converted_labels.append('正面')
                        converted_texts.append(text.strip())
                        conversion_stats['正面'] += 1
                    elif label_str in ['负面', 'negative', 'neg', '差评', '1', '1.0', '2', '2.0']:
                        converted_labels.append('负面')
                        converted_texts.append(text.strip())
                        conversion_stats['负面'] += 1
                    elif label_str in ['中性', 'neutral', '中评', '3', '3.0']:
                        converted_labels.append('中性')
                        converted_texts.append(text.strip())
                        conversion_stats['中性'] += 1
                    else:
                        conversion_stats['无效'] += 1

                self.user_training_texts = converted_texts
                self.user_training_labels = converted_labels

                stats_text = f"转换结果: 正面{conversion_stats['正面']}条, 中性{conversion_stats['中性']}条, 负面{conversion_stats['负面']}条"
                if conversion_stats['无效'] > 0:
                    stats_text += f", 无效{conversion_stats['无效']}条"

                self.train_status_label.config(
                    text=f"训练数据已加载: {len(converted_texts)}条有效数据",
                    fg=self.colors['success']
                )
                self.data_info_label.config(
                    text=f"当前训练数据: {stats_text}",
                    fg=self.colors['primary']
                )

                total = len(converted_labels)
                if total > 0:
                    pos_pct = conversion_stats['正面'] / total * 100
                    neu_pct = conversion_stats['中性'] / total * 100
                    neg_pct = conversion_stats['负面'] / total * 100

                    self.sample_labels['正面'].config(text=f"{conversion_stats['正面']}条 ({pos_pct:.1f}%)")
                    self.sample_labels['中性'].config(text=f"{conversion_stats['中性']}条 ({neu_pct:.1f}%)")
                    self.sample_labels['负面'].config(text=f"{conversion_stats['负面']}条 ({neg_pct:.1f}%)")

                preview_win.destroy()

                if messagebox.askyesno("提示", "数据加载完成，是否立即开始训练？"):
                    self.start_user_training()

            Button(preview_win, text="确认并加载", command=confirm_mapping,
                   bg=self.colors['success'], fg='white', font=('微软雅黑', 9, 'bold')).pack(pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"读取训练数据失败：{str(e)}")
            import traceback
            traceback.print_exc()

    def start_user_training(self):
        train_source = self.train_source_var.get()

        if train_source == 'user':
            if not hasattr(self, 'user_training_texts') or not self.user_training_texts:
                messagebox.showwarning("提示", "请先上传用户训练数据")
                return

            if len(self.user_training_texts) < 10:
                if not messagebox.askyesno("警告",
                                           f"训练数据只有{len(self.user_training_texts)}条，可能效果不佳。是否继续？"):
                    return

            self.train_status_label.config(text="正在使用用户数据训练...", fg=self.colors['warning'])
            self.start_train_btn.config(state=DISABLED, text="训练中...")
            self.analyze_btn.config(state=DISABLED, text="训练中...")  # 分析按钮也禁用

            def train():
                def progress_cb(value, msg):
                    self.queue.put(('train_progress', (value, msg)))

                self.model.train_with_user_data(
                    self.user_training_texts,
                    self.user_training_labels,
                    progress_cb
                )
                self.queue.put(('train_complete', 'user'))

            threading.Thread(target=train, daemon=True).start()

        elif train_source == 'mixed':
            if hasattr(self, 'user_training_texts') and self.user_training_texts:
                self.train_status_label.config(text="正在混合训练...", fg=self.colors['warning'])
                self.start_train_btn.config(state=DISABLED, text="训练中...")
                self.analyze_btn.config(state=DISABLED, text="训练中...")

                def train_mixed():
                    def progress_cb(value, msg):
                        self.queue.put(('train_progress', (value, msg)))

                    self.model.train_mixed(
                        self.user_training_texts,
                        self.user_training_labels,
                        demo_ratio=0.3,
                        progress_callback=progress_cb
                    )
                    self.queue.put(('train_complete', 'mixed'))

                threading.Thread(target=train_mixed, daemon=True).start()
            else:
                if messagebox.askyesno("提示", "没有用户数据，是否使用演示数据训练？"):
                    self.start_training()

        else:
            self.start_training()

    def reset_to_demo_model(self):
        if not messagebox.askyesno("确认", "确定要重置为演示模型吗？这将丢失用户训练的模型。"):
            return

        self.train_status_label.config(text="正在重置为演示模型...", fg=self.colors['warning'])
        self.start_train_btn.config(state=DISABLED, text="训练中...")
        self.analyze_btn.config(state=DISABLED, text="训练中...")

        def reset():
            def progress_cb(value, msg):
                self.queue.put(('train_progress', (value, msg)))

            self.model.train(progress_cb, sample_count=1500)
            self.queue.put(('train_complete', 'demo'))

        threading.Thread(target=reset, daemon=True).start()

    def update_feature_display(self):
        feature_type = self.feature_tab_var.get()
        info = self.model.get_training_info()

        self.feature_text.delete('1.0', END)

        if not info or not info.get('feature_importance'):
            self.feature_text.insert('end', "暂无特征词数据")
            return

        feature_importance = info['feature_importance']

        if feature_type == '正面' and '正面' in feature_importance:
            self.feature_text.insert('end', "📌 正面情感最重要的特征词：\n\n", 'title')
            for word, score in feature_importance['正面'][:20]:
                self.feature_text.insert('end', f"  • {word}  (权重: {score:.3f})\n")

        elif feature_type == '负面' and '负面' in feature_importance:
            self.feature_text.insert('end', "📌 负面情感最重要的特征词：\n\n", 'title')
            for word, score in feature_importance['负面'][:20]:
                self.feature_text.insert('end', f"  • {word}  (权重: {score:.3f})\n")

        elif feature_type == '中性' and '中性' in feature_importance:
            self.feature_text.insert('end', "📌 中性情感最重要的特征词：\n\n", 'title')
            for word, score in feature_importance['中性'][:20]:
                self.feature_text.insert('end', f"  • {word}  (权重: {score:.3f})\n")

        elif 'all' in feature_importance:
            self.feature_text.insert('end', f"📌 所有类别最重要的特征词：\n\n", 'title')
            for word, score in feature_importance['all'][:30]:
                self.feature_text.insert('end', f"  • {word}  (重要性: {score:.4f})\n")

        self.feature_text.tag_configure('title', font=('微软雅黑', 10, 'bold'), foreground='#2c3e50')

    def update_model_info(self):
        info = self.model.get_training_info()
        if not info:
            return

        self.metric_labels["数据来源"].config(text=info.get('data_source', '演示数据'))
        self.metric_labels["模型类型"].config(text=info.get('model_type', '未知'))
        self.metric_labels["准确率"].config(text=f"{info['accuracy']:.4f}")
        self.metric_labels["验证集准确率"].config(text=f"{info.get('val_accuracy', 0):.4f}")
        self.metric_labels["训练样本"].config(text=f"{info['total_samples']}条")
        self.metric_labels["特征词"].config(text=f"{info['feature_count']}个")

        total = info['total_samples']
        for label in ['正面', '中性', '负面']:
            count = info['label_counts'].get(label, 0)
            percentage = (count / total * 100) if total > 0 else 0
            self.sample_labels[label].config(text=f"{count}条 ({percentage:.1f}%)")

        self.update_feature_display()

        self.train_status_label.config(
            text=f"训练状态: 已训练 (使用{info.get('data_source', '演示数据')})",
            fg=self.colors['success']
        )

        data_source = info.get('data_source', '演示数据')
        sample_info = f"{info['total_samples']}条样本"
        if 'label_counts' in info:
            counts = info['label_counts']
            sample_info += f" (正:{counts.get('正面', 0)} 中:{counts.get('中性', 0)} 负:{counts.get('负面', 0)})"

        self.data_info_label.config(
            text=f"当前训练数据: {data_source} - {sample_info}",
            fg=self.colors['primary']
        )


# 导入模型训练标签页组件
from gui_components import ModelTrainingTab