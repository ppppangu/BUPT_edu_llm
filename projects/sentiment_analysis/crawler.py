#!/usr/bin/env python3
"""
数据采集模块 - 从多个数据源采集股票讨论数据
"""

import requests
import json
import time
import random
import logging
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class StockCrawler:
    def __init__(self):
        # 先定义所有属性
        self.stock_keywords = [
            '股票', '股市', 'A股', '大盘', '上证', '深证', '创业板', '科创板',
            '牛市', '熊市', '涨停', '跌停', '抄底', '逃顶', '加仓', '减仓'
        ]
        
        # 用户代理列表（必须在setup_session之前定义）
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # 然后初始化其他组件
        self.setup_directories()
        self.setup_logging()
        self.session = requests.Session()
        self.setup_session()
        
        print("StockCrawler 初始化完成")
    
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
        
        print("所有目录创建完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # 输出到控制台
                logging.FileHandler('logs/crawler.log', encoding='utf-8')  # 输出到文件
            ]
        )
        self.logger = logging.getLogger('StockCrawler')
        self.logger.info("日志系统初始化完成")
    
    def setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Connection': 'keep-alive',
        })
        print("HTTP会话设置完成")
    
    def random_delay(self):
        """随机延迟"""
        delay = random.uniform(1, 3)
        print(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def make_request(self, url, method='GET', **kwargs):
        """发送HTTP请求"""
        print(f"发送请求到: {url}")
        try:
            self.random_delay()
            response = self.session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            print(f"请求成功: {url}")
            return response
        except Exception as e:
            print(f"请求失败 {url}: {e}")
            self.logger.warning(f"请求失败 {url}: {e}")
            return None
    
    def save_data(self, data, source_name):
        """保存数据到文件"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{source_name}_{date_str}.json"
        filepath = os.path.join('data/raw', filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存: {filepath}")
            self.logger.info(f"数据已保存: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存数据失败: {e}")
            self.logger.error(f"保存数据失败: {e}")
            return None
    
    def is_stock_related(self, text):
        """检查文本是否与股票相关"""
        if not text:
            return False
        return any(keyword in text for keyword in self.stock_keywords)
    
    def crawl_eastmoney(self):
        """爬取东方财富股吧"""
        print("开始爬取东方财富股吧...")
        
        # 模拟数据 - 在实际使用中应该删除这部分
        sample_posts = [
            {
                'title': '大盘今日大涨，牛市信号明显',
                'author': '股市达人',
                'read_count': '1.5万',
                'comment_count': '256',
                'post_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': '科技股集体回调，注意风险控制',
                'author': '风险警示员', 
                'read_count': '2.3万',
                'comment_count': '189',
                'post_time': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': '北向资金持续流入，市场情绪回暖',
                'author': '资金观察',
                'read_count': '3.1万', 
                'comment_count': '342',
                'post_time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        result = {
            'source': 'eastmoney',
            'crawl_time': datetime.now().isoformat(),
            'data_count': len(sample_posts),
            'data': sample_posts
        }
        
        self.save_data(result, 'eastmoney')
        return result
    
    def crawl_xueqiu(self):
        """爬取雪球"""
        print("开始爬取雪球...")
        
        # 模拟数据
        posts = [
            {
                'title': '价值投资正当时，这些股票被低估',
                'source': 'xueqiu'
            },
            {
                'title': '市场震荡加剧，如何把握结构性机会',
                'source': 'xueqiu'
            },
            {
                'title': '财报季来临，关注业绩超预期个股',
                'source': 'xueqiu' 
            }
        ]
        
        result = {
            'source': 'xueqiu',
            'crawl_time': datetime.now().isoformat(),
            'data_count': len(posts),
            'data': posts
        }
        
        self.save_data(result, 'xueqiu')
        return result
    
    def crawl_weibo(self):
        """爬取微博热搜"""
        print("开始爬取微博热搜...")
        
        # 模拟数据
        topics = [
            {
                'title': 'A股大涨',
                'source': 'weibo'
            },
            {
                'title': '北向资金',
                'source': 'weibo'
            },
            {
                'title': '证监会最新政策',
                'source': 'weibo'
            }
        ]
        
        result = {
            'source': 'weibo',
            'crawl_time': datetime.now().isoformat(),
            'data_count': len(topics),
            'data': topics
        }
        
        self.save_data(result, 'weibo')
        return result
    
    def crawl_tieba(self):
        """爬取百度贴吧"""
        print("开始爬取百度贴吧...")
        
        # 模拟数据
        posts = [
            {
                'title': '大家觉得明天大盘会怎么走？',
                'bar_name': '股票吧',
                'author': '贴吧网友',
                'reply_count': '45'
            },
            {
                'title': '这个位置的创业板可以抄底吗？',
                'bar_name': '股票吧', 
                'author': '投资新手',
                'reply_count': '32'
            },
            {
                'title': '分享我的长线投资组合',
                'bar_name': '财经吧',
                'author': '老股民',
                'reply_count': '78'
            }
        ]
        
        result = {
            'source': 'tieba',
            'crawl_time': datetime.now().isoformat(),
            'data_count': len(posts),
            'data': posts
        }
        
        self.save_data(result, 'tieba')
        return result
    
    def run_all_crawlers(self):
        """运行所有爬虫"""
        print("=" * 50)
        print("开始执行数据采集任务...")
        print("=" * 50)
        
        results = {}
        crawlers = [
            ('东方财富', self.crawl_eastmoney),
            ('雪球', self.crawl_xueqiu),
            ('微博', self.crawl_weibo),
            ('贴吧', self.crawl_tieba)
        ]
        
        total_data = 0
        for name, crawler in crawlers:
            try:
                print(f"\n开始采集 {name} 数据...")
                results[name] = crawler()
                data_count = results[name].get('data_count', 0)
                total_data += data_count
                print(f"{name} 采集完成，获取 {data_count} 条数据")
            except Exception as e:
                print(f"{name} 采集失败: {e}")
                self.logger.error(f"{name} 采集失败: {e}")
                results[name] = {'error': str(e)}
            
            time.sleep(2)  # 采集间隔
        
        print("\n" + "=" * 50)
        print(f"数据采集完成，总计获取 {total_data} 条数据")
        print("=" * 50)
        
        return results

def main():
    """主函数"""
    print("股票市场情绪数据采集系统")
    print("正在启动...")
    
    try:
        crawler = StockCrawler()
        results = crawler.run_all_crawlers()
        
        # 显示汇总信息
        total_posts = 0
        for name, result in results.items():
            if isinstance(result, dict) and 'data_count' in result:
                total_posts += result['data_count']
                print(f"{name}: {result['data_count']} 条数据")
        
        print(f"\n总计: {total_posts} 条数据")
        print(f"数据文件保存在: data/raw/")
        
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()