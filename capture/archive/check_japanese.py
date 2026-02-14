import sqlite3

db = sqlite3.connect('instance/chinese_vocab.db')
cursor = db.cursor()

# Get sample of translated items
cursor.execute('SELECT hanzi, japanese_kanji, japanese_romaji FROM vocabulary WHERE japanese_kanji != "" AND japanese_kanji IS NOT NULL LIMIT 10')
results = cursor.fetchall()

print(f'Sample of translated items:')
for r in results:
    print(f'  {r[0]} -> {r[1]} ({r[2]})')

# Get count
cursor.execute('SELECT COUNT(*) FROM vocabulary WHERE japanese_kanji != "" AND japanese_kanji IS NOT NULL')
count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM vocabulary')
total = cursor.fetchone()[0]

print(f'\nTotal translated: {count}/{total}')
