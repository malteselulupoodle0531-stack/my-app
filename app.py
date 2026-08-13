import json
import re
import streamlit as st

st.set_page_config(
    page_title="フリマ出品データ一括整形ツール", layout="wide"
)

st.title("📦 フリマ出品データ整形＆出力ツール（API非依存・爆速版）")
st.caption(
    "Web版Gemini等の生成結果を貼り付けるだけで、各モール用に文字数調整＆JSON出力します。"
)

# サイドバー設定
st.sidebar.header("⚙️ 設定")
platforms = st.sidebar.multiselect(
    "対象プラットフォーム",
    ["メルカリShops", "ヤフーフリマ/ヤフオク", "ラクマ", "BASE"],
    default=["メルカリShops", "ヤフーフリマ/ヤフオク", "ラクマ", "BASE"],
)

# 注意書き（併売用）を自動挿入するか
add_notice = st.sidebar.checkbox(
    "商品説明文に併売・即決時の免責事項を自動挿入", value=True
)
notice_text = (
    "\n\n※他サイトでも併売しているため、予告なく出品を取り消す場合や、タイミングにより売り切れとなる場合がございます。あらかじめご了承ください。"
)

# 1. 画像表示エリア（API通信ゼロ・表示ドラッグ用）
st.subheader("1. 📷 出品用画像（確認・ドラッグ用）")
uploaded_images = st.file_uploader(
    "商品をセット（※API送信は行わないため動作は一瞬です）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_images:
  st.caption(
      "💡 出品画面を開いたら、ここから画像を直接ドラッグ＆ドロップで追加できます。"
  )
  cols = st.columns(min(len(uploaded_images), 5))
  for idx, img_file in enumerate(uploaded_images):
    with cols[idx % 5]:
      st.image(img_file, caption=f"画像{idx+1}", use_container_width=True)

st.markdown("---")

# 2. テキスト入力エリア
st.subheader("2. 📝 Web版AIの生成結果を貼り付け")
raw_text = st.text_area(
    "GeminiやChatGPTで生成したテキストをそのままペーストしてください",
    height=180,
    placeholder="""例：
【タイトル】
MAIN Stream ストライプ 半袖シャツ Sサイズ 赤 白 青

【管理番号】
A-102

【商品の状態】
目立った傷や汚れなし

【サイズ・実寸（平置き採寸）】
肩幅: 45cm, 身幅: 50cm, 着丈: 70cm, 袖丈: 22cm

【商品説明文】
ご覧いただきありがとうございます。MAIN Streamの爽やかなストライプ半袖シャツです。

【推奨価格】
3500円
""",
)


# テキストパース（分解）ロジック
def parse_ai_text(text):
  data = {
      "title": "",
      "management_id": "",
      "condition": "",
      "size": "",
      "description": "",
      "price": "",
  }

  if not text:
    return data

  # 簡易パース（各項目キーを探して抽出）
  title_match = re.search(r"【タイトル】\s*(.*?)(?=\n【|\Z)", text, re.S)
  id_match = re.search(r"【管理番号】\s*(.*?)(?=\n【|\Z)", text, re.S)
  condition_match = re.search(r"【商品の状態】\s*(.*?)(?=\n【|\Z)", text, re.S)
  size_match = re.search(r"【サイズ・実寸.*?】\s*(.*?)(?=\n【|\Z)", text, re.S)
  desc_match = re.search(r"【商品説明文】\s*(.*?)(?=\n【|\Z)", text, re.S)
  price_match = re.search(r"【推奨価格】\s*(.*?)(?=\n【|\Z)", text, re.S)

  if title_match:
    data["title"] = title_match.group(1).strip()
  if id_match:
    data["management_id"] = id_match.group(1).strip()
  if condition_match:
    data["condition"] = condition_match.group(1).strip()
  if size_match:
    data["size"] = size_match.group(1).strip()
  if desc_match:
    data["description"] = desc_match.group(1).strip()
  if price_match:
    price_digits = re.sub(r"\D", "", price_match.group(1))
    data["price"] = price_digits

  return data


parsed_data = parse_ai_text(raw_text)

st.markdown("---")
st.subheader("3. ✂️ モール別整形結果・データ出力")

if raw_text:
  # 全体用の商品説明文の組み立て
  full_description = (
      f"{parsed_data['description']}\n\n【サイズ・実寸】\n{parsed_data['size']}"
  )
  if parsed_data["management_id"]:
    full_description += f"\n\n【管理番号】\n{parsed_data['management_id']}"
  if parsed_data["condition"]:
    full_description += f"\n\n【状態】\n{parsed_data['condition']}"
  if add_notice:
    full_description += notice_text

  col_title, col_price = st.columns([3, 1])
  with col_title:
    title_val = st.text_input("共通タイトル", value=parsed_data["title"])
  with col_price:
    price_val = st.text_input("販売価格 (円)", value=parsed_data["price"])

  desc_val = st.text_area("共通商品説明文", value=full_description, height=180)

  # モール別文字数チェック
  st.markdown("##### 📏 モール別タイトル文字数制限チェック")
  m_col1, m_col2, m_col3, m_col4 = st.columns(4)

  title_len = len(title_val)

  with m_col1:
    st.caption("メルカリShops (上限40文字)")
    if title_len > 40:
      st.error(f"❌ {title_len}文字 (要短縮)")
    else:
      st.success(f"⭕ {title_len}/40文字")

  with m_col2:
    st.caption("ヤフーフリマ/ヤフオク (上限65文字)")
    if title_len > 65:
      st.error(f"❌ {title_len}文字")
    else:
      st.success(f"⭕ {title_len}/65文字")

  with m_col3:
    st.caption("ラクマ (上限40文字)")
    if title_len > 40:
      st.error(f"❌ {title_len}文字")
    else:
      st.success(f"⭕ {title_len}/40文字")

  with m_col4:
    st.caption("BASE (上限100文字)")
    st.success(f"⭕ {title_len}/100文字")

  # Chrome拡張機能へ受け渡す用のJSONデータ出力エリア
  st.markdown("---")
  st.markdown("### 🚀 Phase 3 (Chrome拡張機能) 連携用データ")

  export_payload = {
      "title": title_val,
      "price": price_val,
      "description": desc_val,
      "management_id": parsed_data["management_id"],
  }

  json_str = json.dumps(export_payload, ensure_ascii=False)
  st.text_area(
      "このJSONテキストを拡張機能へ渡して自動入力します",
      value=json_str,
      height=70,
  )

else:
  st.info(
      "上のテキストエリアにWeb版AIの回答を貼り付けると、一瞬で各モール用に整形されます。"
  )