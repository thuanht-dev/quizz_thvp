# -*- coding: utf-8 -*-
"""Build mixed review question pool from existing bank + new exam-style items."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
data = json.load(open(HERE / "quiz-data.json", encoding="utf-8"))

# Topic tags used for balanced sampling
# basics | files | security | office

TOPIC_RULES = [
    (
        "basics",
        re.compile(
            r"CPU|RAM|ROM|phần cứng|phần mềm|hệ điều hành|Windows|"
            r"thiết bị nhập|thiết bị xuất|bit\b|byte|KB|MB|GB|TB|"
            r"LAN|WAN|Internet|WWW|World Wide Web|trình duyệt|URL|HTTP|"
            r"Personal Computer|\bPC\b|máy tính|ổ cứng|USB|bàn phím|chuột|"
            r"màn hình|máy in|smartphone|máy tính bảng|Desktop|Taskbar|"
            r"Control Panel|Start Menu|biểu tượng|icon",
            re.I,
        ),
        {1, 2, 6},
    ),
    (
        "files",
        re.compile(
            r"thư mục|tệp tin|tập tin|\bfile\b|Recycle|thùng rác|"
            r"sao chép|di chuyển|đổi tên|xóa|tìm kiếm|Explorer|"
            r"Ctrl\s*\+\s*C|Ctrl\s*\+\s*V|Ctrl\s*\+\s*X|Ctrl\s*\+\s*A|"
            r"Cut|Copy|Paste|Rename|Delete|Folder",
            re.I,
        ),
        {2},
    ),
    (
        "security",
        re.compile(
            r"virus|malware|phishing|bảo mật|mật khẩu|an toàn|tường lửa|"
            r"firewall|spam|trojan|worm|antivirus|mã độc|lừa đảo|"
            r"HTTPS|giả mạo|bản quyền|sao lưu|backup",
            re.I,
        ),
        {1, 2, 6},
    ),
    (
        "office",
        re.compile(
            r"\bWord\b|Excel|PowerPoint|văn bản|bảng tính|slide|trình chiếu|"
            r"Ribbon|công thức|hàm SUM|biểu đồ|định dạng|font|in đậm|"
            r"Mail Merge|Transition|Animation|worksheet|ô tính",
            re.I,
        ),
        {3, 4, 5},
    ),
]


def blob(q):
    return q["text"] + " " + " ".join(q["options"].values())


def clone_q(mod_id, q, topic):
    return {
        "src": f"m{mod_id}-q{q['id']}",
        "topic": topic,
        "text": q["text"],
        "options": dict(q["options"]),
        "answer": q["answer"],
        "explain": q.get("explain", ""),
        "detail": q.get("detail", ""),
        "icon": q.get("icon", "💡"),
    }


# ---- Collect from existing bank ----
picked = {t: [] for t, *_ in TOPIC_RULES}
seen_text = set()

for topic, pat, mods in TOPIC_RULES:
    for m in data["modules"]:
        if m["id"] not in mods:
            continue
        for q in m["questions"]:
            t = q["text"].strip()
            if t in seen_text:
                continue
            if not pat.search(blob(q)):
                continue
            # Prefer overview / conceptual over ultra-specific deep Office tricks
            item = clone_q(m["id"], q, topic)
            picked[topic].append(item)
            seen_text.add(t)

# Cap per topic from bank (keep variety)
CAPS = {"basics": 50, "files": 35, "security": 35, "office": 50}
rng = random.Random(42)
for topic, cap in CAPS.items():
    items = picked[topic]
    if len(items) > cap:
        rng.shuffle(items)
        picked[topic] = items[:cap]

# ---- New exam-style questions ----
NEW = [
    # BASICS
    {
        "topic": "basics",
        "icon": "🧠",
        "text": "Bộ xử lý trung tâm (CPU) có chức năng chính nào?",
        "options": {
            "A": "Lưu trữ lâu dài toàn bộ dữ liệu người dùng",
            "B": "Thực hiện các phép tính và điều khiển hoạt động của máy tính",
            "C": "Kết nối máy tính với mạng Internet",
            "D": "Hiển thị hình ảnh lên màn hình",
        },
        "answer": "B",
        "explain": "CPU là “bộ não” của máy: xử lý lệnh và điều khiển các bộ phận khác làm việc.",
        "detail": "CPU (Central Processing Unit) thực hiện phép tính số học/logic và điều khiển. RAM lưu tạm khi máy đang chạy; ổ cứng/SSD lưu lâu dài; màn hình chỉ xuất hình ảnh.",
    },
    {
        "topic": "basics",
        "icon": "💾",
        "text": "Đặc điểm đúng của bộ nhớ RAM là:",
        "options": {
            "A": "Lưu dữ liệu vĩnh viễn ngay cả khi tắt máy",
            "B": "Chỉ dùng để lưu chương trình hệ điều hành",
            "C": "Lưu tạm dữ liệu đang làm việc; mất dữ liệu khi mất điện",
            "D": "Không ảnh hưởng tốc độ máy tính",
        },
        "answer": "C",
        "explain": "RAM là bộ nhớ tạm: máy đang chạy thì dùng, tắt máy là mất nội dung chưa lưu.",
        "detail": "RAM (Random Access Memory) giúp mở nhiều chương trình nhanh. Dữ liệu quan trọng phải lưu ra ổ cứng/SSD hoặc đám mây. ROM giữ firmware khởi động, không thay thế RAM.",
    },
    {
        "topic": "basics",
        "icon": "📀",
        "text": "ROM thường dùng để:",
        "options": {
            "A": "Lưu file ảnh, video của người dùng",
            "B": "Lưu chương trình khởi động/firmware cần thiết khi bật máy",
            "C": "Thay thế hoàn toàn ổ cứng",
            "D": "Kết nối máy in qua USB",
        },
        "answer": "B",
        "explain": "ROM chứa chương trình “cứng” để máy khởi động, không phải nơi lưu tài liệu của bạn.",
        "detail": "ROM (Read-Only Memory) thường chứa BIOS/UEFI. Người dùng hầu như không ghi đè như ghi file vào Documents. Tài liệu cá nhân lưu trên ổ cứng/SSD, USB, cloud.",
    },
    {
        "topic": "basics",
        "icon": "⌨️",
        "text": "Thiết bị nào thuộc nhóm thiết bị nhập (input)?",
        "options": {
            "A": "Máy in",
            "B": "Loa",
            "C": "Bàn phím",
            "D": "Máy chiếu",
        },
        "answer": "C",
        "explain": "Bàn phím đưa dữ liệu vào máy; máy in, loa, máy chiếu đưa thông tin ra ngoài.",
        "detail": "Thiết bị nhập: bàn phím, chuột, mic, scanner, cảm ứng. Thiết bị xuất: màn hình, loa, máy in, máy chiếu. Một số thiết bị vừa nhập vừa xuất (màn hình cảm ứng).",
    },
    {
        "topic": "basics",
        "icon": "🖨️",
        "text": "Thiết bị nào là thiết bị xuất (output)?",
        "options": {
            "A": "Chuột",
            "B": "Máy quét (scanner)",
            "C": "Micro",
            "D": "Máy in",
        },
        "answer": "D",
        "explain": "Máy in đưa kết quả từ máy ra giấy — thuộc thiết bị xuất.",
        "detail": "Chuột, scanner, micro là thiết bị nhập. Phân biệt đúng input/output là kiến thức nền thường gặp trong đề CNTT cơ bản.",
    },
    {
        "topic": "basics",
        "icon": "🪟",
        "text": "Hệ điều hành (Operating System) có vai trò nào sau đây?",
        "options": {
            "A": "Chỉ dùng để soạn thảo văn bản",
            "B": "Quản lý phần cứng và tạo môi trường chạy phần mềm ứng dụng",
            "C": "Chỉ kết nối mạng LAN",
            "D": "Thay thế hoàn toàn phần cứng",
        },
        "answer": "B",
        "explain": "Hệ điều hành điều khiển phần cứng và cho phép Word, Excel, trình duyệt… chạy được.",
        "detail": "Ví dụ: Windows, macOS, Linux, Android. Không có OS thì người dùng khó tương tác với máy. Phần mềm ứng dụng (Word, Chrome) chạy trên OS, không thay thế OS.",
    },
    {
        "topic": "basics",
        "icon": "📦",
        "text": "Phần mềm ứng dụng khác hệ điều hành ở điểm nào?",
        "options": {
            "A": "Ứng dụng phục vụ công việc cụ thể; hệ điều hành quản lý máy và môi trường chạy",
            "B": "Ứng dụng luôn được cài sẵn trong ROM",
            "C": "Hệ điều hành chỉ dùng để chơi game",
            "D": "Không có sự khác biệt",
        },
        "answer": "A",
        "explain": "Word/Excel là ứng dụng làm việc; Windows là hệ điều hành “nền” để các ứng dụng chạy.",
        "detail": "Phần mềm hệ thống (OS, trình điều khiển) quản lý tài nguyên. Phần mềm ứng dụng giải quyết nhu cầu người dùng: văn phòng, học tập, giải trí.",
    },
    {
        "topic": "basics",
        "icon": "🔢",
        "text": "Đơn vị nhỏ nhất để đo thông tin trong máy tính là:",
        "options": {
            "A": "Byte",
            "B": "Bit",
            "C": "Kilobyte",
            "D": "Megabyte",
        },
        "answer": "B",
        "explain": "Bit là đơn vị nhỏ nhất (0 hoặc 1). 8 bit = 1 byte.",
        "detail": "Thứ tự thường gặp: bit → Byte → KB → MB → GB → TB. Đề thi hay hỏi quan hệ 1 Byte = 8 bit và đơn vị nhỏ nhất là bit.",
    },
    {
        "topic": "basics",
        "icon": "📐",
        "text": "1 Byte bằng bao nhiêu bit?",
        "options": {
            "A": "2 bit",
            "B": "4 bit",
            "C": "8 bit",
            "D": "16 bit",
        },
        "answer": "C",
        "explain": "Quy ước chuẩn: 1 Byte = 8 bit.",
        "detail": "Một ký tự ASCII cơ bản thường chiếm 1 byte. Đây là câu hỏi đo lường thông tin rất phổ biến trong đề trắc nghiệm CNTT cơ bản.",
    },
    {
        "topic": "basics",
        "icon": "🌐",
        "text": "LAN và WAN khác nhau chủ yếu ở phạm vi địa lý:",
        "options": {
            "A": "LAN rộng toàn cầu, WAN chỉ trong một phòng",
            "B": "LAN thường trong phạm vi hẹp (nhà/cơ quan); WAN kết nối trên phạm vi rộng",
            "C": "LAN chỉ dùng Wi-Fi, WAN chỉ dùng cáp quang",
            "D": "LAN và WAN là cùng một loại mạng",
        },
        "answer": "B",
        "explain": "LAN là mạng cục bộ; WAN phủ vùng rộng, Internet là ví dụ WAN quy mô lớn.",
        "detail": "LAN (Local Area Network): nhà, lớp học, văn phòng. WAN (Wide Area Network): kết nối nhiều khu vực. Internet là mạng của các mạng trên toàn cầu.",
    },
    {
        "topic": "basics",
        "icon": "🌍",
        "text": "World Wide Web (WWW) là gì?",
        "options": {
            "A": "Một loại phần cứng mạng",
            "B": "Hệ thống tài nguyên siêu văn bản trên Internet, truy cập bằng trình duyệt",
            "C": "Tên gọi khác của hệ điều hành Windows",
            "D": "Phần mềm diệt virus",
        },
        "answer": "B",
        "explain": "WWW là dịch vụ web trên Internet (trang web, liên kết); Internet rộng hơn, gồm nhiều dịch vụ khác.",
        "detail": "Internet là hạ tầng mạng toàn cầu. WWW dùng giao thức HTTP/HTTPS và trình duyệt (Chrome, Edge…). Email, chat cũng chạy trên Internet nhưng không đồng nghĩa với WWW.",
    },
    {
        "topic": "basics",
        "icon": "🧭",
        "text": "Trình duyệt web (web browser) dùng để:",
        "options": {
            "A": "Soạn thảo bảng tính",
            "B": "Truy cập và hiển thị trang web trên Internet",
            "C": "Quản lý tệp trên ổ cứng thay File Explorer",
            "D": "Cài đặt hệ điều hành",
        },
        "answer": "B",
        "explain": "Trình duyệt (Chrome, Edge, Firefox…) mở trang web và dịch vụ trực tuyến.",
        "detail": "Nhập URL hoặc tìm kiếm để truy cập. Trình duyệt không thay Word/Excel, cũng không phải hệ điều hành.",
    },
    {
        "topic": "basics",
        "icon": "🖥️",
        "text": "Trong Windows, thanh Taskbar (thanh tác vụ) thường dùng để:",
        "options": {
            "A": "Chỉ hiển thị hình nền",
            "B": "Mở Start, chuyển nhanh giữa các cửa sổ đang chạy, xem khay hệ thống",
            "C": "Xóa vĩnh viễn mọi tệp",
            "D": "Thay thế BIOS",
        },
        "answer": "B",
        "explain": "Taskbar giúp mở menu Start, chuyển cửa sổ và xem giờ/mạng/âm lượng.",
        "detail": "Nằm thường ở cạnh dưới màn hình. Click biểu tượng để chuyển ứng dụng; khay hệ thống (system tray) hiện trạng thái mạng, pin, âm thanh.",
    },
    {
        "topic": "basics",
        "icon": "⚙️",
        "text": "Control Panel / Settings trong Windows chủ yếu dùng để:",
        "options": {
            "A": "Soạn thảo slide thuyết trình",
            "B": "Cấu hình máy: mạng, âm thanh, thiết bị, tài khoản, cập nhật…",
            "C": "Chỉ đổi hình nền",
            "D": "Tạo công thức Excel",
        },
        "answer": "B",
        "explain": "Đây là nơi chỉnh thông số hệ thống, không phải phần mềm văn phòng.",
        "detail": "Có thể đổi mật khẩu, kết nối Wi-Fi, gỡ ứng dụng, cập nhật Windows. Word/Excel dùng để làm tài liệu, không thay vai trò Settings.",
    },
    # FILES
    {
        "topic": "files",
        "icon": "📁",
        "text": "Cách nhanh để tạo thư mục mới trong File Explorer là:",
        "options": {
            "A": "Ctrl + Shift + N",
            "B": "Ctrl + S",
            "C": "Alt + F4",
            "D": "Ctrl + P",
        },
        "answer": "A",
        "explain": "Trong cửa sổ thư mục, Ctrl + Shift + N tạo folder mới.",
        "detail": "Ctrl + S thường là Lưu; Alt + F4 đóng cửa sổ; Ctrl + P in. Cũng có thể chuột phải → New → Folder.",
    },
    {
        "topic": "files",
        "icon": "✏️",
        "text": "Phím tắt thường dùng để đổi tên tệp/thư mục đang chọn trong Windows là:",
        "options": {
            "A": "F2",
            "B": "F5",
            "C": "F1",
            "D": "F12",
        },
        "answer": "A",
        "explain": "Chọn mục rồi nhấn F2 để đổi tên.",
        "detail": "F5 làm mới cửa sổ; F1 trợ giúp; F12 trong Office thường là Save As. Chuột phải → Rename cũng được.",
    },
    {
        "topic": "files",
        "icon": "📋",
        "text": "Sau khi Cut (Ctrl + X) một tệp, thao tác Paste (Ctrl + V) sẽ:",
        "options": {
            "A": "Tạo bản sao và giữ nguyên tệp ở vị trí cũ",
            "B": "Di chuyển tệp sang vị trí mới",
            "C": "Xóa vĩnh viễn tệp",
            "D": "Nén tệp thành ZIP",
        },
        "answer": "B",
        "explain": "Cut + Paste là di chuyển; Copy + Paste mới là sao chép.",
        "detail": "Ctrl + C sao chép (giữ bản gốc). Ctrl + X cắt (bản gốc sẽ mất ở chỗ cũ sau khi dán). Kéo thả giữ Shift cũng thường là di chuyển trong cùng ổ.",
    },
    {
        "topic": "files",
        "icon": "📄",
        "text": "Muốn giữ nguyên tệp gốc và tạo thêm bản ở thư mục khác, nên dùng:",
        "options": {
            "A": "Cut rồi Paste",
            "B": "Copy rồi Paste",
            "C": "Delete rồi Restore",
            "D": "Rename rồi Empty Recycle Bin",
        },
        "answer": "B",
        "explain": "Copy + Paste tạo bản sao; Cut + Paste là chuyển chỗ.",
        "detail": "Phím tắt: Ctrl + C rồi Ctrl + V. Rất hay dùng khi nộp bài: giữ bản làm việc, nộp bản copy vào thư mục theo yêu cầu đề thi.",
    },
    {
        "topic": "files",
        "icon": "🗑️",
        "text": "Khi xóa tệp bằng phím Delete (không giữ Shift), tệp thường:",
        "options": {
            "A": "Bị xóa vĩnh viễn ngay lập tức",
            "B": "Được đưa vào Recycle Bin (Thùng rác)",
            "C": "Tự gửi qua email",
            "D": "Được mã hóa bằng virus",
        },
        "answer": "B",
        "explain": "Delete thường đưa vào Thùng rác; còn có thể khôi phục nếu chưa Empty.",
        "detail": "Shift + Delete thường xóa thẳng, khó khôi phục. Trong đề thi/thực hành Windows, cần phân biệt Delete và Shift + Delete.",
    },
    {
        "topic": "files",
        "icon": "♻️",
        "text": "Recycle Bin dùng để:",
        "options": {
            "A": "Cài đặt Windows Update",
            "B": "Lưu tạm các mục đã xóa để có thể khôi phục",
            "C": "Tăng tốc CPU",
            "D": "Quản lý mật khẩu Wi-Fi",
        },
        "answer": "B",
        "explain": "Thùng rác giữ tệp đã xóa; Restore để lấy lại, Empty để xóa hẳn.",
        "detail": "Empty Recycle Bin sẽ xóa vĩnh viễn các mục trong thùng rác. Không dùng Recycle Bin để sao lưu dài hạn.",
    },
    {
        "topic": "files",
        "icon": "🔎",
        "text": "Trong ô Search của File Explorer, gõ `*.docx` thường để:",
        "options": {
            "A": "Tìm mọi tệp Word có phần mở rộng .docx",
            "B": "Xóa toàn bộ tệp Word",
            "C": "Đổi tên hàng loạt thành .docx",
            "D": "Cài Microsoft Word",
        },
        "answer": "A",
        "explain": "Dấu * là ký tự đại diện: `*.docx` = mọi tên file kết thúc bằng .docx.",
        "detail": "Ví dụ khác: `bao_cao*` tìm tên bắt đầu bằng bao_cao. Đây là kỹ năng tìm kiếm tệp thường gặp trong phần Windows của đề thực hành/trắc nghiệm.",
    },
    {
        "topic": "files",
        "icon": "🗂️",
        "text": "Thư mục (folder) khác tệp (file) ở chỗ:",
        "options": {
            "A": "Thư mục dùng để chứa và tổ chức tệp/thư mục con; tệp là đơn vị dữ liệu cụ thể",
            "B": "Thư mục luôn có phần mở rộng .exe",
            "C": "Tệp không thể đổi tên",
            "D": "Thư mục chỉ tồn tại trên Internet",
        },
        "answer": "A",
        "explain": "Folder như ngăn tủ; file như tài liệu nằm trong ngăn tủ đó.",
        "detail": "Ví dụ: thư mục BaiThi chứa BaiWord.docx, BaiExcel.xlsx. Tổ chức thư mục rõ ràng giúp tìm và nộp bài đúng yêu cầu.",
    },
    # SECURITY
    {
        "topic": "security",
        "icon": "🦠",
        "text": "Virus máy tính là:",
        "options": {
            "A": "Phần cứng bị nóng",
            "B": "Chương trình độc hại có thể tự lây lan và gây hại dữ liệu/hệ thống",
            "C": "Một loại trình duyệt web",
            "D": "Cập nhật Windows chính thức",
        },
        "answer": "B",
        "explain": "Virus là phần mềm độc hại, có thể nhân bản và phá dữ liệu hoặc làm chậm máy.",
        "detail": "Malware là khái niệm rộng hơn (virus, worm, trojan, ransomware…). Cần phần mềm diệt virus, cập nhật hệ thống và thói quen an toàn khi tải file/mở email.",
    },
    {
        "topic": "security",
        "icon": "🎣",
        "text": "Phishing (lừa đảo trực tuyến) thường nhằm mục đích:",
        "options": {
            "A": "Tăng tốc độ RAM",
            "B": "Lừa người dùng cung cấp mật khẩu, OTP, thông tin thẻ…",
            "C": "Sao lưu dữ liệu tự động",
            "D": "Cài driver máy in",
        },
        "answer": "B",
        "explain": "Phishing giả danh ngân hàng/cơ quan để đánh cắp thông tin đăng nhập hoặc tiền.",
        "detail": "Dấu hiệu: email/SMS link lạ,催 gấp, sai tên miền (ví dụ ngânhang-secure.ru). Không nhập mật khẩu trên trang không chắc chắn; kiểm tra địa chỉ HTTPS và tên miền chính chủ.",
    },
    {
        "topic": "security",
        "icon": "🔒",
        "text": "Cách tạo mật khẩu mạnh hơn là:",
        "options": {
            "A": "Dùng ngày sinh và tên mình cho dễ nhớ",
            "B": "Dùng một mật khẩu ngắn cho mọi tài khoản",
            "C": "Dài, khó đoán, kết hợp chữ hoa/thường, số, ký tự đặc biệt; mỗi tài khoản một mật khẩu",
            "D": "Gửi mật khẩu cho bạn bè giữ hộ",
        },
        "answer": "C",
        "explain": "Mật khẩu mạnh phải khó đoán và không dùng chung mọi nơi.",
        "detail": "Nên bật xác thực hai yếu tố (2FA) nếu có. Không lưu mật khẩu trên giấy dán màn hình. Tránh mật khẩu kiểu 123456, password.",
    },
    {
        "topic": "security",
        "icon": "🛡️",
        "text": "Biện pháp nào giúp bảo vệ máy/Internet an toàn hơn?",
        "options": {
            "A": "Tắt hoàn toàn cập nhật Windows mãi mãi",
            "B": "Cài phần mềm crack từ diễn đàn lạ",
            "C": "Cập nhật hệ thống, dùng antivirus, không mở tệp đính kèm đáng ngờ",
            "D": "Chia sẻ mật khẩu Wi-Fi công khai trên mạng xã hội",
        },
        "answer": "C",
        "explain": "Cập nhật + antivirus + thận trọng với file/email lạ là bộ ba bảo vệ cơ bản.",
        "detail": "Tường lửa (firewall) cũng hỗ trợ chặn kết nối nguy hiểm. Phần mềm crack/keygen là nguồn malware phổ biến.",
    },
    {
        "topic": "security",
        "icon": "📧",
        "text": "Nhận email báo “trúng thưởng”, yêu cầu bấm link và nhập mật khẩu ngân hàng. Cách xử lý đúng là:",
        "options": {
            "A": "Bấm link ngay để nhận thưởng",
            "B": "Chuyển tiếp cho nhiều người cùng làm",
            "C": "Không bấm link; kiểm tra/báo cáo là thư lừa đảo; liên hệ kênh chính thức nếu cần",
            "D": "Trả lời email bằng số CMND",
        },
        "answer": "C",
        "explain": "Đây là tình huống phishing điển hình — không cung cấp thông tin qua link lạ.",
        "detail": "Ngân hàng/cơ quan uy tín không đòi mật khẩu qua email. Có thể đánh dấu Spam/Phishing và xóa. Nếu đã lộ thông tin, đổi mật khẩu và liên hệ ngân hàng.",
    },
    {
        "topic": "security",
        "icon": "💾",
        "text": "Sao lưu (backup) dữ liệu quan trọng giúp:",
        "options": {
            "A": "Máy chạy nhanh gấp đôi CPU",
            "B": "Khôi phục khi máy hỏng, mất file hoặc dính ransomware",
            "C": "Thay thế antivirus hoàn toàn",
            "D": "Tăng dung lượng RAM vật lý",
        },
        "answer": "B",
        "explain": "Backup là bản dự phòng để lấy lại dữ liệu khi sự cố.",
        "detail": "Có thể copy ra USB/ổ ngoài hoặc dùng cloud. Nguyên tắc 3-2-1 thường gặp: 3 bản, 2 loại thiết bị, 1 bản offsite.",
    },
    {
        "topic": "security",
        "icon": "🔐",
        "text": "Khi dùng máy công cộng, nên:",
        "options": {
            "A": "Lưu mật khẩu trình duyệt và không đăng xuất",
            "B": "Đăng xuất tài khoản, không lưu mật khẩu, chú ý người xung quanh",
            "C": "Tắt antivirus để máy nhẹ hơn",
            "D": "Cài phần mềm lạ theo yêu cầu người ngồi cạnh",
        },
        "answer": "B",
        "explain": "Máy công cộng dễ bị lộ tài khoản nếu quên đăng xuất hoặc lưu mật khẩu.",
        "detail": "Ưu tiên xác thực 2 bước. Tránh thanh toán/nhập OTP trên máy không tin cậy nếu không cần thiết.",
    },
    {
        "topic": "security",
        "icon": "🧱",
        "text": "Tường lửa (firewall) có tác dụng chính:",
        "options": {
            "A": "Tăng dung lượng ổ cứng",
            "B": "Kiểm soát kết nối mạng ra/vào, giảm nguy cơ truy cập trái phép",
            "C": "Soạn thảo văn bản tự động",
            "D": "Thay thế hoàn toàn mật khẩu",
        },
        "answer": "B",
        "explain": "Firewall lọc lưu lượng mạng, giúp chặn kết nối đáng ngờ.",
        "detail": "Windows có tường lửa tích hợp. Firewall không thay antivirus 100%, cũng không bảo vệ nếu bạn tự nhập mật khẩu trên trang giả mạo.",
    },
    {
        "topic": "security",
        "icon": "📎",
        "text": "Tệp đính kèm email lạ có phần mở rộng .exe hoặc .bat thì nên:",
        "options": {
            "A": "Mở ngay để xem nội dung",
            "B": "Tắt máy rồi mở",
            "C": "Không mở; đây có thể là phần mềm độc hại",
            "D": "Đổi tên thành .docx rồi mở",
        },
        "answer": "C",
        "explain": "File thực thi từ người lạ là đường lây malware rất phổ biến.",
        "detail": "Chỉ mở đính kèm khi biết rõ người gửi và đúng ngữ cảnh. Khi nghi ngờ, hỏi lại qua kênh khác (gọi điện, chat nội bộ).",
    },
    {
        "topic": "security",
        "icon": "🔑",
        "text": "HTTPS trên thanh địa chỉ trình duyệt thường cho thấy:",
        "options": {
            "A": "Trang web dùng kết nối mã hóa, an toàn hơn HTTP thường",
            "B": "Trang web chắc chắn không bao giờ lừa đảo",
            "C": "Máy tính đã hết virus",
            "D": "Tốc độ mạng luôn đạt 1 Gbps",
        },
        "answer": "A",
        "explain": "HTTPS mã hóa dữ liệu truyền tải; vẫn phải kiểm tra đúng tên miền chính chủ.",
        "detail": "Trang giả mạo cũng có thể có HTTPS. Cần xem kỹ domain (ví dụ vietcombank.com.vn chứ không phải vietcombank-login.xyz).",
    },
    {
        "topic": "security",
        "icon": "👤",
        "text": "Biện pháp bảo vệ thông tin cá nhân trên mạng xã hội phù hợp là:",
        "options": {
            "A": "Công khai số CMND, địa chỉ nhà và ảnh thẻ ngân hàng",
            "B": "Giới hạn đối tượng xem, không chia sẻ dữ liệu nhạy cảm, kiểm tra quyền riêng tư",
            "C": "Dùng chung một mật khẩu với mọi nền tảng",
            "D": "Chấp nhận mọi lời kết bạn để tăng follow",
        },
        "answer": "B",
        "explain": "Hạn chế lộ dữ liệu cá nhân và chỉnh quyền riêng tư giúp giảm rủi ro bị lợi dụng.",
        "detail": "Không đăng OTP, mật khẩu, ảnh giấy tờ tùy thân. Cảnh giác tin nhắn lạ xin tiền/mượn tài khoản.",
    },
    {
        "topic": "security",
        "icon": "💣",
        "text": "Malware là thuật ngữ chỉ:",
        "options": {
            "A": "Mọi phần mềm Microsoft Office",
            "B": "Phần mềm độc hại nói chung (virus, trojan, ransomware…)",
            "C": "Chỉ các bản cập nhật Windows",
            "D": "Cáp HDMI",
        },
        "answer": "B",
        "explain": "Malware = malicious software: nhóm phần mềm gây hại.",
        "detail": "Virus là một dạng malware. Ransomware mã hóa dữ liệu đòi tiền chuộc. Phòng bằng cập nhật, antivirus, backup và thói quen an toàn.",
    },
    {
        "topic": "security",
        "icon": "🕵️",
        "text": "Phần mềm diệt virus (antivirus) giúp:",
        "options": {
            "A": "Phát hiện/ngăn chặn nhiều loại mã độc; cần cập nhật mẫu nhận diện",
            "B": "Thay thế hoàn toàn việc tạo mật khẩu mạnh",
            "C": "Tự sửa mọi lỗi ngữ pháp trong Word",
            "D": "Tăng số lõi CPU vật lý",
        },
        "answer": "A",
        "explain": "Antivirus quét và cảnh báo mã độc, nhưng vẫn cần thao tác an toàn của người dùng.",
        "detail": "Nên bật cập nhật tự động. Không tắt antivirus để cài crack. Windows Security là lớp bảo vệ cơ bản sẵn có trên nhiều máy.",
    },
    # OFFICE OVERVIEW
    {
        "topic": "office",
        "icon": "📘",
        "text": "Microsoft Word chủ yếu dùng để:",
        "options": {
            "A": "Soạn thảo và định dạng văn bản (đơn, báo cáo, CV…)",
            "B": "Tính toán thống kê lớn như phần mềm kế toán chuyên sâu",
            "C": "Quản trị hệ thống mạng LAN",
            "D": "Thiết kế chip CPU",
        },
        "answer": "A",
        "explain": "Word là phần mềm xử lý văn bản: gõ, định dạng, chèn bảng/ảnh, in ấn.",
        "detail": "Excel mạnh về bảng tính/tính toán; PowerPoint mạnh về trình chiếu. Nhầm chức năng ba phần mềm là lỗi thường gặp khi mới học.",
    },
    {
        "topic": "office",
        "icon": "📗",
        "text": "Microsoft Excel phù hợp nhất với công việc nào?",
        "options": {
            "A": "Viết tiểu thuyết dài nhiều chương",
            "B": "Lập bảng số liệu, tính toán bằng công thức/hàm, vẽ biểu đồ",
            "C": "Chỉ chiếu phim",
            "D": "Cài driver card đồ họa",
        },
        "answer": "B",
        "explain": "Excel là bảng tính: ô, công thức, hàm, biểu đồ phục vụ số liệu.",
        "detail": "Ví dụ: bảng điểm, bảng lương, thống kê doanh thu. Văn bản thuần túy dài nên dùng Word; bài thuyết trình dùng PowerPoint.",
    },
    {
        "topic": "office",
        "icon": "📙",
        "text": "Microsoft PowerPoint dùng chủ yếu để:",
        "options": {
            "A": "Tạo bài trình chiếu (slide) hỗ trợ thuyết trình",
            "B": "Quản lý Recycle Bin",
            "C": "Biên dịch hệ điều hành",
            "D": "Đo tốc độ Internet",
        },
        "answer": "A",
        "explain": "PowerPoint tạo slide, thêm nội dung/ảnh/biểu đồ và trình chiếu.",
        "detail": "Có thể thêm Transition (chuyển slide) và Animation (hiệu ứng đối tượng). Không thay Word để soạn văn bản dài hay Excel để tính bảng phức tạp.",
    },
    {
        "topic": "office",
        "icon": "🎀",
        "text": "Ribbon trong Word/Excel/PowerPoint là:",
        "options": {
            "A": "Thanh công cụ gồm các tab (Home, Insert…) chứa nhóm lệnh",
            "B": "Tên của thùng rác Windows",
            "C": "Một loại virus macro",
            "D": "Cáp mạng LAN",
        },
        "answer": "A",
        "explain": "Ribbon là dải lệnh trên cùng: chọn tab rồi bấm nhóm công cụ cần dùng.",
        "detail": "Ví dụ Word: tab Home (font, đậm/nghiêng), Insert (bảng, ảnh). Hiểu Ribbon giúp tìm đúng lệnh khi làm bài thực hành Office.",
    },
    {
        "topic": "office",
        "icon": "🅱️",
        "text": "Trong Word, tổ hợp phím Ctrl + B thường dùng để:",
        "options": {
            "A": "Lưu tệp",
            "B": "In đậm (Bold) văn bản đang chọn",
            "C": "Mở trình chiếu",
            "D": "Chèn biểu đồ",
        },
        "answer": "B",
        "explain": "Ctrl + B bật/tắt in đậm cho chữ đang chọn.",
        "detail": "Ctrl + I nghiêng, Ctrl + U gạch chân, Ctrl + S lưu. Các phím tắt định dạng này rất hay gặp trong ôn Word cơ bản.",
    },
    {
        "topic": "office",
        "icon": "🧮",
        "text": "Trong Excel, công thức luôn bắt đầu bằng ký tự nào?",
        "options": {
            "A": "#",
            "B": "=",
            "C": "@",
            "D": "*",
        },
        "answer": "B",
        "explain": "Mọi công thức/hàm Excel bắt đầu bằng dấu =, ví dụ =A1+B1 hoặc =SUM(A1:A10).",
        "detail": "Nếu không có dấu =, Excel thường hiểu là văn bản. Lỗi ##### thường do cột hẹp, khác với lỗi công thức như #DIV/0!.",
    },
    {
        "topic": "office",
        "icon": "Σ",
        "text": "Hàm SUM trong Excel dùng để:",
        "options": {
            "A": "Đếm số ô chứa chữ",
            "B": "Tính tổng các giá trị số trong vùng chọn",
            "C": "Sắp xếp chữ cái A→Z",
            "D": "Chèn ảnh vào ô",
        },
        "answer": "B",
        "explain": "SUM cộng các số, ví dụ =SUM(B2:B10).",
        "detail": "COUNT đếm ô số; COUNTA đếm ô không trống; AVERAGE tính trung bình. Nhầm SUM với AVERAGE/COUNT là lỗi phổ biến.",
    },
    {
        "topic": "office",
        "icon": "▶️",
        "text": "Trong PowerPoint, phím F5 thường dùng để:",
        "options": {
            "A": "Lưu bài trình chiếu",
            "B": "Bắt đầu trình chiếu từ đầu",
            "C": "Xóa slide hiện tại",
            "D": "Chèn bảng Excel",
        },
        "answer": "B",
        "explain": "F5 chiếu từ slide đầu; Shift + F5 chiếu từ slide đang chọn.",
        "detail": "Có thể vào tab Slide Show → From Beginning. Esc để thoát chế độ trình chiếu.",
    },
    {
        "topic": "office",
        "icon": "✨",
        "text": "Trong PowerPoint, Transition khác Animation ở chỗ:",
        "options": {
            "A": "Transition là hiệu ứng chuyển giữa các slide; Animation là hiệu ứng cho đối tượng trên slide",
            "B": "Hai khái niệm hoàn toàn giống nhau",
            "C": "Animation chỉ dùng khi in handout",
            "D": "Transition chỉ áp dụng cho hình ảnh trong Word",
        },
        "answer": "A",
        "explain": "Chuyển slide dùng Transition; chữ/ảnh bay vào dùng Animation.",
        "detail": "Tab Transitions và Animations là hai nhóm lệnh khác nhau. Đề thi hay hỏi để kiểm tra thí sinh có phân biệt được không.",
    },
    {
        "topic": "office",
        "icon": "💾",
        "text": "Phím tắt Ctrl + S trong Word/Excel/PowerPoint thường để:",
        "options": {
            "A": "In tài liệu",
            "B": "Lưu tệp đang làm",
            "C": "Mở thùng rác",
            "D": "Tắt máy",
        },
        "answer": "B",
        "explain": "Ctrl + S lưu nhanh — nên nhấn thường xuyên khi làm bài.",
        "detail": "Ctrl + P in; Ctrl + O mở; F12 thường Save As. Trong phòng thi, lưu đúng thư mục và đúng tên file theo đề rất quan trọng.",
    },
    {
        "topic": "office",
        "icon": "📊",
        "text": "Muốn minh họa số liệu bằng cột/tròn trong Excel, nên dùng:",
        "options": {
            "A": "Recycle Bin",
            "B": "Biểu đồ (Chart)",
            "C": "Notepad",
            "D": "Task Manager",
        },
        "answer": "B",
        "explain": "Chart biến bảng số thành hình trực quan: cột, đường, tròn…",
        "detail": "Chọn dữ liệu → Insert → Charts. Word/PowerPoint cũng chèn biểu đồ được, nhưng nguồn số liệu thường xử lý tốt nhất trong Excel.",
    },
]

# Avoid duplicating new texts that already exist in bank
for item in NEW:
    if item["text"] in seen_text:
        continue
    picked[item["topic"]].append(
        {
            "src": "new",
            "topic": item["topic"],
            "text": item["text"],
            "options": item["options"],
            "answer": item["answer"],
            "explain": item["explain"],
            "detail": item["detail"],
            "icon": item["icon"],
        }
    )
    seen_text.add(item["text"])

# Assign sequential pool ids and shuffle within topic for variety
pool = []
for topic in ("basics", "files", "security", "office"):
    items = picked[topic]
    rng.shuffle(items)
    for it in items:
        it = dict(it)
        it["id"] = len(pool) + 1
        pool.append(it)

# Target roughly balanced pool (~160-200)
print("Counts by topic:")
for t in ("basics", "files", "security", "office"):
    print(f"  {t}: {sum(1 for q in pool if q['topic']==t)}")
print("Total pool:", len(pool))

# Attach to quiz-data
data["mixed"] = {
    "id": "mixed",
    "title": "Ôn trắc nghiệm tổng hợp",
    "short": "Tổng hợp",
    "drawCount": 50,
    "drawPlan": {"basics": 18, "files": 10, "security": 8, "office": 14},
    "description": (
        "50 câu ngẫu nhiên mỗi lần: kiến thức CNTT cơ bản, quản lý tệp/thư mục, "
        "an toàn thông tin, tổng quan Word–Excel–PowerPoint."
    ),
    "topics": [
        {
            "id": "basics",
            "label": "Kiến thức CNTT cơ bản",
            "desc": "Phần cứng, phần mềm, mạng, đơn vị đo, Windows",
        },
        {
            "id": "files",
            "label": "Quản lý tệp & thư mục",
            "desc": "Tạo, xóa, đổi tên, copy/move, tìm kiếm, Recycle Bin",
        },
        {
            "id": "security",
            "label": "An toàn thông tin",
            "desc": "Virus, malware, phishing, bảo mật dữ liệu",
        },
        {
            "id": "office",
            "label": "Tổng quan Office",
            "desc": "Chức năng & giao diện Word, Excel, PowerPoint",
        },
    ],
    "questions": pool,
}

with open(HERE / "quiz-data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

with open(HERE / "quiz-data.js", "w", encoding="utf-8") as f:
    f.write("window.QUIZ_DATA = ")
    json.dump(data, f, ensure_ascii=False)
    f.write(";\n")

print("Wrote quiz-data.json / quiz-data.js with mixed pool")
