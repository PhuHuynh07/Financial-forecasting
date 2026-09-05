/**
 * AI English Master - Core Application Logic
 * Integrates Web Speech API (TTS & STT), Gemini AI API, 3D Flashcards, Grammar Mentor, and Reading Quizzes.
 */

// ==================== APPLICATION STATE ====================
const state = {
  apiKey: localStorage.getItem('gemini_api_key') || '',
  model: localStorage.getItem('gemini_model') || 'gemini-2.5-flash',
  theme: localStorage.getItem('app_theme') || 'dark',
  xp: parseInt(localStorage.getItem('app_xp') || '250', 10),
  streak: parseInt(localStorage.getItem('app_streak') || '3', 10),
  chatCount: parseInt(localStorage.getItem('app_chat_count') || '18', 10),
  vocabCount: parseInt(localStorage.getItem('app_vocab_count') || '24', 10),
  currentTab: 'tab-speaking',
  currentScenario: 'coffee',
  chatHistory: [],
  autoSpeak: true,
  showTranslation: true,
  isRecording: false,
  recognition: null,
  currentCardIdx: 0,
  currentDeck: [],
  currentPronounceIdx: 0,
};

// ==================== PRESET DATA ====================
const SCENARIO_CONFIG = {
  coffee: {
    partnerName: 'Emma (Barista & English Tutor)',
    desc: 'Tình huống: Order đồ uống tại quán cà phê',
    systemPrompt: `You are Emma, a friendly native English barista in a cozy cafe in London.
The user is practicing English. Converse naturally, keep responses concise (1-3 sentences), ask natural follow-up questions about their order.
At the end of your response, ALWAYS include a JSON block with:
{
  "translation": "Bản dịch tiếng Việt tự nhiên của câu trả lời trên",
  "tip": "Mẹo ngữ pháp hoặc từ vựng nếu câu của người học có chỗ cần cải thiện, nếu tốt thì khen ngợi ngắn gọn."
}
Format: Start with your conversational reply in English, then on a new line output \`\`\`json { ... } \`\`\``,
    initialMsg: {
      en: "Hi there! Welcome to The Daily Brew. What can I get started for you today?",
      vi: "Xin chào! Chào mừng bạn đến với Daily Brew. Hôm nay tôi có thể lấy cho bạn món gì?",
      tip: "Bạn có thể dùng cấu trúc 'Could I get a...' hoặc 'I'd like a...' để gọi món lịch sự."
    },
    hints: [
      "Hi! Could I get a medium iced cappuccino with oat milk, please?",
      "What do you recommend for someone who likes caramel?",
      "Do you have any fresh croissants or pastries today?"
    ]
  },
  interview: {
    partnerName: 'Mr. David (Senior HR Manager)',
    desc: 'Tình huống: Phỏng vấn xin việc bằng tiếng Anh',
    systemPrompt: `You are Mr. David, a professional yet supportive hiring manager interviewing the user for an international position.
Ask standard behavioral and experience interview questions one by one. Keep replies professional, concise, and structured.
At the end of your response, ALWAYS include a JSON block with:
{
  "translation": "Bản dịch tiếng Việt",
  "tip": "Gợi ý cách trả lời chuyên nghiệp hơn hoặc sửa lỗi ngữ pháp."
}
Format: Start with your interview question in English, then on a new line output \`\`\`json { ... } \`\`\``,
    initialMsg: {
      en: "Good morning! Thank you for joining the interview today. Could you briefly introduce yourself and your background?",
      vi: "Chào buổi sáng! Cảm ơn bạn đã tham gia buổi phỏng vấn hôm nay. Bạn có thể giới thiệu ngắn gọn về bản thân và kinh nghiệm không?",
      tip: "Hãy dùng công thức Hiện tại - Quá khứ - Tương lai (Present - Past - Future) để giới thiệu ngắn gọn trong 1-2 phút."
    },
    hints: [
      "Good morning! I have over 3 years of experience in software development and love solving problems.",
      "Certainly! I graduated with a degree in Marketing and recently managed digital campaigns.",
      "Thank you for having me. I specialize in project management and team leadership."
    ]
  },
  airport: {
    partnerName: 'Officer Jessica (Airline Agent)',
    desc: 'Tình huống: Check-in Sân bay & Du lịch',
    systemPrompt: `You are Officer Jessica, an airline check-in officer at Heathrow Airport. Assist the traveler with check-in, passports, boarding passes, luggage, and gate directions.
At the end of your response, ALWAYS include a JSON block with:
{
  "translation": "Bản dịch tiếng Việt",
  "tip": "Mẹo từ vựng du lịch / sân bay."
}
Format: Start with your reply in English, then on a new line output \`\`\`json { ... } \`\`\``,
    initialMsg: {
      en: "Hello! May I see your passport and flight booking confirmation, please?",
      vi: "Xin chào! Cho tôi xem hộ chiếu và mã đặt vé máy bay của bạn được không?",
      tip: "Dùng 'Here you go' hoặc 'Here it is' khi đưa giấy tờ cho nhân viên."
    },
    hints: [
      "Here is my passport and ticket confirmation to New York.",
      "Could I please get a window seat if available?",
      "How many pieces of checked baggage am I allowed?"
    ]
  },
  ielts: {
    partnerName: 'Examiner Michael (IELTS Speaking)',
    desc: 'Tình huống: Giả lập giám khảo IELTS Speaking',
    systemPrompt: `You are Examiner Michael, a certified IELTS Speaking examiner. Ask IELTS Part 1 / Part 2 questions naturally. Evaluate lexical resource, fluency, and grammar.
At the end of your response, ALWAYS include a JSON block with:
{
  "translation": "Bản dịch tiếng Việt",
  "tip": "Gợi ý nâng cấp từ vựng C1/C2 (Collocations/Idioms) và cải thiện độ trôi chảy."
}
Format: Start with your IELTS question/comment in English, then on a new line output \`\`\`json { ... } \`\`\``,
    initialMsg: {
      en: "Good afternoon. My name is Michael. This is the Speaking test. To start with, let's talk about your hometown. Where do you come from?",
      vi: "Chào buổi chiều. Tôi tên Michael. Đây là bài thi Nói. Để bắt đầu, hãy nói về quê hương bạn. Bạn đến từ đâu?",
      tip: "Mở rộng câu trả lời bằng cách nêu thêm đặc điểm nổi bật hoặc cảm nhận cá nhân về quê hương."
    },
    hints: [
      "I was born and raised in Da Nang, a coastal city famous for its breathtaking beaches and bridges.",
      "I come from a bustling metropolis where life moves at a very fast pace.",
      "My hometown is a tranquil rural town surrounded by lush green hills."
    ]
  },
  freetalk: {
    partnerName: 'Alex (Friendly English Tutor)',
    desc: 'Tình huống: Trò chuyện tự do & Luyện phản xạ',
    systemPrompt: `You are Alex, an enthusiastic, caring English tutor. Chat warmly about any topic the user desires (hobbies, movies, tech, life). Encourage them, ask engaging questions, and gently correct mistakes.
At the end of your response, ALWAYS include a JSON block with:
{
  "translation": "Bản dịch tiếng Việt",
  "tip": "Mẹo dùng từ tự nhiên như người bản xứ."
}
Format: Start with your conversational message in English, then on a new line output \`\`\`json { ... } \`\`\``,
    initialMsg: {
      en: "Hey there! I'm Alex. I'm super excited to practice English with you today! What's something interesting that happened to you this week?",
      vi: "Chào bạn! Mình là Alex. Rất vui được luyện tiếng Anh cùng bạn hôm nay! Tuần này có điều gì thú vị diễn ra với bạn không?",
      tip: "Kể một câu chuyện ngắn giúp bạn rèn luyện việc kết hợp các thì quá khứ rất hiệu quả!"
    },
    hints: [
      "I watched a fantastic sci-fi movie yesterday and really enjoyed the plot twist!",
      "I've been learning to cook Italian pasta recently, and it turned out delicious.",
      "I had a busy week at work, but I'm excited to learn English now."
    ]
  }
};

