from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI

from db_function import get_api_key

OPENAI_API_KEY = get_api_key('OPENAI_API_KEY')

class CategoryCandidate(BaseModel):
    id: int
    pl: str
    confidence: float = Field(ge=0.0, le=1.0)


class CategoryMatches(BaseModel):
    matches: List[CategoryCandidate] = []


def match_categories(description: str, categories: list[tuple[int, str]]) -> CategoryMatches:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    confidence_threshold = 0.7
    system_prompt = (
        "Dopasuj WSZYSTKIE kategorie pasujące do opisu.\n"
        "Dostajesz listę kategorii (id + nazwa PL).\n"
        "Zwróć tylko te, które realnie pasują.\n"
        "Jeśli żadna nie pasuje → zwróć pustą listę matches: [].\n"
        "Nie wymyślaj nowych kategorii.\n"
        "Nie zgaduj — jeśli niska pewność, nie dodawaj kategorii."
    )

    categories_text = "\n".join([f"{cid}: {cpl}" for cid, cpl in categories])

    response = openai_client.responses.parse(
        model="gpt-5.1-2025-11-13",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"OPIS:\n{description}\n\nKATEGORIE:\n{categories_text}"},
        ],
        service_tier="flex",
        text_format=CategoryMatches,
    )

    result: CategoryMatches = response.output_parsed

    # zabezpieczenie: wyrzucamy ID spoza listy
    valid = {cid: cpl for cid, cpl in categories}
    result.matches = [
        # CategoryCandidate(id=m.id, pl=valid[m.id], confidence=m.confidence)
        m.id
        for m in result.matches
        if m.id in valid and m.confidence >= confidence_threshold
    ]

    return result.matches