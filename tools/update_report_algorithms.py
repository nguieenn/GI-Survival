from copy import deepcopy
from pathlib import Path
from shutil import copy2

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


ROOT = Path.cwd()
REPORT = next(ROOT.parent.glob("GI_Survival*.docx"))
BACKUP = REPORT.with_name(REPORT.stem + "_backup_truoc_bo_sung_thuat_toan.docx")


def paragraph_index(doc, text):
    for idx, para in enumerate(doc.paragraphs):
        if para.text.strip() == text:
            return idx
    raise ValueError(f"Khong tim thay doan: {text}")


def insert_paragraph_after(paragraph, text="", style=None):
    new_p = deepcopy(paragraph._p)
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    new_para.clear()
    if style:
        new_para.style = style
    new_para.add_run(text)
    return new_para


def add_after(paragraph, items):
    current = paragraph
    for style, text in items:
        current = insert_paragraph_after(current, text, style)
    return current


def enable_field_update_on_open(doc):
    settings = doc.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


THEORY_SECTIONS = [
    ("Heading 2", "1.5. Thuật toán Tìm kiếm theo chiều rộng (BFS)"),
    ("Heading 3", "1.5.1. Bản chất và nguyên lý hoạt động"),
    (
        "Normal",
        "Thuật toán Tìm kiếm theo chiều rộng (Breadth-First Search - BFS) là thuật toán duyệt đồ thị theo từng lớp. "
        "Từ trạng thái xuất phát, BFS mở rộng tất cả các trạng thái ở khoảng cách 1, sau đó đến khoảng cách 2, rồi tiếp tục "
        "cho đến khi gặp trạng thái đích. Cách duyệt theo lớp giúp BFS tìm được đường đi có số bước ít nhất trong đồ thị "
        "không trọng số.",
    ),
    (
        "Normal",
        "Trong bài toán tìm đường của GI Survival, bản đồ được mô hình hóa thành lưới ô vuông. Mỗi ô đi được là một đỉnh, "
        "các ô láng giềng là các cạnh. BFS phù hợp để minh họa quá trình lan truyền tìm kiếm vì số node được duyệt thường "
        "rất rõ ràng trên phần debug đường đi.",
    ),
    ("Heading 3", "1.5.2. Cấu trúc dữ liệu và pseudocode"),
    ("Normal", "BFS sử dụng hàng đợi (queue) để bảo đảm trạng thái nào được phát hiện trước sẽ được mở rộng trước:"),
    ("Normal", "Algorithm BFS(start, goal):"),
    ("Normal", "queue ← hàng đợi chứa start"),
    ("Normal", "visited ← tập chứa start"),
    ("Normal", "came_from ← rỗng"),
    ("Normal", "while queue không rỗng:"),
    ("Normal", "    current ← queue.pop_front()"),
    ("Normal", "    if current = goal: return reconstruct_path(came_from, current)"),
    ("Normal", "    for each neighbor của current:"),
    ("Normal", "        if neighbor hợp lệ và neighbor ∉ visited:"),
    ("Normal", "            visited.add(neighbor)"),
    ("Normal", "            came_from[neighbor] ← current"),
    ("Normal", "            queue.push_back(neighbor)"),
    ("Normal", "return FAILURE"),
    ("Heading 3", "1.5.3. Độ phức tạp và đặc điểm"),
    (
        "Normal",
        "Nếu gọi V là số đỉnh và E là số cạnh, độ phức tạp thời gian của BFS là O(V + E), độ phức tạp không gian là O(V). "
        "Ưu điểm của BFS là đơn giản, đầy đủ và tìm được đường ngắn nhất theo số cạnh trong đồ thị không trọng số. Nhược điểm "
        "là BFS không dùng heuristic nên có thể duyệt rất nhiều node trước khi đến mục tiêu.",
    ),
    ("Heading 2", "1.6. Thuật toán Dijkstra"),
    ("Heading 3", "1.6.1. Bản chất và nguyên lý hoạt động"),
    (
        "Normal",
        "Dijkstra là thuật toán tìm đường đi ngắn nhất từ một nguồn đến các đỉnh còn lại trong đồ thị có trọng số không âm. "
        "Khác với BFS chỉ coi mọi bước đi có chi phí như nhau, Dijkstra luôn ưu tiên mở rộng trạng thái có chi phí tích lũy "
        "g(n) nhỏ nhất.",
    ),
    (
        "Normal",
        "Trong game 2D cho phép di chuyển chéo, Dijkstra có thể gán chi phí 10 cho bước ngang/dọc và 14 cho bước chéo. "
        "Nhờ đó đường đi có thể phản ánh tốt hơn khoảng cách thực tế so với BFS.",
    ),
    ("Heading 3", "1.6.2. Cấu trúc dữ liệu và pseudocode"),
    ("Normal", "Dijkstra thường sử dụng hàng đợi ưu tiên để lấy node có chi phí nhỏ nhất:"),
    ("Normal", "Algorithm DIJKSTRA(start, goal):"),
    ("Normal", "open_heap ← priority queue với (0, start)"),
    ("Normal", "distance[start] ← 0"),
    ("Normal", "came_from ← rỗng"),
    ("Normal", "while open_heap không rỗng:"),
    ("Normal", "    current ← node có distance nhỏ nhất"),
    ("Normal", "    if current = goal: return reconstruct_path(came_from, current)"),
    ("Normal", "    for each neighbor của current:"),
    ("Normal", "        new_cost ← distance[current] + cost(current, neighbor)"),
    ("Normal", "        if new_cost < distance[neighbor]:"),
    ("Normal", "            distance[neighbor] ← new_cost"),
    ("Normal", "            came_from[neighbor] ← current"),
    ("Normal", "            open_heap.push(new_cost, neighbor)"),
    ("Normal", "return FAILURE"),
    ("Heading 3", "1.6.3. So sánh với A*"),
    (
        "Normal",
        "Dijkstra có thể xem là trường hợp đặc biệt của A* khi h(n) = 0. Vì không có heuristic định hướng, Dijkstra bảo đảm "
        "tối ưu nhưng thường mở rộng nhiều node hơn A*. Trong GI Survival, Dijkstra hữu ích để làm mốc so sánh giữa thuật toán "
        "tìm tối ưu không heuristic và thuật toán tối ưu có heuristic.",
    ),
    ("Heading 2", "1.7. Thuật toán Greedy Best-First Search"),
    ("Heading 3", "1.7.1. Bản chất và hàm đánh giá"),
    (
        "Normal",
        "Greedy Best-First Search là thuật toán tìm kiếm ưu tiên node có vẻ gần đích nhất theo heuristic h(n). Khác với A*, "
        "Greedy không cộng thêm chi phí đã đi g(n), mà chỉ dùng h(n) để ra quyết định. Vì vậy, thuật toán thường di chuyển "
        "rất nhanh về phía mục tiêu nhưng không bảo đảm đường đi tối ưu.",
    ),
    (
        "Normal",
        "Trong môi trường có nhiều vật cản, Greedy có thể bị hấp dẫn bởi hướng nhìn có vẻ gần đích nhưng lại dẫn vào ngõ cụt. "
        "Điều này làm thuật toán rất phù hợp để so sánh trực quan với A*, BFS và Dijkstra trong Algorithm Arena.",
    ),
    ("Heading 3", "1.7.2. Pseudocode"),
    ("Normal", "Algorithm GREEDY_BEST_FIRST(start, goal):"),
    ("Normal", "open_heap ← priority queue với (h(start), start)"),
    ("Normal", "visited ← tập rỗng"),
    ("Normal", "came_from ← rỗng"),
    ("Normal", "while open_heap không rỗng:"),
    ("Normal", "    current ← node có h(n) nhỏ nhất"),
    ("Normal", "    if current = goal: return reconstruct_path(came_from, current)"),
    ("Normal", "    visited.add(current)"),
    ("Normal", "    for each neighbor của current:"),
    ("Normal", "        if neighbor hợp lệ và neighbor ∉ visited:"),
    ("Normal", "            came_from[neighbor] ← current"),
    ("Normal", "            open_heap.push(h(neighbor), neighbor)"),
    ("Normal", "return FAILURE"),
    ("Heading 3", "1.7.3. Độ phức tạp và nhận xét"),
    (
        "Normal",
        "Trong trường hợp xấu, Greedy vẫn có thể phải duyệt nhiều node, nhưng trong thực tế thường nhanh hơn BFS do được "
        "heuristic định hướng. Đổi lại, đường đi có thể dài hơn hoặc dễ mắc kẹt hơn A* vì thuật toán bỏ qua chi phí đã đi.",
    ),
    ("Heading 2", "1.8. Di chuyển trực tiếp (Direct Chase)"),
    ("Heading 3", "1.8.1. Bản chất"),
    (
        "Normal",
        "Direct Chase là chiến lược di chuyển đơn giản nhất: quái vật lấy vector từ vị trí hiện tại đến người chơi, chuẩn hóa "
        "vector đó rồi di chuyển theo hướng thẳng đến mục tiêu. Đây không phải thuật toán tìm đường đầy đủ trên đồ thị, nhưng "
        "là hành vi nền quan trọng để so sánh với các thuật toán có xử lý vật cản.",
    ),
    ("Heading 3", "1.8.2. Pseudocode"),
    ("Normal", "Algorithm DIRECT_CHASE(monster, target):"),
    ("Normal", "dx ← target.x - monster.x"),
    ("Normal", "dy ← target.y - monster.y"),
    ("Normal", "distance ← sqrt(dx² + dy²)"),
    ("Normal", "if distance > 0:"),
    ("Normal", "    monster.x ← monster.x + speed * dx / distance"),
    ("Normal", "    monster.y ← monster.y + speed * dy / distance"),
    ("Heading 3", "1.8.3. Vai trò trong GI Survival"),
    (
        "Normal",
        "Direct Chase có chi phí tính toán rất thấp, gần như O(1) cho mỗi lần cập nhật. Tuy nhiên, nó không tự tìm đường vòng "
        "qua chướng ngại vật. Trong GI Survival, Direct Chase được dùng như thuật toán nền, đồng thời làm mốc so sánh để thấy "
        "giá trị của các thuật toán pathfinding phức tạp hơn.",
    ),
]


