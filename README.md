# iOS Header Dump

IPSW から ObjC ヘッダーをダンプして、ブラウザで検索・閲覧できる静的サイトを生成するツール。

## 必要なもの

```bash
brew install blacktop/tap/ipsw
```

## 使い方

### 1. ヘッダーをダンプ

```bash
make dump IPSW=~/Downloads/iPhone18,3_26.5_23F77_Restore.ipsw
```

`headers/26.5_23F77/` にフレームワークごとに `.h` ファイルが出力される。

### 2. ブラウザ用 HTML を生成

```bash
make site VERSION=26.5_23F77
```

`headers/26.5_23F77/index.html` が生成される。

### 3. ローカルサーバーで閲覧

```bash
make serve VERSION=26.5_23F77
# → http://localhost:8080/index.html をブラウザで開く
```

`VERSION` を省略すると最新の dumped headers を自動検出する。

### まとめて実行

```bash
make all IPSW=~/Downloads/iPhone18,3_26.5_23F77_Restore.ipsw VERSION=26.5_23F77
```

## 出力構造

```
headers/
└── 26.5_23F77/
    ├── index.html        ← 検索UIを含む静的HTML
    ├── UIKit/
    │   ├── UIView.h
    │   ├── UIViewController.h
    │   └── ...
    ├── Foundation/
    │   └── ...
    └── ...
```

## 機能

- フレームワーク一覧のサイドバー表示
- フレームワーク名・クラス名のリアルタイム検索
- ObjC シンタックスハイライト
- ヘッダーファイル内容のインラインビュー

## 注意

- `headers/` と `*.ipsw` は `.gitignore` に含まれているため、Git にはコミットされない
- ダンプには時間がかかる（dyld_shared_cache の展開 + 全クラスの解析）
- ディスク容量は数 GB 必要