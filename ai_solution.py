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


def match_categories(company_profile: str, product_description: str, categories: list[tuple[int, str]], whitelist: list[tuple[int, str]]) -> CategoryMatches:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    confidence_threshold = 0.7
    system_prompt = (
        "Dopasuj WSZYSTKIE kategorie pasujące do opisu.\n"
        "Dostajesz listę kategorii (id + nazwa PL).\n"
        "Zwróć tylko te, które realnie pasują.\n"
        "Jeśli żadna nie pasuje → zwróć pustą listę matches: [].\n"
        "Nie wymyślaj nowych kategorii.\n"
        "Nie zgaduj — jeśli niska pewność, nie dodawaj kategorii."
        "Jeśli dostaniesz listę 'JUŻ WYBRANE (wzorzec)' — wzoruj się na niej i dobieraj spójne kategorie."
    )

    categories_text = "\n".join([f"{cid}: {cpl}" for cid, cpl in categories])
    
    whitelist_text = "\n".join([f"{cid}: {cpl}" for cid, cpl in whitelist])
    if whitelist:
        system_prompt += (
            "\n\nJUŻ WYBRANE (wzorzec):\n"
            f"{whitelist_text}\n"
            "Dobierz do nich podobne kategorie."
        )
    
    response = openai_client.responses.parse(
        model="gpt-5.1-2025-11-13",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""OPIS:\n
                                        Profil firmy: {company_profile}\n
                                        Opis produktu: {product_description}\n\n
                                        KATEGORIE:\n{categories_text}"""},
        ],
        service_tier="flex",
        text_format=CategoryMatches,
    )
    
    result: CategoryMatches = response.output_parsed

    # zabezpieczenie: wyrzucamy ID spoza listy
    valid = {cid: cpl for cid, cpl in categories}
    whitelist_ids = {cid for cid, _ in whitelist}
    
    result.matches = [
        m.id
        for m in result.matches
        if m.id in valid 
        and m.confidence >= confidence_threshold
        and m.id not in whitelist_ids
    ]

    return result.matches