from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def toggle_log_view(window):
    visible = not window.log_view.isVisible()
    window.log_view.setVisible(visible)
    window.log_toggle_button.setText("ログを隠す" if visible else "ログを表示")


def setup_main_window_ui(window):
    window.tab_widget = QTabWidget()
    window.tab_widget.currentChanged.connect(window.on_tab_changed)

    window.move_row_up_button = None
    window.move_row_down_button = None
    window.move_column_left_button = None
    window.move_column_right_button = None
    window.undo_button = QPushButton("Undo")
    window.redo_button = QPushButton("Redo")
    window.add_table_button = QPushButton("表追加")
    window.delete_table_button = QPushButton("表削除")
    window.rename_table_button = QPushButton("表名変更")
    window.add_row_button = None
    window.delete_row_button = None
    window.add_column_button = None
    window.delete_column_button = None
    window.rename_column_button = None
    window.set_formula_button = None
    window.clear_formula_button = None
    window.table_settings_button = QPushButton("表設定")
    window.save_button = QPushButton("保存")
    window.save_all_button = QPushButton("すべて保存")
    window.constants_button = QPushButton("定数設定")
    window.graph_button = QPushButton("グラフ作成")
    window.generate_button = QPushButton("生成")

    window.undo_button.clicked.connect(window.undo)
    window.redo_button.clicked.connect(window.redo)
    window.add_table_button.clicked.connect(window.add_table)
    window.delete_table_button.clicked.connect(window.delete_current_table)
    window.rename_table_button.clicked.connect(window.rename_current_table)
    window.table_settings_button.clicked.connect(window.open_table_settings)
    window.save_button.clicked.connect(window.save_current_table)
    window.save_all_button.clicked.connect(window.save_all_tables)
    window.constants_button.clicked.connect(window.open_constants_settings)
    window.graph_button.clicked.connect(window.open_graph_settings)
    window.generate_button.clicked.connect(window.generate_outputs)

    window.caption_edit = QLineEdit()

    window.log_toggle_button = QPushButton("ログを表示")
    window.log_view = QPlainTextEdit()
    window.log_view.setReadOnly(True)
    window.log_view.setVisible(False)
    window.log_toggle_button.clicked.connect(lambda: toggle_log_view(window))

    table_button_layout = QHBoxLayout()
    table_button_layout.addWidget(window.add_table_button)
    table_button_layout.addWidget(window.delete_table_button)
    table_button_layout.addWidget(window.rename_table_button)
    table_button_layout.addWidget(window.save_button)
    table_button_layout.addWidget(window.save_all_button)
    table_button_layout.addWidget(window.constants_button)
    table_button_layout.addWidget(window.graph_button)
    table_button_layout.addWidget(window.generate_button)
    table_button_layout.addStretch()

    edit_button_layout = QHBoxLayout()
    edit_button_layout.addWidget(window.undo_button)
    edit_button_layout.addWidget(window.redo_button)
    edit_button_layout.addWidget(window.table_settings_button)
    edit_button_layout.addStretch()

    caption_layout = QHBoxLayout()
    caption_layout.addWidget(QLabel("表タイトル"))
    caption_layout.addWidget(window.caption_edit)

    log_header_layout = QHBoxLayout()
    log_header_layout.addWidget(window.log_toggle_button)
    log_header_layout.addStretch()

    layout = QVBoxLayout()
    layout.addLayout(table_button_layout)
    layout.addLayout(caption_layout)
    layout.addWidget(window.tab_widget)
    layout.addLayout(edit_button_layout)
    layout.addLayout(log_header_layout)
    layout.addWidget(window.log_view)

    central_widget = QWidget()
    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)
