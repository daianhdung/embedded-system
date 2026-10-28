# Quan sát model thật: webcam, confidence và báo giả

Model YOLOv8n lửa/khói đã được tải và nạp thành công trên máy người dùng. Model chạy được chưa đồng nghĩa đã được đánh giá đủ. Chế độ dưới đây không có kết nối MQTT, không điều khiển ESP32/Wokwi và không ghi PASS vào bảng nghiệm thu.

## Chạy ngay

Terminal tại thư mục `firmware`, dừng chương trình camera cũ bằng Ctrl+C trước:

```sh
.venv-ai/bin/python tools/ai_observe.py
```

Mặc định camera 0, CPU, kích thước xử lý 640. Máy hiện tại đã có dependency. Khi dựng lại môi trường Python 3.12 trên Mac ARM64, dùng `tools/requirements-ai.txt` để cài các phiên bản đã thử; weights tải riêng theo [manifest](../models/fire-smoke-yolov8n.manifest.json). Không cần cài lại để chạy lệnh trên máy hiện tại.

Cửa sổ vẽ khung và confidence của từng phát hiện, kèm dòng `MQTT OFF`, trạng thái và ngưỡng. Chọn cửa sổ camera rồi nhấn **S** để lưu ảnh của khung đang xử lý; **Q** hoặc Ctrl+C trong terminal để thoát. Snapshot có tên theo frame, không ghi đè lần trước. Chương trình không tự lưu hình/video của phòng; chỉ lưu ảnh khi nhấn S. Log từng frame vẫn được ghi để xem lại các nhận nhầm thoáng qua.

## Đọc kết quả

| Trạng thái | Nghĩa |
|---|---|
| `BELOW_THRESHOLD` | Có vùng vượt ngưỡng hiển thị 0,25, nhưng không vùng nào đủ ngưỡng chọn 0,8 |
| `ABOVE_THRESHOLD` | Có dự đoán đủ ngưỡng chọn; vẫn chỉ quan sát, chưa gửi MQTT hoặc kết luận báo động đúng |
| `NO_DETECTION` | Không có vùng vượt ngưỡng hiển thị; không có nghĩa chắc chắn an toàn |
| `STALE` | Một lần suy luận mất từ 15 giây; không trả dự đoán để phát |

Ví dụ tóc bị nhận `smoke=0.360` sẽ hiện `BELOW_THRESHOLD`. Ảnh lửa trước có `fire=0.426` cũng bị loại bởi cùng ngưỡng. Không tăng/giảm ngưỡng chỉ để một ảnh đạt; ngưỡng 0,8 hiện giữ theo firmware và chưa được hiệu chỉnh bằng tập kiểm thử.

Nếu có cả lửa và khói vượt ngưỡng, chọn lửa; nếu lửa dưới ngưỡng nhưng khói đủ ngưỡng thì chọn khói. Không có vùng đủ ngưỡng trả `None` (unknown), không tự tạo `binh_thuong`. Chưa thêm lọc nhiều frame: nhận nhầm kéo dài vẫn là hạn chế cần đo và xử lý sau.

Terminal cập nhật khoảng mỗi giây để không cuộn quá nhanh. Các lần nhận nhầm ngắn có thể không xuất hiện trong terminal nhưng có trong JSONL.

## File được lưu ở đâu?

Mỗi lần chạy tạo thư mục mới `runs/ai-observe-<UTC>/`:

- `observations.jsonl`: START (weights hash, ngưỡng, cấu hình); FRAME (nhãn, confidence, tọa độ, thời điểm sau đọc frame, thời gian suy luận, kết quả chọn); SNAPSHOT và STOP/ERROR.
- `frame-00000123.jpg`: ảnh khi nhấn S; đối chiếu bằng `frame_id` trong log.

Các file `runs/` được Gitignore và nằm trên máy. `read_utc_ms` là thời điểm phần mềm đọc xong frame, không phải lúc camera phơi sáng; `inference_ms` không phải độ trễ toàn hệ thống. Không tuyên bố realtime từ con số này.

Đọc lại các frame có phát hiện, không mở camera:

