# sentiment_analysis_tool
京东评论情感分析系统是一个图形化工具，能够自动爬取、分析和可视化京东商品的用户评论，判断每条评论的情感倾向（正面/中性/负面），并进行多维度深度分析。
分为五大模块：爬虫、预处理、分析和可视化、模型训练、结果导出，其余还包括配置和工具模块。

运行环境：python Chrome浏览器用于Selenium爬虫功能

依赖：
pandas>=1.3.0               # 数据处理和分析        
numpy>=1.21.0               # 数值计算
scikit-learn>=1.0.0         # 机器学习算法
jieba>=0.42.1               # 中文分词库
matplotlib>=3.4.0           # 图表绘制
selenium>=4.0.0             # 浏览器自动化
webdriver-manager>=3.5.0    # ChromeDriver自动管理
openpyxl>=3.0.0             # Excel文件读写（.xlsx）
xlrd>=2.0.0                 # 读取旧版Excel（.xls）
requests>=2.26.0            # HTTP请求（可选）
tqdm>=4.62.0                # 进度条显示（可选）
joblib>=1.1.0               # 模型保存和加载（可选）

启动方式：直接运行主程序 main.py
