import json
import os
import re
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
from html import escape

# ==========================================
# CONFIGURATION
# ==========================================
# IMPORTANT: Get SERPER_API_KEY from environment variable for security
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Fallback check for local testing or misconfiguration
if not SERPER_API_KEY or SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
    # If not in GitHub Actions, we might want to allow a default for the user if they really want it
    # but for security and reliable CI/CD, it's better to fail early.
    print("❌ ERROR: SERPER_API_KEY is not set. Please set it as an environment variable.")
    # Exit with code 1 so GitHub Actions marked as failure
    import sys
    sys.exit(1)

# List of unique search queries (19 Terms)
QUERIES = [
    # กลุ่ม A — Term หลัก
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน OR วัสดุ) (ชำรุด OR เสื่อมสภาพ OR \"ไม่จำเป็น\") -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:instagram.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "ประกาศ \"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:instagram.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ประมูลขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) -บังคับคดี -\"รอขาย\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "(จำหน่าย OR \"ขายพัสดุ\") (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (ชำรุด OR เสื่อมสภาพ) ราชการ -บังคับคดี -\"รอขาย\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    
    # กลุ่ม B — แยกตามประเภทสินทรัพย์
    "\"ขายทอดตลาด\" (รถยนต์ OR รถตู้ OR รถบรรทุก OR รถกระบะ OR ยานพาหนะ OR \"ครุภัณฑ์ยานพาหนะ\") -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (อาคาร OR \"สิ่งปลูกสร้าง\" OR รื้อถอน) (โรงเรียน OR ราชการ OR จังหวัด OR หน่วยงาน) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th",
    "\"ขายทอดตลาด\" (ครุภัณฑ์ OR เครื่องมือ OR อุปกรณ์) (การแพทย์ OR โรงพยาบาล OR สาธารณสุข) (ชำรุด OR เสื่อมสภาพ) -บังคับคดี -\"รอขาย\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th",
    
    # กลุ่ม C — หน่วยงาน
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (จังหวัด OR สำนักงาน OR กรม OR กอง OR ศูนย์ OR สำนัก OR องค์การ OR เทศบาล OR อบต OR โรงพยาบาล OR มหาวิทยาลัย OR โรงเรียน OR ศาล) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    
    # กลุ่ม D — แยกตามภูมิภาค
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (กรุงเทพ OR กรุงเทพมหานคร OR นนทบุรี OR ปทุมธานี OR สมุทรปราการ OR สมุทรสาคร OR นครปฐม) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (อยุธยา OR \"พระนครศรีอยุธยา\" OR สระบุรี OR ลพบุรี OR สิงห์บุรี OR อ่างทอง OR ชัยนาท OR สุพรรณบุรี OR กาญจนบุรี OR ราชบุรี) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (ชลบุรี OR ระยอง OR จันทบุรี OR ตราด OR ฉะเชิงเทรา OR ปราจีนบุรี OR สระแก้ว) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (ประจวบคีรีขันธ์ OR เพชรบุรี OR สมุทรสงคราม OR ตาก OR กาญจนบุรี) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (ขอนแก่น OR อุดรธานี OR หนองคาย OR เลย OR นครพนม OR สกลนคร OR มุกดาหาร OR หนองบัวลำภู OR บึงกาฬ) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (นครราชสีมา OR บุรีรัมย์ OR สุรินทร์ OR ศรีสะเกษ OR อุบลราชธานี OR ยโสธร OR อำนาจเจริญ OR มหาสารคาม OR ร้อยเอ็ด OR กาฬสินธุ์) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (เชียงใหม่ OR เชียงราย OR ลำปาง OR ลำพูน OR แม่ฮ่องสอน OR พะเยา OR แพร่ OR น่าน) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (พิษณุโลก OR สุโขทัย OR อุตรดิตถ์ OR กำแพงเพชร OR พิจิตร OR เพชรบูรณ์ OR นครสวรรค์ OR อุทัยธานี) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (สุราษฎร์ธานี OR ชุมพร OR ระนอง OR นครศรีธรรมราช OR กระบี่ OR พังงา OR ภูเก็ต) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    "\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์ OR ทรัพย์สิน) (สงขลา OR สตูล OR ตรัง OR พัทลุง OR ปัตตานี OR ยะลา OR นราธิวาส) -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\" -site:youtube.com -site:x.com -site:tiktok.com -site:led.go.th -site:bidding.pea.co.th",
    
    # กลุ่ม E — Term พิเศษเฉพาะเว็บ
    "ขายทอดตลาด site:webportal.bangkok.go.th"
]

# Filtering Words
NEGATIVE_WORDS = [
    "ผู้ชนะ", "ยกเลิก", "รปภ",
    "มือสอง", "ทุบตึก", "ตัวแทน", "เช่าซื้อ", "อาคารพาณิชย์", "ขายอาคาร",
    "บังคับคดี", "รอขาย", "ธนาคารยึด", "ที่ดิน", "ธนาคาร", "อย่างไร", "ไหม", "หรือไม่"
]
NEGATIVE_DOMAINS = ["tiktok.com", "youtube.com", "instagram.com", "x.com", "led.go.th", "bidding.pea.co.th"]
HIGHLIGHT_WORDS = ["ขายทอดตลาด", "จำหน่าย", "ประกาศขาย", "ครุภัณฑ์", "พัสดุ", "วัสดุ", "รถยนต์", "อาคาร", "รื้อถอน", "เสื่อมสภาพ", "ชำรุด"]

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
        "num": 50    # Try to fetch up to 50 results
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

def generate_html_report(results):
    now = datetime.now()
    filename = f"result_{now.strftime('%d_%m_%Y_%H_%M')}.html"
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
                background-color: #fff; /* Google uses white background */
                margin: 0;
                padding: 20px 40px;
                color: #202124;
            }}
            .container {{
                max-width: 652px; /* Close to Google Search width */
                margin: 0;
            }}
            h1 {{
                font-size: 22px;
                font-weight: normal;
                margin-bottom: 5px;
            }}
            .meta {{
                font-size: 14px;
                color: #70757a;
                margin-bottom: 25px;
                border-bottom: 1px solid #ebebeb;
                padding-bottom: 15px;
            }}
            .result-item {{
                margin-bottom: 28px;
                padding: 10px;
                border-radius: 8px;
                transition: background-color 0.2s;
                position: relative;
            }}
            .result-item.read {{
                background-color: #ffebee !important;
            }}
            .result-top {{
                display: flex;
                align-items: center;
                margin-bottom: 4px;
            }}
            /* Mimic Google's icon/domain display */
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
            }}
            .result-title h3 {{
                font-size: 20px;
                color: #1a0dab;
                margin: 0;
                padding: 0;
                font-weight: normal;
                display: inline;
            }}
            .result-title:hover h3 {{
                text-decoration: underline;
            }}
            /* Stylus can override this easily */
            .result-title:visited h3 {{
                color: #609;
            }}
            .result-snippet {{
                font-size: 14px;
                line-height: 1.58;
                color: #4d5156;
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="font-size: 32px; font-weight: bold; border-bottom: 3px solid #1a0dab; padding-bottom: 10px; margin-bottom: 20px;">
                📄 ผลการค้นหาประจำวันที่ {date}
            </h1>
            <div class="meta">พบข้อมูลทั้งหมด {count} รายการ</div>
            
            <div id="results-list">
                {results_html}
            </div>
        </div>

        <script>
            // Handle clicking links to mark as read (Fallback option)
            document.addEventListener('DOMContentLoaded', function() {{
                const links = document.querySelectorAll('.tracked-link');
                let viewedLinks = JSON.parse(localStorage.getItem('viewedLinks')) || [];
                
                links.forEach(link => {{
                    const url = link.getAttribute('href');
                    const parentItem = link.closest('.result-item');
                    if(viewedLinks.includes(url)) {{
                        parentItem.classList.add('read');
                    }}
                    link.addEventListener('click', function(e) {{
                        if(!viewedLinks.includes(url)) {{
                            viewedLinks.push(url);
                            localStorage.setItem('viewedLinks', JSON.stringify(viewedLinks));
                        }}
                        parentItem.classList.add('read');
                    }});
                }});
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
        badge_text = 'ภายใน 24 ชั่วโมงที่ผ่านมา — ' if found_in == '1d' else 'ภายใน 7 วันที่ผ่านมา — '

        results_html += f"""
        <div class="result-item">
            <div class="index-badge">{idx}.</div>
            <div class="result-top">
                <div class="result-icon">
                    <img src="{favicon_url}" alt="icon" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNWY2MzY4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiPjwvY2lyY2xlPjxsaW5lIHgxPSIyIiB5MT0iMTIiIHgyPSIyMiIgeTI9IjEyIj48L2xpbmU+PHBhdGggZD0iTTEyIDJhMTUuMyAxNS4zIDAgMCAxIDQgMTBhMTUuMyAxNS4zIDAgMCAxLTQgMTBhMTUuMyAxNS4zIDAgMCAxLTQtMTBBMTUuMyAxNS4zIDAgMCAxIDEyIDJ6Ij48L3BhdGg+PC9zdmc+'" />
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

    final_html = html_template.format(
        date=now.strftime('%d/%m/%Y %H:%M'),
        count=len(results),
        results_html=results_html
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"✅ Report successfully generated at: {filepath}")
    return filepath

def generate_index_html():
    import glob
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "result_*.html")), reverse=True)
    
    links_html = ""
    for f in files:
        fname = os.path.basename(f)
        # Extract date/time from filename result_DD_MM_YYYY_HH_MM.html
        match = re.search(r'result_(\d{2})_(\d{2})_(\d{4})_(\d{2})_(\d{2})', fname)
        if match:
            d, m, y, hh, mm = match.groups()
            display_name = f"รายงานวันที่ {d}/{m}/{y} เวลา {hh}:{mm}"
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

    all_results = {}
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
            
        print(f"[{i+1}/{len(QUERIES)}] Querying: {query} ...")
        
        # Search last 24 hours (for all except E1)
        # For E1 (last item), search last 1 month if it's the webportal query
        timeframes = ["qdr:d", "qdr:w"]
        if "webportal.bangkok.go.th" in query:
            timeframes = ["qdr:m"] # Bangkok Web Portal 1 month

        for tbs in timeframes:
            print(f"[{i+1}/{len(QUERIES)}] Querying: {query[:50]}... (tbs={tbs})")
            results = search_serper(query, tbs)
            found_tag = '1d' if tbs == 'qdr:d' else ('7d' if tbs == 'qdr:w' else '1m')
            for r in results:
                url = r.get('link')
                if url and url not in all_results:
                    if is_valid_result(url, r.get('title', ''), r.get('snippet', '')):
                        r['_found_in'] = found_tag
                        all_results[url] = r

    # Convert Dict back to List
    final_list = list(all_results.values())
    
    # Sort the list: prioritizing 1d results first, then alphabetically
    final_list_sorted = sorted(final_list, key=lambda x: (x['_found_in'], x.get('title', '')))

    print(f"\n🔍 Found {len(final_list_sorted)} absolute unique and matching results.")
    
    generate_html_report(final_list_sorted)
    generate_index_html()

if __name__ == "__main__":
    main()
