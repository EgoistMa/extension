#!/usr/bin/env python3
"""
剪映项目生成器
基于模板创建新的剪映项目，替换视频素材
"""

import os
import json
import shutil
import uuid
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class JianyingGenerator:
    """剪映项目生成器"""

    def __init__(self, template_path: str, output_base_dir: str = None):
        """
        初始化生成器

        Args:
            template_path: 模板项目路径 (包含 draft_content.json 的文件夹)
            output_base_dir: 输出目录基路径，默认为剪映默认草稿目录
        """
        self.template_path = Path(template_path)
        self.output_base_dir = Path(output_base_dir) if output_base_dir else self._get_default_drafts_dir()

        if not self.template_path.exists():
            raise FileNotFoundError(f"模板路径不存在: {template_path}")

        # 加载模板
        self.template_content = self._load_template()

    def _get_default_drafts_dir(self) -> Path:
        """获取剪映默认草稿目录"""
        # Windows 上剪映默认路径
        possible_paths = [
            Path.home() / "Documents" / "JianyingPro Drafts",
            Path("D:/JianyingPro Drafts"),
            Path("C:/JianyingPro Drafts"),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # 如果都不存在，使用第一个
        return possible_paths[0]

    def _load_template(self) -> dict:
        """加载模板内容"""
        content_file = self.template_path / "draft_content.json"
        if not content_file.exists():
            raise FileNotFoundError(f"找不到模板文件: {content_file}")

        with open(content_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generate_uuid(self) -> str:
        """生成剪映格式的 UUID"""
        return str(uuid.uuid4()).upper()

    def _get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息（时长、宽高）

        Returns:
            dict: {
                'duration_us': 时长（微秒），用于 segment timerange
                'duration_ns': 时长（纳秒），用于 material duration
                'width': 宽度
                'height': 高度
            }
        """
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"[警告] 视频文件不存在: {video_path}")
            return {'duration_us': 10000000, 'duration_ns': 10000000000, 'width': 1080, 'height': 1920}

        # 方法1：从文件名解析时长（格式：xxx_76s_xxx.mp4）
        filename = video_path.stem
        import re
        duration_match = re.search(r'_(\d+)s_', filename)
        if duration_match:
            duration = int(duration_match.group(1))
            duration_us = duration * 1000000
            duration_ns = duration * 1000000000
            print(f"[剪映] 从文件名解析时长: {filename} -> {duration}秒")
            return {'duration_us': duration_us, 'duration_ns': duration_ns, 'width': 1080, 'height': 1920}

        # 方法2：尝试使用 ffprobe
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
                    duration_us = int(duration * 1000000)
                    duration_ns = int(duration * 1000000000)

                    width, height = 1080, 1920
                    for stream in info.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            width = stream.get('width', 1080)
                            height = stream.get('height', 1920)
                            break

                    print(f"[剪映] ffprobe 解析时长: {video_path.name} -> {duration:.1f}秒")
                    return {'duration_us': duration_us, 'duration_ns': duration_ns, 'width': width, 'height': height}
        except FileNotFoundError:
            print("[警告] ffprobe 未安装，无法精确获取视频时长")
        except Exception as e:
            print(f"[警告] ffprobe 失败: {e}")

        # 方法3：使用 cv2（如果安装了 opencv）
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()

                if fps > 0 and frame_count > 0:
                    duration = frame_count / fps
                    duration_us = int(duration * 1000000)
                    duration_ns = int(duration * 1000000000)
                    print(f"[剪映] cv2 解析时长: {video_path.name} -> {duration:.1f}秒")
                    return {'duration_us': duration_us, 'duration_ns': duration_ns, 'width': width, 'height': height}
        except ImportError:
            pass
        except Exception as e:
            print(f"[警告] cv2 失败: {e}")

        # 默认值：30秒（比10秒更合理）
        print(f"[警告] 无法获取视频时长，使用默认30秒: {video_path.name}")
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
                "lower_left_x": 0.0,
                "lower_left_y": 1.0,
                "lower_right_x": 1.0,
                "lower_right_y": 1.0,
                "upper_left_x": 0.0,
                "upper_left_y": 0.0,
                "upper_right_x": 1.0,
                "upper_right_y": 0.0
            },
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": video_info['duration_ns'],  # 纳秒
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
                "flag": 0,
                "has_use_quick_brush": False,
                "has_use_quick_eraser": False,
                "interactiveTime": [],
                "path": "",
                "strokes": []
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
                "time_range": {
                    "duration": 0,
                    "start": 0
                }
            },
            "team_id": "",
            "type": "video",
            "video_algorithm": {
                "algorithms": [],
                "complement_frame_config": None,
                "deflicker": None,
                "gameplay_configs": [],
                "motion_blur_config": None,
                "noise_reduction": None,
                "path": "",
                "quality_enhance": None,
                "time_range": None
            },
            "width": video_info['width']
        }

    def _create_speed_material(self, speed: float) -> dict:
        """
        创建速度材料对象

        Args:
            speed: 播放速度

        Returns:
            速度材料对象
        """
        return {
            "curve_speed": None,
            "id": self._generate_uuid(),
            "mode": 0,
            "speed": speed,
            "type": "speed"
        }

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
        """
        创建时间轴片段

        Args:
            material_id: 素材ID
            start_time: 在时间轴上的起始位置（微秒）
            source_duration: 从原视频截取的时长（微秒）
            target_duration: 在时间轴上显示的时长（微秒）
            speed: 播放速度（1.0为正常，>1快放，<1慢放）
            speed_material_id: 速度材料ID（用于extra_material_refs）
            render_index: 渲染索引
        """
        segment_id = self._generate_uuid()

        # 构建 extra_material_refs
        extra_refs = []
        if speed_material_id:
            extra_refs.append(speed_material_id)

        return {
            "caption_info": None,
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {
                    "horizontal": False,
                    "vertical": False
                },
                "rotation": 0.0,
                "scale": {
                    "x": 1.0,
                    "y": 1.0
                },
                "transform": {
                    "x": 0.0,
                    "y": 0.0
                }
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
            "hdr_settings": {
                "intensity": 1.0,
                "mode": 1,
                "nits": 1000
            },
            "id": segment_id,
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": material_id,
            "render_index": render_index,
            "responsive_layout": {
                "enable": False,
                "horizontal_pos_layout": 0,
                "size_layout": 0,
                "target_follow": "",
                "vertical_pos_layout": 0
            },
            "reverse": False,
            "source_timerange": {
                "duration": source_duration,  # 原视频使用的时长（微秒）
                "start": 0
            },
            "speed": speed,  # 播放速度
            "target_timerange": {
                "duration": target_duration,  # 时间轴上的时长（微秒）
                "start": start_time
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {
                "on": True,
                "value": 1.0
            },
            "visible": True,
            "volume": 1.0
        }

    def _get_template_duration(self) -> int:
        """
        获取模板的总时长（微秒）

        优先使用 export_range.duration（实际导出时长），
        如果没有则使用 duration（项目总时长）
        """
        # 优先使用导出范围的时长
        config = self.template_content.get('config', {})
        export_range = config.get('export_range', {})
        export_duration = export_range.get('duration', 0)

        if export_duration > 0:
            return export_duration

        # 否则使用项目时长
        return self.template_content.get('duration', 0)

    def generate_project(
        self,
        video_files: List[str],
        project_name: str,
        clip_duration: int = None,
        use_template_duration: bool = True,
        auto_open: bool = False
    ) -> str:
        """
        生成剪映项目

        Args:
            video_files: 视频文件路径列表
            project_name: 项目名称
            clip_duration: 每个片段时长（微秒），None 则使用模板或视频时长
            use_template_duration: 是否使用模板时长（会拉伸/压缩视频）
            auto_open: 是否自动打开剪映

        Returns:
            项目路径
        """
        if not video_files:
            raise ValueError("视频文件列表不能为空")

        # 创建项目目录
        project_dir = self.output_base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # 复制模板文件（除了 draft_content.json）
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

        # 创建新的 draft_content
        content = json.loads(json.dumps(self.template_content))  # 深拷贝

        # 生成新的项目 ID
        content['id'] = self._generate_uuid()

        # 获取模板时长（微秒）
        template_duration_us = self._get_template_duration()
        print(f"[剪映] 模板时长: {template_duration_us / 1000000:.1f}秒")

        # 清空原有视频素材和轨道
        content['materials']['videos'] = []

        # 清空或初始化速度材料列表
        if 'speeds' not in content['materials']:
            content['materials']['speeds'] = []
        else:
            content['materials']['speeds'] = []

        # 找到主视频轨道（第一个 track）
        if content.get('tracks') and len(content['tracks']) > 0:
            main_track = content['tracks'][0]
            main_track['segments'] = []
        else:
            # 创建主轨道
            main_track = {
                "attribute": 0,
                "flag": 0,
                "id": self._generate_uuid(),
                "is_default_name": True,
                "name": "",
                "segments": [],
                "type": "video"
            }
            content['tracks'] = [main_track]

        # 第一遍：获取所有视频信息并计算总时长
        video_infos = []
        total_original_duration_us = 0

        for video_path in video_files:
            video_info = self._get_video_info(video_path)
            video_infos.append({
                'path': video_path,
                'info': video_info,
                'duration_us': video_info['duration_us']
            })
            total_original_duration_us += video_info['duration_us']

        print(f"[剪映] 所有视频总时长: {total_original_duration_us / 1000000:.1f}秒")
        print(f"[剪映] 模板目标时长: {template_duration_us / 1000000:.1f}秒")

        # 计算统一的变速比例
        # 剪映speed参数（符合直觉）：
        # - speed > 1.0 = 快放（例如 1.2 = 1.2倍速播放）
        # - speed < 1.0 = 慢放（例如 0.5 = 0.5倍速播放）
        #
        # speed = 原始时长 / 目标时长
        # 例如：310秒视频放入300秒 → speed = 310/300 = 1.033（快放）
        if use_template_duration and template_duration_us > 0 and total_original_duration_us > 0:
            global_speed = total_original_duration_us / template_duration_us
        else:
            global_speed = 1.0

        # 限制速度范围（剪映支持 0.1x - 100x）
        global_speed = max(0.1, min(100.0, global_speed))

        # speed > 1 = 快放，speed < 1 = 慢放
        speed_label = "快放" if global_speed > 1 else ("慢放" if global_speed < 1 else "正常")
        print(f"[剪映] 统一变速: {speed_label} speed={global_speed:.4f}x")

        # 第二遍：添加视频素材和片段
        current_time = 0
        total_duration = 0

        for i, video_data in enumerate(video_infos):
            video_path = video_data['path']
            video_info = video_data['info']
            video_duration_us = video_data['duration_us']  # 视频原始时长（微秒）

            # 创建素材
            material = self._create_video_material(video_path, video_info)
            content['materials']['videos'].append(material)

            # 计算这个视频在时间轴上的目标时长
            if clip_duration:
                # 使用指定的固定时长
                target_duration_us = clip_duration
            elif use_template_duration and template_duration_us > 0:
                # 目标时长 = 原始时长 / 速度
                # 例如：76秒视频，speed=1.2 → 目标时长 = 76/1.2 = 63.3秒
                target_duration_us = int(video_duration_us / global_speed)
            else:
                # 使用视频原始时长
                target_duration_us = video_duration_us

            # 剪映变速机制（符合直觉）：
            # - speed > 1.0 = 快放（例如 speed=1.2 表示1.2倍速）
            # - speed < 1.0 = 慢放（例如 speed=0.8 表示0.8倍速）
            # - speed = 原始时长 / 目标时长
            #
            # 使用全局统一速度（所有视频同样的变速比例）
            speed = global_speed

            # 显示信息（speed > 1 = 快放，speed < 1 = 慢放）
            speed_label = "快放" if speed > 1.001 else ("慢放" if speed < 0.999 else "正常")
            print(f"[剪映] 视频 {i+1}: 原始 {video_duration_us/1000000:.2f}s -> 目标 {target_duration_us/1000000:.2f}s ({speed_label} {speed:.4f}x)")

            # 创建速度材料对象
            speed_material = self._create_speed_material(speed)
            content['materials']['speeds'].append(speed_material)

            # 创建时间轴片段
            # source_duration = 原始视频时长（要播放的内容时长）
            # target_duration = 时间轴上占用的时长
            # speed = source/target（> 1 快放，< 1 慢放）
            segment = self._create_segment(
                material_id=material['id'],
                start_time=current_time,
                source_duration=video_duration_us,    # 原始视频时长
                target_duration=target_duration_us,   # 时间轴目标时长
                speed=speed,                          # 速度控制变速
                speed_material_id=speed_material['id'],
                render_index=i
            )
            main_track['segments'].append(segment)

            current_time += target_duration_us
            total_duration = current_time

        # 更新项目时长（微秒）
        content['duration'] = total_duration

        # 保存 draft_content.json
        content_file = project_dir / "draft_content.json"
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)

        # 更新 draft_meta_info.json
        meta_file = project_dir / "draft_meta_info.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            meta['draft_id'] = content['id']
            meta['draft_name'] = project_name
            meta['draft_fold_path'] = str(project_dir)
            meta['draft_root_path'] = str(self.output_base_dir)
            meta['tm_draft_create'] = int(datetime.now().timestamp() * 1000000)
            meta['tm_draft_modified'] = int(datetime.now().timestamp() * 1000000)
            meta['tm_duration'] = total_duration  # 微秒

            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=4)

        print(f"[剪映] 项目已创建: {project_dir}")
        print(f"[剪映] 包含 {len(video_files)} 个视频，总时长: {total_duration / 1000000:.1f}秒")

        # 自动打开剪映
        if auto_open:
            self._open_jianying(project_dir)

        return str(project_dir)

    def _open_jianying(self, project_dir: Path):
        """打开剪映并加载项目"""
        # 剪映可能的安装路径
        jianying_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / "JianyingPro" / "Apps" / "JianyingPro.exe",
            Path("C:/Program Files/JianyingPro/JianyingPro.exe"),
            Path("D:/Program Files/JianyingPro/JianyingPro.exe"),
        ]

        jianying_exe = None
        for path in jianying_paths:
            if path.exists():
                jianying_exe = path
                break

        if jianying_exe:
            try:
                subprocess.Popen([str(jianying_exe)], shell=True)
                print(f"[剪映] 正在启动剪映...")
            except Exception as e:
                print(f"[剪映] 启动剪映失败: {e}")
        else:
            print("[剪映] 未找到剪映安装路径，请手动打开")


def test_generator():
    """测试生成器"""
    template_path = Path(__file__).parent / "MB12.15"
    generator = JianyingGenerator(str(template_path))

    # 测试生成项目
    test_videos = [
        "C:/test/video1.mp4",
        "C:/test/video2.mp4",
    ]

    try:
        project_path = generator.generate_project(
            video_files=test_videos,
            project_name="测试项目_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            auto_open=False
        )
        print(f"项目已创建: {project_path}")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    test_generator()
