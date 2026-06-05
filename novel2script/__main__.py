"""统一入口(双击 exe 默认启动 gui)"""
import sys


def main():
    if len(sys.argv) <= 1:
        # 双击 exe,无参数时默认启动 gui
        sys.argv.append("gui")

    from novel2script.cli import app

    app()


if __name__ == "__main__":
    main()
