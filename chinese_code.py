from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from pathlib import Path

# Register built-in Chinese font (works for Simplified Chinese)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

# Register DejaVu Sans properly
BASE_DIR = Path(__file__).resolve().parent
dejavu_path = BASE_DIR / "dejavu-sans.ttf"  # Cleaner way

print("Font path:", dejavu_path)
print("File exists:", dejavu_path.exists())

if not dejavu_path.exists():
    raise FileNotFoundError(f"Font not found: {dejavu_path}")

# Register with a clean name: "DejaVuSans"
pdfmetrics.registerFont(TTFont("DejaVuSans", str(dejavu_path)))




width, height = A4
margin = 40

path = "Chinese_notes_full_tables_fr.pdf"
c = canvas.Canvas(path, pagesize=A4)

def draw_cover_page():
    c.setFont("STSong-Light", 40)
    title_cn = "我在学中文"
    title_en = "I'm learning Chinese"
    c.drawCentredString(width/2, height*0.65, title_cn)
    c.setFont("DejaVuSans", 24)
    c.drawCentredString(width/2, height*0.58, title_en)
    # Simple pagoda
    base_y = height*0.25
    c.setLineWidth(1.5)
    c.line(margin, base_y, width-margin, base_y)
    x_center = width/2
    levels = 5
    max_width = 220
    level_height = 18
    for i in range(levels):
        w = max_width - i*30
        h = level_height
        x = x_center - w/2
        y = base_y + i*(level_height+4)
        c.line(x, y+h, x + w/2, y+h+10)
        c.line(x + w/2, y+h+10, x+w, y+h)
        c.rect(x+15, y, w-30, h, stroke=1, fill=0)
    c.circle(width*0.78, height*0.72, 12, stroke=1, fill=0)
    c.showPage()

def draw_toc():
    c.setFont("DejaVuSans", 26)
    c.drawString(margin, height - margin - 10, "Contents")
    c.setFont("DejaVuSans", 14)
    sections = [
        "1. Pronouns & Basics",
        "2. Seasons, Months, Days & Numbers",
        "3. Food & Drink",
        "4. Sports & Exercise",
        "5. House & Rooms",
        "6. Daily Routines & Chores",
        "7. Travel & Places",
        "8. Family",
        "9. Professions",
        "10. Verbs",
        "11. Adjectives & Useful Words",
        "12. Telling the Time",
        "13. Directions",
    ]
    y = height - margin - 50
    for s in sections:
        c.drawString(margin+10, y, s)
        y -= 24
    c.showPage()

def draw_table_page(title, rows):
    c.showPage()
    c.setFont("DejaVuSans", 18)
    c.drawString(margin, height - margin, title)
    y = height - margin - 40

    x_hanzi = margin
    x_english = margin + 150
    x_sentence = margin + 320

    c.setFont("DejaVuSans", 11)
    c.drawString(x_hanzi, y, "汉字 / Pinyin")
    c.drawString(x_english, y, "English / Français")
    c.drawString(x_sentence, y, "Example sentence / Phrase exemple")
    y -= 60  # space under header

    for hanzi, pinyin, english, french, sent_hanzi, sent_pinyin, sent_english, sent_french in rows:
        row_height = 85
        if y < margin + row_height:
            c.showPage()
            c.setFont("DejaVuSans", 18)
            c.drawString(margin, height - margin, title + " (cont.)")
            y = height - margin - 40
            c.setFont("DejaVuSans", 11)
            c.drawString(x_hanzi, y, "汉字 / Pinyin")
            c.drawString(x_english, y, "English / Français")
            c.drawString(x_sentence, y, "Example sentence / Phrase exemple")
            y -= 60

        # Column 1
        c.setFont("STSong-Light", 28)
        c.drawString(x_hanzi, y+30, hanzi)
        c.setFont("DejaVuSans", 11)
        c.drawString(x_hanzi, y+12, pinyin)

        # Column 2
        c.setFont("DejaVuSans", 11)
        c.drawString(x_english, y+24, english)
        c.setFont("DejaVuSans", 10)
        c.drawString(x_english, y+8, french)

        # Column 3
        c.setFont("STSong-Light", 16)
        c.drawString(x_sentence, y+30, sent_hanzi)
        c.setFont("DejaVuSans", 10)
        c.drawString(x_sentence, y+14, sent_pinyin)
        c.setFont("DejaVuSans", 9)
        c.drawString(x_sentence, y-2, sent_english)
        c.setFont("DejaVuSans", 9)
        c.drawString(x_sentence, y-16, sent_french)

        y -= row_height

# Cover & TOC
draw_cover_page()
draw_toc()

