"""生成演示用的测试图片与文件夹。

用途：给「扫描 → 重复检测 → 浏览与分组」这条链路准备一套可控素材，
目录里同时包含完全重复文件、视觉相似文件、互不相同的照片和不应被扫描的杂项文件。

用法：
    python tools/generate_demo_media.py
    python tools/generate_demo_media.py --output ../demo-media --clean

脚本是确定性的（固定随机种子），重复运行会得到相同像素，便于复现演示结果。
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# ---------------------------------------------------------------------------
# 基础绘制工具
# ---------------------------------------------------------------------------

W, H = 1200, 800


def _gradient(width, height, top, bottom):
    """竖直渐变底图。top/bottom 为 (r,g,b)。"""
    ramp = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    top_arr = np.array(top, dtype=np.float32)
    bottom_arr = np.array(bottom, dtype=np.float32)
    rows = top_arr[None, :] * (1 - ramp) + bottom_arr[None, :] * ramp
    canvas = np.repeat(rows[:, None, :], width, axis=1)
    return Image.fromarray(canvas.astype(np.uint8), "RGB")


def _grain(image, amount=6, seed=0):
    """加轻微噪点，避免大片纯色让 pHash 过于理想化。"""
    rng = np.random.default_rng(seed)
    arr = np.asarray(image, dtype=np.int16)
    noise = rng.normal(0, amount, arr.shape).astype(np.int16)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8), "RGB")


def _vignette(image, strength=0.35):
    """四周压暗，模拟真实拍摄的镜头暗角。"""
    width, height = image.size
    y, x = np.mgrid[0:height, 0:width]
    cx, cy = width / 2, height / 2
    dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
    mask = np.clip(1 - strength * np.clip(dist - 0.55, 0, None) ** 1.4, 0.0, 1.0)
    arr = np.asarray(image, dtype=np.float32) * mask[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


def _soft_light(image, radius=1.2):
    return image.filter(ImageFilter.GaussianBlur(radius))


# ---------------------------------------------------------------------------
# 场景一：风景（山、湖、日出）
# ---------------------------------------------------------------------------

def landscape(seed, sky, water, ridge, sun_xy=(0.72, 0.22), horizon=0.56):
    rng = random.Random(seed)
    img = _gradient(W, H, sky[0], sky[1])
    draw = ImageDraw.Draw(img, "RGBA")
    hy = int(H * horizon)

    # 太阳与光晕
    sx, sy = int(W * sun_xy[0]), int(H * sun_xy[1])
    for step in range(9, 0, -1):
        r = int(38 + step * 16)
        draw.ellipse([sx - r, sy - r, sx + r, sy + r],
                     fill=(255, 236, 190, int(6 + step * 2)))
    draw.ellipse([sx - 34, sy - 34, sx + 34, sy + 34], fill=(255, 248, 222, 235))

    # 远山三层，越远越淡
    for layer in range(3):
        base_y = hy - int(H * 0.02 * (2 - layer))
        points = [(-40, base_y + 60)]
        x = -40
        while x < W + 40:
            peak = base_y - rng.randint(30, 110) * (layer + 1) // 2
            points.append((x, peak))
            x += rng.randint(110, 190)
        points.append((W + 40, base_y + 60))
        shade = tuple(int(c + (layer - 1) * 16) for c in ridge)
        draw.polygon(points, fill=shade + (255,))

    # 水面
    draw.rectangle([0, hy, W, H], fill=water + (255,))
    # 水中倒影与横向波纹
    for i in range(60):
        y = hy + rng.randint(2, H - hy - 4)
        w = rng.randint(60, 380)
        x = sx - w // 2 + rng.randint(-160, 160)
        alpha = int(26 * (1 - (y - hy) / (H - hy)))
        draw.line([x, y, x + w, y], fill=(255, 244, 214, alpha), width=2)

    img = _vignette(_soft_light(img), 0.30)
    return _grain(img, 5, seed)


# ---------------------------------------------------------------------------
# 场景二：室内人像 / 合影
# ---------------------------------------------------------------------------

def indoor_portrait(seed, warm=(252, 226, 196), accent=(196, 142, 118)):
    rng = random.Random(seed)
    img = _gradient(W, H, warm, tuple(max(0, c - 55) for c in warm))
    draw = ImageDraw.Draw(img, "RGBA")

    # 背景散景光斑
    for _ in range(28):
        r = rng.randint(28, 90)
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.75))
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(255, 235, 205, rng.randint(20, 55)))

    # 两个人影轮廓：肩线 + 头部
    for cx, scale in ((W * 0.40, 1.0), (W * 0.60, 0.94)):
        sh_w = int(210 * scale)
        top = int(H * 0.52)
        draw.rounded_rectangle([cx - sh_w, top, cx + sh_w, H + 40],
                               radius=90, fill=(72, 56, 62, 255))
        head_r = int(74 * scale)
        head_y = top - head_r + 18
        draw.ellipse([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r],
                     fill=(206, 168, 140, 255))
        # 头发
        draw.chord([cx - head_r, head_y - head_r - 8, cx + head_r, head_y + head_r - 6],
                   180, 360, fill=(48, 38, 40, 255))

    # 前景虚化色块
    for _ in range(10):
        r = rng.randint(50, 120)
        x, y = rng.randint(-40, W + 40), rng.randint(int(H * 0.8), H + 40)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=accent + (34,))

    img = _soft_light(_vignette(img, 0.42), 1.6)
    return _grain(img, 7, seed)


# ---------------------------------------------------------------------------
# 场景三：俯拍餐桌 / 蛋糕
# ---------------------------------------------------------------------------

def table_top(seed, table=(146, 110, 82), food_colors=((214, 96, 74), (232, 190, 118), (108, 142, 92))):
    rng = random.Random(seed)
    img = _gradient(W, H, table, tuple(max(0, c - 30) for c in table))
    draw = ImageDraw.Draw(img, "RGBA")

    # 木纹
    for _ in range(90):
        y = rng.randint(0, H)
        draw.line([0, y, W, y + rng.randint(-6, 6)],
                  fill=(92, 68, 50, rng.randint(10, 26)), width=rng.randint(1, 3))

    # 盘子
    cx, cy = W // 2, int(H * 0.52)
    rx, ry = int(W * 0.30), int(H * 0.36)
    draw.ellipse([cx - rx + 14, cy - ry + 20, cx + rx + 14, cy + ry + 20], fill=(70, 52, 40, 90))
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(248, 246, 240, 255))
    draw.ellipse([cx - rx + 46, cy - ry + 46, cx + rx - 46, cy + ry - 46],
                 outline=(214, 210, 202, 255), width=4)

    # 食物色块
    for i in range(7):
        r = rng.randint(48, 86)
        a = rng.uniform(0, 6.28)
        dist = rng.uniform(0, 0.55)
        x = cx + int(np.cos(a) * rx * dist)
        y = cy + int(np.sin(a) * ry * dist)
        color = food_colors[i % len(food_colors)]
        draw.ellipse([x - r, y - r + 6, x + r, y + r + 6], fill=(60, 44, 34, 60))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))
        draw.ellipse([x - r // 3, y - r // 2, x + r // 6, y - r // 6],
                     fill=(255, 255, 255, 46))

    img = _soft_light(_vignette(img, 0.34), 1.1)
    return _grain(img, 6, seed)


# ---------------------------------------------------------------------------
# 场景四：屏幕截图（浅色 UI，pHash 对版式变化敏感）
# ---------------------------------------------------------------------------

def screenshot(seed, sidebar_left=True, cards=3):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), (247, 248, 250))
    draw = ImageDraw.Draw(img)

    # 顶部条
    draw.rectangle([0, 0, W, 64], fill=(255, 255, 255))
    draw.line([0, 64, W, 64], fill=(228, 232, 236), width=2)
    for i, c in enumerate(((236, 110, 100), (240, 190, 100), (140, 200, 140))):
        draw.ellipse([24 + i * 22, 26, 40 + i * 22, 42], fill=c)

    # 左侧栏
    sx = 0 if sidebar_left else W - 190
    draw.rectangle([sx, 64, sx + 190, H], fill=(250, 251, 252))
    edge = sx + 190
    draw.line([edge, 64, edge, H], fill=(230, 234, 238), width=2)
    for i in range(7):
        y = 96 + i * 46
        draw.rounded_rectangle([sx + 22, y, sx + 160, y + 22], radius=6,
                               fill=(232, 238, 240) if i else (206, 224, 214))

    # 主区标题与正文行
    x0 = 230 if sidebar_left else 40
    draw.rounded_rectangle([x0, 100, x0 + 260, 124], radius=6, fill=(220, 226, 228))
    for i in range(4):
        y = 146 + i * 22
        draw.rounded_rectangle([x0, y, x0 + rng.randint(180, 420), y + 12],
                               radius=5, fill=(236, 240, 242))

    # 卡片区
    cw = 250
    for i in range(cards):
        x = x0 + i * (cw + 24)
        draw.rounded_rectangle([x, 260, x + cw, 520], radius=12,
                               fill=(255, 255, 255), outline=(229, 234, 238), width=2)
        draw.rounded_rectangle([x + 14, 274, x + cw - 14, 390], radius=8,
                               fill=(226, 233, 230))
        for j in range(2):
            y = 406 + j * 24
            draw.rounded_rectangle([x + 14, y, x + cw - 14 - rng.randint(30, 90), y + 10],
                                   radius=5, fill=(234, 238, 240))

    # 表格区
    ty = 560
    draw.rounded_rectangle([x0, ty, W - 40, ty + 190], radius=10,
                           fill=(255, 255, 255), outline=(229, 234, 238), width=2)
    for i in range(5):
        y = ty + 20 + i * 34
        draw.line([x0 + 12, y + 20, W - 52, y + 20], fill=(238, 241, 243), width=1)
        draw.rounded_rectangle([x0 + 20, y, x0 + rng.randint(90, 200), y + 12],
                               radius=4, fill=(226, 231, 234))
        draw.rounded_rectangle([W - 320, y, W - 120, y + 12], radius=4, fill=(232, 238, 234))

    return img


# ---------------------------------------------------------------------------
# 变体生成
# ---------------------------------------------------------------------------

def save(image: Image.Image, path: Path, quality=88, exif_time=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    exif = Image.Exif()
    if exif_time:
        exif[36867] = exif_time          # DateTimeOriginal
        exif[306] = exif_time            # DateTime
    if path.suffix.lower() in (".jpg", ".jpeg"):
        image.save(path, "JPEG", quality=quality, exif=exif, optimize=True)
    else:
        image.save(path, "PNG", optimize=True)
    return path


def brighter(image, factor=1.10):
    return ImageEnhance.Brightness(image).enhance(factor)


def resized(image, scale=0.82):
    size = (int(image.width * scale), int(image.height * scale))
    return image.resize(size, Image.LANCZOS)


def recompressed(image):
    """模拟通过社交软件转发后再次保存的压缩损失。"""
    import io
    buf = io.BytesIO()
    image.save(buf, "JPEG", quality=45)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def cropped(image, ratio=0.05):
    dx = int(image.width * ratio)
    dy = int(image.height * ratio)
    box = (dx, dy, image.width - dx, image.height - dy)
    return image.crop(box).resize((image.width, image.height), Image.LANCZOS)


# ---------------------------------------------------------------------------
# 组装演示目录
# ---------------------------------------------------------------------------

def build(output: Path, clean: bool):
    if clean and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    lake = landscape(11, sky=((132, 176, 205), (238, 226, 208)),
                     water=(96, 128, 140), ridge=(74, 96, 102), sun_xy=(0.74, 0.20))
    ridge = landscape(27, sky=((226, 168, 118), (250, 226, 186)),
                      water=(150, 118, 96), ridge=(96, 76, 66), sun_xy=(0.24, 0.30))
    flowers = landscape(43, sky=((172, 205, 214), (242, 238, 214)),
                        water=(122, 152, 108), ridge=(96, 128, 88), sun_xy=(0.55, 0.16))
    portrait = indoor_portrait(61)
    dinner = table_top(77)
    cake = table_top(95, table=(206, 178, 190),
                     food_colors=((244, 214, 222), (250, 240, 230), (226, 168, 178)))
    shot_a = screenshot(101, sidebar_left=True, cards=3)
    shot_b = screenshot(139, sidebar_left=False, cards=2)

    t = "2024:05:%02d 1%d:%02d:00"

    plan = [
        # 2023 春游：一组连拍（同一场景不同曝光）
        ("2023春游/湖面_日出.jpg", lake, 88, t % (6, 2, 14)),
        ("2023春游/湖面_日出_调亮.jpg", brighter(lake, 1.12), 88, t % (6, 2, 15)),
        ("2023春游/湖面_日出_旧手机.jpg", recompressed(resized(lake, 0.78)), 88, t % (6, 2, 16)),
        ("2023春游/山脊_逆光.jpg", ridge, 88, t % (6, 2, 40)),
        ("2023春游/野花_近景.jpg", flowers, 88, t % (6, 2, 52)),

        # 2024 婚礼：合影被存了三份
        ("2024婚礼/合影_原图.jpg", portrait, 92, t % (12, 1, 30)),
        ("2024婚礼/餐桌_俯拍.jpg", dinner, 90, t % (12, 2, 5)),
        ("2024婚礼/蛋糕_特写.jpg", cake, 90, t % (12, 2, 12)),

        # 截图：同一界面两张，尺寸不同
        ("截图/控制台_全屏.png", shot_a, 88, t % (18, 1, 9)),
        ("截图/控制台_全屏_缩放.png", resized(shot_a, 0.72), 88, t % (18, 1, 10)),
        ("截图/报表页.png", shot_b, 88, t % (18, 1, 22)),
    ]

    written = []
    for rel, image, quality, exif_time in plan:
        written.append(save(image, output / rel, quality, exif_time))

    # 完全重复：内容逐字节一致，只是路径和文件名不同
    dup_sources = [
        ("2024婚礼/合影_原图.jpg", "重复备份/合影_原图 - 副本.jpg"),
        ("2023春游/湖面_日出.jpg", "重复备份/湖面_日出(1).jpg"),
        ("2023春游/山脊_逆光.jpg", "重复备份/山脊_逆光_备份.jpg"),
        ("截图/控制台_全屏.png", "重复备份/控制台_全屏 - 副本.png"),
    ]
    for src, dst in dup_sources:
        (output / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output / src, output / dst)
        written.append(output / dst)

    # 不应被扫描的杂项文件
    (output / "说明.txt").write_text(
        "本目录用于 MediaOrganizer-Pro 演示：\n"
        "1. 所有图片均为程序生成的测试图，不含任何真实个人照片。\n"
        "2. 重复备份/ 下是刻意复制的完全重复文件，用于演示 SHA-256 检测。\n"
        "3. 部分图片是同一张图的调亮、缩放或二次压缩版本，用于演示 pHash 相似检测。\n",
        encoding="utf-8",
    )
    (output / "临时文件.tmp").write_bytes(b"not a media file")
    return sorted(written)


def main():
    parser = argparse.ArgumentParser(description="生成演示用测试图片与文件夹")
    parser.add_argument("--output", default="../demo-media", help="输出目录")
    parser.add_argument("--clean", action="store_true", help="先删除已有目录")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    output = (base / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    files = build(output, args.clean)

    total = sum(p.stat().st_size for p in files)
    print(f"输出目录：{output}")
    print(f"图片 {len(files)} 个，合计 {total / 1024 / 1024:.1f} MB")
    for p in files:
        print("  ", p.relative_to(output), f"{p.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
