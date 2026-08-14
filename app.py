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
    "condition": "やや傷や汚れあり",
    "category": "",
    "brand": "",
    "size": "",
    "selected_sites": [
        "mercari",
        "mercari_shops",
        "yahoo_fleamarket",
        "yahoo_auction",
        "rakuma",
        "base",
        "stores",
    ],
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
        placeholder="Geminiの生成結果をそのまま貼り付けてください",
    )

    if st.button("🪄 貼り付けテキストから各項目へ反映", use_container_width=True):
        if ai_raw_text:
            text = ai_raw_text.strip()

            # --- 解析パターンA: ①〜⑤ 形式の抽出 ---
            p1_title = re.search(r"①\s*(.*)", text)
            p1_price = re.search(r"③\s*([0-9,]+)\s*円?", text)
            p1_cat = re.search(r"④\s*(.*)", text)
            p1_cond = re.search(r"⑤\s*(.*)", text)

            # ②商品説明の抽出（②と③の間を抜く）
            p1_desc = re.search(r"②\s*([\s\S]*?)(?=③|$)", text)

            if p1_title and p1_desc:
                st.session_state["title"] = p1_title.group(1).strip()
                st.session_state["description"] = p1_desc.group(1).strip()

                if p1_price:
                    clean_price = re.sub(r"[^\d]", "", p1_price.group(1))
                    if clean_price:
                        st.session_state["price"] = int(clean_price)
                if p1_cat:
                    st.session_state["category"] = p1_cat.group(1).strip()
                if p1_cond:
                    st.session_state["condition"] = p1_cond.group(1).strip()

                # 管理番号の検出（説明文内から）
                mgmt_match = re.search(
                    r"(?:管理番号|SKU)[:：]?\s*([A-Za-z0-9\-_]+)", text
                )
                if mgmt_match:
                    st.session_state["management_number"] = mgmt_match.group(
                        1
                    ).strip()

            # --- 解析パターンB: 【項目名】 タグ形式の抽出 ---
            else:
                tag_mgmt = re.search(r"【管理番号】\s*(.*)", text)
                tag_title = re.search(r"【商品タイトル】\s*(.*)", text)
                tag_desc = re.search(r"【商品説明】\s*([\s\S]*?)(?=【|$)", text)
                tag_price = re.search(r"【価格】\s*([0-9,]+)", text)
                tag_cat = re.search(r"【カテゴリ】\s*(.*)", text)
                tag_cond = re.search(r"【商品の状態】\s*(.*)", text)

                if tag_mgmt:
                    st.session_state["management_number"] = tag_mgmt.group(
                        1
                    ).strip()
                if tag_title:
                    st.session_state["title"] = tag_title.group(1).strip()
                if tag_desc:
                    st.session_state["description"] = tag_desc.group(1).strip()
                if tag_price:
                    clean_price = re.sub(r"[^\d]", "", tag_price.group(1))
                    if clean_price:
                        st.session_state["price"] = int(clean_price)
                if tag_cat:
                    st.session_state["category"] = tag_cat.group(1).strip()
                if tag_cond:
                    st.session_state["condition"] = tag_cond.group(1).strip()

            st.success("各入力欄へ正確に値を分解・反映しました！")
            st.rerun()

st.markdown("---")

# ----------------------------------------------------
# ✏️ 3. 詳細入力テキストボックスエリア
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
    curr_cond = st.session_state["condition"]
    curr_idx = (
        conditions.index(curr_cond) if curr_cond in conditions else 3
    )  # デフォルト「やや傷や汚れあり」
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
    "商品説明文", value=st.session_state["description"], height=200
)

st.markdown("---")

# ----------------------------------------------------
# 📋 4. 整形結果・データ確認（各サイト用JSON出力）
# ----------------------------------------------------
st.subheader("4. ✂️ 整形結果・データ確認")
st.info(
    "💡 選択中の各サイトに最適化されたJSONです。右上のコピーアイコンを押してChrome拡張機能へ貼り付けてください。"
)

selected_site_keys = st.session_state["selected_sites"]

if not selected_site_keys:
    st.warning(
        "⚠️ トップの「出品対象サイトを選択」で1つ以上のサイトにチェックを入れてください。"
    )
else:
    target_site_defs = [s for s in site_definitions if s[0] in selected_site_keys]

    tab_labels = [s[1] for s in target_site_defs] + ["共通・全サイト汎用JSON"]
    site_tabs = st.tabs(tab_labels)

    for idx, (s_key, s_label, max_len) in enumerate(target_site_defs):
        with site_tabs[idx]:
            raw_title = st.session_state["title"]
            opt_title = (
                raw_title[:max_len] if len(raw_title) > max_len else raw_title
            )

            raw_desc = st.session_state["description"]
            mgmt_num = st.session_state["management_number"]

            # 説明文末尾に管理番号を補強（入っていない場合）
            if mgmt_num and f"【管理番号】" not in raw_desc:
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

            st.caption(
                f"📌 **{s_label}用パラメータ** （タイトル制限: {max_len}文字 / 現在: {len(opt_title)}文字）"
            )
            st.code(
                json.dumps(site_json_payload, ensure_ascii=False, indent=2),
                language="json",
            )

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
        st.code(
            json.dumps(all_export_payload, ensure_ascii=False, indent=2),
            language="json",
        )