IMPLEMENTATION_SECTIONS = [
    ("Heading 2", "2.6. Phân tích thuật toán BFS trong GI Survival"),
    ("Heading 3", "2.6.1. Cách triển khai"),
    (
        "Normal",
        "BFS được triển khai trong move.py dưới dạng một lớp pathfinder dùng chung cơ chế lưới với A*. Khi quái vật cần tính "
        "đường, vị trí hiện tại và vị trí mục tiêu được chuyển từ tọa độ pixel sang tọa độ ô lưới, sau đó thuật toán duyệt "
        "theo hàng đợi để tìm đường đi theo số bước ngắn nhất.",
    ),
    ("Heading 3", "2.6.2. Vai trò trong game"),
    (
        "Normal",
        "Trong chế độ chơi chính và Algorithm Arena, BFS giúp thể hiện rõ quá trình mở rộng node theo lớp. Do không có heuristic, "
        "BFS thường duyệt nhiều node hơn A* nhưng dễ quan sát và dễ giải thích về mặt học thuật.",
    ),
    ("Heading 2", "2.7. Phân tích thuật toán Dijkstra trong GI Survival"),
    ("Heading 3", "2.7.1. Cách triển khai"),
    (
        "Normal",
        "Dijkstra trong GI Survival sử dụng hàng đợi ưu tiên và chi phí di chuyển khác nhau cho hướng ngang/dọc và hướng chéo. "
        "Mỗi lần phát hiện đường đi rẻ hơn đến một ô, thuật toán cập nhật chi phí và lưu lại ô cha để tái tạo đường đi cuối cùng.",
    ),
    ("Heading 3", "2.7.2. Vai trò trong game"),
    (
        "Normal",
        "Dijkstra phù hợp để so sánh với A*: cả hai đều tìm đường tối ưu theo chi phí, nhưng A* dùng thêm heuristic để giảm số "
        "node cần mở rộng. Vì vậy, khi quan sát bảng thống kê nodes và time, Dijkstra thường có xu hướng nặng hơn A* trên cùng bản đồ.",
    ),
    ("Heading 2", "2.8. Phân tích thuật toán Greedy Best-First Search trong GI Survival"),
    ("Heading 3", "2.8.1. Cách triển khai"),
    (
        "Normal",
        "Greedy Best-First Search dùng cùng cấu trúc hàng đợi ưu tiên như A*, nhưng khóa ưu tiên chỉ là heuristic h(n) đến mục tiêu. "
        "Trong triển khai, thuật toán ưu tiên ô có khoảng cách ước lượng nhỏ nhất đến người chơi, nhờ đó phản ứng nhanh và thường "
        "cho cảm giác quái vật lao thẳng về phía mục tiêu.",
    ),
    ("Heading 3", "2.8.2. Ưu điểm và hạn chế trong game"),
    (
        "Normal",
        "Ưu điểm của Greedy là tốc độ và số node duyệt thấp trong các bản đồ thoáng. Hạn chế là thuật toán không xét chi phí đã đi, "
        "nên có thể chọn hướng tưởng gần nhưng thực tế phải vòng xa hơn. Đây là điểm làm Greedy trở nên trực quan khi so sánh trong Arena.",
    ),
    ("Heading 2", "2.9. Phân tích chiến lược Direct Chase trong GI Survival"),
    ("Heading 3", "2.9.1. Cách triển khai"),
    (
        "Normal",
        "Direct Chase được triển khai bằng cách tính vector hướng từ quái vật đến người chơi gần nhất rồi cập nhật vị trí theo vector đó. "
        "Chiến lược này không cần open list, closed list hay lưới tìm đường, nên chi phí xử lý rất thấp.",
    ),
    ("Heading 3", "2.9.2. Vai trò trong hệ thống thuật toán"),
    (
        "Normal",
        "Trong GI Survival, Direct Chase đóng vai trò thuật toán cơ sở. Nó giúp quái vật vẫn có hành vi truy đuổi đơn giản khi không cần "
        "xử lý vật cản phức tạp, đồng thời là mốc so sánh để đánh giá lợi ích của A*, BFS, Dijkstra, Greedy và Hill Climbing.",
    ),
]


def main():
    if not BACKUP.exists():
        copy2(REPORT, BACKUP)

    doc = Document(REPORT)

    # Avoid duplicating content if the script is accidentally run twice.
    all_text = "\n".join(p.text for p in doc.paragraphs)
    if "1.5. Thuật toán Tìm kiếm theo chiều rộng (BFS)" not in all_text:
        ch2_idx = paragraph_index(doc, "CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG")
        add_after(doc.paragraphs[ch2_idx - 1], THEORY_SECTIONS)

    doc = Document(REPORT) if False else doc
    all_text = "\n".join(p.text for p in doc.paragraphs)
    if "2.6. Phân tích thuật toán BFS trong GI Survival" not in all_text:
        future_idx = paragraph_index(doc, "2.6. Hướng phát triển trong tương lai")
        doc.paragraphs[future_idx].text = "2.10. Hướng phát triển trong tương lai"
        add_after(doc.paragraphs[future_idx - 1], IMPLEMENTATION_SECTIONS)

    enable_field_update_on_open(doc)
    doc.save(REPORT)
    print(REPORT)
    print(BACKUP)


if __name__ == "__main__":
    main()
