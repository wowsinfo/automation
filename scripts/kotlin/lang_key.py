"""
Build the language key for the Kotlin language.
"""

import json

def build_key(json_path: str):
    """
    Build the language key for the Kotlin language.
    """
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    keys = []
    TO_REMOTE = ["(", ")", "/", "."]
    for lang in data["en"]:
        content = data["en"][lang]
        processed_key = lang.replace("IDS_", "")
        keys.append(processed_key)
        continue

        if len(content) > 1 and len(content) < len(processed_key):
            processed_key = "_".join(content.split(" ")).upper()
        
        for char in TO_REMOTE:
            processed_key = processed_key.replace(char, "")
        processed_key = processed_key.replace("__", "_")
        keys.append(processed_key)
    keys.sort()
    return keys

if __name__ == "__main__":
    key = build_key("temp\\lang.json")
    
    # 15401 keys, have to be shrinked for the mobile app
    print(len(key))