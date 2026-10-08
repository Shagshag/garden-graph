"""Garden texts, per language.

Sentences are full templates with placeholders ({login}, {total}, {first}, {last}, {day}, {month}),
not words glued together: word order, particles and punctuation change from one language to the next.
To add a language, copy an entry of STRINGS and translate it.
"""

STRINGS = {
    "fr": dict(
        title="Le jardin de {login}",
        subtitle="{total} contributions, de {first} à {last}",
        subtitle_year="{total} contributions en {year}",
        footer="pousse, fleur, arbre, éolienne : plus on contribue, plus ça grandit",
        svg_title="Jardin de contributions de {login}",
        date="{day} {month}",
        months=["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
        group=" ",
        fonts="",
        seasons=dict(
            spring="Printemps", summer="Été", autumn="Automne", winter="Hiver",
            cool="Saison fraîche", hot="Saison chaude", monsoon="Mousson", postmonsoon="Après-mousson",
            wet="Saison des pluies", dry="Saison sèche",
            mild="Hiver doux", plum="Pluies de printemps", humid="Été humide", clear="Automne clair",
            sakura="Sakura", tsuyu="Tsuyu (pluies)", earth="À venir"),
    ),
    "en": dict(
        title="{login}'s garden",
        subtitle="{total} contributions, from {first} to {last}",
        subtitle_year="{total} contributions in {year}",
        footer="sprout, flower, tree, wind turbine: the more you contribute, the more it grows",
        svg_title="Contribution garden of {login}",
        date="{month} {day}",
        months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        group=",",
        fonts="",
        seasons=dict(
            spring="Spring", summer="Summer", autumn="Autumn", winter="Winter",
            cool="Cool season", hot="Hot season", monsoon="Monsoon", postmonsoon="Post-monsoon",
            wet="Wet season", dry="Dry season",
            mild="Mild winter", plum="Spring rains", humid="Humid summer", clear="Clear autumn",
            sakura="Sakura", tsuyu="Tsuyu (rainy season)", earth="Upcoming"),
    ),
    "ja": dict(
        title="{login}の庭",
        subtitle="{first}年から{last}年までに{total}件のコントリビューション",
        subtitle_year="{year}年に{total}件のコントリビューション",
        footer="芽、花、木、風車：コントリビューションが増えるほど、庭は育ちます",
        svg_title="{login}のコントリビューションの庭",
        date="{month}月{day}日",
        months=[str(m) for m in range(1, 13)],
        group=",",
        fonts='"Hiragino Sans","Yu Gothic","Noto Sans JP",Meiryo,',
        seasons=dict(
            spring="春", summer="夏", autumn="秋", winter="冬",
            cool="涼季", hot="暑季", monsoon="モンスーン", postmonsoon="モンスーン後",
            wet="雨季", dry="乾季",
            mild="暖冬", plum="春の長雨", humid="蒸し暑い夏", clear="秋晴れ",
            sakura="桜", tsuyu="梅雨", earth="これから"),
    ),
    "hi": dict(
        title="{login} का बगीचा",
        subtitle="{first} से {last} तक {total} योगदान",
        subtitle_year="{year} में {total} योगदान",
        footer="अंकुर, फूल, पेड़, पवन चक्की: जितना ज़्यादा योगदान, उतना बड़ा बगीचा",
        svg_title="{login} का योगदान बगीचा",
        date="{day} {month}",
        months=["जन.", "फ़र.", "मार्च", "अप्रै.", "मई", "जून", "जुल.", "अग.", "सित.", "अक्टू.", "नव.", "दिस."],
        group="indian",  # 12,34,567
        fonts='"Nirmala UI","Noto Sans Devanagari",Mangal,',
        seasons=dict(
            spring="वसंत", summer="गर्मी", autumn="पतझड़", winter="सर्दी",
            cool="ठंडा मौसम", hot="गर्म मौसम", monsoon="मानसून", postmonsoon="मानसून के बाद",
            wet="बरसात का मौसम", dry="सूखा मौसम",
            mild="हल्की सर्दी", plum="वसंत की बारिश", humid="उमस भरी गर्मी", clear="साफ़ पतझड़",
            sakura="साकुरा", tsuyu="त्सुयु (बरसात)", earth="आगामी"),
    ),
}


def number(n, lang):
    """1280 -> "1 280" (fr), "1,280" (en, ja), "12,34,567" (hi, Indian digit grouping)."""
    group = STRINGS[lang]["group"]
    digits = str(n)
    if group != "indian":
        out = f"{n:,}"
        return out.replace(",", group)
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def text_width(text, size):
    """Approximate width of a text: ideographs are about twice as wide as Latin letters."""
    return sum(size * (1.0 if ord(ch) >= 0x2E80 else 0.58) for ch in text)
