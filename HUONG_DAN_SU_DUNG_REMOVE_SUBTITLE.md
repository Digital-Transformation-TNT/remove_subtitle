# HƯỚNG DẪN SỬ DỤNG — TNT Video Subtitle Remover

Công cụ **tách & xoá phụ đề video** tự động qua vmake.ai.

---

## 1. Tool này làm gì?

Bạn đưa vào 1 video (hoặc cả thư mục video), tool sẽ:

1. **Cắt** video thành nhiều đoạn ngắn (~4 giây/đoạn).
2. **Đưa từng đoạn lên vmake.ai** để xoá phụ đề (hoặc watermark) rồi tải về.
3. **Ghép** các đoạn đã sạch lại → **video hoàn chỉnh không còn phụ đề**, đúng độ dài, đúng tiếng, đúng kích thước như gốc.

> **Vì sao phải cắt 4 giây?** Bản miễn phí của vmake chỉ cho tải **5 giây đầu**. Mỗi đoạn ≤ 4s nằm gọn trong 5s preview nên tải được trọn vẹn. Tool tự lo việc này.

---

## 2. Mở tool

### Windows
1. Giải nén thư mục `TNT_VideoSubtitleRemover` ra ổ đĩa (giữ **nguyên cả thư mục**, không tách riêng file `.exe`).
2. Chạy file **`TNT_VideoSubtitleRemover.exe`**.

> Khi nhận bản cập nhật: thường chỉ cần **ghi đè file `.exe` mới** vào thư mục cũ, giữ nguyên thư mục `_internal/` và `license.key`.

### macOS
1. Chép **`TNT_VideoSubtitleRemover.app`** ra (ví dụ vào Applications).
2. Lần đầu bị macOS chặn (app chưa notarize) → **chuột phải vào app → Open** (hoặc chạy 1 lần lệnh gỡ cờ tải-từ-internet):
   ```bash
   xattr -dr com.apple.quarantine /đường-dẫn/TNT_VideoSubtitleRemover.app
   ```

Trong tool đã **nhúng sẵn** trình duyệt + ffmpeg — máy trắng không cần cài gì thêm.

---

## 3. Kích hoạt bản quyền (license) — làm 1 lần

Mỗi máy cần 1 file `license.key`.

1. Mở tool lần đầu → hiện **MÃ MÁY** (và tự lưu file `machine_id.txt` cạnh tool). Bấm **Copy mã máy**.
2. **Gửi mã máy đó cho người cấp phép (TNT).**
3. Nhận lại file **`license.key`** → đặt vào **1 trong 2 chỗ**:
   - Cạnh chương trình (cùng thư mục file chạy), hoặc
   - `C:\TNT\license.key` (Windows) / `/Library/Application Support/TNT/license.key` (macOS).
4. Mở lại tool → chạy bình thường.

> License gắn với **mã máy** → copy sang máy khác sẽ không chạy (mỗi máy xin 1 license riêng).
> Đổi bản mới (exe/app) **không cần xin lại license** — giữ nguyên file `license.key` là được.

---

## 4. Các bước sử dụng

Giao diện có **2 tab**: **1. Nguồn (vào/ra)** và **2. Cấu hình & Chạy**.

1. **Tab 1 — Nguồn:**
   - Chọn **1 video** hoặc **1 thư mục** chứa nhiều video → bấm **Chọn…** trỏ tới đường dẫn.
   - **Thư mục lưu kết quả**: nơi xuất video (mặc định `vmake_output`).
2. **Tab 2 — Cấu hình:** để mặc định là chạy được (xem mục 5 để tinh chỉnh).
3. Bấm **Bắt đầu**. Theo dõi tiến trình ở khung log phía dưới.
4. Xong **mỗi video** sẽ có **thông báo hiện NGOÀI tool** — cứ thu nhỏ đi làm việc khác:
   - **Windows:** toast góc phải màn hình (vào cả Action Center) + **nháy nút taskbar**.
   - **macOS:** thông báo ở **Notification Center** (góc phải trên) + **nảy icon dock**.
   - Xong **toàn bộ** (và khi **gặp lỗi**) cũng có thông báo riêng.
   - Muốn chắc chắn không bỏ lỡ: tick **"Kèm popup mỗi khi xong 1 video"** ở tab 2.
   - Bấm **"Thử thông báo"** (tab 2) để kiểm tra máy có hiện thông báo không.
5. Muốn dừng giữa chừng: bấm **Dừng** (sẽ dừng sau bước hiện tại).

---

## 5. Giải thích các tuỳ chọn

