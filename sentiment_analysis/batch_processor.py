#!/usr/bin/env python3
"""
批量处理脚本 - 处理多天数据并生成历史分析
"""

import os
import sys
from datetime import datetime, timedelta
from processor import DataProcessor
from calculator import SentimentCalculator
from visualizer import SentimentVisualizer

def process_multiple_days(days=7):
    """处理多天数据"""
    print(f"开始批量处理 {days} 天的数据...")
    
    # 初始化模块
    processor = DataProcessor()
    calculator = SentimentCalculator()
    visualizer = SentimentVisualizer()
    
    processed_dates = []
    
    # 处理每一天的数据
    for i in range(days):
        date_offset = -i  # 从今天往前推
        target_date = datetime.now() + timedelta(days=date_offset)
        date_str = target_date.strftime('%Y%m%d')
        
        print(f"\n处理日期: {date_str} (偏移: {date_offset}天)")
        
        # 检查原始数据是否存在
        raw_files_exist = any(
            os.path.exists(f"data/raw/{source}_{date_str}.json") 
            for source in ['eastmoney', 'xueqiu', 'weibo', 'tieba']
        )
        
        if not raw_files_exist:
            print(f"  ⚠️  跳过 {date_str} - 没有原始数据")
            continue
        
        try:
            # 处理数据
            df = processor.process_daily_data(date_str)
            if df.empty:
                print(f"  ⚠️  跳过 {date_str} - 没有处理后的数据")
                continue
            
            # 计算情绪指数
            report = calculator.generate_daily_sentiment_report(date_str)
            if report:
                print(f"  ✅ 完成 {date_str} - {len(df)} 条数据")
                processed_dates.append(date_str)
            else:
                print(f"  ⚠️  跳过 {date_str} - 情绪计算失败")
                
        except Exception as e:
            print(f"  ❌ 处理 {date_str} 失败: {e}")
    
    if processed_dates:
        print(f"\n成功处理 {len(processed_dates)} 天的数据:")
        for date in processed_dates:
            print(f"  ✅ {date}")
        
        # 生成历史分析
        print(f"\n生成历史分析报告...")
        try:
            historical_report = calculator.generate_historical_analysis(days=days)
            if historical_report:
                print(f"✅ 历史分析报告已生成")
                
                # 生成历史趋势图
                visualizer.create_historical_trend_chart(days=days)
                print(f"✅ 历史趋势图已生成")
            else:
                print("⚠️  历史分析报告生成失败")
                
        except Exception as e:
            print(f"❌ 历史分析失败: {e}")
            
    else:
        print("❌ 没有成功处理任何数据")
    
    return processed_dates

def generate_all_visualizations(days=7):
    """为所有处理过的日期生成可视化"""
    print(f"\n生成所有可视化图表...")
    
    visualizer = SentimentVisualizer()
    
    # 查找所有处理过的数据文件
    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        print("❌ 处理后的数据目录不存在")
        return
    
    processed_files = [f for f in os.listdir(processed_dir) if f.startswith('processed_') and f.endswith('.json')]
    
    for file in processed_files:
        date_str = file.replace('processed_', '').replace('.json', '')
        print(f"生成 {date_str} 的可视化图表...")
        
        try:
            visualizer.create_daily_sentiment_dashboard(date_str)
            visualizer.create_word_cloud(date_str)
            print(f"  ✅ {date_str} 可视化完成")
        except Exception as e:
            print(f"  ❌ {date_str} 可视化失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("股票情绪分析系统 - 批量处理工具")
    print("=" * 60)
    
    # 处理过去7天的数据
    processed_dates = process_multiple_days(days=7)
    
    if processed_dates:
        # 生成所有可视化
        generate_all_visualizations(days=7)
        
        print(f"\n" + "=" * 60)
        print("🎉 批量处理完成！")
        print(f"处理了 {len(processed_dates)} 天的数据")
        print("📊 查看结果:")
        print("   - 每日报告: data/results/sentiment_report_YYYYMMDD.json")
        print("   - 历史分析: data/reports/historical_analysis_7days.json")
        print("   - 趋势图表: data/charts/historical_trend_7days.png")
        print("   - 每日仪表盘: data/charts/sentiment_dashboard_YYYYMMDD.png")
    else:
        print("\n❌ 没有数据被处理，请先运行测试数据生成器")
        print("运行: python test_data.py")

if __name__ == "__main__":
    main()