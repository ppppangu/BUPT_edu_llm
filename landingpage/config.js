// Project Configuration
// This file contains the configuration for all subprojects in the platform

const CONFIG = {
    // Projects list - add new projects here
    projects: [
        {
            id: 'solar_news',
            name: 'Solar News Crawler',
            icon: '☀️',
            description: '多来源国际太阳能新闻聚合系统，自动抓取、翻译和展示全球太阳能行业动态',
            path: '/solar_news/',
            port: 5000,
            status: 'online', // online | offline | maintenance
            tags: ['新闻聚合', 'Web爬虫', '翻译', 'Flask'],
            metadata: {
                version: 'v0.1.0',
                lastUpdate: '2025-11-19',
                uptime: '99.5%'
            }
        },
        // Example for future projects:
        // {
        //     id: 'sentiment_analysis',
        //     name: 'Sentiment Analysis',
        //     icon: '📊',
        //     description: '股票市场情感分析系统，基于多平台数据的情绪指数计算和可视化',
        //     path: '/sentiment/',
        //     port: 5001,
        //     status: 'offline',
        //     tags: ['情感分析', 'NLP', '可视化', '数据分析'],
        //     metadata: {
        //         version: 'v0.1.0',
        //         lastUpdate: '2025-11-19',
        //         uptime: '0%'
        //     }
        // }
    ],

    // Platform stats
    stats: {
        totalProjects: 1,
        activeProjects: 1,
        systemUptime: '99.5%',
        dataProcessed: '12.5k'
    },

    // API endpoints for health checks
    healthCheckEndpoints: {
        solar_news: '/solar_news/api/health'
    }
};

// Make CONFIG available globally
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}