| Tuỳ chọn | Ý nghĩa | Khuyên dùng |
|---|---|---|
| **Độ dài mỗi đoạn (giây)** | Video được cắt thành đoạn dài bấy nhiêu giây. | **4.0** (≤ 4.5 để nằm gọn trong 5s free của vmake) |
| **Các bước** (Tách / Xoá phụ đề / Ghép) | Bật/tắt từng công đoạn. | Bật **cả 3** |
| **Chế độ vmake** | *Tự động* (tool bấm hộ) hoặc *Bán tự động*. | **Tự động** |
| **Chạy ẩn** ✅ | Chạy trình duyệt **ẩn** (không hiện cửa sổ). Nhờ vậy **thu nhỏ / làm việc khác vẫn xử lý**, không bị "đợi lâu". | **Bật** (mặc định) |
| **Loại xoá** | *Smart* (tự nhận), *Subtitle* (phụ đề), *Watermark*. | **Subtitle** để xoá phụ đề cho chuẩn |
| **Timeout mỗi đoạn (giây)** | Chờ tối đa bấy nhiêu giây cho 1 đoạn; quá thì làm lại. | **300** (để thấp như 150 dễ bị "làm đi làm lại") |
| **Nghỉ ngẫu nhiên giữa đoạn** | Giãn cách giữa các lần up cho vmake đỡ dồn. | **1–2s** (mặc định) |
| **Số video song song (batch)** | Tự động = số đoạn, tối đa **4** (chạy nhiều hơn dễ nghẽn GPU → 1 đoạn kẹt). | Để **tự động** |
| **Đăng nhập vmake** | Đăng nhập tài khoản để dùng tiếp khi hết lượt free ẩn danh. | Xem mục 7 |
| **Thông báo khi xong** | *Kèm popup mỗi khi xong 1 video*: ngoài thông báo hệ thống còn bung 1 cửa sổ nổi trên cùng. Nút *Thử thông báo* để test máy. | Bật popup nếu máy hay **chặn** thông báo |

---

## 6. Kết quả nằm ở đâu?

Trong **thư mục lưu kết quả** bạn đã chọn:

```
vmake_output/
├── segments/<tên_video>/      # các đoạn đã cắt
├── processed/<tên_video>/     # các đoạn đã xoá phụ đề (tải từ vmake)
├── final/<tên_video>_nosub.mp4 # ⭐ VIDEO HOÀN CHỈNH (không phụ đề)
└── manifest.json              # thông tin phiên xử lý
```

Video cần lấy nằm trong thư mục **`final/`**.

> **Resume (chạy tiếp):** đoạn nào đã cắt/đã xử lý rồi thì lần chạy sau **bỏ qua** (log ghi "đã tồn tại, bỏ qua"). Muốn làm lại từ đầu → **xoá thư mục `vmake_output`** rồi chạy lại.

---

## 7. Giới hạn tài khoản vmake (RẤT QUAN TRỌNG)

vmake **giới hạn theo TÀI KHOẢN** (quota free). Khi 1 tài khoản dùng nhiều, vmake **bóp tốc độ xử lý** → mỗi đoạn chạy rất lâu → tool phải **làm đi làm lại**. Đổi sang **tài khoản mới** thì xử lý "vèo cái được ngay".

**Cách xử lý khi thấy nhiều đoạn báo "quá lâu — xử lý lại":**
- **Đổi tài khoản vmake khác** (bấm *Đăng nhập vmake & lưu phiên* rồi đăng nhập account khác), hoặc
- **Tăng Timeout** lên 300s để đỡ bị cắt ngang (giảm làm-lại), hoặc
- Chờ tài khoản "hồi" quota rồi chạy lại sau.

> **Lưu ý:** đây **không phải lỗi cache** — file đã cắt vẫn dùng được với tài khoản khoẻ. Xoá cache máy **không** reset được quota (vì quota nằm trên tài khoản ở máy chủ vmake). Chỉ **tài khoản mới** (hoặc đổi IP nếu vmake chặn theo IP) mới reset.

---

## 8. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân & cách xử lý |
|---|---|
| **Bật lên đòi "MÃ MÁY", không vào được** | Chưa có/`license.key` sai chỗ. Xem **mục 3**. |
| Thu nhỏ cửa sổ đi làm việc khác → báo **"đợi lâu"** | Do trình duyệt bị Windows "bóp" khi minimize. **Bật "Chạy ẩn"** (mặc định đã bật) là hết. |
| **Nhiều đoạn "quá lâu — xử lý lại"** | Tài khoản vmake bị bóp quota. Xem **mục 7** (đổi tài khoản / tăng timeout). |
| **1–2 đoạn bị bỏ qua** ("KHÔNG xử lý được") | vmake trục trặc đoạn đó. Tool vẫn ghép ra video hoàn chỉnh, **đoạn lỗi dùng bản gốc** (còn phụ đề ở đoạn đó). Chạy lại sau để xử lý nốt. |
| **Không thấy thông báo khi xong** | Bấm **"Thử thông báo"** (tab 2) để kiểm tra. Không thấy → **Windows:** *Settings → System → Notifications* bật thông báo + **tắt Focus assist / Do not disturb**. **macOS:** *Cài đặt hệ thống → Thông báo* bật cho **Script Editor** (mac hiện thông báo qua tiến trình này) + tắt *Focus/Không làm phiền*. Cách chắc ăn: tick **"Kèm popup mỗi khi xong 1 video"**. Ngoài ra luôn có **nháy taskbar / nảy dock**. |
| Xử lý **chậm** | Video càng dài càng nhiều đoạn. Dùng tài khoản khoẻ + để "Chạy ẩn" (vẫn dùng GPU). |

---

## 9. Mẹo dùng nhanh (tóm tắt)

- Để **"Chạy ẩn" bật**, **Loại xoá = Subtitle**, **Timeout = 300s** → ổn định nhất.
- Xong 1 video có **thông báo hiện ngoài tool** (Windows: toast + nháy taskbar / macOS: Notification Center + nảy dock) → cứ thu nhỏ đi làm việc khác.
- Video ra nằm ở **`vmake_output/final/`**.
- Thấy **làm đi làm lại nhiều** → **đổi tài khoản vmake**.
- Lấy video cần dùng ở thư mục `final`, các thư mục khác là file trung gian (xoá được).

---

*TNT GROUP • Video Subtitle Remover (vmake.ai)*
