import html
import re

from functools import lru_cache

from django.template.defaultfilters import striptags
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer

ENGLISH_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
]

ENGLISH_NUMBERS = [
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
]

ENGLISH_MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

ENGLISH_MISC_WORDS = [
    "across",
    "advice",
    "along",
    "also",
    "always",
    "answer",
    "around",
    "audio",
    "available",
    "back",
    "become",
    "behind",
    "best",
    "better",
    "beyond",
    "big",
    "biggest",
    "bring",
    "brings",
    "change",
    "channel",
    "city",
    "come",
    "content",
    "conversation",
    "course",
    "daily",
    "date",
    "day",
    "days",
    "different",
    "discussion",
    "dont",
    "dr",
    "end",
    "enjoy",
    "episode",
    "episodes",
    "even",
    "ever",
    "every",
    "everyone",
    "everything",
    "favorite",
    "feature",
    "featuring",
    "feed",
    "field",
    "find",
    "first",
    "focus",
    "follow",
    "full",
    "fun",
    "get",
    "give",
    "go",
    "going",
    "good",
    "gmt",
    "great",
    "guest",
    "happen",
    "happening",
    "hear",
    "host",
    "hosted",
    "hour",
    "idea",
    "impact",
    "important",
    "including",
    "information",
    "inside",
    "insight",
    "interesting",
    "interview",
    "issue",
    "join",
    "journalist",
    "keep",
    "know",
    "knowledge",
    "known",
    "latest",
    "leading",
    "learn",
    "let",
    "life",
    "like",
    "listen",
    "listener",
    "little",
    "live",
    "look",
    "looking",
    "made",
    "make",
    "making",
    "many",
    "matter",
    "medium",
    "member",
    "minute",
    "moment",
    "month",
    "mr",
    "mrs",
    "ms",
    "much",
    "name",
    "need",
    "never",
    "new",
    "news",
    "next",
    "night",
    "offer",
    "open",
    "original",
    "other",
    "others",
    "part",
    "past",
    "people",
    "personal",
    "perspective",
    "place",
    "podcast",
    "podcasts",
    "premium",
    "present",
    "problem",
    "produced",
    "producer",
    "product",
    "production",
    "question",
    "radio",
    "read",
    "real",
    "really",
    "review",
    "right",
    "scene",
    "season",
    "see",
    "series",
    "set",
    "share",
    "short",
    "show",
    "shows",
    "side",
    "sign",
    "sir",
    "small",
    "something",
    "sometimes",
    "sound",
    "special",
    "sponsor",
    "start",
    "stories",
    "story",
    "subscribe",
    "support",
    "take",
    "tale",
    "talk",
    "talking",
    "team",
    "tell",
    "thing",
    "think",
    "thought",
    "time",
    "tip",
    "today",
    "together",
    "top",
    "topic",
    "training",
    "true",
    "truth",
    "understand",
    "unique",
    "use",
    "ustream",
    "video",
    "visit",
    "voice",
    "want",
    "way",
    "week",
    "weekly",
    "welcome",
    "well",
    "were",
    "what",
    "word",
    "work",
    "world",
    "would",
    "year",
    "years",
    "youll",
    "youre",
]

CORPORATES = [
    "apple",
    "patreon",
    "spotify",
    "stitcher",
    "itunes",
]

STOPWORDS = {
    "en": ENGLISH_DAYS
    + ENGLISH_MONTHS
    + ENGLISH_NUMBERS
    + ENGLISH_MISC_WORDS
    + CORPORATES
}
NLTK_LANGUAGES = {
    "ar": "arabic",
    "az": "azerbaijani",
    "da": "danish",
    "de": "german",
    "el": "greek",
    "en": "english",
    "es": "spanish",
    "fi": "finnish",
    "fr": "french",
    "hu": "hungarian",
    "id": "indonesian",
    "it": "italian",
    "kk": "kazakh",
    "ne": "nepali",
    "nl": "dutch",
    "no": "norwegian",
    "pt": "portuguese",
    "ro": "romanian",
    "ru": "russian",
    "sl": "slovene",
    "sv": "swedish",
    "tg": "tajik",
    "tr": "turkish",
}

tokenizer = RegexpTokenizer(r"\w+")
lemmatizer = WordNetLemmatizer()


@lru_cache()
def get_stopwords(language):
    """Returns all stopwords for a language, if available.

    Args:
        language (str): 2-char language code e.g. "en"

    Returns:
        frozenset[str]
    """
    try:
        return frozenset(
            stopwords.words(NLTK_LANGUAGES[language]) + STOPWORDS.get(language, [])
        )
    except (OSError, KeyError):
        return frozenset()


def clean_text(text):
    """Scrubs text of any HTML tags and entities, punctuation and numbers.

    Args:
        text (str): text to be cleaned

    Returns:
        str: cleaned text
    """
    text = html.unescape(striptags(text.strip()))
    text = re.sub(r"([^\s\w]|_:.?-)+", "", text)
    text = re.sub(r"\d+", "", text)
    return text


def tokenize(language, text):
    """Extracts all relevant keywords from text, removing any stopwords, HTML tags etc.

    Args:
        language (str): 2-char language code e.g. "en"
        text(str): text source

    Returns:
        str
    """
    if not (text := clean_text(text).casefold()):
        return []

    stopwords_for_language = get_stopwords(language)

    return [
        token
        for token in _lemmatized_tokens(text)
        if token and token not in stopwords_for_language
    ]


def _lemmatized_tokens(text):

    for token in tokenizer.tokenize(text):
        try:
            yield lemmatizer.lemmatize(token)
        except AttributeError:
            # threading issue:
            # 'WordNetCorpusReader' object has no attribute '_LazyCorpusLoader__args'
            pass
