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
    "shipping_payer": "送料込み(出品者負担)",
    "shipping_method": "未定",
    "shipping_region": "未定",
    "shipping_days": "1~2日で発送",
}

for key, val in default_fields.items():
    if key not in st.session_state:
        st.session_state[key] = val

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
        placeholder="""[ITEM_MGMT]
B642

[ITEM_TITLE]
セントジョンズベイ リネンコットン...

[ITEM_DESC_START]
数あるショップの中から...
[ITEM_DESC_END]

[ITEM_PRICE]
6800

[ITEM_CAT]
メンズ > トップス > シャツ

[ITEM_COND]
目立った傷や汚れなし

[ITEM_SIZE]
X-LARGE

[ITEM_BRAND]
ST.JOHN'S BAY""",
    )

    if st.button("🪄 貼り付けテキストから各項目へ反映", use_container_width=True):
        if ai_raw_text:
            text = ai_raw_text.strip()

            # --- 1. [ITEM_...] 形式での抽出 ---
            mgmt_m = re.search(r"\[ITEM_MGMT\]\s*\n?([^\n\[]+)", text)
            title_m = re.search(r"\[ITEM_TITLE\]\s*\n?([^\n\[]+)", text)
            price_m = re.search(r"\[ITEM_PRICE\]\s*\n?(\d+)", text)
            cat_m = re.search(r"\[ITEM_CAT\]\s*\n?([^\n\[]+)", text)
            cond_m = re.search(r"\[ITEM_COND\]\s*\n?([^\n\[]+)", text)
            size_m = re.search(r"\[ITEM_SIZE\]\s*\n?([^\n\[]+)", text)
            brand_m = re.search(r"\[ITEM_BRAND\]\s*\n?([^\n\[]+)", text)

            # 商品説明文（[ITEM_DESC_START]〜[ITEM_DESC_END]）
            desc_m = re.search(r"\[ITEM_DESC_START\]\s*\n?(.*?)\s*\[ITEM_DESC_END\]", text, re.DOTALL)

            # --- 2. 従来の【 】形式でのフォールバック ---
            if not mgmt_m:
                mgmt_m = re.search(r"【管理番号】\s*\n?([^\n【]+)", text)
            if not title_m:
                title_m = re.search(r"【商品タイトル】\s*\n?([^\n【]+)", text)
            if not price_m:
                price_m = re.search(r"【価格】\s*\n?(\d+)", text)
            if not cat_m:
                cat_m = re.search(r"【カテゴリ】\s*\n?([^\n【]+)", text)
            if not cond_m:
                cond_m = re.search(r"【(?:商品の状態|状態)】\s*\n?([^\n【]+)", text)

            if not desc_m:
                desc_m = re.search(
                    r"【商品説明】\s*\n?(.*?)(?=\n【(?:価格|カテゴリ|商品の状態|状態|管理番号|商品タイトル)】|\Z)",
                    text,
                    re.DOTALL,
                )

            # --- セッションステートへ反映 ---
            if mgmt_m:
                st.session_state["management_number"] = mgmt_m.group(1).strip()
            if title_m:
                st.session_state["title"] = title_m.group(1).strip()
            if price_m:
                try:
                    st.session_state["price"] = int(price_m.group(1).strip())
                except ValueError:
                    pass
            if cat_m:
                st.session_state["category"] = cat_m.group(1).strip()
            if cond_m:
                st.session_state["condition"] = cond_m.group(1).strip()

            if desc_m and desc_m.group(1).strip():
                st.session_state["description"] = desc_m.group(1).strip()
            else:
                st.session_state["description"] = text

            if size_m:
                st.session_state["size"] = size_m.group(1).strip()
            else:
                s_in_desc = re.search(r"・?\s*表記サイズ[:：]?\s*([^\n]+)", st.session_state["description"])
                st.session_state["size"] = s_in_desc.group(1).strip() if s_in_desc else ""

            if brand_m:
                st.session_state["brand"] = brand_m.group(1).strip()
            else:
                b_in_desc = re.search(r"・?\s*ブランド[:：]?\s*([^\n]+)", st.session_state["description"])
                st.session_state["brand"] = b_in_desc.group(1).strip() if b_in_desc else ""

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
    "商品説明文", value=st.session_state["description"], height=250
)

st.markdown("---")

# ----------------------------------------------------
# 📋 4. 整形結果・データ確認（全サイト共通・汎用JSON出力）
# ----------------------------------------------------
st.subheader("4. ✂️ 整形結果・データ確認")
st.info("💡 共通フォーマットのJSONデータです。右上のコピーアイコンを押してChrome拡張機能へ貼り付けてください。拡張機能側のプルダウンで対象サイト（メルカリ、ラクマ、Yahoo!フリマ、メルカリShops、ヤフオク!、BASE、STORES）を選択すると、それぞれの仕様に合わせて自動適用されます。")

# 拡張機能がそのまま解釈できる汎用標準構造のデータセット
universal_export_payload = {
    "management_number": st.session_state["management_number"],
    "title": st.session_state["title"],
    "description": st.session_state["description"],
    "price": st.session_state["price"],
    "condition": st.session_state["condition"],
    "category": st.session_state["category"],
    "brand": st.session_state["brand"],
    "size": st.session_state["size"],
    "shipping_payer": st.session_state["shipping_payer"],
    "shipping_method": st.session_state["shipping_method"],
    "shipping_region": st.session_state["shipping_region"],
    "shipping_days": st.session_state["shipping_days"],
}

st.code(json.dumps(universal_export_payload, ensure_ascii=False, indent=2), language="json")
