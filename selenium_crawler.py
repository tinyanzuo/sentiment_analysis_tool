"""
Selenium爬虫模块 - 爬取京东商品评论
"""
import json
import os
import random
import time
import pandas as pd
from config import COOKIE_FILE

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
    from webdriver_manager.chrome import ChromeDriverManager

    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"警告: 缺少Selenium库，请运行: pip install selenium webdriver-manager")


class JDSeleniumCrawler:
    """使用Selenium爬取京东评论 - 增强反爬版（移除点赞数）"""

    def __init__(self):
        self.driver = None
        self.selenium_available = SELENIUM_AVAILABLE
        self.comment_container = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def check_selenium(self):
        if not self.selenium_available:
            return False, "请安装selenium"
        try:
            options = Options()
            options.add_argument('--headless')
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.quit()
            return True, "Selenium就绪"
        except Exception as e:
            return False, f"初始化失败: {str(e)}"

    def save_cookies(self, cookies):
        try:
            with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f)
            return True
        except:
            return False

    def load_cookies(self):
        try:
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None

    def manual_login(self, driver, progress_callback):
        progress_callback("请在浏览器窗口中手动登录京东...")
        progress_callback("登录成功后程序会自动继续")

        driver.get("https://passport.jd.com/new/login.aspx")
        time.sleep(2)

        max_wait_time = 300
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            current_url = driver.current_url
            if "passport" not in current_url:
                progress_callback("检测到登录成功！")
                cookies = driver.get_cookies()
                self.save_cookies(cookies)
                return True

            try:
                driver.find_element(By.CSS_SELECTOR, ".nickname, .user-name")
                progress_callback("检测到登录成功！")
                cookies = driver.get_cookies()
                self.save_cookies(cookies)
                return True
            except:
                pass

            time.sleep(2)

        progress_callback("登录超时")
        return False

    def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延时，模拟人类操作"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay

    def init_driver(self, progress_callback=None):
        """初始化浏览器驱动，增强反爬配置"""
        options = Options()

        # 基础反检测配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # 窗口大小随机化（模拟不同分辨率）
        window_width = random.choice([1920, 1680, 1600, 1440, 1366])
        window_height = random.choice([1080, 1050, 900, 768])
        options.add_argument(f'--window-size={window_width},{window_height}')

        # 随机User-Agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')

        # 禁用自动化提示
        options.add_argument('--disable-infobars')

        # 其他配置
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 语言设置
        options.add_argument('--lang=zh-CN')

        try:
            if progress_callback:
                progress_callback(f"正在启动Chrome浏览器... (UA: {user_agent[:50]}...)")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # 执行JavaScript隐藏webdriver特征
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                window.chrome = { runtime: {} };
            """)

            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"启动失败: {str(e)}")
            return False

    def login_if_needed(self, progress_callback):
        self.driver.get("https://www.jd.com")
        self.random_delay(2, 3)

        cookies = self.load_cookies()
        if cookies:
            for cookie in cookies:
                try:
                    # 处理cookie的domain问题
                    if 'domain' in cookie and cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain'][1:]
                    self.driver.add_cookie(cookie)
                except:
                    pass

            self.driver.refresh()
            self.random_delay(3, 4)

            try:
                self.driver.find_element(By.CSS_SELECTOR, ".nickname, .user-name")
                progress_callback("登录恢复成功")
                return True
            except:
                progress_callback("Cookie已过期，需要重新登录")
                return self.manual_login(self.driver, progress_callback)
        else:
            return self.manual_login(self.driver, progress_callback)

    def human_like_scroll(self, container=None, target_count=100, progress_callback=None):
        """模拟人类滚动行为"""
        if container:
            scroll_script = """
                var container = arguments[0];
                return container.scrollHeight;
            """
            get_height_script = """
                var container = arguments[0];
                return container.scrollHeight;
            """
        else:
            scroll_script = """
                window.scrollTo(0, arguments[0]);
            """
            get_height_script = """
                return document.body.scrollHeight;
            """

        scroll_attempts = 0
        max_scroll_attempts = 40
        no_new_content = 0

        # 获取初始高度和评论数
        if container:
            current_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
        else:
            current_height = self.driver.execute_script("return document.body.scrollHeight;")

        before_count = len(self.extract_all_comments_on_page(progress_callback))
        progress_callback(f"初始评论数: {before_count}, 页面高度: {current_height}")

        while scroll_attempts < max_scroll_attempts and no_new_content < 5 and before_count < target_count:
            try:
                # 随机决定滚动方式
                scroll_style = random.choice(['fast', 'slow', 'step', 'wave', 'pause'])

                if scroll_style == 'fast':
                    if container:
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                    else:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    progress_callback(f"  ⏩ 快速滚动 ({scroll_attempts + 1}/{max_scroll_attempts})")
                    self.random_delay(1, 2)

                elif scroll_style == 'slow':
                    if container:
                        self.driver.execute_script("""
                            var container = arguments[0];
                            var target = container.scrollHeight;
                            var current = container.scrollTop;
                            var step = (target - current) / 10;
                            for(var i = 1; i <= 10; i++) {
                                setTimeout(function() {
                                    container.scrollTop = current + step * i;
                                }, i * 100);
                            }
                        """, container)
                    else:
                        self.driver.execute_script("""
                            var target = document.body.scrollHeight;
                            var current = window.pageYOffset;
                            var step = (target - current) / 10;
                            for(var i = 1; i <= 10; i++) {
                                setTimeout(function() {
                                    window.scrollTo(0, current + step * i);
                                }, i * 100);
                            }
                        """)
                    progress_callback(f"  🐢 慢速滚动 ({scroll_attempts + 1}/{max_scroll_attempts})")
                    time.sleep(2)

                elif scroll_style == 'step':
                    if container:
                        current = self.driver.execute_script("return arguments[0].scrollTop;", container)
                        total = self.driver.execute_script("return arguments[0].scrollHeight;", container)
                    else:
                        current = self.driver.execute_script("return window.pageYOffset;")
                        total = self.driver.execute_script("return document.body.scrollHeight;")

                    steps = random.randint(3, 6)
                    step_size = (total - current) / steps

                    for i in range(1, steps + 1):
                        scroll_to = current + step_size * i
                        if container:
                            self.driver.execute_script(f"arguments[0].scrollTop = {scroll_to};", container)
                        else:
                            self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                        self.random_delay(0.5, 1)

                    progress_callback(f"  👣 分步滚动({steps}步) ({scroll_attempts + 1}/{max_scroll_attempts})")

                elif scroll_style == 'wave':
                    if container:
                        current = self.driver.execute_script("return arguments[0].scrollTop;", container)
                        total = self.driver.execute_script("return arguments[0].scrollHeight;", container)
                    else:
                        current = self.driver.execute_script("return window.pageYOffset;")
                        total = self.driver.execute_script("return document.body.scrollHeight;")

                    # 先向上滚动一点
                    up_amount = random.randint(100, 300)
                    scroll_up = max(0, current - up_amount)
                    if container:
                        self.driver.execute_script(f"arguments[0].scrollTop = {scroll_up};", container)
                    else:
                        self.driver.execute_script(f"window.scrollTo(0, {scroll_up});")
                    self.random_delay(0.5, 1)

                    # 再向下滚动到更远
                    down_amount = random.randint(400, 800)
                    scroll_down = min(total, scroll_up + down_amount)
                    if container:
                        self.driver.execute_script(f"arguments[0].scrollTop = {scroll_down};", container)
                    else:
                        self.driver.execute_script(f"window.scrollTo(0, {scroll_down});")

                    progress_callback(f"  🌊 波浪滚动 ({scroll_attempts + 1}/{max_scroll_attempts})")
                    self.random_delay(1, 2)

                elif scroll_style == 'pause':
                    if container:
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                    else:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    pause_time = random.uniform(3, 5)
                    progress_callback(
                        f"  ⏸️ 滚动后暂停 {pause_time:.1f}秒 ({scroll_attempts + 1}/{max_scroll_attempts})")
                    time.sleep(pause_time)

                # 尝试点击"加载更多"按钮
                self.try_click_load_more(progress_callback)

                # 随机鼠标移动模拟
                if random.random() < 0.3:
                    self.driver.execute_script("""
                        var event = new MouseEvent('mousemove', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: Math.random() * window.innerWidth,
                            clientY: Math.random() * window.innerHeight
                        });
                        document.dispatchEvent(event);
                    """)

                # 获取新高度和评论数
                if container:
                    new_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
                else:
                    new_height = self.driver.execute_script("return document.body.scrollHeight;")

                current_count = len(self.extract_all_comments_on_page(progress_callback))

                if current_count > before_count:
                    progress_callback(f"    ✅ 新增评论: {before_count} → {current_count}")
                    before_count = current_count
                    no_new_content = 0
                else:
                    if new_height > current_height:
                        progress_callback(f"    ⚠️ 高度增加({current_height}→{new_height})但无新评论")
                        no_new_content += 0.5
                    else:
                        progress_callback(f"    ⚠️ 无新内容 ({no_new_content + 1}/5)")
                        no_new_content += 1

                current_height = new_height
                scroll_attempts += 1

            except Exception as e:
                progress_callback(f"    ❌ 滚动出错: {str(e)[:50]}")
                scroll_attempts += 1
                time.sleep(2)

        final_count = len(self.extract_all_comments_on_page(progress_callback))
        progress_callback(f"滚动加载完成，共 {final_count} 条评论")
        return final_count

    def try_click_load_more(self, progress_callback):
        """尝试点击加载更多按钮"""
        try:
            load_more_selectors = [
                "//*[contains(text(),'加载更多')]",
                "//*[contains(text(),'查看更多')]",
                "//*[contains(text(),'点击加载')]",
                "//*[contains(text(),'更多评论')]",
                ".load-more",
                ".more-comment",
                ".J-comment-more",
                ".comment-more",
                ".J-more",
                ".ui-pager-next",
                ".pn-next",
                ".next-page"
            ]

            for selector in load_more_selectors:
                if selector.startswith("//"):
                    btns = self.driver.find_elements(By.XPATH, selector)
                else:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        class_name = btn.get_attribute("class") or ""
                        if "disabled" not in class_name.lower():
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                            self.random_delay(0.5, 1)

                            if random.random() < 0.8:
                                self.driver.execute_script("arguments[0].click();", btn)
                                progress_callback(f"    ✅ 点击'加载更多'按钮")
                                self.random_delay(2, 3)
                                return True
        except:
            pass
        return False

    def click_all_comments_tab(self, progress_callback):
        """增强版：精确点击全部评价选项卡"""
        progress_callback("正在查找'全部评价'选项卡...")
        self.random_delay(1, 2)

        # 方案1：精确文本匹配
        if self.click_by_exact_text(progress_callback):
            return True

        # 方案2：通过data属性
        if self.click_by_data_attribute(progress_callback):
            return True

        # 方案3：通过位置判断
        if self.click_by_position(progress_callback):
            return True

        # 方案4：JavaScript直接选择
        if self.click_by_javascript(progress_callback):
            return True

        progress_callback("⚠ 未找到评价选项卡，尝试直接提取评论")
        return False

    def click_by_exact_text(self, progress_callback):
        """精确文本匹配"""
        exact_xpaths = [
            "//li[contains(text(),'全部评价')]",
            "//a[contains(text(),'全部评价')]",
            "//span[contains(text(),'全部评价')]",
            "//div[contains(text(),'全部评价')]"
        ]

        for xpath in exact_xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        text = element.text
                        if text == "全部评价" or text.strip() == "全部评价":
                            self.random_delay(0.5, 1.5)
                            self.driver.execute_script("arguments[0].click();", element)
                            progress_callback(f"✓ 点击'全部评价'")
                            self.random_delay(2, 3)

                            success, count = self.verify_comment_area()
                            if success:
                                progress_callback(f"✓ 验证成功，找到评论区域")
                                return True
            except:
                continue
        return False

    def click_by_data_attribute(self, progress_callback):
        """通过data属性点击"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR,
                                               "[data-tab='comment'], [clstag*='pingjia-all'], [data-anchor='#comment']")
            if element and element.is_displayed():
                self.random_delay(0.5, 1.5)
                self.driver.execute_script("arguments[0].click();", element)
                progress_callback("✓ 通过data属性点击")
                self.random_delay(2, 3)

                success, count = self.verify_comment_area()
                if success:
                    return True
        except:
            pass
        return False

    def click_by_position(self, progress_callback):
        """通过位置判断"""
        try:
            tabs = self.driver.find_elements(By.CSS_SELECTOR,
                                             ".tab-item, .J-tab, .tab, [class*='tab']")

            for tab in tabs:
                if tab.is_displayed():
                    text = tab.text
                    location = tab.location
                    progress_callback(f"发现选项卡: '{text}' 在位置 x={location['x']}")

                    if "全部评价" in text:
                        self.random_delay(0.5, 1.5)
                        self.driver.execute_script("arguments[0].click();", tab)
                        progress_callback(f"✓ 点击: {text}")
                        self.random_delay(2, 3)
                        return True
                    elif "评价" in text and "问大家" not in text:
                        self.random_delay(0.5, 1.5)
                        self.driver.execute_script("arguments[0].click();", tab)
                        progress_callback(f"✓ 点击: {text}")
                        self.random_delay(2, 3)
                        return True
        except Exception as e:
            progress_callback(f"位置点击失败: {str(e)}")

        return False

    def click_by_javascript(self, progress_callback):
        """使用JavaScript直接选择正确选项卡"""
        try:
            result = self.driver.execute_script("""
                var tabs = document.querySelectorAll('.tab-item, .J-tab, [class*="tab"]');
                for(var i=0; i<tabs.length; i++) {
                    var text = tabs[i].textContent || '';
                    if(text.includes('全部评价') && !text.includes('问大家')) {
                        tabs[i].click();
                        return '通过文本点击: ' + text;
                    }
                }

                var commentTab = document.querySelector('[data-tab="comment"], [clstag*="pingjia"]');
                if(commentTab) {
                    commentTab.click();
                    return '通过data属性点击';
                }

                for(var i=0; i<tabs.length; i++) {
                    var text = tabs[i].textContent || '';
                    if(text.includes('评价') && !text.includes('问大家')) {
                        tabs[i].click();
                        return '通过模糊匹配点击: ' + text;
                    }
                }

                return false;
            """)

            if result:
                progress_callback(f"✓ {result}")
                self.random_delay(2, 3)

                time.sleep(2)
                comments = self.driver.find_elements(By.CSS_SELECTOR,
                                                     ".comment-item, .comment-con")
                if comments:
                    progress_callback(f"✓ 评论区域已加载，找到 {len(comments)} 条评论")
                    return True
        except Exception as e:
            progress_callback(f"JavaScript点击失败: {str(e)}")

        return False

    def verify_comment_area(self):
        """验证是否成功进入评论区域"""
        try:
            comment_selectors = [
                ".comment-item",
                ".comment-con",
                ".comment-content",
                "[class*='comment-item']",
                ".rate-comment-list"
            ]

            for selector in comment_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    return True, len(elements)

            qa_selectors = [
                ".ask-list",
                ".question-list",
                "[class*='question']",
                "[class*='ask']"
            ]

            for selector in qa_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    return False, -1

            return False, 0
        except:
            return False, 0

    def find_comment_container(self, progress_callback):
        """找到真正的评论容器"""
        container_selectors = [
            "#comment-0",
            ".comment-list",
            ".J-comment-list",
            ".tab-con",
            ".comment-items",
            ".comment-box",
            ".rate-comment-list",
            "//div[contains(@class, 'comment') and contains(@class, 'list')]",
            "//div[@id='comment-0']",
            "//div[contains(@class, 'tab-con')]",
            ".comments-list",
            ".comment-container",
            ".detail-comment",
            ".comment-wrap",
            ".comment-detail",
            ".product-comm-main"
        ]

        for selector in container_selectors:
            try:
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for element in elements:
                    if element.is_displayed():
                        comment_items = element.find_elements(By.CSS_SELECTOR,
                                                              ".comment-item, .j-comment-item, [class*='comment-item'], .review-item, .evaluation-item")
                        if comment_items and len(comment_items) > 0:
                            self.comment_container = element
                            progress_callback(f"✓ 找到评论容器: {selector}，包含 {len(comment_items)} 条评论")

                            try:
                                height = self.driver.execute_script("return arguments[0].scrollHeight", element)
                                progress_callback(f"  容器高度: {height}px")
                            except:
                                pass

                            return True
            except:
                continue

        progress_callback("⚠ 未找到标准评论容器，尝试查找任何评论元素...")

        comment_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                     ".comment-con, .comment-content, .review-content, [class*='comment']")

        if comment_elements and len(comment_elements) > 0:
            try:
                parent = comment_elements[0].find_element(By.XPATH,
                                                          "./ancestor::div[contains(@class, 'list') or contains(@class, 'container') or contains(@class, 'wrap')]")
                self.comment_container = parent
                progress_callback(f"✓ 通过评论元素找到容器")
                return True
            except:
                pass

        progress_callback("⚠ 未找到评论容器，将滚动整个页面")
        self.comment_container = self.driver.find_element(By.TAG_NAME, "body")
        return False

    def extract_all_comments_on_page(self, progress_callback=None):
        """提取页面上的所有评论"""
        comments = []

        comment_selectors = [
            ".comment-item",
            ".j-comment-item",
            "[class*='comment-item']",
            ".comment-list .comment-item",
            "#comment-0 .comment-item",
            ".tab-con .comment-item",
            ".J-comment-item",
            ".comment-con",
            ".review-item",
            ".evaluation-item",
            ".jdc-pc-rate-card",
            ".jd-content-pc-skeleton-item",
            ".comment-content",
            ".comment-text",
            ".review-content",
            ".rate-content",
            ".comment-detail",
            ".J-comment-item"
        ]

        found_any = False
        for selector in comment_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    found_any = True
                    for element in elements:
                        try:
                            content = element.text.strip()

                            if content and len(content) > 3:
                                if any(keyword in content for keyword in
                                       ['京东', '商品', '快递', '物流', '客服', '质量', '好评', '差评', '不错',
                                        '满意']):
                                    if content not in comments:
                                        comments.append(content)
                                else:
                                    if len(content) > 5 and content not in comments:
                                        comments.append(content)
                        except:
                            continue

                    if len(comments) > 0 and progress_callback:
                        progress_callback(f"通过 {selector} 找到 {len(comments)} 条评论")
                        break
            except:
                continue

        if not comments and progress_callback:
            progress_callback("尝试通用文本提取...")
            try:
                all_text_elements = self.driver.find_elements(By.XPATH,
                                                              "//*[string-length(text())>10 and not(self::script) and not(self::style) and not(self::meta)]")

                for element in all_text_elements:
                    try:
                        text = element.text.strip()
                        if text and len(text) > 10:
                            if any(keyword in text for keyword in ['京东', '商品', '快递', '物流', '客服', '质量']):
                                if text not in comments:
                                    comments.append(text)
                    except:
                        continue
            except:
                pass

        comments = list(dict.fromkeys(comments))
        comments = [c for c in comments if len(c) > 5]

        return comments

    def scroll_comment_container(self, progress_callback, target_count):
        """在评论区域中滚动加载"""
        progress_callback("开始在评论区域中滚动加载...")

        if not self.find_comment_container(progress_callback):
            progress_callback("⚠ 使用整个页面滚动")

        self.random_delay(2, 3)

        final_count = self.human_like_scroll(
            container=self.comment_container,
            target_count=target_count,
            progress_callback=progress_callback
        )

        if final_count < target_count:
            progress_callback(f"⚠ 只能获取到 {final_count} 条评论，可能已达上限")

        return final_count

    def extract_comments_with_details(self, progress_callback):
        """提取评论详情（移除点赞数）"""
        comments = []

        container_selectors = [
            ".comment-item",
            ".j-comment-item",
            "[class*='comment-item']",
            ".comment-list .comment-item",
            "#comment-0 .comment-item",
            ".tab-con .comment-item",
            ".J-comment-item",
            ".comment-con",
            ".review-item",
            ".evaluation-item",
            ".jdc-pc-rate-card",
            ".jd-content-pc-skeleton-item"
        ]

        content_selectors = [
            ".comment-con",
            ".comment-content",
            ".comment-text",
            ".comment-detail",
            "[class*='comment-con']",
            ".review-content",
            ".evaluate-content",
            ".jdc-pc-rate-card-main-desc",
            ".info.text-ellipsis-2"
        ]

        star_selectors = [
            ".star .star-on",
            ".star-on",
            ".score i.on",
            ".rate i.on"
        ]

        time_selectors = [
            ".comment-time",
            ".time",
            ".date",
            ".comment-date",
            ".jdc-pc-rate-card-info-left .date"
        ]

        containers = []
        for selector in container_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    containers = elements
                    break
            except:
                continue

        if not containers:
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            content = element.text.strip()
                            if content and len(content) > 3:
                                comments.append({
                                    '评论内容': content,
                                    '评分': 5,
                                    '评论时间': ''
                                })
                        except:
                            continue
                except:
                    continue
        else:
            for container in containers:
                try:
                    content = ""
                    for selector in content_selectors:
                        try:
                            elements = container.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                content = elements[0].text.strip()
                                break
                        except:
                            continue

                    if not content:
                        content = container.text.strip()

                    if not content or len(content) < 3:
                        continue

                    score = 5
                    for selector in star_selectors:
                        try:
                            stars = container.find_elements(By.CSS_SELECTOR, selector)
                            if stars:
                                score = len(stars)
                                break
                        except:
                            continue

                    comment_time = ""
                    for selector in time_selectors:
                        try:
                            elements = container.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                comment_time = elements[0].text.strip()
                                break
                        except:
                            continue

                    comments.append({
                        '评论内容': content,
                        '评分': score,
                        '评论时间': comment_time
                    })

                except StaleElementReferenceException:
                    continue
                except:
                    continue

        return comments

    def go_to_next_page(self, progress_callback):
        """翻页"""
        try:
            next_selectors = [
                ".ui-pager-next",
                ".pn-next",
                ".next-page",
                ".pager-next",
                ".next",
                "//a[contains(text(),'下一页')]",
                ".page-next",
                ".J-pager-next"
            ]

            for selector in next_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for btn in elements:
                        if btn.is_displayed() and btn.is_enabled():
                            class_name = btn.get_attribute("class") or ""
                            if "disabled" not in class_name.lower():
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                                self.random_delay(1, 2)

                                self.driver.execute_script("arguments[0].click();", btn)
                                progress_callback("  ✓ 点击下一页")
                                self.random_delay(3, 4)
                                return True
                except:
                    continue

            result = self.driver.execute_script("""
                var btns = document.querySelectorAll('.ui-pager-next, .pn-next, .next-page, .pager-next, .next, .page-next');
                for(var i=0; i<btns.length; i++) {
                    if(btns[i].offsetParent !== null && !btns[i].className.includes('disabled')) {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if result:
                progress_callback("  ✓ JavaScript点击下一页")
                self.random_delay(3, 4)
                return True

            return False

        except Exception as e:
            progress_callback(f"  翻页失败: {str(e)}")
            return False

    def crawl(self, product_id, target_count=100, progress_callback=None):
        """爬取评论主方法"""
        if not self.selenium_available:
            progress_callback("错误: 请安装selenium")
            return None

        all_comments = []
        current_page = 1
        max_pages = 100

        try:
            if not self.init_driver(progress_callback):
                return None

            if not self.login_if_needed(progress_callback):
                progress_callback("登录失败")
                return None

            url = f'https://item.jd.com/{product_id}.html'
            progress_callback(f"打开商品页面: {product_id}")
            self.driver.get(url)
            self.random_delay(3, 5)

            for i in range(random.randint(2, 4)):
                scroll_amount = random.randint(200, 800)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
                self.random_delay(0.5, 1.5)

            if not self.click_all_comments_tab(progress_callback):
                progress_callback("无法点击评价选项卡，尝试直接提取")

            progress_callback("等待评论区域加载...")
            self.random_delay(3, 5)

            self.scroll_comment_container(progress_callback, target_count)

            progress_callback(f"目标: 爬取 {target_count} 条评论")

            consecutive_empty_pages = 0

            while len(all_comments) < target_count and current_page <= max_pages and consecutive_empty_pages < 3:
                progress_callback(f"正在处理第 {current_page} 页...")

                page_comments = self.extract_comments_with_details(progress_callback)

                if page_comments:
                    existing_contents = {c['评论内容'] for c in all_comments}
                    new_comments = [c for c in page_comments if c['评论内容'] not in existing_contents]

                    if new_comments:
                        all_comments.extend(new_comments)
                        consecutive_empty_pages = 0
                        progress_callback(f"  ✓ 新增 {len(new_comments)} 条 (累计 {len(all_comments)}/{target_count})")
                    else:
                        consecutive_empty_pages += 1
                        progress_callback(f"  ⚠ 本页无新评论 ({consecutive_empty_pages}/3)")
                else:
                    consecutive_empty_pages += 1
                    progress_callback(f"  ✗ 本页无评论 ({consecutive_empty_pages}/3)")

                if len(all_comments) >= target_count:
                    progress_callback(f"✓ 已达到目标数量 {target_count}")
                    break

                if consecutive_empty_pages >= 3:
                    progress_callback("连续3页无新评论，停止爬取")
                    break

                if current_page < max_pages:
                    if not self.go_to_next_page(progress_callback):
                        progress_callback("无法继续翻页，爬取结束")
                        break

                    current_page += 1

                    self.random_delay(2, 4)
                    progress_callback(f"翻到第 {current_page} 页，继续滚动加载...")
                    self.scroll_comment_container(progress_callback, target_count)

                    self.random_delay(2, 4)
                else:
                    break

            if all_comments:
                if len(all_comments) > target_count:
                    all_comments = all_comments[:target_count]

                df = pd.DataFrame(all_comments)
                progress_callback(f"✓ 完成！共 {len(df)} 条评论")
                return df
            else:
                progress_callback("✗ 未获取到评论")
                return None

        except Exception as e:
            progress_callback(f"爬取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            if self.driver:
                self.driver.quit()