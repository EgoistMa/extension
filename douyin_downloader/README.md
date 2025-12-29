# 抖音视频下载器

基于浏览器插件逻辑实现的 Python 版抖音视频下载工具。

## 安装

```bash
cd douyin_downloader
pip install -r requirements.txt
```

## 使用方法

### 命令行

```bash
# 使用视频 URL 下载
python douyin_downloader.py https://www.douyin.com/video/7123456789012345678

# 使用短链接下载
python douyin_downloader.py https://v.douyin.com/xxxxx

# 直接使用视频 ID
python douyin_downloader.py 7123456789012345678

# 指定输出文件名
python douyin_downloader.py <url> -o my_video.mp4

# 使用 Cookie（提高成功率）
python douyin_downloader.py <url> --cookie "your_cookie_here"

# 从文件读取 Cookie
python douyin_downloader.py <url> --cookie-file cookie.txt
```

### 作为模块使用

```python
from douyin_downloader import DouyinDownloader

# 创建下载器
downloader = DouyinDownloader(cookie="可选的cookie")

# 下载视频
output_file = downloader.download("https://www.douyin.com/video/7123456789012345678")
print(f"下载完成: {output_file}")
```

## API 说明

该工具使用抖音 Web API:

- **视频详情接口**: `https://www.douyin.com/aweme/v1/web/aweme/detail/`
- **视频 URL**: 从 `video.play_addr.url_list` 或 `video.bit_rate[].play_addr.url_list` 获取

## 注意事项

1. **Cookie**: 某些视频可能需要登录后的 Cookie 才能下载，可以从浏览器开发者工具中获取
2. **频率限制**: 请勿频繁请求，以免被限制
3. **仅供学习**: 请尊重版权，仅下载有权限的内容

## 获取 Cookie

1. 打开浏览器访问 https://www.douyin.com
2. 登录账号
3. 按 F12 打开开发者工具
4. 切换到 Network 标签
5. 刷新页面，点击任意请求
6. 在 Headers 中找到 Cookie 字段并复制

## 许可证

MIT License
