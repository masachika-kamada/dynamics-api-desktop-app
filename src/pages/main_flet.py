import flet as ft
from src.components.tabs import TabManager


def main(page: ft.Page):
    page.title = "Postman-like API Client UI Mock (Flet)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800

    login_btn = ft.FilledButton(
        "Login", width=200
    )  # expand=Trueで自動調整されるので、実際より幅広で指定
    logout_btn = ft.OutlinedButton(
        "Logout", width=200
    )  # expand=Trueで自動調整されるので、実際より幅広で指定
    token_label = ft.Text("Not Authenticated", color=ft.Colors.YELLOW_400)
    token = None

    # 履歴リスト
    history = []

    # サイドバー（履歴）
    group_list = ft.ListView(
        controls=[],
        expand=True,
        spacing=0,
    )
    add_group_btn = ft.FloatingActionButton(
        icon=ft.Icons.ADD, tooltip="Add Group", mini=True
    )
    del_group_btn = ft.FloatingActionButton(
        icon=ft.Icons.DELETE,
        tooltip="Delete Group",
        bgcolor=ft.Colors.RED_400,
        mini=True,
    )

    # --- Authインスタンスを共通化 ---
    from src.api.auth_client import Auth
    auth = Auth()

    # --- ログイン処理 ---
    def on_login(e):
        nonlocal token, auth
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

    # --- タブ管理 ---
    selected_tab_index = 0

    def handle_tab_change(e):
        nonlocal selected_tab_index
        idx = e.control.selected_index
        if idx == len(tab_manager.tabs):  # +タブ
            handle_add_tab()
        else:
            selected_tab_index = idx
            rebuild_ui()

    def handle_add_tab(e=None):
        nonlocal selected_tab_index
        tab_manager.add_tab()
        selected_tab_index = len(tab_manager.tabs) - 1
        rebuild_ui()

    def handle_close_tab(idx):
        nonlocal selected_tab_index
        if len(tab_manager.tabs) <= 1:
            return
        tab_manager.close_tab(idx)
        if selected_tab_index >= len(tab_manager.tabs):
            selected_tab_index = len(tab_manager.tabs) - 1
        rebuild_ui()

    def on_send(tab_idx, method, url):
        nonlocal token, auth
        fields = tab_manager.tab_fields[tab_idx]

        # --- 認証チェック（スコープ動的対応） ---
        import re

        # URLからスコープを決定
        match = re.match(r"https?://[^/]+", url)
        if match:
            domain = match.group(0)
            scopes = [f"{domain}/.default"]
        else:
            # URLが不正な場合は従来のスコープ
            scopes = ["https://api.bap.microsoft.com/.default"]

        # 認証状態表示をloginボタン時と同じように更新
        token_label.value = "Authenticating..."
        token_label.color = ft.Colors.YELLOW_400
        page.update()
        try:
            # サイレント認証のみ（失敗時はインタラクティブ認証しない）
            t = auth.acquire_token_for_scope(scopes, force_interactive=False)
            if t:
                token = t
                token_label.value = "Authenticated"
                token_label.color = ft.Colors.GREEN_400
                page.update()
            else:
                token = None
                token_label.value = "Auth Failed"
                token_label.color = ft.Colors.RED_400
                page.update()
                fields["result_field"].value = "認証が必要です。ログインしてください（Loginボタンを押してください）。"
                if hasattr(fields["result_field"], "update"):
                    fields["result_field"].update()
                return
        except Exception as ex:
            token = None
            token_label.value = f"Auth Error: {ex}"
            token_label.color = ft.Colors.RED_400
            page.update()
            fields["result_field"].value = f"認証エラー: {ex}"
            if hasattr(fields["result_field"], "update"):
                fields["result_field"].update()
            return

        # クエリパラメータを結合
        query = fields["query_field"].value.strip()
        if query:
            if "?" in url:
                url = f"{url}&{query}"
            else:
                url = f"{url}?{query}"

        # 履歴に追加（/apiが含まれていればその後ろ、なければ全体）        
        if url:
            api_idx = url.find("/api")
            if api_idx != -1:
                display_url = url[api_idx:]
            else:
                display_url = url
        else:
            display_url = ""
        history.append((method, display_url))

        # ヘッダーをdictに変換
        headers_text = fields["headers_field"].value
        headers = {}
        for line in headers_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()

        # アクセストークン追加
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # APIリクエスト送信
        from src.api.api_client import APIClient
        import time

        client = APIClient()
        result = ""
        status_code = ""
        elapsed_ms = ""
        try:
            start_time = time.time()
            if method == "GET":
                resp = client.get(url, token, headers)
            elif method == "POST":
                # payload
                import json as _json

                payload_text = fields["payload_field"].value
                try:
                    payload = _json.loads(payload_text) if payload_text.strip() else {}
                except Exception as ex:
                    result = f"Invalid JSON payload: {ex}"
                    resp = None
                else:
                    resp = client.post(url, token, payload, headers)
            else:
                resp = None
                result = f"Unsupported method: {method}"
            elapsed_ms = int((time.time() - start_time) * 1000)
            if resp is not None:
                # ステータスコード取得
                status_code = resp.status_code
                # 本文取得
                result = resp.text
        except Exception as ex:
            result = f"Request failed: {ex}"
            status_code = ""
            elapsed_ms = ""

        # レスポンスをresult_fieldに表示
        print(str(status_code))  # for debug: print status code to command line
        tab_manager.tab_state[tab_idx]["result"] = result
        tab_manager.tab_state[tab_idx]["status_code"] = (
            str(status_code) if status_code is not None else ""
        )
        tab_manager.tab_state[tab_idx]["elapsed_ms"] = elapsed_ms
        fields["result_field"].value = result
        if hasattr(fields["result_field"], "update"):
            fields["result_field"].update()
        rebuild_ui()

    tab_manager = TabManager(
        on_tab_change=handle_tab_change,
        on_add_tab=handle_add_tab,
        on_close_tab=handle_close_tab,
        on_send=on_send,
    )

    def rebuild_ui():
        page.controls.clear()
        # 履歴リストを再構築
        group_list.controls.clear()
        for method, url in history:
            group_list.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{method} {url}", size=16),
                    dense=True,
                    min_vertical_padding=0,
                    content_padding=0,
                )
            )
        tab_bar = ft.Tabs(
            tabs=tab_manager.build_tabs(),
            selected_index=selected_tab_index,
            expand=True,
            scrollable=True,
            on_change=handle_tab_change,
        )
        page.add(
            ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Column([login_btn], expand=True),
                                        ft.Column([logout_btn], expand=True),
                                    ],
                                    spacing=8,
                                ),
                                ft.Row(
                                    [token_label], alignment=ft.MainAxisAlignment.CENTER
                                ),
                                ft.Container(
                                    ft.Text(
                                        "History", size=18, weight=ft.FontWeight.BOLD
                                    ),
                                    margin=ft.margin.only(top=20, bottom=0),
                                ),
                                group_list,
                                ft.Row([add_group_btn, del_group_btn], spacing=8),
                            ],
                            width=210,
                            expand=False,
                        ),
                        padding=18,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        ft.Column([tab_bar], expand=True),
                        padding=18,
                        expand=True,
                    ),
                ],
                expand=True,
            )
        )
        page.update()

    # 初期UI構築
    rebuild_ui()


if __name__ == "__main__":
    import flet as ft

    ft.app(target=main)
