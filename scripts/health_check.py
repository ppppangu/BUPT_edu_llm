#!/usr/bin/env python3
"""
BUPT EDU LLM Platform - Health Check Script
This script checks the health status of all subprojects
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List
import urllib.request
import urllib.error

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


# Service configurations
SERVICES = [
    {
        'name': 'Solar News Crawler',
        'url': 'http://localhost:5000',
        'health_endpoint': '/api/health',
        'enabled': True
    },
    # Add more services as needed
    # {
    #     'name': 'Sentiment Analysis',
    #     'url': 'http://localhost:5001',
    #     'health_endpoint': '/api/health',
    #     'enabled': False
    # }
]


def check_service(service: Dict) -> Dict:
    """
    Check the health status of a single service

    Args:
        service: Service configuration dictionary

    Returns:
        Status dictionary with 'online', 'latency', and 'error' keys
    """
    if not service.get('enabled', True):
        return {
            'online': False,
            'latency': 0,
            'error': 'Service is disabled'
        }

    url = service['url'] + service.get('health_endpoint', '')
    start_time = time.time()

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'BUPT-HealthCheck/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            status_code = response.getcode()

            if status_code == 200:
                return {
                    'online': True,
                    'latency': round(latency, 2),
                    'error': None
                }
            else:
                return {
                    'online': False,
                    'latency': 0,
                    'error': f'HTTP {status_code}'
                }

    except urllib.error.HTTPError as e:
        return {
            'online': False,
            'latency': 0,
            'error': f'HTTP {e.code}: {e.reason}'
        }
    except urllib.error.URLError as e:
        return {
            'online': False,
            'latency': 0,
            'error': f'Connection error: {e.reason}'
        }
    except Exception as e:
        return {
            'online': False,
            'latency': 0,
            'error': str(e)
        }


def run_health_check(verbose: bool = False, json_output: bool = False) -> bool:
    """
    Run health checks on all services

    Args:
        verbose: Print detailed information
        json_output: Output results in JSON format

    Returns:
        True if all services are healthy, False otherwise
    """
    results = []
    all_healthy = True

    for service in SERVICES:
        if not service.get('enabled', True):
            continue

        status = check_service(service)

        results.append({
            'name': service['name'],
            'url': service['url'],
            'online': status['online'],
            'latency': status['latency'],
            'error': status['error']
        })

        if not status['online']:
            all_healthy = False

    # Output results
    if json_output:
        output = {
            'timestamp': datetime.now().isoformat(),
            'all_healthy': all_healthy,
            'services': results
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"{Colors.BLUE}========================================{Colors.NC}")
        print(f"{Colors.BLUE}  BUPT EDU LLM Health Check{Colors.NC}")
        print(f"{Colors.BLUE}========================================{Colors.NC}")
        print()

        for result in results:
            status_symbol = '✓' if result['online'] else '✗'
            status_color = Colors.GREEN if result['online'] else Colors.RED

            print(f"{status_color}{status_symbol} {result['name']}{Colors.NC}")
            print(f"  URL: {result['url']}")

            if result['online']:
                print(f"  Status: {Colors.GREEN}ONLINE{Colors.NC}")
                print(f"  Latency: {result['latency']}ms")
            else:
                print(f"  Status: {Colors.RED}OFFLINE{Colors.NC}")
                if result['error']:
                    print(f"  Error: {result['error']}")

            print()

        print(f"{Colors.BLUE}========================================{Colors.NC}")
        if all_healthy:
            print(f"{Colors.GREEN}  All services are healthy!{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}  Some services are down!{Colors.NC}")
        print(f"{Colors.BLUE}========================================{Colors.NC}")
        print()

    return all_healthy


def main():
    parser = argparse.ArgumentParser(description='BUPT EDU LLM Platform Health Check')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-j', '--json', action='store_true', help='JSON output format')
    parser.add_argument('-w', '--watch', type=int, metavar='SECONDS',
                        help='Continuously monitor services every N seconds')

    args = parser.parse_args()

    try:
        if args.watch:
            # Continuous monitoring mode
            print(f"Monitoring services every {args.watch} seconds... (Press Ctrl+C to stop)")
            print()
            while True:
                run_health_check(verbose=args.verbose, json_output=args.json)
                time.sleep(args.watch)
                if not args.json:
                    print("\n" + "="*40 + "\n")
        else:
            # Single check
            all_healthy = run_health_check(verbose=args.verbose, json_output=args.json)
            sys.exit(0 if all_healthy else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Health check stopped by user{Colors.NC}")
        sys.exit(0)


if __name__ == '__main__':
    main()
