import msal

class Auth:
    def __init__(self):
        client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"
        authority = "https://login.microsoftonline.com/organizations"
        self.app = msal.PublicClientApplication(client_id, authority=authority)
        self.token = None

    def acquire_token(self, scopes):
        accounts = self.app.get_accounts()
        if accounts:
            # if an account is found, token can be acquired silently
            result = self.app.acquire_token_silent(scopes, account=accounts[0])
            if "access_token" in result:
                return result["access_token"]
            else:
                print("Silent token acquisition failed:", result.get("error_description"))
                return None
        else:
            # if no account is found, interactive authentication is required
            result = self.app.acquire_token_interactive(scopes=scopes)
            if "access_token" in result:
                return result["access_token"]
            else:
                print("Interactive token acquisition failed:", result.get("error_description"))
                return None
