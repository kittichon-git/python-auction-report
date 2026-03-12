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
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

if not SERPER_API_KEY or SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
    key_file = os.path.join(os.path.dirname(__file__), "serper_key.txt")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf8") as f:
                SERPER_API_KEY = f.read().strip()
        except: pass

if not SERPER_API_KEY:
    import sys
    print("❌ ERROR: ไม่พบ SERPER_API_KEY")
    print("กรุณาตั้งค่า Environment Variable ชื่อ SERPER_API_KEY หรือสร้างไฟล์ serper_key.txt แล้วใส่ API Key ลงไป")
    sys.exit(1)

# Global Google-level exclusions for all queries to improve depth
# (Excluded led.go.th, youtube, etc. to open space for other results)
GOOGLE_EXCLUDES = "-site:led.go.th -site:youtube.com -site:x.com -site:instagram.com -site:tiktok.com -site:bidding.pea.co.th -site:gprocurement.go.th -site:prd.go.th -บังคับคดี -\"รอขาย\" -\"ธนาคารยึด\" -\"ที่ดิน\""

# Broad exclusion for AOJ/AOT/Municipalities to use in CORE queries (to prevent them from dominating)
LOCAL_DOMINANCE_EXCLUDES = "-อบต -เทศบาล -\"องค์การบริหารส่วนตำบล\" -\"องค์การบริหารส่วนจังหวัด\" -อบจ"

# Regional Province Lists
PROVINCES_NORTH = "เชียงใหม่ OR เชียงราย OR น่าน OR พะเยา OR แพร่ OR แม่ฮ่องสอน OR ลำปาง OR ลำพูน OR อุตรดิตถ์"
PROVINCES_NE = "กาฬสินธุ์ OR ขอนแก่น OR ชัยภูมิ OR นครพนม OR นครราชสีมา OR โคราช OR บึงกาฬ OR บุรีรัมย์ OR มหาสารคาม OR มุกดาหาร OR ยโสธร OR ร้อยเอ็ด OR เลย OR ศรีสะเกษ OR สกลนคร OR สุรินทร์ OR หนองคาย OR หนองบัวลำภู OR อำนาจเจริญ OR อุดรธานี OR อุบลราชธานี"
PROVINCES_CENTRAL = "กรุงเทพ OR นนทบุรี OR ปทุมธานี OR สมุทรปราการ OR อยุธยา OR สุโขทัย OR พิษณุโลก OR นครสวรรค์ OR กำแพงเพชร OR ชัยนาท OR นครนายก OR นครปฐม OR พิจิตร OR เพชรบูรณ์ OR ลพบุรี OR สมุทรสงคราม OR สมุทรสาคร OR สระบุรี OR สิงห์บุรี OR สุพรรณบุรี OR อ่างทอง OR อุทัยธานี"
PROVINCES_EAST = "จันทบุรี OR ฉะเชิงเทรา OR ชลบุรี OR ตราด OR ปราจีนบุรี OR ระยอง OR สระแก้ว"
PROVINCES_WEST = "กาญจนบุรี OR ตาก OR ประจวบคีรีขันธ์ OR เพชรบุรี OR ราชบุรี"
PROVINCES_SOUTH = "กระบี่ OR ชุมพร OR ตรัง OR นครศรีธรรมราช OR นราธิวาส OR ปัตตานี OR พังงา OR พัทลุง OR ภูเก็ต OR ระนอง OR สตูล OR สงขลา OR สุราษฎร์ธานี OR ยะลา"

