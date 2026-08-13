# 4. AI処理ボタン
if st.button("AIで一括解析＆出品文を生成"):
    if not api_key:
        st.error("サイドバーにGemini APIキーを入力してください。")
    elif not raw_images:
        st.error("画像を1枚以上アップロードしてください。")
    elif not platforms:
        st.error("プラットフォームを1つ以上選択してください。")
    else:
        import time
        
        with st.spinner(f"【{selected_model}】で高速解析中..."):
            genai.configure(api_key=api_key)
            compressed_images = [compress_image(img.copy()) for img in raw_images]
            
            platform_str = ", ".join(platforms)
            prompt = f"""
            あなたはプロのフリマ出品者です。
            添付されたすべての画像（計{len(compressed_images)}枚）を総合的に確認し、【{platform_str}】のいずれでも使用できる最適な出品文を作成してください。

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

            # 最大3回まで自動リトライする安全ロジック
            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content([prompt, *compressed_images])
                    break # 成功したら抜け出す
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        # 429制限にかかった場合は8秒待って自動リトライ
                        time.sleep(8)
                    else:
                        st.error(f"エラーが発生しました: {e}")
                        break
            
            if response:
                st.success(f"生成が完了しました！（使用モデル: {selected_model}）")
                st.markdown(response.text)