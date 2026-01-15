# create_structure.py
import os

BASE_DIR = "pro_charging"

structure = {
    "src": {
        "__init__.py": "",
        "main.py": "# 项目主入口\n",
        "config.py": "# 配置信息\n",
        "constants.py": "# 常量定义\n",
        "auth": {
            "__init__.py": "",
            "youdian_login.py": "# 登录模块\n",
            "captcha_solver.py": "# 验证码处理\n",
        },
        "scrapers": {
            "__init__.py": "",
            "base_scraper.py": "# 基础抓取类\n",
            "order_scraper.py": "# 订单抓取\n",
            "device_scraper.py": "# 设备状态抓取\n",
            "income_scraper.py": "# 收入统计\n",
            "alarm_scraper.py": "# 告警抓取\n",
        },
        "processors": {
            "__init__.py": "",
            "data_cleaner.py": "# 数据清洗\n",
            "analyzer.py": "# 分析逻辑\n",
            "metrics.py": "# 指标计算\n",
        },
        "exporters": {
            "__init__.py": "",
            "csv_exporter.py": "# CSV输出\n",
            "excel_exporter.py": "# Excel输出\n",
            "database": {
                "sqlite_handler.py": "# SQLite处理\n",
            },
        },
        "notifications": {
            "__init__.py": "",
            "base_notifier.py": "# 通知基类\n",
            "feishu_notifier.py": "# 飞书通知\n",
            "dingtalk_notifier.py": "# 钉钉通知\n",
            "wecom_notifier.py": "# 企业微信\n",
            "email_notifier.py": "# 邮件通知\n",
        },
        "utils": {
            "__init__.py": "",
            "browser.py": "# 浏览器管理\n",
            "logger.py": "# 日志\n",
            "time_helper.py": "",
            "file_helper.py": "",
            "exception_handler.py": "",
        },
    },
    "config": {
        "accounts.yaml": "# 多账号配置\n",
        "youdian_urls.yaml": "# URL配置\n",
        "secrets": {
            ".env": "# 环境变量（记得加到.gitignore）\n",
        },
    },
    "data": {
        "raw": {},
        "processed": {},
        "reports": {},
    },
    "logs": {},
    "tests": {
        "test_captcha.py": "# 测试验证码\n",
    },
    "requirements.txt": "selenium\npytesseract\nrequests\npandas\npyyaml\nopenpyxl\n",
    ".gitignore": "logs/\ndata/\n__pycache__/\n.env\n*.pyc\n",
    "README.md": "# pro_charging - 充电桩数据抓取与分析项目\n",
}

def create_structure(base_path, tree):
    for name, content in tree.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    create_structure(BASE_DIR, structure)
    print(f"项目结构已生成在 ./{BASE_DIR}")