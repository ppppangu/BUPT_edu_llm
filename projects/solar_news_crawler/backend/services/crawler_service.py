# -*- coding: utf-8 -*-
"""爬虫调度服务"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.config import CRAWLERS_DIR, DATA_DIR


def cleanup_chrome_temp():
    """清理Chrome临时文件，避免多实例冲突"""
    try:
        temp_dir = tempfile.gettempdir()
        patterns = [
            os.path.join(temp_dir, 'chrome_*'),
            os.path.join(temp_dir, '.com.google.Chrome.*'),
            os.path.join(temp_dir, 'scoped_dir*')
        ]
        for pattern in patterns:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass


class CrawlerService:
    """爬虫调度服务"""

    CRAWLER_SCRIPTS = {
        'iea': 'iea_crawler.py',
        'pvmagazine': 'pv_magazine_crawler.py',
        'irena': 'irena_crawler.py',
        'combined': 'combined_crawler.py'
    }

    def __init__(self):
        self.crawlers_dir = CRAWLERS_DIR
        self.data_dir = DATA_DIR

    def run_single_crawler(self, crawler_name: str, timeout: int = 600) -> Dict:
        """
        运行单个爬虫

        Args:
            crawler_name: 爬虫名称 (iea, pvmagazine, irena, combined)
            timeout: 超时时间（秒）

        Returns:
            dict: {'success': bool, 'file': str, 'count': int, 'error': str}
        """
        if crawler_name not in self.CRAWLER_SCRIPTS:
            return {
                'success': False,
                'error': f'未知的爬虫名称: {crawler_name}',
                'file': None,
                'count': 0
            }

        script_path = self.crawlers_dir / self.CRAWLER_SCRIPTS[crawler_name]
        if not script_path.exists():
            return {
                'success': False,
                'error': f'爬虫脚本不存在: {script_path}',
                'file': None,
                'count': 0
            }

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动 {crawler_name.upper()} 爬虫")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=timeout,
                cwd=str(self.crawlers_dir)
            )

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"stderr: {result.stderr}")

            if result.returncode == 0:
                # 查找最新的输出文件
                output_dir = self.data_dir
                pattern = str(output_dir / f"{crawler_name}_*.json")
                files = glob.glob(pattern)

                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    try:
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            count = len(data) if isinstance(data, list) else 0
                    except Exception:
                        count = 0

                    return {
                        'success': True,
                        'file': latest_file,
                        'count': count,
                        'error': None
                    }

            return {
                'success': False,
                'error': f'爬虫返回错误码: {result.returncode}',
                'file': None,
                'count': 0
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'超时（>{timeout}秒）',
                'file': None,
                'count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file': None,
                'count': 0
            }

    def run_all_crawlers(self, timeout_per_crawler: int = 600) -> Dict:
        """
        运行所有爬虫（串行模式）

        Args:
            timeout_per_crawler: 每个爬虫的超时时间

        Returns:
            dict: 执行结果统计
        """
        print(f"开始执行爬虫任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        crawlers = ['iea', 'pvmagazine', 'irena', 'combined']
        results = {}

        for crawler_name in crawlers:
            results[crawler_name] = self.run_single_crawler(
                crawler_name,
                timeout_per_crawler
            )
            cleanup_chrome_temp()
            time.sleep(5)

        # 统计结果
        total_success = sum(1 for r in results.values() if r['success'])
        total_count = sum(r['count'] for r in results.values())
        failed_crawlers = [name for name, r in results.items() if not r['success']]

        return {
            "results": results,
            "total_success": total_success,
            "total_count": total_count,
            "failed_crawlers": failed_crawlers
        }


# 全局单例
crawler_service = CrawlerService()
