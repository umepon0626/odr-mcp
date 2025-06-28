# ODR MCP (OpenDRIVE Model Context Protocol)

OpenDRIVEファイルから曲率半径に基づいて道路やレーン情報を検索するMCP（Model Context Protocol）サーバーです。

## 概要

このプロジェクトは、OpenDRIVE形式の道路データファイルを解析し、指定された曲率半径に最も近い道路やレーン情報を取得するためのMCPツールを提供します。

## 機能

- **道路検索**: 指定された曲率半径に最も近い道路を検索
- **レーン検索**: 指定された曲率半径に最も近い道路のレーン情報を取得
- **OpenDRIVEファイル解析**: XMLベースのOpenDRIVEファイルを読み込み・解析

## 前提条件

- Python 3.12以上
- uv（パッケージマネージャー）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone git@github.com:umepon0626/odr-mcp.git
cd odr-mcp
```

### 1.1 サブモジュールの初期化・更新

テスト用OpenDRIVEファイルはgit submoduleとして管理されています。初回セットアップ時、またはサブモジュールを更新したい場合は以下を実行してください。

```bash
git submodule update --init --recursive
```

### 2. miseを使った環境構築（推奨）

このプロジェクトは [mise](https://github.com/jdx/mise) を使ったバージョン管理・依存管理に対応しています。

#### miseのインストール

[mise公式ドキュメント](https://mise.jdx.dev/ja/install.html) を参考にインストールしてください。

#### Python・uvのインストールと依存関係のセットアップ

```bash
mise install           # .mise.tomlに従いPythonとuvを自動インストール
mise run uv sync       # 依存パッケージのインストール
```

#### 仮想環境の有効化

```bash
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows
```

### 3. 依存関係のインストール（uvのみを使う場合）

```bash
uv sync
```

### 4. 仮想環境の有効化

```bash
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows
```

## 使用方法

### MCPサーバーとして実行

```bash
python main.py
```

#### 仮想環境のPythonパスを明示的に指定する場合

MCPサーバーとして外部ツールやプロセスから起動する場合、仮想環境のPythonパスを明示的に指定する必要があります。

例：
```json
"odr-mcp": {
  "command": "<本リポジトリまでの絶対path>/odr-mcp/.venv/bin/python3",
  "args": [
    "<本リポジトリまでの絶対path>/odr-mcp/main.py"
  ]
}
```

- 仮想環境のパスは各自の環境に合わせて適宜読み替えてください。
- `which python`や`which python3`コマンドで仮想環境のパスを確認できます。

### 利用可能なツール

#### 1. `find_road_with_r`

指定された曲率半径に最も近い道路を検索します。

**パラメータ:**
- `r` (float): 曲率半径 [m]
- `file_path` (str): OpenDRIVEファイルの絶対パス

**戻り値:**
- `RoadInfo`: 最も近い曲率半径を持つ道路の情報

**使用例:**
```python
# 曲率半径100mの道路を検索
road = find_road_with_r(100.0, "/path/to/Town01.xodr")
```

#### 2. `find_lane_with_r`

指定された曲率半径に最も近い道路のレーン情報を取得します。

**パラメータ:**
- `r` (float): 曲率半径 [m]
- `file_path` (str): OpenDRIVEファイルの絶対パス

**戻り値:**
- `LaneInfo`: 最も近い曲率半径を持つ道路のレーン情報

**使用例:**
```python
# 曲率半径50mの道路のレーンを検索
lane = find_lane_with_r(50.0, "/path/to/Town02.xodr")
```

## テストファイル

本プロジェクトのテスト用OpenDRIVEファイルは [carla-simulator/opendrive-test-files](https://github.com/carla-simulator/opendrive-test-files) をサブモジュールとして利用しています。

- サブモジュールの初期化・更新方法は「セットアップ」セクションを参照してください。

## 設定

### ログレベル

ログレベルは`main.py`の最後で設定されています：

```python
logging.basicConfig(level=logging.INFO)
```

### 曲率検索の最小長さ

`MIN_CURVE_LENGTH`定数で、カーブとして認識する最小長さを設定できます（デフォルト: 1.0m）。

## データ構造

### RoadInfo
```python
@dataclass
class RoadInfo:
    id: str                    # 道路ID
    name: Optional[str]        # 道路名
    length: Optional[str]      # 道路長
    junction: Optional[str]    # 交差点情報
    geometries: List[GeometryInfo]  # 幾何学情報
```

### LaneInfo
```python
@dataclass
class LaneInfo:
    id: str                    # レーンID
    type: str                  # レーンタイプ
    level: str                 # レベル
    road_id: str              # 所属道路ID
    link: Optional[List[LinkInfo]]      # リンク情報
    width: Optional[List[WidthInfo]]    # 幅情報
    roadMark: Optional[List[RoadMarkInfo]]  # 道路標示
    userData: Optional[List[UserDataInfo]]   # ユーザーデータ
```

## トラブルシューティング

### よくある問題

1. **ファイルが見つからない**
   - ファイルパスが正しいことを確認してください
   - 絶対パスを使用してください

2. **曲率情報が見つからない**
   - OpenDRIVEファイルに曲率情報が含まれていることを確認してください
   - `MIN_CURVE_LENGTH`の値を調整してみてください

3. **XML解析エラー**
   - OpenDRIVEファイルが正しいXML形式であることを確認してください

## 開発

### 依存関係

- `lxml`: XML解析
- `mcp[cli]`: MCPサーバー機能
- `pyxodr`: OpenDRIVEファイル処理
- `scenariogeneration`: シナリオ生成

### コードの構造

- `main.py`: メインのMCPサーバーとツール関数
- `pyproject.toml`: プロジェクト設定と依存関係
- `opendrive-test-files/`: テスト用OpenDRIVEファイル

## ライセンス

このプロジェクトのライセンス情報については、プロジェクトのルートディレクトリを確認してください。

## 貢献

バグ報告や機能要求については、GitHubのIssueを作成してください。プルリクエストも歓迎します。
