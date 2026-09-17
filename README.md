# 🔬 OpenJournalMetaAnalyzer

[![CI](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/k518-2026/OpenJournalMetaAnalyzer/actions/workflows/ci.yml)
[![PRISMA 2020 Compliant](https://img.shields.io/badge/PRISMA-2020%20Compliant-emerald.svg)](https://www.prisma-statement.org/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**海外オープンアクセスジャーナルからの自動論文検索、PRISMA 2020選定フロー追跡、および統計的・定性的メタ分析プラットフォーム**

キーワードを入力するだけで、海外の主要オープンジャーナルリポジトリ（OpenAlex、Europe PMC）から完全オープンアクセス（OA）論文を網羅的に検索し、**PRISMA 2020声明**に準拠した選定フロー図（Flow Diagram）の自動構築、固定効果・変量効果モデルによる統合効果量の算出、インタラクティブな**フォレストプロット（Forest Plot）**の可視化、そしてエビデンス統合レポート（GRADE評価・バイアスリスク含む）の自動生成を一気通貫で行うWebアプリケーションです。

---

## 🌟 主な機能 (Key Features)

### 1. 🔍 海外オープンジャーナル一括検索 (PRISMA: Identification)
- **マルチソース検索**: 2億5千万件以上の学術論文を網羅する **OpenAlex API** と、医学・生命科学のフルテキストに強い **Europe PMC API** を並行クエリ。
- **完全オープンアクセス保証**: Gold OA, Green OA, Bronze OA などの完全オープンアクセス論文のみを厳格に抽出。PDF直リンク、DOI、ライセンス情報を即座に取得。
- **高精度な重複排除**: DOI正規化およびタイトル類似度マッチングにより、複数リポジトリ間で重複する論文を自動検出し統合。PRISMAの「重複除外レコード数」を自動記録。

### 2. 📋 PRISMA 2020 準拠 スクリーニング＆動的フローダイアグラム (Screening & Eligibility)
- **PRISMA 2020 Flow Diagram**:
  - `Identification`（データベース検出数、重複除外数）
  - `Screening`（抄録スクリーニング数、除外理由別の除外数）
  - `Eligibility`（適格性精読評価数、除外数）
  - `Included`（定性統合採択数、定量的メタ分析採択数）
- **ワンクリック選定・除外**: チェックボックス操作や除外理由（対象集団不一致、対照群欠如、非原著論文、データ不備など）の選択に応じて、**フロー図の数値がリアルタイムに連動更新**。

### 3. 📊 統計的メタ分析 & フォレストプロット (Quantitative Meta-Analysis)
- **効果量・信頼区間の自動抽出**: 抄録テキストからオッズ比（OR）、相対リスク（RR）、ハザード比（HR）、標準化平均差（SMD/Cohen's d）、平均差（MD）および95%信頼区間（95% CI）、サンプルサイズを自動推定。
- **インライン編集マトリクス**: 抽出された数値はUI上のテーブルで自由に微調整・追加可能。
- **本格的な統計モデル**:
  - **固定効果モデル (Fixed-Effect Model)**: 逆分散法（Inverse Variance method）
  - **変量効果モデル (Random-Effects Model)**: DerSimonian-Laird 法
- **異質性の統計的検定**: Cochran's $Q$ 検定、自由度 $df$、$p$値、$I^2$ 統計量（0〜100%）、研究間分散 $\tau^2$（Tau-squared）。
- **Plotly インタラクティブ・フォレストプロット**:
  - 各研究の点推定値、95%エラーバー、変量効果モデルの重み（Weight %）に応じたマーカーサイズ、無効果線（Null Line）。
  - 下部に固定効果および変量効果モデルの「統合効果量ダイヤモンド（Summary Diamond）」を描画。
  - PNG画像ワンクリック保存対応。

### 4. 📝 PRISMA 2020 構造化エビデンス統合レポート (Qualitative Evidence Synthesis)
- PRISMA 2020 ガイドラインに沿った構造化メタ分析サマリーを自動編成：
  1. **背景と目的 (PICOフレームワーク)**
  2. **採用研究の特性一覧表 (Characteristics of Included Studies)**
  3. **結果の統合と知見 (Consensus & Discrepancies)**
  4. **バイアスリスク評価 (Risk of Bias Assessment)**
  5. **GRADEアプローチによるエビデンスの確実性 (Certainty of Evidence)**
  6. **総合結論と今後の課題 (Conclusions & Implications)**
- **ハイブリッド設計**: 内蔵の高精度NLPエンジンにより完全オフライン・APIキーなしでも即座に生成可能。さらに Gemini API キーを設定すれば Gemini 2.5 Flash による最高精度の学術統合も利用可能。

### 5. 📤 データ＆文献エクスポート (Export & Citation)
- **メタ分析データセット (CSV)**: Excel互換（BOM付きUTF-8）で論文情報、効果量、CI、サンプルサイズを出力。
- **学術引用 (BibTeX)**: LaTeX / Zotero / Mendeley で直接読み込める文献引用ファイルを出力。
- **PRISMAフローサマリー (Text)**: 論文執筆時にそのまま引用可能な各ステージの集計テキスト。

---

## 🚀 クイックスタート (Quick Start)

### 動作環境
- Python 3.10 以上（Python 3.11, 3.12, 3.13, 3.14 完全対応）
- Windows, macOS, Linux

### 1. リポジトリのクローン / 依存パッケージのインストール
```bash
git clone https://github.com/k518-2026/OpenJournalMetaAnalyzer.git
cd OpenJournalMetaAnalyzer

pip install -r requirements.txt
```

### 2. ワンクリック起動
```bash
python run.py
```
実行すると、ローカルサーバー（`http://127.0.0.1:8000`）が立ち上がり、既定のブラウザでWebアプリケーション画面が自動的に開きます。

---

## 📂 プロジェクト構成 (Architecture)

```
OpenJournalMetaAnalyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI (テスト自動化)
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI サーバー & REST API
│   ├── config.py                  # アプリケーション共通設定
│   ├── search/
│   │   ├── __init__.py
│   │   ├── base.py                # 論文・クエリ・PRISMA Pydanticモデル
│   │   ├── openalex.py            # OpenAlex API クライアント (完全OA抽出)
│   │   ├── europe_pmc.py          # Europe PMC API クライアント
│   │   └── aggregator.py          # 複数ソース並行取得 & 重複排除
│   ├── meta_analysis/
│   │   ├── __init__.py
│   │   ├── statistics.py          # 固定/変量効果モデル、I^2、Cochran's Q計算
│   │   ├── extractor.py           # アブストラクトからの効果量・サンプルサイズ自動抽出
│   │   ├── synthesizer.py         # PRISMA 2020 定性エビデンス統合レポート生成
│   │   └── forest_plot.py         # Plotly フォレストプロットデータ生成
│   └── static/
│       ├── index.html             # PRISMA ステッパー付きモダンSPA UI
│       ├── css/
│       │   └── style.css          # 学術UIスタイリング & PRISMAノードスタイル
│       └── js/
│           └── app.js             # UI制御、Plotlyチャート描画、PRISMA連動
├── tests/
│   ├── test_meta_analysis.py      # 統計計算・抽出ロジックの単体テスト
│   ├── test_search.py             # 重複排除・正規化の単体テスト
│   └── test_live_search.py        # ライブAPI結合テスト
├── requirements.txt               # 依存関係定義
├── pyproject.toml                 # パッケージ構成メタデータ
├── run.py                         # ブラウザ自動起動ランチャー
└── README.md                      # ドキュメント (本ファイル)
```

---

## 🧪 テストの実行 (Running Tests)

```bash
python -m pytest tests/ -v
```

---

## 📄 ライセンス (License)

MIT License - 学術研究、教育、商用利用を含め自由にご利用いただけます。