# 1. Pronouns & Basics
pronoun_rows = [
    ("我", "wǒ", "I / me", "je / moi",
     "我是学生。", "Wǒ shì xuéshēng.", "I am a student.", "Je suis étudiant."),
    ("你", "nǐ", "you (sing.)", "tu / toi",
     "你好吗？", "Nǐ hǎo ma?", "How are you?", "Comment vas-tu ?"),
    ("他", "tā", "he / him", "il / lui",
     "他是老师。", "Tā shì lǎoshī.", "He is a teacher.", "Il est professeur."),
    ("她", "tā", "she / her", "elle",
     "她很高兴。", "Tā hěn gāoxìng.", "She is very happy.", "Elle est très contente."),
    ("我们", "wǒmen", "we / us", "nous",
     "我们住在北京。", "Wǒmen zhù zài Běijīng.", "We live in Beijing.", "Nous habitons à Pékin."),
    ("你们", "nǐmen", "you (plural)", "vous",
     "你们喜欢中国菜吗？", "Nǐmen xǐhuan Zhōngguó cài ma?", "Do you like Chinese food?", "Est-ce que vous aimez la cuisine chinoise ?"),
    ("他们", "tāmen", "they / them", "ils / elles",
     "他们在工作。", "Tāmen zài gōngzuò.", "They are working.", "Ils sont en train de travailler."),
    ("你好", "nǐ hǎo", "hello", "bonjour",
     "你好，我叫小明。", "Nǐ hǎo, wǒ jiào Xiǎomíng.", "Hello, my name is Xiaoming.", "Bonjour, je m'appelle Xiaoming."),
    ("好的", "hǎo de", "OK / alright", "d'accord",
     "好的，我们走吧。", "Hǎo de, wǒmen zǒu ba.", "OK, let's go.", "D'accord, allons-y."),
    ("对", "duì", "correct / right", "correct / juste",
     "对，你说得对。", "Duì, nǐ shuō de duì.", "Yes, what you said is right.", "Oui, ce que tu dis est juste."),
    ("谢谢", "xièxie", "thanks", "merci",
     "谢谢你的帮助。", "Xièxie nǐ de bāngzhù.", "Thank you for your help.", "Merci pour ton aide."),
    ("不客气", "bú kèqi", "you’re welcome", "de rien / je t'en prie",
     "不客气。", "Bú kèqi.", "You're welcome.", "De rien."),
]
draw_table_page("Pronouns & Basics", pronoun_rows)

