import subprocess
import sys

TASKS = [
    ([sys.executable, "Dhan-Scanx-News.ps1"], "dhan scanx feed"),
    ([sys.executable, "marketsmojo_rss.py"], "marketsmojo feed"),
]

def run_task(cmd, name):
    try:
        subprocess.run(cmd, check=True, timeout=90)
        print("OK:", name)
        return True
    except subprocess.TimeoutExpired as e:
        print("FAILED:", name, "=> timeout:", e)
        return False
    except subprocess.CalledProcessError as e:
        print("FAILED:", name, "=> exit code:", e.returncode)
        return False
    except FileNotFoundError as e:
        print("FAILED:", name, "=> file not found:", e)
        return False
    except Exception as e:
        print("FAILED:", name, "=>", e)
        return False

def main():
    ok = True
    for cmd, name in TASKS:
        ok = run_task(cmd, name) and ok

    # Optional: if you want GitHub Actions to still succeed even when one feed fails,
    # keep exit code 0 always. If you want Actions to fail when any feed fails,
    # uncomment the next 2 lines.
    # if not ok:
    #     raise SystemExit(1)

if __name__ == "__main__":
    main()
