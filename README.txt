đối với lần đầu tiên chạy file có chatBot:
vào https://aistudio.google.com/app/api-keys
đăng nhập bằng tài khoản Google
bấm “Create API key”, rồi copy key
mở cmd prompt nhập
setx GOOGLE_API_KEY "key_mới_copy"

cd Dia\Chi\Thu\Muc
sau đó copy dòng này vào để tải module cần thiết:
pip install -r requirements.txt

vào app.py vào chạy
hoặc dùng
python app.y

link để vào web:
http://localhost:5000/

account 
PhucLaiz
laingan123

để chạy được Ai 
đầu tiên tạo một file tên là ".env"
lên https://aistudio.google.com/app/api-keys
tạo API key mới và cho vào file ".env.

do đã thay database nên vào đường link sau để tải ảnh: https://drive.google.com/drive/folders/1UeO6AejNDUdvGBbMDMWhoKXyuvI4LkM3?usp=drive_link
giải nén và cho thư mục images vào trong thư mục images ở trong phần static
