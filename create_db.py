import os
import mysql.connector
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def create_database():
    try:
        mydb = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "admin"),
            password=os.environ.get("DB_PASSWORD", ""),
            port=int(os.environ.get("DB_PORT", 3306))
        )
        db_name = os.environ.get("DB_NAME", "isms1")
        cursor = mydb.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        print(f"✅ Database '{db_name}' created/verified successfully!")
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
        print("\nCould not connect. Please check your .env file for DB credentials.")

if __name__ == "__main__":
    create_database()
