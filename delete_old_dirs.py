#!/usr/bin/env python3

import os
import sys
import argparse
import time
import subprocess


def get_creation_time(directory):
    """ディレクトリの作成日時（UNIXタイム）を取得する。
    取得できない場合は ctime（inodeの変更時刻）を使用。
    """
    try:
        birth_time = int(
            subprocess.check_output(["stat", "-c", "%W", directory]).decode().strip()
        )
        if birth_time > 0:
            return birth_time
    except Exception:
        pass  # stat -c %W が失敗した場合は ctime を試す

    # 取得できなかった場合は ctime（inodeの変更時刻）を使用
    try:
        return int(os.stat(directory).st_ctime)
    except Exception:
        return None


def format_timestamp(timestamp):
    """UNIXタイムスタンプを YYYY-MM-DD HH:MM:SS 形式に変換"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def main():
    parser = argparse.ArgumentParser(
        description="Delete directories created before a specific date."
    )
    parser.add_argument(
        "date",
        type=str,
        help="Target date in YYYY-MM-DD format (directories before this date will be deleted)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which directories would be deleted without actually deleting them",
    )

    args = parser.parse_args()

    # 入力された日付を UNIX タイムに変換
    try:
        target_timestamp = int(time.mktime(time.strptime(args.date, "%Y-%m-%d")))
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        sys.exit(1)

    print(f"Target date: {args.date} (UNIX timestamp: {target_timestamp})")

    # カレントディレクトリ内のフォルダを取得
    directories = [d for d in os.listdir() if os.path.isdir(d)]

    if not directories:
        print("No directories found.")
        sys.exit(0)

    delete_candidates = []

    for directory in directories:
        creation_time = get_creation_time(directory)

        if creation_time is None:
            continue  # 作成日時が取得できない場合はスキップ

        if creation_time < target_timestamp:
            delete_candidates.append((directory, creation_time))

    # 削除予定のディレクトリを作成日時順（昇順）にソート

    if args.dry_run:
        print(f"Dry-run mode: {len(delete_candidates)} directories would be deleted.")
        for directory, creation_time in delete_candidates:
            print(
                f"Would delete: {directory} (Created: {format_timestamp(creation_time)})"
            )
    else:
        for directory, creation_time in delete_candidates:
            print(f"Deleting: {directory} (Created: {format_timestamp(creation_time)})")
            try:
                subprocess.run(["rm", "-rf", directory], check=True)
            except Exception as e:
                print(f"Error deleting {directory}: {e}")

        print(f"Deleted {len(delete_candidates)} directories.")


if __name__ == "__main__":
    main()
