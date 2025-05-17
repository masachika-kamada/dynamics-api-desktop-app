import msal


class Auth:
    def __init__(self):
        client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"
        authority = "https://login.microsoftonline.com/organizations"
        self.app = msal.PublicClientApplication(client_id, authority=authority)
        self.token = None
        self.tokens = {}  # スコープごとのトークンキャッシュ

    def acquire_token(self, scopes):
        # 既存の後方互換メソッド（最初のスコープのみでキャッシュ）
        scope_str = " ".join(scopes)
        if scope_str in self.tokens:
            return self.tokens[scope_str]
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(scopes, account=accounts[0])
            if "access_token" in result:
                self.tokens[scope_str] = result["access_token"]
                return result["access_token"]
            else:
                print(
                    "Silent token acquisition failed:", result.get("error_description")
                )
                return None
        else:
            result = self.app.acquire_token_interactive(scopes=scopes)
            if "access_token" in result:
                self.tokens[scope_str] = result["access_token"]
                return result["access_token"]
            else:
                print(
                    "Interactive token acquisition failed:",
                    result.get("error_description"),
                )
                return None

    def acquire_token_for_scope(self, scopes, force_interactive=False):
        """
        指定スコープでトークンを取得（キャッシュ優先、silent→interactive）
        scopes: list[str]
        force_interactive: Trueならsilent失敗時にinteractiveも試す
        """
        scope_str = " ".join(scopes)
        if scope_str in self.tokens:
            return self.tokens[scope_str]
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(scopes, account=accounts[0])
            if "access_token" in result:
                self.tokens[scope_str] = result["access_token"]
                return result["access_token"]
            elif force_interactive:
                result = self.app.acquire_token_interactive(scopes=scopes)
                if "access_token" in result:
                    self.tokens[scope_str] = result["access_token"]
                    return result["access_token"]
                else:
                    print(
                        "Interactive token acquisition failed:",
                        result.get("error_description"),
                    )
                    return None
            else:
                print(
                    "Silent token acquisition failed:", result.get("error_description")
                )
                return None
        else:
            # アカウントがなければinteractiveのみ
            if force_interactive:
                result = self.app.acquire_token_interactive(scopes=scopes)
                if "access_token" in result:
                    self.tokens[scope_str] = result["access_token"]
                    return result["access_token"]
                else:
                    print(
                        "Interactive token acquisition failed:",
                        result.get("error_description"),
                    )
                    return None
            else:
                print("No account found and force_interactive=False")
                return None


if __name__ == "__main__":
    auth = Auth()
    scopes = ["https://api.bap.microsoft.com/.default"]
    token = auth.acquire_token(scopes)
    if token:
        print("Access token acquired:", token)
    else:
        print("Failed to acquire access token.")
