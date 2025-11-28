#!/usr/bin/env python3
"""
数据处理模块 - 清洗、分词、情感分析
"""

import json
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
import re
import os
import logging
from datetime import datetime
from collections import Counter

class DataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.setup_logging()
        
        # 加载情感词典
        self.sentiment_words = self.load_sentiment_words()
        
        # 初始化jieba
        self.setup_jieba()
        
        # 情绪强度词
        self.intensity_words = {
            '强烈': 2.0, '非常': 1.8, '极度': 2.2, '特别': 1.7,
            '比较': 1.3, '稍微': 0.8, '有点': 0.9, '十分': 1.6
        }
    
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('DataProcessor')
    
    def setup_jieba(self):
        """设置jieba分词"""
        # 添加股票领域词汇
        stock_words = ['股票', '股市', 'A股', '大盘', '牛市', '熊市', '涨停', '跌停']
        for word in stock_words:
            jieba.add_word(word)
    
    def load_sentiment_words(self):
        """加载情感词典"""
        config_file = 'config/sentiment_words.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载情感词典失败: {e}")
        
        # 默认情感词典
        return {
            "positive": ["涨", "上涨", "牛市", "买入", "看好", "机会", "赚钱", "突破"],
            "negative": ["跌", "下跌", "熊市", "卖出", "风险", "亏钱", "套牢", "崩盘"],
            "neutral": ["震荡", "横盘", "观望", "调整", "平稳"]
        }
    
    def load_raw_data(self, date_str=None):
        """加载原始数据"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        raw_data_dir = os.path.join(self.data_dir, 'raw')
        data_files = []
        
        for filename in os.listdir(raw_data_dir):
            if date_str in filename:
                data_files.append(os.path.join(raw_data_dir, filename))
        
        if not data_files:
            self.logger.warning(f"未找到 {date_str} 的原始数据")
            return []
        
        all_data = []
        for file_path in data_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'data' in data:
                        for item in data['data']:
                            item['source'] = data.get('source', 'unknown')
                        all_data.extend(data['data'])
            except Exception as e:
                self.logger.error(f"加载数据失败 {file_path}: {e}")
        
        self.logger.info(f"加载 {len(all_data)} 条原始数据")
        return all_data
    
    def preprocess_text(self, text):
        """文本预处理"""
        if not text:
            return ""
        
        # 清理文本
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def analyze_sentiment(self, text):
        """分析文本情感"""
        if not text:
            return {'sentiment': 'neutral', 'score': 0.0}
        
        words = jieba.lcut(text)
        
        positive_score = 0.0
        negative_score = 0.0
        
        for i, word in enumerate(words):
            word_score = 1.0
            
            # 检查强度词
            if i > 0 and words[i-1] in self.intensity_words:
                word_score *= self.intensity_words[words[i-1]]
            
            if word in self.sentiment_words['positive']:
                positive_score += word_score
            elif word in self.sentiment_words['negative']:
                negative_score += word_score
        
        total_score = positive_score + negative_score
        if total_score == 0:
            return {'sentiment': 'neutral', 'score': 0.0}
        
        net_score = (positive_score - negative_score) / total_score
        final_score = max(-1.0, min(1.0, net_score))
        
        if final_score > 0.1:
            sentiment = 'positive'
        elif final_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': final_score,
            'positive_score': positive_score,
            'negative_score': negative_score
        }
    
    def extract_keywords(self, text, top_k=10):
        """提取关键词"""
        if not text:
            return []
        
        try:
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
            return keywords
        except Exception as e:
            self.logger.warning(f"提取关键词失败: {e}")
            return []
    
    def calculate_post_weight(self, post):
        """计算帖子权重"""
        weight = 1.0
        
        # 来源权重
        source_weights = {'eastmoney': 1.2, 'xueqiu': 1.1, 'weibo': 0.9, 'tieba': 0.8}
        source = post.get('source', '')
        weight *= source_weights.get(source, 1.0)
        
        return weight
    
    def process_daily_data(self, date_str=None):
        """处理单日数据"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"开始处理 {date_str} 的数据")
        
        # 加载原始数据
        raw_data = self.load_raw_data(date_str)
        if not raw_data:
            self.logger.warning("没有原始数据可处理")
            return pd.DataFrame()
        
        processed_data = []
        
        for i, post in enumerate(raw_data):
            try:
                # 提取文本内容
                title = post.get('title', '')
                content = post.get('content', '')
                full_text = f"{title} {content}"
                
                # 预处理
                cleaned_text = self.preprocess_text(full_text)
                if len(cleaned_text) < 5:
                    continue
                
                # 情感分析
                sentiment_result = self.analyze_sentiment(cleaned_text)
                
                # 提取关键词
                keywords = self.extract_keywords(cleaned_text)
                
                # 计算权重
                weight = self.calculate_post_weight(post)
                
                # 构建处理后的数据
                processed_post = {
                    'id': f"{post.get('source', 'unknown')}_{i}",
                    'source': post.get('source', 'unknown'),
                    'title': title,
                    'content': cleaned_text,
                    'sentiment': sentiment_result['sentiment'],
                    'sentiment_score': sentiment_result['score'],
                    'keywords': [kw[0] for kw in keywords],
                    'weight': weight,
                    'read_count': self.parse_numeric_value(post.get('read_count', 0)),
                    'comment_count': self.parse_numeric_value(post.get('comment_count', 0)),
                    'post_time': post.get('post_time', ''),
                    'processed_time': datetime.now().isoformat()
                }
                
                processed_data.append(processed_post)
                
            except Exception as e:
                self.logger.warning(f"处理数据失败: {e}")
                continue
        
        # 转换为DataFrame
        df = pd.DataFrame(processed_data)
        
        if not df.empty:
            # 保存处理后的数据
            output_file = os.path.join(self.data_dir, 'processed', f'processed_{date_str}.json')
            df.to_json(output_file, orient='records', force_ascii=False, indent=2)
            self.logger.info(f"处理完成，共 {len(df)} 条数据")
        else:
            self.logger.warning("没有有效的数据被处理")
        
        return df
    
    def parse_numeric_value(self, value):
        """解析数值"""
        if isinstance(value, (int, float)):
            return int(value)
        
        value_str = str(value).strip()
        try:
            if '万' in value_str:
                return int(float(value_str.replace('万', '')) * 10000)
            else:
                return int(float(value_str))
        except:
            return 0