const VOCAB_DECKS = {
  daily: [
    { word: "Serendipity", phonetic: "/ˌser.ənˈdɪp.ə.ti/", type: "noun", meaning: "Sự may mắn tình cờ phát hiện ra điều tốt đẹp", example: "Finding my dream job while traveling was pure serendipity.", collocation: "a moment of serendipity, happy serendipity", category: "Daily Life" },
    { word: "Procrastinate", phonetic: "/prəˈkræs.tɪ.neɪt/", type: "verb", meaning: "Trì hoãn, chần chừ làm việc cần làm", example: "I always procrastinate when it comes to doing laundry.", collocation: "tend to procrastinate, stop procrastinating", category: "Daily Life" },
    { word: "Resilient", phonetic: "/rɪˈzɪl.jənt/", type: "adjective", meaning: "Kiên cường, có khả năng phục hồi nhanh sau khó khăn", example: "Children are often remarkably resilient in tough situations.", collocation: "highly resilient, resilient economy", category: "Daily Life" },
    { word: "Meticulous", phonetic: "/məˈtɪk.jə.ləs/", type: "adjective", meaning: "Tỉ mỉ, cẩn thận từng chi tiết nhỏ", example: "She is meticulous about keeping her workspace tidy.", collocation: "meticulous attention to detail, meticulous planning", category: "Daily Life" },
    { word: "Ambience", phonetic: "/ˈæm.bi.əns/", type: "noun", meaning: "Không gian, bầu không khí của một địa điểm", example: "The restaurant has a warm and relaxed ambience.", collocation: "cozy ambience, peaceful ambience", category: "Daily Life" }
  ],
  ielts_academic: [
    { word: "Ubiquitous", phonetic: "/juːˈbɪk.wə.təs/", type: "adjective", meaning: "Phổ biến khắp nơi, đâu đâu cũng có", example: "Smartphones have become ubiquitous in modern society.", collocation: "ubiquitous presence, virtually ubiquitous", category: "IELTS Academic" },
    { word: "Exacerbate", phonetic: "/ɪɡˈzæs.ə.beɪt/", type: "verb", meaning: "Làm trầm trọng thêm (vấn đề, tình trạng xấu)", example: "The traffic congestion exacerbated the city's air pollution.", collocation: "exacerbate the problem, exacerbate tensions", category: "IELTS Academic" },
    { word: "Proponent", phonetic: "/prəˈpəʊ.nənt/", type: "noun", meaning: "Người ủng hộ một quan điểm hoặc chính sách", example: "Proponents of renewable energy advocate for reducing fossil fuel reliance.", collocation: "leading proponent, staunch proponent", category: "IELTS Academic" },
    { word: "Detrimental", phonetic: "/ˌdet.rɪˈmen.təl/", type: "adjective", meaning: "Có hại, gây tổn hại nghiêm trọng", example: "Excessive screen time has a detrimental effect on sleep quality.", collocation: "detrimental effect, detrimental to health", category: "IELTS Academic" },
    { word: "Paradigm", phonetic: "/ˈpær.ə.daɪm/", type: "noun", meaning: "Mô hình mẫu, khuôn mẫu tư duy", example: "The internet caused a paradigm shift in how we access information.", collocation: "paradigm shift, dominant paradigm", category: "IELTS Academic" }
  ],
  business: [
    { word: "Leverage", phonetic: "/ˈliː.vər.ɪdʒ/", type: "verb", meaning: "Tận dụng tối đa nguồn lực/lợi thế để đạt kết quả tốt", example: "We can leverage AI technology to streamline customer service.", collocation: "leverage resources, leverage strengths", category: "Business" },
    { word: "Streamline", phonetic: "/ˈstriːm.laɪn/", type: "verb", meaning: "Tinh giản quy trình để tăng hiệu quả", example: "The company aims to streamline its supply chain operations.", collocation: "streamline the process, streamline workflow", category: "Business" },
    { word: "Viable", phonetic: "/ˈvaɪ.ə.bəl/", type: "adjective", meaning: "Khả thi, có thể phát triển thành công lâu dài", example: "We need a commercially viable business model before launching.", collocation: "economically viable, viable solution", category: "Business" },
    { word: "Benchmark", phonetic: "/ˈbentʃ.mɑːk/", type: "noun", meaning: "Tiêu chuẩn đánh giá, mốc chuẩn để đối chiếu", example: "Our company set a new benchmark for customer satisfaction.", collocation: "industry benchmark, establish a benchmark", category: "Business" },
    { word: "Synergy", phonetic: "/ˈsɪn.ə.dʒi/", type: "noun", meaning: "Sự cộng hưởng, hợp lực tạo ra sức mạnh lớn hơn", example: "The merger created powerful synergy between the two marketing teams.", collocation: "create synergy, team synergy", category: "Business" }
  ],
  technology: [
    { word: "Algorithm", phonetic: "/ˈæl.ɡə.rɪ.ðəm/", type: "noun", meaning: "Thuật toán xử lý dữ liệu và tính toán", example: "Social media feeds are heavily influenced by recommendation algorithms.", collocation: "complex algorithm, machine learning algorithm", category: "Technology" },
    { word: "Autonomous", phonetic: "/ɔːˈtɒn.ə.məs/", type: "adjective", meaning: "Tự hành, tự chủ, không cần con người can thiệp", example: "Autonomous vehicles rely on sensors and AI computer vision.", collocation: "autonomous vehicle, autonomous system", category: "Technology" },
    { word: "Scalability", phonetic: "/ˌskeɪ.ləˈbɪl.ə.ti/", type: "noun", meaning: "Khả năng mở rộng quy mô khi lượng người dùng tăng", example: "Cloud infrastructure offers unmatched scalability for startups.", collocation: "high scalability, system scalability", category: "Technology" },
    { word: "Cybersecurity", phonetic: "/ˈsaɪ.bə.sɪˌkjʊə.rɪ.ti/", type: "noun", meaning: "An ninh mạng, bảo vệ hệ thống trước tấn công", example: "Investing in robust cybersecurity is essential for digital banking.", collocation: "cybersecurity threat, cybersecurity protocol", category: "Technology" },
    { word: "Disruptive", phonetic: "/dɪsˈrʌp.tɪv/", type: "adjective", meaning: "Đột phá, thay đổi hoàn toàn thị trường/ngành nghề", example: "Generative AI is a disruptive technology reshaping multiple industries.", collocation: "disruptive innovation, disruptive technology", category: "Technology" }
  ]
};

const PRONUNCIATION_SENTENCES = [
  {
    text: "Consistency is the key to mastering any new language.",
    ipa: "/kənˈsɪs.tən.si ɪz ðə kiː tuː ˈmæs.tər.ɪŋ ˈɛn.i njuː ˈlæŋ.ɡwɪdʒ/",
    vi: "Sự kiên trì là chìa khóa để làm chủ bất kỳ ngôn ngữ mới nào.",
    level: "Intermediate"
  },
  {
    text: "Artificial intelligence empowers individuals to learn faster and more effectively.",
    ipa: "/ˌɑː.tɪˈfɪʃ.əl ɪnˈtel.ɪ.dʒəns ɪmˈpaʊəz ˌɪn.dɪˈvɪdʒ.u.əlz tuː lɜːn ˈfɑː.stər ænd mɔːr ɪˈfek.tɪv.li/",
    vi: "Trí tuệ nhân tạo trao quyền cho các cá nhân học nhanh hơn và hiệu quả hơn.",
    level: "Advanced"
  },
  {
    text: "Could you please give me a recommendation for a good local restaurant?",
    ipa: "/kʊd juː pliːz ɡɪv miː ə ˌrek.ə.menˈdeɪ.ʃən fɔːr ə ɡʊd ˈləʊ.kəl ˈres.trɒnt/",
    vi: "Bạn có thể vui lòng gợi ý cho tôi một nhà hàng địa phương ngon không?",
    level: "Daily / Travel"
  },
  {
    text: "It is crucial to balance your professional ambitions with personal well-being.",
    ipa: "/ɪt ɪz ˈkruː.ʃəl tuː ˈbæl.əns jɔːr prəˈfeʃ.ən.əl æmˈbɪʃ.ənz wɪð ˈpɜː.sən.əl ˌwelˈbiː.ɪŋ/",
    vi: "Điều cốt yếu là phải cân bằng tham vọng nghề nghiệp với hạnh phúc cá nhân.",
    level: "IELTS 7.0+"
  }
];

