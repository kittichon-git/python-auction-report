
def is_valid_result(url, title, snippet):
    # เว็บไซต์ที่จะกรองออกในระดับ Python (Sync กับ daily_search.py)
    NEGATIVE_DOMAINS = [
        "dailynews.co.th", "line.me", "auct.co.th", "mgronline.com", 
        "sia.co.th", "bam.co.th", "threads.net", "naewna.com"
    ]
    
    # คำศัพท์ที่จะกรองออก (Sync กับ daily_search.py)
    NEGATIVE_WORDS = [
        "รปภ", "มือสอง", "ทุบตึก", "ตัวแทน", "เช่าซื้อ", "อาคารพาณิชย์", "ขายอาคาร",
        "บังคับคดี", "รอขาย", "ธนาคารยึด", "ที่ดิน", "ธนาคาร", "อย่างไร", "ไหม",
        "ยึดบ้าน", "วางแนวยึด", "อายัด", "ยึดอายัด", "คู่มือปฏิบัติงาน"
    ]
    
    # คำสำคัญที่ต้องมี (Sync กับ daily_search.py)
    HIGHLIGHT_WORDS = [
        "ขายทอดตลาด", "จำหน่าย", "ประกาศขาย", "ครุภัณฑ์", "พัสดุ", "วัสดุ", "รถยนต์", 
        "อาคาร", "รื้อถอน", "เสื่อมสภาพ", "ชำรุด", "ไม่จำเป็นต้องใช้งาน", "อบต", "เทศบาล"
    ]

    combined_text = f"{title} {snippet}".lower()
    
    # 1. ตรวจสอบ Domain ยกลเว้น
    for domain in NEGATIVE_DOMAINS:
        if domain in url.lower():
            return False, f"Negative Domain: {domain}"

    # 2. ตรวจสอบคำยกเว้น
    for word in NEGATIVE_WORDS:
        if word in combined_text:
            return False, f"Negative Word: {word}"
            
    # 3. ตรวจสอบรูปแบบ Menu/Sitemap
    menu_indicators = [" · ", " | ", " > ", " - "]
    separator_count = 0
    for sep in menu_indicators:
        separator_count += combined_text.count(sep)
    if separator_count >= 3:
        return False, "Likely Menu/Sitemap"

    # 4. ต้องมี Keyword สำคัญอย่างน้อย 1 คำ
    has_keyword = False
    for word in HIGHLIGHT_WORDS:
        if word in title or word in snippet:
            has_keyword = True
            break
            
    if not has_keyword:
        return False, "No Keywords Found"
        
    return True, "Valid"

# --- TEST CASES ---
test_cases = [
    {"url": "https://www.nfc.or.th/content/31406", "title": "ประกาศสำนักงานสภาเกษตรกรแห่งชาติ เรื่อง ขายทอดตลาดพัสดุ", "snippet": "3 วันที่ผ่านมา — ประกาศสำนักงานสภาเกษตรกรแห่งชาติ เรื่อง ขายทอดตลาดพัสดุชำรุด..."},
    {"url": "https://muangphan.go.th/news/123", "title": "อบต.เมืองพาน ประกาศขายทอดตลาดครุภัณฑ์ยานพาหนะ", "snippet": "องค์การบริหารส่วนตำบลเมืองพาน แจ้งประกาศขายทอดตลาดรถจักรยานยนต์ชำรุด..."},
    {"url": "https://www.gpf.or.th/announcement/456", "title": "กบข. ประกาศจำหน่ายพัสดุที่ไม่จำเป็นต้องใช้งาน", "snippet": "กองทุนบำเหน็จบำนาญข้าราชการ (กบข.) มีความประสงค์จะจำหน่ายพัสดุเสื่อมสภาพ..."},
    {"url": "https://www.dailynews.co.th/news/789", "title": "ข่าวการขายทอดตลาดวันนี้", "snippet": "เดลินิวส์รายงานข่าวการขายทอดตลาดทรัพย์สิน..."},
    {"url": "https://www.gprocurement.go.th/view", "title": "ประกาศผู้ชนะการเสนอราคาประกอบการขาย", "snippet": "ประกาศผู้ชนะการเสนอราคา (กรณีนี้ควรผ่านถ้าไม่มีคำลบอื่นๆ)..."}
]

print("Testing is_valid_result with NEW HYBRID logic:")
for tc in test_cases:
    valid, reason = is_valid_result(tc["url"], tc["title"], tc["snippet"])
    print(f"[{tc['url'][:20]}...] Valid: {valid}, Reason: {reason}")
