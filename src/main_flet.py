import flet as ft
import json

METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

def main(page: ft.Page):
    page.title = "Postman-like API Client (Flet版)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800

    # --- 状態管理 ---
    request_groups = []
    selected_group_idx = 0

    # --- UI部品 ---
    group_list = ft.ListView(expand=True, spacing=4)
    group_name_field = ft.TextField(label="Group Name", width=300, border_color=ft.Colors.GREY_300)
    add_group_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, tooltip="Add Group")
    del_group_btn = ft.FloatingActionButton(icon=ft.Icons.DELETE, tooltip="Delete Group", bgcolor=ft.Colors.RED_400)
    save_group_btn = ft.FilledButton("Save Group")
    clear_group_btn = ft.OutlinedButton("Clear")

    # タブUI用
    tabs = []
    tab_controls = []
    selected_tab_idx = 0

    # 認証
    scope_field = ft.TextField(label="Scopes", value="https://api.bap.microsoft.com/.default", width=400, border_color=ft.Colors.GREY_300)
    login_btn = ft.FilledButton("Login")
    logout_btn = ft.OutlinedButton("Logout")
    token_label = ft.Text("Not Authenticated", color=ft.Colors.YELLOW_400)
    token = None

    # --- 認証処理 ---
    import msal

    msal_app = msal.PublicClientApplication(
        client_id="YOUR_CLIENT_ID",  # 必要に応じて変更
        authority="https://login.microsoftonline.com/common"
    )

    def do_login(e=None):
        nonlocal token
        scopes = [s.strip() for s in scope_field.value.split(",")]
        try:
            result = msal_app.acquire_token_interactive(scopes)
            if "access_token" in result:
                token = result["access_token"]
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

    def do_logout(e=None):
        nonlocal token
        token = None
        token_label.value = "Not Authenticated"
        token_label.color = ft.Colors.YELLOW_400
        page.update()

    login_btn.on_click = do_login
    logout_btn.on_click = do_logout

    # レスポンス表示
    result_field = ft.TextField(label="Result", multiline=True, min_lines=8, max_lines=16, expand=True)

    # 送信ボタン
    send_btn = ft.FilledButton("Send", icon=ft.Icons.SEND)

    # --- タブの内容を生成 ---
    def make_tab_content(tab_data):
        # tab_data: {"method":..., "url":..., "headers":..., "payload":...}
        method_dd = ft.Dropdown(
            label="Method",
            value=tab_data.get("method", "GET"),
            options=[ft.dropdown.Option(m) for m in METHODS],
            width=100,
            border_color=ft.Colors.GREY_300,
        )
        url_field = ft.TextField(
            label="URL",
            value=tab_data.get("url", ""),
            width=400,
            border_color=ft.Colors.GREY_300,
        )
        headers_field = ft.TextField(
            label="Headers (JSON)",
            value=json.dumps(tab_data.get("headers", {}), indent=2, ensure_ascii=False),
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400,
            border_color=ft.Colors.GREY_300,
        )
        payload_field = ft.TextField(
            label="Payload (JSON)",
            value=json.dumps(tab_data.get("payload", {}), indent=2, ensure_ascii=False),
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400,
            border_color=ft.Colors.GREY_300,
        )
        return {
            "method_dd": method_dd,
            "url_field": url_field,
            "headers_field": headers_field,
            "payload_field": payload_field,
        }

    # --- タブUIの再構築 ---
    def rebuild_tabs():
        nonlocal tabs, tab_controls
        tab_controls = []
        for i, tab_data in enumerate(tabs):
            content = make_tab_content(tab_data)
            close_btn = ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Close Tab", on_click=lambda e, idx=i: close_tab(idx))
            tab_controls.append({
                "content": content,
                "tab": ft.Tab(
                    text=f"Request {i+1}",
                    icon=None,
                    content=ft.Column([
                        ft.Row([content["method_dd"], content["url_field"], send_btn], spacing=10),
                        ft.Row(
                            [
                                ft.Column([content["headers_field"]], expand=True),
                                ft.Column([content["payload_field"]], expand=True),
                            ],
                            spacing=10,
                            expand=True,
                        ),
                    ], expand=True),
                )
            })
        # +タブ
        plus_tab = ft.Tab(
            text="",
            icon=ft.Icons.ADD,
            content=ft.IconButton(icon=ft.Icons.ADD, tooltip="Add Tab", on_click=lambda e: add_tab())
        )
        tab_controls.append({"content": None, "tab": plus_tab})

    def add_tab():
        tabs.append({
            "method": "GET",
            "url": "",
            "headers": {},
            "payload": {},
        })
        rebuild_tabs()
        update_ui()

    def close_tab(idx):
        if len(tabs) <= 1:
            return
        tabs.pop(idx)
        rebuild_tabs()
        update_ui()

    def save_group(e=None):
        nonlocal request_groups, selected_group_idx
        name = group_name_field.value.strip() or f"Group {len(request_groups)+1}"
        # タブ内容を保存
        group_data = {
            "name": name,
            "requests": []
        }
        for c in tab_controls[:len(tabs)]:
            content = c["content"]
            group_data["requests"].append({
                "method": content["method_dd"].value,
                "url": content["url_field"].value,
                "headers": json.loads(content["headers_field"].value or "{}"),
                "payload": json.loads(content["payload_field"].value or "{}"),
            })
        if selected_group_idx is not None and selected_group_idx < len(request_groups):
            request_groups[selected_group_idx] = group_data
        else:
            request_groups.append(group_data)
            selected_group_idx = len(request_groups) - 1
        update_ui()

    def clear_group(e=None):
        nonlocal tabs, selected_tab_idx, selected_group_idx
        group_name_field.value = ""
        tabs = [{
            "method": "GET",
            "url": "",
            "headers": {},
            "payload": {},
        }]
        selected_tab_idx = 0
        selected_group_idx = None
        rebuild_tabs()
        update_ui()

    def add_group(e=None):
        nonlocal request_groups, selected_group_idx, tabs, selected_tab_idx
        name = f"Group {len(request_groups)+1}"
        request_groups.append({
            "name": name,
            "requests": [{
                "method": "GET",
                "url": "",
                "headers": {},
                "payload": {},
            }]
        })
        selected_group_idx = len(request_groups) - 1
        tabs = [dict(t) for t in request_groups[selected_group_idx]["requests"]]
        selected_tab_idx = 0
        rebuild_tabs()
        update_ui()

    def delete_group(e=None):
        nonlocal request_groups, selected_group_idx, tabs, selected_tab_idx
        if selected_group_idx is not None and 0 <= selected_group_idx < len(request_groups):
            del request_groups[selected_group_idx]
            if request_groups:
                selected_group_idx = max(0, selected_group_idx - 1)
                tabs = [dict(t) for t in request_groups[selected_group_idx]["requests"]]
            else:
                selected_group_idx = None
                tabs = [{
                    "method": "GET",
                    "url": "",
                    "headers": {},
                    "payload": {},
                }]
            selected_tab_idx = 0
            rebuild_tabs()
            update_ui()

    save_group_btn.on_click = save_group
    clear_group_btn.on_click = clear_group
    add_group_btn.on_click = add_group
    del_group_btn.on_click = delete_group

    def update_ui():
        # サイドバー
        group_list.controls.clear()
        for i, g in enumerate(request_groups):
            group_tile = ft.ListTile(
                title=ft.Text(g["name"]),
                selected=(i == selected_group_idx),
                on_click=lambda e, idx=i: select_group(idx)
            )
            group_list.controls.append(group_tile)
        # タブ
        tab_bar.tabs = [c["tab"] for c in tab_controls]
        tab_bar.selected_index = selected_tab_idx
        # タブ内容はtab_barのcontentで管理するため、ここでtab_content_areaは不要
        page.update()

    def select_group(idx):
        nonlocal selected_group_idx, tabs, selected_tab_idx
        selected_group_idx = idx
        group = request_groups[idx]
        tabs = [dict(t) for t in group["requests"]]
        selected_tab_idx = 0
        rebuild_tabs()
        update_ui()

    # --- UI構築 ---
    tab_bar = ft.Tabs(
        tabs=[],
        selected_index=0,
        on_change=lambda e: on_tab_change(e),
        expand=True,
        scrollable=True,
    )
    # tab_content_area = ft.Column([])  # ← 不要なので削除

    def on_tab_change(e):
        nonlocal selected_tab_idx
        idx = e.control.selected_index
        if idx == len(tabs):  # +タブ
            add_tab()
            tab_bar.selected_index = len(tabs) - 1
            selected_tab_idx = len(tabs) - 1
        else:
            selected_tab_idx = idx
        update_ui()

    # --- 初期データ ---
    tabs = [{
        "method": "GET",
        "url": "",
        "headers": {},
        "payload": {},
    }]
    rebuild_tabs()

    # --- リクエスト送信 ---
    def send_request(e):
        if not (0 <= selected_tab_idx < len(tab_controls)):
            result_field.value = "No request tab selected."
            page.update()
            return
        c = tab_controls[selected_tab_idx]["content"]
        method = c["method_dd"].value
        url = c["url_field"].value.strip()
        try:
            headers = json.loads(c["headers_field"].value)
        except Exception as ex:
            result_field.value = f"Invalid headers JSON: {ex}"
            page.update()
            return
        try:
            payload = json.loads(c["payload_field"].value)
        except Exception:
            payload = None
        if not url:
            result_field.value = "Please enter endpoint URL."
            page.update()
            return
        import requests
        try:
            # 認証済みならAuthorizationヘッダを付与
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if method == "GET":
                resp = requests.get(url, headers=headers)
            elif method == "POST":
                resp = requests.post(url, headers=headers, json=payload)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, json=payload)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, json=payload)
            elif method == "PATCH":
                resp = requests.patch(url, headers=headers, json=payload)
            else:
                result_field.value = f"Unsupported method: {method}"
                page.update()
                return
            try:
                result_field.value = json.dumps(resp.json(), indent=2, ensure_ascii=False)
            except Exception:
                result_field.value = resp.text
        except Exception as ex:
            result_field.value = f"Request failed: {ex}"
        page.update()

    send_btn.on_click = send_request

    # --- レイアウト ---
    page.add(
        ft.Row([
            ft.Column([
                ft.Text("Request Groups", size=18, weight=ft.FontWeight.BOLD),
                group_list,
                ft.Row([add_group_btn, del_group_btn], spacing=8),
            ], width=220, expand=False),
            ft.VerticalDivider(width=1),
            ft.Column([
                ft.Row([
                    group_name_field,
                    save_group_btn,
                    clear_group_btn,
                ], spacing=8),
                ft.Row([
                    scope_field,
                    login_btn,
                    logout_btn,
                    token_label,
                ], spacing=8),
                tab_bar,
                # tab_content_area,  # ← 不要なので削除
                ft.Container(
                    ft.Column([
                        ft.Text("Result", size=16, weight=ft.FontWeight.BOLD),
                        result_field,
                    ],
                    alignment=ft.alignment.bottom_left,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                    ),
                    padding=20,
                    margin=ft.margin.only(top=20),
                    alignment=ft.alignment.bottom_center,
                    expand=True,
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO),
        ], expand=True)
    )
    update_ui()

ft.app(target=main)
