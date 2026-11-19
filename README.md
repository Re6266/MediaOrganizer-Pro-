# MediaOrganizer-Pro

面向个人本地媒体库的媒体索引、重复与相似图片识别、照片组管理工具。

## 当前功能

- 扫描指定文件夹中的常见图片和视频，读取基础元数据并建立本地 SQLite 索引。
- 生成缩略图，展示媒体列表和文件详情；扫描不会移动或改写原始文件。
- 使用 SHA-256 识别完全重复文件，使用 pHash 识别视觉相似图片并形成候选组。
- 在“重复检测”页面设置相似判定阈值，一键检测并把结果保存到数据库。
- 在“媒体浏览与照片组”页面按文件名、类型、路径和日期筛选媒体，展开查看详情与大图。
- 查看已保存的重复和相似候选组，勾选成员后复制为可编辑的人工照片组。
- 新建人工照片组，为照片组添加或移除成员。

AI 最佳瞬间合成、结果来源追踪和安全整理仍在后续计划中，当前版本不会删除、移动或覆盖原始媒体文件。

## 运行方式

建议使用 Python 3.10 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开终端显示的本地地址后，可从侧边栏进入：

- 本地媒体扫描
- 重复检测
- 媒体浏览与照片组

## 界面与设计原型

界面视觉沿用小组交互原型（仓库外 `prototype/` 目录）的立体主义风格：米色画布、深褐墨色、2px 硬边框与偏移阴影、零圆角。实现方式为 `modules/ui_theme.py` 注入 CSS 与页面头组件，只改样式层，不改数据流与页面结构，因此不影响八周计划中的技术栈与分工。

原型本身是纯静态演示（12 个素材、浏览器 localStorage、不读写真实文件），仅作设计参考，不作为运行版本；真实功能由本仓库的 Streamlit 应用承担。

## 测试

```powershell
python -m unittest discover -s tests -p "test_week3.py" -v
python -m unittest discover -s tests -p "test_week4.py" -v
```

## 目录说明

```text
app.py                         Streamlit 首页入口
pages/                         各功能页面
modules/                       扫描、元数据、检测、媒体库与界面主题模块
database.py                    SQLite 初始化与基础数据访问
tests/                         自动化测试
weekly-report/                 周报
```
