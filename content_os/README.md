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

## Local test-first in restricted networks

If `pip install -e ./content_os` fails in offline/proxy-restricted environments, run tests directly first:

```bash
cd content_os
python -m pytest -q
```

## Offline packaging (proxy-restricted environments)

### 1) On a connected machine, prebuild wheels
```bash
cd content_os
python -m pip install --upgrade pip wheel
python -m pip wheel -r requirements-lock.txt -w ./wheelhouse
```

### 2) Move artifacts to restricted environment
- Copy `content_os/wheelhouse/`
- Copy `content_os/requirements-lock.txt`

### 3) Install without internet
```bash
cd content_os
python -m pip install --no-index --find-links=./wheelhouse -r requirements-lock.txt
```

### 4) Fallback: run tests without editable install
```bash
cd content_os
python -m pytest -q
```
