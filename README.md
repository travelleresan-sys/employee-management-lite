# Employee Management Lite

シンプルで使いやすいSaaS型従業員管理システム

## 主な機能

### SaaS管理者機能
- 企業登録・管理
- 契約管理（プラン、期間、料金設定）
- プラン管理（料金・上限の編集）
- システム全体の統計ダッシュボード

### 企業管理者機能
- 従業員管理（登録・編集・削除）
- 労働時間入力・管理
- 給与計算・明細発行
- 年次有給休暇管理（付与・取得状況）
- 契約プラン確認

## 技術スタック

- **Backend**: Python 3.12, Flask 3.1
- **Database**: SQLite (PostgreSQL対応可能)
- **Frontend**: Bootstrap 5, Jinja2
- **Authentication**: Flask-Login
- **Deployment**: Render

## レスポンシブデザイン

- モバイル、タブレット、デスクトップ完全対応
- タッチ操作最適化
- モバイルファーストUI

## セットアップ

### ローカル開発

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# データベース初期化
python init_db.py

# 起動
flask run
```

### デフォルトアカウント

**SaaS管理者:**
- Email: `saas_admin@example.com`
- Password: `admin123`

**テスト企業管理者:**
- Email: `admin@test-company.com`
- Password: `test123`

## デプロイ

Renderでのデプロイに対応しています。

## ライセンス

Proprietary