# List of unique search queries organized by groups
QUERIES = [
    # --- หมวด A: CORE BROAD SEARCH (เน้นหน่วยงานส่วนกลาง/ภูมิภาค โดยกันท้องถิ่นออกเพื่อความลึก) ---
    f"(\"ขายทอดตลาดพัสดุ\" OR \"ขายทอดตลาดครุภัณฑ์\" OR \"ขายทอดตลาดทรัพย์สิน\" OR \"ขายทอดตลาดวัสดุ\") {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (\"พัสดุชำรุด\" OR \"ครุภัณฑ์ชำรุด\" OR \"พัสดุเสื่อมสภาพ\" OR \"ครุภัณฑ์เสื่อมสภาพ\" OR \"ไม่จำเป็นต้องใช้\") {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",
    f"(\"ประกาศขายทอดตลาด\" OR \"ประมูลขายทอดตลาด\") (\"พัสดุ\" OR \"ครุภัณฑ์\" OR \"ทรัพย์สิน\") {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",
    f"(\"จำหน่ายพัสดุ\" OR \"จำหน่ายครุภัณฑ์\" OR \"ขายพัสดุ\" OR \"ขายครุภัณฑ์\") (\"ชำรุด\" OR \"เสื่อมสภาพ\" OR \"ไม่จำเป็นต้องใช้\") {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",
    f"(\"จำหน่ายพัสดุ\" OR \"จำหน่ายครุภัณฑ์\") (\"วิธีเฉพาะเจาะจง\" OR \"วิธีเจรจาตกลงราคา\" OR \"เฉพาะเจาะจง\" OR \"เจรจาตกลงราคา\") {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",

    # --- หมวด B: LOCAL AGENCIES (เจาะจง อบจ./อบต./เทศบาล โดยเฉพาะ) ---
    f"+\"องค์การบริหารส่วนจังหวัด\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"องค์การบริหารส่วนตำบล\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"เทศบาล\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"อบจ\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"อบต\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",

    # --- หมวด C: REGIONAL PROVINCIAL SEARCH (เจาะจงรายภาค/รายจังหวัด) ---
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_NORTH}) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_NE}) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_CENTRAL}) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_EAST}) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_WEST}) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (พัสดุ OR ครุภัณฑ์) ({PROVINCES_SOUTH}) {GOOGLE_EXCLUDES}",

    # --- หมวด D: SPECIFIC ENTITIES & CATEGORIES (หน่วยงานเจาะจงและหมวดหมู่) ---
    f"+\"สำนักงาน\" +\"จังหวัด\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES} {LOCAL_DOMINANCE_EXCLUDES}",
    f"+\"โรงเรียน\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"โรงพยาบาล\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"มหาวิทยาลัย\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"สำนักงานเขตพื้นที่การศึกษา\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"กรม\" +\"กอง\" +\"สำนัก\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"+\"ศาล\" +\"ศูนย์\" +\"องค์การ\" +\"ขายทอดตลาด\" {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (รถยนต์ OR รถตู้ OR รถบรรทุก OR ยานพาหนะ OR \"ครุภัณฑ์ยานพาหนะ\") {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (อาคาร OR \"สิ่งปลูกสร้าง\" OR รื้อถอน) {GOOGLE_EXCLUDES}",
    f"\"ขายทอดตลาด\" (ครุภัณฑ์ OR เครื่องมือ) (การแพทย์ OR โรงพยาบาล OR สาธารณสุข) {GOOGLE_EXCLUDES}",

    # --- หมวด F: SPECIFIC AUCTION METHODS (หมวดคำศัพท์เฉพาะใหม่) ---
    f"(\"โดยวิธีขายทอดตลาด\" OR \"ขายทอดตลาดพัสดุ\" OR \"ขายทอดตลาดครุภัณฑ์\") -ป.ป.ช. {GOOGLE_EXCLUDES}",
    f"(\"ไม่จำเป็นต้องใช้ในราชการ\" OR \"พัสดุชำรุดเสื่อมสภาพ\") -ป.ป.ช. {GOOGLE_EXCLUDES}",

    # --- หมวด E: SPECIAL DOMAINS (เจาะเป้าหมายตรง) ---
    "\"ขายทอดตลาด\" (site:webportal.bangkok.go.th OR site:coj.go.th)",
    "\"ขายทอดตลาด\" site:prd.go.th",
    "\"ขายทอดตลาด\" site:ac.th"
]

