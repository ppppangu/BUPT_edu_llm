#!/usr/bin/env python
"""测试代理连接和 AkShare 数据源

用法:
    python -m scripts.test_proxy
    python scripts/test_proxy.py
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_section(title: str):
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def test_proxy_env():
    """检查代理环境变量"""
    print_section("1. 代理环境变量")

    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    found = False

    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            # 隐藏密码部分
            if '@' in value:
                parts = value.split('@')
                masked = parts[0].rsplit(':', 1)[0] + ':***@' + parts[1]
            else:
                masked = value
            print(f"  {var}: {masked}")
            found = True

    if not found:
        print("  [!] 未检测到代理环境变量")

    return found


def test_basic_connection():
    """测试基本网络连接"""
    print_section("2. 基本网络连接")

    import requests

    test_urls = [
        ("httpbin.org", "https://httpbin.org/ip"),
        ("百度", "https://www.baidu.com"),
    ]

    for name, url in test_urls:
        try:
            start = time.time()
            resp = requests.get(url, timeout=10)
            elapsed = time.time() - start
            print(f"  [{name}] OK - {resp.status_code} ({elapsed:.2f}s)")
        except Exception as e:
            print(f"  [{name}] FAILED - {e}")


def test_akshare_hot_stocks():
    """测试 AkShare 热门股票接口（东方财富）"""
    print_section("3. AkShare 热门股票 (stock_hot_rank_em)")

    try:
        import akshare as ak

        print("  正在请求 emappdata.eastmoney.com ...")
        start = time.time()
        df = ak.stock_hot_rank_em()
        elapsed = time.time() - start

        if df is not None and not df.empty:
            print(f"  [OK] 获取成功，共 {len(df)} 条数据 ({elapsed:.2f}s)")
            print(f"  前3只热门股票:")
            for i, row in df.head(3).iterrows():
                code = row.get("股票代码", row.get("代码", ""))
                name = row.get("股票简称", row.get("股票名称", ""))
                price = row.get("最新价", 0)
                change = row.get("涨跌幅", 0)
                print(f"    {i+1}. {code} {name} ¥{price} ({change:+.2f}%)")
        else:
            print("  [!] 返回数据为空")

    except Exception as e:
        print(f"  [FAILED] {e}")


def test_akshare_stock_price():
    """测试 AkShare 股票价格接口（新浪）"""
    print_section("4. AkShare 股票价格 (stock_zh_a_spot)")

    try:
        import akshare as ak

        print("  正在请求新浪数据源 ...")
        start = time.time()
        df = ak.stock_zh_a_spot()
        elapsed = time.time() - start

        if df is not None and not df.empty:
            print(f"  [OK] 获取成功，共 {len(df)} 只股票 ({elapsed:.2f}s)")
            # 查找平安银行
            stock = df[df["代码"] == "000001"]
            if not stock.empty:
                row = stock.iloc[0]
                print(f"  样例: {row['代码']} {row['名称']} ¥{row['最新价']} ({row['涨跌幅']:+.2f}%)")
        else:
            print("  [!] 返回数据为空")

    except Exception as e:
        print(f"  [FAILED] {e}")


def test_akshare_kline():
    """测试 AkShare K线数据接口（163）"""
    print_section("5. AkShare K线数据 (stock_zh_a_daily)")

    try:
        import akshare as ak
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')

        print(f"  正在请求 163 数据源 (sz000001, {start_date}-{end_date}) ...")
        start = time.time()
        df = ak.stock_zh_a_daily(symbol="sz000001", start_date=start_date, end_date=end_date)
        elapsed = time.time() - start

        if df is not None and not df.empty:
            print(f"  [OK] 获取成功，共 {len(df)} 条K线 ({elapsed:.2f}s)")
            latest = df.iloc[-1]
            print(f"  最新: {latest['date']} 开:{latest['open']} 高:{latest['high']} 低:{latest['low']} 收:{latest['close']}")
        else:
            print("  [!] 返回数据为空")

    except Exception as e:
        print(f"  [FAILED] {e}")


def test_akshare_comment():
    """测试 AkShare 千股千评接口（东方财富）"""
    print_section("6. AkShare 千股千评 (stock_comment_em)")

    try:
        import akshare as ak

        print("  正在请求东方财富千股千评 ...")
        start = time.time()
        df = ak.stock_comment_em()
        elapsed = time.time() - start

        if df is not None and not df.empty:
            print(f"  [OK] 获取成功，共 {len(df)} 条数据 ({elapsed:.2f}s)")
            # 查找平安银行
            stock = df[df["代码"] == "000001"]
            if not stock.empty:
                row = stock.iloc[0]
                print(f"  样例: {row['代码']} {row['名称']} 综合得分:{row.get('综合得分', 'N/A')}")
        else:
            print("  [!] 返回数据为空")

    except Exception as e:
        print(f"  [FAILED] {e}")


def test_deepseek_api():
    """测试 DeepSeek API"""
    print_section("7. DeepSeek API")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("  [!] 未设置 DEEPSEEK_API_KEY 环境变量")
            return

        import requests

        print("  正在测试 DeepSeek API ...")
        start = time.time()

        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 10
            },
            timeout=30
        )
        elapsed = time.time() - start

        if resp.status_code == 200:
            print(f"  [OK] API 连接正常 ({elapsed:.2f}s)")
        else:
            print(f"  [FAILED] HTTP {resp.status_code}: {resp.text[:100]}")

    except Exception as e:
        print(f"  [FAILED] {e}")


def main():
    print("\n" + "=" * 50)
    print(" AlphaSenti 代理 & 数据源测试")
    print("=" * 50)

    # 加载 .env 文件
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"\n已加载: {env_path}")
    except ImportError:
        print("\n[!] python-dotenv 未安装，跳过 .env 加载")

    # 运行测试
    test_proxy_env()
    test_basic_connection()
    test_akshare_hot_stocks()
    test_akshare_stock_price()
    test_akshare_kline()
    test_akshare_comment()
    test_deepseek_api()

    print_section("测试完成")
    print()


if __name__ == "__main__":
    main()
