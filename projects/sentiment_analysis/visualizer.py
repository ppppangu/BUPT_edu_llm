#!/usr/bin/env python3
"""
可视化模块 - 生成图表和可视化报告
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime
from collections import Counter

class SentimentVisualizer:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.setup_directories()
        self.setup_logging()
        
        # 设置中文字体
        self.setup_chinese_font()
        
        # 颜色配置
        self.colors = {
            'positive': '#2ecc71',
            'negative': '#e74c3c', 
            'neutral': '#3498db'
        }
    
    def setup_directories(self):
        """创建必要的目录"""
        directories = [
            'data/raw',
            'data/processed', 
            'data/results',
            'data/reports',
            'data/charts',
            'data/wordcloud',
            'config',
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SentimentVisualizer')
    
    def setup_chinese_font(self):
        """设置中文字体"""
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            self.logger.warning("中文字体设置失败")
    
    def create_daily_sentiment_dashboard(self, date_str=None):
        """创建每日情绪仪表盘"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # 加载情绪报告
        report_file = os.path.join(self.data_dir, 'results', f'sentiment_report_{date_str}.json')
        if not os.path.exists(report_file):
            self.logger.warning(f"情绪报告不存在: {report_file}")
            return
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except Exception as e:
            self.logger.error(f"加载情绪报告失败: {e}")
            return
        
        # 创建仪表盘
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'股票市场情绪分析 - {report["date"]}', fontsize=16, fontweight='bold')
        
        # 1. 情绪分布饼图
        ax1 = axes[0, 0]
        sentiment_counts = report['sentiment_distribution']
        labels = list(sentiment_counts.keys())
        sizes = list(sentiment_counts.values())
        colors = [self.colors.get(label, self.colors['neutral']) for label in labels]
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('情绪分布')
        
        # 2. 来源情绪对比
        ax2 = axes[0, 1]
        sources = list(report['source_statistics'].keys())
        indices = [stats['normalized_index'] for stats in report['source_statistics'].values()]
        ax2.bar(sources, indices, color=[self.colors['positive'] if x >= 50 else self.colors['negative'] for x in indices])
        ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
        ax2.set_ylabel('情绪指数')
        ax2.set_title('各来源情绪指数')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 3. 情绪指数仪表
        ax3 = axes[1, 0]
        sentiment_index = report['normalized_sentiment_index']
        market_state = report['market_state']
        
        # 创建简单的仪表盘
        ax3.text(0.5, 0.7, f'{sentiment_index:.1f}', ha='center', va='center', fontsize=32, 
                color=self.colors['positive'] if sentiment_index >= 50 else self.colors['negative'])
        ax3.text(0.5, 0.5, market_state, ha='center', va='center', fontsize=16)
        ax3.text(0.5, 0.3, f"置信度: {report['confidence_score']:.1%}", ha='center', va='center')
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.axis('off')
        ax3.set_title('市场情绪指数')
        
        # 4. 投资建议
        ax4 = axes[1, 1]
        recommendation = report['recommendation']
        ax4.axis('off')
        text_content = [
            "投资建议",
            "=" * 20,
            f"市场展望: {recommendation['outlook']}",
            f"建议操作: {recommendation['action']}",
            f"风险等级: {recommendation['risk_level']}"
        ]
        for i, line in enumerate(text_content):
            y_pos = 0.8 - i * 0.15
            fontsize = 12 if i > 0 else 14
            fontweight = 'bold' if i <= 1 else 'normal'
            ax4.text(0.5, y_pos, line, ha='center', va='center', 
                   transform=ax4.transAxes, fontsize=fontsize, fontweight=fontweight)
        
        plt.tight_layout()
        
        # 保存仪表盘
        dashboard_file = os.path.join(self.data_dir, 'charts', f'sentiment_dashboard_{date_str}.png')
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"情绪仪表盘已保存: {dashboard_file}")
    
    def create_word_cloud(self, date_str=None):
        """创建词云图（简化版，不使用wordcloud包）"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # 加载处理后的数据
        processed_file = os.path.join(self.data_dir, 'processed', f'processed_{date_str}.json')
        if not os.path.exists(processed_file):
            self.logger.warning(f"处理后的数据不存在: {processed_file}")
            return
        
        try:
            df = pd.read_json(processed_file, orient='records')
        except Exception as e:
            self.logger.error(f"加载处理后的数据失败: {e}")
            return
        
        if df.empty:
            self.logger.warning("没有数据创建词云")
            return
        
        # 提取所有关键词
        all_keywords = []
        for keywords in df['keywords']:
            all_keywords.extend(keywords)
        
        if not all_keywords:
            self.logger.warning("没有关键词数据")
            return
        
        # 计算词频
        word_freq = Counter(all_keywords)
        
        # 创建简单的条形图替代词云
        top_words = word_freq.most_common(15)
        words = [word for word, freq in top_words]
        freqs = [freq for word, freq in top_words]
        
        plt.figure(figsize=(12, 6))
        plt.barh(words, freqs, color='skyblue')
        plt.xlabel('出现频率')
        plt.title(f'热门关键词 - {date_str}')
        plt.gca().invert_yaxis()  # 最高的在最上面
        
        # 保存图表
        wordcloud_file = os.path.join(self.data_dir, 'charts', f'keywords_chart_{date_str}.png')
        plt.savefig(wordcloud_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"关键词图表已保存: {wordcloud_file}")
    
    def create_historical_trend_chart(self, days=7):
        """创建历史趋势图"""
        historical_file = os.path.join(self.data_dir, 'reports', f'historical_analysis_{days}days.json')
        if not os.path.exists(historical_file):
            self.logger.warning(f"历史分析文件不存在: {historical_file}")
            return
        
        try:
            with open(historical_file, 'r', encoding='utf-8') as f:
                historical_data = json.load(f)
        except Exception as e:
            self.logger.error(f"加载历史分析数据失败: {e}")
            return
        
        # 创建趋势图
        dates = historical_data['sentiment_trend']['dates']
        values = historical_data['sentiment_trend']['values']
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, values, marker='o', linewidth=2, color='#3498db')
        plt.fill_between(dates, values, 50, 
                        where=[x >= 50 for x in values], 
                        color='#2ecc71', alpha=0.3, label='乐观区域')
        plt.fill_between(dates, values, 50,
                        where=[x < 50 for x in values],
                        color='#e74c3c', alpha=0.3, label='悲观区域')
        plt.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
        plt.ylabel('情绪指数')
        plt.title(f'过去{days}天市场情绪指数趋势')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存趋势图
        trend_file = os.path.join(self.data_dir, 'charts', f'historical_trend_{days}days.png')
        plt.savefig(trend_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"历史趋势图已保存: {trend_file}")

def main():
    """主函数"""
    visualizer = SentimentVisualizer()
    
    print("开始生成股票市场情绪可视化图表...")
    
    # 生成当日仪表盘
    print("1. 生成情绪仪表盘...")
    visualizer.create_daily_sentiment_dashboard()
    
    # 生成关键词图表（替代词云）
    print("2. 生成关键词图表...")
    visualizer.create_word_cloud()
    
    # 生成历史趋势图
    print("3. 生成历史趋势图...")
    visualizer.create_historical_trend_chart(days=7)
    
    print(f"\n可视化图表生成完成！")
    print(f"图表文件保存在: data/charts/")

if __name__ == "__main__":
    main()