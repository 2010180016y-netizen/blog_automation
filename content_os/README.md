# Content Compliance Rule Engine

Part of the Content-Commerce OS.

## Features
- Multi-language support (KO/EN)
- Rule-based detection for banned claims
- Disclosure requirement checks
- YMYL section validation
- Pattern-based efficacy claim detection

## Usage
### API
```bash
uvicorn app.main:app --reload
```

### CLI
```bash
python -m app.eval.compliance --file content.txt --lang ko
```
