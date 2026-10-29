# Dữ liệu, đánh giá và fine-tune AI

Nhóm chưa có dữliệu gánnhãn. Modelpretrained đãnạp/chạycamera; chưa có metricsđộclập và chưa traintrongđồán. Không lấy kếtquảtácgiảmodel hoặc các ảnhthử tay làmmetrics của nhóm.

## Chuẩn bị manifest

Copy tools/examples/dataset-manifest.template.json tới thưmục dataset local. Điền nguồn/license/version thật; mỗi mẫu có:

```json
{"path":"images/fire-01.jpg","label":"lua","group":"video-A","split":"test"}
```

Labels: lua/khoi/binh_thuong; split train/val/test. Path tươngđối manifest. Group là video/nguồn gốc để ngăn framecùngvideo rò sangtập khác. Không dùng ảnh tóc/phòng cá nhân cho dataset hoặcđưa vào repo nếu chưa cóchủđích. Bổsung ảnh nền/khó và ghi annotationprovenance. Trường independent_from_pretrained_training chỉ đặttrue khi đã xácminh nguồn; tảiảnh từD-Fire cóthể trùng dữliệu model đãhọc.

Audit không inference:

```sh
.venv-ai/bin/python tools/evaluate_ai.py --manifest datasets/manifest.json --audit-only
```

Tool từchối manifesttrống/placeholder, ảnhthiếu, pathsduplicate, group xuyênsplit và contenthash trùngxuyênsplit. Near-duplicate/ảnhcùngscenekhácfile cần người chuẩn bị dữliệu xửlý; hash không tự phát hiện hết. Report có sốảnh mỗi nhãn/tập và cờ yêu cầu200ảnh/lớp; không thay luật chia tập/đánhgiá của thầy.

## Đánh giá quyết định cấp ảnh

```sh
.venv-ai/bin/python tools/evaluate_ai.py --manifest datasets/manifest.json --split test --threshold 0.8
```

Đọc ảnhvàchạy weights thật local, khôngMQTT. Lưu auditedmanifest, từngdựđoán/confidence/hash, confusionmatrix (cóunknown), precision/recall theo nhãn, coverage vàtỉlệ báogiả trên nền. Detector no-box vẫnunknown nên không được tự cộng thành đúngbinh_thuong. Đây là image-level decision metrics, không phải bounding-boxmAP hoặc260lượt nghiệmthu. Timestamp/inference làPC, mẫuđầu cówarmup. Không tunengưỡng trên test rồi tuyênbốtestđộclập: tune trênval, chốt config, sauđó test.

Để đo mAP cần datasetYOLO cóboxannotation đúng. Dùng API validation chínhthức sau audit/đốichiếu split:

```sh
.venv-ai/bin/yolo val model=models/fire-smoke-yolov8n.pt data=datasets/data.yaml split=test device=cpu project=runs name=detector-eval
```

Lưu weights hash/config/datasetlicense cùngreport. Không tự nhận mAP85% nếu chưa đo.

## Fine-tune khi đã có annotations

```sh
.venv-ai/bin/python tools/train_ai.py --manifest datasets/manifest.json --data datasets/data.yaml --epochs 50 --device cpu
```

YOLO YAML phải có các thưmục train/val/test, names0=smoke/1=fire. Tool đốichiếu tậpảnh YAML với manifest đãaudit, ghi config/seed42/hash. Cần thêm kiểmtra chấtlượngbox, tínhđúngnhãn vàtrainingprovenance; côngcụ không chứngthực annotation của người khác. Training không tự đánhPASS, không tựđổi model đangpublish. Đánhgiáweights mới trên test riêng trước khi thay manifest/version.

## Lọc thời gian tùy chọn

```sh
.venv-ai/bin/python tools/ai_publish.py --backend plugin --plugin yolo_plugin:predict --source 0 --model-id rabahdev-fire-smoke-yolov8n-13017fe8 --interval 1 --wokwi-clock --expected-firmware-id R7-ff4ea6a0f5395c1c --confirm-seconds 2 --confirm-frames 3 --confirm-max-gap 5
```

Cần cùngnhãn đủconfidence0,8, ít nhất3framevà kéo dàiít nhất2sPC, gapkhôngquá5s. Unknown/đổinhãn/confidencethấp reset chuỗi; khiđủ chỉphát predictionhiện tại, không phátlạiđiểmcũ. Chếđộ mặcđịnh0giây giữ hànhvi cũ, replay/rawkhôngdùngfilter. Đây làconfigthử, chưa calibrated. Lịch đọcframe, buffer camera vàWokwislow cóthể tăngdelay; phải đo trước khi chốt policy.

Nguồn: [Ultralytics validation](https://docs.ultralytics.com/modes/val/), [training](https://docs.ultralytics.com/modes/train/).
