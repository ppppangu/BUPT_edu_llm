# -*- coding: utf-8 -*-
"""Flask 应用入口"""
from flask import Flask, jsonify, render_template, request

from backend.config import FRONTEND_DIR, HOST, PORT
from backend.services.news_service import news_service
from backend.scheduler import start_scheduler

# 创建 Flask 应用
app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR),
    static_folder=str(FRONTEND_DIR),
    static_url_path='/static'
)


# ==================== 页面路由 ====================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/news_search")
def news_search():
    return render_template("news_search.html")


@app.route("/translated_news")
def translated_news():
    return render_template("translated_news.html")


# ==================== API 路由 ====================

@app.route("/api/health")
def health():
    """健康检查接口"""
    return jsonify({"status": "ok"})


# --- 国内新闻 API ---

@app.route("/api/news")
def get_news():
    """获取筛选后的国内新闻数据"""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    keyword = request.args.get("keyword", "").strip()
    source = request.args.get("source", "").strip()

    result = news_service.get_news(
        start_date=start_date,
        end_date=end_date,
        keyword=keyword if keyword else None,
        source=source if source else None
    )
    return jsonify(result)


@app.route("/api/news/stats")
def get_news_stats():
    """获取国内新闻统计信息"""
    return jsonify(news_service.get_news_stats())


# --- 国际新闻 API ---

@app.route("/api/international")
def get_international_news():
    """获取筛选后的国际新闻数据"""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    keyword = request.args.get("keyword", "").strip()
    source = request.args.get("source", "").strip()

    result = news_service.get_international_news(
        start_date=start_date,
        end_date=end_date,
        keyword=keyword if keyword else None,
        source=source if source else None
    )
    return jsonify(result)


@app.route("/api/international/stats")
def get_international_stats():
    """获取国际新闻统计信息"""
    return jsonify(news_service.get_international_stats())


# --- AI 总结 API ---

@app.route("/api/summary/<news_type>")
def get_ai_summary(news_type):
    """
    获取AI总结
    news_type: domestic(国内) 或 international(国际)
    """
    return jsonify(news_service.get_ai_summary(news_type))


# ==================== 兼容旧 API（过渡期） ====================
# 注：这些路由保留一段时间，方便旧前端迁移

@app.route("/get_news")
def legacy_get_news():
    return get_news()


@app.route("/get_stats")
def legacy_get_stats():
    return get_news_stats()


@app.route("/get_translated_news")
def legacy_get_translated_news():
    return get_international_news()


@app.route("/get_translated_stats")
def legacy_get_translated_stats():
    return get_international_stats()


@app.route("/get_ai_summary/<news_type>")
def legacy_get_ai_summary(news_type):
    return get_ai_summary(news_type)


# ==================== 应用启动 ====================

def create_app():
    """创建应用实例（供 gunicorn 使用）"""
    # 启动后台调度器（如果没有数据则立即抓取）
    start_scheduler(run_immediately=True)
    return app


if __name__ == "__main__":
    print(f"启动 Flask 应用...")
    print(f"访问 http://{HOST}:{PORT} 查看网站")

    # 启动后台调度器
    start_scheduler()

    app.run(debug=True, host=HOST, port=PORT)