# Filtering Words (Python Level)
NEG_WORDS = [
    "รปภ", "มือสอง", "ทุบตึก", "ตัวแทน", "เช่าซื้อ", "อาคารพาณิชย์", "ขายอาคาร",
    "บังคับคดี", "รอขาย", "ธนาคารยึด", "ที่ดิน", "ธนาคาร", "ไหม",
    "ยึดบ้าน", "วางแนวยึด", "อายัด", "ยึดอายัด", "คู่มือปฏิบัติงาน"
]
NEGATIVE_WORDS = [w for w in NEG_WORDS if w != "อย่างไร"]

# News sites and other noisy domains to filter in Python
NEGATIVE_DOMAINS = [
    "dailynews.co.th", "line.me", "auct.co.th", "mgronline.com", 
    "sia.co.th", "bam.co.th", "threads.net", "naewna.com"
]

HIGHLIGHT_WORDS = [
    "ขายทอดตลาด", "จำหน่าย", "ประกาศขาย", "เสื่อมสภาพ", "ชำรุด", "ไม่จำเป็นต้องใช้งาน",
    "ไม่จำเป็นต้องใช้ในราชการ", "โดยวิธีขายทอดตลาด", "ขายทอดตลาดพัสดุ", 
    "ไม่จำเป็นต้องใช้ในราชการ", "พัสดุชำรุดเสื่อมสภาพ", "ขายทอดตลาดครุภัณฑ์"
]

OUTPUT_DIR = "." if os.getenv("GITHUB_ACTIONS") else "D:/project deep search"

# ==========================================
# FUNCTIONS
# ==========================================

def search_serper(query, tbs):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "tbs": tbs,
        "gl": "th",
        "hl": "th",
        "num": 100
    })
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            return json.loads(res_data).get("organic", [])
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return []

def is_valid_result(url, title, snippet):
    combined_text = f"{title} {snippet}".lower()
    for domain in NEGATIVE_DOMAINS:
        if domain in url.lower(): return False
    for word in NEGATIVE_WORDS:
        if word in combined_text: return False
    
    # Menu pattern check
    sep_count = sum([combined_text.count(sep) for sep in [" · ", " | ", " > ", " - "]])
    if sep_count >= 3: return False

    # Highlight check
    for word in HIGHLIGHT_WORDS:
        if word in title or word in snippet: return True
    return False

def highlight_text(text):
    if not text: return ""
    highlighted = escape(text)
    for word in HIGHLIGHT_WORDS:
        highlighted = re.sub(f"({word})", r"<span class='highlight'>\1</span>", highlighted, flags=re.IGNORECASE)
    return highlighted

def get_ict_now():
    return datetime.utcnow() + timedelta(hours=7)