# 2. Seasons, Months, Days & Numbers
season_month_rows = [
    ("春天", "chūntiān", "spring", "le printemps",
     "春天的花很漂亮。", "Chūntiān de huā hěn piàoliang.", "The flowers in spring are beautiful.", "Les fleurs au printemps sont très belles."),
    ("夏天", "xiàtiān", "summer", "l'été",
     "夏天很热。", "Xiàtiān hěn rè.", "Summer is very hot.", "L'été, il fait très chaud."),
    ("秋天", "qiūtiān", "autumn / fall", "l'automne",
     "秋天我喜欢去爬山。", "Qiūtiān wǒ xǐhuan qù páshān.", "In autumn I like to go hiking.", "En automne, j'aime faire de la randonnée."),
    ("冬天", "dōngtiān", "winter", "l'hiver",
     "冬天常常下雪。", "Dōngtiān chángcháng xià xuě.", "It often snows in winter.", "En hiver, il neige souvent."),
    ("一月", "yīyuè", "January", "janvier",
     "一月的天气很冷。", "Yīyuè de tiānqì hěn lěng.", "The weather in January is very cold.", "En janvier, il fait très froid."),
    ("二月", "èryuè", "February", "février",
     "二月只有二十八天。", "Èryuè zhǐ yǒu èrshíbā tiān.", "February has only 28 days.", "Février n'a que vingt-huit jours."),
    ("三月", "sānyuè", "March", "mars",
     "三月开始下雨。", "Sānyuè kāishǐ xià yǔ.", "It starts to rain in March.", "En mars, il commence à pleuvoir."),
    ("四月", "sìyuè", "April", "avril",
     "四月有很多花。", "Sìyuè yǒu hěn duō huā.", "There are many flowers in April.", "En avril, il y a beaucoup de fleurs."),
    ("五月", "wǔyuè", "May", "mai",
     "五月我们放假。", "Wǔyuè wǒmen fàngjià.", "We have a holiday in May.", "En mai, nous sommes en vacances."),
    ("六月", "liùyuè", "June", "juin",
     "六月是夏天的开始。", "Liùyuè shì xiàtiān de kāishǐ.", "June is the beginning of summer.", "Juin est le début de l'été."),
    ("七月", "qīyuè", "July", "juillet",
     "七月很热。", "Qīyuè hěn rè.", "July is very hot.", "En juillet, il fait très chaud."),
    ("八月", "bāyuè", "August", "août",
     "八月我们去海边。", "Bāyuè wǒmen qù hǎibiān.", "We go to the seaside in August.", "En août, nous allons à la mer."),
    ("九月", "jiǔyuè", "September", "septembre",
     "九月开学。", "Jiǔyuè kāixué.", "School starts in September.", "En septembre, l'école recommence."),
    ("十月", "shíyuè", "October", "octobre",
     "十月的天空很蓝。", "Shíyuè de tiānkōng hěn lán.", "The sky in October is very blue.", "En octobre, le ciel est très bleu."),
    ("十一月", "shíyīyuè", "November", "novembre",
     "十一月常常下雨。", "Shíyīyuè chángcháng xià yǔ.", "It often rains in November.", "En novembre, il pleut souvent."),
    ("十二月", "shí'èr yuè", "December", "décembre",
     "十二月是冬天。", "Shí'èr yuè shì dōngtiān.", "December is winter.", "Décembre est en hiver."),
    ("星期一", "xīngqī yī", "Monday", "lundi",
     "星期一我很忙。", "Xīngqī yī wǒ hěn máng.", "I am very busy on Monday.", "Je suis très occupé le lundi."),
    ("星期二", "xīngqī èr", "Tuesday", "mardi",
     "我们星期二上课。", "Wǒmen xīngqī èr shàngkè.", "We have class on Tuesday.", "Nous avons cours le mardi."),
    ("星期三", "xīngqī sān", "Wednesday", "mercredi",
     "星期三去游泳。", "Xīngqī sān qù yóuyǒng.", "We go swimming on Wednesday.", "Le mercredi, nous allons nager."),
    ("星期四", "xīngqī sì", "Thursday", "jeudi",
     "星期四开会。", "Xīngqī sì kāihuì.", "We have a meeting on Thursday.", "Nous avons une réunion le jeudi."),
    ("星期五", "xīngqī wǔ", "Friday", "vendredi",
     "星期五晚上看电影。", "Xīngqī wǔ wǎnshang kàn diànyǐng.", "We watch a movie on Friday evening.", "Le vendredi soir, nous regardons un film."),
    ("星期六", "xīngqī liù", "Saturday", "samedi",
     "星期六我休息。", "Xīngqī liù wǒ xiūxi.", "I rest on Saturday.", "Le samedi, je me repose."),
    ("星期日", "xīngqī rì", "Sunday", "dimanche",
     "星期日去公园。", "Xīngqī rì qù gōngyuán.", "We go to the park on Sunday.", "Le dimanche, nous allons au parc."),
    ("一", "yī", "one", "un",
     "我有一个苹果。", "Wǒ yǒu yí gè píngguǒ.", "I have one apple.", "J'ai une pomme."),
    ("二", "èr", "two", "deux",
     "他有两个妹妹。", "Tā yǒu liǎng gè mèimei.", "He has two younger sisters.", "Il a deux petites sœurs."),
    ("三", "sān", "three", "trois",
     "我有三本书。", "Wǒ yǒu sān běn shū.", "I have three books.", "J'ai trois livres."),
    ("四", "sì", "four", "quatre",
     "桌子上有四个杯子。", "Zhuōzi shàng yǒu sì gè bēizi.", "There are four cups on the table.", "Il y a quatre tasses sur la table."),
    ("五", "wǔ", "five", "cinq",
     "教室里有五个人。", "Jiàoshì lǐ yǒu wǔ gè rén.", "There are five people in the classroom.", "Il y a cinq personnes dans la salle de classe."),
    ("六", "liù", "six", "six",
     "我们六点吃饭。", "Wǒmen liù diǎn chīfàn.", "We eat at six o'clock.", "Nous mangeons à six heures."),
    ("七", "qī", "seven", "sept",
     "他七点起床。", "Tā qī diǎn qǐchuáng.", "He gets up at seven.", "Il se lève à sept heures."),
    ("八", "bā", "eight", "huit",
     "他们八点上班。", "Tāmen bā diǎn shàngbān.", "They start work at eight.", "Ils commencent à travailler à huit heures."),
    ("九", "jiǔ", "nine", "neuf",
     "我九点睡觉。", "Wǒ jiǔ diǎn shuìjiào.", "I go to bed at nine.", "Je me couche à neuf heures."),
    ("十", "shí", "ten", "dix",
     "这里有十张桌子。", "Zhèlǐ yǒu shí zhāng zhuōzi.", "There are ten tables here.", "Il y a dix tables ici."),
    ("十一", "shíyī", "eleven", "onze",
     "教室里有十一名学生。", "Jiàoshì lǐ yǒu shíyī míng xuéshēng.", "There are eleven students in the classroom.", "Il y a onze élèves dans la salle de classe."),
    ("十二", "shí'èr", "twelve", "douze",
     "他十二岁。", "Tā shí'èr suì.", "He is twelve years old.", "Il a douze ans."),
    ("十三", "shísān", "thirteen", "treize",
     "我十三号出发。", "Wǒ shísān hào chūfā.", "I leave on the 13th.", "Je pars le treize."),
    ("十四", "shísì", "fourteen", "quatorze",
     "今天是十四号。", "Jīntiān shì shísì hào.", "Today is the 14th.", "Nous sommes le quatorze aujourd'hui."),
    ("十五", "shíwǔ", "fifteen", "quinze",
     "我有十五块钱。", "Wǒ yǒu shíwǔ kuài qián.", "I have fifteen yuan.", "J'ai quinze yuans."),
    ("十六", "shíliù", "sixteen", "seize",
     "她十六岁。", "Tā shíliù suì.", "She is sixteen.", "Elle a seize ans."),
    ("十七", "shíqī", "seventeen", "dix-sept",
     "十七个人在这儿。", "Shíqī gè rén zài zhèr.", "Seventeen people are here.", "Il y a dix-sept personnes ici."),
    ("十八", "shíbā", "eighteen", "dix-huit",
     "他十八号到北京。", "Tā shíbā hào dào Běijīng.", "He arrives in Beijing on the 18th.", "Il arrive à Pékin le dix-huit."),
    ("十九", "shíjiǔ", "nineteen", "dix-neuf",
     "今天是十九号。", "Jīntiān shì shíjiǔ hào.", "Today is the 19th.", "Nous sommes le dix-neuf aujourd'hui."),
    ("二十", "èrshí", "twenty", "vingt",
     "教室有二十把椅子。", "Jiàoshì yǒu èrshí bǎ yǐzi.", "The classroom has twenty chairs.", "La salle de classe a vingt chaises."),
]
draw_table_page("Seasons, Months, Days & Numbers", season_month_rows)

