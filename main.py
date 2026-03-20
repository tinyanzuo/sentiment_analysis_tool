"""
京东评论情感分析系统 - 主程序入口
"""
import matplotlib.pyplot as plt
from tkinter import Tk

from gui import JDSentimentAnalyzer

if __name__ == '__main__':
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    root = Tk()
    app = JDSentimentAnalyzer(root)
    root.mainloop()