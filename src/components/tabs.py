import flet as ft

METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


class TabManager:
    def __init__(self, on_tab_change, on_add_tab, on_close_tab, on_send):
        self.tabs = [0]  # 初期は1つだけ
        self.on_tab_change = on_tab_change
        self.on_add_tab = on_add_tab
        self.on_close_tab = on_close_tab
        self.on_send = on_send
        self.tab_fields = {}  # {idx: {"method_dd":..., "url_field":...}}
        self.tab_state = {}  # {idx: {"method":..., "url":..., ...}}

    def build_tabs(self):
        tab_controls = []
        for i in self.tabs:
            tab_controls.append(self._make_tab(i))
        # +タブ
        plus_tab = ft.Tab(
            text="",
            icon=ft.Icons.ADD,
            content=ft.IconButton(
                icon=ft.Icons.ADD, tooltip="Add Tab", on_click=self.on_add_tab
            ),
        )
        tab_controls.append(plus_tab)
        return tab_controls

    def _make_tab(self, idx):
        # 状態取得 or デフォルト
        state = self.tab_state.get(idx, {})
        method_val = state.get("method", "GET")
        url_val = state.get("url", "https://*.crm7.dynamics.com/api/data/v9.2/WhoAmI")
        query_val = state.get("query", "")
        headers_val = state.get(
            "headers",
            "Accept: application/json\nContent-Type: application/json\nOData-MaxVersion: 4.0\nOData-Version: 4.0",
        )
        payload_val = state.get("payload", "")
        result_val = state.get("result", " ")
        status_code_val = state.get("status_code", "")
        elapsed_ms_val = state.get("elapsed_ms", "")

        method_dd = ft.Dropdown(
            label="Method",
            value=method_val,
            options=[ft.dropdown.Option(m) for m in METHODS],
            width=110,
            border_color=ft.Colors.GREY_300,
            on_change=lambda e: self._update_state(idx, "method", e.control.value),
        )
        url_field = ft.TextField(
            label="URL",
            value=url_val,
            width=600,
            border_color=ft.Colors.GREY_300,
            on_change=lambda e: self._update_state(idx, "url", e.control.value),
        )
        query_field = ft.TextField(
            label="Query Parameters (after '?')",
            value=query_val,
            multiline=True,
            min_lines=1,
            max_lines=4,
            border_color=ft.Colors.GREY_300,
            on_change=lambda e: self._update_state(idx, "query", e.control.value),
        )

        def handle_extract_query(e):
            url_val = url_field.value
            if "?" in url_val:
                base, query = url_val.split("?", 1)
                url_field.value = base
                query_field.value = query
                self._update_state(idx, "url", base)
                self._update_state(idx, "query", query)
                # 強制UI更新
                if hasattr(url_field, "update"):
                    url_field.update()
                if hasattr(query_field, "update"):
                    query_field.update()

        extract_btn = ft.TextButton(
            text="Extract Query",
            on_click=handle_extract_query,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=8, vertical=0),
                shape=ft.RoundedRectangleBorder(radius=6),
                bgcolor=ft.Colors.GREY_200,
            ),
            width=110,
            tooltip="Move query string from URL to Query Parameters",
        )
        headers_field = ft.TextField(
            label="Headers (key: value)",
            value=headers_val,
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_color=ft.Colors.GREY_300,
            on_change=lambda e: self._update_state(idx, "headers", e.control.value),
        )
        payload_field = ft.TextField(
            label="Payload (JSON)",
            value=payload_val,
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_color=ft.Colors.GREY_300,
            on_change=lambda e: self._update_state(idx, "payload", e.control.value),
        )
        send_btn = ft.FilledButton("Send", icon=ft.Icons.SEND)
        result_field = ft.TextField(
            label="Result",
            value=result_val,
            multiline=True,
            min_lines=100,
            expand=True,
            border_color=ft.Colors.GREY_300,
            read_only=True,
            on_change=lambda e: self._update_state(idx, "result", e.control.value),
        )
        close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            tooltip="Close Tab",
            icon_size=16,
            on_click=lambda e, idx=idx: self.on_close_tab(idx),
        )

        # Sendボタンのコールバック
        def handle_send(e):
            self.on_send(idx, method_dd.value, url_field.value)

        send_btn.on_click = handle_send

        # 各タブのフィールドを記憶
        self.tab_fields[idx] = {
            "method_dd": method_dd,
            "url_field": url_field,
            "query_field": query_field,
            "headers_field": headers_field,
            "payload_field": payload_field,
            "result_field": result_field,
        }

        return ft.Tab(
            text=f"Request {idx+1}",
            icon=None,
            content=ft.Column(
                [
                    ft.Container(
                        ft.Row(
                            [method_dd, ft.Container(url_field, expand=True), send_btn],
                            spacing=10,
                        ),
                        margin=ft.margin.only(top=20, bottom=10),
                    ),
                    ft.Container(
                        ft.Row(
                            [
                                # ft.Column([extract_btn, decode_btn]),  # TODO: implement decode query button
                                extract_btn,
                                ft.Container(query_field, expand=True),
                            ],
                            spacing=10,
                        ),
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Row(
                        [
                            ft.Column([headers_field], expand=True),
                            ft.VerticalDivider(width=1),
                            ft.Column([payload_field], expand=True),
                        ],
                        spacing=10,
                    ),
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(
                                    f" Status: {status_code_val},   Time: {elapsed_ms_val} ms",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                result_field,
                            ],
                            alignment=ft.alignment.bottom_left,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            expand=True,
                        ),
                        margin=ft.margin.only(top=10),
                        alignment=ft.alignment.bottom_center,
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            tab_content=ft.Row(
                [
                    ft.Text(f"Request {idx+1}"),
                    close_btn,
                ],
                spacing=4,
            ),
        )

    def _update_state(self, idx, key, value):
        if idx not in self.tab_state:
            self.tab_state[idx] = {}
        self.tab_state[idx][key] = value

    def add_tab(self):
        new_idx = max(self.tabs) + 1 if self.tabs else 0
        self.tabs.append(new_idx)

    def close_tab(self, idx):
        if len(self.tabs) <= 1:
            return
        self.tabs.remove(idx)
        if idx in self.tab_fields:
            del self.tab_fields[idx]
        if idx in self.tab_state:
            del self.tab_state[idx]
