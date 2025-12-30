const WELCOME_MESSAGES = [
  "👋 Tôi có thể giúp gì cho bạn?",
  "🌍 Bạn đang tìm địa điểm tham quan nào?",
  "🧭 Muốn mình gợi ý vài chỗ hay không?",
  "🏖️ Bạn sắp đi du lịch ở đâu?",
  "📍 Bạn muốn xem thông tin địa điểm nào?"
];

function getRandomWelcome() {
  return WELCOME_MESSAGES[
    Math.floor(Math.random() * WELCOME_MESSAGES.length)
  ];
}
