import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eval.compliance import ComplianceEvaluator


def main():
    parser = argparse.ArgumentParser(description="Apply disclosure templates to title/content")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content-file", required=True)
    parser.add_argument("--language", default="ko", choices=["ko", "en"])
    parser.add_argument("--disclosure-required", action="store_true")
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    content = open(args.content_file, "r", encoding="utf-8").read()
    evaluator = ComplianceEvaluator()
    patched = evaluator.apply_disclosures(
        title=args.title,
        content=content,
        language=args.language,
        disclosure_required=args.disclosure_required,
    )

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(patched["content"])

    print(json.dumps(patched, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
