from langchain.chains.query_constructor.base import AttributeInfo

metadata_field_info = [
    AttributeInfo(
        name="character",
        description="The character class the card belongs to. One of ['All', 'Ironclad', 'Silent', 'Defect', 'Watcher', 'Colorless', 'Status', 'Curse']",
        type="string",
    ),
    AttributeInfo(
        name="cost",
        description="The energy cost to play the card. This can be an integer, 'X' for variable cost cards, or null for unplayable cards like Curses.",
        type="string",
    ),
    AttributeInfo(
        name="rarity",
        description="The rarity of the card. One of ['Basic', 'Common', 'Uncommon', 'Rare', 'Special', 'Status', 'Curse']",
        type="string",
    ),
    AttributeInfo(
        name="type",
        description="The functional type of the card. One of ['Attack', 'Skill', 'Power', 'Status', 'Curse']",
        type="string",
    ),
    AttributeInfo(
        name="name",
        description="The unique name of the Slay the Spire card.",
        type="string",
    ),
]

document_content_description = (
    "The description of the cards from the game Slay the Spire."
)