def load_daily_json(date_str):
    filepath = os.path.join(OUTPUT_DIR, f"result_{date_str}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_daily_json(date_str, results_dict):
    filepath = os.path.join(OUTPUT_DIR, f"result_{date_str}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
    except: pass

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
            body {{ font-family: Arial, sans-serif; background-color: #fff; margin:0; padding:20px 40px; color:#202124; }}
            .container {{ max-width: 652px; margin: 0; }}
            h1 {{ font-size:32px; font-weight:bold; border-bottom:3px solid #1a0dab; padding-bottom:10px; margin-bottom:20px; }}
            .meta {{ font-size:14px; color:#70757a; margin-bottom:25px; border-bottom:1px solid #ebebeb; padding-bottom:15px; }}
            .result-item {{ margin-bottom:28px; padding:10px 14px; border-left:4px solid transparent; border-radius:4px; position:relative; transition: background-color 0.25s, opacity 0.25s; }}
            .result-item.read {{ background-color:#f5f5f5; opacity:0.55; border-left-color:#bdbdbd; }}
            .result-item.read h3 {{ text-decoration:line-through; color:#9e9e9e; }}
            .result-item.read .result-snippet {{ color: #bdbdbd; }}
            .mark-read-btn {{ position:absolute; top:10px; right:10px; border:1.5px solid #bdbdbd; border-radius:50%; width:28px; height:28px; cursor:pointer; color:#bdbdbd; display:flex; align-items:center; justify-content:center; transition: all 0.2s; }}
            .mark-read-btn:hover {{ background-color: #e8f5e9; border-color: #4caf50; color: #4caf50; }}
            .result-item.read .mark-read-btn {{ border-color:#4caf50; color:#4caf50; background-color:#e8f5e9; }}
            .result-top {{ display:flex; align-items:center; margin-bottom:4px; padding-right: 36px; }}
            .result-icon {{ background-color:#f1f3f4; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; margin-right:12px; overflow:hidden; flex-shrink:0; }}
            .result-site-name {{ font-size:14px; color:#202124; text-decoration:none; }}
            .result-url {{ font-size:12px; color:#4d5156; text-decoration:none; word-wrap: break-word; }}
            .result-title h3 {{ font-size:20px; color:#1a0dab; margin:0; font-weight:normal; display: inline; transition: color 0.25s; }}
            .result-title:hover h3 {{ text-decoration: underline; }}
            .result-snippet {{ font-size:14px; line-height:1.58; color:#4d5156; transition: color 0.25s; }}
            .highlight {{ color:#c5221f; font-weight:bold; }}
            .index-badge {{ position:absolute; left:-35px; top:15px; font-size:14px; color:#70757a; font-weight:bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 ผลการค้นหาประจำวันที่ {date}</h1>
            <div class="meta">พบทั้งหมด {count} รายการ <span id="stats"></span></div>
            <div id="results-list">{results_html}</div>
        </div>
        <script>
            const STORAGE_KEY = 'viewedLinks_v2';
            function getViewed() {{ return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }}
            function saveViewed(arr) {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(arr)); }}
            function updateStats() {{
                const total = document.querySelectorAll('.result-item').length;
                const read = document.querySelectorAll('.result-item.read').length;
                document.getElementById('stats').innerText = ` — อ่านแล้ว ${{read}} / ${{total}}`;
            }}

            document.addEventListener('DOMContentLoaded', function() {{
                const viewed = getViewed();
                document.querySelectorAll('.result-item').forEach(it => {{
                    const url = it.dataset.url;
                    if (viewed.includes(url)) it.classList.add('read');

                    it.querySelector('.mark-read-btn').onclick = (e) => {{
                        e.stopPropagation();
                        let v = getViewed();
                        if (it.classList.toggle('read')) {{ if(!v.includes(url)) v.push(url); }}
                        else {{ v = v.filter(u => u !== url); }}
                        saveViewed(v);
                        updateStats();
                    }};

                    it.querySelectorAll('.tracked-link').forEach(link => {{
                        link.onclick = () => {{
                            let v = getViewed();
                            if(!v.includes(url)) {{ v.push(url); saveViewed(v); }}
                            it.classList.add('read');
                            updateStats();
                        }};
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
        title, snippet, url = highlight_text(r.get('title','')), highlight_text(r.get('snippet','')), r.get('link','#')
        domain = urllib.parse.urlparse(url).netloc
        favicon = f"https://s2.googleusercontent.com/s2/favicons?domain={domain}&sz=32"
        f_in, f_at = r.get('_found_in','7d'), r.get('_found_at','N/A')
        badge = f"({f_at}) ภายใน {'24 ชม.' if f_in=='1d' else ('7 วัน' if f_in=='7d' else '1 เดือน')}"

        results_html += f"""
        <div class="result-item" data-url="{escape(url)}">
            <div class="index-badge">{idx}.</div>
            <button class="mark-read-btn">✓</button>
            <div class="result-top">
                <div class="result-icon"><img src="{favicon}" width="16"></div>
                <div class="result-site-info">
                    <a href="{url}" class="result-site-name tracked-link" target="_blank">{domain}</a><br>
                    <a href="{url}" class="result-url tracked-link" target="_blank">{url[:60]}...</a>
                </div>
            </div>
            <a href="{url}" class="result-title tracked-link" style="text-decoration:none" target="_blank"><h3>{title}</h3></a>
            <div class="result-snippet"><span style="color:#70757a">{badge} — </span>{snippet}</div>
        </div>
        """

    date_parts = date_str.split('_')
    display_date = f"{date_parts[0]}/{date_parts[1]}/{date_parts[2]}"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_template.format(date=display_date, count=len(results), results_html=results_html))
    return filepath

def generate_index_html():
    import glob
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "result_*_daily.html")), reverse=True)
    
    links_list = []
    for f in files:
        match = re.search(r"(\d+_\d+_\d+)", f)
        if match:
            date_part = match.group(1).replace("_", "/")
            links_list.append(f'<li><a href="{os.path.basename(f)}" class="report-link">📅 รายงานประจำวันที่ {date_part}</a></li>')
    links = "".join(links_list)
    
    ict_now = get_ict_now()
    updated_at = ict_now.strftime('%d/%m/%Y %H:%M')
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Auction Report Sitemap</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px; display: flex; flex-direction: column; align-items: center; }}
            .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; max-width: 600px; }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 24px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ margin-bottom: 12px; }}
            .report-link {{ display: block; padding: 15px 20px; background-color: #ffffff; border: 1px solid #e1e8ed; border-radius: 8px; text-decoration: none; color: #34495e; font-weight: 500; transition: all 0.3s ease; }}
            .report-link:hover {{ background-color: #3498db; color: white; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .footer {{ margin-top: 30px; color: #7f8c8d; font-size: 14px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 รายการรายงานการค้นหาทั้งหมด</h1>
            <ul>
                {links}
            </ul>
        </div>
        <div class="footer">อัปเดตล่าสุด: {updated_at}</div>
    </body>
    </html>
    """
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_template)

def main():
    ict_now = get_ict_now()
    date_str = ict_now.strftime('%d_%m_%Y')
    all_results = load_daily_json(date_str)
    
    print(f"🚀 Processing {len(QUERIES)} queries with Hybrid-Regional-Agency strategy...")
    for i, raw_q in enumerate(QUERIES):
        q = raw_q.replace('"', '').strip() 
        
        tfs = ["qdr:d", "qdr:w"]
        # Special frequency for stable domains or deep province search (once a month check sometimes catches deep indexes)
        if any(s in raw_q for s in ["webportal.bangkok.go.th", ".prd.go.th", "site:ac.th"]): 
            tfs = ["qdr:m"]

        for tbs in tfs:
            print(f"[{i+1}/{len(QUERIES)}] Querying: {q[:60]}...")
            batch = search_serper(raw_q, tbs) 
            tag = '1d' if tbs == 'qdr:d' else ('7d' if tbs == 'qdr:w' else '1m')
            for r in batch:
                url = r.get('link')
                if url and url not in all_results and is_valid_result(url, r.get('title',''), r.get('snippet','')):
                    r.update({'_found_in': tag, '_found_at': ict_now.strftime('%H:%M')})
                    all_results[url] = r

    save_daily_json(date_str, all_results)
    priority = {'1d': 0, '7d': 1, '1m': 2}
    sorted_list = sorted(all_results.values(), key=lambda x: (priority.get(x.get('_found_in','7d'), 1), x.get('title','')))
    generate_html_report(sorted_list, date_str)
    generate_index_html()
    print(f"✅ Finished. Report generated for {date_str}.")

if __name__ == "__main__": main()
