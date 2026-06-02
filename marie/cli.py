from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .executor import execute, undo
from .planner import plan
from .scanner import scan

app = typer.Typer(help="Marie — 用 AI 整理任何文件夹", add_completion=False)
console = Console()


@app.command()
def organize(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, help="要整理的文件夹"),
    apply: bool = typer.Option(False, "--apply", help="真正执行(默认仅预览 dry-run)"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="递归子文件夹"),
    ai: bool = typer.Option(False, "--ai", help="用 LLM 细分模糊文件(阶段2 起生效)"),
    rule: str = typer.Option("", "--rule", help="自然语言整理规则(自动启用 --ai)"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="指定配置文件路径"),
):
    """扫描并整理文件夹。默认只预览,加 --apply 执行。"""
    from .config import load_config
    from .pipeline import category_dirs, decide_all

    config = load_config(folder, config_path)
    files = scan(folder, recursive, category_dirs(config))
    if not files:
        console.print("[yellow]没有可整理的文件。[/]")
        raise typer.Exit()

    use_ai = ai or bool(rule)
    if use_ai:
        with console.status("[cyan]AI 分析模糊文件中…[/]"):
            decisions = decide_all(files, config, use_ai=True, rule=rule)
    else:
        decisions = decide_all(files, config)
    actions = plan(files, folder, lambda f: decisions[f.path])
    table = Table(title=f"整理预览:{folder}  (共 {len(actions)} 个文件)")
    table.add_column("文件", style="cyan", overflow="fold")
    table.add_column("分类", style="magenta")
    table.add_column("移动到", style="green", overflow="fold")
    for a in actions:
        table.add_row(a.src.name, a.category, str(a.dest.relative_to(folder)))
    console.print(table)

    if apply:
        n = execute(actions, folder)
        console.print(f"[green]✓ 已整理 {n} 个文件。撤销:[bold]marie undo {folder}[/][/]")
    else:
        console.print("[dim]这是预览(dry-run)。确认无误后加 [bold]--apply[/] 执行。[/]")


@app.command()
def init(folder: Path = typer.Argument(Path("."), file_okay=False, help="在哪个目录生成配置")):
    """生成默认配置文件 marie.yaml。"""
    from .config import CONFIG_NAME, init_config

    target = folder / CONFIG_NAME
    try:
        init_config(target)
        console.print(f"[green]✓ 已生成配置:[bold]{target}[/]。编辑它来自定义分类体系。[/]")
    except FileExistsError:
        console.print(f"[yellow]配置已存在,未覆盖:{target}[/]")


@app.command("undo")
def undo_cmd(folder: Path = typer.Argument(..., exists=True, file_okay=False)):
    """撤销上一次整理。"""
    n = undo(folder)
    msg = f"[green]✓ 已撤销 {n} 个文件的移动。[/]" if n else "[yellow]没有可撤销的记录。[/]"
    console.print(msg)


if __name__ == "__main__":
    app()
