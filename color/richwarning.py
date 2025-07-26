import warnings
import sys
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# 创建一个 Rich Console 实例，用于输出
console = Console(file=sys.stderr)  # 警告通常输出到 stderr


def custom_showwarning(message,
                       category,
                       filename,
                       lineno,
                       file=None,
                       line=None):
    """
    自定义的警告显示函数，使用 rich 进行格式化。
    """
    # 格式化警告信息
    warning_text = Text()
    warning_text.append(f"{category.__name__}: ", style="bold yellow")
    warning_text.append(str(message), style="yellow")
    warning_text.append(f"\n  File \"{filename}\", line {lineno}",
                        style="dim white")

    # 使用 Panel 包裹警告信息
    warning_panel = Panel(
        warning_text,
        title="[bold yellow blink]WARNING![/bold yellow blink]",  # 闪烁效果，吸引注意
        border_style="yellow",
        expand=False,
        padding=(1, 2)  # 内边距
    )

    # 将 Panel 打印到控制台
    console.print(warning_panel)


# 替换 warnings 模块的 showwarning 函数
warnings.showwarning = custom_showwarning
