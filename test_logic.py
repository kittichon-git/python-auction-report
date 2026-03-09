
def is_valid_result(url, title, snippet):
    NEGATIVE_WORDS = [
        "รปภ",
        "มือสอง", "ทุบตึก", "ตัวแทน", "เช่าซื้อ", "อาคารพาณิชย์", "ขายอาคาร",
        "บังคับคดี", "รอขาย", "ธนาคารยึด", "ที่ดิน", "ธนาคาร", "อย่างไร", "ไหม",
        "ยึดบ้าน", "วางแนวยึด", "อายัด", "ยึดอายัด", "คู่มือปฏิบัติงาน"
    ]
    NEGATIVE_DOMAINS = [
        "tiktok.com", "youtube.com", "instagram.com", "x.com", "led.go.th", 
        "bidding.pea.co.th", "gprocurement.go.th", "pea.co.th", "egat.go.th",
        "dailynews.co.th", "line.me", "auct.co.th", "mgronline.com", 
        "sia.co.th", "bam.co.th", "threads.net", "naewna.com"
    ]
    HIGHLIGHT_WORDS = [
        "ขายทอดตลาด", "จำหน่าย", "ประกาศขาย", "ครุภัณฑ์", "พัสดุ", "วัสดุ", "รถยนต์", 
        "อาคาร", "รื้อถอน", "เสื่อมสภาพ", "ชำรุด", "ไม่จำเป็นต้องใช้งาน", "อบต", "เทศบาล", "กบข"
    ]
    
    combined_text = f"{title} {snippet}".lower()
    
    for domain in NEGATIVE_DOMAINS:
        if domain in url.lower():
            return False, "Negative Domain"

    for word in NEGATIVE_WORDS:
        if word in combined_text:
            return False, f"Negative Word: {word}"
            
    has_keyword = False
    for word in HIGHLIGHT_WORDS:
        if word in title or word in snippet:
            has_keyword = True
            break
            
    if not has_keyword:
        return False, "No Highlight Keyword"
        
    return True, "Valid"

test_cases = [
    {
        "name": "NFC (สภาเกษตรกร)",
        "url": "https://www.nfc.or.th/content/31406",
        "title": "ประกาศสำนักงานสภาเกษตรกรแห่งชาติ เรื่อง ขายทอดตลาดพัสดุ",
        "snippet": "โทรศัพท์ 0 2142 3901 โทรสาร 0 2143 7608"
    },
    {
        "name": "Muang Phan (อบต.เมืองพาน)",
        "url": "https://www.muangphanlocal.go.th/index",
        "title": "ประกาศองค์การบริหารส่วนตำบลเมืองพาน เรื่อง การจำหน่าย(ขาย) พัสดุครุภัณฑ์ที่ชำรุดเสื่อมสภาพ",
        "snippet": "ประจำปีงบประมาณ 2568 โดยวิธีเฉพาะเจาะจง โดยการเจรจาตกลงราคา · ประกาศ องค์การบริหารส่วนตำบล"
    },
    {
        "name": "GPF (กขบ.)",
        "url": "https://www.gpf.or.th/thai2019/8Purchase/main.php?page=15&lang=th&menu=annouce",
        "title": "การจำหน่ายพัสดุ จำนวน 317 รายการ และการจำหน่ายพัสดุรถยนต์โดยสาร",
        "snippet": "กรณีพัสดุชำรุด เสื่อมสภาพ หรือไม่จำเป็นต้องใช้งาน โดยวิธีขายทอดตลาด"
    }
]

print("Testing is_valid_result with current logic:")
for tc in test_cases:
    valid, reason = is_valid_result(tc["url"], tc["title"], tc["snippet"])
    print(f"[{tc['name']}] Valid: {valid}, Reason: {reason}")