const PRESET_READINGS = {
  B1: {
    title: "The Rise of Artificial Intelligence in Everyday Life",
    level: "Intermediate (B1)",
    body: `In recent years, Artificial Intelligence (AI) has transitioned from science fiction into an indispensable part of our daily routines. From smartphone virtual assistants like Siri and Google Assistant to smart home thermostats that learn our temperature preferences, AI algorithms work quietly in the background to make our lives more comfortable and efficient.

One of the most transformative impacts of AI is in the field of education and personalized learning. Traditional education systems often follow a one-size-fits-all model, where every student receives the same instruction regardless of their individual learning pace. Today, AI-powered applications can assess a learner's strengths and weaknesses in real time, tailoring lessons and flashcards specifically to their needs.

However, the rapid expansion of AI also raises critical ethical questions. Issues concerning data privacy, algorithmic bias, and workforce automation require careful regulation. As technology continues to evolve, society must strike a thoughtful balance between embracing groundbreaking innovation and protecting human welfare.`,
    questions: [
      {
        q: "What is the main topic of the passage?",
        options: [
          "A) The history of smartphones and home thermostats.",
          "B) The increasing impact, benefits, and challenges of AI in everyday life.",
          "C) Why traditional schooling should be completely abolished.",
          "D) How AI is replacing all human jobs immediately."
        ],
        correct: 1,
        explanation: "Bài đọc thảo luận về sự xuất hiện của AI trong cuộc sống thường nhật, các lợi ích (đặc biệt trong giáo dục cá nhân hóa) và các thách thức đạo đức cần cân bằng."
      },
      {
        q: "According to the text, how does AI improve modern education?",
        options: [
          "A) By making all exams much harder for students.",
          "B) By eliminating teachers completely from classrooms.",
          "C) By assessing individual strengths and weaknesses to tailor lessons.",
          "D) By forcing every student to learn at the exact same speed."
        ],
        correct: 2,
        explanation: "Đoạn 2 nêu rõ: 'AI-powered applications can assess a learner's strengths and weaknesses in real time, tailoring lessons specifically to their needs.'"
      },
      {
        q: "What concern regarding AI is mentioned in the final paragraph?",
        options: [
          "A) High electricity costs of smart devices.",
          "B) Data privacy, algorithmic bias, and workforce automation.",
          "C) Students refusing to use smartphones.",
          "D) The slow speed of internet connections."
        ],
        correct: 1,
        explanation: "Đoạn cuối đề cập: 'Issues concerning data privacy, algorithmic bias, and workforce automation require careful regulation.'"
      }
    ]
  }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initModals();
  initSpeechRecognition();
  initSpeakingTab();
  initWritingTab();
  initVocabTab();
  initReadingTab();
  initPronunciationTab();
  updateStatsDisplay();
});

// ==================== THEME MANAGEMENT ====================
function initTheme() {
  const isDark = state.theme === 'dark';
  document.documentElement.classList.toggle('dark', isDark);
  updateThemeIcon(isDark);

  const themeToggle = document.getElementById('themeToggle');
  themeToggle?.addEventListener('click', () => {
    const newTheme = document.documentElement.classList.toggle('dark') ? 'dark' : 'light';
    state.theme = newTheme;
    localStorage.setItem('app_theme', newTheme);
    updateThemeIcon(newTheme === 'dark');
  });
}

function updateThemeIcon(isDark) {
  const themeToggle = document.getElementById('themeToggle');
  if (!themeToggle) return;
  themeToggle.innerHTML = isDark
    ? '<i class="fa-solid fa-sun text-amber-400"></i>'
    : '<i class="fa-solid fa-moon text-indigo-400"></i>';
}

// ==================== NAVIGATION TABS ====================
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-target');
      switchTab(targetId);
    });
  });
}

function switchTab(targetId) {
  state.currentTab = targetId;

  // Update tab buttons
  document.querySelectorAll('.nav-tab').forEach(btn => {
    const isTarget = btn.getAttribute('data-target') === targetId;
    btn.classList.toggle('active-tab', isTarget);
    btn.classList.toggle('bg-indigo-600', isTarget);
    btn.classList.toggle('text-white', isTarget);
    btn.classList.toggle('shadow-md', isTarget);
    btn.classList.toggle('text-slate-400', !isTarget);
  });

  // Update content sections
  document.querySelectorAll('.tab-content').forEach(section => {
    if (section.id === targetId) {
      section.classList.remove('hidden');
      section.classList.add('block');
    } else {
      section.classList.add('hidden');
      section.classList.remove('block');
    }
  });

  // Add XP for exploring tabs if not already granted
  addXp(5);
}

// ==================== XP & STREAK SYSTEM ====================
function addXp(points) {
  state.xp += points;
  localStorage.setItem('app_xp', state.xp);
  updateStatsDisplay();
}

function updateStatsDisplay() {
  const xpCountEl = document.getElementById('xpCount');
  const streakCountEl = document.getElementById('streakCount');
  const statStreak = document.getElementById('statStreak');
  const statXp = document.getElementById('statXp');
  const statVocabCount = document.getElementById('statVocabCount');
  const statChatCount = document.getElementById('statChatCount');

  if (xpCountEl) xpCountEl.textContent = state.xp;
  if (streakCountEl) streakCountEl.textContent = state.streak;
  if (statStreak) statStreak.textContent = state.streak;
  if (statXp) statXp.textContent = state.xp;
  if (statVocabCount) statVocabCount.textContent = state.vocabCount;
  if (statChatCount) statChatCount.textContent = state.chatCount;
}

function triggerConfetti() {
  if (typeof confetti === 'function') {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 }
    });
  }
}

// ==================== WEB SPEECH API (TTS & STT) ====================
function speakText(text, lang = 'en-US', rate = 0.95) {
  if (!('speechSynthesis' in window)) {
    console.warn('Speech Synthesis not supported by browser.');
    return;
  }
  window.speechSynthesis.cancel(); // stop previous speech

  const cleanText = text.replace(/[*_#`]/g, '').trim();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = lang;
  utterance.rate = rate;

  // Try to pick natural native voice
  const voices = window.speechSynthesis.getVoices();
  const naturalVoice = voices.find(v => (v.lang === lang || v.lang.startsWith('en')) && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Daniel')));
  if (naturalVoice) utterance.voice = naturalVoice;

  window.speechSynthesis.speak(utterance);
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn('Speech Recognition is not supported in this browser. (Use Chrome or Edge)');
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = false;
  state.recognition.interimResults = false;
  state.recognition.lang = 'en-US';

  state.recognition.onstart = () => {
    state.isRecording = true;
    updateMicUi(true);
  };

  state.recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    handleSpeechResult(transcript);
  };

  state.recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    state.isRecording = false;
    updateMicUi(false);
  };

  state.recognition.onend = () => {
    state.isRecording = false;
    updateMicUi(false);
  };
}

function toggleSpeechRecognition(targetContext = 'chat') {
  if (!state.recognition) {
    alert('Trình duyệt của bạn chưa hỗ trợ nhận diện giọng nói qua Micro. Hãy dùng Google Chrome hoặc Microsoft Edge nhé!');
    return;
  }

  state.speechTargetContext = targetContext;
  if (state.isRecording) {
    state.recognition.stop();
  } else {
    try {
      state.recognition.start();
    } catch (e) {
      console.error(e);
    }
  }
}

function updateMicUi(isRecording) {
  const btnMic = document.getElementById('btnMic');
  const recordingIndicator = document.getElementById('recordingIndicator');
  const recordPronounceBtnText = document.getElementById('recordPronounceBtnText');

  if (recordingIndicator) {
    recordingIndicator.classList.toggle('hidden', !isRecording);
    recordingIndicator.classList.toggle('flex', isRecording);
  }

  if (btnMic) {
    btnMic.classList.toggle('bg-rose-600', isRecording);
    btnMic.classList.toggle('text-white', isRecording);
  }

  if (recordPronounceBtnText) {
    recordPronounceBtnText.textContent = isRecording ? 'Đang lắng nghe...' : 'Bấm Mic & Phát Âm';
  }
}

function handleSpeechResult(transcript) {
  if (state.speechTargetContext === 'pronounce') {
    handlePronunciationSpeechResult(transcript);
  } else {
    // Default is chat input
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.value = transcript;
      // Auto submit after voice
      setTimeout(() => {
        document.getElementById('chatForm')?.dispatchEvent(new Event('submit', { cancelable: true }));
      }, 500);
    }
  }
}

