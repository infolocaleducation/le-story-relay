# LEストーリーリレー

一般社団法人 Local Education の事業紹介カード動画（10本）を、毎朝8時(JST)に1本ずつ
ローテーションで Instagram ストーリーに自動投稿するシステム。

- 動画は `videos/01.mp4`〜`10.mp4`（15秒・1080×1920）。番号と事業名の対応は `cards.json`
- カードの選択は日付ベースの決定的ローテーション（`src/main.py` の `ANCHOR` 起点）。
  サーバーも状態も不要で、`cards.json` の `enabled: false` で一時的に外せる
- 投稿は Meta Graph API（Content Publishing API / STORIES）。動画は本リポジトリ（公開）の
  raw URL を Graph API に渡す方式（このためリポジトリは Public にしておくこと）
- ハイライトへの追加は手動運用

## 仕組み

| ワークフロー | 内容 |
|---|---|
| `daily-post.yml` | 毎朝 8:07/8:37/9:13/10:42 JST の4回起動（GitHub cronの遅延・スキップ保険）。`output/last_posted.txt` の対象日マーカーで最初の成功1回だけ投稿 |
| `refresh-ig-token.yml` | 毎週月曜にトークン期限をチェック。残り21日未満で自動更新（`GH_PAT` 登録時）またはIssueでリマインド |

## セットアップ（Actions Secrets）

| Secret | 内容 |
|---|---|
| `IG_USER_ID` | LE公式IGアカウントのビジネスアカウントID（`python -m src.main whoami` で確認可能） |
| `IG_ACCESS_TOKEN` | 長期アクセストークン（60日）。必要権限: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`, `business_management` |
| `META_APP_ID` / `META_APP_SECRET` | トークン更新チェック用（gotoji-compass-notifier と同じMetaアプリを流用可） |
| `GH_PAT`（任意） | secrets 書き込み権限のあるPAT。登録するとトークンが全自動更新になる |

## 手動操作

- **お試し実行**: Actions → daily-post → Run workflow → `dry_run: true`（投稿せずカード選択のみ確認）
- **特定カードを今すぐ投稿**: `card` に番号（例: `02`）を入れて Run workflow
- **カードを一時的に外す**: `cards.json` の該当カードを `"enabled": false` にしてコミット
  （例: たがわ教育フェス開催後の05）。残りのカードで自動的にローテーションが継続する
- **動画の差し替え**: `videos/NN.mp4` を上書きコミットするだけ

## 関連

- 動画の生成元素材・仕様: Google Drive「LEストーリー素材」（cards.json / generate_card.sh / README_量産指示書.md）
- 同型の先行システム: [gotoji-compass-notifier](https://github.com/infolocaleducation/gotoji-compass-notifier)
