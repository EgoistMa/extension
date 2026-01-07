"""抖音视频上传器

实现视频上传到抖音创作者中心
"""

import time
import re
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, List
from DrissionPage import ChromiumPage

from core.browser_manager import BrowserManager
from core.config import Config
from models.video import ExportedVideo


class DouyinUploader:
    """抖音视频上传器"""

    HOME_URL = "https://creator.douyin.com/creator-micro/home"
    POST_URL_PREFIX = "https://creator.douyin.com/creator-micro/content/post/video"

    def __init__(
        self,
        browser_manager: BrowserManager,
        account_id: str,
        config: Optional[Config] = None
    ):
        """初始化上传器

        Args:
            browser_manager: 浏览器管理器
            account_id: 账户ID
            config: 配置对象
        """
        self.browser_manager = browser_manager
        self.account_id = account_id
        self.config = config or Config()
        self.page: Optional[ChromiumPage] = None
        self.debug = bool(self.config.get("douyin_upload.debug", False))

    def start(self, headless: bool = False) -> None:
        """启动浏览器"""
        self.page = self.browser_manager.navigate_to_platform(
            self.account_id, 'douyin_creator', headless
        )

    def close(self) -> None:
        """关闭浏览器"""
        self.browser_manager.close_browser(self.account_id, 'douyin_creator')
        self.page = None

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.browser_manager.is_logged_in(self.account_id, 'douyin_creator')

    def wait_for_login(self, timeout: float = 300) -> bool:
        """等待用户登录

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否登录成功
        """
        return self.browser_manager.wait_for_login(
            self.account_id, 'douyin_creator', timeout
        )

    def upload_video(
        self,
        video: ExportedVideo,
        cover_paths: Optional[List[str]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """上传视频并发布"""
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        if not self.page:
            self.start()

        need_home = True
        try:
            url = self.page.url or ""
            if "creator.douyin.com" in url and "creator-micro" in url:
                need_home = False
        except Exception:
            need_home = True

        if need_home:
            log("打开抖音创作者中心...")
            self.page.get(self.HOME_URL)

        home_wait_start = time.time()
        try:
            home_btn = self.page.ele('#douyin-creator-master-side-upload', timeout=15)
        except Exception:
            home_btn = None
        log(f"[perf] home_ready_ms={int((time.time() - home_wait_start) * 1000)}")
        if not home_btn:
            log("高清发布入口未出现")
            return False

        upload_ready_start = time.time()
        if not self._click_hd_publish():
            log("打开高清发布入口失败")
            return False
        log(f"[perf] upload_page_ready_ms={int((time.time() - upload_ready_start) * 1000)}")

        if not self._wait_for_upload_page():
            log("打开上传页面失败")
            return False

        if not self.is_logged_in():
            log("未登录，等待扫码登录...")
            if not self.wait_for_login():
                log("登录失败")
                return False
            log("已登录")

        if on_progress:
            on_progress("上传中", 1, 5)

        try:
            publish_job = {
                "files": {
                    "video_path": video.local_path,
                    "cover_vertical_path": cover_paths[0] if cover_paths else None,
                    "cover_horizontal_path": cover_paths[1] if cover_paths and len(cover_paths) > 1 else None
                },
                "content": {
                    "title": video.title or "测试标题",
                    "description": video.description or "测试描述"
                },
                "category": {
                    "primary": "影视演艺",
                    "description": "测试标签"
                },
                "publish_settings": {
                    "visibility": self.config.get("douyin_upload.visibility", "private"),
                    "download_permission": self.config.get("douyin_upload.download_permission", "allow"),
                    "schedule": {
                        "enable": self.config.get("douyin_upload.schedule.enable", True),
                        "date": self.config.get("douyin_upload.schedule.date", ""),
                        "time": self.config.get("douyin_upload.schedule.time", ""),
                        "offset_minutes": int(self.config.get("douyin_upload.schedule.offset_minutes", 1))
                    }
                }
            }

            if not cover_paths:
                fixed_cover = r"C:\Users\21346\OneDrive\桌面\jianying_test\6a10ed554835d75782f8a37301fe42b.jpg"
                publish_job["files"]["cover_vertical_path"] = fixed_cover
                publish_job["files"]["cover_horizontal_path"] = fixed_cover

            if self.page.url.startswith(self.POST_URL_PREFIX):
                if not self._wait_for_upload_done_on_post_page(timeout=1800, log=log):
                    log("发布页上传未完成")
                    return False
            else:
                find_input_start = time.time()
                upload_input = self._find_upload_input(timeout=5)
                log(f"[perf] find_input_ms={int((time.time() - find_input_start) * 1000)}")
                if not upload_input:
                    log("找不到上传输入框")
                    self._dump_dom_context(log, "upload_input_not_found")
                    return False

                log(f"上传视频: {video.local_path}")
                upload_input.input(video.local_path)

                if on_progress:
                    on_progress("上传完成", 2, 5)

                if not self._wait_for_upload_complete():
                    log("上传超时")
                    self._dump_dom_context(log, "upload_timeout")
                    return False

                log("文件上传完成")

                if not self._wait_for_post_page():
                    log("跳转发布页失败")
                    self._dump_dom_context(log, "post_page_not_loaded")
                    return False

                if not self._wait_for_upload_done_on_post_page(timeout=1800, log=log):
                    log("发布页上传未完成")
                    return False

            if on_progress:
                on_progress("设置封面", 3, 5)

            if not self._ensure_publish_form_filled(publish_job, log):
                return False

            if on_progress:
                on_progress("等待发布", 4, 5)

            if not self._click_publish(log):
                self._log_publish_validation_hints(log)
                return False

            hints = self._log_publish_validation_hints(log)
            if hints:
                return False

            if not self._wait_for_publish_complete():
                log("发布超时")
                self._dump_dom_context(log, "publish_timeout")
                return False

            if on_progress:
                on_progress("发布完成", 5, 5)

            log("发布成功!")
            video.is_uploaded = True
            video.uploaded_at = datetime.now().isoformat()
            return True

        except Exception as e:
            log(f"发布异常: {e}")
            return False

    def _pick_random_cover_from_dir(self, cover_dir: str, log: Callable[[str], None]) -> Optional[str]:
        """从目录中随机选择一张封面图片"""
        try:
            path = Path(cover_dir)
            if not path.exists() or not path.is_dir():
                log(f"封面目录不存在: {cover_dir}")
                return None
            candidates = []
            for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"):
                candidates.extend(path.glob(f"*{ext}"))
                candidates.extend(path.glob(f"*{ext.upper()}"))
            if not candidates:
                log(f"封面目录没有可用图片: {cover_dir}")
                return None
            choice = random.choice(candidates)
            log(f"选择封面图片: {choice}")
            return str(choice)
        except Exception as e:
            log(f"封面图片选择失败: {e}")
            return None
    def _find_upload_input(self, timeout: int = 5) -> Optional[object]:
        """查找上传输入框"""
        root_selectors = [
            'css:div.container-drag-VAfIfu',
            'css:div[class*="container-drag"]',
            'xpath://div[contains(@class,"container-drag")]',
        ]
        input_selectors = [
            'css:input[type="file"][accept*="video/mp4"]',
            'css:input[type="file"][accept*=".mp4"]',
            'css:input[type="file"][accept*="video/"]',
        ]

        root = None
        for selector in root_selectors:
            try:
                root = self.page.ele(selector, timeout=timeout)
                if root:
                    break
            except Exception:
                pass

        if root:
            for selector in input_selectors:
                try:
                    ele = root.ele(selector, timeout=1)
                    if ele:
                        return ele
                except Exception:
                    pass

        fallback_selectors = [
            'css:input[type="file"][accept*="video/mp4"]',
            'css:input[type="file"][accept*=".mp4"]',
            'css:input[type="file"][accept*="video/"]',
            'xpath://input[@type="file" and contains(@accept,"video")]',
        ]
        for selector in fallback_selectors:
            try:
                ele = self.page.ele(selector, timeout=timeout)
                if ele:
                    return ele
            except Exception:
                pass

        return None

    def _click_hd_publish(self) -> bool:
        """点击首页高清发布入口"""
        selectors = [
            '#douyin-creator-master-side-upload',
            'span:contains("高清发布")'
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=5)
                if ele:
                    ele.click()
                    try:
                        if self.page.ele('css:div.container-drag-VAfIfu', timeout=15):
                            return True
                    except Exception:
                        pass
            except Exception:
                pass
        return False

    def _ensure_video_ready_before_publish(
        self,
        timeout: int = 1800,
        log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """发布前确保视频上传完成"""
        if self._wait_until_ready_to_publish(timeout=30, log=log):
            return True
        return self._wait_for_upload_done_on_post_page(timeout=timeout, log=log)

    def _click_upload_video(self) -> bool:
        """点击上传视频按钮"""
        selectors = [
            'button.container-drag-btn-k6XmB4',
            'button[class*="container-drag-btn"]',
            'button:contains("上传视频")',
            'span:contains("上传视频")'
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=5)
                if ele:
                    ele.click()
                    time.sleep(1)
                    return True
            except Exception:
                pass
        # XPath 兜底
        try:
            ele = self.page.ele('xpath://button//span[contains(text(),"上传视频")]/ancestor::button[1]', timeout=5)
            if ele:
                ele.click()
                time.sleep(1)
                return True
        except Exception:
            pass
        # JS 兜底
        try:
            js = (
                "const btns = Array.from(document.querySelectorAll('button'));"
                "const target = btns.find(b => (b.innerText || '').includes('上传视频'));"
                "if (target) { target.click(); return true; }"
                "return false;"
            )
            if self.page.run_js(js):
                time.sleep(1)
                return True
        except Exception:
            pass
        return False

    def _wait_for_upload_page(self, timeout: int = 30) -> bool:
        """等待跳转到上传页面"""
        start_time = time.time()
        container_selectors = [
            'css:div.container-drag-VAfIfu',
            'css:div[class*="container-drag"]',
        ]
        while time.time() - start_time < timeout:
            try:
                for selector in container_selectors:
                    ele = self.page.ele(selector, timeout=1)
                    if ele:
                        return True
            except Exception:
                pass
            try:
                if 'creator-micro/content/upload' in (self.page.url or ''):
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def _wait_for_post_page(self, timeout: int = 120) -> bool:
        """等待跳转到发布页面"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.page.url.startswith(self.POST_URL_PREFIX):
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def _wait_for_upload_done_on_post_page(
        self,
        timeout: int = 1800,
        log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """发布页等待上传完成"""
        def _log(msg: str):
            if log:
                log(msg)

        try:
            if not self.page.url.startswith(self.POST_URL_PREFIX):
                _log("未进入发布页，无法监控上传进度")
                return False
        except Exception:
            return False

        container_selectors = [
            'css:div[class*="upload-card"]',
            'css:div[class*="uploading-container"]',
        ]
        percent_selector = 'xpath://span[contains(@class,"text-hkyzAY") and contains(normalize-space(.),"%")]'
        uploaded_selector = (
            'xpath://div[contains(@class,"upload-progress-detail-inner")]'
            '//div[contains(@class,"text-hkyzAY") and contains(normalize-space(.),"已上传")]'
        )
        extra_selector = (
            'xpath://div[contains(@class,"upload-progress-detail-inner")]'
            '//div[contains(@class,"text-hkyzAY") and (contains(normalize-space(.),"速度") '
            'or contains(normalize-space(.),"剩余"))]'
        )
        done_selectors = [
            'xpath://div[contains(text(),"上传完成")]',
            'xpath://div[contains(text(),"上传成功")]',
            'xpath://div[contains(text(),"已完成")]',
            'xpath://span[contains(text(),"上传完成")]',
            'xpath://span[contains(text(),"上传成功")]',
            'xpath://span[contains(text(),"已完成")]',
        ]
        error_selectors = [
            'xpath://div[contains(text(),"上传失败")]',
            'xpath://div[contains(text(),"错误")]',
            'xpath://div[contains(@class,"error") and string-length(normalize-space())>0]',
        ]

        seen_container = False
        end = time.time() + timeout
        while time.time() < end:
            for selector in error_selectors:
                try:
                    ele = self.page.ele(selector, timeout=0.2)
                except Exception:
                    ele = None
                if ele:
                    text = (ele.text or "").strip()
                    if text:
                        _log(f"上传异常: {text}")
                    return False

            for selector in done_selectors:
                try:
                    ele = self.page.ele(selector, timeout=0.2)
                except Exception:
                    ele = None
                if ele:
                    text = (ele.text or "").strip()
                    if text:
                        _log(f"上传完成提示: {text}")
                    return True

            container = None
            for selector in container_selectors:
                try:
                    container = self.page.ele(selector, timeout=0.2)
                except Exception:
                    container = None
                if container:
                    break

            if container:
                seen_container = True
            elif seen_container:
                _log("[upload] container_gone=Y")
                return True

            percent = None
            percent_text = ""
            uploaded_text = ""
            extra_text = ""

            try:
                ele = self.page.ele(percent_selector, timeout=0.2)
                if ele:
                    percent_text = (ele.text or "").strip()
                    match = re.search(r"(\d+(?:\.\d+)?)\s*%", percent_text)
                    if match:
                        percent = float(match.group(1))
            except Exception:
                pass

            if percent is None:
                try:
                    bar = self.page.ele('css:div.semi-progress-track-inner', timeout=0.2)
                except Exception:
                    bar = None
                if bar:
                    try:
                        style = bar.attr("style") or ""
                    except Exception:
                        style = ""
                    match = re.search(r"width\s*:\s*(\d+(?:\.\d+)?)%", style)
                    if match:
                        percent = float(match.group(1))

            try:
                ele = self.page.ele(uploaded_selector, timeout=0.2)
                if ele:
                    uploaded_text = (ele.text or "").strip()
            except Exception:
                pass

            try:
                ele = self.page.ele(extra_selector, timeout=0.2)
                if ele:
                    extra_text = (ele.text or "").strip()
            except Exception:
                pass

            percent_display = f"{percent:.1f}%" if isinstance(percent, (int, float)) else percent_text or "N/A"
            _log(f"[upload] percent={percent_display} uploaded_text={uploaded_text} extra={extra_text}")

            if percent is not None and percent >= 99.9:
                return True
            if "100%" in percent_text:
                return True

            time.sleep(0.5)

        return False

    def _ensure_publish_form_filled(self, publish_job: dict, log: Callable[[str], None]) -> bool:
        """确保发布页表单填写完成"""
        vertical_path = publish_job["files"]["cover_vertical_path"]
        horizontal_path = publish_job["files"]["cover_horizontal_path"]
        if not vertical_path or not horizontal_path:
            log("封面路径缺失，竖封面和横封面都必须提供")
            return False

        if not self._set_cover_images(vertical_path, horizontal_path, log):
            return False

        if not self._wait_title_and_desc_ready(timeout=20):
            log("标题/描述区域未就绪")
            self._dump_dom_context(log, "title_desc_not_ready")
            return False

        title = publish_job["content"]["title"]
        self._title_log = log
        if self._fill_title(title):
            log(f"标题: {title}")
        else:
            log("标题未设置成功")
            self._dump_dom_context(log, "title_set_failed")
            return False

        description = publish_job["content"]["description"]
        if self._fill_description(description):
            log("描述已设置")
        else:
            log("描述未设置成功")
            self._dump_dom_context(log, "description_set_failed")
            return False

        time.sleep(0.4)
        self._ensure_title_persisted(title, log)

        category_name = publish_job["category"].get("primary")
        if category_name:
            if self._select_category(category_name, log):
                log(f"分类: {category_name}")
            else:
                log(f"分类未选择成功: {category_name}")

        log("发布设置...")
        if not self._apply_publish_settings(publish_job["publish_settings"], log):
            log("发布设置失败")
            self._dump_dom_context(log, "publish_settings_failed")
            return False

        return True

    def _validate_required_fields(self, log: Callable[[str], None]) -> tuple[bool, list[str]]:
        """校验必填字段是否完整"""
        missing = []
        title_value = ""
        try:
            title_value = self._read_input_value_js(
                'input.semi-input[type="text"][placeholder*="\u586b\u5199\u4f5c\u54c1\u6807\u9898"]'
            )
        except Exception:
            title_value = ""
        if not (title_value or "").strip():
            missing.append("title")

        schedule_enabled = bool(self.config.get("douyin_upload.schedule.enable", True))
        if schedule_enabled:
            try:
                js = (
                    "const el = document.querySelector('input.semi-input[placeholder*=\"日期和时间\"]');"
                    "return el ? (el.value || '').trim() : '';"
                )
                schedule_value = (self.page.run_js(js) or "").strip()
            except Exception:
                schedule_value = ""
            log(f'schedule_final="{schedule_value}"')
            if not schedule_value or " " not in schedule_value:
                missing.append("schedule")

        selected_category = self._read_selected_category()
        if not selected_category:
            missing.append("category")

        try:
            js = (
                "const cards = Array.from(document.querySelectorAll('div.coverControl, div[class*=\"coverControl\"]'));"
                "for (const card of cards) {"
                "  const bg = card.querySelector('div.bg, div[class*=\"bg\"]');"
                "  if (bg) {"
                "    const style = bg.getAttribute('style') || '';"
                "    const bgImg = getComputedStyle(bg).backgroundImage || '';"
                "    if (style.includes('background-image') || style.includes('data:image') || style.includes('blob:')) return true;"
                "    if (bgImg && bgImg !== 'none') return true;"
                "  }"
                "  const img = card.querySelector('img');"
                "  if (img && img.src) return true;"
                "}"
                "return false;"
            )
            cover_ok = bool(self.page.run_js(js))
        except Exception:
            cover_ok = False
        if not cover_ok:
            cover_ok = bool(getattr(self, "_cover_set_ok", False))
        if not cover_ok:
            missing.append("cover")

        if missing:
            log(f"必填缺失: {', '.join(missing)}")
        return (len(missing) == 0, missing)

    def _log_publish_validation_hints(self, log: Callable[[str], None]) -> list[str]:
        """读取并打印发布校验提示"""
        hints = []
        selectors = [
            'xpath://div[contains(@class,"error") and (contains(normalize-space(.),"必填") or contains(normalize-space(.),"请填写") or contains(normalize-space(.),"未完成"))]',
            'xpath://span[contains(@class,"error") and (contains(normalize-space(.),"必填") or contains(normalize-space(.),"请填写") or contains(normalize-space(.),"未完成"))]',
            'xpath://div[contains(@class,"warning") and (contains(normalize-space(.),"必填") or contains(normalize-space(.),"请填写") or contains(normalize-space(.),"未完成"))]',
            'xpath://span[contains(@class,"text") and (contains(normalize-space(.),"必填") or contains(normalize-space(.),"请填写") or contains(normalize-space(.),"未完成"))]',
        ]
        for selector in selectors:
            try:
                eles = self.page.eles(selector, timeout=0.5) or []
            except Exception:
                eles = []
            for ele in eles:
                try:
                    text = (ele.text or "").strip()
                except Exception:
                    text = ""
                if text and text not in hints:
                    hints.append(text)
        if hints:
            log(f"发布校验提示: {' | '.join(hints)}")
        return hints

    def _set_cover_images(self, vertical_path: str, horizontal_path: str, log: Callable[[str], None]) -> bool:
        """设置封面图片"""
        if not vertical_path or not horizontal_path:
            return False

        vertical_xpath = (
            'xpath://div[contains(text(),"竖封面3:4")]'
            '/ancestor::div[contains(@class,"coverControl")][1]'
        )
        horizontal_xpath = (
            'xpath://div[contains(text(),"横封面4:3")]'
            '/ancestor::div[contains(@class,"coverControl")][1]'
        )

        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                v_card = self.page.ele(vertical_xpath, timeout=1)
                h_card = self.page.ele(horizontal_xpath, timeout=1)
                if v_card and h_card:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        else:
            return False
        if not self._open_cover_modal_by_xpath(vertical_xpath, log):
            return False

        modal = self._get_cover_modal()
        if not modal:
            return False

        if not self._upload_cover_in_modal(modal, vertical_path, label="竖封面3:4", log=log):
            log("竖封面上传失败")
            return False
        log("竖封面上传成功")

        if not self._click_modal_button_by_span(modal, "完成", log):
            return False

        self._cover_set_ok = True
        return True

    def _open_cover_modal_by_xpath(self, card_xpath: str, log: Callable[[str], None]) -> bool:
        """点击封面卡片打开弹窗"""
        try:
            card = self.page.ele(card_xpath, timeout=2)
        except Exception:
            card = None

        if not card:
            return False

        try:
            card.click()
        except Exception:
            try:
                cover_area = card.ele('xpath:.//div[contains(@class,"cover")]', timeout=1)
                if cover_area:
                    cover_area.click()
            except Exception:
                pass

        for _ in range(10):
            if self._get_cover_modal():
                return True
            time.sleep(0.5)
        return False

    def _upload_cover_in_modal(
        self,
        modal: object,
        image_path: str,
        label: str,
        log: Callable[[str], None]
    ) -> bool:
        """在弹窗内上传封面"""
        container = self._find_cover_container_in_modal(modal, label, log)
        if not container:
            return False

        before_bg = ""
        try:
            bg = container.ele('xpath:.//div[contains(@class,"bg")]', timeout=1)
            before_bg = (bg.attr("style") or "") if bg else ""
        except Exception:
            before_bg = ""

        activate_targets = [
            'xpath:.//*[contains(text(),"点击上传文件或拖拽文件到这里")]/ancestor::div[contains(@class,"semi-upload-drag-area")][1]',
            'css:.semi-upload-drag-area',
            'xpath:.//div[contains(text(),"上传封面")]',
        ]
        activated = False
        for selector in activate_targets:
            try:
                act = container.ele(selector, timeout=1)
            except Exception:
                act = None
            if act:
                try:
                    act.click()
                    activated = True
                    break
                except Exception:
                    pass

        time.sleep(0.3)

        inputs = [
            'css:input.semi-upload-hidden-input',
            'css:input[type="file"]',
        ]
        for selector in inputs:
            try:
                ele = container.ele(selector, timeout=1)
            except Exception:
                ele = None
            if not ele:
                continue
            try:
                idx = self.page.run_js(
                    "const root = arguments[0];"
                    "const el = arguments[1];"
                    "const arr = Array.from(root.querySelectorAll('input[type=\"file\"]'));"
                    "return arr.indexOf(el);",
                    modal,
                    ele,
                )
            except Exception:
                idx = -1
            try:
                ele_class = ele.attr("class") or ""
            except Exception:
                ele_class = ""
            try:
                ele_accept = ele.attr("accept") or ""
            except Exception:
                ele_accept = ""
            if not self._is_visible(ele):
                try:
                    self.page.run_js(
                        "const el = arguments[0];"
                        "if (!el) return;"
                        "el.style.display='block';"
                        "el.style.opacity='0';"
                        "el.style.width='1px';"
                        "el.style.height='1px';"
                        "el.style.position='fixed';"
                        "el.style.left='-10px';",
                        ele,
                    )
                except Exception:
                    pass
            try:
                ele.input(image_path)
            except Exception as e:
                continue

            time.sleep(1.5)
            toast_hit = self._has_unsupported_cover_toast()

            after_bg = ""
            bg_changed = False
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    bg = container.ele('xpath:.//div[contains(@class,"bg")]', timeout=1)
                    after_bg = (bg.attr("style") or "") if bg else ""
                except Exception:
                    after_bg = ""
                if after_bg != before_bg and "background-image" in after_bg:
                    bg_changed = True
                    break
                if "data:image" in after_bg or "blob:" in after_bg:
                    bg_changed = True
                    break
                time.sleep(0.5)

            if bg_changed:
                return True

        return False

    def _has_unsupported_cover_toast(self, timeout: float = 1.5) -> bool:
        """检测不支持的封面格式提示"""
        selectors = [
            'xpath://div[contains(text(),"不支持的图片格式")]',
            'xpath://div[contains(text(),"只支持jpg")]',
            'xpath://div[contains(text(),"只支持 jpg")]',
            'xpath://div[contains(text(),"只支持png")]',
            'xpath://div[contains(text(),"只支持 png")]',
            'xpath://div[contains(text(),"只支持jpeg")]',
            'xpath://div[contains(text(),"只支持 jpeg")]',
        ]
        end_time = time.time() + timeout
        while time.time() < end_time:
            for selector in selectors:
                try:
                    ele = self.page.ele(selector, timeout=0.2)
                    if ele:
                        return True
                except Exception:
                    pass
            html = self._get_page_html()
            if (
                "不支持的图片格式" in html
                or "只支持jpg" in html
                or "只支持 jpg" in html
                or "只支持png" in html
                or "只支持 png" in html
                or "只支持jpeg" in html
                or "只支持 jpeg" in html
            ):
                return True
            time.sleep(0.1)
        return False

    def _find_cover_container_in_modal(self, modal: object, label: str, log: Callable[[str], None]) -> Optional[object]:
        """定位封面上传容器"""
        try:
            containers = modal.eles(
                'xpath:.//div[.//div[normalize-space(text())="上传封面"] and .//div[contains(@class,"semi-upload")]]',
                timeout=2
            ) or []
        except Exception:
            containers = []

        total = len(containers)
        for idx in range(total - 1, -1, -1):
            c = containers[idx]
            visible = self._is_visible(c)
            if visible:
                return c
        return None

    def _debug_describe_input(self, ele: object) -> str:
        """描述 input 关键属性"""
        try:
            accept = ele.attr("accept") or ""
        except Exception:
            accept = ""
        try:
            name = ele.attr("name") or ""
        except Exception:
            name = ""
        try:
            ele_id = ele.attr("id") or ""
        except Exception:
            ele_id = ""
        try:
            cls = ele.attr("class") or ""
        except Exception:
            cls = ""
        try:
            outer = (ele.attr("outerHTML") or "")[:150]
        except Exception:
            outer = ""
        try:
            js = (
                "const el = arguments[0];"
                "if (!el) return ['',''];"
                "const style = window.getComputedStyle(el);"
                "return [style.display, style.visibility];"
            )
            display, visibility = self.page.run_js(js, ele)
        except Exception:
            display = ""
            visibility = ""
        return (
            f"[input] accept={accept} name={name} id={ele_id} class={cls} "
            f"display={display} visibility={visibility} outer={outer}"
        )

    def _debug_dump_modal_file_inputs(self, modal: object, label: str, log: Callable[[str], None]) -> None:
        """打印弹窗内所有 file input"""
        if not self.debug:
            return
        try:
            js = (
                "const root = arguments[0];"
                "const arr = Array.from(root.querySelectorAll('input[type=\"file\"]'));"
                "return arr.map((el,i)=>({"
                "i,"
                "accept: el.getAttribute('accept')||'',"
                "name: el.getAttribute('name')||'',"
                "id: el.id||'',"
                "className: el.className||'',"
                "display: getComputedStyle(el).display,"
                "visibility: getComputedStyle(el).visibility,"
                "outer: (el.outerHTML||'').slice(0,200),"
                "}));"
            )
            inputs = self.page.run_js(js, modal) or []
        except Exception:
            inputs = []
        log(f"[modal-inputs] label={label} count={len(inputs)}")
        for item in inputs:
            log(
                f"[modal-inputs] label={label} index={item.get('i')} "
                f"accept={item.get('accept')} name={item.get('name')} id={item.get('id')} "
                f"class={item.get('className')} display={item.get('display')} "
                f"visibility={item.get('visibility')} outer={item.get('outer')}"
            )

    def _is_visible(self, ele: object) -> bool:
        """判断元素是否可见"""
        try:
            js = (
                "const el = arguments[0];"
                "if (!el) return false;"
                "const style = window.getComputedStyle(el);"
                "return el.offsetParent !== null && style.display !== 'none' && style.visibility !== 'hidden';"
            )
            return bool(self.page.run_js(js, ele))
        except Exception:
            try:
                style = (ele.attr("style") or "").lower()
                if "display: none" in style or "visibility: hidden" in style:
                    return False
            except Exception:
                pass
        return True

    def _click_modal_button_by_span(self, modal: object, text: str, log: Callable[[str], None]) -> bool:
        """通过 span 文案点击弹窗按钮"""
        for _ in range(10):
            try:
                btn = modal.ele(
                    f'xpath:.//button[.//span[contains(@class,"semi-button-content") and normalize-space(text())="{text}"]]',
                    timeout=1
                )
            except Exception:
                btn = None

            if not btn:
                try:
                    btn = modal.ele(
                        f'xpath:.//button[contains(.,"{text}")]',
                        timeout=1
                    )
                except Exception:
                    btn = None

            if not btn:
                time.sleep(0.5)
                continue

            try:
                if self._is_element_disabled(btn):
                    time.sleep(0.5)
                    continue
                btn.click()
                break
            except Exception:
                time.sleep(0.5)

        if text == "设置横封面":
            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    modal_html = modal.html if modal else ""
                except Exception:
                    modal_html = ""
                if "横封面" in modal_html:
                    return True
                time.sleep(0.5)
            return True

        if text == "完成":
            start_time = time.time()
            while time.time() - start_time < 5:
                if not self._get_cover_modal():
                    return True
                time.sleep(0.5)
            return True

        return True

    def _get_cover_modal(self) -> Optional[object]:
        """获取封面弹窗"""
        selectors = [
            'xpath://div[@role="dialog"][last()]',
            'xpath://div[contains(@class,"semi-modal")][last()]',
            'xpath://div[contains(@class,"Modal")][last()]',
            'xpath://div[.//input[@type="file"]][last()]',
        ]
        for selector in selectors:
            try:
                modal = self.page.ele(selector, timeout=1)
                if modal:
                    return modal
            except Exception:
                continue
        return None

    def _wait_for_upload_complete(self, timeout: int = 600) -> bool:
        """等待上传完成

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否完成
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查进度条是否消失或显示100%
                progress = self.page.ele('[class*="progress"]', timeout=1)
                if not progress:
                    # 进度条消失，可能已完成
                    # 检查是否有错误
                    error = self.page.ele('[class*="error"]', timeout=0.5)
                    if error and error.text:
                        return False
                    return True

                # 检查进度文本
                progress_text = progress.text if progress else ""
                if '100%' in progress_text or '完成' in progress_text:
                    return True

            except Exception:
                pass

            time.sleep(2)

        return False

    def _wait_title_and_desc_ready(self, timeout: int = 20) -> bool:
        """等待标题和描述区域就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                title_input = self.page.ele(
                    'css:div.semi-input-wrapper input.semi-input[type="text"][placeholder*="\u586b\u5199\u4f5c\u54c1\u6807\u9898"]',
                    timeout=1
                )
            except Exception:
                title_input = None
            if title_input and self._is_visible(title_input):
                try:
                    desc_editor = self.page.ele(
                        'css:div[data-slate-editor="true"][contenteditable="true"]',
                        timeout=1
                    )
                except Exception:
                    desc_editor = None
                if desc_editor:
                    try:
                        self.page.run_js(
                            "const el = arguments[0];"
                            "if (el) { el.scrollIntoView({block:'center'}); el.click(); }",
                            title_input,
                        )
                    except Exception:
                        try:
                            title_input.scroll.to()
                            title_input.click()
                        except Exception:
                            pass
                    return True
            time.sleep(0.5)
        return False
    def _fill_title(self, title: str) -> bool:
        """Fill"""
        log = getattr(self, "_title_log", None) or (lambda m: None)
        text = title[:30]
        selector = 'input.semi-input[type="text"][placeholder*="\u586b\u5199\u4f5c\u54c1\u6807\u9898"]'

        try:
            ok = bool(self._set_input_value_js(selector, text))
        except Exception:
            ok = False

        time.sleep(0.3)
        try:
            readback = self._read_input_value_js(selector)
        except Exception:
            readback = ""

        readback = self._sanitize_text(readback)
        target = self._sanitize_text(text)
        log(f'[title] set="{target}" readback="{readback}" ok={"Y" if ok and readback == target else "N"}')
        return ok and readback == target
    def _fill_description(self, description: str) -> bool:
        """Fill"""
        selector = '[contenteditable="true"][data-slate-editor="true"]'
        text = description[:500]
        try:
            js = (
                "const el = document.querySelector(arguments[0]);"
                "if (!el) return false;"
                "el.focus();"
                "el.innerText = '';"
                "el.dispatchEvent(new Event('input', { bubbles: true }));"
                "el.innerText = arguments[1];"
                "el.dispatchEvent(new Event('input', { bubbles: true }));"
                "el.dispatchEvent(new Event('change', { bubbles: true }));"
                "el.dispatchEvent(new Event('blur', { bubbles: true }));"
                "return true;"
            )
            ok = bool(self.page.run_js(js, selector, text))
        except Exception:
            ok = False

        log = getattr(self, "_title_log", None) or (lambda m: None)
        log(f"[desc] set_len={len(text)} ok={'Y' if ok else 'N'}")
        return ok

    def _sanitize_text(self, text: str) -> str:
        """??????????"""
        try:
            return re.sub(r"[\x00-\x1F\x7F]", "", text or "").strip()
        except Exception:
            return (text or "").strip()

    def _set_input_value_js(self, selector: str, value: str) -> bool:
        """?? JS ?? input ??????"""
        js = (
            "const el = document.querySelector(arguments[0]);"
            "if (!el) return false;"
            "el.focus();"
            "el.value = '';"
            "el.dispatchEvent(new Event('input', { bubbles: true }));"
            "el.dispatchEvent(new Event('change', { bubbles: true }));"
            "el.value = arguments[1];"
            "el.dispatchEvent(new Event('input', { bubbles: true }));"
            "el.dispatchEvent(new Event('change', { bubbles: true }));"
            "el.dispatchEvent(new Event('blur', { bubbles: true }));"
            "el.dispatchEvent(new CompositionEvent('compositionend', { data: arguments[1], bubbles: true }));"
            "return true;"
        )
        try:
            return bool(self.page.run_js(js, selector, value))
        except Exception:
            return False

    def _read_input_value_js(self, selector: str) -> str:
        """?? input.value"""
        js = "const el = document.querySelector(arguments[0]); return el ? (el.value || '') : '';"
        try:
            return self.page.run_js(js, selector) or ""
        except Exception:
            return ""
    def _ensure_title_persisted(self, title: str, log: Callable[[str], None]) -> None:
        """????????"""
        selector = 'input.semi-input[type="text"][placeholder*="\u586b\u5199\u4f5c\u54c1\u6807\u9898"]'
        target = self._sanitize_text(title[:30])
        try:
            readback = self._sanitize_text(self._read_input_value_js(selector))
        except Exception:
            readback = ""
        if readback != target:
            self._set_input_value_js(selector, target)
            try:
                readback2 = self._sanitize_text(self._read_input_value_js(selector))
            except Exception:
                readback2 = ""
            log(f'[title] repatch=Y readback="{readback2}" target="{target}"')

    def _open_category_dropdown(self, log: Callable[[str], None]) -> Optional[str]:
        """打开分类下拉入口"""
        selectors = [
            'css:div.semi-select.select-lJTtRL.semi-select-single',
            'xpath://div[contains(@class,"semi-select") and .//div[contains(@class,"select-dropdown-option-video")]]',
            'css:div.semi-select[tabindex="0"]',
        ]
        listbox_selector = 'css:div.semi-select-option-list[role="listbox"]'

        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=1)
            except Exception:
                ele = None
            if not ele:
                continue
            try:
                ele.scroll.to()
            except Exception:
                try:
                    self.page.run_js(
                        "const el = arguments[0]; if (el) el.scrollIntoView({block:'center'});",
                        ele,
                    )
                except Exception:
                    pass
            try:
                ele.click()
            except Exception:
                try:
                    self.page.run_js("const el = arguments[0]; if (el) el.click();", ele)
                except Exception:
                    pass
            try:
                listbox = self.page.ele(listbox_selector, timeout=2)
            except Exception:
                listbox = None
            if listbox:
                log(f"[category] dropdown_opened=Y selector={selector}")
                return selector
        log("[category] dropdown_opened=N")
        return None

    def _read_selected_category(self) -> str:
        """读取当前已选分类文本"""
        js = (
            "const a = document.querySelector('div.semi-select.select-lJTtRL .semi-select-selection-text');"
            "if (a && a.innerText) return a.innerText.trim();"
            "const b = document.querySelector('div.semi-select.select-lJTtRL div.select-dropdown-option-video');"
            "return b && b.innerText ? b.innerText.trim() : '';"
        )
        try:
            return (self.page.run_js(js) or "").strip()
        except Exception:
            return ""

    def _select_category(self, category_name: str, log: Callable[[str], None]) -> bool:
        """选择分类/领域"""
        if not category_name:
            return False
        listbox_selector = 'css:div.semi-select-option-list[role="listbox"]'
        option_xpath = (
            f'.//div[contains(@class,"semi-select-option") and '
            f'.//div[contains(@class,"select-dropdown-option-video") and normalize-space(text())="{category_name}"]]'
        )

        for attempt in range(1, 4):
            log(f"[category] attempt={attempt}")
            open_selector = self._open_category_dropdown(log)
            if not open_selector:
                log("[category] FAIL")
                continue
            log(f"[category] open_selector={open_selector}")

            try:
                listbox = self.page.ele(listbox_selector, timeout=2)
            except Exception:
                listbox = None
            if listbox:
                log("[category] listbox_found=Y")
            else:
                log("[category] listbox_found=N")
                continue

            time.sleep(0.2)

            option_clicked = False
            try:
                option_ele = listbox.ele(f'xpath:{option_xpath}', timeout=1)
            except Exception:
                option_ele = None
            if option_ele:
                try:
                    option_ele.scroll.to()
                except Exception:
                    try:
                        self.page.run_js(
                            "const el = arguments[0]; if (el) el.scrollIntoView({block:'center'});",
                            option_ele,
                        )
                    except Exception:
                        pass
                try:
                    option_ele.click()
                    option_clicked = True
                except Exception:
                    option_clicked = False
            else:
                try:
                    js = (
                        "const list = arguments[0];"
                        "const target = arguments[1];"
                        "if (!list) return false;"
                        "const items = Array.from(list.querySelectorAll('.semi-select-option'));"
                        "const hit = items.find(el => (el.innerText || '').includes(target));"
                        "if (!hit) return false;"
                        "hit.scrollIntoView({block:'center'});"
                        "hit.click();"
                        "return true;"
                    )
                    option_clicked = bool(self.page.run_js(js, listbox, category_name))
                except Exception:
                    option_clicked = False

            log(f"[category] option_click={'Y' if option_clicked else 'N'} option_text={category_name}")

            if not option_clicked:
                continue

            start_time = time.time()
            while time.time() - start_time < 5:
                selected = self._read_selected_category()
                try:
                    still_open = bool(self.page.ele(listbox_selector, timeout=0.5))
                except Exception:
                    still_open = False
                if (category_name in selected) or not still_open:
                    break
                time.sleep(0.2)

            selected = self._read_selected_category()
            log(f'[category] selected_readback="{selected}" target="{category_name}"')
            if category_name in selected:
                log("[category] SUCCESS")
                return True

        log("[category] FAIL")
        self._dump_dom_context(log, "category_select_failed")
        return False
    def _get_page_html(self) -> str:
        """获取HTML源码"""
        for attr in ("html", "source", "page_source"):
            try:
                html = getattr(self.page, attr)
                if html:
                    return html
            except Exception:
                continue
        return ""
    def _is_element_disabled(self, ele: object) -> bool:
        """判断元素是否禁用"""
        try:
            disabled = ele.attr('disabled')
            classes = (ele.attr('class') or '')
            if disabled:
                return True
            if 'disabled' in classes or 'is-disabled' in classes:
                return True
        except Exception:
            pass
        return False
    def _find_publish_button(self) -> Optional[object]:
        """查找发布按钮"""
        selectors = [
            'xpath://div[contains(@class,"content-confirm") or contains(@class,"confirm") or contains(@class,"footer") or contains(@class,"bottom") or contains(@class,"fixed")]//button[contains(.,"发布")]',
            'xpath://button[contains(.,"发布")]',
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=1)
                if ele:
                    return ele
            except Exception:
                pass
        return None
    def _wait_until_ready_to_publish(self, timeout: int = 1800, log: Optional[Callable[[str], None]] = None) -> bool:
        """等待可发布"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            btn = self._find_publish_button()
            publish_btn_found = btn is not None
            publish_btn_disabled = self._is_element_disabled(btn) if btn else True
            if publish_btn_found and not publish_btn_disabled:
                return True

            if log:
                log(
                    f"等待发布条件: 发布按钮={'已找到' if publish_btn_found else '未找到'} "
                    f"禁用={'是' if publish_btn_disabled else '否'}"
                )
            time.sleep(2)

        return False
    def _set_tag_and_text(self, tag: str, text: str) -> bool:
        """设置标签与输入内容"""
        ok = False
        # 标签输入
        tag_selectors = [
            'input[placeholder*="标签"]',
            'input[placeholder*="话题"]',
            '[class*="tag"] input',
        ]
        for selector in tag_selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.input(tag)
                    time.sleep(0.5)
                    ele.input('\n')
                    ok = True
                    break
            except Exception:
                pass

        # 兜底：点击“添加话题”，在编辑器输入话题
        if not ok:
            try:
                btn = self.page.ele('xpath://div[contains(text(),"添加话题")]', timeout=2)
                if btn:
                    btn.click()
                    time.sleep(0.5)
                    editor = self.page.ele('[contenteditable="true"]', timeout=2)
                    if editor:
                        editor.input(f"#{tag} ")
                        ok = True
            except Exception:
                pass

        # 额外输入栏（如位置/文本输入）
        text_selectors = [
            'input[placeholder*="输入"]',
            'input[placeholder*="地理"]',
            'input[placeholder*="位置"]',
        ]
        for selector in text_selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.input(text)
                    ok = True
                    break
            except Exception:
                pass
        return ok

    def _apply_publish_settings(self, settings: dict, log: Callable[[str], None]) -> bool:
        """应用发布设置"""
        try:
            visibility = settings.get("visibility", "private")
            download_permission = settings.get("download_permission", "allow")
            schedule = settings.get("schedule", {})
            schedule_enable = bool(schedule.get("enable", True))
            schedule_date = schedule.get("date", "")
            schedule_time = schedule.get("time", "")
            schedule_offset = int(schedule.get("offset_minutes", 1))
        except Exception:
            return False

        self._set_visibility(visibility, log)
        self._set_download_permission(download_permission, log)

        if schedule_enable:
            self._set_schedule_time(schedule_date, schedule_time, schedule_offset, log)
            target_dt = None
            if schedule_date and schedule_time:
                try:
                    target_dt = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
                except Exception:
                    target_dt = None
            if not target_dt:
                target_dt = datetime.now() + timedelta(minutes=schedule_offset)

            target_date = target_dt.strftime("%Y-%m-%d")
            target_time = target_dt.strftime("%H:%M")
            target_value = f"{target_date} {target_time}"

            try:
                js = (
                    "const el = document.querySelector('input.semi-input[placeholder*=\"日期和时间\"]');"
                    "return el ? (el.value || '').trim() : '';"
                )
                schedule_value = (self.page.run_js(js) or "").strip()
            except Exception:
                schedule_value = ""

            log(f'schedule_final="{schedule_value}"')
            if not schedule_value or " " not in schedule_value:
                log(f"schedule_set_failed readback={schedule_value} target={target_value}")
                return False
        else:
            immediate_selectors = [
                'xpath://label[contains(text(),"立即发布")]',
                'xpath://span[contains(text(),"立即发布")]',
                'xpath://div[contains(text(),"立即发布")]',
            ]

            def is_immediate_mode() -> bool:
                try:
                    input_ele = self.page.ele('css:input.semi-input[placeholder*="日期和时间"]', timeout=0.5)
                except Exception:
                    input_ele = None
                if not input_ele:
                    return True
                if not self._is_visible(input_ele):
                    return True
                try:
                    js = (
                        "const el = document.querySelector('input.semi-input[placeholder*=\"日期和时间\"]');"
                        "return el ? (el.value || '').trim() : '';"
                    )
                    value = (self.page.run_js(js) or "").strip()
                except Exception:
                    value = ""
                return value == ""

            ok = False
            for _ in range(3):
                for selector in immediate_selectors:
                    try:
                        ele = self.page.ele(selector, timeout=2)
                        if ele:
                            ele.click()
                            break
                    except Exception:
                        pass
                if is_immediate_mode():
                    ok = True
                    break
                time.sleep(0.2)
            if not ok:
                log("immediate_set_failed")
                return False

        return True
    def _set_visibility(self, visibility: str, log: Callable[[str], None]) -> None:
        """设置可见范围"""
        label_map = {
            "public": "公开",
            "friends": "好友可见",
            "private": "仅自己可见",
        }
        target = label_map.get(visibility, "仅自己可见")
        selectors = [
            f'xpath://label[contains(text(),"{target}")]',
            f'xpath://span[contains(text(),"{target}")]',
            f'xpath://div[contains(text(),"{target}")]',
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.click()
                    log(f"已设置可见范围: {target}")
                    return
            except Exception:
                pass
        log(f"未找到可见范围选项: {target}")
    def _set_download_permission(self, permission: str, log: Callable[[str], None]) -> None:
        """设置下载权限"""
        target = "允许" if permission == "allow" else "不允许"
        selectors = [
            f'xpath://label[contains(text(),"{target}")]',
            f'xpath://span[contains(text(),"{target}")]',
            f'xpath://div[contains(text(),"{target}")]',
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.click()
                    log(f"已设置下载权限: {target}")
                    return
            except Exception:
                pass
        log(f"未找到下载权限选项: {target}")
    def _get_active_datepicker_root(self) -> Optional[object]:
        """获取可用的日期选择器根节点"""
        try:
            roots = self.page.eles('css:div.semi-datepicker', timeout=2) or []
        except Exception:
            roots = []
        for root in roots:
            if not self._is_visible_loose(root):
                continue
            try:
                grid = root.ele('css:div.semi-datepicker-month-grid-left', timeout=0.5)
            except Exception:
                grid = None
            if not grid:
                continue
            try:
                day = root.ele('css:div.semi-datepicker-day[title]', timeout=0.5)
            except Exception:
                day = None
            if day:
                return root
        return None

    def _read_schedule_input_value(self) -> str:
        """读取定时发布时间输入框的值"""
        try:
            js = (
                "const el = document.querySelector('input.semi-input[placeholder*=\"日期和时间\"]');"
                "return el ? (el.value || '').trim() : '';"
            )
            return (self.page.run_js(js) or "").strip()
        except Exception:
            return ""
    def _is_visible_loose(self, ele: object) -> bool:
        """更宽松的可见判断（适配 position: fixed 的面板）"""
        try:
            js = (
                "const el = arguments[0];"
                "if (!el) return false;"
                "const style = window.getComputedStyle(el);"
                "if (style.display === 'none' || style.visibility === 'hidden') return false;"
                "const r = el.getBoundingClientRect();"
                "return r && r.width > 0 && r.height > 0;"
            )
            return bool(self.page.run_js(js, ele))
        except Exception:
            return False
    def _open_schedule_picker(self, log: Callable[[str], None]) -> bool:
        """打开日期/时间选择面板"""
        opened = False
        try:
            input_ele = self.page.ele('css:input.semi-input[placeholder*="日期和时间"]', timeout=2)
        except Exception:
            input_ele = None
        if input_ele:
            try:
                input_ele.click()
            except Exception:
                pass

        suffix_selectors = [
            'css:.semi-input-suffix .semi-icons-calendar_clock',
            'css:.semi-input-suffix',
            'xpath://div[contains(@class,"semi-input-suffix")]//svg[contains(@class,"calendar")]',
        ]
        for selector in suffix_selectors:
            try:
                ele = self.page.ele(selector, timeout=1)
            except Exception:
                ele = None
            if ele:
                try:
                    ele.click()
                    opened = True
                    break
                except Exception:
                    pass

        if not opened:
            try:
                js = (
                    "const icon = document.querySelector('.semi-input-suffix');"
                    "if (icon) { icon.click(); return true; }"
                    "return false;"
                )
                opened = bool(self.page.run_js(js))
            except Exception:
                opened = False

        log(f"[schedule] picker_opened={'Y' if opened else 'N'}")
        return opened
    def _click_time_item(self, root: Optional[object], value: str) -> bool:
        """Click a time item in the time picker panel by exact text."""
        js = (
            "const root = arguments[0] || document;"
            "const value = arguments[1];"
            "const panels = Array.from(root.querySelectorAll('[class*=\"timepicker\"], [class*=\"datepicker-time\"], [class*=\"time-panel\"]'));"
            "const scopes = panels.length ? panels : [root];"
            "const isVisible = (el) => {"
            "  if (!el) return false;"
            "  const r = el.getBoundingClientRect();"
            "  return r && r.width > 0 && r.height > 0;"
            "};"
            "for (const scope of scopes) {"
            "  const items = Array.from(scope.querySelectorAll('li, div, span, button'));"
            "  for (const el of items) {"
            "    const text = (el.innerText || '').trim();"
            "    if (!text) continue;"
            "    if (text === value) {"
            "      const cls = (el.className || '');"
            "      if (cls.includes('disabled')) continue;"
            "      if (!isVisible(el)) continue;"
            "      try { el.scrollIntoView({block:'center'}); } catch (e) {}"
            "      el.click();"
            "      return true;"
            "    }"
            "  }"
            "}"
            "return false;"
        )
        try:
            return bool(self.page.run_js(js, root, value))
        except Exception:
            return False
    def _select_time_in_timepicker(self, root: Optional[object], target_time: str, log: Callable[[str], None]) -> bool:
        """Select hour/minute in time picker panel."""
        try:
            hour, minute = target_time.split(":")
        except Exception:
            return False
        ok_hour = self._click_time_item(root, hour)
        ok_minute = self._click_time_item(root, minute)
        log(f"[schedule] time_click hour={'Y' if ok_hour else 'N'} minute={'Y' if ok_minute else 'N'}")
        return ok_hour and ok_minute
    def _set_schedule_input_value(self, value: str) -> bool:
        """Set schedule input via JS and fire events."""
        js = (
            "const el = document.querySelector('input.semi-input[placeholder*=\"日期和时间\"]');"
            "if (!el) return false;"
            "el.focus();"
            "el.value = arguments[0];"
            "el.dispatchEvent(new Event('input', { bubbles: true }));"
            "el.dispatchEvent(new Event('change', { bubbles: true }));"
            "el.dispatchEvent(new Event('blur', { bubbles: true }));"
            "return true;"
        )
        try:
            return bool(self.page.run_js(js, value))
        except Exception:
            return False
    def _set_schedule_time(self, schedule_date: str, schedule_time: str, offset_minutes: int, log: Callable[[str], None]) -> None:
        """设置定时发布（仅写入 input 值）"""

        # 1) 选中“定时发布”
        selectors = [
            'xpath://label[contains(text(),"定时发布")]',
            'xpath://span[contains(text(),"定时发布")]',
            'xpath://div[contains(text(),"定时发布")]',
        ]
        clicked = False
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.click()
                    clicked = True
                    break
            except Exception:
                pass

        if not clicked:
            log("未找到定时发布入口，降级为立即发布")
            self._set_immediate_publish(log)
            return

        # 2) 计算目标时间（字符串）
        target_dt = None
        if schedule_date and schedule_time:
            try:
                target_dt = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
            except Exception:
                target_dt = None
        if not target_dt:
            target_dt = datetime.now() + timedelta(minutes=offset_minutes)

        target_date = target_dt.strftime("%Y-%m-%d")
        target_time = target_dt.strftime("%H:%M")
        target_value = f"{target_date} {target_time}"
        # 3) 直接写入 input
        ok_set = self._set_schedule_input_value(target_value)
        log(f'schedule_direct_set={"Y" if ok_set else "N"} target="{target_value}"')
        return
    def _set_immediate_publish(self, log: Callable[[str], None]) -> None:
        """设置立即发布"""
        selectors = [
            'xpath://label[contains(text(),"立即发布")]',
            'xpath://span[contains(text(),"立即发布")]',
            'xpath://div[contains(text(),"立即发布")]',
        ]
        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.click()
                    log("已设置立即发布")
                    return
            except Exception:
                pass
        log("未找到立即发布选项")
    def _dump_dom_context(self, log: Callable[[str], None], reason: str) -> None:
        """输出页面DOM关键片段，便于定位问题"""
        if not self.debug:
            return
        try:
            url = self.page.url
        except Exception:
            url = ""
        log(f"[DOM] reason={reason} url={url}")

        html = ""
        for attr in ("html", "source", "page_source"):
            try:
                html = getattr(self.page, attr)
                if html:
                    break
            except Exception:
                continue

        if not html:
            log("[DOM] empty html")
            return

        keywords = ["上传视频", "高清发布", "发布", "选择封面"]
        for kw in keywords:
            idx = html.find(kw)
            if idx != -1:
                start = max(idx - 200, 0)
                end = min(idx + 200, len(html))
                snippet = html[start:end].replace("\n", " ").replace("\r", " ")
                log(f"[DOM] snippet({kw}): {snippet}")

    def _add_tags(self, tags: List[str]) -> None:
        """添加标签"""
        # 查找标签输入区域
        selectors = [
            '[class*="tag"] input',
            'input[placeholder*="标签"]',
            'input[placeholder*="话题"]',
        ]

        for tag in tags[:5]:  # 限制标签数量
            for selector in selectors:
                try:
                    ele = self.page.ele(selector, timeout=1)
                    if ele:
                        # 输入标签
                        tag_text = f"#{tag}" if not tag.startswith('#') else tag
                        ele.input(tag_text)
                        time.sleep(0.5)
                        # 按回车确认
                        ele.input('\n')
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

    def _click_publish(self, log: Callable[[str], None]) -> bool:
        """点击发布按钮"""
        btn = self._find_publish_button()
        if not btn:
            log("未找到发布按钮")
            return False
        if self._is_element_disabled(btn):
            log("发布按钮不可点击")
            return False
        try:
            btn.click()
            return True
        except Exception:
            return False
    def _wait_for_publish_complete(self, timeout: int = 60) -> bool:
        """等待发布完成

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否完成
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查成功提示
                success_selectors = [
                    ':contains("发布成功")',
                    ':contains("已发布")',
                    '[class*="success"]',
                ]
                for selector in success_selectors:
                    ele = self.page.ele(selector, timeout=1)
                    if ele:
                        return True

                # 检查是否跳转到作品列表
                if 'content/manage' in self.page.url:
                    return True

            except Exception:
                pass

            time.sleep(2)

        return False

    def batch_upload(
        self,
        videos: List[ExportedVideo],
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        delay_between: int = 60
    ) -> List[ExportedVideo]:
        """批量上传视频

        Args:
            videos: 视频列表
            on_log: 日志回调
            on_progress: 进度回调
            delay_between: 每个视频之间的延迟(秒)

        Returns:
            上传成功的视频列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)

        uploaded = []
        total = len(videos)

        for i, video in enumerate(videos):
            log(f"\n[{i+1}/{total}] 上传视频: {video.title or video.video_id}")

            if on_progress:
                on_progress(f"上传 {i+1}/{total}", i+1, total)

            success = self.upload_video(video, on_log)
            if success:
                uploaded.append(video)
                log(f"  成功")
            else:
                log(f"  失败")

            # 延迟，避免频繁操作
            if i < total - 1 and delay_between > 0:
                log(f"等待 {delay_between} 秒...")
                time.sleep(delay_between)

        log(f"\n上传完成: {len(uploaded)}/{total}")
        return uploaded
