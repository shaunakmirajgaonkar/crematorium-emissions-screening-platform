from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent
if __name__=="__main__":
    print("Starting EmberGuard — Crematorium Emissions Screening Platform")
    print("Open http://localhost:8501")
    subprocess.run([sys.executable,"-m","streamlit","run",str(ROOT/"app.py")],check=False)
