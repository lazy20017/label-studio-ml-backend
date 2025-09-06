from typing import List, Dict, Optional, Tuple
import json
import os
import base64
import cv2
import numpy as np
import hashlib
import time
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 配置 ====================
SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
LABEL_STUDIO_MEDIA_DIR = os.getenv('LABEL_STUDIO_MEDIA_DIR', r'C:\Users\Administrator\AppData\Local\label-studio\label-studio\media')

# 简化的视频处理配置

# 视频抽帧配置
FRAME_EXTRACTION_CONFIG = {
    "strategy": "time_based",
    "max_frames": 3,
    "min_frames": 3,
    "time_interval": 5.0,
    "assumed_fps": 30.0,
    "quality_factor": 0.85,
    "serial_processing": True,
    "frame_processing_delay": 0.5,
}

# 目标检测标签配置
TARGET_LABELS = {
    "Floods": "洪水区域 - 被水淹没的地面、街道或区域",
    "Affected objects": "受影响物体 - 被洪水损坏、移位或影响的物品，如车辆、树木、电线杆等",
    "personnel": "人员 - 出现在场景中的人",
    "building": "建筑物 - 房屋、建筑结构"
}


class NewModel(LabelStudioMLBase):
    """精简版视频目标跟踪ML Backend模型"""
    
    def setup(self):
        """初始化配置"""
        print(f"\n🚀 视频目标跟踪ML Backend启动中...")
        
        self.set("model_version", "2.0.0-simplified")
        
        # API配置
        self.api_key = os.getenv('MODELSCOPE_API_KEY', 'ms-d200fd06-f07f-4be8-a6a8-9ebf76dd103a')
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        self.model_name = "Qwen/Qwen2.5-VL-72B-Instruct"
        
        # 初始化客户端
        self._init_client()
        self._show_config()
        
    def _init_client(self):
        """初始化OpenAI客户端"""
        if self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.api_base_url,
                    api_key=self.api_key
                )
                print(f"✅ 模型初始化成功: {self.model_name}")
            except Exception as e:
                print(f"❌ 客户端初始化失败: {e}")
                self.client = None
        else:
            print(f"⚠️ 请设置MODELSCOPE_API_KEY环境变量")
            self.client = None
        
    def _show_config(self):
        """显示当前配置"""
        config = FRAME_EXTRACTION_CONFIG
        serial_mode = config.get("serial_processing", True)
        delay = config.get("frame_processing_delay", 0.5)
        
        print(f"\n🎬 视频抽帧处理配置:")
        print(f"📊 抽帧策略: {config['strategy']}")
        print(f"🔢 最大帧数: {config['max_frames']}")
        print(f"🔄 处理模式: {'🔗 串行处理' if serial_mode else '📦 批量处理'}")
        if serial_mode:
            print(f"⏱️ 帧间延迟: {delay}秒")
    
    def _extract_video_frames(self, video_path: str) -> Tuple[List[Dict], Dict]:
        """精简版视频抽帧方法。返回(frames_data, video_info)"""
        frames_data = []
        video_info = {}
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ 无法打开视频文件: {video_path}")
                return frames_data
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or FRAME_EXTRACTION_CONFIG["assumed_fps"]
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 保存视频信息
            video_info = {
                "total_frames": total_frames,
                "fps": fps,
                "duration": duration,
                "width": width,
                "height": height
            }
            
            print(f"📹 视频信息: {total_frames}帧, {fps:.1f}FPS, {duration:.1f}秒, 尺寸:{width}x{height}")
            
            # 计算抽帧计划
            frame_indices = self._calculate_frame_indices(total_frames, fps, duration)
            
            if not frame_indices:
                print("❌ 无法生成抽帧计划")
                cap.release()
                return frames_data, video_info
            
            print(f"🔍 抽帧计划: 抽取 {len(frame_indices)} 帧")
            
            # 抽取帧
            quality = int(FRAME_EXTRACTION_CONFIG["quality_factor"] * 100)
            
            for i, target_frame in enumerate(frame_indices):
                # 跳转到目标帧
                success = self._seek_to_frame(cap, target_frame, fps)
                
                if success:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # 生成更强的哈希值
                        frame_hash = self._calculate_frame_hash(frame)
                        
                        # 转换为base64
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        data_url = f"data:image/jpeg;base64,{frame_base64}"
                        
                        # 获取时间戳
                        actual_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                        timestamp = actual_frame_pos / fps if fps > 0 else 0
                        
                        frame_data = {
                            "frame_number": target_frame,
                            "actual_frame": actual_frame_pos,
                            "timestamp": timestamp,
                            "data_url": data_url,
                            "frame_hash": frame_hash
                        }
                        
                        frames_data.append(frame_data)
                        print(f"✅ 抽取帧{target_frame} (实际:{actual_frame_pos}) 时间:{timestamp:.2f}s 哈希:{frame_hash[:16]}...")
                    else:
                        print(f"❌ 无法读取第 {target_frame} 帧")
                else:
                    print(f"❌ 无法跳转到第 {target_frame} 帧")
            
            cap.release()
            
            # 检查帧的多样性
            self._check_frame_diversity(frames_data)
            
        except Exception as e:
            print(f"❌ 视频抽帧失败: {e}")
        
        return frames_data, video_info
    
    def _calculate_frame_indices(self, total_frames: int, fps: float, duration: float) -> List[int]:
        """计算抽帧索引"""
        config = FRAME_EXTRACTION_CONFIG
        max_frames = config["max_frames"]
        min_frames = config["min_frames"]
        time_interval = config["time_interval"]
        assumed_fps = config["assumed_fps"]
        
        # 基于时间间隔计算
        theoretical_frames = int(duration / time_interval) + 1
        target_frames = min(max_frames, max(min_frames, theoretical_frames))
        
        frame_interval = int(time_interval * assumed_fps)
        
        frame_indices = []
        for i in range(target_frames):
            frame_idx = i * frame_interval
            if frame_idx < total_frames:
                frame_indices.append(frame_idx)
            else:
                break
        
        # 如果帧数不够，使用均匀分布
        if len(frame_indices) < min_frames and total_frames >= min_frames:
            target_frames = min(max_frames, max(min_frames, theoretical_frames))
            if target_frames >= total_frames:
                frame_indices = list(range(total_frames))
            else:
                interval = total_frames / target_frames
                frame_indices = [int(i * interval) for i in range(target_frames)]
        
        return sorted(list(set(frame_indices)))
    
    def _seek_to_frame(self, cap, target_frame: int, fps: float) -> bool:
        """跳转到指定帧"""
        try:
            # 方法1: 按时间戳跳转
            target_time_ms = (target_frame / fps) * 1000
            cap.set(cv2.CAP_PROP_POS_MSEC, target_time_ms)
            return True
        except:
            try:
                # 方法2: 按帧跳转
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                return True
            except:
                return False
    
    def _calculate_frame_hash(self, frame) -> str:
        """计算帧的强哈希值"""
        try:
            # 使用多种特征计算更强的哈希
            # 1. 图像内容哈希
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 2. 计算图像的直方图
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # 3. 计算边缘特征
            edges = cv2.Canny(gray, 50, 150)
            edge_sum = np.sum(edges)
            
            # 4. 计算图像统计信息
            mean_val = np.mean(gray)
            std_val = np.std(gray)
            
            # 5. 组合特征创建唯一哈希
            feature_string = f"{hist.flatten().tobytes()}{edge_sum}{mean_val:.2f}{std_val:.2f}"
            
            # 使用SHA256生成哈希
            hash_obj = hashlib.sha256(feature_string.encode())
            return hash_obj.hexdigest()
            
        except Exception as e:
            # 备用方案：使用原始帧数据
            print(f"⚠️ 高级哈希计算失败，使用备用方案: {e}")
            return hashlib.md5(frame.tobytes()).hexdigest()
    
    def _check_frame_diversity(self, frames_data: List[Dict]):
        """检查抽取帧的多样性"""
        if len(frames_data) < 2:
            return
        
        frame_hashes = [f["frame_hash"] for f in frames_data]
        unique_hashes = set(frame_hashes)
        diversity_rate = len(unique_hashes) / len(frames_data)
        
        print(f"🔍 抽帧多样性分析:")
        print(f"  总帧数: {len(frames_data)}")
        print(f"  唯一帧: {len(unique_hashes)}")
        print(f"  多样性: {diversity_rate:.1%}")
        
        if len(unique_hashes) == 1:
            print("⚠️ 所有帧内容相同！")
        elif diversity_rate < 0.5:
            print("⚠️ 帧多样性较低")
        else:
            print("✅ 帧多样性良好")
    
    def _find_video_file(self, video_url: str) -> Optional[str]:
        """查找视频文件的实际路径"""
        print(f"🔍 查找视频文件: {video_url}")
        
        # 生成可能的路径
        paths_to_check = []
        
        # 1. 标准Label Studio路径格式: /data/upload/X/filename
        if video_url.startswith('/data/upload/'):
            # 移除/data/前缀，直接在media目录下查找
            relative_path = video_url.replace('/data/', '')
            full_path = os.path.join(LABEL_STUDIO_MEDIA_DIR, relative_path)
            paths_to_check.append(full_path)
            print(f"   尝试路径1: {full_path}")
        
        # 2. 直接在media目录下查找
        paths_to_check.append(os.path.join(LABEL_STUDIO_MEDIA_DIR, video_url.lstrip('/')))
        
        # 3. 移除/data/前缀的简化路径
        simplified_path = video_url.replace('/data/', '')
        paths_to_check.append(simplified_path)
        
        # 4. 原始路径
        paths_to_check.append(video_url)
        
        # 返回第一个存在的路径
        for i, path in enumerate(paths_to_check):
            print(f"   检查路径{i+1}: {path}")
            if os.path.exists(path):
                print(f"✅ 找到视频文件: {path}")
                return path
        else:
                print(f"   ❌ 路径不存在")
        
        print(f"❌ 未找到视频文件: {video_url}")
        return None
    
    def _call_serial_api(self, prompt: str, video_frames: List[Dict]) -> Optional[str]:
        """串行调用API分析每帧"""
        if not self.client or not video_frames:
                return None
            
        try:
            print(f"🔄 开始串行处理 {len(video_frames)} 帧")
            
            all_frame_results = []
            
            for i, frame_info in enumerate(video_frames):
                frame_number = frame_info['frame_number']
                timestamp = frame_info['timestamp']
                
                print(f"📱 处理第{i+1}/{len(video_frames)}帧 (帧号:{frame_number}, 时间:{timestamp:.2f}s)")
                
                # 单帧分析
                frame_result = self._analyze_single_frame(frame_info, frame_number, timestamp)
                
                if frame_result:
                    all_frame_results.append(frame_result)
                    print(f"✅ 第{i+1}帧分析完成，检测到 {len(frame_result.get('objects', []))} 个对象")
                
                # 添加延迟
                delay = FRAME_EXTRACTION_CONFIG.get("frame_processing_delay", 0.5)
                if delay > 0:
                    time.sleep(delay)
            
            if all_frame_results:
                combined_result = {"video_objects": all_frame_results}
                return json.dumps(combined_result, ensure_ascii=False, indent=2)
            
            return None
    
        except Exception as e:
            print(f"❌ 串行API调用失败: {e}")
            return None
        
    def _generate_labels_description(self) -> str:
        """生成带说明的标签描述"""
        descriptions = []
        for label, desc in TARGET_LABELS.items():
            descriptions.append(f"• {label}: {desc}")
        return "\n".join(descriptions)
    
    def _convert_coordinates_to_percentage(self, bbox: List[float], video_info: Dict) -> List[float]:
        """将坐标转换为百分比格式"""
        x1, y1, x2, y2 = bbox
        
        # 获取视频尺寸用于判断
        width = video_info.get("width", 640)
        height = video_info.get("height", 364)
        
        # 更智能的坐标格式检测：
        # 1. 如果坐标值都超过100，明显是像素坐标
        # 2. 如果坐标值超过视频尺寸，也是像素坐标
        # 3. 如果x坐标接近视频宽度，y坐标接近视频高度，是像素坐标
        max_coord = max(bbox)
        is_pixel = (
            max_coord > 100 or  # 超过100%明显是像素
            (width > 0 and max_coord > width * 0.8) or  # 接近视频宽度
            (height > 0 and max_coord > height * 0.8) or  # 接近视频高度
            any(coord > min(width, height) for coord in bbox if width > 0 and height > 0)  # 超过较小维度
        )
        
        if is_pixel:
            print(f"🔄 检测到像素坐标，转换为百分比: {bbox}")
            
            if width > 0 and height > 0:
                # 转换为百分比
                x1_pct = (x1 / width) * 100
                y1_pct = (y1 / height) * 100
                x2_pct = (x2 / width) * 100
                y2_pct = (y2 / height) * 100
                
                result = [x1_pct, y1_pct, x2_pct, y2_pct]
                print(f"📐 转换结果: {result}")
                return result
            else:
                print(f"⚠️ 视频尺寸信息无效 ({width}x{height})，使用原始坐标")
                return bbox
        else:
            # 已经是百分比格式
            print(f"✅ 坐标已为百分比格式: {bbox}")
            return bbox
    
    def _analyze_single_frame(self, frame_info: Dict, frame_number: int, timestamp: float) -> Optional[Dict]:
        """分析单个帧"""
        try:
            # 动态生成包含标签说明的提示词
            labels_desc = self._generate_labels_description()
            prompt = f"""分析这个视频帧，检测以下对象类型：

{labels_desc}

要求：
1. 仔细分析图像中的每个区域
2. 识别上述类型的对象
3. 为每个检测到的对象提供准确的边界框坐标

返回JSON格式：
{{"frame_objects": [{{"label": "对象类型", "bbox": [x1, y1, x2, y2], "confidence": 0.95}}]}}

注意：
- 坐标必须为百分比格式：[左上x%, 左上y%, 右下x%, 右下y%]
- 坐标值范围0-100，例如 [10.5, 15.2, 45.8, 50.3]
- label必须完全匹配上述定义的对象类型之一
- confidence范围0-1，表示检测置信度"""
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant specialized in video frame analysis."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": frame_info["data_url"]}}
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                    
                if content:
                    # 解析JSON响应
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        frame_data = json.loads(json_str)
                        
                        return {
                            "frame_number": frame_number,
                            "timestamp": timestamp,
                            "objects": frame_data.get("frame_objects", [])
                        }
            
            # 失败时返回空结果
            return {
                "frame_number": frame_number,
                "timestamp": timestamp,
                "objects": []
            }
                
        except Exception as e:
            print(f"❌ 帧{frame_number}分析失败: {e}")
            return None
    
    def _format_video_prediction(self, api_response: str, task: Dict, video_info: Dict = None) -> Dict:
        """格式化视频预测结果"""
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.95,
            "result": []
        }
        
        try:
            # 解析API响应
            import re
            json_match = re.search(r'\{.*\}', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                tracking_data = json.loads(json_str)
                
                if 'video_objects' in tracking_data:
                    # 收集对象跟踪
                    object_tracks = {}
                    
                    for frame_data in tracking_data['video_objects']:
                        frame_number = frame_data.get('frame_number', 0)
                        timestamp = frame_data.get('timestamp', 0.0)
                        objects = frame_data.get('objects', [])
                        
                        for obj in objects:
                            if 'label' in obj and 'bbox' in obj:
                                label = obj['label']
                                bbox = obj['bbox']
                                confidence = obj.get('confidence', 0.8)
                                
                                print(f"🔍 处理对象: {label}, 坐标: {bbox}, 置信度: {confidence}")
                                
                                # 转换坐标为百分比格式
                                converted_bbox = self._convert_coordinates_to_percentage(bbox, video_info or {})
                                x1, y1, x2, y2 = converted_bbox
                                
                                print(f"📐 转换后坐标: ({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})")
                                
                                # 确保坐标顺序正确（左上角 -> 右下角）
                                if x1 > x2:
                                    x1, x2 = x2, x1
                                if y1 > y2:
                                    y1, y2 = y2, y1
                                
                                # 计算Label Studio需要的格式：x, y, width, height (百分比)
                                x = x1  # 左上角X坐标百分比
                                y = y1  # 左上角Y坐标百分比
                                width = x2 - x1  # 宽度百分比
                                height = y2 - y1  # 高度百分比
                                
                                print(f"🎯 转换后坐标: x={x:.1f}%, y={y:.1f}%, width={width:.1f}%, height={height:.1f}%")
                                
                                # 确保坐标在合理范围内
                                x = max(0, min(100, x))
                                y = max(0, min(100, y))
                                width = max(0.1, min(100-x, width))
                                height = max(0.1, min(100-y, height))
                                
                                if label not in object_tracks:
                                    object_tracks[label] = []
                                
                                object_tracks[label].append({
                                    "frame": frame_number,
                                    "enabled": True,
                                    "rotation": 0,
                                    "x": float(x),  # 确保是百分比 (0-100)
                                    "y": float(y),  # 确保是百分比 (0-100)
                                    "width": float(width),  # 确保是百分比 (0-100)
                                    "height": float(height),  # 确保是百分比 (0-100)
                                    "time": timestamp,
                                    "score": confidence  # 每个点的置信度
                                })
                    
                    # 创建VideoRectangle结果
                    print(f"🎯 检测到的对象轨迹: {list(object_tracks.keys())}")
                    for label, track_sequence in object_tracks.items():
                        track_sequence.sort(key=lambda x: x["frame"])
                        avg_confidence = sum(item["score"] for item in track_sequence) / len(track_sequence)
                        print(f"📊 对象 '{label}' 有 {len(track_sequence)} 个轨迹点，平均置信度: {avg_confidence:.3f}")
                        
                        sequence_data = []
                        for item in track_sequence:
                            sequence_data.append({
                                "frame": item["frame"],
                                "enabled": item["enabled"],
                                "rotation": item["rotation"],
                                "x": item["x"],
                                "y": item["y"],
                                "width": item["width"],
                                "height": item["height"],
                                "time": item["time"],
                                "score": item["score"]  # 添加每个点的置信度
                            })
                        
                        # 添加视频信息
                        value_data = {
                            "sequence": sequence_data,
                            "labels": [label]
                        }
                        
                        # 如果有视频信息，添加duration和framesCount
                        if video_info:
                            value_data["duration"] = video_info.get("duration", 0)
                            value_data["framesCount"] = video_info.get("total_frames", 0)
                        
                        result_item = {
                            "from_name": "box",
                            "to_name": "video",
                            "type": "videorectangle",
                            "value": value_data,
                            "score": avg_confidence
                        }
                        
                        prediction["result"].append(result_item)
                    
        except Exception as e:
            print(f"❌ 解析预测结果失败: {e}")
        
        return prediction
    
    def _create_mock_prediction(self, video_frames: List[Dict], task: Dict, video_info: Dict = None) -> Dict:
        """创建模拟的预测结果（用于API不可用时）"""
        print("🎭 生成模拟标注结果...")
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.85,
            "result": []
        }
        
        try:
            # 为每个标签类型创建一个跟踪序列
            labels = list(TARGET_LABELS.keys())
            
            for label_idx, label in enumerate(labels):
                if label_idx >= len(video_frames):
                    break  # 限制标签数量不超过帧数
                
                # 创建跟踪序列
                sequence_data = []
                
                for i, frame_info in enumerate(video_frames):
                    frame_number = frame_info['frame_number']
                    timestamp = frame_info['timestamp']
                    
                    # 为不同标签生成不同位置的模拟边界框 (使用百分比 0-100)
                    base_x = 10.0 + (label_idx * 25.0) % 60.0
                    base_y = 10.0 + (label_idx * 20.0) % 50.0
                    
                    # 添加一些随机变化模拟目标移动
                    variation = i * 2.0
                    x = base_x + variation % 15.0
                    y = base_y + variation % 10.0
                    width = 15.0 + variation % 10.0
                    height = 12.0 + variation % 8.0
                    
                    sequence_data.append({
                        "frame": frame_number,
                        "enabled": True,
                        "rotation": 0,
                        "x": float(x),  # 百分比坐标 (0-100)
                        "y": float(y),  # 百分比坐标 (0-100)
                        "width": float(width),  # 百分比宽度 (0-100)
                        "height": float(height),  # 百分比高度 (0-100)
                        "time": timestamp,
                        "score": 0.85 - (label_idx * 0.05) + (i * 0.01)  # 模拟置信度变化
                    })
                
                # 创建VideoRectangle结果
                value_data = {
                    "sequence": sequence_data,
                    "labels": [label]
                }
                
                # 如果有视频信息，添加duration和framesCount
                if video_info:
                    value_data["duration"] = video_info.get("duration", 0)
                    value_data["framesCount"] = video_info.get("total_frames", 0)
                
                result_item = {
                    "from_name": "box",
                    "to_name": "video",
                    "type": "videorectangle",
                    "value": value_data,
                    "score": 0.85 - (label_idx * 0.1)  # 递减的置信度
                }
                
                prediction["result"].append(result_item)
                print(f"🎯 生成模拟标签: {label} (包含{len(sequence_data)}个跟踪点)")
            
            print(f"✅ 模拟预测完成，生成了{len(prediction['result'])}个标注对象")
            
        except Exception as e:
            print(f"❌ 生成模拟预测失败: {e}")
        
        return prediction
    
    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """主预测方法"""
        print(f"\n🚀 收到预测请求，任务数量: {len(tasks)}")
        predictions = []
        
        for i, task in enumerate(tasks):
            print(f"\n📝 处理任务 {i+1}/{len(tasks)}")
            try:
                prediction = self._process_task(task)
                if prediction:
                    predictions.append(prediction)
                    print(f"✅ 任务{i+1}处理成功，生成了{len(prediction.get('result', []))}个标注")
                else:
                    print(f"⚠️ 任务{i+1}返回空结果")
                    predictions.append({"model_version": self.get("model_version"), "score": 0.0, "result": []})
            except Exception as e:
                print(f"❌ 任务{i+1}处理失败: {e}")
                import traceback
                print(f"🔍 错误详情: {traceback.format_exc()}")
                predictions.append({"model_version": self.get("model_version"), "score": 0.0, "result": []})
        
        print(f"\n🎯 预测完成，总共返回{len(predictions)}个预测结果")
        for i, pred in enumerate(predictions):
            result_count = len(pred.get('result', []))
            print(f"  任务{i+1}: {result_count}个标注对象")
        
        return ModelResponse(predictions=predictions)
    
    def _process_task(self, task: Dict) -> Optional[Dict]:
        """处理单个任务"""
        print(f"\n🎯 开始处理任务...")
        print(f"📋 任务数据: {json.dumps(task, ensure_ascii=False, indent=2)}")
        
        # 查找视频URL
        video_url = self._extract_video_url(task.get('data', {}))
        if not video_url:
            print("❌ 未找到视频URL")
            return None
        
        print(f"🎬 找到视频URL: {video_url}")
        
        # 查找并处理视频文件
        video_path = self._find_video_file(video_url)
        if not video_path:
            print(f"❌ 未找到视频文件: {video_url}")
            return None
        
        print(f"✅ 视频文件路径: {video_path}")
        
        # 抽帧并分析
        video_frames, video_info = self._extract_video_frames(video_path)
        if not video_frames:
            print("❌ 视频抽帧失败")
            return None
        
        print(f"✅ 成功抽取 {len(video_frames)} 帧")
        
        # 检查API客户端状态
        if not self.client:
            print("⚠️ API客户端未初始化，返回模拟标注结果")
            return self._create_mock_prediction(video_frames, task, video_info)
        
        # 调用API分析
        print("🤖 开始调用API分析...")
        api_response = self._call_serial_api("", video_frames)
        
        if api_response:
            print("✅ API分析完成，开始格式化结果...")
            print(f"📊 API响应: {api_response[:200]}...")
            result = self._format_video_prediction(api_response, task, video_info)
            print(f"🎯 最终预测结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print("❌ API分析失败，返回模拟结果")
            return self._create_mock_prediction(video_frames, task, video_info)
    
    def _extract_video_url(self, task_data: Dict) -> Optional[str]:
        """从任务数据中提取视频URL"""
        for key, value in task_data.items():
            if isinstance(value, str):
                # 检查关键字段
                if key.lower() in ['video', 'vid', 'movie', 'media', 'url']:
                    return value
                # 检查文件扩展名
                if any(value.lower().endswith(f'.{ext}') for ext in SUPPORTED_VIDEO_FORMATS):
                    return value
        return None
    
    def fit(self, event, data, **kwargs):
        """训练方法"""
        self.set('annotation_data', 'updated_video_tracking_data')
        self.set('model_version', 'updated_video_version')
        print(f"✅ 模型已更新 (事件: {event})")