# 3. Food & Drink
food_rows = [
    ("水", "shuǐ", "water", "eau",
     "请给我一杯水。", "Qǐng gěi wǒ yì bēi shuǐ.", "Please give me a glass of water.", "S'il te plaît, donne-moi un verre d'eau."),
    ("茶", "chá", "tea", "thé",
     "我每天喝茶。", "Wǒ měitiān hē chá.", "I drink tea every day.", "Je bois du thé tous les jours."),
    ("咖啡", "kāfēi", "coffee", "café",
     "他早上喝咖啡。", "Tā zǎoshang hē kāfēi.", "He drinks coffee in the morning.", "Il boit du café le matin."),
    ("米饭", "mǐfàn", "cooked rice", "riz cuit",
     "我喜欢吃米饭。", "Wǒ xǐhuan chī mǐfàn.", "I like to eat rice.", "J'aime manger du riz."),
    ("热", "rè", "hot (temperature)", "chaud",
     "汤很热，小心！", "Tāng hěn rè, xiǎoxīn!", "The soup is hot, be careful!", "La soupe est très chaude, fais attention !"),
    ("冷", "lěng", "cold", "froid",
     "今天有点冷。", "Jīntiān yǒudiǎn lěng.", "It is a bit cold today.", "Il fait un peu froid aujourd'hui."),
    ("辣", "là", "spicy", "épicé",
     "这个菜很辣。", "Zhè ge cài hěn là.", "This dish is very spicy.", "Ce plat est très épicé."),
    ("好吃", "hǎochī", "tasty / delicious", "bon / délicieux",
     "饺子很好吃。", "Jiǎozi hěn hǎochī.", "Dumplings are delicious.", "Les raviolis chinois sont délicieux."),
    ("西红柿", "xīhóngshì", "tomato", "tomate",
     "我买了三个西红柿。", "Wǒ mǎi le sān gè xīhóngshì.", "I bought three tomatoes.", "J'ai acheté trois tomates."),
    ("土豆", "tǔdòu", "potato", "pomme de terre",
     "他喜欢吃土豆。", "Tā xǐhuan chī tǔdòu.", "He likes to eat potatoes.", "Il aime manger des pommes de terre."),
    ("肉", "ròu", "meat", "viande",
     "我不吃肉。", "Wǒ bù chī ròu.", "I don’t eat meat.", "Je ne mange pas de viande."),
    ("菜", "cài", "dish; vegetables", "plat / légumes",
     "今天的菜很好吃。", "Jīntiān de cài hěn hǎochī.", "Today’s dishes are very tasty.", "Les plats d'aujourd'hui sont très bons."),
    ("蔬菜", "shūcài", "vegetables", "légumes",
     "多吃蔬菜对身体好。", "Duō chī shūcài duì shēntǐ hǎo.", "Eating more vegetables is good for your body.", "Manger beaucoup de légumes est bon pour la santé."),
    ("水果", "shuǐguǒ", "fruit", "fruit",
     "你喜欢什么水果？", "Nǐ xǐhuan shénme shuǐguǒ?", "What fruit do you like?", "Quel fruit aimes-tu ?"),
    ("饺子", "jiǎozi", "dumplings", "raviolis chinois",
     "我妈妈做的饺子最好吃。", "Wǒ māma zuò de jiǎozi zuì hǎochī.", "The dumplings my mum makes are the best.", "Les raviolis que prépare ma mère sont les meilleurs."),
]
draw_table_page("Food & Drink", food_rows)

# 4. Sports & Exercise
sports_rows = [
    ("打篮球", "dǎ lánqiú", "to play basketball", "jouer au basket(-ball)",
     "我们下午打篮球。", "Wǒmen xiàwǔ dǎ lánqiú.", "We play basketball this afternoon.", "Nous jouons au basket cet après-midi."),
    ("打排球", "dǎ páiqiú", "to play volleyball", "jouer au volley(-ball)",
     "你会打排球吗？", "Nǐ huì dǎ páiqiú ma?", "Can you play volleyball?", "Sais-tu jouer au volley ?"),
    ("打网球", "dǎ wǎngqiú", "to play tennis", "jouer au tennis",
     "他们周末打网球。", "Tāmen zhōumò dǎ wǎngqiú.", "They play tennis at the weekend.", "Ils jouent au tennis le week-end."),
    ("跑步", "pǎobù", "to run / go running", "courir / faire du footing",
     "我每天早上跑步。", "Wǒ měitiān zǎoshang pǎobù.", "I go running every morning.", "Je vais courir tous les matins."),
    ("游泳", "yóuyǒng", "to swim", "nager / faire de la natation",
     "夏天我们去游泳。", "Xiàtiān wǒmen qù yóuyǒng.", "We go swimming in summer.", "En été, nous allons nager."),
    ("运动", "yùndòng", "exercise / sports", "faire du sport",
     "多运动对身体好。", "Duō yùndòng duì shēntǐ hǎo.", "Exercising more is good for your health.", "Faire plus de sport est bon pour la santé."),
    ("健身房", "jiànshēnfáng", "gym", "salle de sport",
     "他在健身房工作。", "Tā zài jiànshēnfáng gōngzuò.", "He works at the gym.", "Il travaille dans une salle de sport."),
]
draw_table_page("Sports & Exercise", sports_rows)

# 5. House & Rooms
house_rows = [
    ("房子", "fángzi", "house", "maison",
     "这是一座新房子。", "Zhè shì yí zuò xīn fángzi.", "This is a new house.", "C'est une nouvelle maison."),
    ("房间", "fángjiān", "room", "pièce / chambre",
     "我的房间很大。", "Wǒ de fángjiān hěn dà.", "My room is very big.", "Ma chambre est très grande."),
    ("客厅", "kètīng", "living room", "salon",
     "我们在客厅看电视。", "Wǒmen zài kètīng kàn diànshì.", "We watch TV in the living room.", "Nous regardons la télé dans le salon."),
    ("卧室", "wòshì", "bedroom", "chambre",
     "她在卧室睡觉。", "Tā zài wòshì shuìjiào.", "She is sleeping in the bedroom.", "Elle dort dans la chambre."),
    ("厨房", "chúfáng", "kitchen", "cuisine",
     "妈妈在厨房做饭。", "Māma zài chúfáng zuò fàn.", "Mum is cooking in the kitchen.", "Maman prépare le repas dans la cuisine."),
    ("新", "xīn", "new", "nouveau / neuf",
     "我买了一辆新车。", "Wǒ mǎi le yí liàng xīn chē.", "I bought a new car.", "J'ai acheté une nouvelle voiture."),
    ("旧", "jiù", "old", "vieux / ancien",
     "这件衣服很旧。", "Zhè jiàn yīfu hěn jiù.", "These clothes are very old.", "Ces vêtements sont très vieux."),
    ("大", "dà", "big", "grand",
     "北京是一个大城市。", "Běijīng shì yí gè dà chéngshì.", "Beijing is a big city.", "Pékin est une grande ville."),
    ("小", "xiǎo", "small", "petit",
     "这只狗很小。", "Zhè zhī gǒu hěn xiǎo.", "This dog is very small.", "Ce chien est très petit."),
    ("漂亮", "piàoliang", "beautiful / pretty", "beau / jolie",
     "你的房子很漂亮。", "Nǐ de fángzi hěn piàoliang.", "Your house is very beautiful.", "Ta maison est très belle."),
]
draw_table_page("House & Rooms", house_rows)

