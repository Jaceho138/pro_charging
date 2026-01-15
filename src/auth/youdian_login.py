# src/auth/youdian_login.py
# 优化版：使用超级鹰 API 识别验证码（取代 Tesseract）
# 包含详细调试打印 + 阻止无限刷新 + 多账号支持

import os
import re
import time
import traceback
import base64
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import platform

load_dotenv()

# ── 超级鹰配置（从 .env 读取） ────────────────────────────────
SUPER_EAGLE_USER = os.getenv('YOUDIAN_SUPER_EAGLE_USER')
SUPER_EAGLE_PASS = os.getenv('YOUDIAN_SUPER_EAGLE_PASS')
SUPER_EAGLE_SOFTID = os.getenv('YOUDIAN_SUPER_EAGLE_SOFTID')
SUPER_EAGLE_CODETYPE = os.getenv('YOUDIAN_SUPER_EAGLE_CODETYPE', '1902')  # 默认算术题 1902

if not all([SUPER_EAGLE_USER, SUPER_EAGLE_PASS, SUPER_EAGLE_SOFTID]):
    raise ValueError("【错误】.env 中缺少超级鹰配置（YOUDIAN_SUPER_EAGLE_USER/PASS/SOFTID）")

print("【超级鹰配置】用户名:", SUPER_EAGLE_USER)
print("【超级鹰配置】软件ID:", SUPER_EAGLE_SOFTID)
print("【验证码类型】:", SUPER_EAGLE_CODETYPE)

# 友电配置
LOGIN_URL = os.getenv('YOUDIAN_LOGIN_URL', 'https://udianwulian.com/admin/#/login')
usernames_str = os.getenv('YOUDIAN_USERNAMES', '')
passwords_str = os.getenv('YOUDIAN_PASSWORDS', '')
usernames = [u.strip() for u in usernames_str.split(',') if u.strip()]
passwords = [p.strip() for p in passwords_str.split(',') if p.strip()]

def recognize_with_supereagle(base64_data):
    """调用超级鹰 API 识别 base64 验证码图片"""
    url = "https://upload.chaojiying.net/Upload/Processing.php"  # HTTPS + .net
    payload = {
        "user": SUPER_EAGLE_USER,
        "pass": SUPER_EAGLE_PASS,
        "softid": SUPER_EAGLE_SOFTID,
        "codetype": SUPER_EAGLE_CODETYPE,
        "file_base64": base64_data,
        "min_len": "1",  # 最小长度
        "max_len": "10"  # 最大长度（算术题通常短）
    }
    try:
        response = requests.post(url, data=payload, timeout=60)
        result = response.json()
        if result.get('err_no') == 0:
            code = result['pic_str'].strip()
            print(f"【超级鹰识别成功】: {code}")
            # 清理结果：提取算术表达式（如去掉多余文字）
            match = re.search(r'[\d\+\-\×÷= ]+', code)
            if match:
                return match.group(0).strip()
            return code
        else:
            print(f"【超级鹰失败】 err_no: {result.get('err_no')}, err_str: {result.get('err_str')}")
            return None
    except Exception as e:
        print(f"【API 异常】: {e}")
        return None

def safe_eval(expression):
    """安全计算表达式"""
    expression = expression.replace('×', '*').replace('÷', '/').replace(' ', '').strip()
    expression = re.sub(r'=$', '', expression)
    try:
        result = eval(expression, {"__builtins__": {}})
        print(f"【计算成功】'{expression}' → {result}")
        return result
    except Exception as e:
        print(f"【计算失败】'{expression}' → 错误: {e}")
        return None

def get_login_driver(headless=False):
    print("【初始化】Chrome 浏览器...")
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=options)

def login_to_youdian_single(username, password, max_retries=5):
    print(f"\n【开始登录】账号: {username}")
    driver = get_login_driver(headless=False)
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)

    for attempt in range(max_retries):
        print(f"\n【第 {attempt+1}/{max_retries} 次尝试】")
        try:
            print("【等待】账号输入框...")
            username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="账号"]')))
            username_input.clear()
            username_input.send_keys(username)
            print("【成功】账号已填入")

            password_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="密码"]')
            password_input.clear()
            password_input.send_keys(password)
            print("【成功】密码已填入")

            print("【等待】验证码图片...")
            captcha_img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.login-code-img')))
            src = captcha_img.get_attribute('src')
            print("【验证码 src (前100)】:", src[:100])

            if not src.startswith("data:image"):
                print("【警告】验证码 src 异常")
                print("【刷新阻止】")
                time.sleep(3)
                continue

            base64_data = src.split(",")[1]
            # 可选：保存图片调试
            # with open(f"captcha_{attempt}.png", "wb") as f:
            #     f.write(base64.b64decode(base64_data))

            captcha_text = recognize_with_supereagle(base64_data)
            if not captcha_text:
                print("【失败】超级鹰识别为空")
                print("【刷新阻止】")
                time.sleep(3)
                continue

            result = safe_eval(captcha_text)
            if result is None:
                print("【失败】计算结果为空")
                print("【刷新阻止】")
                time.sleep(3)
                continue

            captcha_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="验证码"]')
            captcha_input.clear()
            captcha_input.send_keys(str(int(result)))
            print(f"【成功】验证码填入: {int(result)}")

            print("【等待】登录按钮...")
            login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.el-button--primary')))
            login_btn.click()
            print("【成功】已点击登录")

            print("【等待】登录成功...")
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, '.login-form')))
            print(f"【登录成功】账号: {username}  URL: {driver.current_url}")
            return driver

        except Exception as e:
            print(f"【异常】第 {attempt+1} 次失败:")
            print(traceback.format_exc())
            print("【刷新阻止】")
            time.sleep(5)

    print("【失败】达到最大重试次数")
    driver.quit()
    return None

if __name__ == "__main__":
    if not usernames:
        print("【错误】.env 中未配置 YOUDIAN_USERNAMES")
    else:
        for i, username in enumerate(usernames):
            pw = passwords[i] if i < len(passwords) else None
            if pw:
                driver = login_to_youdian_single(username, pw)
                if driver:
                    time.sleep(15)  # 保持观察登录后页面
                    driver.quit()