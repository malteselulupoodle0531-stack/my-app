import json
import re
import streamlit as st

# ----------------------------------------------------
# ページ基本設定
# ----------------------------------------------------
st.set_page_config(
    page_title="フリマ・EC一括出品アシスタント",
    page_icon="📦",
    layout="wide",
)

st.title("📦 フリマ・EC自動出品アシスタント")

# ----------------------------------------------------
# セッション状態の初期化
# ----------------------------------------------------
default_fields = {
    "management_number": "",
    "title": "",
    "description": "",
    "price": 0,
    "condition": "目立った傷や汚れなし",
    "category": "",
    "brand": "",
    "size": "",
    "selected_sites": ["mercari", "yahoo_auction"],
}

for key, val in default_fields.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------------------------------------
# 🎯 対象サイトの選択（列方向展開・チェックボックス式）
# ----------------------------------------------------
st.subheader("🎯 出品対象サイトを選択")

site_definitions = [
    ("mercari", "メルカリ", 40),
    ("mercari_shops", "メルカリShops", 40),
    ("yahoo_fleamarket", "Yahoo!フリマ", 65),
    ("yahoo_auction", "ヤフオク!", 65),
    ("rakuma", "ラクマ", 40),
    ("base", "BASE", 100),
    ("stores", "STORES", 100),
]

cols_site = st.columns(len(site_definitions))
current_selected = []

for idx, (s_key, s_label, _) in enumerate(site_definitions):
    with cols_site[idx]:
        is_checked = s_key in st.session_state["selected_sites"]
        if st.checkbox(s_label, value=is_checked, key=f"chk_{s_key}"):
            current_selected.append(s_key)

st.session_state["selected_sites"] = current_selected

st.markdown("---")

# ----------------------------------------------------
# 📷 1. 画像 ＆ 📝 2. 生成テキスト貼り付け ( 7 : 3 レイアウト )
# ----------------------------------------------------
col_left, col_right = st.columns([7, 3])

