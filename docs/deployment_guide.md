# GitHub API Service - デプロイメントガイド

## 目次
1. [前提条件](#前提条件)
2. [ローカル開発環境](#ローカル開発環境)
3. [本番環境デプロイ](#本番環境デプロイ)
4. [Dockerデプロイ](#dockerデプロイ)
5. [クラウドデプロイ](#クラウドデプロイ)
6. [監視とログ](#監視とログ)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なソフトウェア

| ソフトウェア | バージョン | 用途 |
|------------|----------|------|
| Python | 3.9以上 | アプリケーション実行 |
| pip | 最新版 | パッケージ管理 |
| Git | 2.0以上 | ソースコード管理 |
| curl | - | 動作確認 |

### GitHub要件

- GitHubアカウント
- Personal Access Token（repo権限）
- 対象リポジトリへのアクセス権限

---

## ローカル開発環境

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/github-api-script.git
cd github-api-script/python
```

### 2. Python仮想環境の作成

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルを作成:

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```env
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_OWNER=your-username-or-org
```

### 5. アプリケーションの起動

#### 開発モード（ホットリロード有効）
```bash
uvicorn main:app --reload
```

#### カスタムポート指定
```bash
uvicorn main:app --reload --port 8080
```

#### 外部アクセス許可
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/

# APIドキュメント
# ブラウザで http://localhost:8000/docs にアクセス
```

---

## 本番環境デプロイ

### Ubuntu/Debian サーバー

#### 1. システム準備

```bash
# システムアップデート
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y python3 python3-pip python3-venv git nginx
```

#### 2. アプリケーションのセットアップ

```bash
# アプリケーション用ユーザーの作成
sudo useradd -m -s /bin/bash github-api

# アプリケーションディレクトリ
sudo mkdir -p /opt/github-api-service
sudo chown github-api:github-api /opt/github-api-service

# ユーザーを切り替え
sudo su - github-api

# リポジトリクローン
cd /opt/github-api-service
git clone https://github.com/your-org/github-api-script.git .
cd python

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

#### 3. 環境変数の設定

```bash
# .envファイルの作成
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_OWNER=your-username-or-org
EOF

# ファイル権限の設定
chmod 600 .env
```

#### 4. systemdサービスの作成

```bash
# rootユーザーに戻る
exit

# サービスファイルの作成
sudo tee /etc/systemd/system/github-api.service > /dev/null << 'EOF'
[Unit]
Description=GitHub API Service
After=network.target

[Service]
Type=notify
User=github-api
Group=github-api
WorkingDirectory=/opt/github-api-service/python
Environment="PATH=/opt/github-api-service/python/venv/bin"
EnvironmentFile=/opt/github-api-service/python/.env
ExecStart=/opt/github-api-service/python/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4

# セキュリティ設定
PrivateTmp=true
NoNewPrivileges=true

# リソース制限
LimitNOFILE=65536

# 再起動設定
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# サービスの有効化と起動
sudo systemctl daemon-reload
sudo systemctl enable github-api.service
sudo systemctl start github-api.service

# ステータス確認
sudo systemctl status github-api.service
```

#### 5. Nginxリバースプロキシの設定

```bash
# Nginx設定ファイルの作成
sudo tee /etc/nginx/sites-available/github-api << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;

    # HTTPからHTTPSへリダイレクト（SSL設定後に有効化）
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # バッファ設定
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # アクセスログ
    access_log /var/log/nginx/github-api-access.log;
    error_log /var/log/nginx/github-api-error.log;
}
EOF

# シンボリックリンクの作成
sudo ln -s /etc/nginx/sites-available/github-api /etc/nginx/sites-enabled/

# デフォルト設定の無効化（必要に応じて）
sudo rm /etc/nginx/sites-enabled/default

# 設定テスト
sudo nginx -t

# Nginxの再起動
sudo systemctl restart nginx
```

#### 6. SSL/TLS設定（Let's Encrypt）

```bash
# Certbotのインストール
sudo apt install -y certbot python3-certbot-nginx

# SSL証明書の取得と設定
sudo certbot --nginx -d api.yourdomain.com

# 自動更新の確認
sudo certbot renew --dry-run
```

#### 7. ファイアウォール設定

```bash
# UFWのインストール（未インストールの場合）
sudo apt install -y ufw

# ファイアウォール設定
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# ファイアウォールの有効化
sudo ufw enable

# ステータス確認
sudo ufw status
```

### CentOS/RHEL サーバー

基本的な手順はUbuntu/Debianと同様ですが、以下の違いがあります:

```bash
# パッケージマネージャー
sudo yum install -y python3 python3-pip nginx

# ファイアウォール
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# SELinux設定（必要に応じて）
sudo setsebool -P httpd_can_network_connect 1
```

---

## Dockerデプロイ

### 1. Dockerfileの作成

`python/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存パッケージのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY main.py .

# 非rootユーザーの作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. .dockerignoreの作成

`python/.dockerignore`:

```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.git/
.gitignore
*.md
docs/
```

### 3. Dockerイメージのビルド

```bash
cd python
docker build -t github-api-service:latest .
```

### 4. Dockerコンテナの実行

```bash
# 基本的な実行
docker run -d \
  --name github-api \
  -p 8000:8000 \
  --env-file .env \
  github-api-service:latest

# リソース制限付き実行
docker run -d \
  --name github-api \
  -p 8000:8000 \
  --env-file .env \
  --memory="512m" \
  --cpus="1.0" \
  --restart unless-stopped \
  github-api-service:latest

# ログの確認
docker logs github-api

# コンテナの停止
docker stop github-api

# コンテナの削除
docker rm github-api
```

### 5. Docker Composeの使用

`python/docker-compose.yml`:

```yaml
version: '3.8'

services:
  github-api:
    build: .
    image: github-api-service:latest
    container_name: github-api
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    container_name: github-api-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - github-api
    restart: unless-stopped
```

起動:

```bash
docker-compose up -d

# ログの確認
docker-compose logs -f

# 停止
docker-compose down
```

---

## クラウドデプロイ

### AWS (Elastic Beanstalk)

#### 1. EB CLIのインストール

```bash
pip install awsebcli
```

#### 2. アプリケーションの初期化

```bash
cd python
eb init -p python-3.11 github-api-service --region us-east-1
```

#### 3. 環境の作成

```bash
eb create github-api-production
```

#### 4. 環境変数の設定

```bash
eb setenv GITHUB_TOKEN=ghp_xxx GITHUB_OWNER=your-username
```

#### 5. デプロイ

```bash
eb deploy
```

#### 6. アプリケーションのオープン

```bash
eb open
```

### AWS (ECS Fargate)

#### 1. ECRリポジトリの作成

```bash
aws ecr create-repository --repository-name github-api-service
```

#### 2. Dockerイメージのプッシュ

```bash
# ECRログイン
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# イメージのビルド
docker build -t github-api-service .

# タグ付け
docker tag github-api-service:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/github-api-service:latest

# プッシュ
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/github-api-service:latest
```

#### 3. タスク定義の作成

`task-definition.json`:

```json
{
  "family": "github-api-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "github-api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/github-api-service:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:github-token"
        },
        {
          "name": "GITHUB_OWNER",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:github-owner"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/github-api-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 4. サービスの作成

AWS Management ConsoleまたはCLIを使用してECSサービスを作成します。

### Google Cloud (Cloud Run)

#### 1. gcloud CLIの認証

```bash
gcloud auth login
gcloud config set project your-project-id
```

#### 2. Dockerイメージのビルドとプッシュ

```bash
# Cloud Buildを使用
gcloud builds submit --tag gcr.io/your-project-id/github-api-service

# またはローカルでビルドしてプッシュ
docker build -t gcr.io/your-project-id/github-api-service .
docker push gcr.io/your-project-id/github-api-service
```

#### 3. Cloud Runへのデプロイ

```bash
gcloud run deploy github-api-service \
  --image gcr.io/your-project-id/github-api-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GITHUB_TOKEN=ghp_xxx,GITHUB_OWNER=your-username \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

### Azure (App Service)

#### 1. Azure CLIの認証

```bash
az login
```

#### 2. リソースグループの作成

```bash
az group create --name github-api-rg --location eastus
```

#### 3. App Service Planの作成

```bash
az appservice plan create \
  --name github-api-plan \
  --resource-group github-api-rg \
  --sku B1 \
  --is-linux
```

#### 4. Web Appの作成

```bash
az webapp create \
  --resource-group github-api-rg \
  --plan github-api-plan \
  --name github-api-service \
  --runtime "PYTHON:3.11"
```

#### 5. 環境変数の設定

```bash
az webapp config appsettings set \
  --resource-group github-api-rg \
  --name github-api-service \
  --settings GITHUB_TOKEN=ghp_xxx GITHUB_OWNER=your-username
```

#### 6. コードのデプロイ

```bash
az webapp up \
  --resource-group github-api-rg \
  --name github-api-service \
  --runtime "PYTHON:3.11"
```

### Heroku

#### 1. Heroku CLIのインストールとログイン

```bash
heroku login
```

#### 2. アプリケーションの作成

```bash
cd python
heroku create github-api-service
```

#### 3. Procfileの作成

`Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 4. 環境変数の設定

```bash
heroku config:set GITHUB_TOKEN=ghp_xxx
heroku config:set GITHUB_OWNER=your-username
```

#### 5. デプロイ

```bash
git push heroku main
```

#### 6. アプリケーションのオープン

```bash
heroku open
```

---

## 監視とログ

### ログの確認

#### systemdサービス
```bash
# リアルタイムログ
sudo journalctl -u github-api.service -f

# 最近のログ
sudo journalctl -u github-api.service -n 100

# エラーのみ
sudo journalctl -u github-api.service -p err
```

#### Docker
```bash
# リアルタイムログ
docker logs -f github-api

# 最近のログ
docker logs --tail 100 github-api
```

### 監視の設定

#### Prometheus + Grafanaの使用

`docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. 環境変数が読み込まれない

**症状**: `GITHUB_TOKEN environment variable is not set`

**解決方法**:
```bash
# .envファイルの確認
cat .env

# systemdの場合、EnvironmentFileの確認
sudo systemctl cat github-api.service

# 再起動
sudo systemctl restart github-api.service
```

#### 2. ポートが既に使用されている

**症状**: `Address already in use`

**解決方法**:
```bash
# ポートを使用しているプロセスを確認
sudo lsof -i :8000

# プロセスを停止
sudo kill -9 <PID>
```

#### 3. GitHub API認証エラー

**症状**: `Failed to create issue: 401 Unauthorized`

**解決方法**:
- GitHub Tokenの有効期限を確認
- Token権限（repo）を確認
- Tokenを再生成

#### 4. パフォーマンスの問題

**解決方法**:
```bash
# Workerの数を増やす
uvicorn main:app --workers 8

# systemdの場合
# /etc/systemd/system/github-api.serviceを編集
ExecStart=.../uvicorn main:app --workers 8
```

#### 5. メモリ不足

**解決方法**:
```bash
# Dockerの場合、メモリ制限を増やす
docker run --memory="1g" ...

# システム全体のメモリを確認
free -h
```

### デバッグモードの有効化

```bash
# Uvicornのログレベルを変更
uvicorn main:app --log-level debug

# Pythonのログレベルを設定
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
python -m uvicorn main:app
```

### ヘルスチェック

```bash
# APIの動作確認
curl http://localhost:8000/

# 詳細なレスポンス確認
curl -v http://localhost:8000/
```

---

## セキュリティチェックリスト

- [ ] HTTPS（TLS 1.2以上）を使用
- [ ] 環境変数は.envファイルで管理（リポジトリにコミットしない）
- [ ] GitHub Tokenは最小権限で設定
- [ ] ファイアウォールを適切に設定
- [ ] 定期的なセキュリティアップデート
- [ ] アクセスログの監視
- [ ] レート制限の実装（推奨）

## パフォーマンスチューニング

### Workerの最適化

```bash
# CPUコア数に応じた設定
workers = (2 x CPU cores) + 1

# 例: 4コアの場合
uvicorn main:app --workers 9
```

### Connection Poolingの設定

main.pyに追加:

```python
import httpx

# グローバルクライアントの使用
client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
```

---

## バックアップとリカバリ

### 設定ファイルのバックアップ

```bash
# バックアップディレクトリの作成
mkdir -p ~/backups/github-api-service

# 設定ファイルのバックアップ
cp .env ~/backups/github-api-service/
cp /etc/systemd/system/github-api.service ~/backups/github-api-service/
cp /etc/nginx/sites-available/github-api ~/backups/github-api-service/
```

### リストア

```bash
# 設定ファイルのリストア
cp ~/backups/github-api-service/.env .
sudo cp ~/backups/github-api-service/github-api.service /etc/systemd/system/
sudo cp ~/backups/github-api-service/github-api /etc/nginx/sites-available/

# サービスの再起動
sudo systemctl daemon-reload
sudo systemctl restart github-api.service
sudo systemctl restart nginx
```

---

## まとめ

このガイドでは、GitHub API Serviceのさまざまなデプロイ方法を説明しました:

1. **ローカル開発**: 開発とテストに最適
2. **本番サーバー**: 完全なコントロールが必要な場合
3. **Docker**: コンテナ化と移植性
4. **クラウド**: スケーラビリティと管理の簡素化

環境に応じて適切なデプロイ方法を選択してください。
