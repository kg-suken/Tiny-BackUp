import os
import shutil
from rich.console import Console
import json
from urllib.request import Request, urlopen

console = Console()


webhook_url = 'https://discord.com/api/webhooks/'

import json
from urllib.request import Request, urlopen

def post_discord(message: str, webhook_url: str, color: int):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (private use) Python-urllib/3.10",
    }
    
    # 送信するJSONデータ
    data = {
        "embeds": [
            {
                "title": "バックアップシステム",
                "description": message,
                "color": color,
            }
        ]
    }

    # リクエストの作成
    request = Request(
        webhook_url,
        data=json.dumps(data).encode(),
        headers=headers,
    )

    # リクエスト送信とレスポンス確認
    with urlopen(request) as res:
        assert res.getcode() == 204


def sync_directories(source_dir, backup_dir):
    copied_files = 0
    deleted_files = 0
    allowed_time_difference = 3  # 秒）のズレを許容

    post_discord('バックアップを開始します', webhook_url,1752220)
    # 表示用の行を準備
    with console.status("[blue]Scanning...", spinner="dots") as status:
        # ソースディレクトリのファイルをバックアップディレクトリに同期する
        for root, dirs, files in os.walk(source_dir):
            relative_path = os.path.relpath(root, source_dir)
            backup_subdir = os.path.join(backup_dir, relative_path)

            # バックアップ先にサブディレクトリがない場合は作成
            if not os.path.exists(backup_subdir):
                os.makedirs(backup_subdir)

            # ファイルのコピー
            for file in files:
                source_file = os.path.join(root, file)
                backup_file = os.path.join(backup_subdir, file)

                # スキャン中のファイルを1行だけ表示
                status.update(f"[blue]Scanning: {source_file}")

                # ファイルがバックアップ先に存在するか確認し、最終更新時間を比較してコピー
                try:
                    if not os.path.exists(backup_file):
                        shutil.copy2(source_file, backup_file)
                        console.print(f"[green]Copied: {source_file} to {backup_file}")
                        copied_files += 1
                    else:
                        # 更新時間を比較し、差が1分以上であればコピー
                        source_mtime = os.path.getmtime(source_file)
                        backup_mtime = os.path.getmtime(backup_file)
                        time_difference = abs(source_mtime - backup_mtime)

                        if time_difference > allowed_time_difference:
                            shutil.copy2(source_file, backup_file)
                            console.print(f"[green]Copied: {source_file} to {backup_file} (time difference: {time_difference:.2f} seconds)")
                            copied_files += 1
                except OSError as e:
                    post_discord(f'バックアップ-コピーエラー:{source_file} to {backup_file}', webhook_url,15548997)
                    console.print(f"[bold red]Error copying {source_file} to {backup_file}: {e}[/bold red]")

        # バックアップディレクトリからソースに存在しないファイルやフォルダを削除
        for root, dirs, files in os.walk(backup_dir):
            relative_path = os.path.relpath(root, backup_dir)
            source_subdir = os.path.join(source_dir, relative_path)

            # ソースディレクトリに存在しないディレクトリを削除
            if not os.path.exists(source_subdir):
                try:
                    shutil.rmtree(root)
                    console.print(f"[yellow]Deleted directory: {root}[/yellow]")
                    deleted_files += 1
                    continue
                except OSError as e:
                    post_discord(f'バックアップ-ディレクトリ削除エラー:{root}', webhook_url,15548997)
                    console.print(f"[bold red]Error deleting directory {root}: {e}[/bold red]")

            # ソースディレクトリに存在しないファイルを削除
            for file in files:
                backup_file = os.path.join(root, file)
                source_file = os.path.join(source_subdir, file)

                status.update(f"[blue]Scanning for deletion: {backup_file}")

                if not os.path.exists(source_file):
                    try:
                        os.remove(backup_file)
                        console.print(f"[yellow]Deleted file: {backup_file}[/yellow]")
                        deleted_files += 1
                    except OSError as e:
                        post_discord(f'バックアップ-ファイル削除エラー:{backup_file}', webhook_url,15548997)
                        console.print(f"[bold red]Error deleting file {backup_file}: {e}[/bold red]")

    console.print(f"\n[bold green]Sync complete! Copied files: {copied_files}, Deleted files/directories: {deleted_files}[/bold green]")
    post_discord(f'バックアップ完了!:Copied files: {copied_files}, Deleted files/directories: {deleted_files}', webhook_url,5620992)


source_dir = "ソースディレクトリ"
backup_dir = "バックアップディレクトリ"

sync_directories(source_dir, backup_dir)

