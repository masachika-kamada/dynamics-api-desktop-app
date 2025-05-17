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

    def build_tabs(self):
        tab_controls = []
        for i in self.tabs:
            tab_controls.append(self._make_tab(i))
        # +タブ
        plus_tab = ft.Tab(
            text="",
            icon=ft.Icons.ADD,
            content=ft.IconButton(icon=ft.Icons.ADD, tooltip="Add Tab", on_click=self.on_add_tab),
        )
        tab_controls.append(plus_tab)
        return tab_controls

    def _make_tab(self, idx):
        method_dd = ft.Dropdown(
            label="Method",
            value="GET",
            options=[ft.dropdown.Option(m) for m in METHODS],
            width=100,
            border_color=ft.Colors.GREY_300,
        )
        url_field = ft.TextField(
            label="URL",
            value="https://*.crm7.dynamics.com/api/data/v9.2/WhoAmI",
            width=600,
            border_color=ft.Colors.GREY_300,
        )
        query_field = ft.TextField(
            label="Query Parameters",
            value="",
            multiline=True,
            min_lines=1,
            max_lines=4,
            border_color=ft.Colors.GREY_300,
        )
        headers_field = ft.TextField(
            label="Headers (key: value)",
            value='Content-Type: application/json\nAuthorization: Bearer xxxxx',
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_color=ft.Colors.GREY_300,
        )
        payload_field = ft.TextField(
            label="Payload (JSON)",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_color=ft.Colors.GREY_300,
        )
        send_btn = ft.FilledButton("Send", icon=ft.Icons.SEND)
        result_field = ft.TextField(
            multiline=True,
            min_lines=100,
            expand=True,
            border_color=ft.Colors.GREY_300,
            read_only=True,
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
            content=ft.Column([
                ft.Container(
                    ft.Row([method_dd, ft.Container(url_field, expand=True), send_btn], spacing=10),
                    margin=ft.margin.only(top=20, bottom=10),
                ),
                ft.Container(
                    ft.Row([ft.Container(query_field, expand=True)]),
                    margin=ft.margin.only(left=110, bottom=20),
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
                    ft.Column([
                        ft.Text("Result", size=16, weight=ft.FontWeight.BOLD),
                        result_field,
                    ],
                    alignment=ft.alignment.bottom_left,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                    ),
                    margin=ft.margin.only(top=20),
                    alignment=ft.alignment.bottom_center,
                    expand=True,
                ),
            ], expand=True),
            tab_content=ft.Row([
                ft.Text(f"Request {idx+1}"),
                close_btn,
            ], spacing=4)
        )

    def add_tab(self):
        new_idx = max(self.tabs) + 1 if self.tabs else 0
        self.tabs.append(new_idx)

    def close_tab(self, idx):
        if len(self.tabs) <= 1:
            return
        self.tabs.remove(idx)
        if idx in self.tab_fields:
            del self.tab_fields[idx]
