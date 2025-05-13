# dynamics-api-desktop-app

Microsoft Dynamics APIと連携するPython製デスクトップアプリケーション。

## 概要

このアプリケーションは、Microsoft Dynamics APIと連携し、デスクトップ上でデータの取得や管理を行うことができます。

## 必要要件

- Python 3.10以上

## インストール

```bash
uv sync
```

`pyproject.toml`の依存パッケージが自動でインストールされます。

## 依存パッケージ

- msal >= 1.32.3
- ttkbootstrap >= 1.13.2

## 使い方

```bash
python -m src.main
```

または

```bash
python -m dynamics-api-app
```
