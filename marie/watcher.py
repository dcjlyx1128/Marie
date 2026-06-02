"""watch 自动整理:监听文件夹,新文件稳定后自动归类(只移不删,可 marie undo)。

核心处理逻辑(handle/_ignored/_stable)不依赖 watchdog,便于单测;
watch() 才用 watchdog 起观察者线程,前台运行。
"""
import time
from pathlib import Path

from .executor import execute
from .models import FileInfo
from .pipeline import archive_root, category_dirs, decide_all
from .planner import plan
from .config import CONFIG_NAME


def _ignored(path: Path, config) -> bool:
    """隐藏文件、配置文件、下载中的临时后缀:忽略。"""
    return path.name.startswith(".") or path.name == CONFIG_NAME or path.suffix.lower() in config.watch_ignore


def _in_skip(path: Path, folder: Path, skip) -> bool:
    """已位于某个分类目录下(已整理过):忽略。"""
    try:
        rel = path.relative_to(folder)
    except ValueError:
        return False
    return len(rel.parts) > 1 and rel.parts[0] in skip


def _stable(path: Path, debounce: float) -> bool:
    """文件大小经过 debounce 秒后保持不变,视为写入完成。"""
    try:
        s = path.stat().st_size
    except OSError:
        return False
    time.sleep(debounce)
    try:
        return path.is_file() and path.stat().st_size == s
    except OSError:
        return False


def handle(path: Path, folder: Path, config):
    """处理单个文件:决策 → 移动到归档根目录 → 追加 undo 日志(写在 folder)。返回 dest;无动作返回 None。"""
    path = Path(path)
    st = path.stat()
    f = FileInfo(path, st.st_size, st.st_mtime)
    cat, new_name = decide_all([f], config, use_ai=config.ai_fallback)[path]
    actions = plan([f], archive_root(folder, config), lambda _f: (cat, new_name))
    if not actions:
        return None
    execute(actions, folder, append=True)
    return actions[0].dest


def watch(folder: Path, config, log=print):
    """前台监听 folder,新文件稳定后自动归类。Ctrl-C 停止。"""
    import threading

    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    folder, skip = Path(folder).resolve(), category_dirs(config)
    base = archive_root(folder, config)
    lock = threading.Lock()

    class _Handler(FileSystemEventHandler):
        def on_created(self, e):
            if not e.is_directory:
                self._go(Path(e.src_path))

        def on_moved(self, e):
            if not e.is_directory:
                self._go(Path(e.dest_path))

        def _go(self, path):
            path = Path(path).resolve()  # FSEvents 路径已规范化(如 /var→/private/var),folder 也规范化以对齐
            if _ignored(path, config) or _in_skip(path, folder, skip):
                return
            with lock:  # 串行处理:规避同一文件的重复/并发事件(如 cp 同时触发 created+moved)造成重复搬动
                if not _stable(path, config.watch_debounce):
                    return
                try:
                    dest = handle(path, folder, config)
                except Exception as ex:
                    log(f"[red]处理失败 {path.name}: {ex}[/]")
                    return
            if dest:
                try:
                    rel = dest.relative_to(base)
                except ValueError:
                    rel = dest
                log(f"[green]✓ {path.name} → {rel}[/]")

    obs = Observer()
    obs.schedule(_Handler(), str(folder), recursive=False)
    obs.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        obs.stop()
        obs.join()
