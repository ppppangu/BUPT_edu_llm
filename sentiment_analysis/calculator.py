#!/usr/bin/env python3
"""
情绪指数计算模块 - 计算综合情绪指数，生成分析报告
"""

import json
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter  # 添加Counter导入

class SentimentCalculator:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SentimentCalculator')
    
    def load_processed_data(self, date_str=None):
        """加载处理后的数据"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        processed_file = os.path.join(self.data_dir, 'processed', f'processed_{date_str}.json')
        
        if not os.path.exists(processed_file):
            self.logger.warning(f"处理后的数据不存在: {processed_file}")
            return pd.DataFrame()
        
        try:
            df = pd.read_json(processed_file, orient='records')
            return df
        except Exception as e:
            self.logger.error(f"加载处理后的数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_sentiment_index(self, df):
        """计算情绪指数"""
        if df.empty:
            return {}
        
        # 基础统计
        total_posts = len(df)
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        
        # 加权情绪得分
        weighted_scores = df['sentiment_score'] * df['weight']
        sentiment_index = weighted_scores.mean()
        
        # 标准化到0-100范围
        normalized_index = max(0, min(100, 50 + (sentiment_index * 50)))
        
        # 分来源统计
        source_stats = {}
        for source in df['source'].unique():
            source_df = df[df['source'] == source]
            source_scores = source_df['sentiment_score'] * source_df['weight']
            source_index = source_scores.mean()
            source_normalized = max(0, min(100, 50 + (source_index * 50)))
            
            source_stats[source] = {
                'normalized_index': source_normalized,
                'post_count': len(source_df),
                'positive_ratio': len(source_df[source_df['sentiment'] == 'positive']) / len(source_df)
            }
        
        # 热门关键词
        all_keywords = []
        for keywords in df['keywords']:
            all_keywords.extend(keywords)
        
        keyword_counter = Counter(all_keywords)  # 这里使用了Counter
        top_keywords = keyword_counter.most_common(15)
        
        # 情绪强度
        intensity_metrics = {
            'average_intensity': float(df['sentiment_score'].abs().mean()),
            'volatility': float(df['sentiment_score'].std())
        }
        
        # 市场状态
        market_state = self.determine_market_state(normalized_index)
        
        # 置信度
        confidence = self.calculate_confidence(df)
        
        result = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_posts': total_posts,
            'sentiment_distribution': sentiment_counts,
            'normalized_sentiment_index': float(normalized_index),
            'source_statistics': source_stats,
            'top_keywords': top_keywords,
            'intensity_metrics': intensity_metrics,
            'market_state': market_state,
            'confidence_score': confidence,
            'recommendation': self.generate_recommendation(normalized_index, market_state)
        }
        
        return result
    
    def determine_market_state(self, index):
        """确定市场状态"""
        if index >= 70:
            return "乐观"
        elif index >= 60:
            return "略微乐观"
        elif index >= 45:
            return "中性"
        elif index >= 30:
            return "略微悲观"
        else:
            return "悲观"
    
    def calculate_confidence(self, df):
        """计算置信度"""
        if df.empty:
            return 0.0
        
        post_count = len(df)
        source_count = df['source'].nunique()
        
        # 基于帖子数量和来源多样性的简单置信度计算
        count_confidence = min(1.0, post_count / 50)
        diversity_confidence = min(1.0, source_count / 4)
        
        return (count_confidence + diversity_confidence) / 2
    
    def generate_recommendation(self, sentiment_index, market_state):
        """生成投资建议"""
        if "乐观" in market_state:
            return {
                'outlook': '积极',
                'action': '考虑逢低布局优质标的',
                'risk_level': '中等'
            }
        elif "悲观" in market_state:
            return {
                'outlook': '谨慎', 
                'action': '控制仓位，等待更好时机',
                'risk_level': '较高'
            }
        else:
            return {
                'outlook': '中性',
                'action': '观望为主，谨慎操作',
                'risk_level': '中等'
            }
    
    def generate_daily_sentiment_report(self, date_str=None):
        """生成每日情绪报告"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"生成 {date_str} 的情绪报告")
        
        # 加载处理后的数据
        df = self.load_processed_data(date_str)
        if df.empty:
            self.logger.warning("没有可用的处理数据")
            return {}
        
        # 计算情绪指数
        sentiment_report = self.calculate_sentiment_index(df)
        
        if sentiment_report:
            # 保存报告
            report_file = os.path.join(self.data_dir, 'results', f'sentiment_report_{date_str}.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(sentiment_report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"情绪报告已保存: {report_file}")
            return {'basic_report': sentiment_report}
        
        return {}
    
    def generate_historical_analysis(self, days=7):
        """生成历史分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        historical_data = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            report_file = os.path.join(self.data_dir, 'results', f'sentiment_report_{date_str}.json')
            
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        historical_data.append(data)
                except:
                    pass
            
            current_date += timedelta(days=1)
        
        if historical_data:
            # 简单历史分析
            dates = [data['date'] for data in historical_data]
            indices = [data['normalized_sentiment_index'] for data in historical_data]
            
            historical_analysis = {
                'period': f"{dates[0]} 至 {dates[-1]}",
                'sentiment_trend': {
                    'dates': dates,
                    'values': indices
                },
                'average_sentiment': float(np.mean(indices)),
                'trend': '上升' if indices[-1] > indices[0] else '下降'
            }
            
            # 保存历史分析
            history_file = os.path.join(self.data_dir, 'reports', f'historical_analysis_{days}days.json')
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(historical_analysis, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"历史分析已保存: {history_file}")
            return historical_analysis
        
        return {}

def main():
    """主函数"""
    calculator = SentimentCalculator()
    
    print("开始计算股票市场情绪指数...")
    
    # 生成当日情绪报告
    report = calculator.generate_daily_sentiment_report()
    
    if report:
        basic_report = report['basic_report']
        
        print(f"\n=== 市场情绪指数报告 ===")
        print(f"日期: {basic_report['date']}")
        print(f"综合情绪指数: {basic_report['normalized_sentiment_index']:.2f}")
        print(f"市场状态: {basic_report['market_state']}")
        print(f"数据置信度: {basic_report['confidence_score']:.1%}")
        print(f"分析帖子数: {basic_report['total_posts']}")
        
        print(f"\n情绪分布:")
        for sentiment, count in basic_report['sentiment_distribution'].items():
            percentage = (count / basic_report['total_posts']) * 100
            print(f"  {sentiment}: {count} 条 ({percentage:.1f}%)")
        
        print(f"\n各来源情绪指数:")
        for source, stats in basic_report['source_statistics'].items():
            print(f"  {source}: {stats['normalized_index']:.2f}")
        
        print(f"\n投资建议:")
        rec = basic_report['recommendation']
        print(f"  市场展望: {rec['outlook']}")
        print(f"  建议操作: {rec['action']}")
        print(f"  风险等级: {rec['risk_level']}")
    
    # 生成历史分析
    print(f"\n生成历史趋势分析...")
    calculator.generate_historical_analysis(days=7)
    
    print(f"\n情绪指数计算完成！")
    print(f"报告文件保存在: data/reports/")

if __name__ == "__main__":
    main()