```sh
.venv-ai/bin/python - <<'PY'
from pathlib import Path
import json

folder = max(Path('runs').glob('ai-observe-*'), key=lambda p: p.stat().st_mtime)
print('Log:', folder / 'observations.jsonl')
for line in (folder / 'observations.jsonl').read_text().splitlines():
    row = json.loads(line)
    if row['event'] == 'FRAME' and row['detections']:
        labels = ', '.join(f"{d['label']}={d['confidence']:.3f}" for d in row['detections'])
        print(row['frame_id'], row['utc'], row['status'], labels)
PY
```

Không cần gửi cả log dài: chọn ảnh nhận nhầm và vài dòng tương ứng. Dữ liệu phòng/camera chỉ lưu local; chưa đưa ảnh cá nhân vào repo hoặc dataset huấn luyện.

## Thử file ảnh/video thay webcam

```sh
.venv-ai/bin/python tools/ai_observe.py --source runs/ai-inputs/test.jpg --headless
.venv-ai/bin/python tools/ai_observe.py --source runs/your-video.mp4
```

Ảnh đơn tạo `image-result.jpg` và kết thúc ngay. Video hết thì dừng; camera đọc lỗi thì ghi ERROR và thoát, không báo an toàn. Có thể dùng `--duration 60` để chạy tối đa khoảng 60 giây (không ngắt giữa một lần đọc/suy luận bị chặn), hoặc `--out runs/ten-luot-moi`; thư mục đã tồn tại bị từ chối.

## Plugin tích hợp sau

`tools/yolo_plugin.py` cung cấp `predict(frame_bgr)` đúng giao diện adapter đã có: nạp model một lần, trả Prediction hoặc None. `ai_observe.py` dùng cùng phần suy luận để xem các phát hiện thấp hơn ngưỡng. Chưa tự khởi động publisher, chưa thay firmware và chưa chỉnh threshold/TTL/ACK. Bước sau là xem log báo giả/độ trễ rồi mới quyết định lọc thời gian và nối MQTT.

Nguồn: [model card và giấy phép do tác giả công bố](https://huggingface.co/rabahdev/fire-smoke-yolov8n), [Ultralytics predict](https://docs.ultralytics.com/modes/predict/). Metrics của tác giả không được coi là kết quả đánh giá của nhóm.

## Kiểm tra model→MQTT→ESP khi confidence thấp

Sau khi replay chạy đúng, có thể dùng plugin chẩn đoán `yolo_plugin:predict_raw` thay cho `yolo_plugin:predict`. Không cần build firmware. Dừng publisher cũ, đưa hệ thống về NORMAL trước khi thử:

```sh
.venv-ai/bin/python tools/ai_publish.py \
  --backend plugin --plugin yolo_plugin:predict_raw --source 0 \
  --model-id rabahdev-fire-smoke-yolov8n-13017fe8 --interval 1 \
  --wokwi-clock --expected-firmware-id R7-ff4ea6a0f5395c1c
```

Plugin mặc định `predict` vẫn chỉ phát dự đoán đủ0,8. Plugin `predict_raw` ưu tiên kết quả đủ0,8; khi chưa có, nó gửi một phát hiện từ0,25 với confidence thật để kiểm tra đường truyền. Không có box hoặc stale vẫn không phát; không tạo nhãn bìnhthường. Publisher in thêm `meets_confidence_threshold` để biết điểm có vượt0,8 chưa.

Ví dụ tóc bị nhận smoke0,36: bản tin ghi `khoi`/0,36, ESP tăng Nhan nhưng AIlevel0, không nâng báo động. Đây vẫn là nhận nhầm của model, không trở thành kết quả AI đúng vì MQTT gửi được. Firmware hiện coi bản tin dưới0,8 là AIlevel0; nếu đang có AIlevelcao trước đó, bản tin thấp có thể đưa FSM sang RECOVERY. Vì vậy đây là chế độ chẩn đoán truyềntin, không phải chính sách lọc nhiễu đã được đánh giá. Luật local nguy hiểm, timeout vàACK vẫn có hiệu lực. Nếu dự đoán thật đạt0,8, chế độ này vẫn có thể kích tải như plugin thường.