// ==================== GEMINI AI INTEGRATION ====================
async function callGemini(prompt, systemInstruction = '') {
  // If demo mode or no key provided, return smart mock response
  if (!state.apiKey || state.model === 'demo') {
    return generateSmartMockResponse(prompt, systemInstruction);
  }

  const modelName = state.model || 'gemini-2.5-flash';
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${state.apiKey}`;

  const requestBody = {
    contents: [
      {
        role: "user",
        parts: [{ text: (systemInstruction ? systemInstruction + "\n\n" : "") + prompt }]
      }
    ],
    generationConfig: {
      temperature: 0.7,
      topP: 0.95,
      maxOutputTokens: 2048,
    }
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      console.warn('Gemini API Error, falling back to smart engine:', errData);
      return generateSmartMockResponse(prompt, systemInstruction);
    }

    const data = await response.json();
    const replyText = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    return replyText;
  } catch (error) {
    console.error('Fetch error with Gemini API:', error);
    return generateSmartMockResponse(prompt, systemInstruction);
  }
}

// Fallback intelligent offline engine when API key is not entered
function generateSmartMockResponse(prompt, systemInstruction) {
  // Check what module is calling
  if (systemInstruction.includes('Emma') || prompt.includes('cafe') || prompt.includes('coffee')) {
    return `That sounds wonderful! A medium iced latte with oat milk is actually our customer favorite. Would you like any extra espresso shot or caramel syrup with that?

\`\`\`json
{
  "translation": "Nghe tuyệt quá! Cà phê latte đá cỡ vừa pha với sữa yến mạch là món được khách hàng yêu thích nhất của chúng tôi. Bạn có muốn thêm một shot espresso hay si-rô caramel không?",
  "tip": "Câu nói của bạn rất chuẩn xác và lịch sự. Cụm từ 'Could I get...' là cách người bản xứ rất hay dùng."
}
\`\`\``;
  }

  if (systemInstruction.includes('David') || prompt.includes('interview')) {
    return `That is very impressive! I appreciate your clear summary of your experience. Can you give me a specific example of a challenging project you handled and how you overcame the obstacles?

\`\`\`json
{
  "translation": "Điều đó rất ấn tượng! Tôi đánh giá cao phần tóm tắt kinh nghiệm rõ ràng của bạn. Bạn có thể cho tôi một ví dụ cụ thể về một dự án khó khăn và cách bạn vượt qua không?",
  "tip": "Hãy áp dụng mô hình STAR (Situation - Task - Action - Result) khi trả lời các câu hỏi tình huống phỏng vấn."
}
\`\`\``;
  }

  if (systemInstruction.includes('Grammar & Writing')) {
    return JSON.stringify({
      polishedText: "I have been living in Hanoi for five years, and I really like it here.",
      estimatedBand: "Band 7.0 / B2",
      errors: [
        {
          original: "I has been living",
          corrected: "I have been living",
          reason: "Chủ ngữ 'I' đi với trợ động từ 'have', không dùng 'has' trong thì hiện tại hoàn thành tiếp diễn."
        },
        {
          original: "since five years",
          corrected: "for five years",
          reason: "Dùng 'for' cho khoảng thời gian (khoảng 5 năm), dùng 'since' cho mốc thời gian cụ thể (ví dụ: since 2019)."
        },
        {
          original: "like very much it",
          corrected: "really like it / like it very much",
          reason: "Trong tiếng Anh, trạng từ 'very much' không đứng giữa động từ 'like' và tân ngữ 'it'."
        }
      ],
      upgrades: [
        {
          basic: "I like it very much",
          advanced: "I am thoroughly captivated by the city's vibrant charm",
          explanation: "Nâng cấp từ vựng miêu tả cảm xúc và ấn tượng về nơi sống lên mức C1."
        },
        {
          basic: "living in Hanoi",
          advanced: "residing in the bustling capital of Hanoi",
          explanation: "Dùng 'residing' và tính từ 'bustling capital' giúp câu văn trang trọng hơn."
        }
      ]
    });
  }

  // Default friendly reply
  return `I completely understand! Practicing English step by step every day is the fastest way to achieve fluency.

\`\`\`json
{
  "translation": "Tôi hoàn toàn hiểu! Luyện tập tiếng Anh từng bước mỗi ngày là cách nhanh nhất để đạt được sự lưu loát.",
  "tip": "Hãy tiếp tục duy trì việc nói to từng câu để cải thiện phản xạ và phát âm nhé!"
}
\`\`\``;
}

// ==================== MODAL MANAGEMENT ====================
function initModals() {
  const settingsModal = document.getElementById('settingsModal');
  const btnOpenSettings = document.getElementById('btnOpenSettings');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const btnSaveSettings = document.getElementById('btnSaveSettings');
  const inputApiKey = document.getElementById('inputApiKey');
  const selectAiModel = document.getElementById('selectAiModel');

  if (inputApiKey) inputApiKey.value = state.apiKey;
  if (selectAiModel) selectAiModel.value = state.model;

  btnOpenSettings?.addEventListener('click', () => {
    settingsModal?.classList.remove('hidden');
    settingsModal?.classList.add('flex');
  });

  btnCloseSettings?.addEventListener('click', () => {
    settingsModal?.classList.add('hidden');
    settingsModal?.classList.remove('flex');
  });

  btnSaveSettings?.addEventListener('click', () => {
    state.apiKey = inputApiKey.value.trim();
    state.model = selectAiModel.value;
    localStorage.setItem('gemini_api_key', state.apiKey);
    localStorage.setItem('gemini_model', state.model);
    settingsModal?.classList.add('hidden');
    settingsModal?.classList.remove('flex');
    alert('Đã lưu cấu hình AI thành công!');
  });

  // Vocab Generator Modal
  const aiVocabModal = document.getElementById('aiVocabModal');
  const btnOpenAiVocabModal = document.getElementById('btnOpenAiVocabModal');
  const btnCloseAiVocabModal = document.getElementById('btnCloseAiVocabModal');
  const btnGenerateAiVocabSubmit = document.getElementById('btnGenerateAiVocabSubmit');

  btnOpenAiVocabModal?.addEventListener('click', () => {
    aiVocabModal?.classList.remove('hidden');
    aiVocabModal?.classList.add('flex');
  });

  btnCloseAiVocabModal?.addEventListener('click', () => {
    aiVocabModal?.classList.add('hidden');
    aiVocabModal?.classList.remove('flex');
  });

  btnGenerateAiVocabSubmit?.addEventListener('click', handleGenerateCustomVocab);
}

