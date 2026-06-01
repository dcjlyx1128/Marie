"""生成一个用于演示/测试的凌乱文件夹: python examples/make_demo.py"""
from pathlib import Path

DEMO = Path(__file__).parent / "messy"
SAMPLES = {
    "photo_vacation.jpg": "fake", "screenshot 2024.png": "fake",
    "invoice_march.pdf": "fake", "resume.docx": "fake",
    "budget.xlsx": "fake", "song.mp3": "fake", "movie.mp4": "fake",
    "archive.zip": "fake", "installer.dmg": "fake",
    "notes.txt": "hello world", "script.py": "print(1)", "random.xyz": "fake",
}


def main():
    DEMO.mkdir(exist_ok=True)
    for name, content in SAMPLES.items():
        (DEMO / name).write_text(content)
    print(f"已生成演示文件夹: {DEMO}  ({len(SAMPLES)} 个文件)")


if __name__ == "__main__":
    main()
