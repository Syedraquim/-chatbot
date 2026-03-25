from flask import Flask, request, jsonify, send_from_directory
import re
import random
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

# ═══════════════════════════════════════════════════════════════
# 1. PARAPHRASING  —  300+ synonym entries + 30 restructure patterns
# ═══════════════════════════════════════════════════════════════

SYNONYM_MAP = {
    # Emotions & feelings
    "happy":        ["joyful", "pleased", "content", "delighted", "cheerful", "elated", "ecstatic", "thrilled"],
    "sad":          ["unhappy", "sorrowful", "melancholy", "downcast", "gloomy", "dejected", "despondent", "forlorn"],
    "angry":        ["furious", "irritated", "enraged", "irate", "outraged", "incensed", "agitated", "vexed"],
    "scared":       ["frightened", "terrified", "anxious", "apprehensive", "alarmed", "petrified", "nervous", "uneasy"],
    "surprised":    ["astonished", "amazed", "astounded", "stunned", "startled", "flabbergasted", "shocked", "bewildered"],
    "tired":        ["exhausted", "weary", "fatigued", "drained", "lethargic", "sleepy", "spent", "worn out"],
    "excited":      ["enthusiastic", "eager", "animated", "energized", "thrilled", "fervent", "passionate", "exhilarated"],
    "confused":     ["perplexed", "puzzled", "baffled", "bewildered", "disoriented", "mystified", "uncertain"],
    "proud":        ["gratified", "honored", "pleased", "satisfied", "triumphant", "dignified", "fulfilled"],
    "lonely":       ["isolated", "solitary", "abandoned", "forlorn", "desolate", "withdrawn", "alienated"],
    "curious":      ["inquisitive", "eager", "interested", "intrigued", "fascinated", "exploratory", "questioning"],
    "nervous":      ["anxious", "tense", "uneasy", "apprehensive", "jittery", "restless", "edgy", "unsettled"],
    "brave":        ["courageous", "bold", "fearless", "daring", "valiant", "heroic", "audacious", "intrepid"],
    "calm":         ["serene", "peaceful", "composed", "tranquil", "relaxed", "placid", "unruffled", "collected"],
    "grateful":     ["thankful", "appreciative", "indebted", "obliged", "beholden", "recognizant"],

    # Size & degree
    "big":          ["large", "enormous", "vast", "sizable", "substantial", "immense", "colossal", "massive"],
    "small":        ["tiny", "little", "compact", "miniature", "slight", "petite", "microscopic", "negligible"],
    "huge":         ["gigantic", "tremendous", "monumental", "colossal", "mammoth", "towering", "staggering"],
    "tiny":         ["minuscule", "microscopic", "infinitesimal", "diminutive", "negligible", "meager"],
    "long":         ["extended", "lengthy", "prolonged", "extensive", "sustained", "protracted", "drawn-out"],
    "short":        ["brief", "concise", "compact", "abbreviated", "succinct", "fleeting", "cursory"],
    "high":         ["elevated", "significant", "considerable", "substantial", "notable", "towering", "lofty"],
    "low":          ["minimal", "reduced", "limited", "modest", "slight", "meager", "negligible", "scant"],
    "deep":         ["profound", "intense", "thorough", "extensive", "penetrating", "far-reaching"],
    "wide":         ["broad", "expansive", "extensive", "sweeping", "vast", "all-encompassing"],
    "full":         ["complete", "entire", "whole", "comprehensive", "thorough", "total", "exhaustive"],
    "empty":        ["vacant", "hollow", "bare", "void", "devoid", "unfilled", "depleted"],

    # Speed & time
    "fast":         ["quick", "swift", "rapid", "speedy", "brisk", "hasty", "expeditious", "prompt", "nimble"],
    "slow":         ["gradual", "unhurried", "leisurely", "measured", "sluggish", "deliberate", "plodding", "languid"],
    "soon":         ["shortly", "promptly", "imminently", "before long", "presently", "in due course"],
    "often":        ["frequently", "regularly", "commonly", "routinely", "repeatedly", "habitually", "consistently"],
    "always":       ["invariably", "perpetually", "consistently", "unfailingly", "ceaselessly", "at all times"],
    "never":        ["at no time", "under no circumstances", "in no way", "by no means", "not once"],
    "sometimes":    ["occasionally", "periodically", "from time to time", "now and then", "intermittently"],
    "recently":     ["lately", "in recent times", "of late", "not long ago", "in the recent past"],
    "eventually":   ["ultimately", "in due course", "over time", "finally", "at length", "sooner or later"],
    "immediately":  ["instantly", "at once", "right away", "without delay", "promptly", "forthwith"],

    # Quality
    "good":         ["excellent", "superior", "fine", "admirable", "commendable", "exceptional", "outstanding", "superb"],
    "bad":          ["poor", "inferior", "unsatisfactory", "substandard", "inadequate", "flawed", "deficient"],
    "great":        ["remarkable", "extraordinary", "magnificent", "splendid", "phenomenal", "exceptional", "stellar"],
    "terrible":     ["dreadful", "awful", "horrendous", "atrocious", "appalling", "deplorable", "ghastly"],
    "wonderful":    ["marvelous", "spectacular", "extraordinary", "breathtaking", "astonishing", "magnificent"],
    "awful":        ["dreadful", "horrific", "appalling", "ghastly", "abysmal", "dire", "wretched"],
    "beautiful":    ["stunning", "gorgeous", "elegant", "exquisite", "magnificent", "radiant", "breathtaking", "sublime"],
    "ugly":         ["unattractive", "unsightly", "hideous", "grotesque", "repulsive", "unpleasant"],
    "clean":        ["spotless", "immaculate", "pristine", "pure", "sanitized", "tidy", "uncontaminated"],
    "dirty":        ["filthy", "contaminated", "polluted", "grimy", "soiled", "tainted", "impure"],
    "perfect":      ["flawless", "ideal", "impeccable", "exemplary", "optimal", "faultless", "immaculate"],
    "average":      ["ordinary", "mediocre", "middling", "moderate", "typical", "standard", "unremarkable"],

    # Importance & necessity
    "important":    ["significant", "crucial", "vital", "essential", "critical", "paramount", "indispensable", "pivotal"],
    "necessary":    ["essential", "required", "mandatory", "indispensable", "obligatory", "imperative", "compulsory"],
    "useful":       ["beneficial", "practical", "valuable", "advantageous", "effective", "functional", "helpful"],
    "useless":      ["futile", "ineffective", "pointless", "redundant", "worthless", "unproductive", "vain"],
    "special":      ["unique", "distinctive", "extraordinary", "remarkable", "exceptional", "particular", "notable"],
    "common":       ["widespread", "prevalent", "ordinary", "typical", "standard", "conventional", "routine"],
    "rare":         ["uncommon", "scarce", "infrequent", "exceptional", "unusual", "seldom", "sporadic"],
    "obvious":      ["evident", "apparent", "clear", "unmistakable", "transparent", "self-evident", "plain"],
    "surprising":   ["unexpected", "astonishing", "remarkable", "startling", "unforeseen", "extraordinary"],

    # Actions - communication
    "say":          ["state", "mention", "express", "convey", "articulate", "declare", "assert", "proclaim"],
    "tell":         ["inform", "notify", "advise", "communicate", "relay", "disclose", "reveal", "report"],
    "ask":          ["inquire", "request", "query", "question", "solicit", "seek", "probe", "petition"],
    "answer":       ["respond", "reply", "address", "clarify", "explain", "acknowledge", "react"],
    "explain":      ["clarify", "elaborate", "illustrate", "describe", "outline", "interpret", "detail"],
    "write":        ["compose", "draft", "author", "document", "record", "inscribe", "pen", "formulate"],
    "read":         ["review", "examine", "study", "peruse", "scan", "analyze", "interpret"],
    "listen":       ["hear", "attend to", "pay attention to", "heed", "tune in", "consider"],
    "speak":        ["talk", "communicate", "address", "converse", "utter", "articulate", "vocalize"],
    "discuss":      ["examine", "explore", "address", "analyze", "consider", "review", "evaluate"],
    "agree":        ["concur", "consent", "approve", "affirm", "endorse", "support", "accept"],
    "disagree":     ["dispute", "contest", "challenge", "oppose", "refute", "contradict", "object"],
    "argue":        ["contend", "claim", "assert", "maintain", "propose", "reason", "debate"],
    "suggest":      ["propose", "recommend", "indicate", "imply", "hint", "advise", "advocate"],

    # Actions - thinking
    "think":        ["believe", "consider", "regard", "perceive", "conclude", "reflect", "ponder", "contemplate"],
    "know":         ["understand", "recognize", "comprehend", "be aware of", "realize", "grasp", "acknowledge"],
    "understand":   ["comprehend", "grasp", "recognize", "appreciate", "realize", "fathom", "internalize"],
    "learn":        ["acquire", "absorb", "discover", "master", "study", "grasp", "assimilate", "pick up"],
    "remember":     ["recall", "recollect", "retain", "memorize", "reminisce", "think back on"],
    "forget":       ["overlook", "neglect", "disregard", "lose track of", "fail to recall", "omit"],
    "decide":       ["determine", "resolve", "conclude", "choose", "settle on", "elect", "opt for"],
    "believe":      ["think", "suppose", "assume", "presume", "trust", "be convinced", "hold that"],
    "imagine":      ["envision", "picture", "visualize", "conceive", "dream of", "suppose", "hypothesize"],
    "realize":      ["recognize", "acknowledge", "discover", "understand", "become aware", "appreciate"],
    "consider":     ["reflect on", "contemplate", "evaluate", "assess", "weigh", "review", "deliberate"],
    "analyze":      ["examine", "investigate", "study", "assess", "evaluate", "scrutinize", "dissect"],
    "compare":      ["contrast", "juxtapose", "evaluate against", "measure against", "distinguish"],

    # Actions - physical
    "go":           ["travel", "proceed", "move", "advance", "head", "journey", "navigate", "venture"],
    "come":         ["arrive", "approach", "appear", "emerge", "reach", "turn up", "show up"],
    "walk":         ["stroll", "stride", "march", "amble", "trek", "wander", "pace", "traverse"],
    "run":          ["sprint", "dash", "race", "rush", "hurry", "jog", "charge", "bolt"],
    "look":         ["observe", "examine", "inspect", "view", "survey", "study", "watch", "scrutinize"],
    "see":          ["observe", "witness", "notice", "perceive", "spot", "detect", "behold", "view"],
    "give":         ["provide", "offer", "present", "supply", "deliver", "grant", "bestow", "contribute"],
    "take":         ["obtain", "acquire", "seize", "collect", "gather", "retrieve", "secure", "capture"],
    "put":          ["place", "position", "set", "locate", "deposit", "arrange", "situate"],
    "keep":         ["maintain", "retain", "preserve", "sustain", "hold", "store", "safeguard"],
    "hold":         ["grasp", "grip", "retain", "maintain", "keep", "carry", "possess"],
    "push":         ["propel", "drive", "thrust", "press", "advance", "promote", "urge"],
    "pull":         ["draw", "drag", "attract", "extract", "haul", "tug", "bring"],

    # Actions - creation/change
    "make":         ["create", "produce", "generate", "develop", "construct", "build", "form", "fabricate"],
    "create":       ["develop", "establish", "build", "form", "design", "produce", "generate", "originate"],
    "build":        ["construct", "erect", "assemble", "develop", "establish", "form", "craft", "engineer"],
    "break":        ["shatter", "fracture", "destroy", "dismantle", "collapse", "disrupt", "rupture"],
    "fix":          ["repair", "restore", "mend", "resolve", "correct", "rectify", "remedy", "address"],
    "change":       ["alter", "modify", "transform", "adjust", "revise", "amend", "adapt", "shift"],
    "improve":      ["enhance", "upgrade", "refine", "advance", "develop", "strengthen", "optimize", "elevate"],
    "increase":     ["grow", "rise", "expand", "enhance", "boost", "amplify", "escalate", "augment"],
    "reduce":       ["decrease", "lower", "minimize", "cut", "diminish", "shrink", "curtail", "lessen"],
    "remove":       ["eliminate", "delete", "erase", "extract", "strip", "abolish", "discard", "expunge"],
    "add":          ["include", "append", "insert", "incorporate", "attach", "supplement", "integrate"],
    "move":         ["transfer", "shift", "relocate", "transport", "migrate", "reposition", "displace"],
    "connect":      ["link", "integrate", "interface", "bridge", "join", "synchronize", "unite", "bind"],
    "separate":     ["divide", "split", "partition", "isolate", "disconnect", "detach", "segregate"],
    "combine":      ["merge", "integrate", "blend", "fuse", "unify", "consolidate", "join", "incorporate"],
    "expand":       ["extend", "grow", "enlarge", "broaden", "widen", "amplify", "scale up", "develop"],
    "limit":        ["restrict", "constrain", "cap", "confine", "bound", "curb", "inhibit", "regulate"],

    # Actions - general verbs
    "get":          ["obtain", "acquire", "receive", "gain", "secure", "retrieve", "fetch", "attain"],
    "use":          ["utilize", "employ", "apply", "leverage", "implement", "exercise", "deploy", "harness"],
    "help":         ["assist", "support", "aid", "facilitate", "enable", "guide", "back", "bolster"],
    "need":         ["require", "necessitate", "demand", "call for", "depend on", "must have"],
    "want":         ["desire", "wish for", "seek", "crave", "aspire to", "long for", "aim for"],
    "try":          ["attempt", "endeavor", "strive", "seek to", "aim to", "undertake", "pursue"],
    "show":         ["demonstrate", "illustrate", "reveal", "display", "present", "exhibit", "highlight"],
    "find":         ["discover", "locate", "identify", "uncover", "detect", "encounter", "come across"],
    "start":        ["begin", "initiate", "commence", "launch", "undertake", "embark on", "kick off"],
    "end":          ["conclude", "finish", "complete", "finalize", "terminate", "close", "wrap up"],
    "stop":         ["cease", "halt", "discontinue", "suspend", "pause", "refrain", "quit", "abandon"],
    "allow":        ["permit", "enable", "facilitate", "authorize", "support", "approve", "sanction"],
    "provide":      ["offer", "supply", "deliver", "furnish", "give", "contribute", "grant", "yield"],
    "ensure":       ["guarantee", "confirm", "secure", "verify", "maintain", "assure", "validate"],
    "include":      ["encompass", "incorporate", "involve", "comprise", "contain", "cover", "embrace"],
    "happen":       ["occur", "take place", "arise", "emerge", "unfold", "transpire", "come about"],
    "become":       ["transform into", "evolve into", "develop into", "grow into", "turn into"],
    "seem":         ["appear", "look", "come across as", "give the impression of", "feel like"],
    "mean":         ["signify", "indicate", "imply", "denote", "represent", "suggest", "convey"],
    "affect":       ["influence", "impact", "shape", "alter", "change", "modify", "touch"],
    "support":      ["back", "reinforce", "validate", "strengthen", "confirm", "uphold", "endorse"],
    "produce":      ["generate", "yield", "create", "output", "deliver", "manufacture", "develop"],
    "follow":       ["pursue", "adhere to", "comply with", "observe", "track", "trace", "accompany"],
    "lead":         ["guide", "direct", "spearhead", "head", "pioneer", "drive", "steer"],
    "achieve":      ["accomplish", "attain", "realize", "reach", "fulfill", "deliver", "complete"],
    "develop":      ["advance", "evolve", "cultivate", "grow", "expand", "refine", "progress", "build"],
    "focus":        ["concentrate", "center", "emphasize", "highlight", "prioritize", "target"],
    "measure":      ["assess", "evaluate", "quantify", "gauge", "calculate", "determine", "analyze"],
    "identify":     ["recognize", "pinpoint", "detect", "locate", "discover", "determine", "establish"],
    "address":      ["tackle", "handle", "deal with", "manage", "resolve", "confront", "respond to"],
    "apply":        ["implement", "use", "employ", "exercise", "utilize", "put into practice"],
    "involve":      ["include", "incorporate", "engage", "require", "entail", "encompass", "concern"],

    # Nouns - concepts
    "problem":      ["challenge", "issue", "obstacle", "difficulty", "concern", "complication", "setback", "dilemma"],
    "idea":         ["concept", "notion", "proposal", "suggestion", "thought", "theory", "vision", "insight"],
    "answer":       ["solution", "response", "resolution", "remedy", "explanation", "reply", "outcome"],
    "question":     ["inquiry", "query", "issue", "concern", "matter", "topic", "subject"],
    "plan":         ["strategy", "approach", "blueprint", "scheme", "roadmap", "agenda", "proposal", "framework"],
    "goal":         ["objective", "target", "aim", "purpose", "ambition", "aspiration", "mission", "intention"],
    "result":       ["outcome", "consequence", "effect", "conclusion", "product", "finding", "achievement"],
    "reason":       ["cause", "motive", "rationale", "justification", "basis", "grounds", "explanation"],
    "example":      ["illustration", "instance", "case", "model", "sample", "demonstration", "representation"],
    "information":  ["data", "knowledge", "details", "facts", "insight", "intelligence", "content", "material"],
    "knowledge":    ["understanding", "expertise", "wisdom", "insight", "awareness", "proficiency", "learning"],
    "experience":   ["exposure", "practice", "background", "involvement", "participation", "encounter"],
    "opportunity":  ["chance", "prospect", "opening", "possibility", "occasion", "potential", "avenue"],
    "challenge":    ["obstacle", "difficulty", "hurdle", "setback", "trial", "adversity", "complication"],
    "benefit":      ["advantage", "gain", "merit", "value", "reward", "asset", "upside", "positive"],
    "risk":         ["danger", "hazard", "threat", "peril", "vulnerability", "exposure", "uncertainty"],
    "effort":       ["endeavor", "attempt", "work", "exertion", "initiative", "undertaking", "energy"],
    "success":      ["achievement", "accomplishment", "triumph", "victory", "attainment", "breakthrough"],
    "failure":      ["setback", "defeat", "shortcoming", "collapse", "downfall", "mistake", "lapse"],
    "change":       ["transformation", "shift", "evolution", "transition", "alteration", "modification"],
    "impact":       ["effect", "influence", "consequence", "outcome", "result", "impression", "mark"],
    "value":        ["worth", "merit", "benefit", "significance", "importance", "utility", "advantage"],
    "approach":     ["method", "strategy", "technique", "framework", "process", "way", "manner"],
    "issue":        ["problem", "concern", "matter", "challenge", "difficulty", "question", "topic"],
    "factor":       ["element", "component", "variable", "aspect", "consideration", "feature", "determinant"],
    "level":        ["degree", "extent", "stage", "tier", "measure", "intensity", "magnitude"],
    "aspect":       ["dimension", "element", "feature", "facet", "side", "component", "characteristic"],
    "area":         ["domain", "field", "sector", "zone", "region", "sphere", "territory"],
    "role":         ["function", "responsibility", "position", "duty", "contribution", "part", "capacity"],

    # Nouns - people & society
    "people":       ["individuals", "persons", "human beings", "citizens", "community members", "populace"],
    "person":       ["individual", "human being", "soul", "figure", "character", "party", "subject"],
    "group":        ["team", "community", "collective", "assembly", "organization", "cluster", "coalition"],
    "leader":       ["director", "chief", "head", "commander", "pioneer", "authority", "executive"],
    "expert":       ["specialist", "authority", "professional", "scholar", "veteran", "master", "guru"],
    "student":      ["learner", "pupil", "scholar", "trainee", "apprentice", "novice"],
    "teacher":      ["educator", "instructor", "professor", "mentor", "coach", "facilitator", "tutor"],
    "worker":       ["employee", "staff member", "professional", "practitioner", "contributor", "operator"],
    "government":   ["administration", "authorities", "state", "regime", "leadership", "policymakers"],
    "company":      ["organization", "firm", "enterprise", "corporation", "institution", "establishment"],
    "community":    ["society", "group", "population", "neighborhood", "collective", "network", "assembly"],
    "team":         ["group", "unit", "crew", "squad", "collective", "workforce", "panel"],
    "researcher":   ["scientist", "scholar", "investigator", "analyst", "academic", "expert", "specialist"],

    # Nouns - world & nature
    "world":        ["globe", "earth", "society", "realm", "domain", "universe", "civilization", "planet"],
    "life":         ["existence", "living", "experience", "journey", "reality", "being", "livelihood"],
    "time":         ["period", "duration", "interval", "moment", "occasion", "era", "phase", "epoch"],
    "place":        ["location", "area", "region", "site", "venue", "spot", "zone", "territory"],
    "way":          ["method", "approach", "manner", "means", "technique", "path", "strategy", "mode"],
    "part":         ["component", "element", "section", "aspect", "portion", "segment", "piece", "fraction"],
    "thing":        ["element", "entity", "object", "item", "matter", "subject", "aspect", "factor"],
    "nature":       ["environment", "ecosystem", "natural world", "wilderness", "biology", "ecology"],
    "system":       ["structure", "framework", "mechanism", "network", "process", "organization", "setup"],
    "process":      ["procedure", "method", "mechanism", "workflow", "sequence", "operation", "approach"],
    "environment":  ["surroundings", "setting", "context", "ecosystem", "conditions", "landscape", "domain"],
    "society":      ["community", "civilization", "population", "culture", "public", "nation", "world"],

    # Adjectives
    "new":          ["novel", "innovative", "modern", "contemporary", "recent", "fresh", "cutting-edge", "emerging"],
    "old":          ["ancient", "traditional", "established", "longstanding", "classic", "dated", "historical"],
    "easy":         ["simple", "straightforward", "effortless", "uncomplicated", "accessible", "manageable"],
    "hard":         ["difficult", "challenging", "demanding", "complex", "rigorous", "arduous", "tough"],
    "clear":        ["evident", "obvious", "apparent", "transparent", "explicit", "plain", "unmistakable"],
    "complex":      ["intricate", "sophisticated", "multifaceted", "elaborate", "nuanced", "layered"],
    "simple":       ["basic", "elementary", "straightforward", "uncomplicated", "plain", "fundamental"],
    "strong":       ["powerful", "robust", "sturdy", "formidable", "potent", "resilient", "effective"],
    "weak":         ["fragile", "feeble", "vulnerable", "inadequate", "ineffective", "limited", "frail"],
    "rich":         ["wealthy", "prosperous", "affluent", "well-off", "abundant", "plentiful", "lavish"],
    "poor":         ["impoverished", "underprivileged", "deprived", "disadvantaged", "lacking", "scarce"],
    "interesting":  ["fascinating", "engaging", "compelling", "intriguing", "captivating", "riveting"],
    "boring":       ["tedious", "monotonous", "dull", "uninteresting", "repetitive", "stale", "mundane"],
    "different":    ["distinct", "unique", "varied", "diverse", "contrasting", "alternative", "dissimilar"],
    "similar":      ["comparable", "alike", "equivalent", "corresponding", "analogous", "related"],
    "real":         ["genuine", "authentic", "actual", "legitimate", "true", "concrete", "valid"],
    "false":        ["incorrect", "inaccurate", "erroneous", "misleading", "untrue", "fabricated"],
    "possible":     ["feasible", "viable", "achievable", "attainable", "conceivable", "realistic"],
    "impossible":   ["unachievable", "unattainable", "infeasible", "unrealistic", "inconceivable"],
    "free":         ["unrestricted", "unhindered", "liberated", "open", "independent", "autonomous"],
    "safe":         ["secure", "protected", "shielded", "risk-free", "harmless", "stable", "sheltered"],
    "dangerous":    ["hazardous", "risky", "perilous", "threatening", "harmful", "precarious", "unsafe"],
    "effective":    ["efficient", "successful", "productive", "impactful", "powerful", "capable", "potent"],
    "creative":     ["innovative", "original", "imaginative", "inventive", "resourceful", "ingenious"],
    "critical":     ["essential", "pivotal", "key", "decisive", "fundamental", "vital", "crucial"],
    "significant":  ["notable", "considerable", "substantial", "meaningful", "important", "major", "marked"],
    "major":        ["primary", "principal", "leading", "dominant", "foremost", "chief", "key"],
    "minor":        ["secondary", "marginal", "peripheral", "small", "limited", "negligible", "trivial"],
    "global":       ["worldwide", "international", "universal", "widespread", "cross-border", "planetary"],
    "local":        ["regional", "community-level", "nearby", "neighborhood", "domestic", "area-based"],
    "modern":       ["contemporary", "current", "recent", "present-day", "up-to-date", "twenty-first century"],
    "traditional":  ["conventional", "established", "time-honored", "classic", "orthodox", "customary"],
    "positive":     ["favorable", "beneficial", "constructive", "optimistic", "encouraging", "affirmative"],
    "negative":     ["unfavorable", "detrimental", "harmful", "discouraging", "adverse", "destructive"],
    "active":       ["engaged", "involved", "dynamic", "energetic", "participatory", "proactive"],
    "passive":      ["inactive", "uninvolved", "inert", "dormant", "submissive", "receptive"],
    "public":       ["communal", "collective", "shared", "open", "societal", "accessible", "general"],
    "private":      ["personal", "individual", "confidential", "exclusive", "proprietary", "internal"],

    # Adverbs & connectors
    "very":         ["extremely", "highly", "remarkably", "considerably", "exceptionally", "tremendously"],
    "really":       ["genuinely", "truly", "certainly", "indeed", "absolutely", "undeniably"],
    "also":         ["additionally", "furthermore", "moreover", "as well", "in addition", "besides"],
    "but":          ["however", "yet", "nevertheless", "although", "even so", "on the other hand"],
    "so":           ["therefore", "consequently", "thus", "hence", "as a result", "accordingly"],
    "because":      ["since", "as", "due to the fact that", "given that", "owing to the fact that"],
    "although":     ["even though", "despite the fact that", "while", "whereas", "notwithstanding"],
    "if":           ["provided that", "in the event that", "assuming that", "given that", "should"],
    "only":         ["solely", "exclusively", "merely", "just", "purely", "nothing but", "simply"],
    "just":         ["simply", "merely", "only", "purely", "entirely", "exactly", "precisely"],
    "still":        ["nevertheless", "even so", "yet", "regardless", "all the same", "nonetheless"],
    "already":      ["previously", "by now", "at this point", "beforehand", "thus far"],
    "however":      ["nevertheless", "yet", "despite this", "even so", "that said", "regardless"],
    "therefore":    ["thus", "consequently", "as a result", "hence", "accordingly", "for this reason"],
    "moreover":     ["furthermore", "additionally", "beyond this", "in addition", "what is more"],
    "meanwhile":    ["simultaneously", "at the same time", "concurrently", "in the interim", "during this"],
    "instead":      ["alternatively", "in place of", "as a substitute", "in lieu of", "rather"],
    "overall":      ["in general", "broadly speaking", "on the whole", "generally", "in summary"],
    "clearly":      ["evidently", "obviously", "plainly", "undeniably", "unmistakably", "manifestly"],
    "mainly":       ["primarily", "chiefly", "principally", "predominantly", "largely", "mostly"],

    # Technology-specific
    "data":         ["information", "statistics", "records", "metrics", "figures", "content", "material"],
    "software":     ["application", "program", "system", "tool", "platform", "solution", "code"],
    "network":      ["infrastructure", "system", "grid", "framework", "web", "connection", "channel"],
    "device":       ["gadget", "instrument", "apparatus", "tool", "hardware", "machine", "unit"],
    "digital":      ["electronic", "virtual", "computerized", "online", "cyber", "tech-based"],
    "online":       ["digital", "virtual", "web-based", "internet-based", "connected", "cloud-based"],
    "smart":        ["intelligent", "automated", "advanced", "sophisticated", "capable", "innovative"],

    # Academic / writing
    "research":     ["investigation", "study", "inquiry", "analysis", "exploration", "examination", "survey"],
    "study":        ["analysis", "examination", "investigation", "research", "review", "assessment"],
    "analysis":     ["examination", "assessment", "evaluation", "review", "breakdown", "investigation"],
    "evidence":     ["proof", "data", "findings", "support", "documentation", "indication", "substantiation"],
    "theory":       ["hypothesis", "framework", "model", "concept", "proposition", "thesis", "premise"],
    "argument":     ["claim", "assertion", "contention", "position", "stance", "proposition", "point"],
    "conclusion":   ["finding", "determination", "outcome", "deduction", "inference", "resolution"],
    "method":       ["approach", "technique", "procedure", "strategy", "means", "process", "mechanism"],
    "context":      ["setting", "background", "framework", "circumstances", "environment", "situation"],
    "perspective":  ["viewpoint", "standpoint", "outlook", "angle", "lens", "position", "vantage point"],
    "concept":      ["idea", "notion", "principle", "construct", "framework", "abstraction", "theory"],
    "framework":    ["structure", "model", "system", "approach", "paradigm", "schema", "architecture"],
}

