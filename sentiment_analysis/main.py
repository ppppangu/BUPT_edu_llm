#!/usr/bin/env python3
"""
股票市场情绪分析系统 - 完整版主程序
运行: python main.py --mode full
"""

import os
import sys
import logging
import argparse
import traceback
import json
from datetime import datetime, timedelta
from crawler import StockCrawler
from processor import DataProcessor
from calculator import SentimentCalculator
from visualizer import SentimentVisualizer
from test_data import EnhancedTestDataGenerator

class StockSentimentSystem:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        
        # 初始化各个模块
        self.crawler = StockCrawler()
        self.processor = DataProcessor()
        self.calculator = SentimentCalculator()
        self.visualizer = SentimentVisualizer()
        self.test_generator = EnhancedTestDataGenerator()
        
        self.logger = logging.getLogger('StockSentimentSystem')
    
    def setup_logging(self):
        """设置日志系统"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
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
    
    def run_data_collection(self):
        """运行数据采集"""
        try:
            self.logger.info("执行数据采集...")
            results = self.crawler.run_all_crawlers()
            self.logger.info("数据采集完成")
            return True
        except Exception as e:
            self.logger.error(f"数据采集失败: {e}")
            return False
    
    def run_data_processing(self, date_str=None):
        """运行数据处理"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')
                
            self.logger.info(f"处理 {date_str} 的数据...")
            df = self.processor.process_daily_data(date_str)
            
            if df.empty:
                self.logger.warning(f"没有处理后的数据: {date_str}")
                return False
                
            self.logger.info(f"数据处理完成: {len(df)} 条记录")
            return True
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            return False
    
    def run_sentiment_calculation(self, date_str=None):
        """运行情绪计算"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')
                
            self.logger.info(f"计算 {date_str} 的情绪指数...")
            report = self.calculator.generate_daily_sentiment_report(date_str)
            
            if not report:
                self.logger.warning(f"情绪计算返回空结果: {date_str}")
                return False
                
            self.logger.info("情绪计算完成")
            return True
        except Exception as e:
            self.logger.error(f"情绪计算失败: {e}")
            return False
    
    def run_visualization(self, date_str=None):
        """运行可视化"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')
                
            self.logger.info(f"生成 {date_str} 的可视化图表...")
            self.visualizer.create_daily_sentiment_dashboard(date_str)
            self.visualizer.create_word_cloud(date_str)
            self.logger.info("可视化生成完成")
            return True
        except Exception as e:
            self.logger.error(f"可视化生成失败: {e}")
            return False
    
    def run_historical_analysis(self, days=7):
        """运行历史分析"""
        try:
            self.logger.info(f"生成 {days} 天历史分析...")
            self.calculator.generate_historical_analysis(days=days)
            self.visualizer.create_historical_trend_chart(days=days)
            self.logger.info("历史分析完成")
            return True
        except Exception as e:
            self.logger.error(f"历史分析失败: {e}")
            return False
    
    def run_daily_analysis(self, date_str=None):
        """运行单日分析"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        success = True
        
        # 数据处理
        if not self.run_data_processing(date_str):
            success = False
        
        # 情绪计算
        if not self.run_sentiment_calculation(date_str):
            success = False
        
        # 可视化
        if not self.run_visualization(date_str):
            success = False
        
        return success
    
    def run_batch_analysis(self, days=7):
        """运行批量分析 - 处理多天数据"""
        self.logger.info(f"开始批量处理 {days} 天的数据...")
        
        processed_dates = []
        
        # 处理每一天的数据
        for i in range(days):
            date_offset = -i  # 从今天往前推
            target_date = datetime.now() + timedelta(days=date_offset)
            date_str = target_date.strftime('%Y%m%d')
            
            self.logger.info(f"处理日期: {date_str}")
            
            # 检查原始数据是否存在
            raw_files_exist = any(
                os.path.exists(f"data/raw/{source}_{date_str}.json") 
                for source in ['eastmoney', 'xueqiu', 'weibo', 'tieba']
            )
            
            if not raw_files_exist:
                self.logger.warning(f"跳过 {date_str} - 没有原始数据")
                continue
            
            # 运行单日分析
            if self.run_daily_analysis(date_str):
                processed_dates.append(date_str)
        
        # 生成历史分析
        if processed_dates:
            self.logger.info(f"成功处理 {len(processed_dates)} 天的数据，生成历史分析...")
            self.run_historical_analysis(days=days)
            
            # 打印处理结果
            print(f"\n✅ 批量处理完成!")
            print(f"处理了 {len(processed_dates)} 天的数据:")
            for date in sorted(processed_dates):
                readable_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                print(f"  📅 {readable_date}")
            
            return True
        else:
            self.logger.error("没有成功处理任何数据")
            return False
    
    def run_full_analysis(self, date_str=None, include_history=True):
        """运行完整分析流程"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"开始执行完整的股票情绪分析流程 - {date_str}")
        
        success_steps = 0
        total_steps = 3  # 采集 + 分析 + 可视化
        
        try:
            # 1. 数据采集
            self.logger.info("步骤 1/3: 数据采集")
            if self.run_data_collection():
                success_steps += 1
            else:
                self.logger.warning("数据采集失败，尝试使用现有数据继续...")
            
            # 2. 单日分析
            self.logger.info("步骤 2/3: 数据分析")
            if self.run_daily_analysis(date_str):
                success_steps += 1
            else:
                self.logger.error("数据分析失败")
                return False
            
            # 3. 历史分析（如果启用）
            if include_history:
                self.logger.info("步骤 3/3: 历史分析")
                if self.run_historical_analysis(days=7):
                    success_steps += 1
                else:
                    self.logger.warning("历史分析失败，但单日分析完成")
            
            self.logger.info(f"完整的分析流程执行完成！成功步骤: {success_steps}/{total_steps}")
            
            # 打印简要报告
            self.print_daily_report(date_str)
            
            return success_steps >= 2  # 只要主要步骤成功就认为成功
            
        except Exception as e:
            self.logger.error(f"分析流程执行失败: {e}")
            traceback.print_exc()
            return False
    
    def generate_test_data(self, days=7):
        """生成测试数据"""
        try:
            self.logger.info(f"生成 {days} 天的测试数据")
            self.test_generator.create_sample_sentiment_words()
            self.test_generator.generate_weekly_data(days=days, posts_per_source=25)
            self.logger.info("测试数据生成完成")
            return True
        except Exception as e:
            self.logger.error(f"测试数据生成失败: {e}")
            return False
    
    def print_daily_report(self, date_str=None):
        """打印当日报告"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        report_file = f"data/results/sentiment_report_{date_str}.json"
        
        if not os.path.exists(report_file):
            self.logger.warning(f"报告文件不存在: {report_file}")
            return
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            print("\n" + "="*60)
            print("           股票市场情绪分析报告")
            print("="*60)
            print(f"分析日期: {report_data['date']}")
            print(f"情绪指数: {report_data['normalized_sentiment_index']:.2f}")
            print(f"市场状态: {report_data['market_state']}")
            print(f"数据置信度: {report_data['confidence_score']:.1%}")
            print(f"分析帖子数: {report_data['total_posts']}")
            
            print(f"\n情绪分布:")
            for sentiment, count in report_data['sentiment_distribution'].items():
                percentage = (count / report_data['total_posts']) * 100
                print(f"  {sentiment}: {count} 条 ({percentage:.1f}%)")
            
            print(f"\n各来源情绪指数:")
            for source, stats in report_data['source_statistics'].items():
                print(f"  {source}: {stats['normalized_index']:.2f}")
            
            print(f"\n投资建议:")
            rec = report_data['recommendation']
            print(f"  市场展望: {rec['outlook']}")
            print(f"  建议操作: {rec['action']}")
            print(f"  风险等级: {rec['risk_level']}")
            print("="*60)
            
        except Exception as e:
            self.logger.error(f"打印报告失败: {e}")
    
    def check_system_status(self):
        """检查系统状态"""
        current_date = datetime.now().strftime('%Y%m%d')
        
        print("\n" + "="*60)
        print("系统状态检查")
        print("="*60)
        
        # 检查目录
        directories = ['data/raw', 'data/processed', 'data/results', 'data/charts']
        for directory in directories:
            if os.path.exists(directory):
                file_count = len([f for f in os.listdir(directory) if f.endswith('.json') or f.endswith('.png')])
                print(f"📁 {directory}: {file_count} 个文件")
            else:
                print(f"❌ {directory}: 目录不存在")
        
        # 检查关键文件
        key_files = [
            f'data/raw/eastmoney_{current_date}.json',
            f'data/processed/processed_{current_date}.json',
            f'data/results/sentiment_report_{current_date}.json',
            f'data/charts/sentiment_dashboard_{current_date}.png',
            'data/reports/historical_analysis_7days.json',
            'data/charts/historical_trend_7days.png'
        ]
        
        print(f"\n关键文件检查:")
        for file_path in key_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✅ {file_path} - {file_size} 字节")
            else:
                print(f"❌ {file_path} - 文件不存在")
        
        print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票市场情绪分析系统')
    parser.add_argument('--mode', 
                       choices=['full', 'collect', 'analyze', 'visualize', 'test', 'batch', 'status'], 
                       default='full', 
                       help='运行模式: full(完整流程), collect(仅采集), analyze(仅分析), visualize(仅可视化), test(生成测试数据), batch(批量处理), status(系统状态)')
    parser.add_argument('--date', help='指定分析日期 (格式: YYYYMMDD)')
    parser.add_argument('--days', type=int, default=7, help='处理天数 (用于test和batch模式)')
    parser.add_argument('--no-history', action='store_true', help='不包含历史分析')
    
    args = parser.parse_args()
    
    system = StockSentimentSystem()
    
    print("股票市场情绪分析系统 - 完整版")
    print("=" * 50)
    
    success = False
    
    try:
        if args.mode == 'full':
            # 完整流程
            success = system.run_full_analysis(args.date, not args.no_history)
            
        elif args.mode == 'collect':
            # 仅数据采集
            success = system.run_data_collection()
            
        elif args.mode == 'analyze':
            # 仅分析（使用现有数据）
            if args.date:
                success = system.run_daily_analysis(args.date)
            else:
                success = system.run_daily_analysis()
            
        elif args.mode == 'visualize':
            # 仅可视化
            if args.date:
                success = system.run_visualization(args.date)
            else:
                success = system.run_visualization()
            
        elif args.mode == 'test':
            # 生成测试数据
            success = system.generate_test_data(args.days)
            if success:
                print(f"\n✅ {args.days}天测试数据生成完成！")
                print("现在可以运行分析: python main.py --mode batch --days 7")
            
        elif args.mode == 'batch':
            # 批量处理
            success = system.run_batch_analysis(args.days)
            
        elif args.mode == 'status':
            # 系统状态
            system.check_system_status()
            success = True
    
    except Exception as e:
        print(f"系统运行出错: {e}")
        traceback.print_exc()
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 系统运行成功！")
        print("📊 查看结果:")
        print("   - 原始数据: data/raw/")
        print("   - 处理数据: data/processed/")
        print("   - 分析报告: data/results/") 
        print("   - 可视化图表: data/charts/")
        print("   - 历史分析: data/reports/")
    else:
        print("❌ 系统运行失败，请检查错误信息。")
    print("=" * 50)

if __name__ == "__main__":
    main()