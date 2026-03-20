"""
统计可视化模块 - 生成情感分析图表
"""
import pandas as pd
import matplotlib.pyplot as plt


def analyze_ratio(df):
    """统计情感占比"""
    if df is None or df.empty or '情感分类' not in df.columns:
        return pd.DataFrame()

    count = df['情感分类'].value_counts()
    total = len(df)

    result = []
    for sentiment in ['正面', '中性', '负面']:
        num = count.get(sentiment, 0)
        ratio = (num / total * 100) if total > 0 else 0
        result.append({
            '情感类型': sentiment,
            '评论数量': num,
            '占比(%)': round(ratio, 2)
        })

    return pd.DataFrame(result)


def show_chart(result, dimension_stats=None, current_df=None):
    """显示图表 - 修复版，确保数据一致性"""
    if result.empty:
        return

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    if dimension_stats:
        # 创建更大的画布
        fig = plt.figure(figsize=(20, 12))
        fig.patch.set_facecolor('#f8f9fa')

        # 定义配色方案
        colors = {
            '正面': '#2ecc71',
            '中性': '#f39c12',
            '负面': '#e74c3c',
            'primary': '#3498db',
            'info': '#9b59b6'
        }

        # ========== 第1行：情感分布图表 ==========
        # 1.1 情感分布饼图
        ax1 = plt.subplot(3, 4, 1)
        pie_colors = [colors[row['情感类型']] for _, row in result.iterrows()]

        wedges, texts, autotexts = ax1.pie(
            result['占比(%)'],
            labels=result['情感类型'],
            autopct='%1.1f%%',
            colors=pie_colors,
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5, 'width': 1},
            textprops={'fontsize': 9, 'color': 'white', 'fontweight': 'bold'},
            labeldistance=1.1,
            pctdistance=0.6,
            explode=[0.02, 0.02, 0.02]
        )

        total = sum(result['评论数量'])
        ax1.text(0, -1.2, f'总计: {total}条', ha='center', va='center',
                 fontsize=10, fontweight='bold', color='#2c3e50')

        ax1.set_title('情感分布占比', fontsize=12, fontweight='bold', pad=15)

        ax1.set_position([ax1.get_position().x0, ax1.get_position().y0 + 0.02,
                          ax1.get_position().width, ax1.get_position().height])

        # 1.2 情感数量柱状图
        ax2 = plt.subplot(3, 4, 2)
        bars = ax2.bar(
            result['情感类型'],
            result['评论数量'],
            color=[colors[r['情感类型']] for _, r in result.iterrows()],
            edgecolor='white',
            linewidth=1.5
        )

        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height)}条', ha='center', va='bottom', fontsize=9)

        ax2.set_title('情感数量分布', fontsize=12, fontweight='bold', pad=10)
        ax2.grid(axis='y', alpha=0.2, linestyle='--')
        ax2.set_facecolor('#f8f9fa')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # 1.3 维度提及率横向条形图
        ax3 = plt.subplot(3, 4, (3, 4))
        dimensions = list(dimension_stats.keys())
        total_comments = total
        mention_rates = [dimension_stats[dim]["总提及"] / total_comments * 100
                         for dim in dimensions]

        y_pos = range(len(dimensions))
        bars = ax3.barh(y_pos, mention_rates, color=colors['primary'],
                        alpha=0.8, edgecolor='white', linewidth=1.5)

        for i, (bar, rate) in enumerate(zip(bars, mention_rates)):
            ax3.text(rate + 0.5, bar.get_y() + bar.get_height() / 2,
                     f'{rate:.1f}%', va='center', fontsize=9)

        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(dimensions, fontsize=9)
        ax3.set_title('各维度提及率', fontsize=12, fontweight='bold', pad=10)
        ax3.set_xlabel('提及率 (%)', fontsize=9)
        ax3.set_xlim(0, max(mention_rates) + 10)
        ax3.grid(axis='x', alpha=0.2, linestyle='--')
        ax3.set_facecolor('#f8f9fa')
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # ========== 第2行：维度对比分析 ==========
        # 2.1 好评率vs差评率对比图（占据2列）
        ax4 = plt.subplot(3, 4, (5, 6))
        good_rates = [dimension_stats[dim]["正面率"] for dim in dimensions]
        bad_rates = [dimension_stats[dim]["负面率"] for dim in dimensions]

        x = range(len(dimensions))
        width = 0.35

        bars1 = ax4.bar([i - width / 2 for i in x], good_rates, width,
                        label='好评率', color=colors['正面'], alpha=0.9, edgecolor='white', linewidth=1)
        bars2 = ax4.bar([i + width / 2 for i in x], bad_rates, width,
                        label='差评率', color=colors['负面'], alpha=0.9, edgecolor='white', linewidth=1)

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax4.text(bar.get_x() + bar.get_width() / 2., height + 1,
                             f'{height:.1f}%', ha='center', va='bottom',
                             fontsize=8, rotation=0)

        ax4.text(0, 1.05, '比率 (%)', transform=ax4.transAxes, fontsize=9, ha='center', va='bottom')
        ax4.set_title('各维度好评率 vs 差评率', fontsize=12, fontweight='bold', pad=10)
        ax4.set_xticks(x)
        ax4.set_xticklabels(dimensions, rotation=30, ha='right', fontsize=8)
        ax4.legend(loc='upper right', frameon=True, fancybox=True, fontsize=9)
        ax4.grid(axis='y', alpha=0.2, linestyle='--')
        ax4.set_facecolor('#f8f9fa')
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)

        ax4.tick_params(axis='y', pad=10)

        # 2.2 维度详细统计卡片（占据1列）
        ax5 = plt.subplot(3, 4, 7)
        ax5.axis('off')

        detail_text = "维度详细统计\n" + "-" * 20 + "\n\n"
        for dim in dimensions[:3]:
            stats = dimension_stats[dim]
            detail_text += f"【{dim[:4]}】\n"
            detail_text += f"  正面: {stats['正面']:2d}条 ({stats['正面率']:.0f}%)\n"
            detail_text += f"  负面: {stats['负面']:2d}条 ({stats['负面率']:.0f}%)\n"
            detail_text += f"  中性: {stats['中性']:2d}条\n\n"

        ax5.text(0.1, 1.1, detail_text, fontsize=9, va='top',
                 fontname='Microsoft YaHei',
                 bbox=dict(boxstyle='round', facecolor='white',
                           edgecolor='#3498db', alpha=0.8, pad=2))

        # 2.3 剩余维度统计卡片（占据1列）
        ax5b = plt.subplot(3, 4, 8)
        ax5b.axis('off')

        detail_text2 = "维度详细统计(续)\n" + "-" * 20 + "\n\n"
        for dim in dimensions[3:]:
            stats = dimension_stats[dim]
            detail_text2 += f"【{dim[:4]}】\n"
            detail_text2 += f"  正面: {stats['正面']:2d}条 ({stats['正面率']:.0f}%)\n"
            detail_text2 += f"  负面: {stats['负面']:2d}条 ({stats['负面率']:.0f}%)\n"
            detail_text2 += f"  中性: {stats['中性']:2d}条\n\n"

        ax5b.text(0.1, 1.1, detail_text2, fontsize=9, va='top',
                  fontname='Microsoft YaHei',
                  bbox=dict(boxstyle='round', facecolor='white',
                            edgecolor='#3498db', alpha=0.8, pad=2))

        # ========== 第3行：当前分析数据统计（右下部分） ==========
        # 3.1 核心指标卡片（占据2列）
        ax6 = plt.subplot(3, 4, (9, 10))
        ax6.axis('off')

        pos_count = result[result['情感类型'] == '正面']['评论数量'].values[0] if '正面' in result[
            '情感类型'].values else 0
        neu_count = result[result['情感类型'] == '中性']['评论数量'].values[0] if '中性' in result[
            '情感类型'].values else 0
        neg_count = result[result['情感类型'] == '负面']['评论数量'].values[0] if '负面' in result[
            '情感类型'].values else 0

        avg_score = (pos_count * 5 + neu_count * 3 + neg_count * 1) / total if total > 0 else 0

        ax6.text(0.05, 0.85, '核心分析指标', fontsize=12, fontweight='bold',
                 color='#2c3e50', transform=ax6.transAxes)

        metrics = [
            ('总评论数', f'{total}条', '#3498db'),
            ('综合评分', f'{avg_score:.1f}/5.0', '#f1c40f'),
            ('好评率', f'{pos_count / total * 100:.1f}%', '#2ecc71'),
            ('差评率', f'{neg_count / total * 100:.1f}%', '#e74c3c'),
            ('中评率', f'{neu_count / total * 100:.1f}%', '#f39c12'),
        ]

        for i, (label, value, color) in enumerate(metrics):
            x_pos = 0.05 + (i % 3) * 0.3
            y_pos = 0.6 - (i // 3) * 0.15
            ax6.text(x_pos, y_pos, label, fontsize=9, color='#7f8c8d',
                     transform=ax6.transAxes)
            ax6.text(x_pos, y_pos - 0.07, value, fontsize=12, fontweight='bold',
                     color=color, transform=ax6.transAxes)

        # 3.2 维度分析摘要（右下部分，占据2列）
        ax7 = plt.subplot(3, 4, (11, 12))
        ax7.axis('off')

        top_dim_candidates = [(d, dimension_stats[d]['正面率']) for d in dimensions if dimension_stats[d]['正面率'] > 0]
        weak_dim_candidates = [(d, dimension_stats[d]['负面率']) for d in dimensions if
                               dimension_stats[d]['负面率'] > 0]

        if top_dim_candidates:
            top_dim = max(top_dim_candidates, key=lambda x: x[1])[0]
        else:
            top_dim = dimensions[0]

        if weak_dim_candidates:
            weak_dim = max(weak_dim_candidates, key=lambda x: x[1])[0]
        else:
            weak_dim = dimensions[0]

        most_mentioned = max(dimensions, key=lambda d: dimension_stats[d]['总提及'])

        ax7.text(0.05, 0.9, '维度洞察报告', fontsize=12, fontweight='bold',
                 color='#2c3e50', transform=ax7.transAxes)

        insights = [
            ('表现最佳', f'{top_dim}', dimension_stats[top_dim]['正面率'], colors['正面']),
            ('待改进', f'{weak_dim}', dimension_stats[weak_dim]['负面率'], colors['负面']),
            ('热议焦点', f'{most_mentioned}', dimension_stats[most_mentioned]['总提及'], colors['primary'])
        ]

        for i, (title, dim, value, color) in enumerate(insights):
            y_pos = 0.75 - i * 0.2
            ax7.text(0.1, y_pos, title, fontsize=10, fontweight='bold',
                     color=color, transform=ax7.transAxes)
            ax7.text(0.1, y_pos - 0.08, dim, fontsize=10, fontweight='bold',
                     transform=ax7.transAxes)
            if i < 2:
                ax7.text(0.5, y_pos - 0.04, f'{value:.1f}%', fontsize=9,
                         transform=ax7.transAxes, color=color)
            else:
                ax7.text(0.5, y_pos - 0.04, f'{value}次', fontsize=9,
                         transform=ax7.transAxes, color=color)

        suggestion = f"改进建议：重点关注{weak_dim}问题，{total - pos_count}条非好评中"
        suggestion += f"有{dimension_stats[weak_dim]['负面']}条提及{weak_dim}"

        ax7.text(0.1, 0.1, suggestion, fontsize=9, wrap=True,
                 bbox=dict(boxstyle='round', facecolor='#fef9e7',
                           edgecolor='#f39c12', alpha=0.8),
                 transform=ax7.transAxes)

        ax7.text(0.95, 0.02, '京东评论分析系统', fontsize=8,
                 color='#bdc3c7', ha='right', transform=ax7.transAxes, alpha=0.5)

        plt.suptitle(f'京东商品评论多维度分析报告 (共{total}条评论)',
                     fontsize=16, fontweight='bold', color='#2c3e50', y=0.98)

        plt.tight_layout()
        plt.subplots_adjust(top=0.92, hspace=0.4, wspace=0.3)

    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_facecolor('#f8f9fa')

        colors = {'正面': '#2ecc71', '中性': '#f39c12', '负面': '#e74c3c'}
        total = sum(result['评论数量'])

        pie_colors = [colors[row['情感类型']] for _, row in result.iterrows()]
        wedges, texts, autotexts = ax1.pie(
            result['占比(%)'],
            labels=result['情感类型'],
            autopct='%1.1f%%',
            colors=pie_colors,
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )

        centre_circle = plt.Circle((0, 0), 0.70, fc='#f8f9fa', linewidth=0)
        ax1.add_artist(centre_circle)
        ax1.text(0, 0, f'{total}条', ha='center', va='center',
                 fontsize=12, fontweight='bold', color='#2c3e50')
        ax1.set_title('情感分布占比', fontsize=14, fontweight='bold', pad=15)

        bars = ax2.bar(
            result['情感类型'],
            result['评论数量'],
            color=[colors[r['情感类型']] for _, r in result.iterrows()],
            edgecolor='white',
            linewidth=2
        )

        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height + 1,
                     f'{int(height)}条', ha='center', va='bottom',
                     fontsize=11, fontweight='bold')

        ax2.set_title('情感数量分布', fontsize=14, fontweight='bold', pad=15)
        ax2.set_ylabel('评论数量')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        ax2.set_facecolor('#f8f9fa')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        plt.suptitle(f'京东评论情感分析 (共{total}条评论)', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()

    plt.show()