// ==================== TAB 1: SPEAKING & CHAT ====================
function initSpeakingTab() {
  const scenarioBtns = document.querySelectorAll('.scenario-btn');
  scenarioBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const scenarioKey = btn.getAttribute('data-scenario');
      selectScenario(scenarioKey);
    });
  });

  const chatForm = document.getElementById('chatForm');
  chatForm?.addEventListener('submit', handleSendChatMessage);

  const btnResetChat = document.getElementById('btnResetChat');
  btnResetChat?.addEventListener('click', () => selectScenario(state.currentScenario));

  const btnMic = document.getElementById('btnMic');
  btnMic?.addEventListener('click', () => toggleSpeechRecognition('chat'));

  const chkAutoSpeak = document.getElementById('chkAutoSpeak');
  chkAutoSpeak?.addEventListener('change', (e) => {
    state.autoSpeak = e.target.checked;
  });

  const chkShowTranslation = document.getElementById('chkShowTranslation');
  chkShowTranslation?.addEventListener('change', (e) => {
    state.showTranslation = e.target.checked;
    document.querySelectorAll('.translation-box').forEach(box => {
      box.classList.toggle('hidden', !state.showTranslation);
    });
  });

  // Start with default scenario
  selectScenario('coffee');
}

function selectScenario(scenarioKey) {
  state.currentScenario = scenarioKey;
  const config = SCENARIO_CONFIG[scenarioKey];
  if (!config) return;

  // Update UI headers
  const partnerName = document.getElementById('chatPartnerName');
  const partnerDesc = document.getElementById('chatPartnerDesc');
  if (partnerName) partnerName.textContent = config.partnerName;
  if (partnerDesc) partnerDesc.textContent = config.desc;

  // Update active state on scenario buttons
  document.querySelectorAll('.scenario-btn').forEach(btn => {
    const isSelected = btn.getAttribute('data-scenario') === scenarioKey;
    btn.classList.toggle('bg-indigo-600/20', isSelected);
    btn.classList.toggle('border-indigo-500/40', isSelected);
    btn.classList.toggle('bg-slate-800/80', !isSelected);
    btn.classList.toggle('border-slate-700', !isSelected);
  });

  // Update hints
  renderQuickHints(config.hints);

  // Reset chat history and display initial message
  state.chatHistory = [];
  const chatMessages = document.getElementById('chatMessages');
  if (chatMessages) {
    chatMessages.innerHTML = '';
    appendAiMessage(config.initialMsg.en, config.initialMsg.vi, config.initialMsg.tip);
  }
}

function renderQuickHints(hints) {
  const container = document.getElementById('quickSuggestions');
  if (!container || !hints) return;

  container.innerHTML = `
    <span class="text-slate-400 flex items-center gap-1"><i class="fa-regular fa-lightbulb text-amber-400"></i> Gợi ý câu:</span>
    ${hints.map(hint => `
      <button class="hint-btn px-2.5 py-1 rounded-full bg-slate-800 hover:bg-indigo-600/30 border border-slate-700 hover:border-indigo-500/50 text-slate-300 transition">
        "${hint}"
      </button>
    `).join('')}
  `;

  // Attach click to hints
  container.querySelectorAll('.hint-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.textContent.replace(/["\n]/g, '').trim();
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = text;
        input.focus();
      }
    });
  });
}

function appendUserMessage(text) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = 'flex justify-end';
  msgDiv.innerHTML = `
    <div class="max-w-[80%] bg-indigo-600 text-white rounded-2xl chat-bubble-user p-3.5 shadow-md space-y-1">
      <div class="text-sm font-medium">${escapeHtml(text)}</div>
      <div class="flex items-center justify-end gap-2 text-[10px] text-indigo-200">
        <span>Bạn</span>
        <button class="hover:text-white transition btn-speak-msg" data-text="${escapeHtml(text)}" title="Nghe lại câu này">
          <i class="fa-solid fa-volume-high"></i>
        </button>
      </div>
    </div>
  `;

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  msgDiv.querySelector('.btn-speak-msg')?.addEventListener('click', (e) => {
    e.stopPropagation();
    speakText(text);
  });
}

function appendAiMessage(enText, viText = '', tipText = '') {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = 'flex justify-start';
  msgDiv.innerHTML = `
    <div class="max-w-[85%] bg-slate-800/90 border border-slate-700 text-slate-100 rounded-2xl chat-bubble-ai p-3.5 shadow-md space-y-2">
      <div class="flex items-center justify-between text-xs text-indigo-400 font-semibold border-b border-slate-700/50 pb-1.5">
        <span class="flex items-center gap-1.5"><i class="fa-solid fa-robot"></i> Gia sư AI</span>
        <button class="hover:text-indigo-300 transition btn-speak-msg" title="Nghe phát âm">
          <i class="fa-solid fa-volume-high text-sm"></i>
        </button>
      </div>
      
      <div class="text-sm font-normal text-slate-100 leading-relaxed">${escapeHtml(enText)}</div>

      ${viText ? `
        <div class="translation-box text-xs text-slate-400 italic bg-slate-900/60 p-2 rounded-lg border border-slate-800 ${state.showTranslation ? '' : 'hidden'}">
          <span class="text-slate-500 font-medium mr-1">Dịch:</span>${escapeHtml(viText)}
        </div>
      ` : ''}

      ${tipText ? `
        <div class="text-[11px] text-amber-300/90 bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg flex items-start gap-1.5">
          <i class="fa-solid fa-circle-check text-amber-400 mt-0.5"></i>
          <span>${escapeHtml(tipText)}</span>
        </div>
      ` : ''}
    </div>
  `;

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  msgDiv.querySelector('.btn-speak-msg')?.addEventListener('click', (e) => {
    e.stopPropagation();
    speakText(enText);
  });

  if (state.autoSpeak) {
    speakText(enText);
  }
}

async function handleSendChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById('chatInput');
  const userText = input?.value.trim();
  if (!userText) return;

  // 1. Show user message
  appendUserMessage(userText);
  input.value = '';

  // 2. Increment stats & XP
  state.chatCount++;
  localStorage.setItem('app_chat_count', state.chatCount);
  addXp(10);

  // 3. Show typing indicator
  const chatMessages = document.getElementById('chatMessages');
  const typingDiv = document.createElement('div');
  typingDiv.id = 'typingIndicator';
  typingDiv.className = 'flex justify-start';
  typingDiv.innerHTML = `
    <div class="bg-slate-800/80 border border-slate-700 rounded-2xl p-3 text-xs text-slate-400 flex items-center gap-2">
      <div class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"></div>
      <div class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style="animation-delay: 0.2s"></div>
      <div class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style="animation-delay: 0.4s"></div>
      <span>AI đang suy nghĩ và phản hồi...</span>
    </div>
  `;
  chatMessages?.appendChild(typingDiv);
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

  // 4. Call AI
  const config = SCENARIO_CONFIG[state.currentScenario];
  const prompt = `User said: "${userText}"\nPlease respond as the roleplay character in English, and provide the JSON with translation and tips.`;

  const aiRawReply = await callGemini(prompt, config.systemPrompt);

  // Remove typing indicator
  document.getElementById('typingIndicator')?.remove();

  // 5. Parse reply
  let enReply = aiRawReply;
  let viReply = "";
  let tipReply = "";

  const jsonMatch = aiRawReply.match(/```json\s*([\s\S]*?)\s*```/) || aiRawReply.match(/\{[\s\S]*"translation"[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const jsonStr = jsonMatch[1] || jsonMatch[0];
      const parsed = JSON.parse(jsonStr);
      viReply = parsed.translation || "";
      tipReply = parsed.tip || "";
      enReply = aiRawReply.replace(/```json[\s\S]*?```/g, '').trim();
    } catch (err) {
      console.warn('JSON parse fallback:', err);
    }
  }

  appendAiMessage(enReply, viReply, tipReply);
}

