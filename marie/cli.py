from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .classifier import classify
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
    ai: bool = typer.Option(False, "--ai", help="用 LLM 读内容智能分类+重命名"),
    rule: str = typer.Option("", "--rule", help="自然语言整理规则(自动启用 --ai)"),
):
    """扫描并整理文件夹。默认只预览,加 --apply 执行。"""
    files = scan(folder, recursive)
    if not files:
        console.print("[yellow]没有可整理的文件。[/]")
        raise typer.Exit()

    decide = None
    if ai or rule:
        from .llm import classify_files

        with console.status("[cyan]AI 分析文件中…[/]"):
            decisions = classify_files(files, rule)
        decide = lambda f: decisions.get(f.path, (classify(f), f.name))

    actions = plan(files, folder, decide)
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