with col_left:
    st.subheader("1. 📷 出品用画像（確認・ドラッグ用）")
    uploaded_images = st.file_uploader(
        "画像をアップロード（複数可）",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    if uploaded_images:
        img_cols = st.columns(min(len(uploaded_images), 5))
        for i, img_file in enumerate(uploaded_images):
            with img_cols[i % 5]:
                st.image(img_file, caption=img_file.name, use_container_width=True)
    else:
        st.info("画像をここにドラッグ＆ドロップまたは選択してください。")

with col_right:
    st.subheader("2. 📝 Web版AIの生成結果を貼り付け")
    ai_raw_text = st.text_area(
        "AI生成テキスト",
        height=320,
        placeholder="""例:
管理番号: A-102
タイトル: 【美品】Nike エアマックス 27cm
価格: 8500
状態: 目立った傷や汚れなし
カテゴリ: メンズ > 靴 > スニーカー
ブランド: NIKE
サイズ: 27cm

商品説明:
履き心地の良いスニーカーです。数回着用の美品です。""",
    )

    if st.button("🪄 貼り付けテキストから各項目へ反映", use_container_width=True):
        if ai_raw_text:
            # 各単一項目（1行）の抽出パターン
            patterns = {
                "management_number": r"管理番号[:：]?\s*(.*)",
                "title": r"タイトル[:：]?\s*(.*)",
                "price": r"価格[:：]?\s*(\d+)",
                "condition": r"(?:状態|商品の状態)[:：]?\s*(.*)",
                "category": r"カテゴリ[:：]?\s*(.*)",
                "brand": r"ブランド[:：]?\s*(.*)",
                "size": r"サイズ[:：]?\s*(.*)",
            }

            for key, pat in patterns.items():
                match = re.search(pat, ai_raw_text)
                if match:
                    val = match.group(1).strip()
                    if key == "price":
                        try:
                            st.session_state["price"] = int(val)
                        except ValueError:
                            pass
                    else:
                        st.session_state[key] = val

            # 商品説明文の複数行抽出（「商品説明:」〜次の項目またはテキスト末尾まで）
            desc_match = re.search(
                r"商品説明[:：]?\s*\n?(.*?)(?=\n(?:管理番号|タイトル|価格|状態|商品の状態|カテゴリ|ブランド|サイズ)[:：]|\Z)",
                ai_raw_text,
                re.DOTALL,
            )

            if desc_match and desc_match.group(1).strip():
                st.session_state["description"] = desc_match.group(1).strip()
            else:
                # 「商品説明:」の見出しが無い場合は全文を入れる（必要に応じて調整）
                st.session_state["description"] = ai_raw_text.strip()

            st.success("各入力欄へ値を抽出・反映しました！")
            st.rerun()

st.markdown("---")

# ----------------------------------------------------
# ✏️ 3. 詳細入力テキストボックス挿入エリア
# ----------------------------------------------------
st.subheader("3. ✏️ 商品詳細情報の編集・手動調整")

row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
with row1_col1:
    st.session_state["management_number"] = st.text_input(
        "管理番号", value=st.session_state["management_number"]
    )
with row1_col2:
    st.session_state["price"] = st.number_input(
        "価格 (円)", value=int(st.session_state["price"]), step=100
    )
with row1_col3:
    conditions = [
        "新品・未使用",
        "未使用に近い",
        "目立った傷や汚れなし",
        "やや傷や汚れあり",
        "傷や汚れあり",
    ]
    curr_idx = (
        conditions.index(st.session_state["condition"])
        if st.session_state["condition"] in conditions
        else 2
    )
    st.session_state["condition"] = st.selectbox(
        "商品の状態", conditions, index=curr_idx
    )
with row1_col4:
    st.session_state["size"] = st.text_input("サイズ", value=st.session_state["size"])

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.session_state["category"] = st.text_input(
        "カテゴリ", value=st.session_state["category"]
    )
with row2_col2:
    st.session_state["brand"] = st.text_input(
        "ブランド", value=st.session_state["brand"]
    )

st.session_state["title"] = st.text_input(
    "商品タイトル", value=st.session_state["title"]
)
st.session_state["description"] = st.text_area(
    "商品説明文", value=st.session_state["description"], height=180
)

st.markdown("---")

# ----------------------------------------------------
# 📋 4. 整形結果・データ確認（各サイト用JSON出力）
# ----------------------------------------------------
st.subheader("4. ✂️ 整形結果・データ確認")
st.info("💡 選択中の各サイトに最適化されたJSONです。右上のコピーアイコンを押してChrome拡張機能へ貼り付けてください。")

selected_site_keys = st.session_state["selected_sites"]

if not selected_site_keys:
    st.warning("⚠️ トップの「出品対象サイトを選択」で1つ以上のサイトにチェックを入れてください。")
else:
    # 選択されたサイトに対応する定義のみ抽出
    target_site_defs = [s for s in site_definitions if s[0] in selected_site_keys]
    
    # サイトごとのタブメニューを作成
    tab_labels = [s[1] for s in target_site_defs] + ["共通・全サイト汎用JSON"]
    site_tabs = st.tabs(tab_labels)

    # 各サイト個別タブの出力
    for idx, (s_key, s_label, max_len) in enumerate(target_site_defs):
        with site_tabs[idx]:
            # タイトルの文字数自動調整
            raw_title = st.session_state["title"]
            opt_title = raw_title[:max_len] if len(raw_title) > max_len else raw_title

            # 説明文に管理番号を含める処理
            raw_desc = st.session_state["description"]
            mgmt_num = st.session_state["management_number"]
            if mgmt_num and "【管理番号】" not in raw_desc:
                final_desc = f"{raw_desc}\n\n【管理番号】{mgmt_num}"
            else:
                final_desc = raw_desc

            site_json_payload = {
                "site": s_key,
                "title": opt_title,
                "description": final_desc,
                "price": st.session_state["price"],
                "condition": st.session_state["condition"],
                "category": st.session_state["category"],
                "brand": st.session_state["brand"],
                "size": st.session_state["size"],
                "management_number": mgmt_num,
            }

            st.caption(f"📌 **{s_label}用パラメータ** （タイトル制限: {max_len}文字 / 現在: {len(opt_title)}文字）")
            st.code(json.dumps(site_json_payload, ensure_ascii=False, indent=2), language="json")

    # 最後の汎用全データ出力タブ
    with site_tabs[-1]:
        all_export_payload = {
            "management_number": st.session_state["management_number"],
            "title": st.session_state["title"],
            "description": st.session_state["description"],
            "price": st.session_state["price"],
            "condition": st.session_state["condition"],
            "category": st.session_state["category"],
            "brand": st.session_state["brand"],
            "size": st.session_state["size"],
            "target_sites": st.session_state["selected_sites"],
        }
        st.caption("📌 **選択された全サイト・基本情報を含む統合データ**")
        st.code(json.dumps(all_export_payload, ensure_ascii=False, indent=2), language="json")
