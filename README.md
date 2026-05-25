# iOS Header Dump

IPSW から ObjC ヘッダーをダンプして、ブラウザで検索・閲覧できる静的サイトを生成するツール。  
新しい iOS バージョンが出たら GitHub Actions が検知し、PR で差分を確認できる。

## 必要なもの

```bash
brew install blacktop/tap/ipsw
```

## ローカルでの使い方

### ヘッダーをダンプして閲覧

```bash
make dump IPSW=~/Downloads/iPhone18,3_26.5_23F77_Restore.ipsw
make site
make serve
# → http://localhost:8080/index.html
```

## GitHub Actions による自動化

### 仕組み

| ワークフロー | トリガー | ランナー | 役割 |
|---|---|---|---|
| `check-ios-version` | 毎日 17:00 JST | ubuntu (GitHub 管理) | 新バージョンを検知して Issue を作成 |
| `dump-headers` | 手動 / Issue 後に実行 | **self-hosted (あなたの Mac)** | IPSW をダウンロードしてヘッダーを dump、PR を作成 |

### セルフホストランナーのセットアップ（初回のみ）

GitHub のホステッドランナーは IPSW (11GB+) + DSC 展開のディスクが足りないため、  
ローカルの Mac をランナーとして登録する。

**1. ランナーを登録**

このリポジトリの Settings → Actions → Runners → **New self-hosted runner** を開き、  
macOS の手順に従って `actions-runner` をインストールする。

**2. サービスとして常駐させる**

```bash
cd ~/actions-runner
./svc.sh install
./svc.sh start
```

これで Mac がスリープから復帰するたびに自動起動する。

**3. ラベルを作成（初回のみ）**

```bash
gh label create "new-ios-version" --color "0075ca" --description "New iOS version detected"
gh label create "ios-headers" --color "e4e669" --description "iOS header diff"
```

### 新バージョンが出たときのフロー

1. `check-ios-version` が毎日動いて新バージョンを検知 → **Issue が自動作成される**
2. Mac のランナーが起動していることを確認
3. Issue に書かれたコマンド or GitHub UI から `dump-headers` を実行

   ```bash
   gh workflow run dump-headers.yml \
     -f device=iPhone18,3 \
     -f build=24B81
   ```

4. ワークフローが完了すると **PR が自動作成される**
5. PR の Files changed でヘッダーの差分を確認

### 追跡するデバイスの変更

`.github/workflows/check-ios-version.yml` の `env.DEVICE` を変更する：

```yaml
env:
  DEVICE: iPhone18,3  # ← ここを変更 (例: iPhone18,4 = iPhone 17 Pro Max)
```

## 出力構造

```
headers/
  version.txt        ← "iOS 26.5 (23F77)"
  UIKitCore/
    UIView.h         ← 変更があれば PR の diff に出る
  Foundation/
    ...
  (3,364 フレームワーク / 288,370 ヘッダー)
```

## 注意

- `headers/index.html` と `*.ipsw` は `.gitignore` で除外
- ダンプには 20〜30 分かかる（ipsw class-dump --all）
- Mac に 30GB 以上の空き容量が必要