// ==================== TAB 2: WRITING & GRAMMAR MENTOR ====================
function initWritingTab() {
  const writingInput = document.getElementById('writingInput');
  const wordCountLabel = document.getElementById('wordCountLabel');
  const btnCheckGrammar = document.getElementById('btnCheckGrammar');
  const sampleWritingSelect = document.getElementById('sampleWritingSelect');
  const btnCopyPolished = document.getElementById('btnCopyPolished');

  writingInput?.addEventListener('input', () => {
    const text = writingInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    if (wordCountLabel) wordCountLabel.textContent = `${words} từ`;
  });

  sampleWritingSelect?.addEventListener('change', (e) => {
    if (e.target.value && writingInput) {
      writingInput.value = e.target.value;
      writingInput.dispatchEvent(new Event('input'));
    }
  });

  btnCheckGrammar?.addEventListener('click', handleCheckGrammar);

  btnCopyPolished?.addEventListener('click', () => {
    const text = document.getElementById('polishedText')?.textContent;
    if (text) {
      navigator.clipboard.writeText(text);
      alert('Đã sao chép bản viết nâng cấp!');
    }
  });
}

async function handleCheckGrammar() {
  const writingInput = document.getElementById('writingInput');
  const userText = writingInput?.value.trim();
  if (!userText) {
    alert('Vui lòng nhập đoạn văn bản tiếng Anh cần kiểm tra!');
    return;
  }

  const grammarLoading = document.getElementById('grammarLoading');
  const grammarEmptyState = document.getElementById('grammarEmptyState');
  const grammarResultContent = document.getElementById('grammarResultContent');
  const grammarScoreBadge = document.getElementById('grammarScoreBadge');

  grammarEmptyState?.classList.add('hidden');
  grammarResultContent?.classList.add('hidden');
  grammarLoading?.classList.remove('hidden');

  const systemInstruction = `You are an expert English Grammar & Writing Professor and IELTS Examiner.
Analyze the user's input text. Return ONLY a valid JSON object matching this structure:
{
  "polishedText": "A natural, high-level (C1/IELTS 7.5+) improved version of the entire paragraph",
  "estimatedBand": "Band 7.0 / B2",
  "errors": [
    {
      "original": "exact wrong phrase",
      "corrected": "exact corrected phrase",
      "reason": "Detailed grammatical or lexical explanation in Vietnamese"
    }
  ],
  "upgrades": [
    {
      "basic": "simple word/phrase",
      "advanced": "advanced academic collocation/idiom",
      "explanation": "Why this upgrade improves the writing style in Vietnamese"
    }
  ]
}`;

  const prompt = `Analyze this English text:\n"${userText}"`;

  try {
    const rawResult = await callGemini(prompt, systemInstruction);
    let data;
    const jsonMatch = rawResult.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      data = JSON.parse(jsonMatch[0]);
    } else {
      data = JSON.parse(rawResult);
    }

    renderGrammarResults(data);
    addXp(15);
  } catch (err) {
    console.error('Grammar check parse error:', err);
    alert('Có lỗi khi phân tích văn bản. Vui lòng thử lại!');
  } finally {
    grammarLoading?.classList.add('hidden');
  }
}

function renderGrammarResults(data) {
  const grammarResultContent = document.getElementById('grammarResultContent');
  const grammarScoreBadge = document.getElementById('grammarScoreBadge');
  const polishedText = document.getElementById('polishedText');
  const errorList = document.getElementById('errorList');
  const vocabUpgradeList = document.getElementById('vocabUpgradeList');

  if (grammarScoreBadge && data.estimatedBand) {
    grammarScoreBadge.textContent = data.estimatedBand;
    grammarScoreBadge.classList.remove('hidden');
  }

  if (polishedText) {
    polishedText.textContent = data.polishedText || 'Không có gợi ý.';
  }

  if (errorList) {
    if (data.errors && data.errors.length > 0) {
      errorList.innerHTML = data.errors.map(err => `
        <div class="p-3 rounded-xl bg-slate-800/80 border border-rose-500/30 text-xs space-y-1">
          <div class="flex items-center gap-2">
            <span class="line-through text-rose-400 font-semibold">${escapeHtml(err.original)}</span>
            <i class="fa-solid fa-arrow-right text-slate-500 text-[10px]"></i>
            <span class="text-emerald-400 font-bold">${escapeHtml(err.corrected)}</span>
          </div>
          <p class="text-slate-300 italic pt-0.5">${escapeHtml(err.reason)}</p>
        </div>
      `).join('');
    } else {
      errorList.innerHTML = `<div class="text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/20"><i class="fa-solid fa-circle-check mr-1.5"></i>Tuyệt vời! Không phát hiện lỗi ngữ pháp cơ bản nào.</div>`;
    }
  }

  if (vocabUpgradeList) {
    if (data.upgrades && data.upgrades.length > 0) {
      vocabUpgradeList.innerHTML = data.upgrades.map(upg => `
        <div class="p-3 rounded-xl bg-slate-800/80 border border-emerald-500/30 text-xs space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-slate-400">${escapeHtml(upg.basic)}</span>
            <i class="fa-solid fa-arrow-up-right-dots text-emerald-400 text-[10px]"></i>
            <span class="text-indigo-300 font-bold">${escapeHtml(upg.advanced)}</span>
          </div>
          <p class="text-slate-300 pt-0.5">${escapeHtml(upg.explanation)}</p>
        </div>
      `).join('');
    } else {
      vocabUpgradeList.innerHTML = `<div class="text-xs text-slate-400 italic">Văn phong đã tương đối tự nhiên.</div>`;
    }
  }

  grammarResultContent?.classList.remove('hidden');
}

// ==================== TAB 3: SMART FLASHCARDS ====================
function initVocabTab() {
  const vocabTopicSelect = document.getElementById('vocabTopicSelect');
  const flashcardBox = document.getElementById('flashcardBox');
  const flashcardCard = document.getElementById('flashcardCard');
  const btnPrevCard = document.getElementById('btnPrevCard');
  const btnNextCard = document.getElementById('btnNextCard');
  const btnSpeakCurrent = document.getElementById('btnSpeakCurrent');
  const btnStartVocabQuiz = document.getElementById('btnStartVocabQuiz');
  const btnCloseQuiz = document.getElementById('btnCloseQuiz');

  // Load initial deck
  state.currentDeck = VOCAB_DECKS.ielts_academic;
  state.currentCardIdx = 0;
  renderCurrentFlashcard();

  vocabTopicSelect?.addEventListener('change', (e) => {
    const deckKey = e.target.value;
    if (VOCAB_DECKS[deckKey]) {
      state.currentDeck = VOCAB_DECKS[deckKey];
      state.currentCardIdx = 0;
      renderCurrentFlashcard();
    }
  });

  // 3D Flip on click
  flashcardBox?.addEventListener('click', (e) => {
    if (e.target.closest('.btn-speak-word')) return;
    flashcardCard?.classList.toggle('flashcard-flipped');
  });

  btnPrevCard?.addEventListener('click', () => {
    if (state.currentCardIdx > 0) {
      state.currentCardIdx--;
      flashcardCard?.classList.remove('flashcard-flipped');
      renderCurrentFlashcard();
    }
  });

  btnNextCard?.addEventListener('click', () => {
    if (state.currentCardIdx < state.currentDeck.length - 1) {
      state.currentCardIdx++;
      flashcardCard?.classList.remove('flashcard-flipped');
      renderCurrentFlashcard();
      addXp(2);
    }
  });

  btnSpeakCurrent?.addEventListener('click', () => {
    const card = state.currentDeck[state.currentCardIdx];
    if (card) speakText(card.word);
  });

  document.querySelectorAll('.btn-speak-word').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const card = state.currentDeck[state.currentCardIdx];
      if (card) speakText(card.word);
    });
  });

  btnStartVocabQuiz?.addEventListener('click', startVocabQuiz);
  btnCloseQuiz?.addEventListener('click', () => {
    document.getElementById('vocabQuizContainer')?.classList.add('hidden');
    document.getElementById('flashcardSection')?.classList.remove('hidden');
  });
}

