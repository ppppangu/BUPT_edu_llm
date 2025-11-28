#!/usr/bin/env python3
"""
增强版测试数据生成器 - 生成一周内的测试数据，包含情绪波动
"""

import json
import random
import os
from datetime import datetime, timedelta

class EnhancedTestDataGenerator:
    def __init__(self):
        self.setup_directories()
        
        # 扩展的股票相关词汇
        self.stock_terms = {
            "positive": [
                "牛市来了", "大涨在即", "突破压力位", "主力资金流入", "技术面看好",
                "估值合理", "政策利好", "经济复苏", "外资加仓", "龙头领涨",
                "放量上涨", "突破前高", "金叉形成", "底部放量", "价值回归",
                "业绩超预期", "行业景气", "资金青睐", "趋势向上", "买入信号",
                "北向资金大幅流入", "政策暖风频吹", "市场信心恢复", "技术指标走强",
                "估值修复空间大", "结构性机会凸显", "春季行情启动", "反弹一触即发"
            ],
            "negative": [
                "熊市开启", "大跌风险", "跌破支撑", "主力出货", "技术面走坏",
                "估值过高", "政策利空", "经济下滑", "外资撤离", "龙头领跌",
                "缩量下跌", "跌破前低", "死叉形成", "顶部放量", "泡沫破裂",
                "业绩不及预期", "行业低迷", "资金流出", "趋势向下", "卖出信号",
                "北向资金持续流出", "监管政策收紧", "市场恐慌情绪蔓延", "技术指标恶化",
                "估值仍然偏高", "风险大于机会", "调整尚未结束", "谨慎观望为主"
            ],
            "neutral": [
                "震荡整理", "横盘调整", "方向不明", "观望为主", "等待突破",
                "量能萎缩", "多空平衡", "区间震荡", "技术修复", "等待信号",
                "政策真空期", "数据平淡", "市场冷静", "平稳运行", "蓄势待发",
                "市场分歧加大", "上下两难", "胶着状态", "存量博弈", "风格切换"
            ]
        }
        
        self.authors = [
            "股海沉浮", "价值投资者", "短线狙击手", "趋势交易者", "财经观察员",
            "股市老司机", "技术分析师", "基本面研究", "量化投资", "波段操作",
            "长线持有", "打板高手", "低吸选手", "追涨杀跌", "理性投资",
            "华尔街之狼", "私募大佬", "游资传奇", "散户代言人", "市场老兵"
        ]
        
        self.sources = ["eastmoney", "xueqiu", "weibo", "tieba"]
        
        # 模拟一周的情绪波动模式
        self.sentiment_pattern = {
            0: {"positive": 0.5, "negative": 0.2, "neutral": 0.3},   # 今天 - 乐观
            -1: {"positive": 0.4, "negative": 0.3, "neutral": 0.3},  # 1天前 - 略微乐观
            -2: {"positive": 0.3, "negative": 0.4, "neutral": 0.3},  # 2天前 - 中性偏悲观
            -3: {"positive": 0.2, "negative": 0.5, "neutral": 0.3},  # 3天前 - 悲观
            -4: {"positive": 0.3, "negative": 0.3, "neutral": 0.4},  # 4天前 - 中性
            -5: {"positive": 0.4, "negative": 0.2, "neutral": 0.4},  # 5天前 - 略微乐观
            -6: {"positive": 0.5, "negative": 0.3, "neutral": 0.2}   # 6天前 - 乐观
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
    
    def create_sample_sentiment_words(self):
        """创建示例情感词典"""
        sentiment_words = {
            "positive": [
                "涨", "上涨", "拉升", "反弹", "突破", "牛市", "大涨", "暴涨", "飙升",
                "看好", "乐观", "买入", "加仓", "抄底", "机会", "黄金坑", "价值",
                "强势", "放量", "突破", "创新高", "赚钱", "盈利", "收益", "红利",
                "龙头", "领涨", "涨停", "牛股", "黑马", "价值投资", "长期持有",
                "低估", "便宜", "底部", "反转", "企稳", "修复", "回暖", "活跃",
                "惊喜", "利好", "好消息", "突破", "加速", "主升浪", "行情", "机会",
                "收益", "赚钱效应", "资金流入", "政策支持", "经济向好", "复苏"
            ],
            "negative": [
                "跌", "下跌", "回落", "回调", "跌破", "熊市", "大跌", "暴跌", "崩盘",
                "看空", "悲观", "卖出", "减仓", "逃顶", "风险", "套牢", "割肉",
                "弱势", "缩量", "破位", "创新低", "亏钱", "亏损", "被套", "深套",
                "垃圾股", "领跌", "跌停", "熊股", "泡沫", "高估", "贵", "顶部",
                "利空", "暴雷", "退市", "警示", "风险", "危机", "恐慌", "崩盘",
                "失望", "担忧", "问题", "困难", "压力", "调整", "下跌中继", "阴跌",
                "资金流出", "政策风险", "经济下行", "衰退", "危机", "不确定性"
            ],
            "neutral": [
                "震荡", "横盘", "整理", "盘整", "平稳", "中性", "观望", "等待",
                "调整", "波动", "反复", "胶着", "僵持", "平衡", "稳定", "持平",
                "关注", "观察", "分析", "研究", "讨论", "思考", "评估", "考虑",
                "可能", "或许", "大概", "预计", "预测", "展望", "前景", "趋势"
            ]
        }
        
        with open('config/sentiment_words.json', 'w', encoding='utf-8') as f:
            json.dump(sentiment_words, f, ensure_ascii=False, indent=2)
        
        print("情感词典已创建: config/sentiment_words.json")
    
    def generate_content(self, sentiment, day_offset=0):
        """生成更真实的帖子内容"""
        # 基础句子模板
        templates = {
            "positive": [
                "今天{}表现强势，{}，建议{}。技术面显示{}，资金面{}。",
                "经过{}的分析，{}板块{}，目标价{}。{}资金持续流入，{}。",
                "{}政策利好{}，{}基本面{}，{}值得重点关注。{}。",
                "市场情绪{}，{}形成{}，{}机会凸显。建议{}。",
                "{}突破{}关键位置，{}放量上涨，{}行情可期。{}。"
            ],
            "negative": [
                "{}出现{}信号，{}风险加大，建议{}。技术面{}，资金面{}。",
                "{}板块{}，{}可能{}，注意{}。{}资金流出，{}。",
                "{}政策收紧{}，{}基本面{}，{}需要谨慎。{}。",
                "市场情绪{}，{}显示{}，需要{}防范风险。建议{}。",
                "{}跌破{}支撑位，{}缩量下跌，{}调整继续。{}。"
            ],
            "neutral": [
                "{}目前{}，{}方向不明，建议{}。等待{}信号。",
                "{}板块{}，{}需要{}观察。{}资金观望，{}。",
                "{}政策真空{}，{}数据{}，{}保持耐心。{}。",
                "市场情绪{}，{}处于{}，{}等待突破。建议{}。",
                "{}在{}区间震荡，{}量能萎缩，{}等待方向选择。{}。"
            ]
        }
        
        # 填充词汇
        fillers = {
            "positive": {
                "表现强势": ["大盘", "创业板", "科技股", "消费板块", "新能源", "医药"],
                "建议": ["逢低加仓", "坚定持有", "分批买入", "布局优质标的", "适度参与"],
                "技术面显示": ["MACD金叉", "KDJ向上", "RSI走强", "均线多头排列", "突破压力位"],
                "资金面": ["北向资金大幅流入", "主力资金净流入", "机构资金加仓", "游资活跃"],
                "政策利好": ["支持", "鼓励", "放开", "补贴", "减税"],
                "值得重点关注": ["龙头股", "成长股", "价值股", "题材股", "蓝筹股"]
            },
            "negative": {
                "风险加大": ["调整", "回调", "下跌", "震荡", "破位"],
                "建议": ["控制仓位", "止损止盈", "风险防范", "谨慎操作", "减仓观望"],
                "技术面": ["出现顶背离", "形成死叉", "跌破支撑", "趋势转弱", "均线空头排列"],
                "资金面": ["外资撤离", "主力出货", "机构减仓", "游资撤退"],
                "政策收紧": ["监管", "限制", "调控", "审查", "去杠杆"],
                "需要谨慎": ["高位股", "概念股", "问题股", "高估值股", "ST股"]
            },
            "neutral": {
                "方向不明": ["震荡整理", "横盘调整", "多空博弈", "胶着状态", "选择方向"],
                "建议": ["观望为主", "耐心等待", "谨慎操作", "控制仓位", "不追涨杀跌"],
                "处于": ["修复中", "整理中", "酝酿中", "转换中", "平衡中"],
                "等待": ["突破", "放量", "政策明朗", "数据公布", "市场选择"],
                "资金观望": ["外资", "主力", "机构", "游资", "散户"]
            }
        }
        
        template = random.choice(templates[sentiment])
        content = template
        
        # 智能替换
        for key, values in fillers[sentiment].items():
            if key in content:
                content = content.replace(key, random.choice(values), 1)
        
        # 根据日期偏移调整语气强度
        intensity_modifiers = {
            "positive": ["非常", "特别", "明显", "显著", ""],
            "negative": ["非常", "特别", "明显", "显著", ""],
            "neutral": ["仍然", "继续", "持续", "依旧", ""]
        }
        
        # 添加一些专业分析术语
        analysis_terms = [
            "从技术面看，", "基本面分析显示，", "资金流向表明，", 
            "市场情绪指标显示，", "宏观经济环境", "行业景气度"
        ]
        
        if random.random() > 0.7:  # 30%的概率添加分析术语
            content = random.choice(analysis_terms) + content
        
        # 添加免责声明
        disclaimers = [
            "个人观点，仅供参考。",
            "投资有风险，入市需谨慎。",
            "以上分析不构成投资建议。",
            "市场有风险，投资需谨慎。",
            "仅供参考，盈亏自负。"
        ]
        
        content += " " + random.choice(disclaimers)
        
        return content
    
    def generate_post(self, source, sentiment, day_offset=0):
        """生成单个帖子"""
        title = random.choice(self.stock_terms[sentiment])
        
        # 生成更真实的时间（考虑日期偏移）
        post_time = datetime.now() + timedelta(days=day_offset, 
                                              hours=random.randint(9, 15),  # 交易时间
                                              minutes=random.randint(0, 59))
        
        # 根据来源生成不同的数据结构
        base_post = {
            "title": title,
            "author": random.choice(self.authors),
            "read_count": random.randint(1000, 50000),
            "comment_count": random.randint(10, 500),
            "post_time": post_time.strftime('%Y-%m-%d %H:%M:%S'),
            "content": self.generate_content(sentiment, day_offset)
        }
        
        # 根据不同数据源添加特定字段
        if source == "eastmoney":
            base_post["read_count"] = f"{base_post['read_count'] // 10000}万" if base_post['read_count'] > 10000 else str(base_post['read_count'])
            base_post["comment_count"] = f"{base_post['comment_count'] // 100}百" if base_post['comment_count'] > 100 else str(base_post['comment_count'])
        elif source == "xueqiu":
            base_post["retweet_count"] = random.randint(0, 200)
        elif source == "weibo":
            base_post["hot_count"] = random.randint(1000, 50000)
        elif source == "tieba":
            base_post["bar_name"] = random.choice(["股票吧", "财经吧", "股市吧", "投资吧", "理财吧"])
            base_post["reply_count"] = str(base_post["comment_count"])
        
        return base_post
    
    def generate_source_data(self, source, date_str, day_offset=0, post_count=20):
        """为数据源生成测试数据"""
        # 根据日期偏移获取情绪分布
        sentiment_dist = self.sentiment_pattern.get(day_offset, {"positive": 0.4, "negative": 0.3, "neutral": 0.3})
        
        # 计算每种情绪的数量
        positive_count = int(post_count * sentiment_dist["positive"])
        negative_count = int(post_count * sentiment_dist["negative"]) 
        neutral_count = post_count - positive_count - negative_count
        
        posts = []
        
        # 生成积极情绪帖子
        for _ in range(positive_count):
            post = self.generate_post(source, "positive", day_offset)
            posts.append(post)
        
        # 生成消极情绪帖子
        for _ in range(negative_count):
            post = self.generate_post(source, "negative", day_offset)
            posts.append(post)
        
        # 生成中性情绪帖子
        for _ in range(neutral_count):
            post = self.generate_post(source, "neutral", day_offset)
            posts.append(post)
        
        # 打乱顺序
        random.shuffle(posts)
        
        data = {
            "source": source,
            "crawl_time": datetime.now().isoformat(),
            "data_count": len(posts),
            "data": posts
        }
        
        return data
    
    def generate_daily_test_data(self, date_str=None, day_offset=0, posts_per_source=20):
        """生成单日测试数据"""
        if date_str is None:
            target_date = datetime.now() + timedelta(days=day_offset)
            date_str = target_date.strftime('%Y%m%d')
        
        print(f"生成 {date_str} 的测试数据 (日期偏移: {day_offset}天)...")
        
        daily_stats = {}
        
        for source in self.sources:
            source_data = self.generate_source_data(source, date_str, day_offset, posts_per_source)
            
            filename = f"{source}_{date_str}.json"
            filepath = os.path.join('data/raw', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(source_data, f, ensure_ascii=False, indent=2)
            
            # 统计情绪分布
            sentiment_count = {"positive": 0, "negative": 0, "neutral": 0}
            for post in source_data['data']:
                # 根据标题判断情绪
                title = post['title'].lower()
                if any(word in title for word in ['涨', '牛', '好', '买入', '突破']):
                    sentiment_count['positive'] += 1
                elif any(word in title for word in ['跌', '熊', '坏', '卖出', '跌破']):
                    sentiment_count['negative'] += 1
                else:
                    sentiment_count['neutral'] += 1
            
            daily_stats[source] = {
                'total': len(source_data['data']),
                'sentiment_dist': sentiment_count
            }
            
            print(f"  已生成 {source} 数据: {filename}")
        
        # 打印当日统计
        total_posts = sum(stats['total'] for stats in daily_stats.values())
        print(f"  当日总计: {total_posts} 条数据")
        
        return daily_stats
    
    def generate_weekly_data(self, days=7, posts_per_source=20):
        """生成一周的测试数据"""
        print(f"开始生成 {days} 天的测试数据...")
        print("情绪波动模式:")
        
        # 显示情绪模式
        for day_offset in range(-days+1, 1):
            sentiment_dist = self.sentiment_pattern.get(day_offset, {"positive": 0.33, "negative": 0.33, "neutral": 0.34})
            date_str = (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            print(f"  {date_str}: 积极{sentiment_dist['positive']:.0%}, 消极{sentiment_dist['negative']:.0%}, 中性{sentiment_dist['neutral']:.0%}")
        
        weekly_stats = {}
        
        for day_offset in range(-days+1, 1):  # 从-days+1到0（今天）
            date_str = (datetime.now() + timedelta(days=day_offset)).strftime('%Y%m%d')
            daily_stats = self.generate_daily_test_data(date_str, day_offset, posts_per_source)
            weekly_stats[date_str] = daily_stats
        
        # 生成周度总结
        self.generate_weekly_summary(weekly_stats, days)
        
        return weekly_stats
    
    def generate_weekly_summary(self, weekly_stats, days):
        """生成周度数据总结"""
        summary = {
            "generation_time": datetime.now().isoformat(),
            "period_days": days,
            "daily_stats": {},
            "total_posts": 0,
            "overall_sentiment": {"positive": 0, "negative": 0, "neutral": 0}
        }
        
        for date_str, daily_data in weekly_stats.items():
            date_total = 0
            date_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
            
            for source, stats in daily_data.items():
                date_total += stats['total']
                for sentiment, count in stats['sentiment_dist'].items():
                    date_sentiment[sentiment] += count
            
            summary["daily_stats"][date_str] = {
                "total_posts": date_total,
                "sentiment_distribution": date_sentiment
            }
            
            summary["total_posts"] += date_total
            for sentiment, count in date_sentiment.items():
                summary["overall_sentiment"][sentiment] += count
        
        # 保存总结
        summary_file = os.path.join('data', 'weekly_test_data_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n周度数据总结已保存: {summary_file}")
        
        # 打印简要统计
        print(f"\n=== {days}天测试数据生成完成 ===")
        print(f"总帖子数: {summary['total_posts']}")
        print(f"整体情绪分布:")
        for sentiment, count in summary['overall_sentiment'].items():
            percentage = count / summary['total_posts'] * 100
            print(f"  {sentiment}: {count} 条 ({percentage:.1f}%)")
        
        print(f"\n数据文件保存在: data/raw/")
        print("现在可以运行分析系统了!")

def main():
    """主函数"""
    generator = EnhancedTestDataGenerator()
    
    print("=" * 60)
    print("增强版股票情绪测试数据生成器")
    print("生成一周内包含情绪波动的测试数据")
    print("=" * 60)
    
    # 创建情感词典
    generator.create_sample_sentiment_words()
    
    # 生成一周数据（今天+过去6天，共7天）
    generator.generate_weekly_data(days=7, posts_per_source=25)
    
    print("\n" + "=" * 60)
    print("✅ 测试数据生成完成！")
    print("运行分析命令: python main.py --mode analyze")
    print("=" * 60)

if __name__ == "__main__":
    main()