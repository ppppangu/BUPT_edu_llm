#!/usr/bin/env python3
"""
详细错误诊断脚本
"""

import json
import traceback
import sys
import os
from datetime import datetime

def check_data_files():
    """检查所有数据文件的状态"""
    current_date = datetime.now().strftime('%Y%m%d')
    
    print("=" * 60)
    print("数据文件状态检查")
    print("=" * 60)
    
    files_to_check = [
        f'data/raw/eastmoney_{current_date}.json',
        f'data/raw/xueqiu_{current_date}.json',
        f'data/raw/weibo_{current_date}.json', 
        f'data/raw/tieba_{current_date}.json',
        f'data/processed/processed_{current_date}.json',
        f'data/results/sentiment_report_{current_date}.json'
    ]
    
    for file_path in files_to_check:
        print(f"\n检查: {file_path}")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"  ✅ 文件存在，大小: {os.path.getsize(file_path)} 字节")
                
                # 检查数据结构
                if isinstance(data, dict):
                    print(f"  📊 数据类型: 字典")
                    for key, value in data.items():
                        print(f"    键: '{key}', 类型: {type(value).__name__}")
                        if isinstance(value, list) and len(value) > 0:
                            print(f"      列表长度: {len(value)}")
                            if len(value) > 0:
                                print(f"      第一个元素类型: {type(value[0]).__name__}")
                elif isinstance(data, list):
                    print(f"  📊 数据类型: 列表，长度: {len(data)}")
                    if len(data) > 0:
                        print(f"    第一个元素类型: {type(data[0]).__name__}")
                else:
                    print(f"  ⚠️  未知数据类型: {type(data).__name__}")
                    
            except Exception as e:
                print(f"  ❌ 文件解析错误: {e}")
        else:
            print(f"  ❌ 文件不存在")

def test_processor():
    """测试数据处理模块"""
    print("\n" + "=" * 60)
    print("测试数据处理模块")
    print("=" * 60)
    
    try:
        from processor import DataProcessor
        processor = DataProcessor()
        print("✅ DataProcessor 初始化成功")
        
        # 测试处理数据
        df = processor.process_daily_data()
        if not df.empty:
            print(f"✅ 数据处理成功，共 {len(df)} 条记录")
            print(f"   列名: {list(df.columns)}")
            
            # 检查关键列的数据类型
            for col in ['sentiment', 'sentiment_score', 'keywords']:
                if col in df.columns:
                    sample = df[col].iloc[0] if len(df) > 0 else None
                    print(f"   {col}: 类型={type(sample).__name__}, 示例={sample}")
        else:
            print("⚠️  没有处理后的数据")
            
    except Exception as e:
        print(f"❌ 数据处理测试失败: {e}")
        traceback.print_exc()

def test_calculator():
    """测试情绪计算模块"""
    print("\n" + "=" * 60)
    print("测试情绪计算模块")
    print("=" * 60)
    
    try:
        from calculator import SentimentCalculator
        calculator = SentimentCalculator()
        print("✅ SentimentCalculator 初始化成功")
        
        # 测试计算情绪指数
        report = calculator.generate_daily_sentiment_report()
        if report:
            print("✅ 情绪计算成功")
        else:
            print("⚠️  情绪计算返回空结果")
            
    except Exception as e:
        print(f"❌ 情绪计算测试失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("开始详细错误诊断...")
    check_data_files()
    test_processor()
    test_calculator()
    print("\n诊断完成！")