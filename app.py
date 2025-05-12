import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt

from auth import Auth
from api import APIClient

class ApiRequest:
    def __init__(self, name, method, url, headers, payload):
        self.name = name
        self.method = method
        self.url = url
        self.headers = headers
        self.payload = payload

    def to_dict(self):
        return {
            "name": self.name,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "payload": self.payload
        }

    @staticmethod
    def from_dict(d):
        return ApiRequest(
            d["name"], d["method"], d["url"], d["headers"], d["payload"]
        )

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Postman-like API Client")
        self.resize(900, 600)
        self.auth = Auth()
        self.token = None
        self.requests = []
        self.selected_idx = None

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left: Request List
        left_layout = QVBoxLayout()
        self.req_list = QListWidget()
        self.req_list.itemClicked.connect(self.on_req_selected)
        left_layout.addWidget(QLabel("リクエスト一覧"))
        left_layout.addWidget(self.req_list)
        btn_del = QPushButton("選択リクエスト削除")
        btn_del.clicked.connect(self.delete_request)
        left_layout.addWidget(btn_del)
        main_layout.addLayout(left_layout, 2)

        # Right: Request Editor & Result
        right_layout = QVBoxLayout()

        # Auth section
        auth_layout = QHBoxLayout()
        self.scope_edit = QLineEdit("user.read")
        auth_layout.addWidget(QLabel("Scopes:"))
        auth_layout.addWidget(self.scope_edit)
        self.auth_btn = QPushButton("認証（MSALでアクセストークン取得）")
        self.auth_btn.clicked.connect(self.authenticate)
        auth_layout.addWidget(self.auth_btn)
        self.token_label = QLabel("未認証")
        self.token_label.setWordWrap(True)
        auth_layout.addWidget(self.token_label)
        right_layout.addLayout(auth_layout)

        # Request editor
        form_layout = QVBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("リクエスト名")
        form_layout.addWidget(self.name_edit)

        method_url_layout = QHBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        method_url_layout.addWidget(self.method_combo)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("エンドポイントURL")
        method_url_layout.addWidget(self.url_edit)
        form_layout.addLayout(method_url_layout)

        self.headers_edit = QTextEdit('{\n  "Content-Type": "application/json",\n  "OData-MaxVersion": "4.0",\n  "OData-Version": "4.0",\n  "Accept": "application/json"\n}')
        self.headers_edit.setPlaceholderText("ヘッダー (JSON形式)")
        form_layout.addWidget(QLabel("ヘッダー"))
        form_layout.addWidget(self.headers_edit)

        self.payload_edit = QTextEdit("{}")
        self.payload_edit.setPlaceholderText("ペイロード (JSON形式)")
        form_layout.addWidget(QLabel("ペイロード"))
        form_layout.addWidget(self.payload_edit)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("リクエスト追加/更新")
        self.add_btn.clicked.connect(self.add_or_update_request)
        btn_layout.addWidget(self.add_btn)
        self.clear_btn = QPushButton("入力クリア")
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)
        form_layout.addLayout(btn_layout)

        right_layout.addLayout(form_layout)

        # Execute & Result
        exec_layout = QHBoxLayout()
        self.exec_btn = QPushButton("実行")
        self.exec_btn.clicked.connect(self.execute_request)
        exec_layout.addWidget(self.exec_btn)
        right_layout.addLayout(exec_layout)

        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        right_layout.addWidget(QLabel("結果"))
        right_layout.addWidget(self.result_edit)

        main_layout.addLayout(right_layout, 5)

    def authenticate(self):
        scopes = [s.strip() for s in self.scope_edit.text().split(",")]
        token = self.auth.acquire_token(scopes)
        if token:
            self.token = token
            self.token_label.setText("認証済み")
            QMessageBox.information(self, "認証", "アクセストークン取得成功")
        else:
            self.token = None
            self.token_label.setText("未認証")
            QMessageBox.warning(self, "認証", "アクセストークン取得失敗")

    def add_or_update_request(self):
        try:
            headers = json.loads(self.headers_edit.toPlainText())
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ヘッダーのJSONが不正です: {e}")
            return
        try:
            payload = json.loads(self.payload_edit.toPlainText())
        except Exception as e:
            payload = None  # GET等では空でもOK

        name = self.name_edit.text().strip() or f"Request {len(self.requests)+1}"
        method = self.method_combo.currentText()
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "エラー", "エンドポイントURLを入力してください")
            return

        req = ApiRequest(name, method, url, headers, payload)
        if self.selected_idx is not None:
            self.requests[self.selected_idx] = req
            self.selected_idx = None
        else:
            self.requests.append(req)
        self.refresh_req_list()
        self.clear_inputs()

    def clear_inputs(self):
        self.name_edit.clear()
        self.method_combo.setCurrentIndex(0)
        self.url_edit.clear()
        self.headers_edit.setText('{\n  "Content-Type": "application/json",\n  "OData-MaxVersion": "4.0",\n  "OData-Version": "4.0",\n  "Accept": "application/json"\n}')
        self.payload_edit.setText("{}")
        self.selected_idx = None

    def refresh_req_list(self):
        self.req_list.clear()
        for req in self.requests:
            item = QListWidgetItem(f"{req.name} ({req.method} {req.url})")
            self.req_list.addItem(item)

    def on_req_selected(self, item):
        idx = self.req_list.currentRow()
        req = self.requests[idx]
        self.selected_idx = idx
        self.name_edit.setText(req.name)
        self.method_combo.setCurrentText(req.method)
        self.url_edit.setText(req.url)
        self.headers_edit.setText(json.dumps(req.headers, indent=2, ensure_ascii=False))
        self.payload_edit.setText(json.dumps(req.payload, indent=2, ensure_ascii=False) if req.payload else "")

    def delete_request(self):
        idx = self.req_list.currentRow()
        if idx >= 0:
            del self.requests[idx]
            self.refresh_req_list()
            self.clear_inputs()

    def execute_request(self):
        idx = self.req_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "エラー", "リクエストを選択してください")
            return
        if not self.token:
            QMessageBox.warning(self, "エラー", "先に認証してください")
            return
        req = self.requests[idx]
        client = APIClient()
        headers = req.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        try:
            if req.method == "GET":
                response = client.get(req.url, self.token)
            elif req.method == "POST":
                response = client.post(req.url, self.token, req.payload)
            else:
                import requests
                resp = requests.request(
                    req.method,
                    req.url,
                    headers=headers,
                    json=req.payload if req.payload else None
                )
                try:
                    response = resp.json()
                except Exception:
                    response = resp.text
            self.result_edit.setPlainText(json.dumps(response, indent=2, ensure_ascii=False))
        except Exception as e:
            self.result_edit.setPlainText(f"リクエスト送信失敗: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
