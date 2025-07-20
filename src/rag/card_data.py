from langchain_core.documents import Document

def get_card_data():
    return [
        Document(
            page_content="Deal 6 damage. || Upgraded: Deal 9 damage.",
            metadata={"name": "Strike", "character": "All", "cost": 1, "rarity": "Basic", "type": "Attack"},
        ),
        Document(
            page_content="Gain 5 Block. || Upgraded: Gain 8 Block.",
            metadata={"name": "Defend", "character": "All", "cost": 1, "rarity": "Basic", "type": "Skill"},
        ),
        Document(
            page_content="Deal 8 damage. Apply 2 Vulnerable. || Upgraded: Deal 10 damage. Apply 3 Vulnerable.",
            metadata={"name": "Bash", "character": "Ironclad", "cost": 2, "rarity": "Basic", "type": "Attack"},
        ),
        Document(
            page_content="Deal 3 damage. Apply 1 Weak. || Upgraded: Deal 4 damage. Apply 2 Weak.",
            metadata={"name": "Neutralize", "character": "Silent", "cost": 0, "rarity": "Basic", "type": "Attack"},
        ),
        Document(
            page_content="Gain 8 Block. Discard 1 card. || Upgraded: Gain 11 Block. Discard 1 card.",
            metadata={"name": "Survivor", "character": "Silent", "cost": 1, "rarity": "Basic", "type": "Skill"},
        ),
        Document(
            page_content="Channel 1 Lightning. || Upgraded: Channel 1 Lightning. Costs 0.",
            metadata={"name": "Zap", "character": "Defect", "cost": 1, "rarity": "Basic", "type": "Skill"},
        ),
        Document(
            page_content="Evoke your next Orb. || Upgraded: Evoke your next Orb twice.",
            metadata={"name": "Dualcast", "character": "Defect", "cost": 1, "rarity": "Basic", "type": "Skill"},
        ),
        Document(
            page_content="Deal 9 damage. Enter Wrath. || Upgraded: Costs 1. Deal 9 damage. Enter Wrath.",
            metadata={"name": "Eruption", "character": "Watcher", "cost": 2, "rarity": "Basic", "type": "Attack"},
        ),
        Document(
            page_content="Enter Calm. Gain 8 Block. || Upgraded: Enter Calm. Gain 12 Block.",
            metadata={"name": "Vigilance", "character": "Watcher", "cost": 2, "rarity": "Basic", "type": "Skill"},
        ),
    ]

CARD_DATA = get_card_data() 