# 6. Daily Routines & Chores
chores_rows = [
    ("洗碗", "xǐ wǎn", "wash the dishes", "faire la vaisselle",
     "我晚饭后洗碗。", "Wǒ wǎnfàn hòu xǐ wǎn.", "I wash the dishes after dinner.", "Je fais la vaisselle après le dîner."),
    ("扫地", "sǎo dì", "sweep the floor", "balayer le sol",
     "哥哥在扫地。", "Gēge zài sǎo dì.", "Elder brother is sweeping the floor.", "Mon grand frère est en train de balayer le sol."),
    ("拖地", "tuō dì", "mop the floor", "passer la serpillière",
     "请你帮我拖地。", "Qǐng nǐ bāng wǒ tuō dì.", "Please help me mop the floor.", "S'il te plaît, aide-moi à passer la serpillière."),
    ("打扫", "dǎsǎo", "to clean / tidy up", "nettoyer / ranger",
     "我们周末打扫房间。", "Wǒmen zhōumò dǎsǎo fángjiān.", "We clean the room at the weekend.", "Le week-end, nous nettoyons la chambre."),
    ("看电视", "kàn diànshì", "to watch TV", "regarder la télé",
     "不要一直看电视。", "Bú yào yìzhí kàn diànshì.", "Don’t watch TV all the time.", "Ne regarde pas la télé tout le temps."),
]
draw_table_page("Daily Routines & Chores", chores_rows)

# 7. Travel & Places
travel_rows = [
    ("北京", "Běijīng", "Beijing", "Pékin",
     "我想去北京旅行。", "Wǒ xiǎng qù Běijīng lǚxíng.", "I want to travel to Beijing.", "Je veux voyager à Pékin."),
    ("公园", "gōngyuán", "park", "parc",
     "我们在公园散步。", "Wǒmen zài gōngyuán sànbù.", "We take a walk in the park.", "Nous nous promenons dans le parc."),
    ("博物馆", "bówùguǎn", "museum", "musée",
     "这个城市有一个大博物馆。", "Zhè gè chéngshì yǒu yí gè dà bówùguǎn.", "This city has a big museum.", "Cette ville a un grand musée."),
    ("故宫", "Gùgōng", "the Forbidden City", "la Cité interdite",
     "很多游客去故宫。", "Hěn duō yóukè qù Gùgōng.", "Many tourists go to the Forbidden City.", "Beaucoup de touristes vont à la Cité interdite."),
    ("学校", "xuéxiào", "school", "école",
     "弟弟在学校学习。", "Dìdi zài xuéxiào xuéxí.", "Little brother studies at school.", "Mon petit frère étudie à l'école."),
    ("饭店", "fàndiàn", "restaurant / hotel", "hôtel / restaurant",
     "我们住在这家饭店。", "Wǒmen zhù zài zhè jiā fàndiàn.", "We are staying at this hotel.", "Nous logeons dans cet hôtel."),
    ("餐厅", "cāntīng", "restaurant", "restaurant",
     "这家餐厅很有名。", "Zhè jiā cāntīng hěn yǒumíng.", "This restaurant is very famous.", "Ce restaurant est très connu."),
]
draw_table_page("Travel & Places", travel_rows)

# 8. Family
family_rows = [
    ("妈妈", "māma", "mum", "maman",
     "我妈妈很忙。", "Wǒ māma hěn máng.", "My mum is very busy.", "Ma mère est très occupée."),
    ("爸爸", "bàba", "dad", "papa",
     "爸爸喜欢看足球。", "Bàba xǐhuan kàn zúqiú.", "Dad likes watching football.", "Mon père aime regarder le football."),
    ("老公", "lǎogōng", "husband", "mari",
     "她的老公是医生。", "Tā de lǎogōng shì yīshēng.", "Her husband is a doctor.", "Son mari est médecin."),
    ("老婆", "lǎopo", "wife", "femme / épouse",
     "我老婆会说中文。", "Wǒ lǎopo huì shuō Zhōngwén.", "My wife can speak Chinese.", "Ma femme sait parler chinois."),
    ("爷爷", "yéye", "grandfather (paternal)", "grand-père (paternel)",
     "爷爷每天早起。", "Yéye měitiān zǎoqǐ.", "Grandfather gets up early every day.", "Mon grand-père se lève tôt tous les jours."),
    ("女儿", "nǚ’ér", "daughter", "fille",
     "我们有一个女儿。", "Wǒmen yǒu yí gè nǚ’ér.", "We have a daughter.", "Nous avons une fille."),
    ("儿子", "érzi", "son", "fils",
     "他的儿子五岁。", "Tā de érzi wǔ suì.", "His son is five years old.", "Son fils a cinq ans."),
    ("姐姐", "jiějie", "older sister", "grande sœur",
     "姐姐在上海工作。", "Jiějie zài Shànghǎi gōngzuò.", "Older sister works in Shanghai.", "Ma grande sœur travaille à Shanghai."),
    ("妹妹", "mèimei", "younger sister", "petite sœur",
     "妹妹喜欢画画。", "Mèimei xǐhuan huàhuà.", "Younger sister likes drawing.", "Ma petite sœur aime dessiner."),
    ("兄弟", "xiōngdì", "brothers / bros", "frères",
     "他们是好兄弟。", "Tāmen shì hǎo xiōngdì.", "They are good brothers.", "Ils sont de bons frères."),
]
draw_table_page("Family", family_rows)

