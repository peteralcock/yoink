# YOINK!
Steal SEO from your competitors and level the content marketing playing field. Generate fresh WordPress blog posts from any public website’s sitemap.xml using OpenAI’s GPT models.

✨ Key Features

Auto‑discover a site’s sitemap via robots.txt (falls back to /sitemap.xml).

Recursive parsing—handles sitemap indexes and grabs every <loc> entry.

Smart filtering (optional --domain-filter) to target only blog URLs.

Title scraping—fetches each page’s <title> tag for context.

AI generation—creates original 800‑1 000‑word posts with GPT‑4o (customisable prompt ↔ temperature).

One‑click import—outputs a WordPress WXR (XML) file ready for Tools → Import → WordPress.

Rate‑limit friendly—polite delays & progress bar via tqdm.

🛠️ Installation

# Clone / download the script
pip install -r requirements.txt  # requests, beautifulsoup4, lxml, openai, tqdm, python-slugify

export OPENAI_API_KEY="sk-…"      # <-- your OpenAI key

Python ≥ 3.9 recommended.

🚀 Usage

python sitemap_to_wxr.py <SITE_URL> [options]

Option

Default

Description

--domain-filter

None

Only process URLs containing this substring (e.g. /blog/).

--max-posts

20

Limit number of posts to generate (helps control token spend).

--output

generated_posts.xml

File name for the WXR export.

--model

hard‑coded in script

Edit in code (e.g. gpt-4o-mini, gpt-3.5-turbo).

Example

python sitemap_to_wxr.py https://secrethotline.com \
  --domain-filter "/blog/" \
  --max-posts 30 \
  --output secret_hotline_posts.xml

Import the resulting XML in WordPress:

WP Admin → Tools → Import → WordPress → Upload File & Import

📝 Prompt Customisation

Inside generate_post() tweak the prompt, temperature, max_tokens, or switch the OpenAI model. You can also add topics, tone guidelines, or SEO instructions.

⚠️ Caveats & Ethics

Respect robots.txt and site T&C before scraping.

Generated content should not replicate copyrighted material; the prompt instructs GPT accordingly.

Large runs can incur significant OpenAI token costs—use --max-posts wisely.

🪪 License

MIT — do what you want, but no warranties.

🙌 Credits

Crafted by the Secret Hotline growth/dev squad • Powered by OpenAI GPT‑4o.

