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


để chạy được Ai 
đầu tiên tạo một file tên là ".env"
lên https://aistudio.google.com/app/api-keys
tạo API key mới và cho vào file ".env.
