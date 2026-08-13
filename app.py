import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("フリマ出品文＆画像自動生成アプリ")

# 1. APIキーの設定
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# 2. 画像の一括アップロード（accept_multiple_files=True を追加！）
uploaded_files = st.file_uploader(
    "商品画像をまとめて選択・ドラッグ＆ドロップ（複数OK）", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

images = []
if uploaded_files:
    st.write(f"📷 アップロードされた画像: {len(uploaded_files)}枚")
    
    # 横並びでプレビュー表示する列を作成
    cols = st.columns(min(len(uploaded_files), 5))
    for i, file in enumerate(uploaded_files):
        img = Image.open(file)
        images.append(img)
        with cols[i % 5]:
            st.image(img, caption=f"画像 {i+1}", use_container_width=True)

# 3. 入力フォーム
product_name = st.text_input("補足情報（任意）", placeholder="例: 新品未使用、箱付き")
platform = st.selectbox("プラットフォーム", ["メルカリShops", "ヤフーフリマ", "ラクマ"])

# 4. AI処理ボタン
if st.button("AIで一括解析＆出品文を生成"):
    if not api_key:
        st.error("サイドバーにGemini APIキーを入力してください。")
    elif not images:
        st.error("画像を1枚以上アップロードしてください。")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        あなたはプロのフリマ出品者です。
        添付されたすべての画像（計{len(images)}枚）を総合的に確認し、{platform}向けの最適な出品データを生成してください。

        【補足情報】: {product_name}

        以下のフォーマットで出力してください：
        ---
        【タイトル】（40文字以内、検索キーワードを含める）
        【商品の状態】（画像から推測される状態）
        【商品説明文】（商品の特徴、魅力、サイズ感、注意点などを丁寧に解説）
        【推奨価格】（相場を踏まえた価格案）
        ---
        """
        
        with st.spinner("画像をAI解析中..."):
            # 画像リストとプロンプトを一緒にGeminiへ渡す
            response = model.generate_content([prompt, *images])
            st.success("生成が完了しました！")
            st.markdown(response.text)