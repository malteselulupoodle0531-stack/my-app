import json
import re
import streamlit as st

st.set_page_config(
    page_title="フリマ出品データ一括整形ツール", layout="wide"
)

st.title("📦 フリマ出品データ整形＆出力ツール（完全修正版）")
st.caption(
    "Web版Gemini等の生成結果を貼り付けるだけで、余計な文字を削除し正確にデータを抽出します。"
)

# サイドバー設定
st.sidebar.header("⚙️ 設定")
platforms = st.sidebar.multiselect(
    "対象プラットフォーム",
    ["メルカリShops", "ヤフーフリマ/ヤフオク", "ラクマ", "BASE"],
    default=["メルカリShops", "ヤフーフリマ/ヤフオク", "ラクマ", "BASE"],
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
    "GeminiやChatGPTで生成された回答（①〜⑤全体）をそのままペーストしてください",
    height=250,
    placeholder="""①【商品タイトル】
MAIN Stream ストライプ 半袖シャツ Sサイズ 赤 白 青

②【商品説明】
数あるショップの中から、当ショップをご覧いただき誠にありがとうございます。...

③【推奨販売価格】
3,500円

④【カテゴリ】
メンズ > トップス > シャツ

⑤【商品の状態】
目立った傷や汚れなし""",
)


# 不要な文字（(60字以内) や 文頭の「文」など）を除去する強力なクレンジング関数
def clean_noise_text(text):
  if not text:
    return ""
  # 文頭に残った「文」や「文：」「：」を消去
  text = re.sub(r"^\s*文[：:\s]*", "", text)
  text = re.sub(r"^\s*[：:\s]+", "", text)

  # (◯字以内) や （テンプレート適用・850字以内） などを除去
  text = re.sub(
      r"[\(（][^()（）]*?(?:文字|字|テンプレ|適用|以内|約)[^()（）]*?[\)）]",
      "",
      text,
  )
  # 孤立したカッコ類を綺麗にする
  text = re.sub(r"^\s*[\(（]|[\)）]\s*$", "", text)
  return text.strip()


# パース（解析）ロジック（柔軟な表記揺れ対応）
def parse_ai_text(text):
  data = {
      "title": "",
      "description": "",
      "price": "",
      "category": "",
      "condition": "",
  }

  if not text:
    return data

  # ①〜⑤の見出しに対応する正規表現パターン
  # タイトル
  title_match = re.search(
      r"(?:①|1|\*)\s*【?(?:商品)?タイトル(?:文)?】?[：:\s]*(.*?)(?=\n(?:②|2|\*|【)|$)",
      text,
      re.S,
  )
  # 説明文
  desc_match = re.search(
      r"(?:②|2|\*)\s*【?(?:商品)?説明(?:文)?】?[：:\s]*(.*?)(?=\n(?:③|3|\*|【)|$)",
      text,
      re.S,
  )
  # 価格（推奨価格、販売価格、平均価格等）
  price_match = re.search(
      r"(?:③|3|\*)\s*【?(?:推奨|販売|平均|予想)?(?:販売)?価格】?[：:\s]*(.*?)(?=\n(?:④|4|\*|【)|$)",
      text,
      re.S,
  )
  # カテゴリ
  cat_match = re.search(
      r"(?:④|4|\*)\s*【?(?:販売する際の)?カテゴリ(?:ー)?】?[：:\s]*(.*?)(?=\n(?:⑤|5|\*|【)|$)",
      text,
      re.S,
  )
  # 状態
  cond_match = re.search(
      r"(?:⑤|5|\*)\s*【?(?:商品)?の?状態】?[：:\s]*(.*?)(?=\n|\Z)",
      text,
      re.S,
  )

  if title_match:
    data["title"] = clean_noise_text(title_match.group(1))
  if desc_match:
    data["description"] = clean_noise_text(desc_match.group(1))
  if price_match:
    # 3,500円 や 3500円 から数字だけを安全に抽出
    price_digits = re.sub(r"\D", "", price_match.group(1))
    data["price"] = price_digits
  if cat_match:
    data["category"] = clean_noise_text(cat_match.group(1))
  if cond_match:
    data["condition"] = clean_noise_text(cond_match.group(1))

  # 万が一抽出できなかった場合のバックアップ処理
  if not data["description"] and "数あるショップの中から" in text:
    data["description"] = clean_noise_text(text)

  return data


parsed_data = parse_ai_text(raw_text)

st.markdown("---")
st.subheader("3. ✂️ 整形結果・データ確認")

if raw_text:
  col_title, col_price = st.columns([3, 1])
  with col_title:
    title_val = st.text_input("商品タイトル", value=parsed_data["title"])
  with col_price:
    price_val = st.text_input("販売価格 (円)", value=parsed_data["price"])

  col_cat, col_cond = st.columns(2)
  with col_cat:
    cat_val = st.text_input("カテゴリ", value=parsed_data["category"])
  with col_cond:
    cond_val = st.text_input("商品の状態", value=parsed_data["condition"])

  desc_val = st.text_area("商品説明文", value=parsed_data["description"], height=250)

  # 最新文字数制限チェック
  st.markdown("##### 📏 文字数チェック（タイトル目標: 60文字以内）")
  m_col1, m_col2, m_col3, m_col4 = st.columns(4)

  title_len = len(title_val)
  desc_len = len(desc_val)

  with m_col1:
    st.caption("メルカリShops (上限130字)")
    if title_len > 130:
      st.error(f"タイトル: ❌ {title_len}字")
    else:
      st.success(f"タイトル: ⭕ {title_len}/130字")

  with m_col2:
    st.caption("ヤフーフリマ/ヤフオク (上限65字)")
    if title_len > 65:
      st.error(f"タイトル: ❌ {title_len}字")
    else:
      st.success(f"タイトル: ⭕ {title_len}/65字")

  with m_col3:
    st.caption("ラクマ (上限65字)")
    if title_len > 65:
      st.error(f"タイトル: ❌ {title_len}字")
    else:
      st.success(f"タイトル: ⭕ {title_len}/65字")

  with m_col4:
    st.caption("商品説明文 (目標850字)")
    if desc_len > 1000:
      st.warning(f"本文: ⚠️ {desc_len}字 (1000字超過注意)")
    else:
      st.success(f"本文: ⭕ {desc_len}字")

  # Chrome拡張機能へ受け渡す用のJSONデータ出力エリア
  st.markdown("---")
  st.markdown("### 🚀 Phase 3 (Chrome拡張機能) 連携用データ")

  export_payload = {
      "title": title_val,
      "price": price_val,
      "description": desc_val,
      "category": cat_val,
      "condition": cond_val,
  }

  json_str = json.dumps(export_payload, ensure_ascii=False)
  st.text_area(
      "このJSONテキストを拡張機能へ渡して自動入力します",
      value=json_str,
      height=80,
  )

else:
  st.info(
      "上のテキストエリアにWeb版AIの回答を貼り付けると、一瞬で解析して各項目にセットされます。"
  )