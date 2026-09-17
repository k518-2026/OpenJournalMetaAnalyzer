# 🔬 OpenJournalMetaAnalyzer (Web & GitHub Pages)

[![GitHub Pages Deployment](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/pages.yml/badge.svg)](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/pages.yml)
[![CI](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/ci.yml)
[![PRISMA 2020 Compliant](https://img.shields.io/badge/PRISMA-2020%20Compliant-emerald.svg)](https://www.prisma-statement.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🌐 **Webアクセス対応システム**: ローカルサーバーの起動は不要です。インターネット上のブラウザからURLを開くだけで、世界中どこからでもPC・タブレット・スマートフォンでメタ分析を実行できます！
>
> 🚀 **Live Web App URL**: **`https://k518-2026.github.io/OpenJournalMetaAnalyzer/`**

---

## 📖 システム概要

キーワードを入力するだけで、海外の主要オープンアクセスジャーナル（OpenAlex、Europe PMC / PubMed Central等）から学術論文を自動検索し、**PRISMA 2020声明**に準拠した選定フロー図（Flow Diagram）の自動構築、固定効果・変量効果モデルによる統計的統合効果量の算出、インタラクティブな**フォレストプロット（Forest Plot）**の可視化、そしてエビデンス統合レポートの自動生成を一気通貫で行うWebアプリケーションです。

ローカルサーバーを起動する必要がなく、**GitHub Pages 上で静的Webアプリとして完全自律稼働（無料・無停止）**します。

---

## 🌟 主な機能 (Features)

### 1. 🔍 海外オープンジャーナル一括検索 (PRISMA: Identification)
- **世界2.5億件のオープンアクセス論文**: OpenAlex API を通じて完全オープンアクセス（Gold/Green/Bronze OA）の論文のみを抽出。
- **学術メタデータ取得**: タイトル、著者、出版年、ジャーナル名、DOI、オープンアクセスURL、PDF直接ダウンロードURL、被引用数を瞬時に取得。
- **高精度な重複排除**: DOI正規化およびタイトル類似度マッチングにより、複数リポジトリ間で重複する論文を自動除外・マージ。PRISMAの「重複除外レコード数」を自動記録。

### 2. 📋 PRISMA 2020 準拠 スクリーニング＆動的フロー図 (Screening & Eligibility)
- **PRISMA 2020 Flow Diagram**:
  - `Identification`（データベース検出数、重複除外数）
  - `Screening`（抄録スクリーニング数、除外理由別の除外数）
  - `Eligibility`（適格性精読評価数、除外判定数）
  - `Included`（定性統合採択数、定量的メタ分析採択数）
- **リアルタイム連動**: UI上の採用・除外トグルや除外理由（対象集団不一致、対照群欠如、非原著論文、データ不備など）の変更に応じて、**フロー図の数値が即座に連動更新**。

### 3. 📊 統計的メタ分析 & フォレストプロット (Quantitative Meta-Analysis)
- **効果量・信頼区間の自動抽出**: 抄録テキストからオッズ比（OR）、相対リスク（RR）、ハザード比（HR）、標準化平均差（SMD/Cohen's d）、平均差（MD）および95%信頼区間（95% CI）、サンプルサイズを自動抽出。
- **インライン編集マトリクス**: 抽出された数値はUI上のテーブルで自由に微調整・手動修正が可能。
- **本格的な統計モデル（JavaScript実装によりブラウザで完全動作）**:
  - **固定効果モデル (Fixed-Effect Model)**: 逆分散法（Inverse Variance method）
  - **変量効果モデル (Random-Effects Model)**: DerSimonian-Laird 法
- **異質性の統計的検定**: Cochran's $Q$ 検定、$p$値（不完全ガンマ関数級数展開による正確なカイ二乗分布検定）、$I^2$ 統計量（0〜100%）、研究間分散 $\tau^2$。
- **Plotly インタラクティブ・フォレストプロット**:
  - 各研究の点推定値・95%エラーバー・重み（Weight %）に応じたマーカーサイズ。
  - 固定効果モデルおよび変量効果モデルの「統合効果量ダイヤモンド（Summary Diamond）」を描画。
  - PNG画像ワンクリック保存対応。

### 4. 📝 PRISMA 2020 構造化エビデンス統合レポート (Qualitative Evidence Synthesis)
- PICOフレームワーク、採用研究特性表、知見の統合（合意点・不一致点）、バイアスリスク評価、GRADE確実性格付け、総合結論を自動編成。
- **ハイブリッド設計**: 内蔵NLPエンジン（APIキー不要・完全オフライン）と Gemini API（Gemini 2.5 Flash）のハイブリッド対応。

### 5. 📤 データ＆文献エクスポート (Export & Citation)
- **CSV**: Excel互換（BOM付きUTF-8）のメタ分析データセット。
- **BibTeX**: LaTeX / Zotero / Mendeley で直接読み込める文献引用ファイル。
- **PRISMAサマリーテキスト**: 論文執筆時にそのまま引用可能な選定フロー集計。

---

## 🌐 Webでの利用方法 (How to Use on the Web)

### 方法 1: GitHub Pages（推奨・即座に利用可能）
本リポジトリをGitHubにプッシュした後、リポジトリの設定で GitHub Pages を有効化するだけで、世界中にWeb公開されます：

1. GitHubリポジトリの **Settings** タブを開きます。
2. 左メニューの **Pages** をクリックします。
3. **Build and deployment** の Source で **GitHub Actions**（または `Deploy from a branch` $\rightarrow$ `main` / `docs`）を選択します。
4. 数十秒でデプロイが完了し、**`https://<あなたのGitHubユーザー名>.github.io/OpenJournalMetaAnalyzer/`** から誰でもWebアクセスできるようになります！

### 方法 2: クラウドサービス（Vercel / Render / Docker）
クラウド上にFastAPIバックエンドも含めて公開したい場合：
- **Vercel**: GitHubリポジトリを連携して「Import」するだけで自動デプロイ（`vercel.json` 完備）。
- **Render**: リポジトリを連携して「New Web Service」を作成（`render.yaml` 完備）。
- **Docker**: `docker build -t open-journal-meta-analyzer .` $\rightarrow$ `docker run -p 8000:8000 open-journal-meta-analyzer`

---

## 💻 ローカルでの実行方法 (オプション)

ローカルPCで動かしたい場合も、ワンクリックで起動可能です：
```bash
git clone https://github.com/k518-2026/OpenJournalMetaAnalyzer.git
cd OpenJournalMetaAnalyzer

pip install -r requirements.txt
python run.py
```

---

## 🧪 テストの実行

```bash
python -m pytest tests/ -v
```

---

## 📄 ライセンス

MIT License - 学術研究、教育、商用利用を含め自由にご利用いただけます。
