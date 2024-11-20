import nltk
from nltk.corpus import wordnet as wn
from itertools import product
import telethon
import tqdm
from sympy.physics.units import current
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.tl.functions.users import GetFullUserRequest
from config import APIs
from config import api_id
from config import api_hash
from time import time

import asyncio
from concurrent.futures import ThreadPoolExecutor

from check_names import check_available_usernames

isPremium = False
current_bot = 1


personal_words = [
]

replacements = {
    'a': ['4', '_'],
    'b': ['8'],
    'e': ['3'],
    'g': ['9'],
    'i': ['1'],
    'o': ['0', '_'],
    's': ['5'],
    'z': ['2'],
}

def get_related_words(word):
    related_words = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            related_words.add(lemma.name())
    return related_words

def generate_related_words(words):
    all_related_words = set(words)
    for word in words:
        related_words = get_related_words(word)
        all_related_words.update(related_words)
    return {word for word in all_related_words if len(word) <= 10}

def apply_replacements_with_case(word):
    positions = []
    for i, char in enumerate(word):
        variations = [char.lower(), char.upper()]
        if char.lower() in replacements:
            variations.extend(replacements[char.lower()])
        positions.append((i, variations))

    all_variations = set()
    for combo in product(*[pos[1] for pos in positions]):
        temp_word = list(word)
        changes = 0
        for (i, chars), new_char in zip(positions, combo):
            if temp_word[i] != new_char:
                if new_char == '_':
                    changes += 3
                else:
                    changes += 1
                temp_word[i] = new_char

        temp_word_str = ''.join(temp_word)
        if temp_word_str[-1] == '_':
            continue

        all_variations.add((''.join(temp_word), changes))

    return all_variations

def generate_all_variations(words):
    all_variations = set()
    for word in words:
        word_variations = apply_replacements_with_case(word)
        all_variations.update(word_variations)
    return all_variations

# related_words = generate_related_words(personal_words)

async def check_uname(username, client):
    try:
        entity = await client.get_entity(username)
        return False
    except telethon.errors.rpcerrorlist.UsernameInvalidError:
        return False
    except telethon.errors.rpcerrorlist.UsernameOccupiedError:
        return False
    except telethon.errors.rpcerrorlist.FloodWaitError:
        print("Flood")
        global current_bot
        current_bot+=1
        return False
    except Exception:
        return True



async def main(usernames, prem):
    isPremium = prem
    personal_words = usernames
    related_words = personal_words;
    variations_with_changes = generate_all_variations(related_words)

    usernames = [word for word, _ in sorted(variations_with_changes, key=lambda x: (len(x[0]), x[1]))]
    usernames = [username for username in usernames if len(username) >= 5 and username[0].isalpha()]
    client = TelegramClient(f'sessions/bot{current_bot}', api_id, api_hash)
    await client.connect()

    available_usernames = []
    free_usernames = []

    async with client:
        with ThreadPoolExecutor() as executor:
            for idx, username in enumerate(tqdm.tqdm(usernames)):
                is_free = await check_uname(username, client)
                if is_free:
                    available_usernames.append(username)
                if (isPremium and len(available_usernames) >= 50 or (idx == len(usernames)-1 and isPremium)):
                    free_usernames += await asyncio.get_event_loop().run_in_executor(
                        executor,
                        check_available_usernames,
                        available_usernames
                    )
                    available_usernames.clear()
                    if(len(free_usernames)>=25):
                        return free_usernames[:25]
                elif (isPremium == False and len(available_usernames) >= 10):
                    return available_usernames
    if(isPremium):
        return free_usernames
    return available_usernames

# if __name__ == '__main__':
#     print(asyncio.run(main(usernames)))
