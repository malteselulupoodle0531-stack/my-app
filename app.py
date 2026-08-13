import io
import time
import google.generativeai as genai
from PIL import Image
import streamlit as st

st.title("フリマ出品文＆画像自動生成アプリ")

# 1. APIキーの設定
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# 使用可能なモデル候補（429上限に達した際に別のモデルへ切り替えられるように設定）
MODEL_OPTIONS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.6-flash",
]

selected_model = st.sidebar.selectbox(
    "使用するGeminiモデル",
    MODEL_OPTIONS,
    index=0,  # デフォルトは安定していて上限の緩い gemini-2.0-flash
    help="1日の利用上限（429エラー）が出た場合は、別のモデルに切り替えて試してください。",
)

# 2. 画像の一括アップロード
uploaded_files = st.file_uploader(
    "商品画像をまとめて選択・ドラッグ＆ドロップ（複数OK）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

raw_images = []
if uploaded_files:
  st.write(f"📷 アップロードされた画像: {len(uploaded_files)}枚")
  cols = st.columns(min(len(uploaded_files), 5))
  for i, file in enumerate(uploaded_files):
    img = Image.open(file)
    raw_images.append(img)
    with cols[i % 5]:
      st.image(img, caption=f"画像 {i+1}", use_container_width=True)


# 🚀 画像を高速処理用に軽量化（圧縮）する関数
def compress_image(image, max_size=800):
  """画像の長辺をmax_size(標準800px)にリサイズし、JPEGで圧縮する"""
  image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

  if image.mode in ("RGBA", "LA", "P"):
    background = Image.new("RGB", image.size, (255, 255, 255))
    background.paste(image, mask=image.split()[-1])
    image = background
  elif image.mode != "RGB":
    image = image.convert("RGB")

  img_io = io.BytesIO()
  image.save(img_io, format="JPEG", quality=85)
  img_io.seek(0)
  return Image.open(img_io)


st.markdown("---")

# 3. 入力フォームエリア
col_id, col_info = st.columns(2)
with col_id:
  management_id = st.text_input("管理番号", placeholder="例: A-102")
with col_info:
  measurements_input = st.text_area(
      "実寸値入力（コピペ可）",
      placeholder="例:\n肩幅: 45cm\n身幅: 50cm\n着丈: 70cm",
      height=100,
  )

st.markdown("---")

# 4. AI処理ボタン
if st.button("AIで出品文を爆速生成"):
  if not api_key:
    st.error("サイドバーにGemini APIキーを入力してください。")
  elif not raw_images:
    st.error("画像を1枚以上アップロードしてください。")
  else:
    with st.spinner(
        f"画像を自動軽量化して【{selected_model}】で爆速解析中..."
    ):
      genai.configure(api_key=api_key)

      # 画像の軽量化処理
      compressed_images = [compress_image(img.copy()) for img in raw_images]

      prompt = f"""
            あなたはプロのフリマ出品者です。
            添付されたすべての画像（計{len(compressed_images)}枚）を総合的に確認し、メルカリShops、ヤフーフリマ、ラクマのいずれでも使用できる最適な出品文を作成してください。

            【管理番号】: {management_id if management_id else "なし"}
            【実寸値情報】: 
            {measurements_input if measurements_input else "なし（画像から推測して記載してください）"}

            以下のフォーマットで出力してください：
            ---
            【タイトル】（40文字以内、検索キーワードやブランド名を効率よく含める）
            
            【管理番号】（指定があれば明記）
            
            【商品の状態】（画像から推測される状態）
            
            【サイズ・実寸（平置き採寸）】
            （※入力された実寸値はそのまま明記し、記載のない項目で画像から分かる部分があれば補足してください）
            
            【商品説明文】
            （商品の特徴、デザイン、カラー、素材感、活用シーンなどを魅力的に解説。採寸情報や管理番号も箇条書き等で見やすく記載してください）
            
            【推奨価格】（相場を踏まえた価格案）
            ---
            """

      max_retries = 3
      response = None

      for attempt in range(max_retries):
        try:
          model = genai.GenerativeModel(selected_model)
          response = model.generate_content([prompt, *compressed_images])
          break
        except Exception as e:
          error_str = str(e)
          if "429" in error_str:
            if attempt < max_retries - 1:
              # 一時的なレート制限なら待機して再試行
              time.sleep(8)
            else:
              st.error(
                  f"【利用制限エラー (429)】\n選択中のモデル ({selected_model}) の利用回数制限に達しました。"
                  "\nサイドバーから別のモデル（例: gemini-2.0-flash）に変更して再度お試しください。"
              )
              break
          else:
            st.error(f"エラーが発生しました: {e}")
            break

      if response:
        st.success("生成が完了しました！")
        st.markdown(response.text)