# 機器情報可視化 仕様書

## 概要
機器データを可視化するWebアプリケーション。FastAPI + Jinja2 + Chart.js で構築。
エンジニアが数億件規模のデータを効率的に分析できるEDA（探索的データ分析）型ダッシュボードを提供。

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| バックエンド | Python FastAPI |
| テンプレートエンジン | Jinja2 |
| グラフ描画 | Chart.js + プラグイン（zoom, annotation, boxplot） |
| スタイリング | Vanilla CSS（ライトモードデザイン） |
| データベース | SQLAlchemy 2.0 + Alembic（SQLite/PostgreSQL/SQL Server） |
| 認証 | Cookieセッション + bcrypt |

---

## 環境設定

`.env` ファイルで環境を設定:

```bash
# アプリケーション設定
APP_ENV=development          # development / staging / production
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

# データベース設定
DATABASE_URL=sqlite:///./machine_viz.db

# データソース設定
USE_DUMMY_DATA=true          # true=ダミーデータ, false=データベース

# セキュリティ
SECRET_KEY=your-secret-key
LOG_LEVEL=DEBUG
```

---

## 認証・認可

### ログイン
- Cookieベースのセッション認証
- パスワードはbcryptでハッシュ化
- セッション有効期限: 7日間

### 管理者ユーザー作成
```bash
PYTHONPATH=. uv run python scripts/create_admin.py <username> <password>
```

### ページ保護
- 全ページ（ログイン画面を除く）は認証必須
- 未ログイン時はログイン画面にリダイレクト
- ナビゲーションバーにログアウトボタン

---

## 機能

### 1. トップ画面
- 各機能へのナビゲーションカード
- 対応データの概要表示

### 2. 機番検索
- **検索条件**:
  - 機種シリーズ（単一選択）
  - 機種番号（複数選択可能、チェックボックスリスト形式）
  - 製造月（From-To形式で範囲指定）
  - 稼働開始月（From-To形式で範囲指定）
- **結果表示**: 
  - 該当機番一覧をテーブル表示
  - ページネーション対応（デフォルト20件/ページ、20/50/100件から選択可）
  - 検索結果件数バッジ表示
- **ランダムサンプリング**: サンプリング数を指定して抽出
- **機番選択・操作**:
  - 全選択チェックボックス
  - 選択件数バッジ表示
  - 選択時のみアクションボタン（コピー、時系列表示へ、断面データ表示へ）が有効化
- **機番コピー**: 選択した機番をクリップボードにコピー可能
- **画面遷移**: 選択した機番を時系列表示・断面データ表示へ自動入力
- **UX機能**:
  - 検索中のローディングスピナー表示
  - エラー発生時のアラート表示

### 3. 時系列表示（EDA型ダッシュボード）
- **レイアウト**: 3エリア分割（左：条件設定、中央：可視化、下：詳細データ）
- **機番入力**: テキストエリアに機番をカンマまたは改行区切りで入力（最大5台）
- **多変量表示**:
  - 最大2変数まで追加可能（左軸・右軸各1つ）
  - 変数ごとにカテゴリー・特性値ID・集計方法を選択
  - 自動的に1つ目は左軸、2つ目は右軸に配置
- **X軸タイプ切り替え**:
  - 時間（月次）: 月ごとの推移
  - 使用回数: 0〜1100の使用回数ベース
- **Brush & Zoom**:
  - メインチャートの上に概要チャート（全期間表示）
  - マウスホイールでズーム、ドラッグでパン操作
  - ズームリセットボタン、現在の表示期間を表示
- **アノテーション**:
  - イベント情報（FW更新、部品交換、メンテナンス、エラー発生）を縦線で表示
  - チェックボックスでアノテーション表示/非表示切替
  - 使用回数モードではアノテーション非表示
  - 複数機番選択時は機番ラベル表示
- **URL状態管理**:
  - 選択中の期間・フィルタ条件・表示変数をURLパラメータに自動反映
  - 「URLをコピー」ボタンで分析状態を即座に共有可能
  - URLアクセス時に自動でグラフ表示
- **表形式表示への遷移**: グラフデータを表形式で確認可能

### 4. 断面データ表示（EDA型ダッシュボード）
- **レイアウト**: 3エリア分割（左：条件設定、中央：可視化、下：詳細データ）
- **基本条件**: 機種シリーズ、機種番号、対象月を選択
- **特性値条件**: データカテゴリー、特性値ID、集計方法を選択
- **チャート種別タブ**:
  - **ヒストグラム**: 値の分布を棒グラフで表示（相対頻度表示対応）
  - **散布図**: 2変数の相関を可視化、相関係数を自動表示
  - **箱ひげ図**: 機種ごとの分布（中央値、四分位範囲）を比較
