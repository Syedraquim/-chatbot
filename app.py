from flask import Flask, request, jsonify, send_from_directory
import re
import random
import hashlib
from collections import Counter
import math
import os

app = Flask(__name__, static_folder='static')

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────

def tokenize(text):
    return re.findall(r'\b[a-z]+\b', text.lower())

def sentence_split(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

# ─────────────────────────────────────────────
# 1. PARAPHRASING
# ─────────────────────────────────────────────

SYNONYM_MAP = {
    "happy": ["joyful", "pleased", "content", "delighted", "cheerful"],
    "sad": ["unhappy", "sorrowful", "melancholy", "downcast", "gloomy"],
    "big": ["large", "enormous", "vast", "sizable", "substantial"],
    "small": ["tiny", "little", "compact", "miniature", "slight"],
    "fast": ["quick", "swift", "rapid", "speedy", "brisk"],
    "slow": ["gradual", "unhurried", "leisurely", "measured", "sluggish"],
    "good": ["excellent", "superior", "fine", "admirable", "commendable"],
    "bad": ["poor", "inferior", "unsatisfactory", "substandard", "inadequate"],
    "important": ["significant", "crucial", "vital", "essential", "critical"],
    "show": ["demonstrate", "illustrate", "reveal", "display", "present"],
    "make": ["create", "produce", "generate", "develop", "construct"],
    "get": ["obtain", "acquire", "receive", "gain", "secure"],
    "use": ["utilize", "employ", "apply", "leverage", "implement"],
    "say": ["state", "mention", "express", "convey", "articulate"],
    "think": ["believe", "consider", "regard", "perceive", "conclude"],
    "help": ["assist", "support", "aid", "facilitate", "enable"],
    "need": ["require", "necessitate", "demand", "call for", "depend on"],
    "many": ["numerous", "several", "various", "multiple", "abundant"],
    "often": ["frequently", "regularly", "commonly", "routinely", "repeatedly"],
    "very": ["extremely", "highly", "remarkably", "considerably", "exceptionally"],
    "start": ["begin", "initiate", "commence", "launch", "undertake"],
    "end": ["conclude", "finish", "complete", "finalize", "terminate"],
    "new": ["novel", "innovative", "modern", "contemporary", "recent"],
    "old": ["ancient", "traditional", "established", "longstanding", "classic"],
    "easy": ["simple", "straightforward", "effortless", "uncomplicated", "accessible"],
    "hard": ["difficult", "challenging", "demanding", "complex", "rigorous"],
    "beautiful": ["stunning", "gorgeous", "elegant", "exquisite", "magnificent"],
    "interesting": ["fascinating", "engaging", "compelling", "intriguing", "captivating"],
    "problem": ["challenge", "issue", "obstacle", "difficulty", "concern"],
    "idea": ["concept", "notion", "proposal", "suggestion", "thought"],
    "work": ["function", "operate", "perform", "execute", "accomplish"],
    "people": ["individuals", "persons", "human beings", "folks", "community members"],
    "time": ["period", "duration", "interval", "moment", "occasion"],
    "way": ["method", "approach", "manner", "means", "technique"],
    "place": ["location", "area", "region", "site", "venue"],
    "world": ["globe", "earth", "society", "realm", "domain"],
    "life": ["existence", "living", "experience", "journey", "reality"],
    "long": ["extended", "lengthy", "prolonged", "extensive", "sustained"],
    "high": ["elevated", "significant", "considerable", "substantial", "notable"],
    "low": ["minimal", "reduced", "limited", "modest", "slight"],
    "change": ["alter", "modify", "transform", "adjust", "revise"],
    "create": ["develop", "establish", "build", "form", "design"],
    "provide": ["offer", "supply", "deliver", "furnish", "give"],
    "increase": ["grow", "rise", "expand", "enhance", "boost"],
    "reduce": ["decrease", "lower", "minimize", "cut", "diminish"],
    "allow": ["permit", "enable", "facilitate", "authorize", "support"],
    "include": ["encompass", "incorporate", "involve", "comprise", "contain"],
    "understand": ["comprehend", "grasp", "recognize", "appreciate", "realize"],
    "ensure": ["guarantee", "confirm", "secure", "verify", "maintain"],
}

SENTENCE_RESTRUCTURE_PATTERNS = [
    # Active to passive-ish and restructuring
    (r'^(\w+)\s+is\s+(.+)$', lambda m: f"What can be described as {m.group(2)} is {m.group(1)}."),
    (r'^It\s+is\s+(.+)\s+that\s+(.+)$', lambda m: f"{m.group(2).capitalize()}, which is {m.group(1)}."),
    (r'^(\w+)\s+are\s+(.+)$', lambda m: f"Among things worth noting, {m.group(1)} are {m.group(2)}."),
    (r'^The\s+(\w+)\s+(.+)$', lambda m: f"Regarding the {m.group(1)}, {m.group(2)}."),
    (r'^(\w+)\s+can\s+(.+)$', lambda m: f"It is possible for {m.group(1)} to {m.group(2)}."),
    (r'^(\w+)\s+should\s+(.+)$', lambda m: f"It is recommended that {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+will\s+(.+)$', lambda m: f"In the future, {m.group(1)} will {m.group(2)}."),
    (r'^This\s+(.+)$', lambda m: f"The {m.group(1)}"),
    (r'^There\s+is\s+(.+)$', lambda m: f"One can observe that {m.group(1)}."),
    (r'^(\w+)\s+has\s+(.+)$', lambda m: f"Notably, {m.group(1)} possesses {m.group(2)}."),
]

def replace_synonyms(text, intensity=0.5):
    words = text.split()
    result = []
    for word in words:
        clean = word.lower().strip('.,!?;:"\'-')
        punct = word[len(clean):] if word.endswith(tuple('.,!?;:"\'-')) else ''
        if clean in SYNONYM_MAP and random.random() < intensity:
            replacement = random.choice(SYNONYM_MAP[clean])
            # Preserve capitalization
            if word[0].isupper():
                replacement = replacement.capitalize()
            result.append(replacement + punct)
        else:
            result.append(word)
    return ' '.join(result)

def restructure_sentence(sentence):
    for pattern, transform in SENTENCE_RESTRUCTURE_PATTERNS:
        m = re.match(pattern, sentence, re.IGNORECASE)
        if m:
            try:
                return transform(m)
            except:
                pass
    return sentence

def paraphrase(text):
    sentences = sentence_split(text)
    paraphrased = []
    for i, sent in enumerate(sentences):
        # Alternate: synonym replacement and restructuring
        if i % 2 == 0:
            result = replace_synonyms(sent, intensity=0.6)
            result = restructure_sentence(result)
        else:
            result = restructure_sentence(sent)
            result = replace_synonyms(result, intensity=0.5)
        paraphrased.append(result)
    return ' '.join(paraphrased)

# ─────────────────────────────────────────────
# 2. PARAGRAPH GENERATION
# ─────────────────────────────────────────────

TOPIC_TEMPLATES = {
    "technology": [
        "Technology has fundamentally transformed the way humans interact with the world. From the invention of the printing press to the rise of artificial intelligence, each technological leap has redefined society's structure and individual behavior. In today's digital era, {topic} continues to evolve at an unprecedented pace, enabling innovations that were once considered science fiction. Businesses, governments, and individuals are adapting rapidly, recognizing that those who embrace change will thrive while those who resist risk obsolescence. The future of technology promises even greater disruption, with breakthroughs in {topic} shaping industries, economies, and the very fabric of human connection.",
        "The rapid advancement of {topic} represents one of the most significant shifts in modern civilization. Engineers, researchers, and visionaries across the globe are pushing the boundaries of what machines and software can achieve. Every breakthrough in {topic} opens new doors while simultaneously raising important ethical and social questions. How we navigate these developments will determine whether technology serves humanity's best interests or undermines them. Ultimately, a balanced approach that encourages innovation while safeguarding human values will be essential for sustainable progress.",
    ],
    "health": [
        "Health is the cornerstone of a fulfilling human life, encompassing physical, mental, and emotional well-being. Research into {topic} has revealed that small, consistent lifestyle changes yield the most lasting results. Nutrition, exercise, sleep, and stress management are deeply interconnected pillars of overall wellness. Modern medicine continues to make remarkable strides, yet prevention remains far more effective than cure. By understanding and investing in {topic}, individuals and communities can reduce the burden of chronic disease and enhance quality of life for generations to come.",
        "The science of {topic} has grown enormously over the past century, giving us unprecedented insight into the human body's remarkable capabilities and vulnerabilities. Public health initiatives that focus on {topic} have dramatically increased life expectancy in many parts of the world. Yet significant disparities remain, highlighting the need for equitable access to healthcare resources and education. Empowering individuals with accurate knowledge about {topic} is one of the most effective strategies for building healthier societies.",
    ],
    "education": [
        "Education is the most powerful instrument available to society for transforming lives and driving progress. The study of {topic} reveals that effective learning goes far beyond memorizing facts — it requires critical thinking, creativity, and the ability to apply knowledge in real-world contexts. Modern educational systems are being challenged to evolve, incorporating technology and student-centered methods to meet the diverse needs of learners. Investment in {topic} yields extraordinary returns, not just economically but in terms of social cohesion and democratic participation.",
        "{topic} forms the bedrock upon which informed, capable citizens are built. From early childhood development to lifelong learning, education shapes how individuals perceive themselves and their place in the world. Innovative approaches to {topic} are dismantling traditional barriers and making quality learning accessible to more people than ever before. As automation transforms the job market, the ability to think critically and adapt quickly — skills cultivated through strong education — becomes increasingly invaluable.",
    ],
    "environment": [
        "The natural environment sustains all life on Earth, yet human activity has placed it under extraordinary strain. Understanding {topic} is no longer an academic pursuit — it is an urgent necessity. Climate change, biodiversity loss, and pollution are interconnected crises that demand coordinated global action. Sustainable practices in energy, agriculture, manufacturing, and consumption offer viable pathways forward. By prioritizing {topic} in policy, business, and everyday choices, humanity can preserve the ecological systems that future generations depend upon.",
        "{topic} sits at the heart of humanity's most pressing challenge: maintaining a livable planet in the face of rapid industrialization. Scientific consensus is clear — without significant changes to how we produce and consume, the consequences will be severe and irreversible. However, there is reason for optimism. Renewable energy, circular economies, and nature-based solutions demonstrate that prosperity and environmental responsibility are not mutually exclusive. Commitment to {topic} at every level — individual, corporate, and governmental — is the defining challenge of our era.",
    ],
    "business": [
        "The world of business is in constant flux, shaped by technological disruption, shifting consumer preferences, and evolving global dynamics. Success in {topic} demands both strategic vision and operational excellence. Companies that thrive are those that innovate relentlessly, cultivate strong organizational cultures, and respond nimbly to change. At its core, {topic} is about creating value — for customers, employees, shareholders, and society at large. In an increasingly competitive landscape, sustainable business practices are not just ethically desirable but strategically essential.",
        "{topic} drives economic growth and provides livelihoods for billions of people worldwide. The principles underlying successful business — understanding markets, managing resources, building relationships, and delivering value — are timeless, even as the tools and contexts change. Today's business leaders must navigate digital transformation, geopolitical uncertainty, and heightened expectations around social responsibility. Those who master {topic} with integrity and adaptability will be best positioned to build organizations that endure and contribute meaningfully to the world.",
    ],
    "science": [
        "Science is humanity's most reliable method for understanding the universe, advancing through observation, experimentation, and rigorous peer review. The field of {topic} has yielded discoveries that have saved countless lives, expanded human knowledge, and inspired new technologies. The scientific process, though slow and often frustrating, is self-correcting — an extraordinary feature that distinguishes it from dogma. Investment in fundamental research into {topic} pays dividends that are difficult to predict but invariably significant over time.",
        "From ancient astronomers mapping the stars to modern physicists probing subatomic particles, the pursuit of {topic} reflects humanity's deepest curiosity about existence. Science thrives on questioning assumptions and challenging established ideas, a quality that has driven every major paradigm shift in history. Today, collaboration across disciplines and borders accelerates discovery in {topic} faster than any single institution could achieve alone. Communicating these discoveries clearly and accessibly to the public remains a critical challenge and responsibility.",
    ],
    "default": [
        "{topic} is a subject of considerable importance and broad relevance in today's world. Those who engage deeply with {topic} discover layers of complexity that reward careful study and open-minded inquiry. The implications of understanding {topic} extend across personal, professional, and societal dimensions, making it a worthy focus of attention and discussion. As perspectives evolve and new information emerges, the conversation around {topic} continues to grow richer and more nuanced.",
        "A thorough examination of {topic} reveals both challenges and opportunities that merit thoughtful consideration. Experts across various fields have contributed valuable insights into {topic}, building a body of knowledge that continues to expand. Engaging with this subject fosters greater awareness and equips individuals with the understanding needed to make informed decisions. Ultimately, the significance of {topic} lies in its capacity to inform, inspire, and guide meaningful action.",
    ]
}

def detect_topic_category(topic):
    topic_lower = topic.lower()
    keywords = {
        "technology": ["tech", "ai", "software", "computer", "digital", "internet", "robot", "machine", "data", "cyber", "code", "app"],
        "health": ["health", "wellness", "medical", "fitness", "diet", "exercise", "mental", "nutrition", "medicine", "disease"],
        "education": ["education", "learning", "school", "university", "teaching", "study", "knowledge", "training", "academic"],
        "environment": ["environment", "climate", "nature", "ecology", "pollution", "sustainable", "green", "carbon", "ocean", "biodiversity"],
        "business": ["business", "market", "economy", "finance", "invest", "startup", "company", "corporate", "entrepreneur", "trade"],
        "science": ["science", "research", "experiment", "physics", "chemistry", "biology", "space", "quantum", "lab", "discovery"],
    }
    for category, words in keywords.items():
        if any(w in topic_lower for w in words):
            return category
    return "default"

def generate_paragraph(topic):
    category = detect_topic_category(topic)
    templates = TOPIC_TEMPLATES.get(category, TOPIC_TEMPLATES["default"])
    template = random.choice(templates)
    paragraph = template.replace("{topic}", topic)
    return paragraph

# ─────────────────────────────────────────────
# 3. TONE ADJUSTMENT
# ─────────────────────────────────────────────

TONE_WORD_MAP = {
    "formal": {
        "but": "however", "also": "furthermore", "so": "therefore",
        "big": "substantial", "small": "minimal", "get": "obtain",
        "show": "demonstrate", "use": "utilize", "need": "require",
        "want": "desire", "tell": "inform", "ask": "inquire",
        "i think": "it is believed that", "you": "one",
        "can't": "cannot", "won't": "will not", "don't": "do not",
        "isn't": "is not", "aren't": "are not", "it's": "it is",
        "let's": "let us", "we're": "we are", "they're": "they are",
        "ok": "acceptable", "okay": "acceptable", "yeah": "yes",
        "a lot": "considerably", "lots of": "numerous",
    },
    "casual": {
        "however": "but", "furthermore": "also", "therefore": "so",
        "substantial": "big", "minimal": "small", "obtain": "get",
        "demonstrate": "show", "utilize": "use", "require": "need",
        "desire": "want", "inform": "tell", "inquire": "ask",
        "it is believed": "I think", "one": "you",
        "cannot": "can't", "will not": "won't", "do not": "don't",
        "is not": "isn't", "are not": "aren't", "it is": "it's",
        "let us": "let's", "we are": "we're", "they are": "they're",
        "acceptable": "okay", "yes": "yeah", "considerably": "a lot",
        "numerous": "lots of",
    },
    "professional": {
        "but": "however", "also": "additionally", "so": "consequently",
        "i think": "our analysis suggests", "you": "stakeholders",
        "good": "effective", "bad": "suboptimal", "big": "significant",
        "small": "limited", "need": "require", "help": "support",
        "use": "leverage", "show": "demonstrate", "make": "develop",
        "can't": "cannot", "won't": "will not", "don't": "do not",
        "ok": "satisfactory", "okay": "satisfactory",
        "a lot": "substantially", "lots of": "a significant number of",
    }
}

TONE_STARTERS = {
    "formal": [
        "It is imperative to note that",
        "Upon careful consideration,",
        "In accordance with established principles,",
        "It should be observed that",
    ],
    "casual": [
        "So basically,",
        "Here's the thing —",
        "Just so you know,",
        "Honestly,",
    ],
    "professional": [
        "From a strategic standpoint,",
        "Based on current analysis,",
        "To maximize outcomes,",
        "In alignment with best practices,",
    ]
}

def adjust_tone(text, tone):
    tone = tone.lower()
    if tone not in TONE_WORD_MAP:
        return text

    word_map = TONE_WORD_MAP[tone]
    result = text

    # Sort by length (longest first) to avoid partial replacements
    for phrase in sorted(word_map.keys(), key=len, reverse=True):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        def replace_match(m, repl=word_map[phrase]):
            if m.group(0)[0].isupper():
                return repl.capitalize()
            return repl
        result = pattern.sub(replace_match, result)

    # Optionally prepend a tone-appropriate opener to first sentence
    sentences = sentence_split(result)
    if sentences and random.random() > 0.5:
        opener = random.choice(TONE_STARTERS[tone])
        sentences[0] = f"{opener} {sentences[0][0].lower()}{sentences[0][1:]}"
        result = ' '.join(sentences)

    return result

# ─────────────────────────────────────────────
# 4. PLAGIARISM CHECK
# ─────────────────────────────────────────────

# A small corpus of "known" texts to compare against
KNOWN_CORPUS = [
    "To be or not to be, that is the question.",
    "It was the best of times, it was the worst of times.",
    "All men are created equal.",
    "We hold these truths to be self-evident.",
    "Four score and seven years ago.",
    "Ask not what your country can do for you, ask what you can do for your country.",
    "I have a dream that my four little children will one day live in a nation where they will not be judged by the color of their skin.",
    "The only thing we have to fear is fear itself.",
    "That's one small step for man, one giant leap for mankind.",
    "In the beginning, God created the heavens and the earth.",
    "It is a truth universally acknowledged that a single man in possession of a good fortune must be in want of a wife.",
    "Call me Ishmael.",
    "The quick brown fox jumps over the lazy dog.",
    "To be prepared for war is one of the most effective means of preserving peace.",
    "The internet is the world's largest library.",
    "Artificial intelligence is the new electricity.",
    "Data is the new oil.",
    "Content is king.",
    "Think different.",
    "Just do it.",
    "The future is already here, it's just not evenly distributed.",
    "Technology is neither good nor bad, nor is it neutral.",
    "The medium is the message.",
    "Knowledge is power.",
    "Time is money.",
    "Actions speak louder than words.",
    "The pen is mightier than the sword.",
    "All that glitters is not gold.",
    "Where there is a will, there is a way.",
    "Practice makes perfect.",
]

def cosine_similarity(vec1, vec2):
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    dot = sum(vec1[w] * vec2[w] for w in common)
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

def text_to_tfidf_vector(text, corpus):
    tokens = tokenize(text)
    if not tokens:
        return {}
    tf = Counter(tokens)
    total = len(tokens)
    tf_norm = {w: c / total for w, c in tf.items()}

    all_corpus_tokens = [tokenize(doc) for doc in corpus]
    N = len(corpus) + 1
    idf = {}
    for word in tf_norm:
        df = sum(1 for doc_tokens in all_corpus_tokens if word in doc_tokens) + 1
        idf[word] = math.log(N / df)

    return {w: tf_norm[w] * idf[w] for w in tf_norm}

def check_plagiarism(text):
    input_vec = text_to_tfidf_vector(text, KNOWN_CORPUS)
    input_tokens = set(tokenize(text))

    results = []
    for known in KNOWN_CORPUS:
        known_vec = text_to_tfidf_vector(known, KNOWN_CORPUS)
        sim = cosine_similarity(input_vec, known_vec)

        # Also check n-gram overlap (bigrams)
        known_tokens = set(tokenize(known))
        overlap = len(input_tokens & known_tokens)
        overlap_ratio = overlap / max(len(input_tokens), 1)

        combined_score = (sim * 0.6 + overlap_ratio * 0.4)

        if combined_score > 0.08:
            results.append({
                "source": known[:80] + ("..." if len(known) > 80 else ""),
                "similarity": round(combined_score * 100, 1)
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    top_results = results[:3]

    max_sim = max((r["similarity"] for r in top_results), default=0)

    if max_sim >= 70:
        risk = "High"
        color = "red"
        summary = "This text shows significant similarity to known sources. It may be plagiarized."
    elif max_sim >= 35:
        risk = "Moderate"
        color = "orange"
        summary = "This text has moderate similarity to some known sources. Review recommended."
    elif max_sim >= 15:
        risk = "Low"
        color = "yellow"
        summary = "Minimal similarity detected. The text appears mostly original."
    else:
        risk = "None"
        color = "green"
        summary = "No significant matches found. The text appears to be original."

    # Uniqueness heuristic based on vocabulary richness
    tokens = tokenize(text)
    unique_ratio = len(set(tokens)) / max(len(tokens), 1)
    originality_score = round(min(100, unique_ratio * 100 + (100 - max_sim) * 0.5), 1)

    return {
        "risk": risk,
        "color": color,
        "summary": summary,
        "originality_score": originality_score,
        "matches": top_results,
        "word_count": len(tokens),
        "unique_words": len(set(tokens)),
    }

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/paraphrase', methods=['POST'])
def api_paraphrase():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    result = paraphrase(text)
    return jsonify({"result": result})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({"error": "No topic provided."}), 400
    result = generate_paragraph(topic)
    return jsonify({"result": result})

@app.route('/api/tone', methods=['POST'])
def api_tone():
    data = request.get_json()
    text = data.get('text', '').strip()
    tone = data.get('tone', 'formal').strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    result = adjust_tone(text, tone)
    return jsonify({"result": result})

@app.route('/api/plagiarism', methods=['POST'])
def api_plagiarism():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    result = check_plagiarism(text)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
