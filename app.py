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

# 3. 入力フォーム（機能追加エリア）

# 【複数選択に変更】プラットフォーム
platforms = st.multiselect(
    "出品先プラットフォーム（複数選択可）",
    ["メルカリShops", "ヤフーフリマ", "ラクマ"],
    default=["メルカリShops", "ヤフーフリマ", "ラクマ"]
)

# 【追加】管理番号 ＆ 実寸値
col1, col2 = st.columns(2)
with col1:
    management_id = st.text_input("管理番号（任意）", placeholder="例: A-102, ITEM-2024")
with col2:
    measurements = st.text_input("実寸値 / 採寸情報（任意）", placeholder="例: 着丈65cm, 身幅50cm, 肩幅45cm")

# 補足情報
product_name = st.text_input("その他・補足情報（任意）", placeholder="例: 新品未使用、箱付き、値下げ不可")

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
        
        # プラットフォーム名をカンマ区切りに変換
        platform_str = ", ".join(platforms)
        
        prompt = f"""
        あなたはプロのフリマ出品者です。
        添付されたすべての画像（計{len(images)}枚）を総合的に確認し、【{platform_str}】のいずれでも使用できる最適な出品文を作成してください。

        【管理番号】: {management_id if management_id else "なし"}
        【実寸値・サイズ詳細】: {measurements if measurements else "画像・デザインから自動推測"}
        【その他補足情報】: {product_name if product_name else "なし"}

        以下のフォーマットで出力してください：
        ---
        【タイトル】（40文字以内、検索キーワードやブランド名を効率よく含める）
        
        【管理番号】（指定があれば明記）
        
        【商品の状態】（画像から推測される状態）
        
        【サイズ・実寸】（入力された実寸値を反映、または画像から推測）
        
        【商品説明文】
        （商品の特徴、デザイン、カラー、素材感、活用シーンなどを魅力的に解説。実寸値や管理番号も文章内に分かりやすく記載してください）
        
        【推奨価格】（相場を踏まえた価格案）
        ---
        """
        
        with st.spinner("画像をAI解析中..."):
            response = model.generate_content([prompt, *images])
            st.success("生成が完了しました！")
            st.markdown(response.text)