function renderCurrentFlashcard() {
  const card = state.currentDeck[state.currentCardIdx];
  if (!card) return;

  const currentCardIndex = document.getElementById('currentCardIndex');
  const totalCardCount = document.getElementById('totalCardCount');
  const cardCategory = document.getElementById('cardCategory');
  const cardWord = document.getElementById('cardWord');
  const cardPhonetic = document.getElementById('cardPhonetic');
  const cardType = document.getElementById('cardType');
  const cardMeaning = document.getElementById('cardMeaning');
  const cardExample = document.getElementById('cardExample');
  const cardCollocation = document.getElementById('cardCollocation');

  if (currentCardIndex) currentCardIndex.textContent = state.currentCardIdx + 1;
  if (totalCardCount) totalCardCount.textContent = state.currentDeck.length;
  if (cardCategory) cardCategory.textContent = card.category || 'Vocabulary';
  if (cardWord) cardWord.textContent = card.word;
  if (cardPhonetic) cardPhonetic.textContent = card.phonetic;
  if (cardType) cardType.textContent = card.type;
  if (cardMeaning) cardMeaning.textContent = card.meaning;
  if (cardExample) cardExample.textContent = `"${card.example}"`;
  if (cardCollocation) cardCollocation.innerHTML = `<strong class="text-slate-300">Collocation / Đồng nghĩa:</strong> ${card.collocation}`;
}

async function handleGenerateCustomVocab() {
  const inputAiVocabTopic = document.getElementById('inputAiVocabTopic');
  const selectAiVocabLevel = document.getElementById('selectAiVocabLevel');
  const topic = inputAiVocabTopic?.value.trim() || 'General Communication';
  const level = selectAiVocabLevel?.value || 'B2';

  const btn = document.getElementById('btnGenerateAiVocabSubmit');
  if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tạo bộ từ...';

  const systemInstruction = `You are a vocabulary builder for English learners.
Generate 5 practical, high-value English words for the given topic and CEFR level.
Return ONLY a valid JSON array matching this format:
[
  {
    "word": "Word",
    "phonetic": "/IPA/",
    "type": "noun/verb/adj",
    "meaning": "Định nghĩa tiếng Việt súc tích",
    "example": "An authentic example sentence using the word.",
    "collocation": "common collocations or synonyms",
    "category": "${topic}"
  }
]`;

  try {
    const raw = await callGemini(`Topic: ${topic}, Level: ${level}`, systemInstruction);
    let newWords = [];
    const match = raw.match(/\[[\s\S]*\]/);
    if (match) {
      newWords = JSON.parse(match[0]);
    }

    if (newWords.length > 0) {
      state.currentDeck = newWords;
      state.currentCardIdx = 0;
      renderCurrentFlashcard();
      document.getElementById('aiVocabModal')?.classList.add('hidden');
      document.getElementById('aiVocabModal')?.classList.remove('flex');
      addXp(20);
      triggerConfetti();
      alert(`Đã tạo thành công 5 từ vựng chủ đề "${topic}"!`);
    }
  } catch (err) {
    console.error(err);
    alert('Không thể tạo bộ từ vào lúc này. Vui lòng kiểm tra lại!');
  } finally {
    if (btn) btn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo Thẻ Ngay';
  }
}

function startVocabQuiz() {
  const quizContainer = document.getElementById('vocabQuizContainer');
  const flashcardSection = document.getElementById('flashcardSection');
  const questionBox = document.getElementById('quizQuestionBox');

  if (!quizContainer || !questionBox) return;

  flashcardSection?.classList.add('hidden');
  quizContainer.classList.remove('hidden');

  // Pick random question from current deck
  const currentCard = state.currentDeck[state.currentCardIdx] || state.currentDeck[0];
  const wrongCards = state.currentDeck.filter(c => c.word !== currentCard.word);
  const options = [currentCard.meaning];

  while (options.length < 4 && wrongCards.length > 0) {
    const rand = wrongCards.splice(Math.floor(Math.random() * wrongCards.length), 1)[0];
    options.push(rand.meaning);
  }

  // Shuffle options
  options.sort(() => Math.random() - 0.5);

  questionBox.innerHTML = `
    <div class="space-y-3">
      <div class="text-xs text-indigo-400 font-semibold uppercase">Câu hỏi kiểm tra nghĩa từ:</div>
      <h3 class="text-2xl font-bold text-white text-center py-4 bg-slate-800/80 rounded-xl border border-slate-700">
        "${currentCard.word}" <span class="text-xs text-cyan-400 font-mono font-normal">(${currentCard.type})</span>
      </h3>
      <p class="text-xs text-slate-400">Chọn nghĩa tiếng Việt chính xác nhất cho từ trên:</p>
      
      <div class="space-y-2" id="quizOptionsList">
        ${options.map((opt, i) => `
          <button class="quiz-option-btn w-full text-left p-3 rounded-xl bg-slate-800 hover:bg-indigo-600/30 border border-slate-700 hover:border-indigo-500 text-slate-200 text-sm transition flex items-center gap-3" data-answer="${escapeHtml(opt)}">
            <span class="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">${String.fromCharCode(65 + i)}</span>
            <span>${escapeHtml(opt)}</span>
          </button>
        `).join('')}
      </div>

      <div id="quizFeedback" class="hidden p-3 rounded-xl text-xs"></div>
    </div>
  `;

  questionBox.querySelectorAll('.quiz-option-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const selected = btn.getAttribute('data-answer');
      const isCorrect = selected === currentCard.meaning;
      const feedback = document.getElementById('quizFeedback');

      if (isCorrect) {
        btn.classList.add('bg-emerald-600/40', 'border-emerald-500', 'text-emerald-300');
        if (feedback) {
          feedback.className = 'p-3 rounded-xl text-xs bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 block';
          feedback.innerHTML = `<i class="fa-solid fa-circle-check mr-1.5"></i> Chính xác! Bạn nhận được +15 XP.`;
        }
        addXp(15);
        triggerConfetti();
      } else {
        btn.classList.add('bg-rose-600/40', 'border-rose-500', 'text-rose-300');
        if (feedback) {
          feedback.className = 'p-3 rounded-xl text-xs bg-rose-500/20 border border-rose-500/40 text-rose-300 block';
          feedback.innerHTML = `<i class="fa-solid fa-circle-xmark mr-1.5"></i> Chưa đúng! Đáp án đúng là: <strong>${currentCard.meaning}</strong>`;
        }
      }

      // Disable buttons after answer
      questionBox.querySelectorAll('.quiz-option-btn').forEach(b => b.disabled = true);
    });
  });
}

// ==================== TAB 4: READING & COMPREHENSION ====================
function initReadingTab() {
  const btnGenerateReading = document.getElementById('btnGenerateReading');
  const btnReadAloudArticle = document.getElementById('btnReadAloudArticle');
  const btnSubmitReadingQuiz = document.getElementById('btnSubmitReadingQuiz');

  renderReadingArticle(PRESET_READINGS.B1);

  btnGenerateReading?.addEventListener('click', handleGenerateAiReading);

  btnReadAloudArticle?.addEventListener('click', () => {
    const body = document.getElementById('readingArticleBody')?.innerText;
    if (body) speakText(body);
  });

  btnSubmitReadingQuiz?.addEventListener('click', handleSubmitReadingQuiz);
}

