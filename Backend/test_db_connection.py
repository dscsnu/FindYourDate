"""
Test database connection and provide troubleshooting info.
"""

from dotenv import load_dotenv
import os
import socket

load_dotenv()

def test_connection():
    db_url = os.getenv('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found in .env file")
        return False
    
    print("🔍 Checking database connection...")
    print(f"Database URL: {db_url[:50]}...")
    
    # Extract hostname from URL
    # Format: postgresql://user:pass@hostname:port/dbname
    try:
        parts = db_url.split('@')[1].split(':')[0]
        hostname = parts
        print(f"\n📡 Testing DNS resolution for: {hostname}")
        
        # Test DNS resolution
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ DNS resolution successful: {ip}")
        except socket.gaierror:
            print(f"❌ DNS resolution failed for {hostname}")
            print("\n💡 Possible solutions:")
            print("   1. Check your internet connection")
            print("   2. Your Supabase project might be paused or deleted")
            print("   3. Get a fresh connection string from Supabase dashboard:")
            print("      https://supabase.com/dashboard/project/_/settings/database")
            print("\n   Try using the CONNECTION POOLER string instead of direct connection")
            print("   Look for: 'Connection pooler' or 'Transaction' mode")
            return False
        
        # Try to connect to database
        print("\n🔌 Testing database connection...")
        from sqlalchemy import create_engine
        
        try:
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
            with engine.connect() as conn:
                result = conn.execute("SELECT version()")
                version = result.fetchone()[0]
                print(f"✅ Connected successfully!")
                print(f"PostgreSQL version: {version[:50]}...")
                
                # Check tables
                from sqlalchemy import inspect
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f"\n📊 Tables in database: {tables if tables else 'None (empty database)'}")
                
                if not tables:
                    print("\n💡 Database is empty. You need to create tables:")
                    print("   Option 1: alembic upgrade head")
                    print("   Option 2: python3 create_tables.py")
                
                return True
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\n💡 Possible solutions:")
            print("   1. Verify your password in the connection string")
            print("   2. Check if your Supabase project is active")
            print("   3. Try using the CONNECTION POOLER URL (port 6543)")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing database URL: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  DATABASE CONNECTION TEST")
    print("=" * 60)
    test_connection()
    print("=" * 60)
