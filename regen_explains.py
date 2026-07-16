#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate Vietnamese `explain` fields for THVP quiz-data.json.
Builds explanations from (question text + correct option), with topic detection
on both sides and a large set of concept blurbs.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "quiz-data.json"
JS_PATH = ROOT / "quiz-data.js"


def clean_text(s: str) -> str:
    """Strip OCR/page junk and markdown leaks from option/question text."""
    if not s:
        return ""
    s = s.split("---")[0]
    s = re.sub(r"<[^>]+>", " ", s)
    # only strip markdown headings, not lone '#' answers (Excel column-width marker)
    s = re.sub(r"(?m)^#{1,6}\s+", " ", s)
    # trailing page markers like " 19", " 7", " 105" after meaningful text
    s = re.sub(r"(?<=\S)\s+\d{1,3}\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.rstrip(" .…")
    return s.strip()


def fold(s: str) -> str:
    s = clean_text(s).lower()
    s = unicodedata.normalize("NFC", s)
    return s


def clip_ans(ans: str, max_len: int = 110) -> str:
    ans = clean_text(ans)
    ans = re.sub(r"^(bấm|nhấn|chọn|kích)\s+", "", ans, flags=re.I)
    if len(ans) <= max_len:
        return ans
    # prefer cut at comma/semicolon
    cut = ans[:max_len]
    for sep in ("；", ";", ",", " và ", " hoặc "):
        i = cut.rfind(sep)
        if i > 40:
            return cut[:i].rstrip(" ,;") + "…"
    return cut.rstrip() + "…"


def sentence_case(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    return s[0].upper() + s[1:]


# ---------------------------------------------------------------------------
# Concept blurbs: matched when BOTH question and/or answer suggest the topic.
# Each entry: (q_keys, a_keys, blurb) — empty tuple means "any".
# Prefer more specific matches (longer key lists scored higher).
# ---------------------------------------------------------------------------

CONCEPTS: list[tuple[tuple[str, ...], tuple[str, ...], str]] = [
    # --- Hardware / memory / units ---
    (("phần cứng",), ("vật lý", "bộ phận"),
     "Phần cứng là các bộ phận vật lý của máy tính như màn hình, bàn phím, chuột, CPU, RAM… Người dùng có thể nhìn thấy và chạm vào. Ngược lại, phần mềm là chương trình và dữ liệu logic chạy trên phần cứng, không phải thiết bị vật lý."),
    (("phần mềm",), ("câu lệnh", "ngôn ngữ lập trình"),
     "Phần mềm là tập hợp câu lệnh (viết bằng ngôn ngữ lập trình) cùng dữ liệu/tài liệu liên quan để máy tính tự động thực hiện nhiệm vụ. Nó chạy trên phần cứng chứ không phải là thiết bị vật lý."),
    (("laptop", "máy tính xách tay"), ("mang", "di động"),
     "Ưu thế nổi bật của máy tính xách tay là tính di động: có thể mang theo và dùng ở nhiều nơi nhờ tích hợp sẵn pin, màn hình và bàn phím. Máy để bàn thường mạnh hơn về nâng cấp nhưng kém linh hoạt khi di chuyển."),
    (("pc", "personal computer"), ("personal computer",),
     "PC viết tắt của Personal Computer — máy tính cá nhân dùng cho một người. Đây là thuật ngữ chuẩn trong tin học cơ bản, khác với các cụm từ không chính thống như Performance Computer."),
    (("máy tính bảng", "tablet"), ("cảm ứng", "máy tính bảng"),
     "Máy tính bảng dùng màn hình cảm ứng làm giao diện chính: chạm, bút cảm ứng hoặc bàn phím ảo để thao tác. Nó khác máy để bàn (chuột/bàn phím vật lý) và máy chủ (phục vụ mạng)."),
    (("smartphone", "điện thoại thông minh"), ("hệ điều hành", "tính năng"),
     "Smartphone là điện thoại gắn hệ điều hành di động và nhiều ứng dụng/tính năng nâng cao (Internet, camera, cảm biến…). Điện thoại thường chỉ nghe-gọi thì không đủ để gọi là smartphone."),
    (("thiết bị ngoại vi", "ngoại vi"), ("máy in", "bàn phím", "chuột", "màn hình"),
     "Thiết bị ngoại vi kết nối với máy tính để nhập/xuất hoặc lưu trữ bổ sung (bàn phím, chuột, màn hình, máy in…). Chúng nằm ngoài khối xử lý trung tâm nhưng phục vụ tương tác người–máy."),
    (("nhập dữ liệu", "thiết bị nhập", "thiết bị nào", "nhập thông tin"), ("bàn phím", "chuột", "máy quét", "scanner", "máy ghi"),
     "Thiết bị nhập đưa dữ liệu/lệnh từ bên ngoài vào máy tính. Bàn phím, chuột, máy quét (scanner), webcam thuộc nhóm này; màn hình/máy in/loa thuộc nhóm xuất."),
    (("thiết bị xuất", "xuất ra", "đưa ra kết quả"), ("màn hình", "máy in", "loa", "tai nghe", "máy chiếu"),
     "Thiết bị xuất trình bày kết quả đã xử lý cho người dùng dưới dạng hình ảnh, chữ in hoặc âm thanh. Màn hình, máy in, loa, tai nghe, máy chiếu là các ví dụ điển hình."),
    (("ram",), ("random access", "truy cập ngẫu nhiên", "đọc và ghi", "4.00gb", "dung lượng bộ nhớ"),
     "RAM (Random Access Memory) là bộ nhớ truy cập ngẫu nhiên: máy đọc/ghi nhanh dữ liệu đang chạy chương trình. Dung lượng RAM (ví dụ 4 GB) ảnh hưởng nhiều đến khả năng đa nhiệm; tắt máy thì nội dung RAM thường mất."),
    (("rom",), ("read only", "chỉ đọc"),
     "ROM (Read Only Memory) là bộ nhớ chỉ đọc, thường chứa firmware/BIOS cần khi khởi động. Khác RAM, ROM giữ dữ liệu khi mất điện và người dùng thông thường không ghi đè tùy ý."),
    (("cpu", "bộ xử lý"), ("xử lý", "central", "vi xử lý", "processing"),
     "CPU (Central Processing Unit) là bộ xử lý trung tâm: thực thi lệnh chương trình và xử lý dữ liệu. Tốc độ/khả năng CPU quyết định lớn đến hiệu năng máy; thiếu CPU thì máy không hoạt động được."),
    (("mb", "megabyte"), ("dung lượng", "lưu trữ"),
     "MB (Megabyte) là đơn vị đo dung lượng lưu trữ/bộ nhớ. Trong tin học cơ bản, các đơn vị bit/byte/KB/MB/GB dùng để mô tả kích thước dữ liệu và dung lượng thiết bị."),
    (("bit",), ("nhỏ nhất", "0 và 1", "đơn vị"),
     "Bit là đơn vị thông tin nhỏ nhất trong máy tính, nhận giá trị 0 hoặc 1. Mọi dữ liệu số đều được biểu diễn bằng chuỗi bit."),
    (("byte", "1 byte"), ("8 bit",),
     "1 byte gồm 8 bit — đơn vị cơ bản để biểu diễn một ký tự/mã dữ liệu nhỏ. Các đơn vị lớn hơn (KB, MB, GB) được xây từ byte."),
    (("1 kb", "kb bằng"), ("1024",),
     "Theo quy ước nhị phân phổ biến trong tin học cơ bản, 1 KB = 1024 byte (2^10). Tương tự, 1 MB = 1024 KB."),
    (("ổ đĩa mềm", "floppy"), ("thiếu",),
     "Ổ đĩa mềm từng dùng lưu trữ nhưng ngày nay không còn thiết yếu. Bộ máy tính hiện đại vẫn chạy bình thường với ổ cứng/SSD, USB mà không cần ổ mềm."),
    (("cấu trúc chung", "thành phần cơ bản"), ("cpu", "bộ nhớ", "nhập", "xuất", "lưu trữ"),
     "Máy tính gồm khối xử lý (CPU), bộ nhớ, thiết bị lưu trữ và thiết bị nhập/xuất. Các khối này phối hợp để nhận dữ liệu, xử lý, lưu và trả kết quả."),
    (("usb", "ổ nhớ", "thiết bị lưu trữ"), ("usb", "đĩa cứng", "cd", "dvd", "thẻ nhớ"),
     "Thiết bị lưu trữ giữ dữ liệu lâu dài: ổ cứng, USB, thẻ nhớ, đĩa quang… Khác RAM, dữ liệu trên chúng thường còn sau khi tắt máy."),
    (("scanner", "máy quét", "máy scan"), ("usb", "nhập"),
     "Máy quét (scanner) chuyển tài liệu/ảnh giấy thành dữ liệu số đưa vào máy — thuộc thiết bị nhập. Kết nối phổ biến hiện nay là qua cổng USB."),
    (("máy ảnh kỹ thuật số", "digital"), ("hình ảnh", "phim"),
     "Máy ảnh kỹ thuật số thu và lưu ảnh dưới dạng file số, không cần phim truyền thống. Ảnh có thể chuyển sang máy tính để xem, chỉnh sửa, chia sẻ."),
    (("driver", "điều khiển thiết bị"), ("driver",),
     "Driver (trình điều khiển) là phần mềm giúp hệ điều hành giao tiếp đúng với thiết bị phần cứng. Khi gắn thiết bị mới, thường cần cài driver kèm theo đĩa/file nhà sản xuất."),
    (("hệ điều hành", "operating system"), ("quản lý", "tài nguyên", "windows", "linux", "mac os", "điều hành"),
     "Hệ điều hành quản lý phần cứng và tài nguyên (CPU, bộ nhớ, đĩa, thiết bị), đồng thời cung cấp môi trường để phần mềm ứng dụng chạy. Windows, Linux, macOS là các ví dụ phổ biến."),
    (("phần mềm ứng dụng",), ("microsoft word", "ứng dụng"),
     "Phần mềm ứng dụng phục vụ công việc cụ thể của người dùng (soạn thảo, bảng tính, trình chiếu…). Nó cần hệ điều hành để chạy, khác phần mềm hệ thống."),
    (("phần mềm hệ thống",), ("hệ điều hành",),
     "Phần mềm hệ thống quản lý và điều phối máy tính; hệ điều hành là ví dụ điển hình. Nó khác phần mềm ứng dụng vốn phục vụ tác vụ người dùng cuối."),
    (("mã nguồn mở", "open source"), ("mã nguồn", "sửa đổi", "open office"),
     "Phần mềm mã nguồn mở công bố mã nguồn để ai cũng có thể xem, sửa, phân phối theo giấy phép mở. Không đồng nghĩa với “phải mua bản quyền độc quyền” như phần mềm thương mại đóng."),
    (("giấy phép", "bản quyền", "software license", "quyền tác giả"), ("giấy phép", "đồng ý", "quyền", "bản quyền"),
     "Giấy phép phần mềm quy định quyền và nghĩa vụ khi dùng phần mềm. Cài đặt thêm máy/sao chép chỉ hợp pháp khi giấy phép cho phép; dùng bản bẻ khóa là vi phạm bản quyền."),
    (("sleep",), ("tiêu thụ điện",),
     "Chế độ Sleep tạm dừng hầu hết hoạt động để tiết kiệm điện nhưng máy vẫn tiêu thụ một ít điện để giữ trạng thái trong RAM. Khác Hibernate (lưu trạng thái xuống ổ cứng rồi gần như tắt hẳn)."),
    (("hibernate",), ("ổ đĩa cứng", "phím bất kỳ"),
     "Hibernate lưu trạng thái phiên làm việc xuống ổ cứng rồi tắt máy gần như hoàn toàn; bật lại có thể tiếp tục từ chỗ đã dừng. Tiết kiệm điện hơn Sleep vì không cần nuôi RAM liên tục."),
    (("lan", "mạng cục bộ"), ("local area", "gần nhau", "văn phòng"),
     "LAN (Local Area Network) là mạng cục bộ kết nối máy trong phạm vi hẹp như phòng/văn phòng/tòa nhà để chia sẻ tài nguyên. Phạm vi nhỏ hơn WAN."),
    (("wan", "mạng diện rộng"), ("wide area", "khoảng cách lớn"),
     "WAN (Wide Area Network) nối các mạng/máy ở khoảng cách lớn (thành phố, quốc gia). Internet là ví dụ mạng diện rộng quy mô toàn cầu."),
    (("bps", "mbps", "tốc độ truyền"), ("bit per second", "tốc độ truyền"),
     "Tốc độ truyền dữ liệu mạng thường đo bằng bps (bit mỗi giây) và các bội số như Kbps, Mbps. Đơn vị này mô tả băng thông, khác đơn vị dung lượng lưu trữ (byte)."),
    (("intranet",), ("cơ quan", "admin"),
     "Intranet là mạng nội bộ của tổ chức, dùng công nghệ kiểu Internet nhưng phạm vi kiểm soát nội bộ. Quản trị viên quyết định thông tin nào được phép ra ngoài."),
    (("internet",), ("toàn cầu", "liên kết"),
     "Internet là hệ thống mạng máy tính toàn cầu liên kết với nhau, cho phép truy cập công cộng nhiều dịch vụ (Web, email…). Không phải dịch vụ chỉ do một công ty Mỹ độc quyền điều hành."),
    (("download",), ("tải",),
     "Download là tải dữ liệu/file từ máy chủ hoặc thiết bị khác về máy của bạn. Ngược lại, upload là gửi dữ liệu từ máy bạn lên máy chủ."),
    (("email", "thư điện tử"), ("electronic mail", "@", "hộp thư"),
     "Email (Electronic mail) là dịch vụ gửi/nhận thư qua mạng. Địa chỉ chuẩn dạng tên_người_dùng@tên_miền; ký hiệu @ bắt buộc có trong địa chỉ email."),
    (("voip", "voice over"), ("điện thoại", "ip"),
     "VoIP truyền thoại qua giao thức IP/Internet thay vì chỉ phụ thuộc đường dây điện thoại truyền thống. Có thể gọi qua mạng máy tính với phần mềm/tài khoản phù hợp."),
    (("forum", "diễn đàn"), ("thảo luận", "trao đổi"),
     "Diễn đàn (forum) là không gian trực tuyến để người dùng đăng bài, thảo luận theo chủ đề. Khác chat thời gian thực, forum thường lưu trữ theo luồng bài viết."),
    (("chatroom", "chat", "tán gẫu"), ("thảo luận trực tiếp", "ngay lập tức"),
     "Phòng chat cho phép trao đổi gần như tức thời trên Internet, giống hội thoại trực tiếp. Phản hồi thường nhanh hơn diễn đàn dạng chủ đề."),
    (("ergonomic", "tư thế", "ngồi lâu", "màn hình máy tính"), ("cánh tay", "góc vuông", "cửa sổ", "mắt"),
     "Ngồi máy đúng tư thế (lưng thẳng, chân đặt sàn, khuỷu tay gần góc vuông) và đặt màn hình tránh chói giúp giảm mỏi cổ–lưng–mắt. Ngồi lâu không nghỉ có thể gây hại sức khỏe."),
    (("tái chế",), ("ô nhiễm",),
     "Tái chế linh kiện máy tính giúp thu hồi vật liệu và giảm rác thải điện tử gây ô nhiễm. Vứt thiết bị bừa bãi có thể phát tán kim loại nặng/hóa chất độc."),
    (("mật khẩu",), ("ký tự đặc biệt", "chữ hoa", "7 ký tự", "p@ss"),
     "Mật khẩu mạnh thường dài, kết hợp chữ hoa–thường, số và ký tự đặc biệt, tránh từ điển/tên dễ đoán. Mật khẩu yếu giúp kẻ tấn công dò ra nhanh hơn."),
    (("tường lửa", "firewall"), ("ngăn", "an ninh", "xâm nhập"),
     "Tường lửa (firewall) lọc kết nối mạng theo chính sách bảo mật, chặn truy cập không được phép từ ngoài vào hoặc ra. Có thể là phần mềm, phần cứng, hoặc kết hợp cả hai."),
    (("virus",), ("tự lây", "tự sao", "phá hoại"),
     "Virus là chương trình độc hại có khả năng tự sao chép/lây lan và có thể phá dữ liệu hoặc đánh cắp thông tin. Nên dùng antivirus cập nhật và thận trọng với file lạ."),
    (("trojan",), ("không", "tự sao"),
     "Trojan (ngựa thành Troy) gây hại giống mã độc nhưng thường không tự nhân bản như virus; thường ngụy trang thành phần mềm hợp lệ để đánh lừa người dùng."),
    (("sao lưu", "backup"), ("thường xuyên",),
     "Sao lưu (backup) định kỳ giữ bản sao dữ liệu quan trọng để khôi phục khi mất mát, hỏng đĩa hoặc nhiễm mã độc. Chỉ dựa vào một bản trên máy đang dùng là rủi ro cao."),
    (("cập nhật", "update"), ("bảo mật", "hệ thống"),
     "Cập nhật hệ điều hành/phần mềm vá lỗ hổng bảo mật đã biết. Không cập nhật khiến máy dễ bị khai thác qua điểm yếu cũ."),

    # --- Windows / Module 2 ---
    (("shut down", "tắt máy", "shutdown"), ("tắt", "start", "ghi dữ liệu"),
     "Shutdown tắt máy đúng quy trình: lưu dữ liệu, đóng chương trình rồi chọn Start → Shutdown. Cách này giúp hệ thống đóng file an toàn, giảm nguy cơ hỏng dữ liệu so với cắt điện đột ngột."),
    (("khi khởi động máy tính", "phần mềm nào sau đây sẽ được thực hiện trước"), ("hệ điều hành",),
     "Khi bật máy, hệ điều hành được nạp và chạy trước các ứng dụng. Ứng dụng chỉ hoạt động được sau khi hệ điều hành đã sẵn sàng quản lý phần cứng."),
    (("cài đặt đầu tiên", "được cài đặt đầu tiên"), ("windows", "ms windows"),
     "Hệ điều hành (ví dụ MS Windows) cần được cài trước vì nó quản lý phần cứng và tạo môi trường để các phần mềm ứng dụng chạy. Cài Word/Excel trước khi có hệ điều hành là không thực tế."),
    (("khởi động microsoft office word", "cách khởi động microsoft office word"), ("shortcut", "biểu tượng", "đúp"),
     "Cách phổ biến để mở Word là kích đúp biểu tượng shortcut Microsoft Office Word trên Desktop/thanh tác vụ. Shortcut chỉ là lối tắt; chương trình Word phải đã được cài trên máy."),
    (("eject", "usb", "ngắt ổ"), ("eject", "chuột phải"),
     "Gỡ USB an toàn (Eject) để hệ thống hoàn tất ghi dữ liệu trước khi rút. Rút đột ngột có thể làm hỏng file đang ghi hoặc hệ thống file trên USB."),
    (("screen saver", "nghỉ màn hình"), ("display",),
     "Screen Saver thiết lập ảnh/hiệu ứng khi không thao tác một lúc; trong Windows thường cấu hình qua Display (Control Panel) hoặc Personalization. Mục đích chính là bảo vệ/hiển thị khi máy nhàn rỗi."),
    (("lock this computer", "khóa máy"), ("ctrl + alt + del", "lock"),
     "Khóa máy (Lock) giữ phiên đăng nhập nhưng yêu cầu mật khẩu để tiếp tục, phù hợp khi rời máy tạm thời. Không tắt các chương trình đang mở như Shutdown."),
    (("alt+print", "alt + print", "chụp cửa sổ"), ("alt", "print"),
     "Alt + Print Screen chụp cửa sổ đang active vào Clipboard. Print Screen không kèm Alt thường chụp toàn màn hình."),
    (("alt+f4", "alt + f4"), ("đóng cửa sổ",),
     "Alt + F4 đóng cửa sổ/ứng dụng hiện hành trong Windows. Đây là phím tắt chuẩn, khác Alt + Tab (chuyển cửa sổ)."),
    (("ctrl+c", "ctrl + c"), ("sao chép", "copy", "clipboard"),
     "Ctrl + C sao chép nội dung đã chọn vào Clipboard mà không xóa bản gốc. Sau đó dùng Ctrl + V để dán ở vị trí mới."),
    (("ctrl+x", "ctrl + x"), ("cắt", "cut", "di chuyển"),
     "Ctrl + X cắt đối tượng vào Clipboard (bản gốc sẽ bị gỡ khi dán thành công theo ngữ cảnh). Dùng khi muốn di chuyển chứ không nhân bản."),
    (("ctrl+v", "ctrl + v"), ("dán", "paste"),
     "Ctrl + V dán nội dung từ Clipboard vào vị trí hiện tại. Cần Copy/Cut trước thì Clipboard mới có dữ liệu để dán."),
    (("ctrl+z", "ctrl + z"), ("undo", "hủy", "quay lại"),
     "Ctrl + Z hoàn tác (Undo) thao tác vừa làm. Giúp sửa nhanh sai sót mà không cần làm lại từ đầu."),
    (("alt + tab", "alt+tab"), ("chuyển", "cửa sổ"),
     "Alt + Tab chuyển nhanh giữa các cửa sổ đang mở. Giữ Alt và nhấn Tab để chọn cửa sổ cần đưa lên trước."),
    (("ctrl+esc", "ctrl + esc", "start menu"), ("start",),
     "Ctrl + Esc mở menu Start (tương tự nhấn phím Windows). Từ Start có thể mở chương trình, tìm kiếm hoặc tắt máy."),
    (("windows + d", "win + d"), ("desktop", "màn hình nền"),
     "Windows + D hiện Desktop (ẩn/hiện tạm các cửa sổ). Thuận tiện khi cần truy cập biểu tượng trên màn hình nền."),
    (("ctrl+a", "ctrl + a"), ("tất cả", "chọn tất cả"),
     "Ctrl + A chọn tất cả đối tượng trong cửa sổ/vùng hiện hành (file trong thư mục, chữ trong văn bản…)."),
    (("ctrl+p", "ctrl + p"), ("in",),
     "Ctrl + P mở hộp thoại/in tài liệu hiện hành. Đây là phím tắt in phổ biến trên nhiều ứng dụng Windows."),
    (("f2",), ("đổi tên",),
     "F2 đổi tên file/thư mục đang chọn trong Windows Explorer. Sau khi sửa tên, nhấn Enter để xác nhận."),
    (("delete",), ("xóa", "ký tự đằng sau", "recycle"),
     "Phím Delete xóa ký tự bên phải con trỏ khi soạn thảo, hoặc đưa file/thư mục vào Recycle Bin khi quản lý đĩa cứng. Shift + Delete thì xóa vĩnh viễn."),
    (("shift + delete", "shift+delete"), ("vĩnh viễn",),
     "Shift + Delete xóa vĩnh viễn, không đưa vào Recycle Bin nên khó khôi phục bằng thùng rác. Chỉ dùng khi chắc chắn không cần phục hồi."),
    (("recycle bin", "thùng rác"), ("ổ đĩa cứng", "restore", "khôi phục"),
     "Recycle Bin giữ tạm file xóa từ ổ cứng nội bộ để có thể Restore. File xóa từ USB thường mất ngay, không qua thùng rác."),
    (("control panel",), ("thiết lập", "cấu hình", "date and time", "region", "programs"),
     "Control Panel là nơi thiết lập hệ thống Windows: ngày giờ, ngôn ngữ, gỡ chương trình, tài khoản, thiết bị… Nhiều tùy chỉnh quan trọng được tập trung tại đây."),
    (("date and time",), ("ngày", "giờ"),
     "Date and Time trong Control Panel chỉnh ngày–giờ hệ thống. Đồng hồ hệ thống đúng rất quan trọng cho lịch, chứng chỉ và nhật ký."),
    (("region and language",), ("định dạng", "biểu diễn", "ngôn ngữ"),
     "Region and Language quy định cách hiển thị ngày/giờ/số và tùy chọn ngôn ngữ. Khác với việc chỉnh giá trị đồng hồ tại Date and Time."),
    (("personalization", "desktop background", "hình nền"), ("background", "personalization"),
     "Đổi hình nền Desktop qua Personalization → Desktop Background (chuột phải Desktop). Chỉ đổi giao diện, không ảnh hưởng dữ liệu người dùng."),
    (("programs and features", "uninstall"), ("gỡ", "uninstall"),
     "Programs and Features cho phép Uninstall phần mềm đã cài. Gỡ đúng cách giúp xóa đăng ký/file chương trình sạch hơn so với chỉ xóa thư mục."),
    (("user accounts",), ("tài khoản", "log on", "login"),
     "User Accounts quản lý tài khoản đăng nhập Windows và tùy chọn cách log on/log off. Mỗi tài khoản có quyền và dữ liệu riêng."),
    (("shortcut",), ("truy cập nhanh", "không thay đổi", "không mở"),
     "Shortcut là lối tắt trỏ tới file/chương trình gốc để mở nhanh. Xóa shortcut không xóa chương trình; copy shortcut sang máy khác thường hỏng vì đường dẫn gốc khác."),
    (("windows explorer", "explorer"), ("quản lý", "tập tin", "thư mục"),
     "Windows Explorer (File Explorer) dùng quản lý ổ đĩa, thư mục và tập tin: sao chép, đổi tên, tìm kiếm, xem thuộc tính…"),
    (("phần mở rộng", "đuôi file", ".jpg", "jpg", "mp3", "pdf", "ppt", "txt", "rar", "zip"),
     ("kiểu file", "ảnh", "âm thanh", "nén", "foxit", "powerpoint", "notepad"),
     "Phần mở rộng sau dấu chấm cho biết kiểu file và chương trình mặc định mở nó (ví dụ .jpg ảnh, .mp3 nhạc, .pdf tài liệu). Đổi đuôi tùy tiện có thể làm file mở sai."),
    (("cấu trúc cây", "thư mục được tổ chức"), ("cây",),
     "File/thư mục trong Windows tổ chức dạng cây: thư mục chứa file và thư mục con. Một file không chứa file/thư mục khác bên trong."),
    (("tên tệp", "tên file", "tên thư mục"), ("255", "không chứa", "dấu chấm", "2 phần"),
     "Tên file gồm tên + phần mở rộng, ngăn bởi dấu chấm; tối đa khoảng 255 ký tự và không dùng \\ / : * ? \" < > |. Ký tự cấm hoặc dạng giống URL dễ khiến hệ thống báo lỗi."),
    (("shift", "liền nhau"), ("shift",),
     "Giữ Shift khi chọn giúp bôi một dải file/thư mục liền nhau từ mục đầu đến mục cuối. Muốn chọn rải rác thì dùng Ctrl."),
    (("không liền", "không liên tục", "rải rác"), ("ctrl",),
     "Giữ Ctrl và click từng mục để chọn nhiều file không liền nhau. Shift dùng cho dải liên tục."),
    (("nén", "compression", "zip", "rar"), ("giảm dung lượng", "winrar", "winzip", "nhỏ hơn"),
     "Nén (ZIP/RAR) giảm dung lượng lưu trữ/truyền tải mà vẫn giữ thông tin để giải nén lại. Rất hữu ích khi gửi nhiều file lớn qua email."),
    (("antivirus", "chống virus"), ("antivirus", "quét"),
     "Phần mềm antivirus phát hiện, ngăn chặn và loại bỏ mã độc. Cần cập nhật mẫu nhận diện thường xuyên mới phát hiện mối đe dọa mới."),
    (("unikey", "gõ tiếng việt", "telex"), ("unikey", "ctrl + shift", "z", "times new roman"),
     "Unikey hỗ trợ gõ tiếng Việt (Telex/VNI…); Ctrl + Shift thường dùng chuyển Anh↔Việt, phím Z thường bỏ dấu theo Telex. Font Times New Roman được nêu trong quy định thể thức văn bản hành chính."),
    (("default printer", "máy in mặc định"), ("set as default",),
     "Set as Default Printer chọn máy in dùng mặc định khi in. Các lệnh in sẽ ưu tiên máy này trừ khi chọn máy khác."),
    (("cài đặt máy in",), ("driver",),
     "Cài máy in cần máy tính, máy in đã kết nối và driver phù hợp. Thiếu driver thì hệ điều hành khó điều khiển đúng thiết bị."),

    # --- Word ---
    (("ctrl + e", "ctrl+e"), ("căn", "giữa"),
     "Trong Word/PowerPoint, Ctrl + E căn giữa đoạn đang chọn. Căn giữa thường dùng cho tiêu đề."),
    (("ctrl + j", "ctrl+j"), ("đều hai bên", "justify"),
     "Ctrl + J căn đều hai bên (justify), làm mép trái và phải thẳng hàng. Thường dùng cho thân văn bản trang trọng."),
    ((".docx", "phần mở rộng", "định dạng mặc định"), (".docx", "docx"),
     "Word 2007/2010 trở đi lưu mặc định dạng .docx (Office Open XML). .doc là định dạng cũ hơn; vẫn có thể Save As sang PDF khi cần."),
    (("ctrl+k", "ctrl + k", "hyperlink"), ("hyperlink", "liên kết"),
     "Ctrl + K mở hộp thoại chèn/sửa Hyperlink — gắn liên kết tới trang web, file hoặc vị trí trong tài liệu."),
    (("file/close", "file / close"), ("đóng",),
     "File → Close đóng tài liệu hiện tại nhưng thường không thoát hẳn ứng dụng. Muốn thoát chương trình dùng Exit/Close cửa sổ chính."),
    (("file/save", "ctrl + s", "ctrl+s"), ("lưu",),
     "File → Save hoặc Ctrl + S lưu thay đổi vào file hiện có. Lưu thường xuyên giảm mất dữ liệu khi sự cố."),
    (("save as",), ("tên mới", "pdf"),
     "Save As lưu thành bản mới (đổi tên/đường dẫn/định dạng). Dùng khi cần giữ bản gốc và tạo bản sao hoặc xuất PDF."),
    (("ctrl + n", "ctrl+n"), ("mới",),
     "Ctrl + N tạo tài liệu/workbook/presentation mới theo ứng dụng đang dùng. Nhanh hơn vào menu File → New."),
    (("ctrl + o", "ctrl+o"), ("mở",),
     "Ctrl + O mở file đã có trên máy. Hộp thoại Open cho phép chọn đường dẫn và kiểu file."),
    (("print layout",), ("in ra giấy",),
     "Print Layout hiển thị trang gần như khi in (lề, đầu trang, chân trang…). Thuận tiện chỉnh bố cục trước khi in."),
    (("full screen reading", "reading"), ("đọc", "không được sửa"),
     "Full Screen Reading tối ưu để đọc toàn màn hình; thường hạn chế sửa nội dung. Phù hợp xem tài liệu, không phải chế độ soạn thảo chính."),
    (("f1", "help"), ("trợ giúp", "f1"),
     "F1 mở trợ giúp (Help) của ứng dụng Office/Windows. Dùng để tra cứu lệnh và thao tác khi chưa nhớ đường menu."),
    (("web layout",), ("website",),
     "Web Layout xem văn bản theo kiểu trang web (dòng chảy theo cửa sổ). Khác Print Layout vốn bám khổ giấy in."),
    (("auto recover", "tự động"), ("thời gian",),
     "Save AutoRecover đặt khoảng thời gian Word tự lưu bản phục hồi. Khi treo/mất điện, có cơ hội lấy lại phần đã soạn."),
    (("insert/ symbol", "symbol", "ký hiệu"), ("symbol", "≥", "®", "©"),
     "Insert → Symbol chèn ký tự đặc biệt không có sẵn trên bàn phím (©, ®, ≥…). Có thể chọn thêm trong More Symbols/Special Characters."),
    (("ctrl + h", "ctrl+h", "replace"), ("thay thế", "find and replace"),
     "Ctrl + H mở Find and Replace để tìm và thay văn bản hàng loạt. Tiết kiệm thời gian hơn sửa từng chỗ thủ công."),
    (("ctrl + f", "ctrl+f"), ("tìm kiếm", "find"),
     "Ctrl + F mở tìm kiếm trong tài liệu/trang. Nhập từ khóa để nhảy tới các vị trí khớp."),
    (("ctrl + ]",), ("tăng cỡ chữ",),
     "Ctrl + ] tăng cỡ chữ vùng chọn trong Word. Ngược lại, Ctrl + [ thường dùng để giảm cỡ chữ."),
    (("ctrl+b", "ctrl + b"), ("đậm", "bold"),
     "Ctrl + B bật/tắt chữ đậm (Bold) cho vùng chọn. Đây là phím tắt định dạng font phổ biến trong Office."),
    (("chỉ số dưới", "subscript", "chỉ số trên", "superscript"), ("đều đúng", "cách"),
     "Chỉ số trên/dưới (superscript/subscript) dùng cho công thức, chú thích. Có thể bật qua nhóm Font trên tab Home hoặc hộp thoại Font."),
    (("shading", "màu nền"), ("shading",),
     "Shading tô nền đoạn/ô được chọn để nhấn mạnh nội dung. Nằm trong nhóm Paragraph (Word) hoặc Design của bảng."),
    (("capslock", "caps lock", "upper case", "lower case", "change case"),
     ("hoa", "thường", "upper", "lower", "change case"),
     "Caps Lock giữ trạng thái gõ hoa toàn bộ phím chữ; Change Case (Upper/Lower…) đổi hoa/thường cho đoạn đã chọn mà không cần gõ lại."),
    (("indent", "thụt", "paragraph"), ("indentation", "left", "right"),
     "Indentation trong hộp thoại Paragraph thụt đoạn trái/phải theo số đo cụ thể. Giúp bố cục rõ cấp ý hơn so với chỉ dùng Space."),
    (("ruler", "thước"), ("ruler",),
     "Thước kẻ (Ruler) hỗ trợ căn lề, tab và thụt đoạn trực quan. Bật/tắt qua View → Show → Ruler."),
    (("line spacing", "spacing", "khoảng cách dòng", "khoảng cách đoạn"), ("spacing", "before", "after", "line spacing"),
     "Spacing (Before/After, Line Spacing) chỉnh khoảng cách đoạn và dòng cho dễ đọc. Tránh xuống dòng thủ công bằng Enter để tạo khoảng trống giả."),
    (("bullets", "numbering", "đánh dấu", "đánh số"), ("bullets", "numbering"),
     "Bullets tạo danh sách ký hiệu; Numbering tạo danh sách đánh số. Cả hai nằm nhóm Paragraph tab Home, giúp cấu trúc ý rõ ràng."),
    (("page border", "border and shading", "đường viền"), ("border", "art", "page border"),
     "Borders and Shading/Page Border tạo viền đoạn hoặc viền trang (kể cả kiểu Art). Có thể giới hạn áp dụng First Page Only khi cần."),
    (("style",), ("modify", "styles"),
     "Style gói sẵn font, cỡ chữ, khoảng đoạn… để áp dụng đồng nhất. Modify Style để đổi định dạng mẫu; chọn đoạn rồi chọn Style để áp dụng."),
    (("ctrl+shift+c",), ("copy định dạng",),
     "Ctrl + Shift + C sao chép định dạng (format) trong Word để dán định dạng sang chỗ khác (thường kèm Ctrl + Shift + V). Khác Ctrl + C chỉ copy nội dung."),
    (("table", "bảng", "merge cells"), ("insert table", "merge", "5 cột", "tab"),
     "Bảng (Table) tổ chức dữ liệu theo hàng–cột; kích thước m×n nghĩa là m cột n hàng (theo cách đề nêu). Tab di chuyển giữa các ô; Merge Cells gộp ô."),
    (("shapes", "chart", "picture", "illustrations", "textbox"),
     ("shapes", "chart", "picture", "textbox", "illustrations"),
     "Nhóm Illustrations/Insert cho phép chèn Shape, Chart, Picture, Text Box… để minh họa nội dung. Sau khi chèn có thể định dạng viền, màu, kích thước."),
    (("footnote", "chú thích"), ("footnote", "references"),
     "Insert Footnote (tab References) thêm chú thích cuối trang gắn với vị trí đánh dấu trong văn bản. Phù hợp trích dẫn/giải thích thuật ngữ."),
    (("page number", "header", "footer", "ngắt trang", "page break"),
     ("page number", "header", "footer", "page break"),
     "Page Number/Header/Footer gắn thông tin lặp trên các trang; Page Break ngắt sang trang mới đúng vị trí. Các lệnh nằm chủ yếu ở Insert và Page Layout."),
    (("portrait", "landscape", "hướng"), ("dọc", "ngang", "orientation"),
     "Orientation Portrait là hướng dọc (mặc định), Landscape là ngang. Đổi trong Page Layout → Orientation tùy khổ trình bày."),
    (("lề", "margins"), ("khoảng cách", "margins"),
     "Lề (Margins) là khoảng trống giữa mép giấy và vùng chữ. Chỉnh lề giúp văn bản cân đối và tránh bị máy in cắt chữ."),
    (("print preview",), ("xem", "trước khi in"),
     "Print Preview xem trước bố cục in để phát hiện lỗi lề/ngắt trang trước khi in giấy. Giảm lãng phí giấy mực."),
    (("encrypt", "mật khẩu cho văn bản", "protect document"), ("password", "encrypt"),
     "Encrypt with Password khóa file bằng mật khẩu; không có mật khẩu đúng thì khó mở nội dung. Cần nhớ mật khẩu vì mất có thể không mở lại được."),
    (("times new roman", "thông tư", "tt03", "thể thức"), ("times new roman",),
     "Theo quy định thể thức văn bản hành chính phổ biến trong đề thi, font Times New Roman được yêu cầu khi trình bày văn bản. Giúp thống nhất hình thức công văn."),

    # --- Excel ---
    (("excel",), ("tính toán", "xlsx", "xls"),
     "Excel là phần mềm bảng tính dùng nhập liệu, tính toán, phân tích và biểu đồ hóa dữ liệu. File mặc định Excel 2007+ là .xlsx; .xls là định dạng cũ hơn, thường nặng hơn."),
    (("16384", "1048576", "số cột", "số hàng"), ("16384", "1048576"),
     "Một worksheet Excel 2007/2010 có tới 16 384 cột và 1 048 576 hàng. Giới hạn này lớn hơn nhiều so với phiên bản .xls cũ."),
    (("địa chỉ tuyệt đối", "$a$12", "f4"), ("$a$12", "$", "f4"),
     "Địa chỉ tuyệt đối dạng $Cột$Hàng (ví dụ $A$12) không đổi khi sao chép công thức. Phím F4 xoay vòng tương đối/tuyệt đối/hỗn hợp khi đang sửa tham chiếu."),
    (("địa chỉ hỗn hợp", "$a12"), ("$a12",),
     "Địa chỉ hỗn hợp khóa một phần: $A12 cố định cột A, A$12 cố định hàng 12. Khi fill công thức, phần không có $ sẽ dịch chuyển."),
    (("vùng", "b1:h15"), ("b1:h15", ":"),
     "Vùng (range) là khối ô chữ nhật, địa chỉ viết dạng ÔĐầu:ÔCuối (ví dụ B1:H15). Dùng làm đối số cho nhiều hàm Excel."),
    (("căn lề", "ký tự", "ngày tháng"), ("trái", "phải"),
     "Theo mặc định Excel căn trái dữ liệu kiểu chữ và căn phải số/ngày tháng. Cách hiển thị này giúp nhận biết nhanh kiểu dữ liệu."),
    (("filter", "autofilter", "sort"), ("filter", "sort"),
     "Sort sắp xếp; Filter/AutoFilter lọc hiện các dòng thỏa điều kiện (ví dụ xếp loại “xuất sắc”). Cả hai nằm tab Data, rất hay dùng khi phân tích danh sách."),
    (("freeze panes",), ("freeze",),
     "Freeze Panes giữ cố định hàng/cột tiêu đề khi cuộn trang tính. Giúp luôn nhìn thấy nhãn cột/hàng trong bảng dài."),
    (("=", "công thức"), ("=", "dấu"),
     "Mọi công thức Excel bắt đầu bằng dấu =. Sau đó nhập biểu thức, hàm và tham chiếu ô cần tính."),
    (("&", "ghép", "nối chuỗi"), ("&",),
     "Toán tử & nối chuỗi trong Excel. Có thể ghép ô và chuỗi cố định, ví dụ =A5&\" \"&B5 để tạo họ tên có khoảng trắng."),
    (("#ref", "#div/0", "#name?", "#value!", "#####"), ("#ref", "#div/0", "#name?", "#value!", "#"),
     "Excel báo lỗi theo mã: ##### thường do cột hẹp với số; #DIV/0! chia cho 0; #NAME? sai tên hàm/chưa có tên; #REF! tham chiếu hỏng; #VALUE! kiểu dữ liệu không phù hợp."),
    (("sum", "tổng"), ("tổng", "sum"),
     "SUM cộng các giá trị số trong đối số/vùng chọn. Là hàm thống kê cơ bản nhất trên bảng tính."),
    (("min",), ("nhỏ nhất", "min"),
     "MIN trả về giá trị nhỏ nhất trong danh sách/vùng. Ngược lại MAX trả về giá trị lớn nhất."),
    (("max",), ("lớn nhất", "max", "65", "14"),
     "MAX chọn giá trị lớn nhất trong các đối số. Ví dụ =MAX(30,10,65,5) cho 65."),
    (("average", "everage"), ("trung bình", "average"),
     "AVERAGE tính trung bình cộng các giá trị số. Lưu ý gõ đúng tên hàm; sai chính tả sẽ ra #NAME?."),
    (("countif", "sumif"), ("countif", "sumif", "điều kiện"),
     "COUNTIF đếm ô thỏa điều kiện; SUMIF cộng theo điều kiện trên một vùng tiêu chí. Cú pháp điển hình: =SUMIF(range,criteria,[sum_range])."),
    (("count(", "counta"), ("count", "counta"),
     "COUNT đếm ô/giá trị kiểu số; COUNTA đếm ô không rỗng (gồm cả chữ). Chọn đúng hàm để thống kê không lệch."),
    (("product",), ("product", "nhân"),
     "PRODUCT nhân các đối số với nhau. Ví dụ =PRODUCT(A2,5) tương đương A2*5."),
    (("mod",), ("mod", "chia dư"),
     "MOD(số, số_chia) trả về phần dư phép chia. Ví dụ =MOD(26,7) = 5."),
    (("round",), ("round", "làm tròn"),
     "ROUND làm tròn số theo số chữ số chỉ định; số âm làm tròn về hàng chục/trăm… Ví dụ ROUND(7475.47,-2) → 7500."),
    (("mid",), ("mid", "chuỗi"),
     "MID(chuỗi, vị_trí, số_ký_tự) lấy chuỗi con. Ví dụ =MID(\"m1234\",2,3) → \"123\"."),
    (("if(", "hàm if", "cú pháp hàm if"), ("if", "logic", "<>"),
     "IF(điều_kiện, giá_trị_đúng, giá_trị_sai) rẽ nhánh theo phép so sánh. Toán tử <> nghĩa là khác; có thể lồng nhiều IF hoặc kết hợp AND/OR."),
    (("today", "month", "year", "now"), ("today", "tháng", "năm", "ngày"),
     "TODAY()/NOW() lấy ngày (và giờ) hệ thống; MONTH/YEAR tách thành phần tháng/năm từ một giá trị ngày. Rất hữu ích tính tuổi, hạn, báo cáo theo thời gian."),
    (("vlookup", "hlookup", "dò tìm"), ("vlookup", "hlookup", "lookup"),
     "VLOOKUP/HLOOKUP dò giá trị trong bảng và trả về dữ liệu ở cột/hàng chỉ định. Tham số range_lookup quyết định khớp gần đúng (1) hay khớp Exact (0)."),
    (("conditional formatting",), ("conditional",),
     "Conditional Formatting đổi màu/chữ tự động theo điều kiện dữ liệu. Giúp nhận biết nhanh giá trị nổi bật mà không format thủ công từng ô."),
    (("format painter",), ("format paint",),
     "Format Painter sao chép định dạng ô này sang ô khác. Giữ nhất quán giao diện bảng mà không cần thiết lập lại từng thuộc tính."),
    (("wrap text",), ("wrap",),
     "Wrap Text cho phép nội dung dài xuống dòng trong một ô thay vì tràn sang ô bên. Kết hợp chỉnh cao hàng để nhìn đủ chữ."),
    (("merge cells",), ("merge",),
     "Merge Cells gộp nhiều ô thành một ô lớn, thường dùng cho tiêu đề bảng. Cần thận trọng vì gộp ô có thể ảnh hưởng sắp xếp/lọc."),
    (("pie", "biểu đồ", "column", "chart"), ("pie", "column", "chart", "%"),
     "Biểu đồ cột so sánh giá trị; biểu đồ tròn (Pie) phù hợp thể hiện tỷ lệ phần trăm tổng thể. Chèn qua Insert → Charts."),
    (("print titles",), ("print titles",),
     "Print Titles in lặp hàng/cột tiêu đề trên mọi trang in. Khi bảng nhiều trang, tiêu đề vẫn xuất hiện để dễ đọc."),

    # --- PowerPoint ---
    (("để một bài thuyết trình đạt hiệu quả", "nắm vững nội dung"), ("nắm vững", "nội dung"),
     "Bài thuyết trình hiệu quả bắt đầu từ nắm vững nội dung cần nói; kỹ thuật chỉ là phương tiện hỗ trợ. Hình ảnh/hiệu ứng đẹp không thay được việc hiểu rõ thông điệp."),
    (("phần mở rộng của tên file", "phần mở rộng", "pptx"), ("pptx",),
     "File PowerPoint 2007/2010 trở đi thường có đuôi .pptx. Mỗi trang trình bày gọi là một slide."),
    (("mỗi trang trình diễn", "được gọi là"), ("slide", "một slide"),
     "Mỗi trang trình diễn trong PowerPoint được gọi là một slide. Tập hợp nhiều slide tạo thành một presentation."),
    (("slide sorter",), ("sắp xếp", "slide sorter"),
     "Slide Sorter hiển thị nhiều slide dạng thu nhỏ để kéo thả đổi thứ tự nhanh. Phù hợp chỉnh cấu trúc bài trước khi trình chiếu."),
    (("reading view",), ("reading",),
     "Reading View xem bài gần như trình chiếu nhưng vẫn trong cửa sổ ứng dụng. Tiện duyệt nội dung mà chưa cần fullscreen Slide Show."),
    (("slide master",), ("master", "định dạng chung"),
     "Slide Master đặt định dạng/chỗ đặt chung cho nhiều slide (font, logo, chỗ tiêu đề…). Sửa Master giúp đồng bộ giao diện cả bài."),
    (("layout", "placeholder", "two content", "comparison"),
     ("layout", "placeholder", "title and content"),
     "Layout quy định bố cục placeholder (ô chứa tiêu đề/nội dung/ảnh…). Ví dụ Title and Content có tiêu đề + vùng nội dung; số placeholder tùy mẫu (Two Content, Comparison…)."),
    (("themes", "design/themes"), ("themes", "giao diện"),
     "Themes áp bộ màu–font–hiệu ứng thống nhất cho slide. Giúp bài nhìn chuyên nghiệp và nhất quán hơn chỉnh từng phần rời."),
    (("format background",), ("background", "apply to all"),
     "Format Background đổi màu/ảnh nền; Apply to All áp cho mọi slide, còn Close sau khi chọn màu thường chỉ ảnh hưởng slide hiện hành (theo thao tác đề nêu)."),
    (("duplicate slide",), ("duplicate", "nhân đôi"),
     "Duplicate Slide tạo bản sao slide đã chọn (kể cả nội dung/định dạng). Nhanh hơn tạo mới rồi copy từng đối tượng."),
    (("animation", "animations", "with previous", "thiết lập hiệu ứng"), ("animation", "with previous", "hiệu ứng"),
     "Animation gắn hiệu ứng xuất hiện/chuyển động cho đối tượng trên slide (chữ, ảnh…). Chọn hiệu ứng trong tab Animations; Start = With Previous cho chạy đồng thời với hiệu ứng trước."),
    (("autocorrect", "hiệu ứng điều chỉnh tự động", "loại bỏ các hiệu ứng điều chỉnh tự động"), ("autocorrect", "proofing", "option"),
     "AutoCorrect tự sửa chữ khi gõ; với tiếng Việt đôi khi sửa sai gây phiền. Vào File → Options → Proofing → AutoCorrect Options để xóa/tắt mục không cần."),
    (("xóa vĩnh viễn", "không cần phục hồi"), ("shift", "vĩnh viễn", "delete"),
     "Giữ Shift khi Delete (hoặc Shift + Delete) xóa vĩnh viễn, không đưa vào Recycle Bin. Chỉ dùng khi chắc chắn không cần khôi phục bằng thùng rác."),
    (("transitions",), ("transitions", "preview"),
     "Transitions là hiệu ứng chuyển trang giữa các slide. Preview trong tab Transitions để xem thử trước khi trình chiếu thật."),
    (("hide slide",), ("hide", "ẩn"),
     "Hide Slide ẩn slide khỏi trình chiếu nhưng vẫn giữ trong file để dùng sau. Hữu ích khi có nội dung dự phòng không muốn chiếu lần này."),
    (("f5", "shift + f5", "slide show", "from beginning"), ("f5", "shift + f5", "esc", "end show"),
     "F5 (hoặc Slide Show → From Beginning) chiếu từ đầu; Shift + F5 chiếu từ slide hiện tại; Esc hoặc End Show để thoát trình chiếu."),
    (("go to slide",), ("go to slide",),
     "Trong lúc chiếu, chuột phải → Go to Slide nhảy tới slide không liền kề. Tránh phải bấm Next liên tục khi cần quay lại mục cụ thể."),

    # --- Internet / Email ---
    (("isp",), ("internet service provider",),
     "ISP (Internet Service Provider) là nhà cung cấp dịch vụ kết nối Internet. Máy tính thường kết nối qua modem/hạ tầng rồi tới ISP để vào mạng toàn cầu."),
    (("www",), ("world wide web",),
     "WWW (World Wide Web) là dịch vụ Web trên Internet gồm các trang siêu văn bản liên kết với nhau. Truy cập bằng trình duyệt qua địa chỉ URL."),
    (("http",), ("siêu văn bản", "giao thức"),
     "HTTP là giao thức truyền tải siêu văn bản giữa trình duyệt và máy chủ Web. HTTPS là biến thể mã hóa an toàn hơn khi truyền dữ liệu nhạy cảm."),
    (("url",), ("uniform resource locator", "địa chỉ"),
     "URL (Uniform Resource Locator) là địa chỉ định danh tài nguyên trên Internet (thường bắt đầu bằng http/https). Gõ URL vào thanh địa chỉ để mở đúng trang."),
    (("ip",), ("địa chỉ ip",),
     "Địa chỉ IP định danh thiết bị trong mạng để gửi/nhận gói tin. Không có địa chỉ hợp lệ thì thiết bị khó tham gia giao tiếp mạng."),
    (("trình duyệt", "browser", "chrome", "firefox", "opera", "internet explorer"),
     ("trình duyệt", "duyệt web"),
     "Trình duyệt Web (Chrome, Firefox, Edge/IE, Opera…) hiển thị trang Web và chạy liên kết/script phía khách. Cần cài trình duyệt và có kết nối mạng để xem website."),
    (("thanh địa chỉ",), ("thanh địa chỉ",),
     "Thanh địa chỉ (address bar) nơi nhập URL để mở trang. Khác ô tìm kiếm của công cụ search dù một số trình duyệt tích hợp cả hai."),
    (("refresh", "tải lại"), ("refresh", "tải lại"),
     "Refresh/Reload tải lại trang từ máy chủ (hoặc cache) để cập nhật nội dung mới. Dùng khi trang lỗi tạm thời hoặc dữ liệu đã thay đổi."),
    (("stop",), ("ngừng tải", "stop"),
     "Nút Stop dừng tải trang đang mở dở. Hữu ích khi trang nặng/treo hoặc mở nhầm."),
    (("back", "forward", "backspace"), ("quay", "tiếp theo", "back"),
     "Back về trang trước trong lịch sử phiên; Forward đi tới lại nếu đã Back. Backspace thường cũng Back; Back không phải lệnh đóng cửa sổ trình duyệt."),
    (("favorites", "bookmark", "ưa thích"), ("favorites", "bookmark"),
     "Favorites/Bookmarks lưu địa chỉ trang hay dùng để mở lại nhanh. Add to Favorites (IE) hoặc Bookmark tương đương trên trình duyệt khác."),
    (("ctrl+t", "ctrl + t", "ctrl+w", "ctrl+tab"), ("tab",),
     "Trong trình duyệt kiểu IE/Chrome: Ctrl + T mở tab mới, Ctrl + W đóng tab, Ctrl + Tab/Ctrl + Shift + Tab chuyển tab. Làm việc nhiều trang trong một cửa sổ."),
    (("pop-up", "popup"), ("pop-up", "khó chịu"),
     "Cửa sổ pop-up thường là quảng cáo/thông báo chồng lên trang; ít khi phá hệ thống nhưng gây khó chịu. Có thể chặn và mở lại ngoại lệ khi cần."),
    (("ctrl + h", "history"), ("lịch sử", "history"),
     "Ctrl + H thường mở History — danh sách trang đã thăm. Có thể xóa lịch sử (Clear Recent History) để bảo mật/riêng tư trên máy dùng chung."),
    (("hyperlink", "siêu liên kết", "link"), ("liên kết", "hyperlink"),
     "Hyperlink (link) là liên kết đưa tới vị trí khác trên trang, trang khác hoặc tài nguyên khác khi người dùng kích chuột. Đây là nền tảng điều hướng của Web."),
    (("submit", "biểu mẫu", "form"), ("submit", "form"),
     "Sau khi điền form web, chọn Submit (hoặc tương đương) để gửi dữ liệu lên máy chủ xử lý. Không bấm gửi thì dữ liệu thường chưa được chuyển."),
    (("google", "tìm kiếm", "site:"), ("google", "\"", "site:"),
     "Công cụ tìm kiếm (Google…) giúp tìm URL/nội dung nhanh bằng từ khóa. Đặt cụm trong dấu nháy để khớp cụm từ; toán tử site: giới hạn kết quả trong một tên miền."),
    (("save picture", "lưu ảnh", "save as"), ("save", "ảnh"),
     "Chuột phải ảnh → Save picture as lưu riêng file ảnh; File → Save As lưu cả trang (có tùy chọn HTML only nếu không cần kèm ảnh)."),
    (("compose", "soạn"), ("compose",),
     "Compose mở cửa sổ soạn thư mới. Cần điền người nhận, Subject và nội dung trước khi Send."),
    (("reply", "reply to all"), ("reply", "trả lời"),
     "Reply trả lời người gửi; Reply to all trả lời cả người gửi và các người nhận khác trong thư. RE: trên Subject thường báo đây là thư trả lời."),
    (("forward",), ("forward", "chuyển tiếp"),
     "Forward chuyển tiếp thư (và thường cả đính kèm) tới người khác. Khác Reply vốn gửi phản hồi về người gửi gốc."),
    (("attachment", "đính kèm"), ("attachment",),
     "Attachment đính kèm file gửi cùng email. Nên quét virus file lạ trước khi mở để giảm rủi ro mã độc."),
    (("draft",), ("draft", "nháp"),
     "Thư soạn dở chưa Send thường nằm trong Drafts (Thư nháp). Có thể mở lại để sửa và gửi sau."),
    (("spam",), ("spam", "rác"),
     "Thư rác/không mong muốn thường vào thư mục Spam; có thể đánh dấu Spam để bộ lọc học và chặn tương tự. Không mở link/file đáng ngờ trong thư rác."),
    (("bcc",), ("bcc",),
     "BCC (Blind Carbon Copy) gửi ẩn danh sách người nhận phụ: mỗi người không thấy địa chỉ BCC khác. Dùng khi cần bảo mật danh sách người nhận."),
    (("inbox", "đã đọc", "chưa đọc"), ("in đậm", "inbox"),
     "Trong Inbox, thư chưa đọc thường in đậm; thư đã đọc chuyển về kiểu thường. Giúp nhận biết nhanh thư mới."),
    (("im", "instant messaging", "tin nhắn tức thời"), ("im", "instant", "thời gian thực"),
     "IM (Instant Messaging) trao đổi tin nhắn gần như thời gian thực. Phù hợp hỏi đáp nhanh hơn email, nhưng không phải kho lưu trữ lớn như dịch vụ lưu file."),
    (("https", "mua hàng", "an toàn"), ("https", "an toàn"),
     "Khi thanh toán/mua hàng online nên kiểm tra trang dùng HTTPS và đáng tin. HTTPS mã hóa đường truyền, giảm rủi ro bị nghe lén thông tin thẻ/mật khẩu."),
]


def score_concept(q: str, a: str, q_keys: tuple[str, ...], a_keys: tuple[str, ...]) -> int:
    """Require answer-side evidence whenever a_keys are declared (avoids greedy Q-only hits)."""
    qa = q + " " + a
    if q_keys:
        q_hits = [k for k in q_keys if k in q or k in qa]
        if not any(k in q for k in q_keys):
            # allow match if distinctive key appears in answer alone (rare)
            if not any(k in a for k in q_keys):
                return 0
        score = sum(len(k) for k in q_hits) + 2 * len(q_hits)
    else:
        score = 1

    if a_keys:
        a_hits = [k for k in a_keys if k in a]
        if not a_hits:
            return 0  # strict: answer must confirm the concept
        score += sum(len(k) for k in a_hits) * 3 + 5 * len(a_hits)
    else:
        # Q-only concepts are weaker
        score = score // 2
    return score


def find_concept_blurb(q: str, a: str) -> str | None:
    qf, af = fold(q), fold(a)
    best = None
    best_score = 0
    for q_keys, a_keys, blurb in CONCEPTS:
        sc = score_concept(qf, af, q_keys, a_keys)
        if sc > best_score:
            best_score = sc
            best = blurb
    if best_score >= 8:
        return best
    return None


# ---------------------------------------------------------------------------
# Pattern-based builders
# ---------------------------------------------------------------------------

SHORTCUT_MAP = {
    "ctrl+c": ("sao chép (Copy) nội dung đã chọn vào Clipboard", "Bản gốc vẫn còn cho đến khi bị cắt hoặc xóa"),
    "ctrl+x": ("cắt (Cut) nội dung vào Clipboard", "Dùng khi muốn di chuyển chứ không nhân bản"),
    "ctrl+v": ("dán (Paste) nội dung từ Clipboard", "Cần Copy hoặc Cut trước thì mới có gì để dán"),
    "ctrl+z": ("hoàn tác (Undo) thao tác vừa thực hiện", "Giúp sửa nhanh sai sót gần nhất"),
    "ctrl+y": ("làm lại (Redo) sau Undo", "Khôi phục thao tác vừa hoàn tác"),
    "ctrl+a": ("chọn tất cả đối tượng trong vùng đang active", "Áp dụng cho chữ, ô, file trong cửa sổ hiện hành"),
    "ctrl+s": ("lưu file hiện tại", "Ghi đè lên bản đã có đường dẫn lưu"),
    "ctrl+o": ("mở file đã có trên máy", "Hộp thoại Open cho chọn đường dẫn và kiểu file"),
    "ctrl+n": ("tạo tài liệu/workbook/presentation mới", "Nhanh hơn vào menu File → New"),
    "ctrl+p": ("mở lệnh in (Print)", "Có thể chọn máy in và tùy chọn trước khi in"),
    "ctrl+f": ("tìm kiếm trong tài liệu/trang", "Nhập từ khóa để nhảy tới vị trí khớp"),
    "ctrl+h": ("tìm và thay thế (Office) hoặc mở History (trình duyệt)", "Tùy phần mềm đang dùng mà chức năng khác nhau"),
    "ctrl+b": ("bật/tắt chữ đậm (Bold)", "Áp dụng cho vùng đang chọn"),
    "ctrl+i": ("bật/tắt chữ nghiêng (Italic)", "Áp dụng cho vùng đang chọn"),
    "ctrl+u": ("bật/tắt gạch chân (Underline)", "Áp dụng cho vùng đang chọn"),
    "ctrl+e": ("căn giữa đoạn/vùng chọn", "Thường dùng cho tiêu đề"),
    "ctrl+j": ("căn đều hai bên (Justify)", "Mép trái và phải thẳng hàng"),
    "ctrl+r": ("căn phải đoạn/vùng chọn", "Đẩy nội dung về phía phải"),
    "ctrl+l": ("căn trái đoạn/vùng chọn", "Kiểu căn mặc định của nhiều đoạn văn"),
    "ctrl+esc": ("mở menu Start", "Tương tự nhấn phím Windows"),
    "ctrl+tab": ("chuyển sang tab liền kề bên phải", "Dùng trong trình duyệt nhiều tab"),
    "ctrl+shift+tab": ("chuyển sang tab liền kề bên trái", "Duyệt ngược giữa các tab đang mở"),
    "ctrl+t": ("mở tab mới trong trình duyệt", "Giữ nhiều trang trong cùng một cửa sổ"),
    "ctrl+w": ("đóng tab hiện tại", "Không nhất thiết đóng cả cửa sổ trình duyệt"),
    "alt+f4": ("đóng cửa sổ/ứng dụng hiện hành", "Khác Alt+Tab chỉ chuyển cửa sổ"),
    "alt+tab": ("chuyển nhanh giữa các cửa sổ đang mở", "Giữ Alt rồi nhấn Tab để chọn"),
    "alt+printscreen": ("chụp cửa sổ đang active vào Clipboard", "Không kèm Alt thì thường chụp cả màn hình"),
    "windows+d": ("hiện Desktop (ẩn/hiện tạm các cửa sổ)", "Thuận tiện truy cập biểu tượng màn hình nền"),
    "shift+f5": ("trình chiếu từ slide hiện tại trong PowerPoint", "Khác F5 chiếu từ đầu bài"),
    "shift+delete": ("xóa vĩnh viễn, bỏ qua Recycle Bin", "Khó khôi phục bằng thùng rác"),
    "f1": ("mở trợ giúp Help", "Tra cứu lệnh ngay trong phần mềm"),
    "f2": ("đổi tên file/thư mục hoặc sửa nội dung ô Excel", "Tùy ngữ cảnh Explorer hay bảng tính"),
    "f4": ("đổi kiểu tham chiếu ô khi sửa công thức Excel", "Xoay vòng tương đối / tuyệt đối / hỗn hợp"),
    "f5": ("bắt đầu trình chiếu từ đầu trong PowerPoint", "Tương đương Slide Show → From Beginning"),
    "f9": ("tính toán/gỡ rối công thức đang chọn trong Excel", "Hữu ích khi kiểm tra từng phần biểu thức"),
    "f12": ("Save As — lưu thành tên hoặc định dạng mới", "Giữ được bản gốc nếu đổi tên/đường dẫn"),
}


def norm_shortcut_key(s: str) -> str:
    s = fold(s).replace(" ", "")
    s = s.replace("win+", "windows+")
    s = s.replace("prtSc".lower(), "printscreen")
    s = s.replace("printscreen", "printscreen")
    s = s.replace("prtsc", "printscreen")
    return s


def extract_shortcut(text: str) -> str | None:
    t = fold(text)
    candidates = re.findall(
        r"(?:ctrl|alt|shift|windows|win)\s*\+\s*[a-z0-9]+(?:\s*\+\s*[a-z0-9]+)*|f\d{1,2}",
        t,
    )
    if candidates:
        return norm_shortcut_key(candidates[0])
    return None


def lookup_shortcut(sc: str) -> tuple[str, str] | None:
    key = norm_shortcut_key(sc)
    if key in SHORTCUT_MAP:
        return SHORTCUT_MAP[key]
    # try without reordering
    for k, v in SHORTCUT_MAP.items():
        if norm_shortcut_key(k) == key:
            return v
    return None


def is_wrong_statement_question(q: str) -> bool:
    qf = fold(q)
    markers = (
        "phát biểu nào sau đây là sai",
        "phát biểu nào dưới đây là sai",
        "phát biểu nào là sai",
        "phát biểu nào chưa đúng",
        "chọn phát biểu sai",
        "phát biểu nào dưới đây là sai",
        "đâu là phát biểu sai",
        "câu nào sai",
        "phương pháp nào sau đây không",
        "thao tác nào sau đây không",
        "cách nào sau đây không",
    )
    return any(x in qf for x in markers)


def is_all_correct_answer(a: str) -> bool:
    af = fold(a)
    return ("tất cả" in af or "cả (1)" in af or "cả 3" in af or "cả ba" in af) and (
        "đúng" in af or "đáp án" in af or "(1)" in af or "(2)" in af
    )


def topic_phrase(q: str) -> str:
    q = clean_text(q)
    q = re.sub(r"\?+$", "", q).strip()
    for pref in (
        "Hãy cho biết ",
        "Hãy nêu ",
        "Hãy chọn ",
        "Hãy chỉ ra ",
        "Cho biết ",
        "Trong các ",
        "Trong Microsoft ",
        "Trong MS ",
        "Trong Powerpoint ",
        "Trong PowerPoint ",
        "Trong Excel ",
        "Trong bảng tính ",
        "Trong hệ điều hành ",
        "Trong trình duyệt ",
    ):
        if q.startswith(pref):
            q = q[len(pref) :]
            break
    if len(q) > 90:
        q = q[:87] + "…"
    return q


# Term blurbs used to teach from words appearing in the correct option.
TERM_BLURBS: list[tuple[str, str]] = [
    ("windows", "Windows là hệ điều hành phổ biến; thường được cài trước để máy có môi trường chạy phần mềm ứng dụng."),
    ("ms windows", "MS Windows là hệ điều hành; máy cần hệ điều hành trước khi dùng Word, Excel hay trình duyệt."),
    ("hệ điều hành", "Hệ điều hành quản lý phần cứng và tạo môi trường cho ứng dụng chạy."),
    ("recycle bin", "Recycle Bin (Thùng rác) giữ tạm file xóa từ ổ cứng để có thể Restore khi cần."),
    ("shortcut", "Shortcut là lối tắt trỏ tới đối tượng gốc; xóa shortcut không xóa chương trình/file gốc."),
    ("control panel", "Control Panel tập trung nhiều thiết lập hệ thống Windows (ngày giờ, chương trình, tài khoản…)."),
    ("clipboard", "Clipboard là bộ nhớ tạm giữ nội dung vừa Copy/Cut để Paste sang chỗ khác."),
    ("hyperlink", "Hyperlink gắn liên kết tới trang web, file hoặc vị trí khác khi người dùng kích chuột."),
    ("placeholder", "Placeholder là khung chỗ sẵn trên slide để nhập tiêu đề, nội dung hoặc media."),
    ("slide master", "Slide Master quy định định dạng/chỗ đặt chung cho nhiều slide trong bài."),
    ("animation", "Animation là hiệu ứng xuất hiện/chuyển động của đối tượng trên một slide."),
    ("transition", "Transition là hiệu ứng chuyển từ slide này sang slide khác khi trình chiếu."),
    ("vlookup", "VLOOKUP dò giá trị theo cột trong bảng và trả về dữ liệu ở cột chỉ định."),
    ("sumif", "SUMIF cộng các giá trị thỏa một điều kiện trên vùng tiêu chí."),
    ("countif", "COUNTIF đếm số ô thỏa điều kiện cho trước."),
    ("average", "AVERAGE tính trung bình cộng các giá trị số."),
    ("firewall", "Tường lửa lọc kết nối mạng theo chính sách, giảm truy cập trái phép."),
    ("tường lửa", "Tường lửa lọc kết nối mạng theo chính sách, giảm truy cập trái phép."),
    ("https", "HTTPS là HTTP có mã hóa, giúp truyền dữ liệu an toàn hơn trên Web."),
    ("url", "URL là địa chỉ định danh tài nguyên trên Internet, nhập vào thanh địa chỉ để mở trang."),
    ("isp", "ISP là nhà cung cấp dịch vụ kết nối Internet."),
    ("smtp", "Gửi nhận thư điện tử đi qua máy chủ thư; cần đăng nhập đúng tài khoản."),
    ("attachment", "Attachment là file đính kèm gửi cùng email."),
    ("spam", "Spam là thư rác/không mong muốn; nên đánh dấu và tránh mở link lạ."),
    ("bcc", "BCC gửi ẩn danh sách người nhận phụ, người nhận không thấy các địa chỉ BCC khác."),
    ("reply to all", "Reply to all trả lời cho người gửi và tất cả người nhận khác của thư gốc."),
    ("reply", "Reply trả lời người gửi thư; thường thêm tiền tố RE: trên dòng Subject."),
    ("forward", "Forward chuyển tiếp nội dung thư (và thường cả đính kèm) tới người khác."),
    ("draft", "Drafts lưu thư soạn dở chưa gửi để mở lại và hoàn thiện sau."),
    ("compose", "Compose mở cửa sổ soạn thư mới trước khi gửi."),
    ("bookmark", "Bookmark/Favorites lưu địa chỉ trang hay dùng để mở lại nhanh."),
    ("favorites", "Favorites/Bookmark lưu địa chỉ trang ưa thích trong trình duyệt."),
    ("refresh", "Refresh tải lại trang để cập nhật nội dung mới từ máy chủ."),
    ("modem", "Modem chuyển tín hiệu để máy tính kết nối tới hạ tầng mạng/ISP."),
    ("driver", "Driver giúp hệ điều hành điều khiển đúng thiết bị phần cứng."),
    ("antivirus", "Antivirus phát hiện và xử lý mã độc; cần cập nhật mẫu nhận diện thường xuyên."),
    ("unikey", "Unikey hỗ trợ gõ tiếng Việt; thường dùng Ctrl+Shift để chuyển Anh↔Việt."),
    ("times new roman", "Times New Roman là font thường được yêu cầu trong thể thức văn bản hành chính."),
    ("docx", "Đuôi .docx là định dạng mặc định của Word hiện đại (Office Open XML)."),
    ("xlsx", "Đuôi .xlsx là định dạng mặc định của Excel 2007 trở lên."),
    ("pptx", "Đuôi .pptx là định dạng mặc định của PowerPoint 2007 trở lên."),
    ("pdf", "PDF là định dạng tài liệu điện tử giữ bố cục ổn định khi xem/in trên nhiều máy."),
    ("footnote", "Footnote là chú thích gắn với vị trí đánh dấu, thường hiện ở cuối trang."),
    ("header", "Header là vùng đầu trang lặp lại trên các trang (số trang, tiêu đề…)."),
    ("footer", "Footer là vùng chân trang lặp lại thông tin phụ trợ."),
    ("portrait", "Portrait là hướng giấy/trang dọc — hướng in mặc định phổ biến."),
    ("landscape", "Landscape là hướng giấy/trang ngang, phù hợp bảng rộng hoặc slide."),
    ("wrap text", "Wrap Text cho phép chữ dài xuống dòng trong một ô Excel."),
    ("merge cells", "Merge Cells gộp nhiều ô thành một ô lớn, hay dùng cho tiêu đề bảng."),
    ("freeze panes", "Freeze Panes giữ cố định hàng/cột tiêu đề khi cuộn trang tính."),
    ("autocorrect", "AutoCorrect tự sửa chữ khi gõ; có thể tắt/xóa mục gây phiền trong Option/Proofing."),
    ("print preview", "Print Preview xem trước bố cục in để phát hiện lỗi trước khi in giấy."),
    ("encrypt", "Mã hóa bằng mật khẩu khóa file; không có mật khẩu đúng thì khó mở nội dung."),
    ("hibernate", "Hibernate lưu trạng thái xuống ổ cứng rồi gần như tắt máy để tiết kiệm điện."),
    ("sleep", "Sleep tạm dừng để tiết kiệm điện nhưng vẫn nuôi RAM, nên vẫn tiêu thụ một ít điện."),
]


def teach_terms(a: str) -> str | None:
    af = fold(a)
    hits: list[str] = []
    for key, blurb in TERM_BLURBS:
        # prefer whole-phrase / token-ish match to avoid 'reply' hitting 'reply to all' twice wrongly
        if key in af:
            # skip shorter key if a longer key already matched as superstring
            if any(key != k and key in k and k in af for k, _ in TERM_BLURBS):
                continue
            hits.append(blurb)
        if len(hits) >= 2:
            break
    if not hits:
        return None
    return " ".join(hits)


def explain_shortcut(a_clean: str, q_clean: str) -> str | None:
    sc = extract_shortcut(a_clean)
    # Only trust shortcut from answer; question may mention unrelated keys
    if not sc and re.search(r"(?:ctrl|alt|shift|f\d)", fold(a_clean)):
        sc = extract_shortcut(a_clean)
    if not sc:
        return None
    # Answer should look like a shortcut / include the keys
    if not extract_shortcut(a_clean) and len(a_clean) > 60:
        return None
    info = lookup_shortcut(sc)
    shown = clean_text(a_clean)
    shown = re.sub(r"^(bấm|nhấn|chọn|kích)\s+", "", shown, flags=re.I)
    if info:
        meaning, extra = info
        return (
            f"Tổ hợp/phím đúng là {shown}: dùng để {meaning}. "
            f"{extra}."
        )
    return (
        f"Tổ hợp/phím đúng là {shown}. "
        f"Đây là phím tắt thực hiện đúng thao tác được nêu trong câu hỏi; "
        f"thuộc nhóm phím cần thuộc khi thao tác Windows/Office/trình duyệt."
    )


def explain_menu_path(a_clean: str) -> str | None:
    if not (("/" in a_clean) or ("\\" in a_clean) or ("→" in a_clean) or ("-->" in a_clean) or (" chọn " in fold(a_clean) and ("vào " in fold(a_clean) or "tab " in fold(a_clean)))):
        return None
    if extract_shortcut(a_clean) and len(a_clean) < 25:
        return None
    return (
        f"Thao tác đúng đi theo đường lệnh: {clip_ans(a_clean, 130)}. "
        f"Mỗi tab/menu (File, Home, Insert, Data, View, Design…) nhóm một nhóm chức năng; "
        f"đi đúng chuỗi sẽ mở đúng công cụ cần dùng."
    )


def build_from_answer(module_id: int, q: str, a: str) -> str:
    """Teach from the correct option content when no stronger blurb matches."""
    a_clean = clean_text(a)
    q_clean = clean_text(q)
    qf, af = fold(q_clean), fold(a_clean)

    if is_wrong_statement_question(q_clean):
        return (
            f"Phải chọn phát biểu SAI: «{clip_ans(a_clean, 100)}». "
            f"Dạng câu này yêu cầu nhận diện nội dung không đúng kiến thức tin học. "
            f"So sánh với thực tế thao tác/định nghĩa chuẩn để loại trừ các ý đúng."
        )

    if is_all_correct_answer(a_clean):
        tip = topic_phrase(q_clean)
        return (
            f"Về {tip}, các ý được liệt kê đều đúng và bổ sung lẫn nhau. "
            f"Khi đề cho phương án “tất cả đều đúng/cả (1)(2)(3)”, hãy kiểm tra từng ý thành phần thay vì chọn một ví dụ đơn lẻ."
        )

    sc_explain = explain_shortcut(a_clean, q_clean)
    if sc_explain and (extract_shortcut(a_clean) or fold(a_clean).startswith("f")):
        return sc_explain

    menu_explain = explain_menu_path(a_clean)
    if menu_explain:
        term = teach_terms(a_clean)
        if term:
            return menu_explain + " " + term
        return menu_explain

    # Abbreviation / expansion
    if "viết tắt" in qf or (re.search(r"\b[A-Z]{2,}\b", a_clean) and " " in a_clean and len(a_clean.split()) <= 8):
        if re.search(r"[A-Za-z]", a_clean):
            return (
                f"Cụm đúng là «{clip_ans(a_clean)}». "
                f"Đây là dạng viết đầy đủ/ý nghĩa chuẩn của thuật ngữ viết tắt trong câu hỏi. "
                f"Tránh nhầm các cụm gần giống nhưng không đúng quy ước tin học."
            )

    if a_clean in {"#", "#####"} or a_clean.startswith("#") and len(a_clean) <= 8:
        return (
            f"Khi số quá dài so với độ rộng cột, Excel thường hiện {a_clean} (chuỗi dấu #). "
            f"Hãy kéo rộng cột hoặc giảm cỡ chữ/định dạng số để nhìn đủ giá trị — đây không phải mã lỗi công thức như #DIV/0!."
        )

    # Numeric / error codes
    compact = a_clean.replace(" ", "")
    if re.fullmatch(r"-?\d+([.,]\d+)?", compact) or a_clean in {
        "#DIV/0!", "#NAME?", "#REF!", "#VALUE!", "#REF", "#DIV/0",
    }:
        return (
            f"Kết quả đúng là {a_clean}. "
            f"Áp dụng đúng công thức/hàm, thứ tự ưu tiên toán tử và kiểu dữ liệu của từng đối số. "
            f"Các mã như #DIV/0!, #NAME?, #REF!, ##### báo lỗi chia 0, sai tên hàm, tham chiếu hỏng hoặc cột quá hẹp."
        )

    # File extension
    if any(x in qf for x in ("phần mở rộng", "đuôi", "định dạng mặc định", "định dạng của tên file")) or af in {
        "docx", ".docx", "xlsx", "pptx", "txt", "jpg", "pdf", "zip", "rar", "mp3", "wma",
    }:
        return (
            f"Phần mở rộng/định dạng đúng là {clip_ans(a_clean)}. "
            f"Đuôi file cho biết kiểu dữ liệu và chương trình phù hợp để mở. "
            f"Chọn sai định dạng dễ khiến file mở lỗi hoặc mất tương thích."
        )

    # Definition questions
    if any(x in qf for x in ("là gì", "nghĩa là", "định nghĩa", "được gọi là", "có nghĩa", "là?", "là ")):
        term = teach_terms(a_clean)
        core = sentence_case(clip_ans(a_clean, 140))
        if term:
            return f"{core}. {term}"
        return (
            f"{core}. "
            f"Hãy nắm đặc điểm cốt lõi trong định nghĩa này để phân biệt với các khái niệm gần nghĩa trong cùng chủ đề."
        )

    # How / which procedure
    if any(x in qf for x in ("làm thế nào", "làm như thế nào", "cách nào", "thao tác nào", "để ", "muốn ")):
        term = teach_terms(a_clean)
        base = (
            f"Cách đúng là: {clip_ans(a_clean, 130)}. "
            f"Thực hiện đúng thao tác/đúng công cụ sẽ ra kết quả đề yêu cầu."
        )
        if term:
            return base + " " + term
        return base + " Ghi nhớ vị trí lệnh và điều kiện áp dụng để làm bài thực hành nhanh hơn."

    # What is / which device software
    if any(x in qf for x in ("đâu là", "thiết bị nào", "phần mềm nào", "chức năng nào", "nút nào", "hàm nào")):
        term = teach_terms(a_clean)
        base = f"Đáp án đúng là «{clip_ans(a_clean, 100)}»."
        if term:
            return f"{base} {term}"
        return (
            f"{base} "
            f"Tên/đối tượng này đúng với vai trò được hỏi; hãy gắn với chức năng thực tế để khỏi nhầm nhóm tương tự."
        )

    term = teach_terms(a_clean)
    if term:
        return (
            f"Đáp án đúng hướng tới «{clip_ans(a_clean, 90)}». "
            f"{term}"
        )

    # Final teaching fallback — paraphrase answer, no filler slogans
    if len(a_clean) <= 50:
        return (
            f"Đáp án đúng là «{a_clean}». "
            f"Hãy gắn thuật ngữ/thao tác này với chức năng thực tế trong máy tính để phân biệt các phương án gần nghĩa."
        )
    return (
        f"Đáp án đúng khẳng định: {clip_ans(a_clean, 130)}. "
        f"Hiểu vì sao nội dung này đúng với tình huống đề (định nghĩa, điều kiện dùng hoặc kết quả thao tác) sẽ giúp làm các câu tương tự."
    )


def polish(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    banned = (
        "khớp với kiến thức chuẩn của bài",
        "các lựa chọn khác không chính xác",
        "thiếu đầy đủ",
    )
    for b in banned:
        text = text.replace(b, "")
    text = re.sub(r"\s+", " ", text).strip()
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    if len(parts) > 4:
        parts = parts[:4]
    if len(parts) == 1:
        parts.append("Ghi nhớ đúng thao tác/khái niệm này giúp tránh nhầm với chức năng gần nghĩa trong cùng phần mềm.")
    text = " ".join(parts)
    if text and text[-1] not in ".!?…":
        text += "."
    return text


def build_explain(module_id: int, q: dict) -> str:
    ans_letter = q["answer"]
    raw_ans = q["options"].get(ans_letter, "")
    a = clean_text(raw_ans)
    text = clean_text(q["text"])

    # Priority 1: wrong-statement / all-correct / clear shortcut / menu — via builder
    if is_wrong_statement_question(text) or is_all_correct_answer(a):
        return polish(build_from_answer(module_id, text, a))

    if extract_shortcut(a) and len(a) < 70:
        sc_e = explain_shortcut(a, text)
        if sc_e:
            return polish(sc_e)

    blurb = find_concept_blurb(text, a)
    if blurb:
        return polish(blurb)

    return polish(build_from_answer(module_id, text, a))


def regenerate() -> tuple[int, list[tuple[int, int, str]]]:
    with JSON_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    samples: list[tuple[int, int, str]] = []

    for mod in data["modules"]:
        mid = mod["id"]
        for q in mod["questions"]:
            new_explain = build_explain(mid, q)
            q["explain"] = new_explain
            count += 1
            if q["id"] in (1, 50, 100):
                samples.append((mid, q["id"], new_explain))

    with JSON_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # quiz-data.js
    js = "window.QUIZ_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    JS_PATH.write_text(js, encoding="utf-8", newline="\n")

    return count, samples


def main() -> None:
    count, samples = regenerate()
    print(f"Rewrote explains: {count}")
    print(f"Updated: {JSON_PATH}")
    print(f"Updated: {JS_PATH}")
    print("\n--- Spot-check (q1, q50, q100 each module) ---")
    for mid, qid, expl in samples:
        print(f"\n[M{mid} Q{qid}] {expl}")


if __name__ == "__main__":
    main()
