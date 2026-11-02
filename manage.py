import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_check.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            '找不到 Django，请先激活虚拟环境并安装 requirements.txt 中的依赖。'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
