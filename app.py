from pprint import pp
from db_function import get_postgres_connection
from ai_solution import match_categories
from tqdm import tqdm

def get_company_profile(user_id: int):
    conn = get_postgres_connection("system")
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT company_profile, product_description
            FROM user_config uc
            LEFT JOIN users u ON uc.user_id = u.id
            WHERE uc.user_id = %s;
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    conn.close()
    return (row["company_profile"], row["product_description"]) if row else (None, None)


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

def get_users_and_rule_list(categories):
    conn = get_postgres_connection('system')
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                u.id,
                COALESCE(rl.categories_whitelist, '{}'::int[]) AS categories_whitelist
            FROM users u
            LEFT JOIN rule_list rl ON u.id = rl.user_id
            LEFT JOIN user_config uc ON u.id = uc.user_id
            WHERE u.is_active = TRUE 
                AND whitelist_ai = TRUE
                AND uc.company_profile IS NOT NULL;
            """)
        rows = cursor.fetchall()
    conn.close()
    for row in rows:
        row['categories_whitelist'] = [(cat['id'], cat['pl']) for cat in categories if cat['id'] in row['categories_whitelist']]
    return rows


if __name__ == "__main__":
    batch_size = 200
    
    try:
        while True:
            all_categories = get_categories()
            users = get_users_and_rule_list(all_categories)
            
            for user in users:
                user_id = user['id']
                print(f"Processing user_id: {user_id}")
                company_profile, product_description = get_company_profile(user_id)
                print(f"Company profile: {company_profile}")
                print(f"Product description: {product_description}")
                
                new_categories = set()
                
                # ID kategorii już przypisanych temu userowi
                whitelist_ids = {cid for cid, _ in user['categories_whitelist']}
                
                #  wywal z batcha kategorie, które już są w whitelist
                categories = [row for row in all_categories if row['id'] not in whitelist_ids]
                
                for i in tqdm(range(0, len(categories), batch_size)):
                    batch_rows = categories[i:i + batch_size]
                    
                    batch = [(row['id'], row['pl']) for row in batch_rows]
                    
                    matched_categories = match_categories(
                        company_profile, 
                        product_description,
                        batch, 
                        user['categories_whitelist']
                        )
                    
                    new_categories.update(matched_categories)
                
                pp(f"Matched categories for user {user_id}: {new_categories}")    
                exit()
            
    except Exception as e:
        print(f"[ERROR]: {e}")
    
    for i in range(0, len(categories), batch_size):
        batch = categories[i:i + batch_size]
        
    