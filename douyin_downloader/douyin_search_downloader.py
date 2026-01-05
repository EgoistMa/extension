#!/usr/bin/env python3
"""
抖音搜索视频下载器
从搜索页面筛选并下载符合条件的视频
"""

import os
import re
import json
import time
import random
import argparse
import platform
from pathlib import Path
from urllib.parse import unquote, quote
from dataclasses import dataclass
from typing import List, Optional

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("请先安装 DrissionPage: pip install DrissionPage")
    exit(1)

import requests


@dataclass
class VideoInfo:
    """视频信息"""
    aweme_id: str
    title: str
    author: str
    duration: float  # 秒
    digg_count: int  # 点赞数
    play_count: int  # 播放数
    video_url: str = ""
    cover_url: str = ""
    create_time: int = 0  # 发布时间戳


class DouyinSearchDownloader:
    """抖音搜索下载器"""

    def __init__(self, headless: bool = False, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.page = None

    def _find_chrome_path(self) -> str:
        """查找 Chrome 浏览器路径"""
        possible_paths = []

        if platform.system() == 'Windows':
            possible_paths = [
                os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
            ]
        elif platform.system() == 'Darwin':
            possible_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ]
        else:
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium-browser',
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _get_chrome_user_data_dir(self) -> str:
        """获取 Chrome 用户数据目录"""
        if platform.system() == 'Windows':
            # Windows 默认 Chrome 用户数据目录
            local_app_data = os.environ.get('LOCALAPPDATA', '')
            possible_paths = [
                os.path.join(local_app_data, 'Google', 'Chrome', 'User Data'),
                os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),
            ]
            # 也检查 Edge
            edge_paths = [
                os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data'),
            ]
            possible_paths.extend(edge_paths)
        elif platform.system() == 'Darwin':
            # macOS
            home = os.path.expanduser('~')
            possible_paths = [
                os.path.join(home, 'Library', 'Application Support', 'Google', 'Chrome'),
            ]
        else:
            # Linux
            home = os.path.expanduser('~')
            possible_paths = [
                os.path.join(home, '.config', 'google-chrome'),
                os.path.join(home, '.config', 'chromium'),
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _init_browser(self):
        """初始化浏览器 - 使用现有浏览器的用户数据"""
        if self.page:
            return

        co = ChromiumOptions()

        # ============ 使用现有浏览器的用户数据 ============
        # 这样可以继承已有的 cookies、登录状态、浏览器指纹等
        user_data_dir = self._get_chrome_user_data_dir()
        if user_data_dir and os.path.exists(user_data_dir):
            print(f"[浏览器] 使用现有用户数据: {user_data_dir}")
            # 复制用户数据到临时目录，避免与正在运行的 Chrome 冲突
            import shutil
            import tempfile
            temp_user_data = os.path.join(tempfile.gettempdir(), 'douyin_chrome_profile')

            # 只复制必要的文件（cookies, 登录状态等）
            default_profile = os.path.join(user_data_dir, 'Default')
            temp_default = os.path.join(temp_user_data, 'Default')

            try:
                # 确保目录存在
                os.makedirs(temp_default, exist_ok=True)

                # 复制关键文件
                files_to_copy = ['Cookies', 'Login Data', 'Web Data', 'Preferences', 'Secure Preferences']
                for filename in files_to_copy:
                    src = os.path.join(default_profile, filename)
                    dst = os.path.join(temp_default, filename)
                    if os.path.exists(src):
                        try:
                            shutil.copy2(src, dst)
                        except Exception as e:
                            if self.debug:
                                print(f"[DEBUG] 复制 {filename} 失败: {e}")

                # 复制 Local State 文件
                local_state_src = os.path.join(user_data_dir, 'Local State')
                local_state_dst = os.path.join(temp_user_data, 'Local State')
                if os.path.exists(local_state_src):
                    try:
                        shutil.copy2(local_state_src, local_state_dst)
                    except Exception:
                        pass

                print(f"[浏览器] 已复制用户配置到: {temp_user_data}")
                co.set_user_data_path(temp_user_data)
                co.set_argument('--profile-directory=Default')

            except Exception as e:
                print(f"[浏览器] 复制用户数据失败: {e}，使用新配置")
                co.auto_port()
        else:
            print("[浏览器] 未找到现有用户数据，使用新配置")
            co.auto_port()

        # 设置独立端口，避免冲突
        co.auto_port()

        chrome_path = self._find_chrome_path()
        if chrome_path:
            if self.debug:
                print(f"[DEBUG] 找到浏览器: {chrome_path}")
            co.set_browser_path(chrome_path)

        if self.headless:
            co.set_argument('--headless=new')

        # ============ 基础参数（保留关键的反检测） ============
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--window-size=1920,1080')
        co.set_argument('--start-maximized')

        # 禁用自动化标志
        co.set_argument('--disable-automation')

        # 不禁用扩展（保留用户已安装的扩展）
        # co.set_argument('--disable-extensions')

        print("[浏览器] 正在启动...")
        self.page = ChromiumPage(co)
        print("[浏览器] 启动成功")

        # 注入反检测脚本
        self._inject_stealth_scripts()

        if self.debug:
            print(f"[DEBUG] 浏览器已初始化, headless={self.headless}")

    def _inject_stealth_scripts(self):
        """注入反检测脚本"""
        try:
            self.page.run_js('''
                // ============ 1. 隐藏 webdriver 标志 ============
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });

                // 删除 webdriver 相关属性
                delete navigator.__proto__.webdriver;

                // ============ 2. 模拟真实的 navigator 属性 ============
                // 插件列表 (模拟真实 Chrome)
                const mockPlugins = {
                    length: 5,
                    item: function(index) { return this[index] || null; },
                    namedItem: function(name) {
                        for (let i = 0; i < this.length; i++) {
                            if (this[i].name === name) return this[i];
                        }
                        return null;
                    },
                    refresh: function() {},
                    0: {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
                    1: {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1},
                    2: {name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 2},
                    3: {name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
                    4: {name: 'Microsoft Edge PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => mockPlugins,
                    configurable: true
                });

                // MimeTypes
                const mockMimeTypes = {
                    length: 4,
                    item: function(index) { return this[index] || null; },
                    namedItem: function(name) {
                        for (let i = 0; i < this.length; i++) {
                            if (this[i].type === name) return this[i];
                        }
                        return null;
                    },
                    0: {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    1: {type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    2: {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    3: {type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable'}
                };
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => mockMimeTypes,
                    configurable: true
                });

                // 语言设置
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                    configurable: true
                });
                Object.defineProperty(navigator, 'language', {
                    get: () => 'zh-CN',
                    configurable: true
                });

                // 平台信息
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                    configurable: true
                });

                // 硬件信息
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                    configurable: true
                });
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                    configurable: true
                });
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: () => 0,
                    configurable: true
                });

                // 连接信息
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    }),
                    configurable: true
                });

                // ============ 3. 模拟 Chrome 对象 ============
                window.chrome = {
                    app: {
                        isInstalled: false,
                        InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'},
                        RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}
                    },
                    runtime: {
                        OnInstalledReason: {CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update'},
                        OnRestartRequiredReason: {APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic'},
                        PlatformArch: {ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64'},
                        PlatformNaclArch: {ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64'},
                        PlatformOs: {ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win'},
                        RequestUpdateCheckStatus: {NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available'},
                        connect: function() { return {onMessage: {addListener: function(){}}, postMessage: function(){}, disconnect: function(){}} },
                        sendMessage: function() {}
                    },
                    csi: function() { return {}; },
                    loadTimes: function() {
                        return {
                            commitLoadTime: Date.now() / 1000 - Math.random() * 2,
                            connectionInfo: 'h2',
                            finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                            finishLoadTime: Date.now() / 1000 - Math.random() * 0.5,
                            firstPaintAfterLoadTime: 0,
                            firstPaintTime: Date.now() / 1000 - Math.random() * 1.5,
                            navigationType: 'Other',
                            npnNegotiatedProtocol: 'unknown',
                            requestTime: Date.now() / 1000 - Math.random() * 3,
                            startLoadTime: Date.now() / 1000 - Math.random() * 2.5,
                            wasAlternateProtocolAvailable: false,
                            wasFetchedViaSpdy: true,
                            wasNpnNegotiated: true
                        };
                    }
                };

                // ============ 4. 屏幕信息 ============
                Object.defineProperty(screen, 'width', {get: () => 1920, configurable: true});
                Object.defineProperty(screen, 'height', {get: () => 1080, configurable: true});
                Object.defineProperty(screen, 'availWidth', {get: () => 1920, configurable: true});
                Object.defineProperty(screen, 'availHeight', {get: () => 1040, configurable: true});
                Object.defineProperty(screen, 'colorDepth', {get: () => 24, configurable: true});
                Object.defineProperty(screen, 'pixelDepth', {get: () => 24, configurable: true});

                // ============ 5. 权限 API ============
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => {
                    if (parameters.name === 'notifications') {
                        return Promise.resolve({state: Notification.permission, onchange: null});
                    }
                    return originalQuery.call(navigator.permissions, parameters);
                };

                // ============ 6. WebGL 信息 ============
                const getParameterProxyHandler = {
                    apply: function(target, thisArg, args) {
                        const param = args[0];
                        const gl = thisArg;

                        // UNMASKED_VENDOR_WEBGL
                        if (param === 37445) {
                            return 'Google Inc. (NVIDIA)';
                        }
                        // UNMASKED_RENDERER_WEBGL
                        if (param === 37446) {
                            return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        }

                        return Reflect.apply(target, thisArg, args);
                    }
                };

                // 代理 WebGL getParameter
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {
                    gl.getParameter = new Proxy(gl.getParameter, getParameterProxyHandler);
                }
                const gl2 = canvas.getContext('webgl2');
                if (gl2) {
                    gl2.getParameter = new Proxy(gl2.getParameter, getParameterProxyHandler);
                }

                // ============ 7. 删除自动化痕迹 ============
                // 删除 ChromeDriver 注入的变量
                const cdcProps = Object.getOwnPropertyNames(window).filter(p => p.match(/^cdc_/));
                cdcProps.forEach(prop => { delete window[prop]; });

                // 删除 Selenium 痕迹
                delete window.__selenium_unwrapped;
                delete window.__webdriver_evaluate;
                delete window.__webdriver_script_function;
                delete window.__webdriver_script_func;
                delete window.__webdriver_script_fn;
                delete window.__fxdriver_evaluate;
                delete window.__driver_evaluate;
                delete window.__webdriver_unwrapped;
                delete window.__fxdriver_unwrapped;
                delete window.__driver_unwrapped;
                delete window._Selenium_IDE_Recorder;
                delete window._selenium;
                delete window.calledSelenium;
                delete document.__webdriver_script_fn;
                delete document.$chrome_asyncScriptInfo;
                delete document.$cdc_asdjflasutopfhvcZLmcfl_;

                // ============ 8. 修复 iframe contentWindow ============
                const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        const iframe = originalContentWindow.get.call(this);
                        if (iframe) {
                            try {
                                Object.defineProperty(iframe.navigator, 'webdriver', {get: () => undefined});
                            } catch(e) {}
                        }
                        return iframe;
                    }
                });

                // ============ 9. 修复 toString 检测 ============
                const oldCall = Function.prototype.call;
                function hook(func, returnVal) {
                    const old = func;
                    func = function() {
                        if (returnVal !== undefined) return returnVal;
                        return old.apply(this, arguments);
                    };
                    func.toString = function() {
                        return old.toString();
                    };
                    return func;
                }

                // 确保 navigator.webdriver.toString() 不会暴露
                try {
                    navigator.__proto__.hasOwnProperty = hook(navigator.__proto__.hasOwnProperty);
                } catch(e) {}

                // ============ 10. 时区设置 ============
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                    value: function() {
                        return {
                            locale: 'zh-CN',
                            calendar: 'gregory',
                            numberingSystem: 'latn',
                            timeZone: 'Asia/Shanghai',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit'
                        };
                    }
                });

                console.log('[Stealth] Anti-detection scripts injected successfully');
            ''')
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 注入反检测脚本失败: {e}")

    def _check_and_wait_captcha(self, max_wait: int = 120) -> bool:
        """
        检测验证码并等待用户完成验证

        Args:
            max_wait: 最大等待时间（秒）

        Returns:
            True 如果验证码已完成或无验证码，False 如果超时
        """
        captcha_selectors = [
            'div[class*="captcha"]',
            'div[class*="verify"]',
            'div[class*="slider"]',
            'iframe[src*="captcha"]',
            '#captcha',
            '.captcha-container',
            'div[class*="secsdk"]',
            'div[class*="verify-bar"]'
        ]

        start_time = time.time()
        captcha_detected = False

        while time.time() - start_time < max_wait:
            # 检查是否有验证码元素
            has_captcha = False
            for selector in captcha_selectors:
                try:
                    ele = self.page.ele(selector, timeout=0.5)
                    if ele:
                        has_captcha = True
                        break
                except:
                    pass

            # 也检查页面内容是否包含验证码关键词
            try:
                page_text = self.page.html.lower() if self.page.html else ''
                if any(kw in page_text for kw in ['验证码', '滑动验证', '请完成验证', 'captcha', 'verify']):
                    # 但要排除已经在搜索结果页的情况
                    if 'search' not in self.page.url or len(page_text) < 5000:
                        has_captcha = True
            except:
                pass

            if has_captcha:
                if not captcha_detected:
                    captcha_detected = True
                    print("\n" + "=" * 50)
                    print("⚠️  检测到验证码，请在浏览器中完成验证...")
                    print("=" * 50 + "\n")

                time.sleep(2)  # 等待用户完成验证
            else:
                if captcha_detected:
                    print("✅ 验证码已完成，继续执行...")
                    time.sleep(1)  # 给页面一点时间加载
                return True

        if captcha_detected:
            print("❌ 验证码等待超时")
            return False

        return True

    def _wait_for_page_load(self, max_wait: int = 60) -> bool:
        """
        等待页面加载完成，直到检测到视频内容

        Args:
            max_wait: 最大等待时间（秒）

        Returns:
            True 如果页面加载成功并找到视频内容
        """
        print("[等待] 页面加载中...")
        start_time = time.time()
        check_interval = 2  # 每2秒检查一次

        while time.time() - start_time < max_wait:
            # 先检查验证码
            if not self._check_and_wait_captcha(max_wait=5):
                time.sleep(check_interval)
                continue

            # 检查页面是否有视频卡片
            try:
                # 方法1: 使用 JavaScript 检查视频链接 (最可靠)
                # 链接格式: href="//www.douyin.com/video/xxx" 或 href="/video/xxx"
                video_count = self.page.run_js('''
                    return document.querySelectorAll('a[href*="douyin.com/video/"], a[href*="/video/"]').length;
                ''')
                if video_count and video_count > 0:
                    print(f"[成功] 页面加载完成，检测到 {video_count} 个视频链接")
                    return True

                # 方法2: 检查 search-result-card (抖音搜索结果页面的实际结构)
                card_count = self.page.run_js('''
                    return document.querySelectorAll('.search-result-card, [class*="search-result"]').length;
                ''')
                if card_count and card_count > 0:
                    print(f"[成功] 页面加载完成，检测到 {card_count} 个搜索结果卡片")
                    return True

                # 方法3: 检查 RENDER_DATA
                render_script = self.page.ele('#RENDER_DATA', timeout=1)
                if render_script and render_script.text and len(render_script.text) > 1000:
                    print(f"[成功] 页面加载完成，检测到渲染数据")
                    return True

            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] 检查页面内容时出错: {e}")

            # 检查是否是空结果页面
            try:
                page_text = self.page.html if self.page.html else ''
                if '没有找到' in page_text or '暂无结果' in page_text or 'no result' in page_text.lower():
                    print("[提示] 搜索无结果")
                    return True  # 返回 True 让程序继续，后续会发现没有视频
            except:
                pass

            elapsed = int(time.time() - start_time)
            print(f"[等待] 已等待 {elapsed}秒，继续等待页面加载...")
            time.sleep(check_interval)

        print(f"[超时] 等待页面加载超过 {max_wait} 秒")
        return False

    def search_videos(self, search_url: str, scroll_times: int = 3) -> List[VideoInfo]:
        """
        从搜索页面获取视频列表

        Args:
            search_url: 搜索页面 URL
            scroll_times: 滚动次数，用于加载更多内容

        Returns:
            视频信息列表
        """
        self._init_browser()

        if self.debug:
            print(f"[DEBUG] 访问搜索页面: {search_url}")

        self.page.get(search_url)

        # 等待页面初步加载
        time.sleep(2)

        # 页面跳转后重新注入完整的反检测脚本
        self._inject_stealth_scripts()

        # 模拟真实用户行为 - 随机等待
        time.sleep(1 + random.random() * 2)

        # 检查并等待验证码
        if not self._check_and_wait_captcha():
            print("[错误] 验证码超时，无法继续")
            return []

        # 等待页面完全加载，直到检测到视频内容
        if not self._wait_for_page_load(max_wait=120):
            print("[警告] 页面加载超时，尝试继续...")

        videos = []

        # 先尝试提取当前页面的视频
        videos = self._extract_videos_from_page()
        if videos:
            print(f"[结果] 初始加载找到 {len(videos)} 个视频")
            self._print_videos_info(videos)

        # 滚动页面加载更多内容
        for i in range(scroll_times):
            if self.debug:
                print(f"[DEBUG] 滚动页面 ({i + 1}/{scroll_times})...")

            # 每次滚动前检查验证码
            if not self._check_and_wait_captcha(max_wait=30):
                break

            self.page.scroll.to_bottom()

            # 等待新内容加载
            time.sleep(3)

            # 尝试从页面提取视频
            new_videos = self._extract_videos_from_page()
            if new_videos:
                if len(new_videos) > len(videos):
                    new_count = len(new_videos) - len(videos)
                    print(f"[滚动 {i+1}] 找到 {len(new_videos)} 个视频 (+{new_count})")
                    # 只打印新增的视频
                    self._print_videos_info(new_videos[len(videos):])
                videos = new_videos

        # 最终打印汇总
        if videos:
            print(f"\n{'='*80}")
            print(f"[汇总] 共找到 {len(videos)} 个视频")
            print(f"{'='*80}")

        return videos

    def _print_videos_info(self, videos: List[VideoInfo]):
        """打印视频信息到控制台"""
        if not videos:
            return

        print(f"\n{'-'*80}")
        print(f"{'序号':^4} | {'视频URL':<45} | {'作者':<12} | {'点赞':>10} | {'时长':>6}")
        print(f"{'-'*80}")

        for i, v in enumerate(videos, 1):
            video_url = f"https://www.douyin.com/video/{v.aweme_id}"
            author = (v.author[:10] + '..') if len(v.author) > 12 else v.author
            likes = self._format_count(v.digg_count)
            duration = f"{int(v.duration)}s" if v.duration > 0 else "-"

            print(f"{i:^4} | {video_url:<45} | {author:<12} | {likes:>10} | {duration:>6}")

            # 如果有标题也打印
            if v.title:
                title_short = (v.title[:60] + '...') if len(v.title) > 60 else v.title
                print(f"     └─ 标题: {title_short}")

        print(f"{'-'*80}\n")

    def _format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        elif count >= 1000:
            return f"{count/1000:.1f}k"
        else:
            return str(count)

    def _extract_videos_from_page(self) -> List[VideoInfo]:
        """从页面提取视频信息"""
        videos = []

        if self.debug:
            print(f"[DEBUG] 页面标题: {self.page.title}")
            print(f"[DEBUG] 页面 URL: {self.page.url}")
            html_len = len(self.page.html) if self.page.html else 0
            print(f"[DEBUG] 页面长度: {html_len}")

        # 方法1: 从 RENDER_DATA 提取
        try:
            render_script = self.page.ele('#RENDER_DATA', timeout=2)
            if render_script:
                render_text = render_script.text
                if render_text:
                    if self.debug:
                        print(f"[DEBUG] RENDER_DATA 长度: {len(render_text)}")
                    data = json.loads(unquote(render_text))
                    videos = self._parse_search_data(data)
                    if self.debug:
                        print(f"[DEBUG] 从 RENDER_DATA 解析到 {len(videos)} 个视频")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] RENDER_DATA 解析失败: {e}")

        # 方法2: 从页面 HTML 中搜索视频数据
        if not videos:
            try:
                html = self.page.html
                # 搜索 aweme_id 模式
                aweme_ids = re.findall(r'"aweme_id"\s*:\s*"(\d+)"', html)
                if self.debug:
                    print(f"[DEBUG] 从 HTML 找到 {len(set(aweme_ids))} 个 aweme_id")

                # 尝试找到完整的 JSON 数据块
                json_matches = re.findall(r'\{"aweme_id"[^}]+?"statistics"[^}]+?\}', html)
                if self.debug:
                    print(f"[DEBUG] 找到 {len(json_matches)} 个 JSON 块")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] HTML 搜索失败: {e}")

        # 方法3: 从视频卡片元素提取
        if not videos:
            videos = self._extract_from_cards()

        return videos

    def _extract_from_cards(self) -> List[VideoInfo]:
        """从页面视频卡片元素提取 - 使用 JavaScript 直接操作 DOM"""
        videos = []

        # 使用 JavaScript 提取所有视频信息（更可靠，不依赖随机类名）
        try:
            video_data = self.page.run_js('''
                const videos = [];
                const seenIds = new Set();

                // 查找所有包含视频链接的元素
                // 链接格式: //www.douyin.com/video/xxx 或 /video/xxx
                const videoLinks = document.querySelectorAll('a[href*="douyin.com/video/"], a[href*="/video/"]');

                videoLinks.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    const match = href.match(/\\/video\\/(\\d+)/);
                    if (!match) return;

                    const videoId = match[1];
                    if (seenIds.has(videoId)) return;
                    seenIds.add(videoId);

                    // 向上查找父容器（搜索结果卡片）
                    // 尝试多种方式找到卡片容器
                    let card = link.closest('.search-result-card') ||
                               link.closest('[class*="search-result"]') ||
                               link.closest('[data-home-video-id]')?.parentElement ||
                               link.closest('[class*="videoImage"]')?.parentElement?.parentElement ||
                               link.parentElement?.parentElement?.parentElement?.parentElement;

                    let title = '';
                    let author = '';
                    let duration = '';
                    let likes = '';

                    if (card) {
                        // 方法1: 查找点赞数 - 在 SVG (心形图标) 旁边的 span
                        // 结构: <svg>...</svg><span class="xxx">2326</span>
                        const svgElements = card.querySelectorAll('svg');
                        for (const svg of svgElements) {
                            const nextSpan = svg.nextElementSibling;
                            if (nextSpan && nextSpan.tagName === 'SPAN') {
                                const text = nextSpan.textContent?.trim() || '';
                                // 检查是否是数字（可能带万/w/k后缀）
                                if (text.match(/^[\\d.]+[万wk]?$/i)) {
                                    likes = text;
                                    break;
                                }
                            }
                        }

                        // 方法2: 如果方法1没找到，查找包含心形path的svg旁边的span
                        if (!likes) {
                            const likeContainer = card.querySelector('svg[viewBox="0 0 24 24"]');
                            if (likeContainer) {
                                const parent = likeContainer.parentElement;
                                const likeSpan = parent?.querySelector('span');
                                if (likeSpan) {
                                    likes = likeSpan.textContent?.trim() || '';
                                }
                            }
                        }

                        // 提取时长 - 在视频封面上，格式如 01:28
                        // 查找只包含时间格式的元素
                        const allDivs = card.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.textContent?.trim() || '';
                            // 精确匹配时长格式，且元素只包含时长文本
                            if (text.match(/^\\d{1,2}:\\d{2}(:\\d{2})?$/) && div.children.length === 0) {
                                duration = text;
                                break;
                            }
                        }

                        // 提取作者 - 在 @ 符号后面
                        // 结构: <span>@</span><span class="xxx">作者名</span>
                        const atSpans = card.querySelectorAll('span');
                        for (let i = 0; i < atSpans.length; i++) {
                            if (atSpans[i].textContent?.trim() === '@' && atSpans[i + 1]) {
                                author = atSpans[i + 1].textContent?.trim() || '';
                                break;
                            }
                        }

                        // 提取标题 - 查找较长的文本内容
                        // 通常是卡片中最长的非数字文本
                        for (const div of allDivs) {
                            // 只检查叶子节点或只包含文本的节点
                            if (div.children.length === 0 ||
                                (div.children.length > 0 && div.textContent === div.innerText)) {
                                const text = div.textContent?.trim() || '';
                                // 标题通常较长，排除时长、数字、作者等
                                if (text.length > 15 &&
                                    !text.match(/^[\\d:]+$/) &&
                                    !text.match(/^[\\d.]+[万wk]?$/i) &&
                                    !text.startsWith('@') &&
                                    !text.includes('月前') &&
                                    !text.includes('天前') &&
                                    !text.includes('小时前')) {
                                    // 选择合适长度的文本作为标题
                                    if (!title || (text.length > title.length && text.length < 200)) {
                                        title = text.substring(0, 150);
                                    }
                                }
                            }
                        }
                    }

                    // 也尝试从链接的 title 属性获取标题
                    if (!title) {
                        title = link.getAttribute('title') || '';
                    }

                    videos.push({
                        id: videoId,
                        title: title,
                        author: author,
                        duration: duration,
                        likes: likes
                    });
                });

                return JSON.stringify(videos);
            ''')

            if video_data:
                try:
                    parsed = json.loads(video_data)
                    if self.debug:
                        print(f"[DEBUG] JavaScript 提取到 {len(parsed)} 个视频")

                    for item in parsed:
                        # 解析时长
                        duration = 0
                        if item.get('duration'):
                            parts = item['duration'].split(':')
                            try:
                                if len(parts) == 2:
                                    duration = int(parts[0]) * 60 + int(parts[1])
                                elif len(parts) == 3:
                                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            except:
                                pass

                        # 解析点赞数
                        digg_count = self._parse_count(item.get('likes', ''))

                        videos.append(VideoInfo(
                            aweme_id=item['id'],
                            title=item.get('title', ''),
                            author=item.get('author', 'unknown'),
                            duration=duration,
                            digg_count=digg_count,
                            play_count=0
                        ))
                except json.JSONDecodeError as e:
                    if self.debug:
                        print(f"[DEBUG] JSON 解析失败: {e}")

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] JavaScript 提取失败: {e}")

        # 备用方法: 如果 JavaScript 方法失败，尝试使用正则从 HTML 提取
        if not videos:
            try:
                html = self.page.html
                # 查找所有视频 ID
                video_ids = re.findall(r'douyin\.com/video/(\d+)|href="/video/(\d+)', html)
                seen_ids = set()
                for match in video_ids:
                    video_id = match[0] or match[1]
                    if video_id and video_id not in seen_ids:
                        seen_ids.add(video_id)
                        videos.append(VideoInfo(
                            aweme_id=video_id,
                            title='',
                            author='unknown',
                            duration=0,
                            digg_count=0,
                            play_count=0
                        ))

                if self.debug and videos:
                    print(f"[DEBUG] 从 HTML 正则提取到 {len(videos)} 个视频")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] HTML 正则提取失败: {e}")

        return videos

    def _parse_count(self, text: str) -> int:
        """解析数量文本 (如 1.2万, 1.5w, 421, 100k 等)"""
        if not text:
            return 0

        text = text.strip().lower().replace(',', '')

        try:
            # 处理万
            if '万' in text or 'w' in text:
                num = float(re.sub(r'[^\d.]', '', text))
                return int(num * 10000)
            # 处理 k
            elif 'k' in text:
                num = float(re.sub(r'[^\d.]', '', text))
                return int(num * 1000)
            # 纯数字
            else:
                return int(re.sub(r'[^\d]', '', text) or 0)
        except:
            return 0

    def _parse_search_data(self, data: dict, depth: int = 0) -> List[VideoInfo]:
        """递归解析搜索数据"""
        videos = []

        if depth > 15:
            return videos

        if isinstance(data, dict):
            # 检查是否是视频列表
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            # 检查 aweme_list
            if 'aweme_list' in data and isinstance(data['aweme_list'], list):
                for item in data['aweme_list']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            # 递归搜索
            for value in data.values():
                videos.extend(self._parse_search_data(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                videos.extend(self._parse_search_data(item, depth + 1))

        # 去重
        seen = set()
        unique_videos = []
        for v in videos:
            if v.aweme_id not in seen:
                seen.add(v.aweme_id)
                unique_videos.append(v)

        return unique_videos

    def _parse_video_item(self, item: dict) -> Optional[VideoInfo]:
        """解析单个视频项"""
        try:
            # 可能在 aweme_info 里
            aweme = item.get('aweme_info') or item

            aweme_id = aweme.get('aweme_id')
            if not aweme_id:
                return None

            # 获取时长 (毫秒转秒)
            duration_ms = aweme.get('video', {}).get('duration', 0)
            if not duration_ms:
                duration_ms = aweme.get('duration', 0)
            duration = duration_ms / 1000 if duration_ms > 1000 else duration_ms

            # 获取统计数据
            statistics = aweme.get('statistics', {})
            digg_count = statistics.get('digg_count', 0)
            play_count = statistics.get('play_count', 0)

            # 获取发布时间
            create_time = aweme.get('create_time', 0)

            # 标题和作者
            title = aweme.get('desc', '')[:100]
            author = aweme.get('author', {}).get('nickname', 'unknown')

            # 视频 URL
            video_url = ""
            video_data = aweme.get('video', {})
            play_addr = video_data.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            if url_list:
                video_url = url_list[2] if len(url_list) > 2 else url_list[0]

            # 封面
            cover_url = ""
            cover_data = video_data.get('cover', {}) or video_data.get('origin_cover', {})
            cover_list = cover_data.get('url_list', [])
            if cover_list:
                cover_url = cover_list[0]

            return VideoInfo(
                aweme_id=aweme_id,
                title=title,
                author=author,
                duration=duration,
                digg_count=digg_count,
                play_count=play_count,
                video_url=video_url,
                cover_url=cover_url,
                create_time=create_time
            )
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 解析视频项失败: {e}")
            return None

    def _extract_from_network(self) -> List[VideoInfo]:
        """从网络请求中提取（备用方案）"""
        # TODO: 可以通过监听网络请求获取
        return []

    def filter_videos(
        self,
        videos: List[VideoInfo],
        min_duration: float = 0,
        max_duration: float = 9999,
        top_n: int = 1,
        sort_by: str = "digg"  # digg, time, or digg_time
    ) -> List[VideoInfo]:
        """
        筛选视频

        Args:
            videos: 视频列表
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
            top_n: 返回前 N 个
            sort_by: 排序方式 - digg(点赞), time(最新), digg_time(点赞+最新)

        Returns:
            筛选后的视频列表
        """
        # 按时长筛选
        if min_duration > 0 or max_duration < 9999:
            filtered = [v for v in videos if min_duration <= v.duration <= max_duration]
            if self.debug:
                print(f"[DEBUG] 时长 {min_duration}-{max_duration}s 筛选后: {len(filtered)} 个视频")
        else:
            filtered = videos.copy()

        # 排序
        if sort_by == "time":
            # 按发布时间排序（最新的在前）
            filtered.sort(key=lambda x: x.create_time, reverse=True)
        elif sort_by == "digg_time":
            # 先按时间筛选最新的，再按点赞排序
            filtered.sort(key=lambda x: x.create_time, reverse=True)
            # 取最新的一批（比如前50%或至少top_n*3个）
            recent_count = max(len(filtered) // 2, top_n * 3, 10)
            recent = filtered[:recent_count]
            # 再按点赞排序
            recent.sort(key=lambda x: x.digg_count, reverse=True)
            filtered = recent
        else:  # digg
            # 按点赞量排序
            filtered.sort(key=lambda x: x.digg_count, reverse=True)

        return filtered[:top_n]

    def get_video_url(self, aweme_id: str) -> str:
        """获取视频的下载 URL"""
        video_page_url = f"https://www.douyin.com/video/{aweme_id}"

        if self.debug:
            print(f"[DEBUG] 获取视频详情: {video_page_url}")

        self.page.get(video_page_url)
        time.sleep(3)

        # 尝试从 source 元素获取
        for _ in range(10):
            try:
                source_ele = self.page.ele('tag:source', timeout=1)
                if source_ele:
                    src = source_ele.attr('src')
                    if src and src.startswith('http'):
                        return src
            except Exception:
                pass
            time.sleep(1)

        return ""

    def download_video(self, video_url: str, output_path: str) -> bool:
        """下载视频"""
        video_url = video_url.replace('http:', 'https:')

        print(f"开始下载: {video_url[:80]}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.douyin.com/',
        }

        try:
            resp = requests.get(video_url, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()

            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度: {percent:.1f}%", end='')

            print(f"\n下载完成: {output_path}")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False

    def search_and_download(
        self,
        search_url: str,
        min_duration: float = 0,
        max_duration: float = 9999,
        top_n: int = 1,
        output_dir: str = ".",
        scroll_times: int = 5,
        sort_by: str = "digg"
    ):
        """
        搜索并下载视频

        Args:
            search_url: 搜索页面 URL
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
            top_n: 下载前 N 个
            output_dir: 输出目录
            scroll_times: 滚动次数
            sort_by: 排序方式
        """
        from datetime import datetime

        print(f"正在搜索视频...")
        sort_desc = {"digg": "点赞最高", "time": "最新发布", "digg_time": "最新+点赞最高"}
        print(f"筛选条件: {sort_desc.get(sort_by, sort_by)}, 下载 {top_n} 个")
        if min_duration > 0 or max_duration < 9999:
            print(f"时长限制: {min_duration}-{max_duration} 秒")
        print()

        # 1. 获取搜索结果
        videos = self.search_videos(search_url, scroll_times)

        if not videos:
            print("未找到任何视频")
            return

        print(f"找到 {len(videos)} 个视频")
        print()

        # 显示所有视频信息
        def format_time(ts):
            if ts:
                try:
                    return datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
                except:
                    pass
            return "未知"

        print("=" * 100)
        print(f"{'ID':<20} {'时长':>8} {'点赞':>12} {'发布时间':<12} {'标题':<30}")
        print("=" * 100)
        for v in sorted(videos, key=lambda x: x.digg_count, reverse=True)[:20]:
            title_short = v.title[:26] + '..' if len(v.title) > 28 else v.title
            pub_time = format_time(v.create_time)
            print(f"{v.aweme_id:<20} {v.duration:>6.1f}s {v.digg_count:>12,} {pub_time:<12} {title_short}")
        print("=" * 100)
        print()

        # 2. 筛选视频
        selected = self.filter_videos(videos, min_duration, max_duration, top_n, sort_by)

        if not selected:
            print(f"没有找到符合条件的视频")
            durations = [v.duration for v in videos]
            if durations:
                print(f"提示: 当前视频时长范围 {min(durations):.1f}s - {max(durations):.1f}s")
            return

        print(f"筛选出 {len(selected)} 个符合条件的视频:")
        for i, v in enumerate(selected, 1):
            pub_time = format_time(v.create_time)
            print(f"  {i}. [{v.aweme_id}] 时长:{v.duration:.1f}s 点赞:{v.digg_count:,} 发布:{pub_time}")
            print(f"     标题: {v.title[:60]}...")
        print()

        # 3. 下载视频
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, video in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] 正在下载视频 {video.aweme_id}...")

            # 获取视频 URL
            video_url = video.video_url
            if not video_url or 'douyin' not in video_url:
                video_url = self.get_video_url(video.aweme_id)

            if not video_url:
                print(f"无法获取视频 URL，跳过")
                continue

            # 下载
            filename = f"douyin_{video.aweme_id}_{video.duration:.0f}s_{video.digg_count}.mp4"
            filepath = output_path / filename
            self.download_video(video_url, str(filepath))

    def close(self):
        """关闭浏览器"""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None


def main():
    parser = argparse.ArgumentParser(
        description='抖音搜索视频下载器 - 自动筛选并下载符合条件的视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 下载点赞最高的 5 个视频
  python douyin_search_downloader.py <url> --top 5

  # 下载最新且点赞最高的 5 个视频
  python douyin_search_downloader.py <url> --top 5 --sort digg_time

  # 下载时长 30-40 秒、点赞最高的前 3 个
  python douyin_search_downloader.py <url> --min-duration 30 --max-duration 40 --top 3

  # 更多滚动以加载更多视频
  python douyin_search_downloader.py <url> --scroll 10

排序方式:
  digg      - 按点赞量排序（默认）
  time      - 按发布时间排序（最新的在前）
  digg_time - 从最新视频中选点赞最高的
        '''
    )
    parser.add_argument('url', help='抖音搜索页面 URL')
    parser.add_argument('--min-duration', type=float, default=0, help='最小时长（秒），默认不限')
    parser.add_argument('--max-duration', type=float, default=9999, help='最大时长（秒），默认不限')
    parser.add_argument('--top', type=int, default=1, help='下载前 N 个，默认 1')
    parser.add_argument('--sort', choices=['digg', 'time', 'digg_time'], default='digg_time',
                        help='排序方式: digg(点赞), time(最新), digg_time(最新+点赞)')
    parser.add_argument('--output', '-o', default='.', help='输出目录')
    parser.add_argument('--scroll', type=int, default=5, help='滚动次数（加载更多），默认 5')
    parser.add_argument('--headless', action='store_true', help='无头模式（不显示浏览器）')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    downloader = None
    try:
        downloader = DouyinSearchDownloader(
            headless=args.headless,
            debug=args.debug
        )
        downloader.search_and_download(
            search_url=args.url,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            top_n=args.top,
            output_dir=args.output,
            scroll_times=args.scroll,
            sort_by=args.sort
        )
    except KeyboardInterrupt:
        print("\n用户取消")
    except Exception as e:
        print(f"\n错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        if downloader:
            downloader.close()

    return 0


if __name__ == '__main__':
    exit(main())
