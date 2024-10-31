import sys
import os

# モジュール検索パスを表示
print("Current sys.path:", sys.path)

# `__init__.py` ファイルが存在するディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)