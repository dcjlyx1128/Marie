"""生成一个用于演示/测试的凌乱文件夹: python examples/make_demo.py
图片会生成真实可被视觉模型识别的内容(需 pillow,缺失则降级为占位文件)。"""
from pathlib import Path

DEMO = Path(__file__).parent / "messy"

NON_IMAGE = {
    "invoice_march.pdf": "fake", "resume.docx": "fake", "budget.xlsx": "fake",
    "song.mp3": "fake", "movie.mp4": "fake", "archive.zip": "fake",
    "installer.dmg": "fake", "notes.txt": "今天的会议纪要:讨论了三季度计划。",
    "script.py": "print('hello')", "random.xyz": "fake",
}
# 文件名 -> (画面文字, 背景色)
IMAGES = {
    "photo_vacation.jpg": ("BEACH SUNSET PHOTO", (240, 160, 90)),
    "screenshot 2024.png": ("App Settings Screen", (60, 90, 140)),
}


def _make_image(path: Path, text: str, color):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (640, 400), color)
    ImageDraw.Draw(img).text((30, 180), text, fill="white")
    img.save(path)


def main():
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise SystemExit("需要 Pillow 才能生成演示图片,请先安装: pip install pillow")
    DEMO.mkdir(exist_ok=True)
    for name, content in NON_IMAGE.items():
        (DEMO / name).write_text(content)
    for name, (text, color) in IMAGES.items():
        _make_image(DEMO / name, text, color)
    print(f"已生成演示文件夹: {DEMO}  ({len(NON_IMAGE) + len(IMAGES)} 个文件)")


if __name__ == "__main__":
    main()
