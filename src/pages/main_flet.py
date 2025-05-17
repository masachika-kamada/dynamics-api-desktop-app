import flet as ft
from src.components.tabs import TabManager

def main(page: ft.Page):
    page.title = "Postman-like API Client UI Mock (Flet)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800

    login_btn = ft.FilledButton("Login", width=100)
    logout_btn = ft.OutlinedButton("Logout", width=100)
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
    add_group_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, tooltip="Add Group", mini=True)
    del_group_btn = ft.FloatingActionButton(icon=ft.Icons.DELETE, tooltip="Delete Group", bgcolor=ft.Colors.RED_400, mini=True)

    # --- ログイン処理 ---
    def on_login(e):
        nonlocal token
        from src.api.auth_client import Auth
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
        rebuild_ui()

    tab_manager = TabManager(
        on_tab_change=handle_tab_change,
        on_add_tab=handle_add_tab,
        on_close_tab=handle_close_tab,
        on_send=on_send
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
                    content_padding=0
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
    rebuild_ui()

if __name__ == "__main__":
    import flet as ft
    ft.app(target=main)