SENTENCE_RESTRUCTURE_PATTERNS = [
    (r'^(\w+)\s+is\s+(.+)$',           lambda m: f"What can be described as {m.group(2)} is {m.group(1)}."),
    (r'^It\s+is\s+(.+)\s+that\s+(.+)$',lambda m: f"{m.group(2).capitalize()}, which is {m.group(1)}."),
    (r'^(\w+)\s+are\s+(.+)$',          lambda m: f"Among things worth noting, {m.group(1)} are {m.group(2)}."),
    (r'^The\s+(\w+)\s+(.+)$',          lambda m: f"Regarding the {m.group(1)}, {m.group(2)}."),
    (r'^(\w+)\s+can\s+(.+)$',          lambda m: f"It is possible for {m.group(1)} to {m.group(2)}."),
    (r'^(\w+)\s+should\s+(.+)$',       lambda m: f"It is recommended that {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+will\s+(.+)$',         lambda m: f"In the future, {m.group(1)} will {m.group(2)}."),
    (r'^This\s+(.+)$',                  lambda m: f"The {m.group(1)}"),
    (r'^There\s+is\s+(.+)$',           lambda m: f"One can observe that {m.group(1)}."),
    (r'^(\w+)\s+has\s+(.+)$',          lambda m: f"Notably, {m.group(1)} possesses {m.group(2)}."),
    (r'^(\w+)\s+must\s+(.+)$',         lambda m: f"It is imperative that {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+want[s]?\s+(.+)$',     lambda m: f"The desire of {m.group(1)} is to {m.group(2)}."),
    (r'^(\w+)\s+need[s]?\s+(.+)$',     lambda m: f"There exists a requirement for {m.group(1)} to {m.group(2)}."),
    (r'^(\w+)\s+help[s]?\s+(.+)$',     lambda m: f"A key role of {m.group(1)} is to assist with {m.group(2)}."),
    (r'^(\w+)\s+make[s]?\s+(.+)$',     lambda m: f"Through the actions of {m.group(1)}, {m.group(2)} is produced."),
    (r'^(\w+)\s+allow[s]?\s+(.+)$',    lambda m: f"By means of {m.group(1)}, it becomes possible to {m.group(2)}."),
    (r'^(\w+)\s+include[s]?\s+(.+)$',  lambda m: f"Among the components of {m.group(1)}, one finds {m.group(2)}."),
    (r'^(\w+)\s+provide[s]?\s+(.+)$',  lambda m: f"{m.group(1).capitalize()} serves as a source of {m.group(2)}."),
    (r'^(\w+)\s+cause[s]?\s+(.+)$',    lambda m: f"As a result of {m.group(1)}, {m.group(2)} occurs."),
    (r'^(\w+)\s+show[s]?\s+(.+)$',     lambda m: f"Evidence from {m.group(1)} demonstrates {m.group(2)}."),
    (r'^(\w+)\s+and\s+(\w+)\s+(.+)$',  lambda m: f"Both {m.group(1)} and {m.group(2)} {m.group(3)}."),
    (r'^Although\s+(.+),\s+(.+)$',     lambda m: f"Despite {m.group(1)}, {m.group(2)}."),
    (r'^Because\s+(.+),\s+(.+)$',      lambda m: f"Since {m.group(1)}, it follows that {m.group(2)}."),
    (r'^When\s+(.+),\s+(.+)$',         lambda m: f"At the point when {m.group(1)}, {m.group(2)}."),
    (r'^If\s+(.+),\s+(.+)$',           lambda m: f"Provided that {m.group(1)}, {m.group(2)}."),
    (r'^(\w+)\s+often\s+(.+)$',        lambda m: f"It is frequently the case that {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+never\s+(.+)$',        lambda m: f"Under no circumstances does {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+always\s+(.+)$',       lambda m: f"Invariably, {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+seem[s]?\s+(.+)$',     lambda m: f"It appears that {m.group(1)} {m.group(2)}."),
    (r'^(\w+)\s+feel[s]?\s+(.+)$',     lambda m: f"The experience of {m.group(1)} is one of {m.group(2)}."),
]

def replace_synonyms(text, intensity=0.5):
    words = text.split()
    result = []
    for word in words:
        clean = word.lower().strip('.,!?;:"\'-')
        punct = ''.join(c for c in word if c in '.,!?;:"\'-') if any(c in word for c in '.,!?;:"\'-') else ''
        if clean in SYNONYM_MAP and random.random() < intensity:
            replacement = random.choice(SYNONYM_MAP[clean])
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
        if i % 2 == 0:
            result = replace_synonyms(sent, intensity=0.6)
            result = restructure_sentence(result)
        else:
            result = restructure_sentence(sent)
            result = replace_synonyms(result, intensity=0.5)
        paraphrased.append(result)
    return ' '.join(paraphrased)

# ═══════════════════════════════════════════════════════════════
# 2. PARAGRAPH GENERATION  —  14 categories, 4 templates each
# ═══════════════════════════════════════════════════════════════

TOPIC_TEMPLATES = {
    "technology": [
        "Technology has fundamentally transformed the way humans interact with the world. From the invention of the printing press to the rise of artificial intelligence, each technological leap has redefined society's structure and individual behavior. In today's digital era, {topic} continues to evolve at an unprecedented pace, enabling innovations that were once considered science fiction. Businesses, governments, and individuals are adapting rapidly, recognizing that those who embrace change will thrive while those who resist risk obsolescence. The future of technology promises even greater disruption, with breakthroughs in {topic} shaping industries, economies, and the very fabric of human connection.",
        "The rapid advancement of {topic} represents one of the most significant shifts in modern civilization. Engineers, researchers, and visionaries across the globe are pushing the boundaries of what machines and software can achieve. Every breakthrough in {topic} opens new doors while simultaneously raising important ethical and social questions. How we navigate these developments will determine whether technology serves humanity's best interests or undermines them. Ultimately, a balanced approach that encourages innovation while safeguarding human values will be essential for sustainable progress.",
        "Few forces in the modern world rival the transformative power of {topic}. From reshaping entire industries to redefining how individuals communicate and consume information, its influence is both pervasive and profound. Early adopters have demonstrated that embracing {topic} yields competitive advantages, while laggards face mounting pressure to adapt or be displaced. The societal implications extend beyond economics — questions of privacy, equity, and human autonomy are increasingly central to any meaningful conversation about the trajectory of {topic} and its long-term consequences.",
        "The story of {topic} is fundamentally a story about human ambition and ingenuity. What began as a solution to isolated problems has grown into an ecosystem of interconnected innovations that now underpin daily life. The speed at which {topic} advances often outpaces society's ability to regulate or even comprehend it, creating both exciting possibilities and genuine risks. Navigating this complexity demands not only technical expertise but also philosophical clarity about the values we wish to preserve as technology continues to reshape our world.",
    ],
    "health": [
        "Health is the cornerstone of a fulfilling human life, encompassing physical, mental, and emotional well-being. Research into {topic} has revealed that small, consistent lifestyle changes yield the most lasting results. Nutrition, exercise, sleep, and stress management are deeply interconnected pillars of overall wellness. Modern medicine continues to make remarkable strides, yet prevention remains far more effective than cure. By understanding and investing in {topic}, individuals and communities can reduce the burden of chronic disease and enhance quality of life for generations to come.",
        "The science of {topic} has grown enormously over the past century, giving us unprecedented insight into the human body's remarkable capabilities and vulnerabilities. Public health initiatives that focus on {topic} have dramatically increased life expectancy in many parts of the world. Yet significant disparities remain, highlighting the need for equitable access to healthcare resources and education. Empowering individuals with accurate knowledge about {topic} is one of the most effective strategies for building healthier societies.",
        "Understanding {topic} goes far beyond diagnosing illness — it encompasses the full spectrum of human well-being. Modern approaches increasingly recognize that sustainable health outcomes require addressing root causes: socioeconomic conditions, environmental exposures, behavioral patterns, and access to care. As chronic conditions replace infectious disease as the primary driver of mortality in many regions, the importance of preventive strategies and early intervention has never been greater. Investing in {topic} at both the individual and systemic level is among the wisest decisions a society can make.",
        "The relationship between lifestyle and health outcomes has never been better understood than it is today. Decades of research into {topic} have established that diet, physical activity, sleep, and mental wellness are deeply interdependent systems. A disruption in one area reliably cascades into others, making a holistic approach to {topic} essential. Despite this knowledge, translating evidence into practice remains a significant challenge, hampered by cultural norms, economic pressures, and the pervasive influence of industries that profit from unhealthy behaviors.",
    ],
    "education": [
        "Education is the most powerful instrument available to society for transforming lives and driving progress. The study of {topic} reveals that effective learning goes far beyond memorizing facts — it requires critical thinking, creativity, and the ability to apply knowledge in real-world contexts. Modern educational systems are being challenged to evolve, incorporating technology and student-centered methods to meet the diverse needs of learners. Investment in {topic} yields extraordinary returns, not just economically but in terms of social cohesion and democratic participation.",
        "{topic} forms the bedrock upon which informed, capable citizens are built. From early childhood development to lifelong learning, education shapes how individuals perceive themselves and their place in the world. Innovative approaches to {topic} are dismantling traditional barriers and making quality learning accessible to more people than ever before. As automation transforms the job market, the ability to think critically and adapt quickly — skills cultivated through strong education — becomes increasingly invaluable.",
        "The landscape of {topic} is undergoing its most profound transformation in centuries. Digital platforms, personalized learning algorithms, and open-access resources are democratizing knowledge in ways unimaginable a generation ago. Yet technology alone cannot replace the irreplaceable role of skilled educators, mentorship, and human connection in the learning process. The most effective approaches to {topic} blend the best of both worlds: leveraging data and digital tools while preserving the relational and motivational dimensions of genuine teaching.",
        "What we teach and how we teach it reflects the values a society holds most dear. {topic} is therefore never merely a technical exercise — it is a profoundly moral undertaking. Debates about curriculum, assessment, and access are ultimately debates about what kind of future we want to build. Societies that invest in {topic} as a public good, rather than a private commodity, tend to demonstrate stronger economic resilience, lower inequality, and greater civic participation.",
    ],
    "environment": [
        "The natural environment sustains all life on Earth, yet human activity has placed it under extraordinary strain. Understanding {topic} is no longer an academic pursuit — it is an urgent necessity. Climate change, biodiversity loss, and pollution are interconnected crises that demand coordinated global action. Sustainable practices in energy, agriculture, manufacturing, and consumption offer viable pathways forward. By prioritizing {topic} in policy, business, and everyday choices, humanity can preserve the ecological systems that future generations depend upon.",
        "{topic} sits at the heart of humanity's most pressing challenge: maintaining a livable planet in the face of rapid industrialization. Scientific consensus is clear — without significant changes to how we produce and consume, the consequences will be severe and irreversible. However, there is reason for optimism. Renewable energy, circular economies, and nature-based solutions demonstrate that prosperity and environmental responsibility are not mutually exclusive. Commitment to {topic} at every level is the defining challenge of our era.",
        "Across every ecosystem on Earth, the fingerprints of human influence are unmistakable. {topic} represents the cumulative impact of centuries of industrial development and resource exploitation — a legacy that now demands urgent reckoning. The good news is that nature's capacity for recovery, when given the chance, is remarkable. Conservation science, ecological restoration, and sustainable land management have demonstrated that meaningful reversal is possible. But the window for action is narrowing, making leadership on {topic} one of the most morally urgent responsibilities of this generation.",
        "The economics of ignoring {topic} are becoming impossible to overlook. Extreme weather events, crop failures, rising sea levels, and public health crises linked to environmental degradation now cost trillions annually. Yet the cost of prevention remains a fraction of the cost of inaction — a fact that is gradually reshaping corporate and government decision-making worldwide. Engaging seriously with {topic} is not just the right thing to do — it is increasingly the smart thing to do.",
    ],
    "business": [
        "The world of business is in constant flux, shaped by technological disruption, shifting consumer preferences, and evolving global dynamics. Success in {topic} demands both strategic vision and operational excellence. Companies that thrive are those that innovate relentlessly, cultivate strong organizational cultures, and respond nimbly to change. At its core, {topic} is about creating value — for customers, employees, shareholders, and society at large. In an increasingly competitive landscape, sustainable business practices are not just ethically desirable but strategically essential.",
        "{topic} drives economic growth and provides livelihoods for billions of people worldwide. The principles underlying successful business — understanding markets, managing resources, building relationships, and delivering value — are timeless, even as the tools and contexts change. Today's business leaders must navigate digital transformation, geopolitical uncertainty, and heightened expectations around social responsibility. Those who master {topic} with integrity and adaptability will be best positioned to build organizations that endure.",
        "The most enduring lesson that {topic} teaches is that value creation and value capture are distinct but interdependent activities. Organizations that focus exclusively on extracting short-term profit erode the foundations of their own success. By contrast, companies that genuinely invest in {topic} as a source of innovation, resilience, and purpose tend to outperform across economic cycles. Ethical, people-centered approaches to {topic} are not merely admirable — they are demonstrably more effective.",
        "In an era defined by radical transparency, globalization, and accelerating disruption, the rules of {topic} are being rewritten in real time. Startups challenge incumbents overnight; algorithms optimize supply chains in milliseconds; consumer expectations shift seasonally. Navigating this environment requires leaders who combine analytical rigor with genuine empathy and cultural intelligence. Understanding {topic} today means understanding not just financial models and market dynamics, but the human systems that underpin every transaction.",
    ],
    "science": [
        "Science is humanity's most reliable method for understanding the universe, advancing through observation, experimentation, and rigorous peer review. The field of {topic} has yielded discoveries that have saved countless lives, expanded human knowledge, and inspired new technologies. The scientific process, though slow and often frustrating, is self-correcting — an extraordinary feature that distinguishes it from dogma. Investment in fundamental research into {topic} pays dividends that are difficult to predict but invariably significant over time.",
        "From ancient astronomers mapping the stars to modern physicists probing subatomic particles, the pursuit of {topic} reflects humanity's deepest curiosity about existence. Science thrives on questioning assumptions and challenging established ideas, a quality that has driven every major paradigm shift in history. Today, collaboration across disciplines and borders accelerates discovery in {topic} faster than any single institution could achieve alone. Communicating these discoveries clearly and accessibly to the public remains a critical challenge and responsibility.",
        "The history of {topic} is a chronicle of humanity's refusal to accept ignorance as inevitable. Each generation of scientists inherits a body of knowledge shaped by those who came before and bears the obligation to push its boundaries further. The rewards of this enterprise — longer lives, deeper understanding, new technologies — accrue not just to researchers but to all of humanity. Supporting the infrastructure of scientific inquiry is therefore an investment in the collective future.",
        "What makes {topic} uniquely powerful is its insistence on evidence over authority. Unlike systems of belief that derive legitimacy from tradition or revelation, science earns its credibility by making predictions that can be tested and falsified. This intellectual humility — the willingness to be proven wrong — is not a weakness but a strength. It is precisely what allows {topic} to self-correct and accumulate reliable knowledge over time.",
    ],
    "psychology": [
        "The study of {topic} reveals that the human mind is at once the most familiar and the most mysterious object in the known universe. We spend our entire lives within our own consciousness, yet its depths remain largely uncharted. Modern psychology has made extraordinary strides in understanding perception, emotion, memory, motivation, and behavior — while also demonstrating how consistently humans misunderstand themselves. The insights generated by {topic} have transformed fields as diverse as medicine, economics, education, and law.",
        "{topic} has fundamentally reshaped how we think about human behavior and well-being. Where previous generations attributed mental suffering to moral failure, contemporary psychology understands it as the product of complex biological, psychological, and social interactions. This shift carries profound implications — for how we design institutions, conduct relationships, raise children, and structure work. Investing in the application of {topic} across society offers one of the most promising paths toward reducing unnecessary suffering.",
        "Understanding {topic} means confronting the uncomfortable reality that we are not the rational actors we imagine ourselves to be. Decades of research have revealed systematic patterns in how humans reason, feel, and decide — patterns that deviate consistently from classical models of rationality. Cognitive biases, emotional contagion, social conformity, and unconscious motivation shape behavior far more than deliberate choice. Accepting this humbling truth is the first step toward designing environments and habits that work with human nature rather than against it.",
        "The most profound contribution of {topic} to modern life may be the simple recognition that inner experience matters. Emotions, relationships, meaning, and identity are not peripheral concerns — they are central to human flourishing. Research in {topic} consistently demonstrates that the quality of social connections, sense of purpose, and psychological safety have enormous impacts on well-being. Building a society that takes {topic} seriously means building one that genuinely prioritizes the conditions for human happiness.",
    ],
    "economics": [
        "{topic} provides the analytical framework through which societies allocate scarce resources to meet unlimited human wants. At its core, economics is not merely the study of money but the study of human decision-making under conditions of scarcity and uncertainty. The elegance of {topic} lies in its ability to reveal how individual choices aggregate into complex social outcomes — often in ways that are counterintuitive and surprising. Mastery of {topic} offers invaluable tools not just for policymakers and investors, but for any person seeking to understand the forces that shape daily life.",
        "The great debates within {topic} often reflect deeper disagreements about human nature, social values, and the proper role of government. Should markets be trusted to allocate resources efficiently, or do systemic failures demand intervention? How do we weigh growth against equality, or present consumption against future sustainability? These are not merely technical questions — they are fundamentally ethical ones. Understanding {topic} at its deepest level requires engaging seriously with these tensions.",
        "Few forces shape the material conditions of human life as powerfully as {topic}. The systems of production, exchange, and distribution that constitute economic life determine whether billions of people have access to food, shelter, healthcare, and education. Getting {topic} right — or wrong — has consequences that ripple across generations. The twentieth century offered vivid demonstrations of both success and catastrophic failure, providing lessons that continue to inform contemporary debates.",
        "The discipline of {topic} has undergone remarkable evolution, incorporating insights from psychology, sociology, ecology, and data science. Behavioral economics, complexity theory, and institutional analysis have enriched the field's understanding of how real markets and real people operate, often very differently from textbook models. This intellectual dynamism makes {topic} one of the most relevant and rapidly evolving social sciences.",
    ],
    "culture": [
        "Culture is the invisible architecture of human life — the shared system of beliefs, values, symbols, and practices through which communities make meaning and organize collective existence. The study of {topic} reveals that no human behavior can be fully understood in isolation from its cultural context. What appears universal often proves to be profoundly particular; what seems natural is frequently revealed to be constructed. Engaging with {topic} across its extraordinary diversity is a fundamental act of human empathy and self-understanding.",
        "{topic} is both inherited and continuously reinvented. Each generation receives a cultural legacy from its predecessors and simultaneously transforms it in response to new circumstances, technologies, and encounters with difference. This dynamic quality makes {topic} resilient and adaptive — capable of absorbing profound shocks while maintaining continuity of identity. Understanding how {topic} changes over time is essential to understanding the trajectories of societies.",
        "The relationship between {topic} and power is inescapable. Dominant groups within societies typically have greater ability to define cultural norms, shape narratives, and determine whose experiences are represented and whose are marginalized. Recognizing this dimension of {topic} does not diminish its capacity for beauty, meaning, and connection — but it does demand a critical awareness of the ways in which cultural production can both reflect and reinforce social hierarchies.",
        "In an era of unprecedented global connectivity, {topic} is both under threat and more dynamic than ever. The homogenizing forces of digital media and global commerce create real risks of cultural impoverishment — the loss of languages, traditions, and ways of knowing that have evolved over millennia. Yet the same connectivity enables new forms of cultural exchange, hybrid identities, and cross-cultural dialogue that would have been unimaginable a generation ago.",
    ],
    "leadership": [
        "Effective leadership is among the most studied and least understood phenomena in organizational life. The study of {topic} reveals that the qualities which make leaders successful are not fixed traits but dynamic capabilities — contextual, relational, and continuously developed. History offers examples of leaders who transformed institutions through vision, courage, and the ability to inspire collective action. It also offers cautionary tales of charisma divorced from competence, or authority exercised without accountability.",
        "{topic} is ultimately about the relationship between influence and responsibility. Those who lead shape the conditions in which others live and work — a power that carries profound obligations. The most respected leaders across history and culture share a common characteristic: they led in service of something larger than themselves. Whether in business, politics, education, or community life, {topic} that prioritizes purpose over position produces more durable outcomes and more meaningful legacies.",
        "The demands placed on leaders in the contemporary world are unlike anything previous generations faced. Complexity, ambiguity, speed, and global interdependence create an environment in which no individual can possess all the knowledge needed to act with complete confidence. This reality has elevated the importance of a particular kind of {topic}: one characterized by intellectual humility, collaborative decision-making, and the ability to build diverse teams whose collective intelligence far exceeds that of any individual.",
        "The development of {topic} capacity is not merely a professional concern but a civic one. Healthy institutions require an ongoing supply of capable, ethical leaders at every level. Investing in {topic} development, mentorship, and succession planning is therefore one of the most important long-term investments any organization or society can make. The returns are not always immediate, but they accumulate over time in the form of stronger institutions and better decisions.",
    ],
    "philosophy": [
        "Philosophy begins in wonder and ends in wisdom — or at least in a deeper appreciation of how much remains unknown. The history of {topic} is a record of humanity's most rigorous attempts to answer the questions that matter most: What exists? What can we know? What should we do? What is a good life? These questions resist easy answers, which is precisely why they have sustained centuries of brilliant minds and generated insights that continue to shape how we understand ourselves and our world.",
        "{topic} occupies a unique position among the disciplines: it is both the foundation from which the natural and social sciences emerged and the critical lens through which their assumptions and limits can be examined. Every scientific theory rests on philosophical commitments about the nature of evidence, causation, and explanation. Every ethical system reflects a philosophical position on the nature of value and obligation. Ignoring {topic} does not make these commitments disappear — it merely makes them immune to critical scrutiny.",
        "The practical relevance of {topic} has never been greater. As artificial intelligence challenges our understanding of mind and consciousness, as biotechnology raises unprecedented questions about identity and enhancement, the tools of philosophical analysis are urgently needed. {topic} offers not answers but methods: ways of clarifying concepts, identifying assumptions, mapping logical relationships, and testing arguments that make it possible to think about difficult problems with greater precision and honesty.",
        "One of the most valuable contributions of {topic} is its insistence that the way we frame questions determines the range of answers available to us. Many seemingly intractable debates — about justice, freedom, identity, meaning — persist not because the underlying facts are unclear but because the concepts involved are confused or contested. Philosophical analysis, by clarifying what is actually being claimed, often reveals that apparent disagreements are really conceptual misunderstandings — or that genuine disagreements run far deeper than initially supposed.",
    ],
    "sports": [
        "Sports occupy a unique place in human culture, functioning simultaneously as competition, entertainment, community, and metaphor. The study of {topic} reveals that athletic pursuits are never purely physical — they are profoundly psychological, social, and even philosophical in nature. The values of discipline, teamwork, resilience, and fair play that {topic} instills reach far beyond the playing field, shaping character and cultivating virtues that translate into every domain of life.",
        "At its best, {topic} transcends the boundaries of language, ethnicity, and ideology, creating moments of shared humanity that few other experiences can match. The roar of a crowd witnessing an extraordinary athletic performance, the agony and ecstasy of competition decided in its final seconds — these are experiences that connect people at a primal level. But {topic} also reflects the societies that produce it, and its structures of power and exclusion warrant ongoing critical attention.",
        "The science of athletic performance has transformed our understanding of human physical potential. Research into {topic} has revealed that the limits of what the human body can achieve are far higher than previously imagined — and that the mental dimensions of performance are at least as important as the physical ones. Elite athletes at the highest levels of {topic} increasingly work with psychologists, nutritionists, and data analysts, recognizing that marginal gains across multiple dimensions compound into decisive competitive advantages.",
        "The economics and politics of {topic} have grown enormously complex in the modern era. What were once local contests of skill and courage have become global entertainment industries with revenues in the tens of billions. This commercialization has brought resources and professional opportunities to athletes across the world, while simultaneously raising difficult questions about exploitation, integrity, and the commodification of play. Engaging honestly with these tensions is essential to ensuring that {topic} continues to serve its deepest human purposes.",
    ],
    "art": [
        "Art is humanity's oldest and most persistent form of self-expression, predating written language by tens of thousands of years. The study of {topic} reveals that artistic creation is not a luxury appended to civilized life but a foundational dimension of it — a means by which individuals and communities process experience, construct identity, communicate across difference, and imagine alternative realities. In this sense, {topic} is not merely cultural decoration but a core mechanism of human consciousness and social cohesion.",
        "{topic} occupies a paradoxical position: it is at once deeply personal and profoundly communal, simultaneously timeless and embedded in its historical moment. A painting created centuries ago can still move a contemporary viewer to tears; a piece of music composed for a specific occasion can transcend it to become a universal statement. This temporal and cultural mobility is one of the most remarkable qualities of {topic}, suggesting that beneath the surface diversity of styles and forms lies a common human capacity for aesthetic experience.",
        "The relationship between {topic} and society is one of mutual constitution. Art reflects the values, anxieties, and aspirations of the culture that produces it — and in turn shapes how people within that culture perceive themselves and their world. Great works of {topic} do not merely describe reality; they create new possibilities of feeling and thinking, expanding the imaginative horizon of their audiences. This generative capacity makes {topic} not just a record of human experience but one of its most powerful drivers of change.",
        "The question of what makes something good {topic} has exercised critics, philosophers, and artists themselves for millennia without yielding consensus. This very irresolvability is part of what makes {topic} so enduring — it perpetually resists reduction to formula or rule. Yet this does not mean that judgments about {topic} are arbitrary. Engagement with great works across time reveals patterns of quality — originality, technical mastery, emotional depth, conceptual coherence — that, while not algorithmic, are recognizable and communicable.",
    ],
    "default": [
        "{topic} is a subject of considerable importance and broad relevance in today's world. Those who engage deeply with {topic} discover layers of complexity that reward careful study and open-minded inquiry. The implications of understanding {topic} extend across personal, professional, and societal dimensions, making it a worthy focus of attention and discussion. As perspectives evolve and new information emerges, the conversation around {topic} continues to grow richer and more nuanced.",
        "A thorough examination of {topic} reveals both challenges and opportunities that merit thoughtful consideration. Experts across various fields have contributed valuable insights into {topic}, building a body of knowledge that continues to expand. Engaging with this subject fosters greater awareness and equips individuals with the understanding needed to make informed decisions. Ultimately, the significance of {topic} lies in its capacity to inform, inspire, and guide meaningful action.",
        "The more one explores {topic}, the more apparent it becomes that surface-level understanding is rarely sufficient. Beneath the obvious dimensions of the subject lie deeper questions of causation, meaning, and consequence that demand sustained attention. Practitioners and scholars who devote themselves to {topic} often find that the most important insights emerge not from initial investigation but from the willingness to revise assumptions and pursue understanding beyond the point of initial comfort.",
        "Few subjects reward interdisciplinary attention as richly as {topic}. The most penetrating analyses tend to draw on insights from multiple fields — combining empirical evidence with theoretical reflection, quantitative analysis with qualitative depth, historical perspective with contemporary relevance. This integrative approach does not dilute rigor but enhances it, revealing connections and contradictions that narrowly disciplinary inquiry might miss.",
    ],
}

def detect_topic_category(topic):
    topic_lower = topic.lower()
    keywords = {
        "technology":  ["tech", "ai", "software", "computer", "digital", "internet", "robot", "machine",
                        "data", "cyber", "code", "app", "algorithm", "automation", "blockchain", "cloud",
                        "programming", "hardware", "network", "cybersecurity", "virtual", "semiconductor",
                        "smartphone", "gadget", "laptop", "database", "api", "iot", "drone", "3d printing"],
        "health":      ["health", "wellness", "medical", "fitness", "diet", "exercise", "mental", "nutrition",
                        "medicine", "disease", "therapy", "doctor", "hospital", "pandemic", "vaccine",
                        "surgery", "chronic", "diabetes", "cancer", "immune", "brain", "stress", "sleep",
                        "yoga", "meditation", "obesity", "nutrition", "supplement", "pharmacy", "patient"],
        "education":   ["education", "learning", "school", "university", "teaching", "study", "knowledge",
                        "training", "academic", "curriculum", "student", "classroom", "literacy", "skill",
                        "college", "degree", "course", "pedagogy", "exam", "diploma", "scholarship",
                        "tuition", "textbook", "lecture", "homework", "graduation", "campus"],
        "environment": ["environment", "climate", "nature", "ecology", "pollution", "sustainable", "green",
                        "carbon", "ocean", "biodiversity", "fossil", "renewable", "recycling", "deforestation",
                        "global warming", "conservation", "emissions", "habitat", "species", "plastic",
                        "solar", "wind energy", "wildfire", "drought", "flood", "ozone", "glacier"],
        "business":    ["business", "market", "economy", "finance", "invest", "startup", "company",
                        "corporate", "entrepreneur", "trade", "profit", "revenue", "brand", "marketing",
                        "sales", "management", "strategy", "supply chain", "retail", "stock", "merger",
                        "acquisition", "shareholder", "dividend", "balance sheet", "franchise", "ecommerce"],
        "science":     ["science", "research", "experiment", "physics", "chemistry", "biology", "space",
                        "quantum", "lab", "discovery", "molecule", "atom", "evolution", "genetics",
                        "astronomy", "geology", "neuroscience", "mathematics", "theorem", "hypothesis",
                        "telescope", "particle", "dna", "fossil", "periodic", "relativity", "gravity"],
        "psychology":  ["psychology", "mental health", "behavior", "cognitive", "emotion", "personality",
                        "therapy", "trauma", "anxiety", "depression", "motivation", "consciousness",
                        "mindset", "habit", "memory", "perception", "bias", "social psychology",
                        "attachment", "self-esteem", "resilience", "phobia", "mindfulness", "grief"],
        "economics":   ["economics", "economy", "gdp", "inflation", "unemployment", "monetary", "fiscal",
                        "capitalism", "socialism", "trade", "currency", "recession", "growth", "inequality",
                        "poverty", "taxation", "labor", "supply", "demand", "market forces", "interest rate",
                        "central bank", "budget deficit", "wealth gap", "minimum wage", "subsidy"],
        "culture":     ["culture", "tradition", "society", "custom", "heritage", "identity", "diversity",
                        "language", "religion", "ethnicity", "ritual", "mythology", "folklore", "art",
                        "music", "film", "literature", "food culture", "festival", "norms", "subculture",
                        "globalization", "indigenous", "diaspora", "multiculturalism", "pop culture"],
        "leadership":  ["leadership", "leader", "management", "executive", "ceo", "director", "vision",
                        "strategy", "inspire", "motivate", "delegate", "accountability", "mentorship",
                        "organizational", "governance", "decision-making", "authority", "influence",
                        "team building", "culture change", "transformation", "servant leader"],
        "philosophy":  ["philosophy", "ethics", "moral", "logic", "metaphysics", "epistemology", "truth",
                        "justice", "virtue", "existence", "meaning", "consciousness", "free will",
                        "aesthetics", "ontology", "rationalism", "empiricism", "existentialism",
                        "stoicism", "utilitarianism", "kant", "socrates", "plato", "aristotle"],
        "sports":      ["sport", "football", "basketball", "cricket", "tennis", "athlete", "team",
                        "competition", "tournament", "championship", "training", "fitness", "coach",
                        "player", "stadium", "olympics", "marathon", "swimming", "cycling", "rugby",
                        "baseball", "hockey", "golf", "soccer", "volleyball", "boxing", "wrestling"],
        "art":         ["art", "painting", "sculpture", "music", "poetry", "creative", "design",
                        "architecture", "photography", "cinema", "theatre", "dance", "illustration",
                        "gallery", "museum", "exhibition", "aesthetic", "craft", "visual", "drawing",
                        "composition", "canvas", "abstract", "classical", "contemporary", "artist"],
    }
    for category, words in keywords.items():
        if any(w in topic_lower for w in words):
            return category
    return "default"

def generate_paragraph(topic):
    category = detect_topic_category(topic)
    templates = TOPIC_TEMPLATES.get(category, TOPIC_TEMPLATES["default"])
    template = random.choice(templates)
    return template.replace("{topic}", topic)

# ═══════════════════════════════════════════════════════════════
# 3. TONE ADJUSTMENT  —  5 tones with rich word maps & openers
# ═══════════════════════════════════════════════════════════════

TONE_WORD_MAP = {
    "formal": {
        "but": "however", "also": "furthermore", "so": "therefore",
        "big": "substantial", "small": "minimal", "get": "obtain",
        "show": "demonstrate", "use": "utilize", "need": "require",
        "want": "desire", "tell": "inform", "ask": "inquire",
        "help": "assist", "make": "produce", "find": "identify",
        "think": "consider", "look at": "examine", "talk about": "discuss",
        "go up": "increase", "go down": "decrease", "set up": "establish",
        "find out": "determine", "come up with": "devise", "deal with": "address",
        "look into": "investigate", "carry out": "execute", "put off": "postpone",
        "bring up": "raise", "point out": "indicate", "take part": "participate",
        "i think": "it is believed that", "i feel": "it is considered that",
        "i believe": "it is posited that", "we think": "it is our position that",
        "you": "one", "your": "one's", "we": "the organization",
        "can't": "cannot", "won't": "will not", "don't": "do not",
        "isn't": "is not", "aren't": "are not", "it's": "it is",
        "let's": "let us", "we're": "we are", "they're": "they are",
        "he's": "he is", "she's": "she is", "that's": "that is",
        "there's": "there is", "here's": "here is", "what's": "what is",
        "ok": "acceptable", "okay": "acceptable", "yeah": "yes",
        "yep": "yes", "nope": "no", "alright": "very well",
        "a lot": "considerably", "lots of": "numerous", "tons of": "a substantial number of",
        "kind of": "somewhat", "sort of": "to some extent", "pretty": "rather",
        "really": "genuinely", "stuff": "material", "things": "matters",
        "guy": "individual", "guys": "individuals", "kids": "children",
        "fix": "rectify", "check": "verify", "pick": "select",
        "start": "commence", "end": "conclude", "try": "endeavor",
        "give": "provide", "get rid of": "eliminate", "look for": "seek",
        "about": "regarding", "around": "approximately", "more than": "in excess of",
        "less than": "below", "because": "due to the fact that",
        "before": "prior to", "after": "subsequent to", "during": "throughout",
        "now": "at present", "soon": "in the near future", "later": "subsequently",
        "also": "in addition", "next": "the following", "last": "the preceding",
        "big deal": "matter of significance", "no problem": "certainly acceptable",
        "lots": "a considerable number", "way too": "excessively",
    },
    "casual": {
        "however": "but", "furthermore": "also", "therefore": "so",
        "substantial": "big", "minimal": "small", "obtain": "get",
        "demonstrate": "show", "utilize": "use", "require": "need",
        "desire": "want", "inform": "tell", "inquire": "ask",
        "assist": "help", "produce": "make", "identify": "find",
        "consider": "think", "examine": "look at", "discuss": "talk about",
        "increase": "go up", "decrease": "go down", "establish": "set up",
        "determine": "find out", "devise": "come up with", "address": "deal with",
        "investigate": "look into", "execute": "carry out", "postpone": "put off",
        "raise": "bring up", "indicate": "point out", "participate": "take part",
        "it is believed that": "i think", "it is considered that": "i feel",
        "one": "you", "one's": "your", "the organization": "we",
        "cannot": "can't", "will not": "won't", "do not": "don't",
        "is not": "isn't", "are not": "aren't", "it is": "it's",
        "let us": "let's", "we are": "we're", "they are": "they're",
        "he is": "he's", "she is": "she's", "that is": "that's",
        "there is": "there's", "acceptable": "okay",
        "yes": "yeah", "no": "nope", "very well": "alright",
        "considerably": "a lot", "numerous": "lots of",
        "somewhat": "kind of", "to some extent": "sort of",
        "rather": "pretty", "genuinely": "really",
        "material": "stuff", "matters": "things",
        "individual": "person", "children": "kids",
        "rectify": "fix", "verify": "check", "select": "pick",
        "commence": "start", "conclude": "end", "endeavor": "try",
        "provide": "give", "eliminate": "get rid of", "seek": "look for",
        "regarding": "about", "approximately": "around",
        "prior to": "before", "subsequent to": "after",
        "due to the fact that": "because", "at present": "now",
        "in the near future": "soon", "subsequently": "later",
        "commence": "kick off", "terminate": "wrap up",
        "in addition": "plus", "furthermore": "on top of that",
    },
    "professional": {
        "but": "however", "also": "additionally", "so": "consequently",
        "i think": "our analysis suggests", "i believe": "the evidence indicates",
        "i feel": "our assessment indicates", "we think": "our team recommends",
        "you": "stakeholders", "your": "your organization's",
        "good": "effective", "bad": "suboptimal", "big": "significant",
        "small": "limited", "need": "require", "help": "support",
        "use": "leverage", "show": "demonstrate", "make": "develop",
        "get": "achieve", "start": "initiate", "end": "finalize",
        "check": "review", "fix": "address", "find": "identify",
        "try": "aim to", "give": "provide", "ask": "request",
        "look at": "evaluate", "talk about": "discuss", "come up with": "develop",
        "deal with": "manage", "find out": "determine", "set up": "establish",
        "can't": "cannot", "won't": "will not", "don't": "do not",
        "isn't": "is not", "aren't": "are not", "it's": "it is",
        "let's": "let us", "ok": "satisfactory", "okay": "satisfactory",
        "a lot": "substantially", "lots of": "a significant number of",
        "really": "significantly", "very": "highly",
        "problem": "challenge", "issues": "concerns",
        "people": "team members", "workers": "personnel",
        "plan": "strategic initiative", "goal": "objective",
        "meeting": "session", "talk": "discussion",
        "money": "budget", "cost": "expenditure", "buy": "procure",
        "about": "pertaining to", "because": "as a result of",
        "change": "transformation", "update": "enhancement",
        "now": "at this juncture", "soon": "in the near term",
        "think about": "consider", "work on": "develop",
        "put together": "compile", "go over": "review",
        "look into": "investigate", "follow up": "conduct a follow-up",
    },
    "academic": {
        "but": "however", "also": "moreover", "so": "thus",
        "show": "demonstrate", "think": "argue", "say": "contend",
        "i think": "this paper argues", "i believe": "the evidence suggests",
        "we found": "the findings indicate", "we see": "it is observed that",
        "a lot": "a substantial body of", "many": "numerous",
        "use": "employ", "make": "construct", "look at": "examine",
        "help": "facilitate", "find": "identify", "check": "analyze",
        "start": "initiate", "end": "conclude", "talk about": "address",
        "can't": "cannot", "won't": "will not", "don't": "do not",
        "isn't": "is not", "it's": "it is", "let's": "let us",
        "important": "significant", "very important": "of paramount importance",
        "big": "substantial", "small": "limited", "problem": "challenge",
        "answer": "solution", "question": "inquiry", "reason": "rationale",
        "example": "illustration", "result": "outcome", "plan": "framework",
        "research": "investigation", "study": "analysis", "data": "evidence",
        "you": "one", "your": "one's", "we": "researchers",
        "about": "pertaining to", "because": "given that",
        "before": "prior to", "after": "subsequent to",
        "really": "substantively", "very": "considerably",
        "shows that": "demonstrates that", "proves that": "substantiates that",
        "seems like": "appears to", "looks like": "suggests that",
        "according to": "as posited by", "based on": "drawing upon",
        "this means": "this implies", "that is why": "consequently",
    },
    "empathetic": {
        "you must": "you might want to consider",
        "you should": "it could help to",
        "you need to": "it may be beneficial to",
        "you have to": "one option is to",
        "do this": "consider trying this",
        "fix it": "work through this",
        "the problem is": "one challenge you might be facing is",
        "you failed": "this hasn't worked out yet",
        "that's wrong": "there might be another way to look at this",
        "but": "and yet", "however": "at the same time",
        "i think": "from what i understand",
        "you need": "it sounds like you might need",
        "obviously": "as you may already know",
        "clearly": "it seems", "can't": "may find it difficult to",
        "won't": "might not be ready to", "don't": "may not want to",
        "failed": "encountered a setback", "mistake": "learning opportunity",
        "problem": "challenge", "difficult": "demanding", "hard": "challenging",
        "terrible": "really tough", "awful": "genuinely difficult",
        "wrong": "not quite right yet", "bad": "not ideal",
        "impossible": "very challenging right now",
        "just": "simply", "really": "genuinely", "very": "deeply",
        "stop": "take a break from", "quit": "step back from",
        "fail": "not succeed yet", "weak": "still developing",
        "criticism": "feedback", "complaint": "concern",
        "angry": "frustrated", "upset": "feeling challenged",
        "stupid": "still learning", "wrong answer": "different approach needed",
    },
}

TONE_STARTERS = {
    "formal": [
        "It is imperative to note that", "Upon careful consideration,",
        "In accordance with established principles,", "It should be observed that",
        "As evidenced by the foregoing,", "It is hereby established that",
        "For the purposes of this communication,", "It is pertinent to acknowledge that",
        "Following thorough deliberation,", "In light of the aforementioned,",
    ],
    "casual": [
        "So basically,", "Here's the thing —", "Just so you know,", "Honestly,",
        "To be real with you,", "Quick heads up —", "Between you and me,",
        "The way I see it,", "Not gonna lie,", "Let me break it down —",
        "Real talk,", "Here's what's up —",
    ],
    "professional": [
        "From a strategic standpoint,", "Based on current analysis,",
        "To maximize outcomes,", "In alignment with best practices,",
        "Our assessment indicates that", "From an operational perspective,",
        "To ensure optimal results,", "In line with organizational objectives,",
        "Following a thorough review,", "To drive meaningful progress,",
    ],
    "academic": [
        "Empirical evidence suggests that", "Scholarly consensus indicates that",
        "A critical examination reveals that", "As the literature demonstrates,",
        "From a theoretical perspective,", "This analysis posits that",
        "Prior research has established that", "A review of the evidence indicates that",
        "Drawing on existing scholarship,", "As noted by leading researchers,",
    ],
    "empathetic": [
        "I understand this may feel overwhelming, but",
        "It's completely natural to feel that way —",
        "Many people share this experience, and",
        "What you're going through is valid, and",
        "Taking things one step at a time,",
        "It's okay to feel uncertain —",
        "Your feelings make a lot of sense, and",
        "With patience and support,",
        "You're not alone in this —",
        "It takes real courage to face this, and",
    ],
}

def adjust_tone(text, tone):
    tone = tone.lower()
    if tone not in TONE_WORD_MAP:
        return text
    word_map = TONE_WORD_MAP[tone]
    result = text
    for phrase in sorted(word_map.keys(), key=len, reverse=True):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        def replace_match(m, repl=word_map[phrase]):
            if m.group(0)[0].isupper():
                return repl.capitalize()
            return repl
        result = pattern.sub(replace_match, result)
    sentences = sentence_split(result)
    if sentences and random.random() > 0.4:
        opener = random.choice(TONE_STARTERS[tone])
        first = sentences[0]
        sentences[0] = f"{opener} {first[0].lower()}{first[1:]}"
        result = ' '.join(sentences)
    return result

# ═══════════════════════════════════════════════════════════════
# 4. PLAGIARISM CHECK  —  150+ corpus entries across categories
# ═══════════════════════════════════════════════════════════════

KNOWN_CORPUS = [
    # Classic literature
    "To be or not to be, that is the question.",
    "It was the best of times, it was the worst of times.",
    "Call me Ishmael.",
    "It is a truth universally acknowledged that a single man in possession of a good fortune must be in want of a wife.",
    "All happy families are alike; each unhappy family is unhappy in its own way.",
    "It was a bright cold day in April and the clocks were striking thirteen.",
    "Not all those who wander are lost.",
    "It does not do to dwell on dreams and forget to live.",
    "There is no greater agony than bearing an untold story inside you.",
    "The world is a book and those who do not travel read only one page.",
    "We accept the love we think we deserve.",
    "All animals are equal but some animals are more equal than others.",
    "It is our choices that show what we truly are far more than our abilities.",
    "In the beginning God created the heavens and the earth.",
    "Elementary, my dear Watson.",
    "The only way out of the labyrinth of suffering is to forgive.",
    "So it goes.",
    "Stay gold Ponyboy stay gold.",
    "It is not our abilities that show what we truly are it is our choices.",
    "After all tomorrow is another day.",
    "I am no bird and no net ensnares me.",
    "The course of true love never did run smooth.",
    "We are all mad here.",
    "It matters not what someone is born but what they grow to be.",
    "Do I dare disturb the universe.",

    # Famous speeches & historical
    "All men are created equal.",
    "We hold these truths to be self-evident.",
    "Four score and seven years ago our fathers brought forth on this continent a new nation.",
    "Ask not what your country can do for you ask what you can do for your country.",
    "I have a dream that one day this nation will rise up and live out the true meaning of its creed.",
    "The only thing we have to fear is fear itself.",
    "That is one small step for man one giant leap for mankind.",
    "To be prepared for war is one of the most effective means of preserving peace.",
    "Give me liberty or give me death.",
    "Never in the field of human conflict was so much owed by so many to so few.",
    "We shall fight on the beaches we shall fight on the landing grounds.",
    "The arc of the moral universe is long but it bends toward justice.",
    "Power tends to corrupt and absolute power corrupts absolutely.",
    "An eye for an eye leaves the whole world blind.",
    "Be the change you wish to see in the world.",
    "Education is the most powerful weapon which you can use to change the world.",
    "It always seems impossible until it is done.",
    "The measure of a man is what he does with power.",
    "I have not failed I have just found ten thousand ways that will not work.",
    "America was not built on fear America was built on courage imagination and unbeatable determination.",
    "Freedom is never voluntarily given by the oppressor it must be demanded by the oppressed.",
    "The time is always right to do what is right.",
    "Injustice anywhere is a threat to justice everywhere.",

    # Philosophy & wisdom
    "Knowledge is power.",
    "Time is money.",
    "I think therefore I am.",
    "The unexamined life is not worth living.",
    "One cannot step into the same river twice.",
    "The only true wisdom is in knowing you know nothing.",
    "Man is by nature a social animal.",
    "Happiness depends upon ourselves.",
    "We are what we repeatedly do excellence then is not an act but a habit.",
    "The secret of happiness is not in doing what one likes but in liking what one does.",
    "The journey of a thousand miles begins with a single step.",
    "Life is what happens when you are busy making other plans.",
    "No man is an island entire of itself.",
    "This above all to thine own self be true.",
    "What we think we become.",
    "Whether you think you can or think you cannot you are right.",
    "The greatest glory in living lies not in never falling but in rising every time we fall.",
    "In three words I can sum up everything I have learned about life it goes on.",
    "To live is the rarest thing in the world most people just exist.",
    "It is not the strongest of the species that survives but the most adaptable.",
    "You only live once but if you do it right once is enough.",
    "Do not go where the path may lead go instead where there is no path and leave a trail.",
    "In the end it is not the years in your life that count it is the life in your years.",
    "The purpose of our lives is to be happy.",
    "Get busy living or get busy dying.",
    "It is never too late to be what you might have been.",
    "Everything you can imagine is real.",
    "Life is either a daring adventure or nothing at all.",

    # Common proverbs & sayings
    "Actions speak louder than words.",
    "The pen is mightier than the sword.",
    "All that glitters is not gold.",
    "Where there is a will there is a way.",
    "Practice makes perfect.",
    "Look before you leap.",
    "A stitch in time saves nine.",
    "Do not count your chickens before they hatch.",
    "Every cloud has a silver lining.",
    "The early bird catches the worm.",
    "You cannot judge a book by its cover.",
    "Better late than never.",
    "Two wrongs do not make a right.",
    "When in Rome do as the Romans do.",
    "The grass is always greener on the other side.",
    "A penny saved is a penny earned.",
    "Necessity is the mother of invention.",
    "Fortune favors the brave.",
    "Honesty is the best policy.",
    "Laughter is the best medicine.",
    "Time heals all wounds.",
    "Blood is thicker than water.",
    "Birds of a feather flock together.",
    "Do unto others as you would have them do unto you.",
    "A chain is only as strong as its weakest link.",
    "The squeaky wheel gets the grease.",
    "Too many cooks spoil the broth.",
    "Strike while the iron is hot.",
    "Every dog has his day.",
    "Rome was not built in a day.",
    "All good things must come to an end.",
    "The road to hell is paved with good intentions.",
    "A rolling stone gathers no moss.",

    # Science & technology
    "The internet is the world's largest library.",
    "Artificial intelligence is the new electricity.",
    "Data is the new oil.",
    "Content is king.",
    "The future is already here it is just not evenly distributed.",
    "Technology is neither good nor bad nor is it neutral.",
    "The medium is the message.",
    "Any sufficiently advanced technology is indistinguishable from magic.",
    "Science is the great antidote to the poison of enthusiasm and superstition.",
    "The good thing about science is that it is true whether or not you believe in it.",
    "Imagination is more important than knowledge.",
    "Two things are infinite the universe and human stupidity.",
    "If you cannot explain it simply you do not understand it well enough.",
    "Research is to see what everybody else has seen and to think what nobody else has thought.",
    "In science there are no shortcuts to truth.",
    "The most beautiful thing we can experience is the mysterious.",
    "Science is a way of thinking much more than it is a body of knowledge.",
    "The day science begins to study non-physical phenomena it will make more progress in one decade.",
    "To invent you need a good imagination and a pile of junk.",
    "The scientist is not a person who gives the right answers he is one who asks the right questions.",

    # Business & economics
    "Think different.",
    "Just do it.",
    "Innovation distinguishes between a leader and a follower.",
    "The customer is always right.",
    "In the middle of difficulty lies opportunity.",
    "Success is not final failure is not fatal it is the courage to continue that counts.",
    "The secret of getting ahead is getting started.",
    "Do or do not there is no try.",
    "An investment in knowledge pays the best interest.",
    "Price is what you pay value is what you get.",
    "The best investment you can make is an investment in yourself.",
    "The stock market is a device for transferring money from the impatient to the patient.",
    "Risk comes from not knowing what you are doing.",
    "Beware of little expenses a small leak will sink a great ship.",
    "It takes twenty years to build a reputation and five minutes to ruin it.",
    "Your most unhappy customers are your greatest source of learning.",
    "The way to get started is to quit talking and begin doing.",
    "Management is doing things right leadership is doing the right things.",
    "If you really look closely most overnight successes took a long time.",
    "The only way to do great work is to love what you do.",

    # Health & wellness
    "Let food be thy medicine and medicine be thy food.",
    "A healthy outside starts from the inside.",
    "Take care of your body it is the only place you have to live.",
    "Physical fitness is the first requisite of happiness.",
    "Health is not valued until sickness comes.",
    "The greatest wealth is health.",
    "An ounce of prevention is worth a pound of cure.",
    "Sleep is the best meditation.",
    "It is health that is real wealth and not pieces of gold and silver.",
    "The body achieves what the mind believes.",
    "A fit body a calm mind a house full of love these things cannot be bought they must be earned.",
    "To keep the body in good health is a duty otherwise we shall not be able to keep our mind strong and clear.",
    "It is exercise alone that supports the spirits and keeps the mind in vigor.",

    # Education & knowledge
    "Education is not the filling of a pail but the lighting of a fire.",
    "The beautiful thing about learning is that nobody can take it away from you.",
    "Tell me and I forget teach me and I remember involve me and I learn.",
    "Education is the passport to the future for tomorrow belongs to those who prepare for it today.",
    "Live as if you were to die tomorrow learn as if you were to live forever.",
    "The more that you read the more things you will know.",
    "Intelligence plus character that is the goal of true education.",
    "Education is not preparation for life education is life itself.",
    "The mind is not a vessel to be filled but a fire to be kindled.",
    "Learning is a treasure that will follow its owner everywhere.",
    "An educated mind is able to entertain a thought without accepting it.",
    "The goal of education is not to increase the amount of knowledge but to create the possibilities for a child to invent and discover.",

    # Social & cultural
    "No act of kindness no matter how small is ever wasted.",
    "In diversity there is beauty and there is strength.",
    "Alone we can do so little together we can do so much.",
    "The purpose of life is not to be happy but to be useful.",
    "You miss 100 percent of the shots you never take.",
    "Stay hungry stay foolish.",
    "Your time is limited so do not waste it living someone else's life.",
    "It is not about how hard you hit it is about how hard you can get hit and keep moving forward.",
    "We are all different which is great because we are all unique.",
    "The strength of a team is each individual member the strength of each member is the team.",
    "Try to be a rainbow in someone else's cloud.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Believe you can and you are halfway there.",
    "You are never too old to set another goal or to dream a new dream.",
    "When one door of happiness closes another opens but often we look so long at the closed door.",
    "Start where you are use what you have do what you can.",
    "Life is ten percent what happens to you and ninety percent how you react to it.",
    "If you want to lift yourself up lift up someone else.",
    "Spread love everywhere you go let no one ever come to you without leaving happier.",
    "When you reach the end of your rope tie a knot in it and hang on.",
]

def cosine_similarity(vec1, vec2):
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    dot  = sum(vec1[w] * vec2[w] for w in common)
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
    input_vec    = text_to_tfidf_vector(text, KNOWN_CORPUS)
    input_tokens = set(tokenize(text))
    results = []
    for known in KNOWN_CORPUS:
        known_vec     = text_to_tfidf_vector(known, KNOWN_CORPUS)
        sim           = cosine_similarity(input_vec, known_vec)
        known_tokens  = set(tokenize(known))
        overlap       = len(input_tokens & known_tokens)
        overlap_ratio = overlap / max(len(input_tokens), 1)
        combined_score = (sim * 0.6 + overlap_ratio * 0.4)
        if combined_score > 0.08:
            results.append({
                "source":     known[:80] + ("..." if len(known) > 80 else ""),
                "similarity": round(combined_score * 100, 1)
            })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    top_results = results[:3]
    max_sim = max((r["similarity"] for r in top_results), default=0)

    if max_sim >= 70:
        risk, color = "High", "red"
        summary = "This text shows significant similarity to known sources. It may be plagiarized."
    elif max_sim >= 35:
        risk, color = "Moderate", "orange"
        summary = "This text has moderate similarity to some known sources. Review recommended."
    elif max_sim >= 15:
        risk, color = "Low", "yellow"
        summary = "Minimal similarity detected. The text appears mostly original."
    else:
        risk, color = "None", "green"
        summary = "No significant matches found. The text appears to be original."

    tokens = tokenize(text)
    unique_ratio      = len(set(tokens)) / max(len(tokens), 1)
    originality_score = round(min(100, unique_ratio * 100 + (100 - max_sim) * 0.5), 1)

    return {
        "risk": risk, "color": color, "summary": summary,
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
    return jsonify({"result": paraphrase(text)})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({"error": "No topic provided."}), 400
    return jsonify({"result": generate_paragraph(topic)})

@app.route('/api/tone', methods=['POST'])
def api_tone():
    data = request.get_json()
    text = data.get('text', '').strip()
    tone = data.get('tone', 'formal').strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    return jsonify({"result": adjust_tone(text, tone)})

@app.route('/api/plagiarism', methods=['POST'])
def api_plagiarism():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    return jsonify(check_plagiarism(text))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
