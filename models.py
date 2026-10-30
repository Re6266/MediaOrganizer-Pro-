
from dataclasses import dataclass
from typing import Optional


@dataclass
class Media:
    """媒体文件信息"""

    file_path: str
    file_name: str
    file_type: str
    file_size: int

    id: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    capture_time: Optional[str] = None
    file_hash: Optional[str] = None
    similarity_group: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: Optional[str] = None

    # 新增：区分原始文件和 AI 生成文件
    is_generated: bool = False

    # 新增：记录生成该文件的合成任务
    source_composition_id: Optional[int] = None


@dataclass
class PhotoGroup:
    """照片组"""

    group_name: str
    group_type: str
    group_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class PhotoGroupItem:
    """照片组与媒体文件的关联"""

    group_id: int
    media_id: int
    relation_type: str = "similar"
    id: Optional[int] = None


@dataclass
class AIComposition:
    """AI 合成任务"""

    group_id: int
    mode: str
    status: str = "pending"
    composition_id: Optional[int] = None
    output_path: Optional[str] = None
    prompt: Optional[str] = None
    model_name: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class CompositionSource:
    """参与 AI 合成的原始照片及其作用"""

    composition_id: int
    media_id: int
    feature_type: str
    is_selected: bool = True
    id: Optional[int] = None


@dataclass
class OperationLog:
    """文件整理操作日志"""

    operation_type: str
    target_path: str
    status: str
    id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
