# GI Survival

Trò chơi sinh tồn 2D viết bằng Python và Pygame. Người chơi điều khiển nhân vật trên bản đồ rộng, chiến đấu với quái vật, thu thập tài nguyên, nâng cấp chỉ số và theo dõi tiến trình theo thời gian thực.

## Điểm nổi bật

- Bản đồ thế giới, camera theo nhân vật, va chạm chướng ngại vật và chế độ toàn màn hình.
- Quái vật slime với cấp độ, máu và tốc độ xuất hiện tăng theo thời gian.
- Hệ thống vàng, XP, hồi sinh và nâng cấp sát thương, máu, tốc độ, tầm đánh, tốc độ đánh, thu nhập vàng/XP, bán kính nhặt đồ và tỉ lệ chí mạng.
- `Algorithm Arena` để quan sát và so sánh cách quái vật di chuyển với Direct, A*, BFS, Dijkstra, Greedy và Hill Climbing.
- Tài nguyên hình ảnh, âm thanh, font, sprite và dữ liệu điều khiển nằm trực tiếp trong repository.

## Cấu trúc chính

- `main.py`: vòng lặp game, màn hình, nhân vật, quái vật và giao diện.
- `move.py`: các thuật toán tìm đường, lưới chướng ngại vật và thống kê đường đi.
- `slime4.py`: hành vi/thành phần slime bổ sung.
- `sprites/`, `images/`, `sounds/`, `fonts/`, `icons/`: tài nguyên game.
- `controls.json` và `highscores.json`: dữ liệu điều khiển và điểm số cục bộ.

## Yêu cầu và cách chạy

- Python 3.10 trở lên.
- Pygame.

```powershell
pip install pygame
python -u main.py
```

Chạy lệnh tại thư mục gốc của project để chương trình tìm đúng các file tài nguyên.

## Phím tắt

- `F11`: bật/tắt toàn màn hình.
- `Esc`: mở hoặc đóng menu tạm dừng.
- `Tab`: mở bảng đổi thuật toán slime.
- `F3`: bật/tắt hiển thị debug đường đi.
- Từ menu chính, chọn **Algorithm Arena** để vào chế độ so sánh thuật toán.
