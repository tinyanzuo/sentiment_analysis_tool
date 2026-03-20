# sentiment_analysis_tool
京东评论情感分析系统是一个图形化工具，能够自动爬取、分析和可视化京东商品的用户评论，判断每条评论的情感倾向（正面/中性/负面），并进行多维度深度分析。
分为五大模块：爬虫、预处理、分析和可视化、模型训练、结果导出，其余还包括配置和工具模块。

运行环境：python Chrome浏览器用于Selenium爬虫功能

依赖：pandas、numpy、scikit-learn、jieba、matplotlib、selenium、 webdriver-manager、openpyxl、xlrd、requests、tqdm、joblib         

启动方式：直接运行主程序 main.py
