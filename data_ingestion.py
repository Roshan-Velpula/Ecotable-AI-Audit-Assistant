import os
import psycopg2
import io


from dotenv import load_dotenv

# Set the current working directory to the script's directory
script_dir = os.path.dirname(__file__)
os.chdir(script_dir)

env_loaded = load_dotenv()
print("Environment loaded:", env_loaded)

NEON_DB = os.getenv('NEON_DB')

csv_file_path = os.path.join('data','data_with_embeddings.csv' )

def connect_db():
    connection = psycopg2.connect(NEON_DB)
    return connection, connection.cursor()

# Function to check if a table exists
def table_exists(cursor, table_name):
    check_table_sql = f'''
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name = '{table_name}'
    );
    '''
    cursor.execute(check_table_sql)
    return cursor.fetchone()[0]

# Function to create the table if it doesn't exist
def create_table_if_not_exists(cursor, connection):
    if not table_exists(cursor, 'viande_fromage'):
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS public.viande_fromage (
            id INTEGER NOT NULL,
            Categorie TEXT,
            AOP TEXT,
            content TEXT,
            content_vector vector(1024),
            durable TEXT
        );

        ALTER TABLE public.viande_fromage ADD PRIMARY KEY (id);
        '''
        cursor.execute(create_table_sql)
        connection.commit()
        
def process_file(csv_file_path):
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            yield line

def load_csv_to_db(cursor, connection, csv_file_path):
    modified_lines = io.StringIO(''.join(list(process_file(csv_file_path))))
    copy_command = '''
    COPY public.viande_fromage (id, Categorie, AOP, content, content_vector, durable)
    FROM STDIN WITH (FORMAT CSV, HEADER true, DELIMITER ',');
    '''
    
    cursor.copy_expert(copy_command, modified_lines)
    connection.commit()
    
        

