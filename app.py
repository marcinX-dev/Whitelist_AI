from pprint import pp
from db_function import get_postgres_connection
from ai_solution import match_categories
from tqdm import tqdm

def get_company_profile(user_id: int):
    conn = get_postgres_connection("system")
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT company_profile
            FROM user_config
            WHERE user_id = %s;
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    conn.close()
    return row["company_profile"] if row else None


def get_categories():
    conn = get_postgres_connection('system')
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, pl 
            FROM categories 
            ORDER BY id;
            """)
        rows = cursor.fetchall()
    conn.close()
    return rows

def get_users():
    conn = get_postgres_connection('system')
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id 
            FROM users u
            LEFT JOIN user_config uc ON u.id = uc.user_id
            WHERE u.is_active = TRUE 
                AND whitelist_ai = TRUE
                AND uc.company_profile IS NOT NULL;
            """)
        rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    batch_size = 200
    
    try:
        while True:
            categories = get_categories()
            users = get_users()
            
            for user in users:
                user_id = user['id']
                print(f"Processing user_id: {user_id}")
                company_profile = get_company_profile(user_id)
                print(f"Company profile: {company_profile}")
                
                new_categories = set()
                
                for i in tqdm(range(0, len(categories), batch_size)):
                    batch = categories[i:i + batch_size]
                    matched_categories = match_categories(company_profile, batch)
                    new_categories.update(matched_categories)
                
                pp(f"Matched categories for user {user_id}: {new_categories}")    
                exit()
            
    except Exception as e:
        print(f"[ERROR]: {e}")
    
    for i in range(0, len(categories), batch_size):
        batch = categories[i:i + batch_size]
        
    