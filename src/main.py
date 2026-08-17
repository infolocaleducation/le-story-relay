"""LEストーリーリレー: 事業紹介カード動画を毎朝1本ずつInstagramストーリーに投稿する。

- cards.json の enabled なカードを日付ベースでローテーション(状態を持たない決定的な選択)
- 動画は本リポジトリ(公開)の videos/NN.mp4 を raw.githubusercontent.com 経由で配信
- 投稿は Meta Graph API の Content Publishing API (STORIES)
"""
import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v21.0"
ROOT = Path(__file__).resolve().parent.parent
JST = datetime.timezone(datetime.timedelta(hours=9))

# この日にカード01(enabled先頭)を投稿し、以降1日1枚ずつ循環する
ANCHOR = datetime.date(2026, 8, 15)


def load_enabled_cards() -> list[dict]:
    cards = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
    enabled = [c for c in cards if c.get("enabled", True)]
    if not enabled:
        sys.exit("cards.json に enabled なカードがありません。")
    return sorted(enabled, key=lambda c: c["no"])


def select_card(target: datetime.date, override_no: str | None = None) -> dict:
    cards = load_enabled_cards()
    if override_no:
        for c in cards:
            if c["no"] == override_no.zfill(2):
                return c
        sys.exit(f"カード {override_no} は cards.json に無いか enabled ではありません。")
    idx = (target - ANCHOR).days % len(cards)
    return cards[idx]


def video_url_for(card: dict) -> str:
    repo = os.environ["GITHUB_REPOSITORY"]  # 例: infolocaleducation/le-story-relay
    return f"https://raw.githubusercontent.com/{repo}/main/videos/{card['no']}.mp4"


def post_story(video_url: str) -> None:
    ig_user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]

    # 1. メディアコンテナ作成(ストーリー)
    res = requests.post(
        f"{GRAPH}/{ig_user_id}/media",
        data={"media_type": "STORIES", "video_url": video_url, "access_token": token},
        timeout=60,
    )
    res.raise_for_status()
    creation_id = res.json()["id"]

    # 2. メディア処理完了を待つ(動画は時間がかかるため最大5分)
    for _ in range(30):
        status = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=60,
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram メディア処理エラー: {status}")
        time.sleep(10)

    # 3. 公開
    res = requests.post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    res.raise_for_status()
    print(f"Instagram ストーリー投稿に成功しました: media id = {res.json()['id']}")


def cmd_whoami() -> None:
    """トークンで管理しているFBページとIGビジネスアカウントIDの一覧を表示する。

    IG_USER_ID を調べるためのセットアップ補助。IG_ACCESS_TOKEN だけ環境変数に
    設定して実行する。
    """
    token = os.environ["IG_ACCESS_TOKEN"]
    res = requests.get(
        f"{GRAPH}/me/accounts",
        params={"fields": "name,instagram_business_account{id,username}", "access_token": token},
        timeout=60,
    )
    res.raise_for_status()
    for page in res.json().get("data", []):
        ig = page.get("instagram_business_account") or {}
        print(f"FBページ: {page['name']}")
        print(f"  IGアカウント: @{ig.get('username', '(未連携)')} / IG_USER_ID = {ig.get('id', '-')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["post", "select", "whoami"])
    parser.add_argument("--date", help="対象日 YYYY-MM-DD(省略時はJSTの今日)")
    parser.add_argument("--card", help="カード番号の指定(ローテーションを無視して投稿)")
    parser.add_argument("--dry-run", action="store_true", help="投稿せず選択結果のみ表示")
    args = parser.parse_args()

    if args.command == "whoami":
        cmd_whoami()
        return

    target = (
        datetime.date.fromisoformat(args.date)
        if args.date
        else datetime.datetime.now(JST).date()
    )
    card = select_card(target, args.card)
    print(f"対象日 {target} → カード{card['no']}「{card['title']}」")

    if args.command == "select" or args.dry_run:
        return

    post_story(video_url_for(card))


if __name__ == "__main__":
    main()