- **グループ比較**: 比較対象の機番をテキストエリアで入力し、選択機番群とその他機番群で比較可能
- **URL状態管理**: 
  - チャート種別・フィルタ条件をURLパラメータに反映
  - URLアクセス時に自動でグラフ表示
- **表形式表示への遷移**: グラフデータを表形式で確認可能

### 5. 表形式表示
- 時系列データまたは断面データをテーブル形式で表示
- **CSVエクスポート**: データをCSVファイルとしてダウンロード

---

## データベース設計

### ER図
```
Series (1) ─── (N) Model (1) ─── (N) Machine
Category (1) ─── (N) Characteristic
Machine (1) ─── (N) MachineData
Machine (1) ─── (N) Annotation
User（認証用）
```

### テーブル一覧
| テーブル | 説明 |
|---------|------|
| series | 機種シリーズ |
| models | 機種番号 |
| machines | 機番 |
| categories | データカテゴリー |
| characteristics | 特性値ID |
| aggregations | 集計方法 |
| machine_data | 機番データ（時系列） |
| annotations | アノテーション |
| users | ユーザー（認証用） |

---

## ファイル構成

```
machine-viz/
├── app/
│   ├── main.py              # FastAPIアプリ
│   ├── config.py            # 環境設定
│   ├── database.py          # DB接続設定
│   ├── exceptions.py        # カスタム例外
│   ├── error_handlers.py    # エラーハンドラー
│   ├── auth/                # 認証モジュール
│   │   ├── service.py       # 認証サービス
│   │   └── dependencies.py  # FastAPI依存性
│   ├── models/              # SQLAlchemyモデル
│   │   ├── base.py          # 機器関連モデル
│   │   └── user.py          # ユーザーモデル
│   ├── routers/
│   │   ├── api.py           # APIエンドポイント
│   │   ├── auth.py          # 認証API
│   │   └── pages.py         # ページルーティング
│   ├── data/
│   │   ├── dummy.py         # ダミーデータ生成
│   │   ├── annotations.py   # アノテーションデータ
│   │   ├── repository.py    # DBリポジトリ
│   │   └── data_service.py  # データサービス（dummy/DB切り替え）
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── index.html
│   │   ├── search.html
│   │   ├── timeseries.html
│   │   ├── histogram.html
│   │   └── table.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── migrations/              # Alembicマイグレーション
├── scripts/
│   ├── seed_data.py         # 初期データ投入
│   └── create_admin.py      # 管理者作成
├── .env                     # 環境設定
├── .env.example             # 環境設定テンプレート
├── pyproject.toml
└── README.md
```

---

## APIエンドポイント

### 認証
- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `GET /api/auth/me` - 現在のユーザー取得

### マスタデータ
- `GET /api/series` - シリーズ一覧
- `GET /api/models/{series}` - 機種番号一覧
- `GET /api/categories` - データカテゴリー一覧
- `GET /api/characteristics/{category}` - 特性値ID一覧
- `GET /api/aggregations` - 集計方法一覧
- `GET /api/months` - 利用可能月一覧
- `GET /api/annotation-types` - アノテーションタイプ一覧

### 検索・データ取得
- `POST /api/search` - 機番検索
- `POST /api/sample` - ランダムサンプリング
- `POST /api/timeseries` - 時系列データ取得
- `POST /api/timeseries/multi` - 多変量時系列データ取得
- `POST /api/histogram` - ヒストグラムデータ取得
- `POST /api/scatter` - 散布図データ取得
- `POST /api/boxplot` - 箱ひげ図データ取得
- `POST /api/annotations` - アノテーションデータ取得

---

## 起動方法

### 開発環境
```bash
cd /path/to/machine-viz
source .venv/bin/activate

# 依存関係インストール
uv sync

# マイグレーション実行
uv run alembic upgrade head

# 初期データ投入（オプション）
PYTHONPATH=. uv run python scripts/seed_data.py

# 管理者ユーザー作成
PYTHONPATH=. uv run python scripts/create_admin.py admin password123

# サーバー起動
uv run uvicorn app.main:app --reload --port 8000
```

アクセス: http://127.0.0.1:8000

### 本番環境
```bash
# 環境変数設定
APP_ENV=production
USE_DUMMY_DATA=false
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=<secure-random-key>

# サーバー起動（Gunicorn推奨）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```