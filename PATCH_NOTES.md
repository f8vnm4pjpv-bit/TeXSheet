# Patch Notes

## 2026-06-01

### 列名ヘッダーのLaTeXコマンド保持

- 原因
  - TeX表ヘッダーの列名出力に、captionや表セルと同じ表示用エスケープ処理を使っていたため、列名中の `\` が `\textbackslash{}` に変換され、`\makecell{...}` などのLaTeXコマンドとして機能しなかった。
  - 表示用列名、表セル、caption、label、保存用ファイル名の用途別処理が十分に分かれていなかった。
- 修正内容
  - TeX表ヘッダー専用のエスケープ処理を追加し、列名ヘッダーでは `\` と `{}` を保持するようにした。
  - captionと表セルでは従来通り `\` を `\textbackslash{}` にエスケープする処理を維持した。
  - `\label{...}` は既存のlabel専用正規化を維持し、保存用ファイル名・CSVファイル名・TeX表ファイル名・`\input{...}` 参照パスの安全化処理とは混同しないようにした。
  - 通常の列名に含まれる `_` などは、列名ヘッダーでも引き続きLaTeX用にエスケープするようにした。
- 主な変更ファイル
  - `texsheet/latex.py`
  - `PATCH_NOTES.md`
- 確認内容
  - 列名 `\makecell{Temp\\$[\si{\kelvin}]$}` がTeX表ヘッダーに `\makecell{Temp\\$[\si{\kelvin}]$}` のまま出力されることを確認した。
  - ヘッダーに `\textbackslash makecell` 相当の文字列が出ないことを確認した。
  - captionと表セルでは従来通り `\textbackslash{}` による安全化が残ることを確認した。
  - labelでは `\` や `/` が混入せず、`tab:bad_label_001` のように正規化されることを確認した。
  - `makecell` を使う最小LaTeX文書を `latexmk -lualatex` でビルドし、PDF生成まで通ることを確認した。
  - `python -m compileall texsheet` 相当が通ることを確認した。

## 2026-05-31

### LaTeX表ラベルのエスケープ分離

- 原因
  - 表生成時に `\label{...}` の中身へ本文・caption・表セル用のLaTeXエスケープ処理を適用していたため、`tab:table_001` の `_` が `\_` に変換される場合があった。
  - LaTeXの表示文字列用エスケープと、参照識別子としてのlabel正規化が分離されていなかった。
- 修正内容
  - `\caption{...}` と表セルでは従来通り表示用LaTeXエスケープを使うようにした。
  - `\label{...}` では表示用エスケープを使わず、label専用の安全な識別子正規化を使うようにした。
  - `tab:table_001` のようなlabelでは `:` と `_` を保持し、`/`、`\`、空白などは `_` に正規化するようにした。
- 主な変更ファイル
  - `texsheet/latex.py`
  - `PATCH_NOTES.md`
- 確認内容
  - 表生成結果が `\label{tab:table_001}` となり、`table\_001` にならないことを確認した。
  - captionと表セルの `_` は従来通り `\_` にエスケープされることを確認した。
  - `python -m compileall texsheet app.py` 相当が通ることを確認した。

### 表示用表名と保存用ファイル名の分離

- 原因
  - 表名または既存設定由来の `input_csv` / `output_tex` が保存ファイル名として扱われる経路があり、`/` などのパス区切り文字を含むと `project/tables_data` や `project/tables` の保存先が意図しないサブディレクトリとして解釈される可能性があった。
  - 表名変更と保存ファイル名の安定性が明確に分離されていなかったため、TeX記号・日本語・空白・スラッシュを含む表名で保存経路が壊れる余地があった。
- 修正内容
  - 新規表の保存用IDを `table_001`, `table_002`, `table_003` 形式で生成するようにした。
  - UI表示用の `name` / `caption` はそのまま保持し、CSV保存先とTeX表保存先は `tables_data/{table_id}.csv` / `tables/{table_id}.tex` として扱うようにした。
  - 既存configの安全な `input_csv` / `output_tex` は維持し、危険なパスまたは重複パスだけ安全な保存先へ正規化するようにした。
  - 危険な既存パスから安全な保存先へ移行する際、既存ファイルが存在すればコピーし、TeX表の移行時は `main.tex` 内の `\input{...}` / `\include{...}` 参照も安全化後のパスへ置換するようにした。
- 主な変更ファイル
  - `texsheet/config.py`
  - `texsheet/main_window_table_actions.py`
  - `PATCH_NOTES.md`
- 確認内容
  - 表示名 `1/T$` の表が、表示名を維持したまま `tables_data/table_001.csv` / `tables/table_001.tex` に正規化されることを確認した。
  - 既存の安全な保存ファイル名が維持されることを確認した。
  - `tables_data/a/b.csv` のようなサブディレクトリ化するCSVパスが安全でないと判定されることを確認した。
  - `python -m compileall texsheet` 相当が通ることを確認した。
- 既存プロジェクト互換性
  - 既存configに安全なファイル名フィールドがある場合は尊重する設計である。
  - 既存configに危険なファイル名がある場合のみ、安全な保存用ファイル名へ正規化する設計である。
  - 表名そのものはUI表示用として保持し、保存用ファイル名とは分離する設計である。

## 2026-05-15

### グラフ作成ダイアログの列変更反映修正

- 修正内容
  - 基本タブのX軸列・グラフ種類コンボボックス変更時に、系列一覧の再同期が確実に走るようにした。
  - グラフ作成ダイアログの基本タブでX軸列を変更したとき、既存系列の `x_column` も更新するように修正した。
  - 系列一覧を再構成した後、右側の系列詳細欄も新しい系列設定で再読み込みするようにした。
  - プレビュー更新とPDF生成で同じ `GraphConfig` が使われるため、ダイアログ上の列変更が両方に反映される。

- 原因
  - `QComboBox.currentTextChanged` / `currentIndexChanged` を引数なしメソッドへ直接接続しており、選択変更時の系列再同期が確実に動いていなかった。
  - 基本タブのX軸列変更時に系列一覧は再構成されていたが、同じY列の既存系列は設定をそのまま再利用していた。
  - さらに、系列一覧を再構成しても右側の系列詳細欄が古いX列を保持し、`graph_config()` 作成時に古い値で上書きしていた。
  - そのため、既存系列内の古い `x_column` が残り、プレビューとPDFが古い列設定で描画されていた。
  - 最近の列名分離や補完追加とは独立した、以前から存在した設計上の同期漏れと考えられる。

- 主な変更ファイル
  - `texsheet/dialogs/graph/basic_tab.py`
  - `texsheet/dialogs/graph/series_tab.py`
  - `PATCH_NOTES.md`

- 確認内容
  - X軸列変更後に `GraphConfig.series[*].x_column` が更新されること。
  - Y軸列の選択変更が系列一覧に反映されること。
  - 既存系列の近似設定が列変更後も保持されること。
  - 更新後の `GraphConfig` でPDF形式への描画ができること。
  - `python -m compileall texsheet` 相当が通ること。

### グラフ設定のOK確定・保存・再読込経路の追加修正

- 修正内容
  - OK押下時に確定した `GraphConfig` を `GraphSettingsDialog.accepted_config` として保持し、保存処理とPDF生成で同じ設定を使うようにした。
  - `open_graph_settings()` で保存用・PDF用に `dialog.graph_config()` を複数回再計算しないようにした。
  - `normalize_config()` 後の設定を `window.config` に戻し、再オープン時に最新の保存済みグラフ設定を参照するようにした。
  - X軸列変更時にX軸ラベルを新しい列名へ更新するようにした。
  - Y軸列選択変更時にY軸ラベルを選択中の列名へ更新するようにした。

- 原因
  - 前回修正は主にプレビュー更新経路の同期漏れに対応したが、OK確定後の保存・再読込経路に古い設定が再注入される余地が残っていた。
  - `graph_config()` は系列詳細欄の内容を保存する副作用を持つため、OK後に複数回呼ぶとUI状態によって保存値がぶれる可能性があった。
  - `normalize_config()` は `window.config["tables"]` を再構成するため、保存後の `window.config` を明示的に更新しておく必要があった。
  - 軸ラベル欄は列変更に追従しておらず、列参照が変わっても古い列名のラベルが残る状態だった。

- 主な変更ファイル
  - `texsheet/dialogs/graph_dialog.py`
  - `texsheet/dialogs/graph/basic_tab.py`
  - `texsheet/main_window_io_actions.py`
  - `PATCH_NOTES.md`

- 確認内容
  - `python -m compileall texsheet` 相当が通ること。
  - 追加のGUI経路確認は、現在の実行環境で `PySide6` が利用できないため未実施である。

### グラフ設定経路の再整理と凡例警告の修正

- 構造確認
  - 保存済みグラフ設定は `config.yaml` の `tables[*].graph_configs` に保持される。
  - `open_graph_settings()` が保存済み設定を `graph_config_from_dict()` で `GraphConfig` に戻し、`GraphSettingsDialog` へ渡す。
  - プレビュー更新は `GraphSettingsDialog.graph_config()` が現在のUI状態から作る `GraphConfig` だけを使う。
  - OK押下時は `GraphSettingsDialog.try_accept()` が `accepted_config` に確定済み `GraphConfig` を保持し、`open_graph_settings()` がそれを保存・PDF生成に使う。
  - rendererには `save_graph(dataframe, accepted_config)` 経由で確定済み `GraphConfig.series` が渡される。

- 問題点
  - `graph_config()` が右側の系列詳細欄を経由して系列を保存していたため、基本タブのX軸列・Y軸列選択より古い系列詳細欄の値が混入する余地があった。
  - 系列の同期処理が、基本タブのX/Y選択を唯一の正として扱い切れていなかった。
  - rendererは系列設定が存在するだけで `axis.legend()` を呼んでおり、実際に描画済みartist/labelがない場合に Matplotlib の凡例警告が出ていた。

- 修正内容
  - 系列同期処理を `sync_series_from_basic()` に集約し、基本タブのX軸列コンボとY軸列選択から `series_configs` を再構築するようにした。
  - 系列詳細欄の保存では、`x_column` は基本タブのX軸列、`y_column` は同期済み系列のY列を使うようにした。
  - `series_from_detail()` でも必ず基本タブから同期してから `GraphConfig` へ渡すようにした。
  - rendererの凡例生成前に、実際のhandles/labelsが存在するかを確認し、対象がない場合は `axis.legend()` を呼ばないようにした。

- 主な変更ファイル
  - `texsheet/dialogs/graph/series_tab.py`
  - `texsheet/graph/renderer.py`
  - `PATCH_NOTES.md`

- 確認内容
  - `python -m compileall texsheet` 相当が通ること。
  - 現在のシェル実行環境では `PySide6` と `matplotlib` が import できないため、GUI操作とrenderer実行の自動確認は未実施である。

### グラフ描画データ診断と数値フィルタリング強化

- 追加調査の観点
  - X軸列変更が `GraphConfig.series[*].x_column` に入っているか。
  - rendererが受け取るDataFrameの列名、各系列のX/Y列、グラフ種類が期待通りか。
  - 描画直前にX/Yデータが数値化できているか。
  - 極小値、`NaN`、`inf`、空文字、指数式文字列が有効点をすべて落としていないか。
  - 手動軸範囲やlog scaleにより、描画点が見えない状態になっていないか。

- 修正内容
  - rendererで、各系列についてX/Y列名、元dtype、先頭サンプル、min/max、NaN数、inf数、有効点数を診断表示するようにした。
  - rendererでDataFrame列一覧、系列一覧、軸範囲、log/linear scale、描画artist数、凡例handle/label数を診断表示するようにした。
  - `pd.to_numeric(..., errors="coerce")` 後に `inf` / `-inf` を除外対象にした。
  - 数値化やlog scale条件で有効点が0になった系列は、描画可能な数値データがないことを表示するようにした。

- 主な変更ファイル
  - `texsheet/graph/renderer.py`
  - `PATCH_NOTES.md`

- 確認内容
  - `python -m compileall texsheet` 相当が通ること。
  - 現在のシェル実行環境では `matplotlib` が import できないため、最小データ・実データ風データによるrenderer実行確認は未実施である。

### グラフデバッグ表示削除・Y軸復元・累乗記号対応

- 修正内容
  - rendererで一時的にグラフ内へ描画していた `columns=...`、`series=...`、`dtype=...`、`sample=...`、`legend_handles=...` などのデバッグ情報を通常のプレビュー/PDFへ出さないようにした。
  - 保存済みグラフ設定をダイアログへ復元するとき、X軸/Y軸の保存済み列が存在するなら、数値列判定に関係なく選択状態を復元するようにした。
  - 表計算の式評価で `^` を数学的な累乗として扱い、`10^(-3)` を `10**(-3)` と同様に計算できるようにした。

- 原因
  - 前回の調査用診断を `render_warnings()` に混ぜたため、通常のグラフ画像内にデバッグ文字列が描画されていた。
  - Y軸は再オープン時に `default_y_columns()` で `is_numeric_column()` を通していたため、保存済みのY列が式未評価・空・数値化不能に見える場合、保存済み設定ではなくデフォルトY列へ戻る可能性があった。
  - X軸は今回のデータでは数値列として判定されやすく、Y軸だけ戻るように見えていた。

- 主な変更ファイル
  - `texsheet/graph/renderer.py`
  - `texsheet/dialogs/graph_dialog.py`
  - `texsheet/formula.py`
  - `PATCH_NOTES.md`

- 確認内容
  - `10**(-3)` が従来通り計算できること。
  - `10^(-3)` が `0.001` として計算できること。
  - `python -m compileall texsheet` 相当が通ること。
  - 現在のシェル実行環境では `PySide6` と `matplotlib` が import できないため、GUI再オープン確認とPDF目視確認は未実施である。
