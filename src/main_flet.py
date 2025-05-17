import flet as ft
import json

METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

def main(page: ft.Page):
    page.title = "Postman-like API Client UI Mock (Flet)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800

    # サイドバー（履歴ダミーデータ）
    group_list = ft.ListView(
        controls=[
            ft.ListTile(
                title=ft.Text("GET /api/users", size=16),
                selected=True,
                dense=True,
                min_vertical_padding=0,
                content_padding=0
            ),
            ft.ListTile(
                title=ft.Text("POST /api/items", size=16),
                dense=True,
                min_vertical_padding=0,
                content_padding=0
            ),
            ft.ListTile(
                title=ft.Text("DELETE /api/users/123", size=16),
                dense=True,
                min_vertical_padding=0,
                content_padding=0
            ),
            ft.ListTile(
                title=ft.Text("PATCH /api/items/456", size=16),
                dense=True,
                min_vertical_padding=0,
                content_padding=0
            ),
        ],
        expand=True,
        spacing=0,
    )
    add_group_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, tooltip="Add Group", mini=True)
    del_group_btn = ft.FloatingActionButton(icon=ft.Icons.DELETE, tooltip="Delete Group", bgcolor=ft.Colors.RED_400, mini=True)

    login_btn = ft.FilledButton("Login", width=100)
    logout_btn = ft.OutlinedButton("Logout", width=100)
    token_label = ft.Text("Not Authenticated", color=ft.Colors.YELLOW_400)
    token = None

    # タブUIの状態
    tabs = [0]  # タブのインデックスリスト（初期は1つだけ）

    # --- ログイン処理 ---
    def on_login(e):
        nonlocal token
        from src.auth_client import Auth
        auth = Auth()
        scopes = ["https://api.bap.microsoft.com/.default"]
        token_label.value = "Authenticating..."
        token_label.color = ft.Colors.YELLOW_400
        page.update()
        try:
            t = auth.acquire_token(scopes)
            if t:
                token = t
                token_label.value = "Authenticated"
                token_label.color = ft.Colors.GREEN_400
            else:
                token = None
                token_label.value = "Auth Failed"
                token_label.color = ft.Colors.RED_400
        except Exception as ex:
            token = None
            token_label.value = f"Auth Error: {ex}"
            token_label.color = ft.Colors.RED_400
        page.update()

    login_btn.on_click = on_login

    def on_logout(e):
        nonlocal token
        token = None
        token_label.value = "Not Authenticated"
        token_label.color = ft.Colors.YELLOW_400
        page.update()

    logout_btn.on_click = on_logout

    def build_tabs():
        tab_controls = []
        for i in tabs:
            def make_tab(idx):
                method_dd = ft.Dropdown(
                    label="Method",
                    value="GET",
                    options=[ft.dropdown.Option(m) for m in METHODS],
                    width=100,
                    border_color=ft.Colors.GREY_300,
                )
                url_field = ft.TextField(
                    label="URL",
                    value="https://api.example.com/endpoint",
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
                    on_click=lambda e, idx=idx: close_tab(idx),
                )
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
                    # タブタイトル右端に×ボタン
                    tab_content=ft.Row([
                        ft.Text(f"Request {idx+1}"),
                        close_btn,
                    ], spacing=4)
                )
            tab_controls.append(make_tab(i))
        # +タブ
        plus_tab = ft.Tab(
            text="",
            icon=ft.Icons.ADD,
            content=ft.IconButton(icon=ft.Icons.ADD, tooltip="Add Tab", on_click=add_tab),
        )
        tab_controls.append(plus_tab)
        return tab_controls

    def close_tab(idx):
        if len(tabs) <= 1:
            return
        tabs.remove(idx)
        rebuild_ui(selected_index=min(idx, len(tabs)-1))

    def add_tab(e=None):
        new_idx = max(tabs) + 1 if tabs else 0
        tabs.append(new_idx)
        rebuild_ui(selected_index=len(tabs)-1)

    def on_tab_change(e):
        idx = e.control.selected_index
        if idx == len(tabs):  # ＋タブが選択された場合
            add_tab()

    def rebuild_ui(selected_index=0):
        page.controls.clear()
        tab_bar = ft.Tabs(
            tabs=build_tabs(),
            selected_index=selected_index,
            expand=True,
            scrollable=True,
            on_change=on_tab_change,
        )
        page.add(
            ft.Row([
                ft.Container(
                    ft.Column([
                        ft.Row([login_btn, logout_btn], spacing=8),
                        ft.Row([token_label], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(
                            ft.Text("History", size=18, weight=ft.FontWeight.BOLD),
                            margin=ft.margin.only(top=20, bottom=0),
                        ),
                        group_list,
                        ft.Row([add_group_btn, del_group_btn], spacing=8),
                    ], width=210, expand=False),
                    padding=18,
                ),
                ft.VerticalDivider(width=1),
                ft.Container(
                    ft.Column([
                        tab_bar
                    ], expand=True),
                    padding=18,
                    expand=True,
                ),
            ], expand=True)
        )
        page.update()

    # 初期UI構築
    rebuild_ui(selected_index=0)

if __name__ == "__main__":
    import flet as ft
    ft.app(target=main)