# 9. Professions
profession_rows = [
    ("电工", "diàngōng", "electrician", "électricien",
     "他是电工。", "Tā shì diàngōng.", "He is an electrician.", "Il est électricien."),
    ("医生", "yīshēng", "doctor", "médecin",
     "我想当医生。", "Wǒ xiǎng dāng yīshēng.", "I want to be a doctor.", "Je voudrais devenir médecin."),
    ("律师", "lǜshī", "lawyer", "avocat / avocate",
     "她是有名的律师。", "Tā shì yǒumíng de lǜshī.", "She is a famous lawyer.", "Elle est une avocate célèbre."),
    ("老师", "lǎoshī", "teacher", "professeur / enseignant",
     "老师在教中文。", "Lǎoshī zài jiāo Zhōngwén.", "The teacher is teaching Chinese.", "Le professeur enseigne le chinois."),
]
draw_table_page("Professions", profession_rows)

# 10. Verbs
verb_rows = [
    ("是", "shì", "to be", "être",
     "这是我的书。", "Zhè shì wǒ de shū.", "This is my book.", "Ceci est mon livre."),
    ("有", "yǒu", "to have", "avoir",
     "我有两个妹妹。", "Wǒ yǒu liǎng gè mèimei.", "I have two younger sisters.", "J'ai deux petites sœurs."),
    ("喜欢", "xǐhuan", "to like", "aimer / apprécier",
     "我喜欢中国菜。", "Wǒ xǐhuan Zhōngguó cài.", "I like Chinese food.", "J'aime la cuisine chinoise."),
    ("要", "yào", "to want / need", "vouloir / avoir besoin de",
     "你要喝什么？", "Nǐ yào hē shénme?", "What do you want to drink?", "Que veux-tu boire ?"),
    ("想", "xiǎng", "to want / to think", "vouloir / penser",
     "我想去旅行。", "Wǒ xiǎng qù lǚxíng.", "I want to travel.", "Je veux voyager."),
    ("需要", "xūyào", "to need", "avoir besoin de",
     "我需要你的帮助。", "Wǒ xūyào nǐ de bāngzhù.", "I need your help.", "J'ai besoin de ton aide."),
    ("做", "zuò", "to do / make", "faire",
     "你在做什么？", "Nǐ zài zuò shénme?", "What are you doing?", "Qu'est-ce que tu fais ?"),
    ("吃", "chī", "to eat", "manger",
     "我们一起吃饭吧。", "Wǒmen yìqǐ chī fàn ba.", "Let’s eat together.", "Mangeons ensemble."),
    ("喝", "hē", "to drink", "boire",
     "多喝水。", "Duō hē shuǐ.", "Drink more water.", "Bois plus d'eau."),
    ("做饭", "zuò fàn", "to cook", "cuisiner / faire à manger",
     "爸爸在厨房做饭。", "Bàba zài chúfáng zuò fàn.", "Dad is cooking in the kitchen.", "Papa cuisine dans la cuisine."),
    ("去", "qù", "to go", "aller",
     "我们去学校。", "Wǒmen qù xuéxiào.", "We are going to school.", "Nous allons à l'école."),
    ("来", "lái", "to come", "venir",
     "请到我家来。", "Qǐng dào wǒ jiā lái.", "Please come to my home.", "Viens chez moi, s'il te plaît."),
    ("跑步", "pǎobù", "to run", "courir",
     "他每天早上跑步。", "Tā měitiān zǎoshang pǎobù.", "He runs every morning.", "Il court tous les matins."),
    ("游泳", "yóuyǒng", "to swim", "nager",
     "我不会游泳。", "Wǒ bú huì yóuyǒng.", "I can’t swim.", "Je ne sais pas nager."),
    ("运动", "yùndòng", "to exercise", "faire du sport / bouger",
     "我们晚上运动。", "Wǒmen wǎnshang yùndòng.", "We exercise in the evening.", "Nous faisons du sport le soir."),
    ("打篮球", "dǎ lánqiú", "to play basketball", "jouer au basket",
     "周末一起打篮球吧。", "Zhōumò yìqǐ dǎ lánqiú ba.", "Let’s play basketball at the weekend.", "Jouons au basket ce week-end."),
    ("打排球", "dǎ páiqiú", "to play volleyball", "jouer au volley",
     "他们在海边打排球。", "Tāmen zài hǎibiān dǎ páiqiú.", "They play volleyball at the beach.", "Ils jouent au volley à la plage."),
    ("打网球", "dǎ wǎngqiú", "to play tennis", "jouer au tennis",
     "姐姐喜欢打网球。", "Jiějie xǐhuan dǎ wǎngqiú.", "Older sister likes playing tennis.", "Ma grande sœur aime jouer au tennis."),
    ("睡觉", "shuìjiào", "to sleep", "dormir",
     "宝宝在睡觉。", "Bǎobao zài shuìjiào.", "The baby is sleeping.", "Le bébé est en train de dormir."),
    ("看", "kàn", "to look / watch", "regarder",
     "请看这张照片。", "Qǐng kàn zhè zhāng zhàopiàn.", "Please look at this photo.", "Regarde cette photo, s'il te plaît."),
    ("看电视", "kàn diànshì", "to watch TV", "regarder la télévision",
     "他们晚上看电视。", "Tāmen wǎnshang kàn diànshì.", "They watch TV in the evening.", "Ils regardent la télé le soir."),
    ("说", "shuō", "to speak / say", "parler / dire",
     "他说中文。", "Tā shuō Zhōngwén.", "He speaks Chinese.", "Il parle chinois."),
    ("学习", "xuéxí", "to study", "étudier",
     "我在学习汉语。", "Wǒ zài xuéxí Hànyǔ.", "I am studying Chinese.", "J'étudie le chinois."),
    ("工作", "gōngzuò", "to work", "travailler",
     "妈妈在银行工作。", "Māma zài yínháng gōngzuò.", "Mum works in a bank.", "Ma mère travaille dans une banque."),
    ("打扫", "dǎsǎo", "to clean / tidy", "nettoyer / faire le ménage",
     "今天我们打扫家里。", "Jīntiān wǒmen dǎsǎo jiālǐ.", "Today we clean the house.", "Aujourd'hui, nous faisons le ménage à la maison."),
    ("洗碗", "xǐ wǎn", "to wash dishes", "faire la vaisselle",
     "你帮我洗碗好吗？", "Nǐ bāng wǒ xǐ wǎn hǎo ma?", "Can you help me wash the dishes?", "Peux-tu m'aider à faire la vaisselle ?"),
    ("扫地", "sǎo dì", "to sweep", "balayer",
     "他在客厅扫地。", "Tā zài kètīng sǎo dì.", "He is sweeping the living room.", "Il balaie le salon."),
    ("拖地", "tuō dì", "to mop", "passer la serpillière",
     "她在厨房拖地。", "Tā zài chúfáng tuō dì.", "She is mopping the kitchen floor.", "Elle passe la serpillière dans la cuisine."),
]
draw_table_page("Verbs", verb_rows)

