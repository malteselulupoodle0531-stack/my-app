import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("フリマ出品文＆画像自動生成アプリ")

# 1. APIキーの設定
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# 2. 画像の一括アップロード
uploaded_files = st.file_uploader(
    "商品画像をまとめて選択・ドラッグ＆ドロップ（複数OK）", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

images = []
if uploaded_files:
    st.write(f"📷 アップロードされた画像: {len(uploaded_files)}枚")
    cols = st.columns(min(len(uploaded_files), 5))
    for i, file in enumerate(uploaded_files):
        img = Image.open(file)
        images.append(img)
        with cols[i % 5]:
            st.image(img, caption=f"画像 {i+1}", use_container_width=True)

st.markdown("---")

# 3. 入力フォームエリア

# プラットフォームの複数選択
platforms = st.multiselect(
    "出品先プラットフォーム（複数選択可）",
    ["メルカリShops", "ヤフーフリマ", "ラクマ"],
    default=["メルカリShops", "ヤフーフリマ", "ラクマ"]
)

# 管理番号・基本補足情報
col_id, col_info = st.columns(2)
with col_id:
    management_id = st.text_input("管理番号（任意）", placeholder="例: A-102")
with col_info:
    product_name = st.text_input("その他・補足情報（任意）", placeholder="例: 新品未使用、箱付き")

# 実寸値（採寸情報）を独立項目としてレイアウト
st.subheader("📏 実寸値（採寸情報）")

st.markdown("**【トップス類】**")
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
with col_t1:
    length = st.text_input("着丈 (cm)", placeholder="65")
with col_t2:
    width = st.text_input("身幅 (cm)", placeholder="50")
with col_t3:
    shoulder = st.text_input("肩幅 (cm)", placeholder="45")
with col_t4:
    sleeve = st.text_input("袖丈 (cm)", placeholder="60")

st.markdown("**【ボトムス類】**")
col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
with col_b1:
    waist = st.text_input("ウエスト (cm)", placeholder="76")
with col_b2:
    rise = st.text_input("股上 (cm)", placeholder="28")
with col_b3:
    inseam = st.text_input("股下 (cm)", placeholder="72")
with col_b4:
    thigh = st.text_input("太もも回り (cm)", placeholder="54")
with col_b5:
    hem = st.text_input("裾幅 (cm)", placeholder="20")

# 入力された採寸項目だけをまとめる処理
measurements_dict = {
    "着丈": f"{length}cm" if length else None,
    "身幅": f"{width}cm" if width else None,
    "肩幅": f"{shoulder}cm" if shoulder else None,
    "袖丈": f"{sleeve}cm" if sleeve else None,
    "ウエスト": f"{waist}cm" if waist else None,
    "股上": f"{rise}cm" if rise else None,
    "股下": f"{inseam}cm" if inseam else None,
    "太もも回り": f"{thigh}cm" if thigh else None,
    "裾幅": f"{hem}cm" if hem else None,
}

# 値が入っている項目だけを抽出
active_measurements = [f"{k}: {v}" for k, v in measurements_dict.items() if v]
measurements_text = ", ".join(active_measurements) if active_measurements else "なし（画像から推測）"

st.markdown("---")

# 4. AI処理ボタン
if st.button("AIで一括解析＆出品文を生成"):
    if not api_key:
        st.error("サイドバーにGemini APIキーを入力してください。")
    elif not images:
        st.error("画像を1枚以上アップロードしてください。")
    elif not platforms:
        st.error("プラットフォームを1つ以上選択してください。")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        platform_str = ", ".join(platforms)
        
        prompt = f"""
        あなたはプロのフリマ出品者です。
        添付されたすべての画像（計{len(images)}枚）を総合的に確認し、【{platform_str}】のいずれでも使用できる最適な出品文を作成してください。

        【管理番号】: {management_id if management_id else "なし"}
        【指定された実寸値】: {measurements_text}
        【その他補足情報】: {product_name if product_name else "なし"}

        以下のフォーマットで出力してください：
        ---
        【タイトル】（40文字以内、検索キーワードやブランド名を効率よく含める）
        
        【管理番号】（指定があれば明記）
        
        【商品の状態】（画像から推測される状態）
        
        【サイズ・実寸（平置き採寸）】
        （※指定された実寸値がある項目はそのまま明記し、記載のない項目で画像から分かる部分があれば補足してください）
        
        【商品説明文】
        （商品の特徴、デザイン、カラー、素材感、活用シーンなどを魅力的に解説。採寸情報や管理番号も箇条書き等で見やすく記載してください）
        
        【推奨価格】（相場を踏まえた価格案）
        ---
        """
        
        with st.spinner("画像をAI解析中..."):
            response = model.generate_content([prompt, *images])
            st.success("生成が完了しました！")
            st.markdown(response.text)