# boatrace-insta-images

Instagram投稿用の画像置き場です。

- `prompts/<名前>.txt` を置くと、GitHub Actions が OpenAI の画像生成で `images/covers/<名前>.png` を作ります。
- 動かすには、Settings → Secrets and variables → Actions に `OPENAI_API_KEY` を登録してください。