# 11. Adjectives & Useful Words
adj_rows = [
    ("热", "rè", "hot", "chaud",
     "今天很热。", "Jīntiān hěn rè.", "It is very hot today.", "Il fait très chaud aujourd'hui."),
    ("冷", "lěng", "cold", "froid",
     "外面很冷。", "Wàimiàn hěn lěng.", "It is very cold outside.", "Dehors, il fait très froid."),
    ("辣", "là", "spicy", "épicé",
     "我不太能吃辣。", "Wǒ bú tài néng chī là.", "I can’t really eat spicy food.", "Je ne supporte pas très bien la nourriture épicée."),
    ("大", "dà", "big", "grand",
     "这只猫很大。", "Zhè zhī māo hěn dà.", "This cat is very big.", "Ce chat est très grand."),
    ("小", "xiǎo", "small", "petit",
     "小孩子在玩。", "Xiǎo háizi zài wán.", "The little children are playing.", "Les petits enfants jouent."),
    ("新", "xīn", "new", "nouveau / neuf",
     "我有一个新手机。", "Wǒ yǒu yí gè xīn shǒujī.", "I have a new mobile phone.", "J'ai un nouveau téléphone portable."),
    ("旧", "jiù", "old", "vieux / ancien",
     "这本书很旧。", "Zhè běn shū hěn jiù.", "This book is very old.", "Ce livre est très vieux."),
    ("漂亮", "piàoliang", "pretty / beautiful", "joli / beau",
     "她的衣服很漂亮。", "Tā de yīfu hěn piàoliang.", "Her clothes are very beautiful.", "Ses vêtements sont très jolis."),
    ("特别", "tèbié", "especially", "surtout / particulièrement",
     "我特别喜欢这首歌。", "Wǒ tèbié xǐhuan zhè shǒu gē.", "I especially like this song.", "J'aime particulièrement cette chanson."),
    ("慢", "màn", "slow", "lent",
     "请说慢一点。", "Qǐng shuō màn yìdiǎn.", "Please speak a bit more slowly.", "Parle un peu plus lentement, s'il te plaît."),
    ("快", "kuài", "fast", "rapide / vite",
     "时间过得很快。", "Shíjiān guò de hěn kuài.", "Time passes very quickly.", "Le temps passe très vite."),
]
draw_table_page("Adjectives & Useful Words", adj_rows)

