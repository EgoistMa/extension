"""剪映项目生成器

基于模板创建新的剪映项目，替换视频素材
"""

import os
import json
import re
import shutil
import uuid
import subprocess
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable

from core.config import Config
from models.video import Video


class JianyingGenerator:
    """剪映项目生成器"""

    def __init__(
        self,
        template_path: str,
        output_dir: Optional[str] = None,
        config: Optional[Config] = None
    ):
        """初始化生成器

        Args:
            template_path: 模板项目路径
            output_dir: 输出目录，默认为剪映草稿目录
            config: 配置对象
        """
        self.template_path = Path(template_path)
        self.config = config or Config()

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(self.config.get('jianying.draft_dir', '')) or self._get_default_drafts_dir()

        if not self.template_path.exists():
            raise FileNotFoundError(f"模板路径不存在: {template_path}")

        self.template_content = self._load_template()

    def _get_default_drafts_dir(self) -> Path:
        """获取剪映默认草稿目录"""
        possible_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
            Path.home() / "Documents" / "JianyingPro Drafts",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return possible_paths[0]

    def _load_template(self) -> dict:
        """加载模板内容"""
        content_file = self.template_path / "draft_content.json"
        if not content_file.exists():
            raise FileNotFoundError(f"找不到模板文件: {content_file}")

        with open(content_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generate_uuid(self) -> str:
        """生成剪映格式的UUID"""
        return str(uuid.uuid4()).upper()

    def _get_video_info(self, video_path: str) -> dict:
        """获取视频信息"""
        video_path = Path(video_path)
        if not video_path.exists():
            return {'duration_us': 30000000, 'duration_ns': 30000000000, 'width': 1080, 'height': 1920}

        # 方法1: 使用ffprobe
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info.get('format', {}).get('duration', 0))
                if duration > 0:
                    width, height = 1080, 1920
                    for stream in info.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            width = stream.get('width', 1080)
                            height = stream.get('height', 1920)
                            break
                    return {
                        'duration_us': int(duration * 1000000),
                        'duration_ns': int(duration * 1000000000),
                        'width': width,
                        'height': height
                    }
        except Exception:
            pass

        # 方法2: 使用ffmpeg解析时长（兼容缺少ffprobe的环境）
        try:
            cmd = ['ffmpeg', '-i', str(video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            text = result.stderr or result.stdout
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', text)
            if duration_match:
                hours = float(duration_match.group(1))
                minutes = float(duration_match.group(2))
                seconds = float(duration_match.group(3))
                duration = hours * 3600 + minutes * 60 + seconds
                if duration > 0:
                    return {
                        'duration_us': int(duration * 1000000),
                        'duration_ns': int(duration * 1000000000),
                        'width': 1080,
                        'height': 1920
                    }
        except Exception:
            pass

        # 方法3: Windows MediaPlayer 读取时长（无需ffprobe/ffmpeg）
        if os.name == 'nt':
            try:
                safe_uri = video_path.absolute().as_uri().replace("'", "''")
                cmd = [
                    'powershell', '-NoProfile', '-Sta', '-Command',
                    f"$uri='{safe_uri}';"
                    "Add-Type -AssemblyName PresentationCore;"
                    "$player=New-Object System.Windows.Media.MediaPlayer;"
                    "$player.Open([Uri]$uri);"
                    "for ($i=0; $i -lt 20 -and -not $player.NaturalDuration.HasTimeSpan; $i++) {"
                    "Start-Sleep -Milliseconds 100;"
                    "}"
                    "$duration=$player.NaturalDuration.TimeSpan.TotalSeconds;"
                    "$player.Close();"
                    "Write-Output $duration;"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    text = (result.stdout or "").strip()
                    if text:
                        duration = float(text)
                        if duration > 0:
                            return {
                                'duration_us': int(duration * 1000000),
                                'duration_ns': int(duration * 1000000000),
                                'width': 1080,
                                'height': 1920
                            }
            except Exception:
                pass

        # 默认值
        return {'duration_us': 30000000, 'duration_ns': 30000000000, 'width': 1080, 'height': 1920}

    def _create_video_material(self, video_path: str, video_info: dict) -> dict:
        """创建视频素材对象"""
        material_id = self._generate_uuid()
        video_path = str(Path(video_path).absolute())

        return {
            "aigc_type": "none",
            "audio_fade": None,
            "cartoon_path": "",
            "category_id": "",
            "category_name": "",
            "check_flag": 63487,
            "crop": {
                "lower_left_x": 0.0, "lower_left_y": 1.0,
                "lower_right_x": 1.0, "lower_right_y": 1.0,
                "upper_left_x": 0.0, "upper_left_y": 0.0,
                "upper_right_x": 1.0, "upper_right_y": 0.0
            },
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": video_info['duration_ns'],
            "extra_type_option": 0,
            "formula_id": "",
            "freeze": None,
            "has_audio": True,
            "height": video_info['height'],
            "id": material_id,
            "intensifies_audio_path": "",
            "intensifies_path": "",
            "is_ai_generate_content": False,
            "is_copyright": False,
            "is_text_edit_overdub": False,
            "is_unified_beauty_mode": False,
            "local_id": "",
            "local_material_id": "",
            "material_id": "",
            "material_name": Path(video_path).name,
            "material_url": "",
            "matting": {
                "flag": 0, "has_use_quick_brush": False,
                "has_use_quick_eraser": False, "interactiveTime": [],
                "path": "", "strokes": []
            },
            "media_path": "",
            "object_locked": None,
            "origin_material_id": "",
            "path": video_path,
            "picture_from": "none",
            "picture_set_category_id": "",
            "picture_set_category_name": "",
            "request_id": "",
            "reverse_intensifies_path": "",
            "reverse_path": "",
            "smart_motion": None,
            "source": 0,
            "source_platform": 0,
            "stable": {
                "matrix_path": "",
                "stable_level": 0,
                "time_range": {"duration": 0, "start": 0}
            },
            "team_id": "",
            "type": "video",
            "video_algorithm": {
                "algorithms": [], "complement_frame_config": None,
                "deflicker": None, "gameplay_configs": [],
                "motion_blur_config": None, "noise_reduction": None,
                "path": "", "quality_enhance": None, "time_range": None
            },
            "width": video_info['width']
        }

    def _create_speed_material(self, speed: float) -> dict:
        """创建速度材料对象"""
        return {
            "curve_speed": None,
            "id": self._generate_uuid(),
            "mode": 0,
            "speed": speed,
            "type": "speed"
        }

    def _create_photo_material(self, image_path: str, width: int, height: int, duration_us: int) -> dict:
        """创建照片素材对象（存入 materials.videos，type=photo）"""
        material_id = self._generate_uuid()
        image_path = str(Path(image_path).absolute())

        return {
            "aigc_type": "none",
            "audio_fade": None,
            "cartoon_path": "",
            "category_id": "",
            "category_name": "",
            "check_flag": 63487,
            "crop": {
                "lower_left_x": 0.0, "lower_left_y": 1.0,
                "lower_right_x": 1.0, "lower_right_y": 1.0,
                "upper_left_x": 0.0, "upper_left_y": 0.0,
                "upper_right_x": 1.0, "upper_right_y": 0.0
            },
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": duration_us * 1000,
            "extra_type_option": 0,
            "formula_id": "",
            "height": height,
            "id": material_id,
            "intensifies_audio_path": "",
            "intensifies_path": "",
            "is_ai_generate_content": False,
            "is_copyright": False,
            "is_text_edit_overdub": False,
            "is_unified_beauty_mode": False,
            "local_id": "",
            "local_material_id": "",
            "material_id": "",
            "material_name": Path(image_path).name,
            "material_url": "",
            "matting": {
                "flag": 0, "has_use_quick_brush": False,
                "has_use_quick_eraser": False, "interactiveTime": [],
                "path": "", "strokes": []
            },
            "media_path": "",
            "object_locked": None,
            "origin_material_id": "",
            "path": image_path,
            "picture_from": "none",
            "picture_set_category_id": "",
            "picture_set_category_name": "",
            "request_id": "",
            "reverse_intensifies_path": "",
            "reverse_path": "",
            "smart_motion": None,
            "source": 0,
            "source_platform": 0,
            "stable": {
                "matrix_path": "",
                "stable_level": 0,
                "time_range": {"duration": 0, "start": 0}
            },
            "team_id": "",
            "type": "photo",
            "video_algorithm": {
                "algorithms": [], "complement_frame_config": None,
                "deflicker": None, "gameplay_configs": [],
                "motion_blur_config": None, "noise_reduction": None,
                "path": "", "quality_enhance": None, "time_range": None
            },
            "width": width
        }

    def _clone_segment(
        self,
        template: dict,
        material_id: str,
        start_time: int,
        duration: int,
        render_index: int
    ) -> dict:
        """克隆时间轴片段并替换关键字段"""
        segment = json.loads(json.dumps(template))
        segment["id"] = self._generate_uuid()
        segment["material_id"] = material_id
        segment["render_index"] = render_index
        if not isinstance(segment.get("source_timerange"), dict):
            segment["source_timerange"] = {"start": 0, "duration": duration}
        else:
            segment["source_timerange"]["start"] = 0
            segment["source_timerange"]["duration"] = duration
        if not isinstance(segment.get("target_timerange"), dict):
            segment["target_timerange"] = {"start": start_time, "duration": duration}
        else:
            segment["target_timerange"]["start"] = start_time
            segment["target_timerange"]["duration"] = duration
        segment["speed"] = 1.0
        return segment

    def _create_segment(
        self,
        material_id: str,
        start_time: int,
        source_duration: int,
        target_duration: int,
        speed: float = 1.0,
        speed_material_id: str = None,
        render_index: int = 0
    ) -> dict:
        """创建时间轴片段"""
        segment_id = self._generate_uuid()
        extra_refs = [speed_material_id] if speed_material_id else []

        return {
            "caption_info": None,
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "transform": {"x": 0.0, "y": 0.0}
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": extra_refs,
            "group_id": "",
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "id": segment_id,
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": material_id,
            "render_index": render_index,
            "responsive_layout": {
                "enable": False, "horizontal_pos_layout": 0,
                "size_layout": 0, "target_follow": "",
                "vertical_pos_layout": 0
            },
            "reverse": False,
            "source_timerange": {"duration": source_duration, "start": 0},
            "speed": speed,
            "target_timerange": {"duration": target_duration, "start": start_time},
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {"on": True, "value": 1.0},
            "visible": True,
            "volume": 1.0
        }

    def _get_template_duration(self) -> int:
        """获取模板时长(微秒)"""
        config = self.template_content.get('config', {})
        export_range = config.get('export_range', {})
        export_duration = export_range.get('duration', 0)
        if export_duration > 0:
            return export_duration
        return self.template_content.get('duration', 0)

    def _kill_jianying(self) -> None:
        """关闭剪映进程"""
        import time
        try:
            if os.name == 'nt':
                # 尝试关闭剪映相关进程
                for proc_name in ['JianyingPro.exe', 'JianyingPro', 'CapCut.exe']:
                    subprocess.run(['taskkill', '/F', '/IM', proc_name],
                                 capture_output=True, timeout=10)
                time.sleep(3)  # 等待进程完全退出和文件句柄释放
        except Exception:
            pass

    def generate_project(
        self,
        video_files: List[str],
        project_name: str,
        use_template_duration: bool = True,
        image_files: Optional[List[str]] = None,
        video_duration_overrides: Optional[dict] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> str:
        """生成剪映项目

        Args:
            video_files: 视频文件路径列表
            project_name: 项目名称
            use_template_duration: 是否使用模板时长
            on_log: 日志回调

        Returns:
            项目路径
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        if not video_files:
            raise ValueError("视频文件列表不能为空")

        # 关闭剪映以避免文件锁定
        self._kill_jianying()

        def get_video_info(video_path: str) -> dict:
            if video_duration_overrides:
                key = str(Path(video_path).absolute())
                override = video_duration_overrides.get(key)
                if override and override > 0:
                    return {
                        'duration_us': int(override * 1000000),
                        'duration_ns': int(override * 1000000000),
                        'width': 1080,
                        'height': 1920
                    }
            return self._get_video_info(video_path)

        # 创建项目目录 - 如果已存在则先删除
        project_dir = self.output_dir / project_name
        if project_dir.exists():
            import time as time_mod
            shutil.rmtree(project_dir)
            time_mod.sleep(1)  # 等待文件系统释放
        project_dir.mkdir(parents=True, exist_ok=True)

        # 复制模板文件
        for item in self.template_path.iterdir():
            if item.name == 'draft_content.json':
                continue
            dst = project_dir / item.name
            if item.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)

        # 深拷贝模板内容
        content = json.loads(json.dumps(self.template_content))
        content['id'] = self._generate_uuid()

        # 获取模板时长
        template_duration_us = self._get_template_duration()
        log(f"模板时长: {template_duration_us / 1000000:.1f}秒")

        # 清空素材
        content['materials']['videos'] = []

        # 获取或创建主轨道
        if content.get('tracks') and len(content['tracks']) > 0:
            main_track = content['tracks'][0]
            main_track['segments'] = []
        else:
            main_track = {
                "attribute": 0, "flag": 0,
                "id": self._generate_uuid(),
                "is_default_name": True, "name": "",
                "segments": [], "type": "video"
            }
            content['tracks'] = [main_track]

        # 生成视频+图片时间线
        if image_files:
            if len(video_files) > 1:
                log("检测到多个视频素材，仅使用第一个视频作为开头")
            video_path = video_files[0]
            video_info = get_video_info(video_path)
            video_duration_us = video_info['duration_us']
            material = self._create_video_material(video_path, video_info)
            content['materials']['videos'].append(material)

            video_segment = self._create_segment(
                material_id=material['id'],
                start_time=0,
                source_duration=video_duration_us,
                target_duration=video_duration_us,
                speed=1.0,
                speed_material_id=None,
                render_index=0
            )
            main_track['segments'].append(video_segment)

            current_time = video_duration_us
            remaining_us = max(template_duration_us - current_time, 0)

            try:
                from PIL import Image
            except Exception:
                Image = None

            images_cycle = list(image_files)
            if not images_cycle:
                log("未提供图片素材，跳过图片填充")
            else:
                image_idx = 0
                while remaining_us > 0:
                    img_path = Path(images_cycle[image_idx % len(images_cycle)]).absolute()
                    image_idx += 1
                    if not img_path.exists():
                        continue

                    width, height = 1080, 1920
                    if Image:
                        try:
                            with Image.open(img_path) as im:
                                width, height = im.size
                        except Exception:
                            pass

                    duration_sec = random.randint(10, 20)
                    duration_us = duration_sec * 1_000_000
                    if duration_us > remaining_us:
                        duration_us = remaining_us

                    image_material = self._create_photo_material(str(img_path), width, height, duration_us)
                    content['materials']['videos'].append(image_material)

                    image_segment = self._create_segment(
                        material_id=image_material['id'],
                        start_time=current_time,
                        source_duration=duration_us,
                        target_duration=duration_us,
                        speed=1.0,
                        speed_material_id=None,
                        render_index=len(main_track['segments'])
                    )
                    main_track['segments'].append(image_segment)

                    current_time += duration_us
                    remaining_us -= duration_us
        else:
            # 第一遍: 获取视频信息
            video_infos = []
            total_original_duration_us = 0
            for video_path in video_files:
                video_info = get_video_info(video_path)
                video_infos.append({
                    'path': video_path,
                    'info': video_info,
                    'duration_us': video_info['duration_us']
                })
                total_original_duration_us += video_info['duration_us']

            log(f"视频总时长: {total_original_duration_us / 1000000:.1f}秒")

            # 计算变速
            if use_template_duration and template_duration_us > 0:
                global_speed = total_original_duration_us / template_duration_us
            else:
                global_speed = 1.0
            global_speed = max(0.1, min(100.0, global_speed))

            speed_label = "快放" if global_speed > 1 else ("慢放" if global_speed < 1 else "正常")
            log(f"变速: {speed_label} {global_speed:.4f}x")

            # 第二遍: 添加素材和片段
            current_time = 0
            for i, video_data in enumerate(video_infos):
                video_path = video_data['path']
                video_info = video_data['info']
                video_duration_us = video_data['duration_us']

                # 创建素材
                material = self._create_video_material(video_path, video_info)
                content['materials']['videos'].append(material)

                # 计算目标时长
                if use_template_duration and template_duration_us > 0:
                    target_duration_us = int(video_duration_us / global_speed)
                else:
                    target_duration_us = video_duration_us

                # 创建速度材料
                speed_material = self._create_speed_material(global_speed)
                content['materials']['speeds'].append(speed_material)

                # 创建片段
                segment = self._create_segment(
                    material_id=material['id'],
                    start_time=current_time,
                    source_duration=video_duration_us,
                    target_duration=target_duration_us,
                    speed=global_speed,
                    speed_material_id=speed_material['id'],
                    render_index=i
                )
                main_track['segments'].append(segment)

                current_time += target_duration_us

        # 随机打乱特效顺序（保留卡通脸轨道不变）
        self._shuffle_effect_tracks(content)
        # 随机交换贴纸位置（仅交换位置）
        self._shuffle_sticker_positions(content)

        # 更新项目时长
        current_time = main_track['segments'][-1]['target_timerange']['start'] + \
            main_track['segments'][-1]['target_timerange']['duration'] if main_track['segments'] else 0

        content['duration'] = current_time

        # 保存draft_content.json
        content_file = project_dir / "draft_content.json"
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)

        # 更新draft_meta_info.json
        meta_file = project_dir / "draft_meta_info.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            meta['draft_id'] = content['id']
            meta['draft_name'] = project_name
            meta['draft_fold_path'] = str(project_dir)
            meta['draft_root_path'] = str(self.output_dir)
            meta['tm_draft_create'] = int(datetime.now().timestamp() * 1000000)
            meta['tm_draft_modified'] = int(datetime.now().timestamp() * 1000000)
            meta['tm_duration'] = current_time

            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=4)

        log(f"项目已创建: {project_dir}")
        log(f"包含 {len(video_files)} 个视频，总时长: {current_time / 1000000:.1f}秒")

        return str(project_dir)

    def _shuffle_effect_tracks(self, content: dict) -> None:
        """随机打乱特效轨道顺序，保留卡通脸轨道不变"""
        tracks = content.get('tracks', [])
        materials = content.get('materials', {})
        effects = {m.get('id'): m for m in materials.get('video_effects', [])}

        for track in tracks:
            if track.get('type') != 'effect':
                continue
            segments = track.get('segments', [])
            if not segments:
                continue
            is_cartoon_track = True
            for seg in segments:
                info = effects.get(seg.get('material_id'), {})
                if info.get('name') != "卡通脸" and info.get('effect_id') != "10092161":
                    is_cartoon_track = False
                    break
            if is_cartoon_track:
                continue

            random.shuffle(segments)
            current = 0
            for idx, seg in enumerate(segments):
                tr = seg.get('target_timerange')
                if not isinstance(tr, dict):
                    tr = {"start": 0, "duration": 0}
                    seg['target_timerange'] = tr
                duration = tr.get('duration', 0)
                tr['start'] = current
                seg['render_index'] = idx
                current += duration

    def _shuffle_sticker_positions(self, content: dict) -> None:
        """随机交换贴纸位置，仅变更位置"""
        tracks = content.get('tracks', [])
        sticker_segments = []
        for track in tracks:
            if track.get('type') != 'sticker':
                continue
            sticker_segments.extend(track.get('segments', []))

        if not sticker_segments:
            return

        positions = []
        for seg in sticker_segments:
            clip = seg.get('clip') or {}
            transform = clip.get('transform') or {}
            positions.append({
                "x": transform.get('x', 0.0),
                "y": transform.get('y', 0.0)
            })

        random.shuffle(positions)

        for seg, pos in zip(sticker_segments, positions):
            clip = seg.setdefault('clip', {})
            transform = clip.setdefault('transform', {})
            transform['x'] = pos['x']
            transform['y'] = pos['y']

    def generate_from_videos(
        self,
        videos: List[Video],
        project_name: str,
        image_files: Optional[List[str]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> str:
        """从Video对象列表生成项目

        Args:
            videos: Video对象列表
            project_name: 项目名称
            on_log: 日志回调

        Returns:
            项目路径
        """
        video_files = [v.local_path for v in videos if v.local_path and Path(v.local_path).exists()]
        duration_overrides = {}
        for v in videos:
            if v.local_path and v.duration and Path(v.local_path).exists():
                duration_overrides[str(Path(v.local_path).absolute())] = v.duration
        return self.generate_project(
            video_files,
            project_name,
            image_files=image_files,
            video_duration_overrides=duration_overrides,
            on_log=on_log
        )
