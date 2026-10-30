
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据目录
DATA_DIR = BASE_DIR / "data"

# 数据库文件
DATABASE_PATH = DATA_DIR / "organizer.db"

# 缩略图目录
THUMBNAIL_DIR = DATA_DIR / "thumbnails"

# AI 合成照片保存目录
GENERATED_DIR = DATA_DIR / "generated"

# 应用名称
APP_NAME = "MediaOrganizer-Pro"

# 支持的文件格式
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv"
}

# 自动创建必要目录
DATA_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
