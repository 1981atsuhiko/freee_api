import sys
import os

# `app` ディレクトリをモジュール検索パスに追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)