function renderReadingArticle(data) {
  const title = document.getElementById('readingTitle');
  const badgeLevel = document.getElementById('readingBadgeLevel');
  const body = document.getElementById('readingArticleBody');
  const questionsList = document.getElementById('readingQuestionsList');

  if (title) title.textContent = data.title;
  if (badgeLevel) badgeLevel.textContent = data.level;
  if (body) {
    body.innerHTML = data.body.split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('');
  }

  if (questionsList && data.questions) {
    questionsList.innerHTML = data.questions.map((q, qIdx) => `
      <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/80 space-y-3">
        <p class="font-semibold text-sm text-slate-100">${qIdx + 1}. ${escapeHtml(q.q)}</p>
        <div class="space-y-1.5">
          ${q.options.map((opt, optIdx) => `
            <label class="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-700/50 cursor-pointer text-xs text-slate-300">
              <input type="radio" name="question_${qIdx}" value="${optIdx}" class="text-indigo-600 focus:ring-indigo-500 bg-slate-900 border-slate-700">
              <span>${escapeHtml(opt)}</span>
            </label>
          `).join('')}
        </div>
        <div class="reading-explanation hidden text-xs p-2.5 rounded-lg" id="explanation_${qIdx}"></div>
      </div>
    `).join('');
  }
}

async function handleGenerateAiReading() {
  const readingLevel = document.getElementById('readingLevel')?.value || 'B1';
  const readingTopic = document.getElementById('readingTopic')?.selectedOptions[0]?.text || 'AI & Technology';
  const btn = document.getElementById('btnGenerateReading');

  if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tạo bài đọc...';

  const systemInstruction = `You are an English reading test creator.
Generate an engaging 3-paragraph reading passage and 3 multiple-choice comprehension questions for the topic and level.
Return ONLY valid JSON matching this schema:
{
  "title": "Article Title",
  "level": "Level ${readingLevel}",
  "body": "Paragraph 1...\\n\\nParagraph 2...\\n\\nParagraph 3...",
  "questions": [
    {
      "q": "Question text?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct": 0,
      "explanation": "Giải thích chi tiết bằng tiếng Việt tại sao đáp án này đúng."
    }
  ]
}`;

  try {
    const raw = await callGemini(`Topic: ${readingTopic}, Level: ${readingLevel}`, systemInstruction);
    let parsed;
    const match = raw.match(/\{[\s\S]*\}/);
    if (match) {
      parsed = JSON.parse(match[0]);
    }

    if (parsed && parsed.body) {
      PRESET_READINGS[readingLevel] = parsed;
      renderReadingArticle(parsed);
      addXp(25);
      triggerConfetti();
    }
  } catch (err) {
    console.error(err);
    alert('Không thể tạo bài đọc lúc này. Vui lòng thử lại!');
  } finally {
    if (btn) btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> AI Tạo Bài Đọc Mới';
  }
}

function handleSubmitReadingQuiz() {
  const currentLevel = document.getElementById('readingLevel')?.value || 'B1';
  const articleData = PRESET_READINGS[currentLevel] || PRESET_READINGS.B1;
  if (!articleData || !articleData.questions) return;

  let correctCount = 0;
  articleData.questions.forEach((q, idx) => {
    const selectedInput = document.querySelector(`input[name="question_${idx}"]:checked`);
    const explBox = document.getElementById(`explanation_${idx}`);
    if (!explBox) return;

    if (selectedInput && parseInt(selectedInput.value, 10) === q.correct) {
      correctCount++;
      explBox.className = 'reading-explanation block text-xs p-2.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
      explBox.innerHTML = `<i class="fa-solid fa-circle-check mr-1"></i> Đúng! ${escapeHtml(q.explanation)}`;
    } else {
      explBox.className = 'reading-explanation block text-xs p-2.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/40';
      explBox.innerHTML = `<i class="fa-solid fa-circle-xmark mr-1"></i> Chưa chính xác. Đáp án đúng: <strong>${escapeHtml(q.options[q.correct])}</strong><br>${escapeHtml(q.explanation)}`;
    }
  });

  addXp(correctCount * 10);
  if (correctCount === articleData.questions.length) {
    triggerConfetti();
  }
  alert(`Bạn đã làm đúng ${correctCount}/${articleData.questions.length} câu! (+${correctCount * 10} XP)`);
}

// ==================== TAB 5: PRONUNCIATION & SHADOWING ====================
function initPronunciationTab() {
  const btnNewSentence = document.getElementById('btnNewPronounceSentence');
  const btnListenPronounce = document.getElementById('btnListenPronounce');
  const btnRecordPronounce = document.getElementById('btnRecordPronounce');

  renderPronunciationSentence();

  btnNewSentence?.addEventListener('click', () => {
    state.currentPronounceIdx = (state.currentPronounceIdx + 1) % PRONUNCIATION_SENTENCES.length;
    renderPronunciationSentence();
  });

  btnListenPronounce?.addEventListener('click', () => {
    const item = PRONUNCIATION_SENTENCES[state.currentPronounceIdx];
    if (item) speakText(item.text, 'en-US', 0.85); // Slightly slower for clear shadowing
  });

  btnRecordPronounce?.addEventListener('click', () => {
    toggleSpeechRecognition('pronounce');
  });
}

function renderPronunciationSentence() {
  const item = PRONUNCIATION_SENTENCES[state.currentPronounceIdx];
  if (!item) return;

  const targetText = document.getElementById('pronounceTargetText');
  const ipaText = document.getElementById('pronounceIpaText');
  const meaningText = document.getElementById('pronounceMeaningText');
  const levelBadge = document.getElementById('pronounceLevelBadge');
  const resultBox = document.getElementById('pronounceResultBox');

  if (targetText) targetText.textContent = `"${item.text}"`;
  if (ipaText) ipaText.textContent = item.ipa;
  if (meaningText) meaningText.textContent = `"${item.vi}"`;
  if (levelBadge) levelBadge.textContent = `Level: ${item.level}`;
  resultBox?.classList.add('hidden');
}

function handlePronunciationSpeechResult(spokenText) {
  const currentItem = PRONUNCIATION_SENTENCES[state.currentPronounceIdx];
  if (!currentItem) return;

  const resultBox = document.getElementById('pronounceResultBox');
  const userSpokenText = document.getElementById('userSpokenText');
  const accuracyBadge = document.getElementById('pronounceAccuracyBadge');
  const feedbackTip = document.getElementById('pronounceFeedbackTip');

  resultBox?.classList.remove('hidden');
  if (userSpokenText) userSpokenText.textContent = `"${spokenText}"`;

  // Calculate word match similarity
  const targetWords = currentItem.text.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/);
  const spokenWords = spokenText.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/);

  let matchCount = 0;
  targetWords.forEach(w => {
    if (spokenWords.includes(w)) matchCount++;
  });

  const accuracy = Math.min(100, Math.round((matchCount / targetWords.length) * 100));

  if (accuracyBadge) {
    accuracyBadge.textContent = `Độ khớp: ${accuracy}%`;
    if (accuracy >= 80) {
      accuracyBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
    } else if (accuracy >= 50) {
      accuracyBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30';
    } else {
      accuracyBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30';
    }
  }

  if (feedbackTip) {
    if (accuracy >= 85) {
      feedbackTip.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 mt-0.5"></i> <span>Phát âm xuất sắc! Bạn phát âm rõ ràng, nhịp điệu và ngữ điệu rất chuẩn xác. (+20 XP)</span>`;
      addXp(20);
      triggerConfetti();
    } else if (accuracy >= 60) {
      feedbackTip.innerHTML = `<i class="fa-solid fa-circle-info text-amber-400 mt-0.5"></i> <span>Khá tốt! Hãy chú ý các âm nối và phát âm rõ âm đuôi (ending sounds) hơn một chút nhé. (+10 XP)</span>`;
      addXp(10);
    } else {
      feedbackTip.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400 mt-0.5"></i> <span>Hãy bấm nút 'Nghe Giọng Mẫu Chuẩn' để nghe lại và thử nói chậm rãi từng cụm từ nhé! (+5 XP)</span>`;
      addXp(5);
    }
  }
}

// ==================== UTILITY FUNCTIONS ====================
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

