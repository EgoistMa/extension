# 抖音自动化营销工具 - 项目规范文档

> 此文档供 Claude 参考，记录项目的核心流程、模块架构和开发约定。

## 一、项目概述

这是一个端到端的抖音视频营销自动化工具，实现从百应选品到抖音发布的完整工作流。

**核心理念：一键处理全部流程**

**开发重点：GUI 优先**
- 项目以图形界面 (GUI) 为主要交互方式
- CLI 仅作为辅助，开发时可暂不考虑
- 所有新功能优先在 GUI 中实现

## 二、工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              完整工作流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│   │ 百应模块 │ -> │ 素材下载 │ -> │ 抖音搜索 │ -> │ 剪映剪辑 │ -> │ 抖音上传 │  │
│   │         │    │         │    │ & 下载   │    │ & 导出   │    │ & 发布   │  │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       ↓              ↓              ↓              ↓              ↓         │
│   Checkpoint     Checkpoint     Checkpoint     Checkpoint     Checkpoint   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 详细步骤

| 步骤 | 模块 | 功能描述 | Checkpoint |
|------|------|----------|------------|
| 1 | 百应模块 | 在百应中找到合适的 N 个产品 | PRODUCT_FOUND |
| 2 | 百应模块 | 分别进入每个产品下载素材 | MATERIAL_DOWNLOADED |
| 3 | 抖音模块 | 搜索下载合适的视频素材 | VIDEO_DOWNLOADED |
| 4 | 剪映模块 | 自动剪辑生成视频 | JIANYING_GENERATED |
| 5 | 剪映模块 | 导出视频 | EXPORTED |
| 6 | 抖音创作者模块 | 上传视频并发布 | PUBLISHED |

## 三、模块架构

### 3.1 百应模块 (`platforms/baiying/`)

| 文件 | 类 | 功能 |
|------|-----|------|
| parser.py | ProductParser | 解析产品信息、图片、视频 |
| picker.py | BaiyingPicker | 智能选品、筛选产品 |
| downloader.py | MaterialDownloader | 并发下载产品素材 |

**浏览器控制**：需要支持有头/无头模式

### 3.2 抖音视频模块 (`platforms/douyin/`)

| 文件 | 类 | 功能 |
|------|-----|------|
| searcher.py | DouyinSearcher | 搜索、筛选视频 |
| downloader.py | VideoDownloader | 批量下载视频 |
| uploader.py | DouyinUploader | 上传到创作者中心 |

**浏览器控制**：需要支持有头/无头模式

### 3.3 剪映模块 (`platforms/jianying/`)

| 文件 | 类 | 功能 |
|------|-----|------|
| generator.py | JianyingGenerator | 基于模板生成剪映项目 |
| exporter.py | JianyingExporter | 导出视频 |

### 3.4 工作流模块 (`workflow/`)

| 文件 | 类 | 功能 |
|------|-----|------|
| pipeline.py | Pipeline | 编排完整流程，管理 7 个步骤 |
| task.py | Task | 单个任务定义 |
| checkpoint.py | Checkpoint | 断点续传机制 |

## 四、开发模式约定

### 4.1 Checkpoint 机制

- 每个模块完成后自动保存 Checkpoint
- 支持从任意 Checkpoint 恢复
- 项目状态存储在 `data/checkpoints/{project_id}.json`

### 4.2 进度显示

**总体进度**：基于完成的步骤数 / 总步骤数 (7步)

**每个模块进度**：
- 百应选品：已处理产品数 / 目标产品数
- 素材下载：已下载素材数 / 总素材数
- 视频搜索：搜索进度 (滚动次数)
- 视频下载：已下载视频数 / 目标视频数
- 剪映剪辑：生成进度
- 视频导出：导出进度
- 抖音上传：上传进度

### 4.3 浏览器模式控制

**每个涉及浏览器的模块都需要支持：**
- `headless=True`: 无头模式（后台运行）
- `headless=False`: 有头模式（可见浏览器窗口）

**各模块可独立控制**，配置示例：
```python
{
    "browser": {
        "baiying_headless": False,      # 百应模块
        "douyin_headless": False,       # 抖音搜索/下载
        "douyin_creator_headless": False # 抖音上传
    }
}
```

### 4.4 多账户支持

- 用户可选择一个或多个账户
- 每个账户有独立的浏览器 Profile
- 支持账户级别的并行处理（TODO）

## 五、状态流转

```
PENDING
    ↓
PRODUCT_SEARCHING → PRODUCT_FOUND
    ↓
MATERIAL_DOWNLOADING → MATERIAL_DOWNLOADED
    ↓
VIDEO_SEARCHING → VIDEO_FILTERED → VIDEO_DOWNLOADING → VIDEO_DOWNLOADED
    ↓
JIANYING_GENERATING → JIANYING_GENERATED
    ↓
EXPORTING → EXPORTED
    ↓
UPLOADING → PUBLISHED
    ↓
COMPLETED
```

**失败状态**：任何步骤失败 → FAILED（可从 Checkpoint 恢复）

## 六、确认的需求规范

| 功能点 | 规范 |
|--------|------|
| 选品方式 | **自动智能选品** - 程序自动在百应中根据条件筛选产品 |
| 产品数量 | **N个产品各1个视频** - 批量处理，每个产品生成1个视频 |
| 浏览器模式 | **UI界面开关** - 每个模块可独立控制有头/无头模式 |

## 七、功能完成状态

> 已完成功能：

- [x] 百应智能选品（自动筛选 N 个产品）
- [x] 多产品批量处理
- [x] 素材下载（图片+视频）
- [x] 抖音视频搜索与下载
- [x] 剪映项目生成
- [x] 剪映自动导出
- [x] 抖音上传发布
- [x] 完整流程串联（选品→素材→搜索→剪映→上传）
- [x] 模块级进度显示
- [x] 滚动次数可配置

> 待开发功能：

- [ ] 浏览器有头/无头模式独立控制（UI开关）
- [ ] 多账户并行处理
- [ ] AI 文案生成（豆包集成）
- [ ] 断点续传优化

## 八、关键文件路径

```
douyin-automation/
├── src/
│   ├── main.py                 # CLI 入口 (辅助)
│   ├── workflow/
│   │   ├── pipeline.py         # 核心流程编排
│   │   └── checkpoint.py       # 断点续传
│   ├── platforms/
│   │   ├── baiying/            # 百应模块
│   │   ├── douyin/             # 抖音模块
│   │   └── jianying/           # 剪映模块
│   ├── core/
│   │   ├── browser_manager.py  # 浏览器管理
│   │   └── account_manager.py  # 账户管理
│   ├── models/
│   │   ├── project.py          # 项目状态
│   │   ├── product.py          # 产品模型
│   │   └── video.py            # 视频模型
│   └── ui/
│       └── main_window.py      # GUI 界面 (主要)
├── config/
│   └── settings.json           # 配置文件
└── data/
    ├── accounts/               # 账户数据
    └── checkpoints/            # 断点数据
```

---

**最后更新**: 2026-01-07

**说明**: 此文档会随项目进展更新，Claude 在处理项目相关任务时应参考此文档。
