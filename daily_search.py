import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import urllib.error
from html import escape

# ==========================================
# CONFIGURATION
# ==========================================
# IMPORTANT: Get SERPER_API_KEY from environment variable for security
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Local testing support: Check for serper_key.txt if env var is missing
if not SERPER_API_KEY or SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
    key_file = os.path.join(os.path.dirname(__file__), "serper_key.txt")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf8") as f:
                SERPER_API_KEY = f.read().strip()
                print(f"ℹ️ Using API Key from local file: {key_file}")
        except Exception as e:
            print(f"⚠️ Error reading {key_file}: {e}")

if not SERPER_API_KEY or SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
    print("❌ ERROR: SERPER_API_KEY is not set.")
    print("👉 To run locally: Create a file named 'serper_key.txt' and paste your key inside.")
    print("👉 To run in GitHub: Add 'SERPER_API_KEY' to your Repository Secrets.")
    # Exit with code 1 so GitHub Actions marked as failure
    import sys
    sys.exit(1)

# List of unique search queries (add/remove entries freely — count updates automatically)
QUERIES = [
    # กลุ่ม A — Term หลัก (ปรับปรุง: นำ "ราชการ" ออกเพื่อให้กว้างขึ้น)
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน OR วัสดุ) (ชำรุด OR เสื่อมสภาพ OR \"ไม่จำเป็น\") -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:instagram.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "ประกาศ \"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:instagram.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ประมูลขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) -บังคับคดี -\"รอขาย\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "(จำหน่าย OR \"ขายพัสดุ\" OR \"ขายครุภัณฑ์\") (พัสดุ OR ครุภัณฑ์) (ชำรุด OR เสื่อมสภาพ OR \"ไม่จำเป็น\") -บังคับคดี -\"รอขาย\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "(จำหน่าย OR \"ขายพัสดุ\") (พัสดุ OR ครุภัณฑ์) (เฉพาะเจาะจง OR \"เจรจาตกลงราคา\") -บังคับคดี -site:youtube.com -site:led.go.th",

    # กลุ่มใหม่: เจาะจงหน่วยงาน (Targeted Agencies)
    "+\"สำนักงาน\" +\"จังหวัด\" +\"ขายทอดตลาด\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -site:pea.co.th -site:egat.go.th -\"องค์การบริหารส่วนตำบล\" -\"เทศบาล\"",
    "+\"สำนักงาน\" +\"จังหวัด\" +\"จำหน่ายพัสดุ\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -site:pea.co.th -site:egat.go.th -\"องค์การบริหารส่วนตำบล\" -\"เทศบาล\"",
    "+\"โรงเรียน\" +\"ขายทอดตลาด\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -\"เทศบาล\" -\"องค์การบริหาร\" -\"ผู้ชนะ\" -site:tiktok.com -\"บังคับคดี\" -site:instagram.com",
    "+\"โรงพยาบาล\" +\"ขายทอดตลาด\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -\"เทศบาล\" -\"องค์การบริหาร\" -\"ผู้ชนะ\" -site:tiktok.com -\"บังคับคดี\" -site:instagram.com",
    "+\"มหาวิทยาลัย\" +\"ขายทอดตลาด\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -\"เทศบาล\" -\"องค์การบริหาร\" -\"ผู้ชนะ\" -site:tiktok.com -\"บังคับคดี\" -site:instagram.com",
    "+\"สำนักงานเขตพื้นที่การศึกษา\" +\"ขายทอดตลาด\" -site:prd.go.th -site:led.go.th -site:facebook.com -site:youtube.com -site:gprocurement.go.th -\"เทศบาล\" -\"องค์การบริหาร\" -\"ผู้ชนะ\" -site:tiktok.com -\"บังคับคดี\" -site:instagram.com",
    "\"ขายทอดตลาด\" site:ac.th",

    # กลุ่มเดิมอื่นๆ
    "\"ขายทอดตลาด\" (รถยนต์ OR รถตู้ OR รถบรรทุก OR รถกระบะ OR ยานพาหนะ OR \"ครุภัณฑ์ยานพาหนะ\") -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (อาคาร OR \"สิ่งปลูกสร้าง\" OR รื้อถอน) (โรงเรียน OR จังหวัด OR หน่วยงาน) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th",
    "\"ขายทอดตลาด\" (ครุภัณฑ์ OR เครื่องมือ OR อุปกรณ์) (การแพทย์ OR โรงพยาบาล OR สาธารณสุข) (ชำรุด OR เสื่อมสภาพ) -บังคับคดี -\"รอขาย\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (จังหวัด OR สำนักงาน OR กรม OR กอง OR ศูนย์ OR สำนัก OR องค์การ OR เทศบาล OR อบต OR โรงพยาบาล OR มหาวิทยาลัย OR โรงเรียน OR ศาล) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (site:webportal.bangkok.go.th OR site:prd.go.th OR site:coj.go.th)",
    "ขายทอดตลาด site:.prd.go.th"
]

# Filtering Words
NEGATIVE_WORDS = [
    "ผู้ชนะ", "ยกเลิก", "รปภ",
    "มือสอง", "ทุบตึก", "ตัวแทน", "เช่าซื้อ", "อาคารพาณิชย์", "ขายอาคาร",
    "บังคับคดี", "รอขาย", "ธนาคารยึด", "ที่ดิน", "ธนาคาร", "อย่างไร", "ไหม"
]
NEGATIVE_DOMAINS = [
    "tiktok.com", "youtube.com", "instagram.com", "x.com", "led.go.th", 
    "bidding.pea.co.th", "gprocurement.go.th", "pea.co.th", "egat.co.th"
]
HIGHLIGHT_WORDS = [
    "ขายทอดตลาด", "จำหน่าย", "ประกาศขาย", "ครุภัณฑ์", "พัสดุ", "วัสดุ", "รถยนต์", 
    "อาคาร", "รื้อถอน", "เสื่อมสภาพ", "ชำรุด", "ไม่จำเป็นต้องใช้งาน", "อบต", "เทศบาล"
]

# Directories
# If running in GitHub Actions, use current directory
OUTPUT_DIR = "." if os.getenv("GITHUB_ACTIONS") else "D:/project deep search"

# ==========================================
# FUNCTIONS
# ==========================================

def search_serper(query, tbs):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "tbs": tbs,  # "qdr:d" for 24h, "qdr:w" for 7 days
        "gl": "th",  # Thailand
        "hl": "th",  # Thai language
        "num": 100    # Fetch up to 100 results as requested
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            return json.loads(res_data).get("organic", [])
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error for query '{query}': {e.code} {e.reason}")
        if e.code == 403:
            print("   Hint: Your SERPER_API_KEY might be invalid or reached its limit.")
        return []
    except Exception as e:
        print(f"❌ Error querying '{query}' with tbs={tbs}: {e}")
        return []

def is_valid_result(url, title, snippet):
    combined_text = f"{title} {snippet}".lower()
    
    # Check for negative domains in URL
    for domain in NEGATIVE_DOMAINS:
        if domain in url.lower():
            return False

    # Check for negative keywords
    for word in NEGATIVE_WORDS:
        if word in combined_text:
            return False
            
    # Check for menu-like patterns (multiple separators)
    menu_indicators = [" · ", " | ", " > ", " - "]
    separator_count = 0
    for sep in menu_indicators:
        separator_count += combined_text.count(sep)
    if separator_count >= 3: # Likely a menu or sitemap
        return False

    # Enforce that the snippet OR title MUST contain at least one important keyword
    has_keyword = False
    for word in HIGHLIGHT_WORDS:
        if word in title or word in snippet:
            has_keyword = True
            break
            
    if not has_keyword:
        return False
        
    return True

def highlight_text(text):
    if not text:
        return ""
    highlighted = escape(text)
    for word in HIGHLIGHT_WORDS:
        highlighted = re.sub(f"({word})", r"<span class='highlight'>\1</span>", highlighted, flags=re.IGNORECASE)
    return highlighted

def get_ict_now():
    """Return current datetime in ICT (UTC+7), works on GitHub Actions (UTC) and local."""
    return datetime.utcnow() + timedelta(hours=7)

def load_daily_json(date_str):
    """Load accumulated results JSON for a given date. Returns dict {url: result}."""
    filepath = os.path.join(OUTPUT_DIR, f"result_{date_str}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📂 Loaded {len(data)} existing results from {filepath}")
                return data
        except Exception as e:
            print(f"⚠️ Could not load existing JSON ({filepath}): {e}")
    return {}

def save_daily_json(date_str, results_dict):
    """Save accumulated results dict to JSON for the given date."""
    filepath = os.path.join(OUTPUT_DIR, f"result_{date_str}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(results_dict)} results to {filepath}")
    except Exception as e:
        print(f"⚠️ Could not save JSON ({filepath}): {e}")

# NOTE: Cross-day history filtering has been removed.
# Deduplication is handled only within the same day (via daily JSON).
# The browser-based "Mark as Read" feature (localStorage) handles visual dedup for the user.

def generate_html_report(results, date_str):
    ict_now = get_ict_now()
    filename = f"result_{date_str}_daily.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    html_template = """
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>รายงานผลการค้นหา {date}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #fff;
                margin: 0;
                padding: 20px 40px;
                color: #202124;
            }}
            .container {{
                max-width: 652px;
                margin: 0;
            }}
            h1 {{
                font-size: 32px;
                font-weight: bold;
                border-bottom: 3px solid #1a0dab;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .meta {{
                font-size: 14px;
                color: #70757a;
                margin-bottom: 25px;
                border-bottom: 1px solid #ebebeb;
                padding-bottom: 15px;
            }}
            /* ===== READ / UNREAD STATES ===== */
            .result-item {{
                margin-bottom: 28px;
                padding: 10px 10px 10px 14px;
                border-left: 4px solid transparent;
                border-radius: 4px;
                transition: background-color 0.25s, opacity 0.25s;
                position: relative;
            }}
            .result-item.read {{
                background-color: #f5f5f5;
                opacity: 0.55;
                border-left-color: #bdbdbd;
            }}
            .result-item.read .result-title h3 {{
                text-decoration: line-through;
                color: #9e9e9e;
            }}
            .result-item.read .result-snippet {{
                color: #bdbdbd;
            }}
            /* ===== MARK-AS-READ BUTTON ===== */
            .mark-read-btn {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: none;
                border: 1.5px solid #bdbdbd;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                cursor: pointer;
                font-size: 14px;
                color: #bdbdbd;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                flex-shrink: 0;
            }}
            .mark-read-btn:hover {{
                background-color: #e8f5e9;
                border-color: #4caf50;
                color: #4caf50;
            }}
            .result-item.read .mark-read-btn {{
                border-color: #4caf50;
                color: #4caf50;
                background-color: #e8f5e9;
            }}
            /* ===== RESULT CARD ELEMENTS ===== */
            .result-top {{
                display: flex;
                align-items: center;
                margin-bottom: 4px;
                padding-right: 36px;
            }}
            .result-icon {{
                background-color: #f1f3f4;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 12px;
                overflow: hidden;
                flex-shrink: 0;
            }}
            .result-icon img {{
                width: 16px;
                height: 16px;
            }}
            .result-site-info {{
                display: flex;
                flex-direction: column;
            }}
            .result-site-name {{
                font-size: 14px;
                color: #202124;
                text-decoration: none;
            }}
            .result-url {{
                font-size: 12px;
                color: #4d5156;
                text-decoration: none;
                word-wrap: break-word;
            }}
            .result-title {{
                text-decoration: none;
                display: inline-block;
                margin-bottom: 4px;
                line-height: 1.3;
                padding-right: 36px;
            }}
            .result-title h3 {{
                font-size: 20px;
                color: #1a0dab;
                margin: 0;
                padding: 0;
                font-weight: normal;
                display: inline;
                transition: color 0.25s;
            }}
            .result-title:hover h3 {{
                text-decoration: underline;
            }}
            .result-title:visited h3 {{
                color: #609;
            }}
            .result-snippet {{
                font-size: 14px;
                line-height: 1.58;
                color: #4d5156;
                transition: color 0.25s;
            }}
            .highlight {{
                color: #c5221f;
                font-weight: bold;
                background-color: transparent;
            }}
            .date-badge {{
                color: #70757a;
            }}
            .index-badge {{
                position: absolute;
                left: -35px;
                top: 15px;
                font-size: 14px;
                color: #70757a;
                font-weight: bold;
            }}
            .stats-bar {{
                font-size: 13px;
                color: #70757a;
                margin-bottom: 8px;
            }}
            #clear-all-btn {{
                font-size: 12px;
                color: #1a73e8;
                cursor: pointer;
                background: none;
                border: none;
                padding: 0;
                margin-left: 12px;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 ผลการค้นหาประจำวันที่ {date}</h1>
            <div class="meta">
                พบข้อมูลทั้งหมด {count} รายการ
                <span class="stats-bar" id="stats-bar"></span>
            </div>
            <div style="margin-bottom:16px;">
                <button id="clear-all-btn" onclick="clearAllRead()">↺ รีเซ็ต "อ่านแล้ว" ทั้งหมด</button>
            </div>

            <div id="results-list">
                {results_html}
            </div>
        </div>

        <script>
            const STORAGE_KEY = 'viewedLinks_v2';

            function getViewed() {{
                return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
            }}
            function saveViewed(arr) {{
                localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
            }}
            function updateStats() {{
                const total = document.querySelectorAll('.result-item').length;
                const read  = document.querySelectorAll('.result-item.read').length;
                const bar   = document.getElementById('stats-bar');
                if (bar) bar.textContent = ` — อ่านแล้ว ${{read}} / ${{total}} รายการ`;
            }}
            function clearAllRead() {{
                saveViewed([]);
                document.querySelectorAll('.result-item.read').forEach(el => el.classList.remove('read'));
                updateStats();
            }}

            document.addEventListener('DOMContentLoaded', function() {{
                let viewed = getViewed();

                document.querySelectorAll('.result-item').forEach(item => {{
                    const url = item.dataset.url;
                    const btn = item.querySelector('.mark-read-btn');

                    // Restore read state
                    if (viewed.includes(url)) item.classList.add('read');

                    // Mark-as-read button
                    btn.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        let v = getViewed();
                        if (item.classList.contains('read')) {{
                            // Toggle back to unread
                            item.classList.remove('read');
                            v = v.filter(u => u !== url);
                        }} else {{
                            item.classList.add('read');
                            if (!v.includes(url)) v.push(url);
                        }}
                        saveViewed(v);
                        updateStats();
                    }});

                    // Clicking any link also marks as read
                    item.querySelectorAll('.tracked-link').forEach(link => {{
                        link.addEventListener('click', function() {{
                            let v = getViewed();
                            if (!v.includes(url)) {{
                                v.push(url);
                                saveViewed(v);
                            }}
                            item.classList.add('read');
                            updateStats();
                        }});
                    }});
                }});

                updateStats();
            }});
        </script>
    </body>
    </html>
    """

    results_html = ""
    for idx, r in enumerate(results, 1):
        title = highlight_text(r.get('title', ''))
        snippet = highlight_text(r.get('snippet', ''))
        url = r.get('link', '#')
        
        # Parse domain from URL
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        # Basic Google Favicon Service
        favicon_url = f"https://s2.googleusercontent.com/s2/favicons?domain={domain}&sz=32"
        
        # Format the URL for display
        try:
            decoded_url = urllib.parse.unquote(url)
        except:
            decoded_url = url
            
        display_url = decoded_url
        if len(display_url) > 65:
            display_url = display_url[:45] + "..." + display_url[-15:]
            
        found_in = r.get('_found_in', '7d')
        found_at = r.get('_found_at', 'N/A')
        badge_text = f'({found_at}) '
        if found_in == '1d':
            badge_text += 'ภายใน 24 ชม. — '
        elif found_in == '7d':
            badge_text += 'ภายใน 7 วัน — '
        else:
            badge_text += 'ภายใน 1 เดือน — '
            
        # Escape url for use in data-url attribute
        url_escaped = escape(url)

        results_html += f"""
        <div class="result-item" data-url="{url_escaped}">
            <div class="index-badge">{idx}.</div>
            <button class="mark-read-btn" title="อ่านแล้ว / ยังไม่ได้อ่าน">✓</button>
            <div class="result-top">
                <div class="result-icon">
                    <img src="{favicon_url}" alt="icon" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNWY2MzY4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiPjwvY2lyY2xlPjxsaW5lIHgxPSIyIiB5MT0iMTIiIHgyPSIyMiIgeTI9IjEyIj48L2xpbmU+PHBhdGggZD0iTTEyIDJhMTUuMyAxNS4zIDAgMCAxIDQgMTBhMTUuMyAxNS4zIDAgMCAxLTQgMTBhMTUuMyAxNS4zIDAgMCAxLTQtMTBBMTUuMyAxNS4zIDAgMCAxIDEyIDJ6Ij48L3BhdGg+PC9zdmc+' " />
                </div>
                <div class="result-site-info">
                    <a href="{url}" class="result-site-name tracked-link" target="_blank">{domain}</a>
                    <a href="{url}" class="result-url tracked-link" target="_blank">{display_url}</a>
                </div>
            </div>
            <a href="{url}" class="result-title tracked-link LC20lb" target="_blank">
                <h3>{title}</h3>
            </a>
            <div class="result-snippet">
                <span class="date-badge">{badge_text}</span>{snippet}
            </div>
        </div>
        """

    # Format date display (DD/MM/YYYY) from date_str (DD_MM_YYYY)
    d, m, y = date_str.split('_')
    date_display = f"{d}/{m}/{y}"
    final_html = html_template.format(
        date=date_display,
        count=len(results),
        results_html=results_html
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"✅ Report successfully generated at: {filepath}")
    return filepath

def generate_index_html():
    import glob
    # Only list daily digest files (one per day)
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "result_*_daily.html")), reverse=True)
    
    links_html = ""
    for f in files:
        fname = os.path.basename(f)
        # Extract date from filename result_DD_MM_YYYY_daily.html
        match = re.search(r'result_(\d{2})_(\d{2})_(\d{4})_daily', fname)
        if match:
            d, m, y = match.groups()
            display_name = f"📅 รายงานประจำวันที่ {d}/{m}/{y}"
            links_html += f'<li><a href="{fname}" class="report-link">{display_name}</a></li>\n'
        else:
            links_html += f'<li><a href="{fname}" class="report-link">{fname}</a></li>\n'

    index_template = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Auction Report Sitemap</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                padding: 40px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 600px;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
                font-size: 24px;
            }}
            ul {{
                list-style: none;
                padding: 0;
            }}
            li {{
                margin-bottom: 12px;
            }}
            .report-link {{
                display: block;
                padding: 15px 20px;
                background-color: #ffffff;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                text-decoration: none;
                color: #34495e;
                font-weight: 500;
                transition: all 0.3s ease;
            }}
            .report-link:hover {{
                background-color: #3498db;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .footer {{
                margin-top: 30px;
                color: #7f8c8d;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 รายการรายงานการค้นหาทั้งหมด</h1>
            <ul>
                {links_html}
            </ul>
        </div>
        <div class="footer">อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </body>
    </html>
    """
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_template)
    print(f"✅ Index page successfully generated at: {index_path}")

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    if SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
        print("❌ Error: Please set your SERPER_API_KEY in the script first.")
        return

    # ── ICT date for today (UTC+7) — works on GitHub Actions (UTC) and locally ──
    ict_now = get_ict_now()
    date_str = ict_now.strftime('%d_%m_%Y')   # e.g. "03_03_2026"
    print(f"📅 Report date (ICT): {date_str}")

    # ── Load accumulated results from earlier runs today (Daily Digest) ──
    all_results = load_daily_json(date_str)   # dict: {url: result}
    
    print(f"🚀 Starting Search Process using {len(QUERIES)} queries...")
    
    for i, raw_query in enumerate(QUERIES):
        query = raw_query.replace('"', '') # REMOVE QUOTES TO PREVENT HTTP 400
        # REMOVE 'site:' operators as Serper blocks them directly
        query = re.sub(r'site:\S+', '', query).strip()
        # REMOVE '-.domain.go.th' blocks which might also trigger the generic block
        query = re.sub(r'-\S+\.go\.th', '', query).strip()
        query = re.sub(r'\s+', ' ', query) # clean up extra spaces
        
        # If query is too empty after stripping, skip
        if not query:
            continue
            
        # Determine timeframes for this query
        timeframes = ["qdr:d", "qdr:w"]
        if "webportal.bangkok.go.th" in raw_query or ".prd.go.th" in raw_query:
            timeframes = ["qdr:m"]  # Special sites: search 1 month

        for tbs in timeframes:
            print(f"[{i+1}/{len(QUERIES)}] Querying: {query[:60]}... (tbs={tbs})")
            results = search_serper(query, tbs)
            found_tag = '1d' if tbs == 'qdr:d' else ('7d' if tbs == 'qdr:w' else '1m')
            
            for r in results:
                url = r.get('link')
                title = r.get('title', '')
                if not url: continue
                
                # Skip if already in current day's results (same-day dedup by URL only)
                if url in all_results:
                    continue

                # Valid result? Add to today's collection
                if is_valid_result(url, title, r.get('snippet', '')):
                    r['_found_in'] = found_tag
                    r['_found_at'] = ict_now.strftime('%H:%M')
                    all_results[url] = r

    # ── Save accumulated state back to JSON ──
    save_daily_json(date_str, all_results)

    # ── Sort: 1d first, then 7d, then 1m, then alphabetically by title ──
    priority = {'1d': 0, '7d': 1, '1m': 2}
    final_list_sorted = sorted(
        all_results.values(),
        key=lambda x: (priority.get(x.get('_found_in', '7d'), 1), x.get('title', ''))
    )

    print(f"\n🔍 Found {len(final_list_sorted)} unique results total (accumulated for {date_str}).")
    
    generate_html_report(final_list_sorted, date_str)
    generate_index_html()

if __name__ == "__main__":
    main()
