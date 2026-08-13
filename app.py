import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os

# --- ページ設定 ---
st.set_page_config(page_title="フリマAI商品情報生成アプリ", layout="centered")

st.title("👕 フリマAI商品情報生成アプリ")
st.write("画像・管理番号・実寸値を入力すると、規定テンプレートに沿った出品テキストを自動生成します。")

# --- APIキーの設定 ---
# 環境変数または画面からの入力
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Keyを入力", type="password")

if api_key:
    genai.configure(api_key=api_key)

# --- フォーム入力画面 ---
st.header("1. 商品情報の入力")

uploaded_file = st.file_uploader("商品画像をアップロード", type=["jpg", "jpeg", "png"])
management_no = st.text_input("管理番号", value="A-001")

# 実寸値入力エリア
st.subheader("実寸値（平置き）")
col1, col2 = st.columns(2)

with col1:
    size_label = st.text_input("表記サイズ", value="L")
    v_length = st.text_input("着丈 / 股上", value="68cm")
    v_width = st.text_input("身幅 / ウエスト", value="54cm")

with col2:
    v_shoulder = st.text_input("肩幅 / 股下", value="48cm")
    v_sleeve = st.text_input("袖丈 / ワタリ幅", value="21cm")

# --- AI生成ロジック ---
def generate_product_info(image, mgmt_no, measurements_dict):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    measurements_json = json.dumps(measurements_dict, ensure_ascii=False)

    prompt = f"""
あなたは古着専門のプロ出品者・コピーライターです。
アップロードされた画像、管理番号、および入力された実寸値データをもとに、フリマ出品用の商品情報を生成してください。

【入力データ】
・管理番号: {mgmt_no}
・実寸値データ: {measurements_json}

【絶対厳守ルール】
1. 環境依存文字（絵文字、特殊丸数字など）は一切使用しないでください。
2. サイズ表記に「インチ（inch, in）」は絶対に使用しないでください。すべて「cm」表記に統一してください。
3. 商品タイトルは【ブランド名 カテゴリ 色 サイズ 特徴+α】の構成で、半角・全角問わず必ず40文字以内に収めてください。
4. 商品説明文は指定されたテンプレートの文章・構造・改行・文言を一切変更・崩さず、{{}}内のみを埋めて作成してください。テンプレート全体（固定文＋入力文）で必ず850文字以内に収めてください。
5. コンディションは「やや傷や汚れあり」を基本基準とし、画像から読み取れる傷・シミ・破れ・生地のたるみ・ウエストゴムやドローコードの状態を細かく詳細に記載してください。

---
【出力するJSON形式】
以下のJSON構造のみを出力してください。余計な解説文やMarkdown記法(```json など)は一切含めないでください。

{{
  "management_no": "{mgmt_no}",
  "title": "40文字以内の商品タイトル",
  "description": "数あるショップの中から、当ショップをご覧いただき誠にありがとうございます。\\n{{簡潔なセールスポイント}}\\n\\n◆Brand & Item\\n・ブランド：{{ブランド名}} {{製造場所}}\\n・アイテム：{{カテゴリ・アイテム名}}\\n・カラー  ：{{色 ※深みのあるネイビーなど表現にこだわりを入れる}}\\n・素材    ：{{素材}}\\n\\n◆Size\\n・表記サイズ：{{表記サイズ}}\\n・実寸サイズ（平置き）\\n{{実寸値を入力}}\\n※丁寧な採寸を心がけておりますが、多少の誤差はご容赦ください。お手持ちのお洋服と照らし合わせてのご検討をお勧めいたします。\\n\\n◆Condition\\n・コンディション：{{「目立った傷や汚れなし」「やや傷や汚れあり」「傷や汚れあり」から選択}}\\n・詳細：{{状態の詳細。特筆すべきダメージの有無、ゴム/ドローコード、シミ、擦れ等を詳細に}}\\n\\n◆Attention / ご購入時の注意点\\n心地よくお召しいただくため、以下をご一読ください。\\n～商品の状態について～\\n検品には万全を期しておりますが、すべてスタッフが手作業にて行っており、稀にほつれや小さな見落としがある場合がございます。あらかじめご了承ください。\\n～カラー・質感について～\\n光の加減や撮影環境、お客様がお使いのモニター環境により、実物とわずかに色味が異なる場合がございます。\\n～配送について～\\nご注文いただきましてから、丁寧に梱包して1～2日以内に発送いたします。配送時の畳みジワはご容赦ください。\\n\\n◆Follow Us\\n当ショップを【フォロー】していただくと、新しいアイテムをいち早くチェックしていただけます。\\nまた、フォロワー様限定の特別なご案内や、シークレットなイベントも予定しております。\\nぜひ、画面上の「フォローする」ボタンよりご登録くださいませ。\\n管理番号: {mgmt_no}",
  "price": 5800,
  "condition_status": "やや傷や汚れあり"
}}
"""
    response = model.generate_content([prompt, image])
    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]
    return json.loads(raw_text)

# --- 生成実行ボタン ---
if st.button("🚀 商品情報を自動生成する", type="primary"):
    if not api_key:
        st.error("APIキーを入力してください。")
    elif not uploaded_file:
        st.error("商品画像をアップロードしてください。")
    else:
        with st.spinner("AIが画像を解析中..."):
            image = Image.open(uploaded_file)
            measurements = {
                "表記サイズ": size_label,
                "項目1": v_length,
                "項目2": v_width,
                "項目3": v_shoulder,
                "項目4": v_sleeve
            }
            
            result = generate_product_info(image, management_no, measurements)
            
            # 画面への表示処理
            st.success("生成が完了しました！")
            st.header("2. 生成結果")
            
            st.subheader("商品タイトル")
            st.text_input("タイトル（ワンクリックでコピー可能）", value=result["title"])
            st.caption(f"文字数: {len(result['title'])} / 40字")
            
            st.subheader("商品説明文（テンプレート適用済み）")
            st.text_area("説明文（ワンクリックでコピー可能）", value=result["description"], height=300)
            st.caption(f"文字数: {len(result['description'])} / 850字")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.number_input("推奨販売価格", value=result["price"])
            with col_res2:
                st.text_input("商品の状態", value=result["condition_status"])
                
            # Chrome拡張機能が読み込めるようにJSON形式で保存
            with open("product_data.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            st.toast("拡張機能用のデータを更新しました！")