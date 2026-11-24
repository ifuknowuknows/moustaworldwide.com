# Website source

Edit the English text and the startup list at https://app.pagescms.org (sign in with GitHub, open this repository).
English decides: saving runs the "Build site" action, which translates changed lines into the other 7 languages (DeepL, needs the DEEPL_API_KEY secret) and rebuilds the 8 pages.

- en.json: the English texts (edit in Pages CMS)
- da/es/pt/sv/fr/id/ar.json: translations (written by translate.py; you can still fix a line by hand, it stays until its English line changes)
- dnt.json: texts that stay in English everywhere
- template.html: the page design
- build.py / translate.py: the build
