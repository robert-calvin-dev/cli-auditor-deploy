
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
import time
import csv
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

class SEOAuditor:
    def __init__(self, base_url, output_dir="reports", template_dir="seo_auditor/templates", config_dir="seo_auditor/config"):
        self.base_url = base_url if base_url.startswith("http") else f"https://{base_url}"
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.config_dir = config_dir
        self.domain = tldextract.extract(self.base_url).domain
        self.visited = set()
        self.internal_links = set()
        self.external_links = set()
        self.page_data = []
        self.duplicate_check = {
            'title': defaultdict(list),
            'meta': defaultdict(list)
        }

    def is_internal(self, url):
        ext_url = tldextract.extract(url)
        return ext_url.domain == self.domain

    def crawl_page(self, url):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            load_time = round(time.time() - start_time, 3)
            if response.status_code != 200:
                self.record_data(url, response.status_code, "", "", [], [], [], load_time)
                return []
            soup = BeautifulSoup(response.text, 'lxml')

            title = soup.title.string.strip() if soup.title else ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            meta_description = meta_tag["content"].strip() if meta_tag else ""

            h1_tags = [h1.text.strip() for h1 in soup.find_all("h1")]
            images = soup.find_all("img")
            missing_alt = [img.get("src") for img in images if not img.get("alt")]

            found_links = []
            for link in soup.find_all("a", href=True):
                full_url = urljoin(url, link["href"])
                parsed = urlparse(full_url)
                if parsed.scheme in ["http", "https"]:
                    if self.is_internal(full_url):
                        found_links.append(full_url)
                    else:
                        self.external_links.add(full_url)

            broken_links = []
            for a in soup.find_all("a", href=True):
                link_url = urljoin(url, a["href"])
                try:
                    link_response = requests.head(link_url, timeout=5)
                    if link_response.status_code >= 400:
                        broken_links.append(link_url)
                except:
                    broken_links.append(link_url)

            self.record_data(url, response.status_code, title, meta_description, h1_tags, missing_alt, broken_links, load_time)
            self.duplicate_check["title"][title].append(url)
            self.duplicate_check["meta"][meta_description].append(url)

            return found_links
        except Exception as e:
            print(f"[ERROR] crawl_page failed for {url}: {e}")
            self.record_data(url, "ERROR", "", "", [], [], [], 0)
            return []

    def record_data(self, url, status, title, meta_desc, h1_tags, missing_alt, broken_links, load_time):
        self.page_data.append({
            "URL": url,
            "Status Code": status,
            "Load Time": load_time,
            "Title": title,
            "Title Length": len(title) if title else 0,
            "Meta Description": meta_desc,
            "Meta Length": len(meta_desc) if meta_desc else 0,
            "H1 Tags": len(h1_tags),
            "Missing ALT Images": len(missing_alt),
            "Broken Links": len(broken_links),
            "Broken Links List": broken_links
        })

    def crawl(self):
        print("[*] Starting crawl...")
        queue = [self.base_url]
        while queue:
            current = queue.pop(0)
            if current not in self.visited:
                self.visited.add(current)
                links = self.crawl_page(current)
                for link in links:
                    if link not in self.visited:
                        queue.append(link)
        print(f"[*] Crawled {len(self.visited)} pages.")

    def save_report(self):
        if not self.page_data:
            print("❌ No data to save.")
            return None, None

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs(self.output_dir, exist_ok=True)
        csv_path = os.path.join(self.output_dir, f"report_{timestamp}.csv")
        html_path = os.path.join(self.output_dir, f"report_{timestamp}.html")

        print(f"[*] Writing CSV to {csv_path}")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.page_data[0].keys())
            writer.writeheader()
            for row in self.page_data:
                writer.writerow(row)

        try:
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template("report_template.html")
            rendered = template.render(
                data=self.page_data,
                duplicate_titles={k: v for k, v in self.duplicate_check['title'].items() if len(v) > 1},
                duplicate_meta={k: v for k, v in self.duplicate_check['meta'].items() if len(v) > 1},
                external_links=self.external_links,
                timestamp=timestamp
            )
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(rendered)
            print(f"[+] HTML report saved to: {html_path}")
        except Exception as e:
            print(f"⚠️ Failed to render HTML: {e}")

        print(f"[+] CSV exists? {os.path.exists(csv_path)}")
        return csv_path, html_path
