import json
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap import ttk

from src.auth_client import Auth
from src.api_client import APIClient
from src.models import ApiRequest

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Custom Postman-like API Client (tkinter + ttkbootstrap)")
        self.geometry("1100x700")
        self.style = Style("superhero")  # ttkbootstrapのテーマを指定
        self.style.configure(".", font=("TkDefaultFont", 11))
        self.style.configure("TButton", font=("TkDefaultFont", 11))

        # 標準タイトルバー（カスタムタイトルバーは使わない）

        self.auth = Auth()
        self.token = None
        self.requests = []
        self.selected_idx = None

        self.create_widgets()


    def create_widgets(self):
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=LEFT, fill=Y, padx=(0, 10), expand=False)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Left: Request List
        ttk.Label(left_frame, text="Requests").pack(anchor=NW)
        self.req_listbox = tk.Listbox(left_frame, width=30, height=25, font=("TkDefaultFont", 11))
        self.req_listbox.pack(fill=Y, expand=True)
        self.req_listbox.bind("<<ListboxSelect>>", self.on_req_selected)
        ttk.Button(left_frame, text="Delete", command=self.delete_request, bootstyle=DANGER).pack(fill=X, pady=5)

        # Right: Auth section
        auth_frame = ttk.Frame(right_frame)
        auth_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(auth_frame, text="Scopes:").pack(side=LEFT)
        self.scope_var = tk.StringVar(value="https://api.bap.microsoft.com/.default")
        ttk.Entry(auth_frame, textvariable=self.scope_var, width=40, font=("TkDefaultFont", 11)).pack(side=LEFT, padx=5)
        ttk.Button(auth_frame, text="Login", command=self.authenticate, bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        ttk.Button(auth_frame, text="Logout", command=self.logout, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        self.token_label = ttk.Label(auth_frame, text="Not Authenticated", bootstyle=WARNING)
        self.token_label.pack(side=LEFT, padx=10)

        # Right: Request editor
        editor_frame = ttk.Frame(right_frame)
        editor_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(editor_frame, text="Name").grid(row=0, column=0, sticky=W, pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.name_var, width=30, font=("TkDefaultFont", 11)).grid(row=0, column=1, sticky=W, padx=5, pady=4)

        ttk.Label(editor_frame, text="Method").grid(row=1, column=0, sticky=W, pady=4)
        self.method_var = tk.StringVar(value="GET")
        method_frame = ttk.Frame(editor_frame)
        method_frame.grid(row=1, column=1, sticky=W, padx=5, pady=4)
        self.method_buttons = {}
        for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            btn = ttk.Button(method_frame, text=m, width=6, bootstyle=PRIMARY if m == "GET" else SECONDARY, command=lambda m=m: self.select_method(m))
            btn.pack(side=LEFT, padx=2)
            self.method_buttons[m] = btn

        # --- 以下をcreate_widgets内に戻す ---
        ttk.Label(editor_frame, text="URL").grid(row=2, column=0, sticky=W, pady=4)
        self.url_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.url_var, width=50, font=("TkDefaultFont", 11)).grid(row=2, column=1, sticky=W, padx=5, pady=4)

        ttk.Label(editor_frame, text="Headers (JSON)").grid(row=3, column=0, sticky=NW, pady=4)
        self.headers_text = tk.Text(editor_frame, width=50, height=6, font=("TkDefaultFont", 11))
        self.headers_text.grid(row=3, column=1, sticky=W, padx=5, pady=4)
        self.set_default_headers()

        ttk.Label(editor_frame, text="Payload (JSON)").grid(row=4, column=0, sticky=NW, pady=4)
        self.payload_text = tk.Text(editor_frame, width=50, height=6, font=("TkDefaultFont", 11))
        self.payload_text.grid(row=4, column=1, sticky=W, padx=5, pady=4)
        self.payload_text.insert("1.0", "{}")

        btn_frame = ttk.Frame(editor_frame)
        btn_frame.grid(row=5, column=1, sticky=E, pady=5)
        ttk.Button(btn_frame, text="Save", command=self.add_or_update_request, bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self.clear_inputs, bootstyle=SECONDARY).pack(side=LEFT, padx=2)

        # Right: Execute & Result
        exec_frame = ttk.Frame(right_frame)
        exec_frame.pack(fill=X, pady=(0, 10))
        ttk.Button(exec_frame, text="Send", command=self.execute_request, bootstyle=SUCCESS).pack(side=LEFT, padx=2)

        ttk.Label(right_frame, text="Result").pack(anchor=NW)
        self.result_text = tk.Text(right_frame, width=80, height=10, state="normal", font=("TkDefaultFont", 11))
        self.result_text.pack(fill=BOTH, expand=True)

    def select_method(self, method):
        self.method_var.set(method)
        for m, btn in self.method_buttons.items():
            btn.config(bootstyle=PRIMARY if m == method else SECONDARY)

    def set_default_headers(self):
        default_headers = {
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json"
        }
        self.headers_text.delete("1.0", tk.END)
        self.headers_text.insert("1.0", json.dumps(default_headers, indent=2, ensure_ascii=False))

    def authenticate(self):
        scopes = [s.strip() for s in self.scope_var.get().split(",")]
        token = self.auth.acquire_token(scopes)
        if token:
            self.token = token
            self.token_label.config(text="Authenticated", bootstyle=SUCCESS)
            messagebox.showinfo("Auth", "Access token acquired successfully")
        else:
            self.token = None
            self.token_label.config(text="Not Authenticated", bootstyle=WARNING)
            messagebox.showwarning("Auth", "Failed to acquire access token")

    def logout(self):
        self.token = None
        self.token_label.config(text="Not Authenticated", bootstyle=WARNING)
        messagebox.showinfo("Logout", "Logged out")

    def add_or_update_request(self):
        try:
            headers = json.loads(self.headers_text.get("1.0", tk.END))
        except Exception as e:
            messagebox.showwarning("Error", f"Invalid header JSON: {e}")
            return
        try:
            payload = json.loads(self.payload_text.get("1.0", tk.END))
        except Exception as e:
            payload = None  # GET等では空でもOK

        name = self.name_var.get().strip() or f"Request {len(self.requests)+1}"
        method = self.method_var.get()
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter endpoint URL")
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
        self.name_var.set("")
        self.method_var.set("GET")
        self.url_var.set("")
        self.set_default_headers()
        self.payload_text.delete("1.0", tk.END)
        self.payload_text.insert("1.0", "{}")
        self.selected_idx = None

    def refresh_req_list(self):
        self.req_listbox.delete(0, tk.END)
        for req in self.requests:
            self.req_listbox.insert(tk.END, f"{req.name} ({req.method} {req.url})")

    def on_req_selected(self, event):
        idxs = self.req_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        req = self.requests[idx]
        self.selected_idx = idx
        self.name_var.set(req.name)
        self.method_var.set(req.method)
        self.url_var.set(req.url)
        self.headers_text.delete("1.0", tk.END)
        self.headers_text.insert("1.0", json.dumps(req.headers, indent=2, ensure_ascii=False))
        self.payload_text.delete("1.0", tk.END)
        self.payload_text.insert("1.0", json.dumps(req.payload, indent=2, ensure_ascii=False) if req.payload else "")

    def delete_request(self):
        idxs = self.req_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        del self.requests[idx]
        self.refresh_req_list()
        self.clear_inputs()

    def execute_request(self):
        idxs = self.req_listbox.curselection()
        if not idxs:
            messagebox.showwarning("Error", "Please select a request")
            return
        if not self.token:
            messagebox.showwarning("Error", "Please authenticate first")
            return
        req = self.requests[idxs[0]]
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
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", json.dumps(response, indent=2, ensure_ascii=False))
        except Exception as e:
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"Request failed: {e}")
