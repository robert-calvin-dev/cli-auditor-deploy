import argparse
import os
from seo_auditor.auditor import SEOAuditor

def main():
    parser = argparse.ArgumentParser(
        description="SEO Site Auditor - Crawl a website and generate SEO reports in CSV and HTML format."
    )
    parser.add_argument(
        "url",
        type=str,
        help="The base URL of the website to audit (include http/https)."
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send the report via email if smtp.json is configured."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory to save reports (default: ./reports)"
    )
    parser.add_argument(
        "--template-dir",
        type=str,
        default="seo_auditor/templates",
        help="Directory where the HTML templates are stored"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="seo_auditor/config",
        help="Directory for smtp.json config"
    )

    args = parser.parse_args()

    print("ARGS PARSED:")
    print("URL:", args.url)
    print("Output Dir:", args.output_dir)
    print("Template Dir:", args.template_dir)
    print("Config Dir:", args.config_dir)

    auditor = SEOAuditor(
        base_url=args.url,
        output_dir=args.output_dir,
        template_dir=args.template_dir,
        config_dir=args.config_dir
    )

    try:
        print("[*] Starting crawl for", args.url)
        auditor.crawl()
        print("[*] Crawl complete.")
    except Exception as e:
        print("❌ Crawl failed:", str(e))
        exit(1)

    try:
        print("[*] Saving report...")
        csv_report, html_report = auditor.save_report()
        print("[+] Saved CSV to:", csv_report)
        print("[+] CSV exists:", os.path.exists(csv_report))
    except Exception as e:
        print("❌ Report generation failed:", str(e))
        exit(1)

    if args.email:
        print("[*] Sending report via email...")
        auditor.send_email_report(html_report)

if __name__ == "__main__":
    main()