# 12. Telling the Time
time_rows = [
    ("现在", "xiànzài", "now", "maintenant",
     "现在三点。", "Xiànzài sān diǎn.", "It is three o'clock now.", "Il est trois heures maintenant."),
    ("点", "diǎn", "o'clock; hour", "heure(s)",
     "我们八点见。", "Wǒmen bā diǎn jiàn.", "We meet at eight o'clock.", "On se voit à huit heures."),
    ("分", "fēn", "minute", "minute",
     "现在三点二十分。", "Xiànzài sān diǎn èrshí fēn.", "It is 3:20 now.", "Il est maintenant trois heures vingt."),
    ("半", "bàn", "half", "et demie",
     "现在四点半。", "Xiànzài sì diǎn bàn.", "It is half past four.", "Il est quatre heures et demie."),
    ("刻", "kè", "quarter (of an hour)", "quart d'heure",
     "七点一刻上课。", "Qī diǎn yí kè shàngkè.", "Class starts at 7:15.", "Le cours commence à sept heures et quart."),
    ("上午", "shàngwǔ", "morning (before noon)", "matin (avant midi)",
     "我上午工作。", "Wǒ shàngwǔ gōngzuò.", "I work in the morning.", "Je travaille le matin."),
    ("下午", "xiàwǔ", "afternoon", "après-midi",
     "我们下午开会。", "Wǒmen xiàwǔ kāihuì.", "We have a meeting in the afternoon.", "Nous avons une réunion l'après-midi."),
    ("晚上", "wǎnshang", "evening / night", "soir / nuit",
     "我晚上学习中文。", "Wǒ wǎnshang xuéxí Zhōngwén.", "I study Chinese in the evening.", "J'étudie le chinois le soir."),
    ("一点", "yī diǎn", "one o'clock", "une heure",
     "一点我们吃午饭。", "Yī diǎn wǒmen chī wǔfàn.", "We eat lunch at one o'clock.", "Nous déjeunons à une heure."),
    ("两点", "liǎng diǎn", "two o'clock", "deux heures",
     "两点去图书馆。", "Liǎng diǎn qù túshūguǎn.", "At two o'clock we go to the library.", "À deux heures, nous allons à la bibliothèque."),
    ("三点半", "sān diǎn bàn", "half past three", "trois heures et demie",
     "现在三点半。", "Xiànzài sān diǎn bàn.", "It is half past three.", "Il est trois heures et demie."),
    ("七点一刻", "qī diǎn yí kè", "quarter past seven", "sept heures et quart",
     "七点一刻出门。", "Qī diǎn yí kè chūmén.", "We leave at 7:15.", "Nous sortons à sept heures et quart."),
    ("九点三刻", "jiǔ diǎn sān kè", "quarter to ten", "dix heures moins le quart",
     "九点三刻睡觉。", "Jiǔ diǎn sān kè shuìjiào.", "I go to bed at 9:45.", "Je me couche à dix heures moins le quart."),
    ("十点十分", "shí diǎn shí fēn", "ten ten (10:10)", "dix heures dix",
     "车十点十分到。", "Chē shí diǎn shí fēn dào.", "The bus arrives at 10:10.", "Le bus arrive à dix heures dix."),
    ("中午十二点", "zhōngwǔ shí'èr diǎn", "twelve noon", "midi",
     "我们中午十二点见。", "Wǒmen zhōngwǔ shí'èr diǎn jiàn.", "We meet at twelve noon.", "On se retrouve à midi."),
]
draw_table_page("Telling the Time", time_rows)

# 13. Directions
direction_rows = [
    ("左边", "zuǒbian", "left side", "à gauche",
     "银行在超市左边。", "Yínháng zài chāoshì zuǒbian.", "The bank is on the left of the supermarket.", "La banque est à gauche du supermarché."),
    ("右边", "yòubian", "right side", "à droite",
     "学校在公园右边。", "Xuéxiào zài gōngyuán yòubian.", "The school is on the right of the park.", "L'école est à droite du parc."),
    ("前面", "qiánmiàn", "in front; ahead", "devant / devant soi",
     "前面有一个红绿灯。", "Qiánmiàn yǒu yí gè hónglǜdēng.", "There is a traffic light ahead.", "Devant, il y a un feu rouge."),
    ("后面", "hòumiàn", "behind", "derrière",
     "超市在我家后面。", "Chāoshì zài wǒ jiā hòumiàn.", "The supermarket is behind my home.", "Le supermarché est derrière chez moi."),
    ("旁边", "pángbiān", "next to", "à côté de",
     "公交站在学校旁边。", "Gōngjiāo zhàn zài xuéxiào pángbiān.", "The bus stop is next to the school.", "L'arrêt de bus est à côté de l'école."),
    ("对面", "duìmiàn", "opposite; across from", "en face de",
     "银行在邮局对面。", "Yínháng zài yóujú duìmiàn.", "The bank is opposite the post office.", "La banque est en face de la poste."),
    ("一直走", "yìzhí zǒu", "go straight", "aller tout droit",
     "一直走，然后左转。", "Yìzhí zǒu, ránhòu zuǒ zhuǎn.", "Go straight, then turn left.", "Va tout droit, puis tourne à gauche."),
    ("往前", "wǎng qián", "go forward", "aller vers l'avant",
     "往前走三百米。", "Wǎng qián zǒu sānbǎi mǐ.", "Walk forward three hundred meters.", "Avance de trois cents mètres."),
    ("左转", "zuǒ zhuǎn", "turn left", "tourner à gauche",
     "在下一个路口左转。", "Zài xià yí gè lùkǒu zuǒ zhuǎn.", "Turn left at the next crossing.", "Au prochain carrefour, tourne à gauche."),
    ("右转", "yòu zhuǎn", "turn right", "tourner à droite",
     "在红绿灯右转。", "Zài hónglǜdēng yòu zhuǎn.", "Turn right at the traffic light.", "Au feu, tourne à droite."),
    ("十字路口", "shízì lùkǒu", "intersection; crossroads", "carrefour",
     "在十字路口往右走。", "Zài shízì lùkǒu wǎng yòu zǒu.", "At the intersection, go to the right.", "Au carrefour, va sur la droite."),
    ("路口", "lùkǒu", "junction; crossing", "croisement / carrefour",
     "前面第一个路口左转。", "Qiánmiàn dì yī gè lùkǒu zuǒ zhuǎn.", "At the first crossing ahead, turn left.", "Au premier croisement devant, tourne à gauche."),
]
draw_table_page("Directions", direction_rows)


pdf_path = Path("Chinese_notes_full_tables_fr.pdf").resolve()
print(f"PDF saved to: {pdf_path}")
print(f"File exists: {pdf_path.exists()}")
print(f"File size: {pdf_path.stat().st_size if pdf_path.exists() else 0} bytes")


c.save()
path
