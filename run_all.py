import subprocess
import sys

TASKS = [
    ([sys.executable, "dhan_scanx_news.py"], "dhan scanx api"),
    ([sys.executable, "buzzing_stocks.py"], "moneycontrol buzzing"),
    ([sys.executable, "marketsmojo_news.py"], "marketsmojo news"),
]

def main():
    for cmd, name in TASKS:
        try:
            # check=True makes Python raise an error if the script exits non-zero,
            # and timeout prevents hanging forever. [web:22]
            subprocess.run(cmd, check=True, timeout=90)  # [web:22]
            print("OK:", name)
        except Exception as e:
            print("FAILED:", name, "=>", e)

if __name__ == "__main__":
    main()
