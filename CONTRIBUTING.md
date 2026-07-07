# Contributing

Keep changes small, local, typed, and documented. Preserve the local-first
architecture and avoid adding dependencies unless they are necessary.

Before submitting changes, run:

```bash
python3 -m pytest
python3 -m compileall assistant main.py
```

Do not add Version 2 features such as voice, OCR, vision, browser control, mouse
control, keyboard control, or desktop automation to Version 1 code.
