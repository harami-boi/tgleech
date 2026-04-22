import os
import re
import glob

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all common emojis found in the source code
    # This regex specifically strips blocks of unicode associated with emojis and symbols
    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])|"  # flags (iOS)
        u"([\u2600-\u26FF])|"        # miscellaneous symbols
        u"([\u2700-\u27bf])|"        # dingbats
        u"([\u2300-\u23FF])|"        # technical symbols
        u"([\u2B50\u2B55])|"         # stars and circles
        u"([\u200D\uFE0F])"          # zero width joiners and variation selectors
        "+", flags=re.UNICODE)
    
    content = emoji_pattern.sub(r'', content)
    
    # Remove specific fancy borders and characters
    content = content.replace('╭⌬', '-').replace('├⌬', '-').replace('╰⌬', '-')
    content = content.replace('╭', '').replace('├', '').replace('╰', '')
    content = content.replace('⌬', '-').replace('»', ':').replace('◲', '-')
    
    # Clean up double spaces or weird formatting caused by removals
    content = content.replace('  ', ' ')
    content = content.replace(' :', ':')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

for f in glob.glob('colab_leecher/**/*.py', recursive=True):
    clean_file(f)

# Also clean main.py
if os.path.exists('main.py'):
    clean_file('main.py')

print("All emojis and fancy text removed successfully!")
