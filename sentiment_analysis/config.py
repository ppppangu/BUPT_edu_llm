#!/usr/bin/env python3
"""
配置文件 - 股票市场情绪分析系统
"""

# 系统配置
SYSTEM_CONFIG = {
    'data_dir': 'data',
    'log_dir': 'logs',
    'max_workers': 4,
    'timezone': 'Asia/Shanghai'
}

# 爬虫配置
CRAWLER_CONFIG = {
    'timeout': 15,
    'retry_times': 3,
    'delay_range': (1, 3),
    'max_pages': 3,
    'user_agent_rotation': True
}

# 数据源配置
DATA_SOURCES = {
    'eastmoney': {
        'base_url': 'http://guba.eastmoney.com',
        'list_url': 'http://guba.eastmoney.com/list,default_{}.html',
        'enabled': True,
        'weight': 1.2
    },
    'xueqiu': {
        'base_url': 'https://xueqiu.com',
        'hot_url': 'https://xueqiu.com/hots',
        'enabled': True,
        'weight': 1.1
    },
    'weibo': {
        'base_url': 'https://s.weibo.com',
        'hot_url': 'https://s.weibo.com/top/summary',
        'enabled': True,
        'weight': 0.9
    },
    'tieba': {
        'base_url': 'https://tieba.baidu.com',
        'stock_bar': 'https://tieba.baidu.com/f?kw=股票',
        'finance_bar': 'https://tieba.baidu.com/f?kw=财经',
        'enabled': True,
        'weight': 0.8
    }
}

# 情感分析配置
SENTIMENT_CONFIG = {
    'min_text_length': 5,
    'confidence_threshold': 0.6,
    'intensity_threshold': 0.3,
    'source_weights': {
        'eastmoney': 1.2,
        'xueqiu': 1.1, 
        'weibo': 0.9,
        'tieba': 0.8
    }
}

# 情绪指数配置
INDEX_CONFIG = {
    'normalization_range': (0, 100),
    'neutral_zone': (45, 55),
    'market_states': {
        '极度乐观': (80, 100),
        '非常乐观': (70, 80),
        '乐观': (60, 70),
        '略微乐观': (55, 60),
        '中性': (45, 55),
        '略微悲观': (40, 45),
        '悲观': (30, 40),
        '非常悲观': (20, 30),
        '极度悲观': (0, 20)
    }
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'chart_size': (12, 8),
    'dpi': 300,
    'color_scheme': {
        'positive': '#2ecc71',
        'negative': '#e74c3c',
        'neutral': '#3498db',
        'background': '#ecf0f1'
    }
}