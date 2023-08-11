"""
The japanese translation

Copyright
---------
Animenosekai
    Original Author, MIT License
"""

from nasse.localization.base import Localization


class JapaneseLocalization(Localization):
    """
    The japanese version of the docs generation
    """
    __native__ = "日本語"

    sections = "セクション"
    getting_started = "はじめに"

    yes = "はい"
    no = "いいえ"

    no_description = "詳細なし"
    using_method = "{method}を使って"

    # Authentication
    authentication = "認証"
    no_auth_rule = "認証ルールが定義されていません"
    no_login = "ログインは**不要**です"
    login_with_types_required = "{types} アカウントでのログインが**必要**です"
    login_with_types_optional = "{types} アカウントでのログインは**任意**です"
    login_required = "ログインは**必要**です"
    login_optional = "ログインは**任意**です"
    login_suffix_only_verified = " （検証のみ）"

    # User sent values
    parameters = "パラメーター"
    headers = "ヘッダー"
    cookies = "クッキー"
    dynamic_url = "ダイナミックURL"

    name = "名前"
    description = "詳細"
    required = "必要"
    type = "タイプ"

    # Example
    example = "例"

    # Response
    response = "レスポンス"  # 応答や解答より「レスポンス」の方が使われているよう
    example_response = "レスポンスの例"
    not_json_response = "このエンドポイントは、JSON形式のレスポンスを返さないようです。"

    # Response description
    returns = "返したフィールド"
    field = "フィールド"
    nullable = "null可能"

    # Errors
    possible_errors = "起こりうるエラー"
    exception = "エラー名"
    code = "コード"

    # Index
    index = "インデックス"
    return_to_index = "インデックスに戻る"

    # Postman
    postman_description = "{name} APIインターフェイスでの「{section}」セクションの全てのエンドポイント"

    # Headers
    getting_started_header = '''
# {name} APIリファレンス

{name} APIリファレンスへようこそ！

## 全体的に

### レスポンスの形式

一般的に、JSONで形式されたレスポンスは以下の形に返されます（エラーが発生された時もこの形で返されます）

```json
{{
    "success": true,
    "message": "出来ました!",
    "error": null,
    "data": {{}}
}}
```

| フィールド     | 詳細                            |  null可能         |
| ------------ | ------------------------------  | ---------------- |
| `success`    | リクエストが成功したかどうか         | いいえ            |
| `message`    | 何があったか説明する文章            | はい             |
| `error`      | エラーが発生した時のエラー名         | はい             |
| `data`       | 解答のデータ、リクエストされたデータ  | いいえ            |

### エラー

サーバー上でも、リクエストからでも、様々なエラーが発生する可能性があります。

特定なエラーはそれぞれのエンドポイントドキュメントで説明されていなすが、以下に一般的に発生可能のエラーを説明します

| エラー名                     | 詳細                                                                                                             | コード  |
| --------------------------- | --------------------------------------------------------------------------------------------------------------- | ----- |
| `SERVER_ERROR`              | リクエストの処理中でサーバー上のエラーが発生した時                                                                       | 500   |
| `MISSING_CONTEXT`           | Nasseコンテキストに居ないのに、Nasseコンテキストのみで利用可能のデータをアクセスしようとしたとき                               | 500   |
| `INTERNAL_SERVER_ERROR`     | システム上でエラーが発生した時                                                                                       | 500   |
| `METHOD_NOT_ALLOWED`        | HTTPリクエストメソッドを間違えた時                                                                                   | 405   |
| `CLIENT_ERROR`              | リクエストで何か足りないかダメな時                                                                                    | 400   |
| `INVALID_TYPE`              | Nasseが送られたデータを正しい型に変換できなかった時                                                                     | 400   |
| `MISSING_VALUE`             | リクエストから何か足りない時                                                                                         | 400   |
| `MISSING_PARAM`             | 必要のパラメーターが一つリクエストから不足している時                                                                     | 400   |
| `MISSING_DYNAMIC`           | ダイナミックURLのパーツが一つURLから不足している時                                                                      | 400   |
| `MISSING_HEADER`            | 必要のヘッダーが一つリクエストから不足している時                                                                        | 400   |
| `MISSING_COOKIE`            | 必要のクッキーが一つリクエストから不足している時                                                                        | 400   |
| `AUTH_ERROR`                | 認証中にエラーが発生した時                                                                                           | 403   |

### 認証されたリクエスト

ユーザーがログインされていること

ユーザーのログインが必要な場合、「Authorization」ヘッダーがログインの時に送られたトークンに設定されることが必要です。

「{id}_token」のパラメーターと「__{id}_token」のクッキーも利用可能ですがこれらは優先されません

エンドポイントの認証ルールが「検証のみ」になっている場合は、アカウントがデータベースから読み込む事なく、トークンの形式や有効期限をチェックするだけです。

### デバッグモード

デバッグモードが有効の時(`-d`か`--debug`)は、色々な情報が`debug`フィールドで返送されて、`DEBUG`のロギングレベルが選ばれます。

'debug'フィルーどは重大なエラー（`INTERNAL_SERVER_ERROR`、 `METHOD_NOT_ALLOWED`、 など）しない限り、送られます。(重大なエラーが発生したら、なるべくもう一度エラーが発生しないようにする必要があります)

`call_stack`フィールドは`call_stack`パラメーターをリクエストで入れる時だけ送信されます。

```json
{{
    "success": true,
    "message": "リクエストが成功しませんでした",
    "error": null,
    "data": {{
        "username": "Animenosekai"
    }},
    "debug": {{
        "time": {{
            "global": 0.036757,
            "verification": 0.033558,
            "authentication": 0.003031,
            "processing": 4.9e-05,
            "formatting": 0.0001
        }},
        "ip": "127.0.0.1",
        "headers": {{
            "Host": "api.{id}.com",
            "Connection": "close",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-fr",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
        }},
        "values": {{}},
        "domain": "api.{id}.com",
        "logs": [
            "1636562693.036563｜[INFO] [nasse.receive.Receive.__call__] → Incoming GET request to /account/name from 127.0.0.1",
            "1636562693.070008｜[ERROR] [nasse.exceptions.base.MissingToken.__init__] An authentication token is missing from the request"
        ],
        "call_stack": [
            "pass the 'call_stack' parameter to get the call stack"
        ]
    }}
}}
```

'''

    section_header = '''
# {name} セクションのAPIリファレンス

このファイルは「{name}」セクションの全てのエンドポイントを説明します。
'''

    # TUI

    # Footer
    tui_history = "履歴"
    tui_result = "結果"
    tui_explorer = "エクスプローラー"
    tui_submit = "送信"
    tui_options = "設定"
    tui_quit = "終了"

    # History
    # WARNING: This should stay under 3 characters to avoid having styling issues
    tui_min = "低"
    tui_average = "平均"
    tui_max = "高"

    # Explorer
    tui_reset = "リセット"

    # Request
    tui_request = "リクエスト"
    tui_name = "名前"
    tui_value = "内容"
    tui_path = "道"
    # tui_parameters = "Parameters"
    # tui_headers = "Headers"
    # tui_cookies = "Cookies"
    tui_file = "ファイル"
    tui_add_file = "ファイルを追加"
    tui_data = "データ"
    tui_add_data_file = "データファイルを追加"

    # Options
    tui_language = "言語"
    tui_language_notice = "言語変化を有効するには再起動して下さい"
    tui_base_url = "ベースURL"
    tui_base_url_placeholder = "リクエストとエクスプローラーのベースURL"
    tui_endpoints_update = "エンドポイントの更新度"
    tui_endpoints_update_placeholder = "エンドポイントの更新までの時間 (秒)"
    tui_history_limit = "履歴制限"
    tui_history_limit_placeholder = "履歴に残る最高のリクエスト数"
    tui_timeout = "タイムアウト"
    tui_timeout_placeholder = "タイムアウト (秒)"
    tui_redirects = "リダイレクト"
    tui_allow_redirects = "リダイレクトの許可"
    tui_proxies = "プロキシ"
    tui_security = "セキュリティー"
    tui_verify_request = "リクエストの確認"
    tui_certificate_files = "認証ファイル"
    tui_add_certificate = "認証ファイルの追加"

    # Result
    tui_start_prompt = "まずはリクエストを送信して下さい"
    tui_content = "内容"
    tui_no_content = "内容を表示できません"
    tui_contacting = "{url}を連絡しています"
    tui_files = "ファイル"
    tui_error = "エラー"

    # File Explorer
    tui_filter = "フィルター"

    # Quit
    tui_quit_confirmation = "本当に終了しますか？"
    tui_cancel = "戻る"
