import os
import sys
import subprocess
import time
import webbrowser

def main():
    # app.py のパスを取得
    if getattr(sys, 'frozen', False):
        # exe化された場合のパス
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "app.py")

    # バックグラウンドでStreamlitを起動
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless=true",
        "--global.developmentMode=false"
    ])

    # サーバー立ち上がりを待ってブラウザでアプリ画面を開く
    time.sleep(3)
    webbrowser.open("http://localhost:8501")

    # アプリプロセスを保持
    process.wait()

if __name__ == "__main__":
    main()