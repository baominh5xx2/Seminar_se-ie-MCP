"""
Migrate Bookings from Supabase (PostgreSQL) to FalkorDB
"""
import os
from dotenv import load_dotenv
from falkordb import FalkorDB
from supabase import create_client, Client
from datetime import datetime
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# FalkorDB configuration
FALKORDB_HOST = os.getenv("FALKORDB_HOST")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", 6379))
FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME")
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD")
FALKORDB_DATABASE = os.getenv("FALKORDB_DATABASE", "db2")
FALKORDB_SSL = os.getenv("FALKORDB_SSL", "false").lower() == "true"


def connect_supabase() -> Client:
    """Connect to Supabase"""
    print("🔌 Connecting to Supabase...")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase successfully!")
    return client


def connect_falkordb():
    """Connect to FalkorDB"""
    print("\n🔌 Connecting to FalkorDB...")
    db = FalkorDB(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        username=FALKORDB_USERNAME,
        password=FALKORDB_PASSWORD,
        ssl=FALKORDB_SSL
    )
    graph = db.select_graph(FALKORDB_DATABASE)
    print(f"✅ Connected to FalkorDB successfully!")
    print(f"📊 Database: {FALKORDB_DATABASE}")
    return graph


def fetch_all_bookings(supabase: Client) -> List[Dict[str, Any]]:
    """Fetch all bookings from Supabase"""
    print("\n" + "=" * 60)
    print("📥 Fetching bookings from Supabase...")
    print("=" * 60)
    
    try:
        # Fetch all bookings with related tour package info
        response = supabase.table("bookings")\
            .select("*, tour_packages(*)")\
            .execute()
        
        bookings = response.data if response.data else []
        print(f"✅ Found {len(bookings)} booking(s)")
        
        return bookings
        
    except Exception as e:
        print(f"❌ Error fetching bookings: {str(e)}")
        return []


def migrate_booking_to_falkordb(graph, booking: Dict[str, Any]) -> bool:
    """
    Migrate a single booking to FalkorDB
    Creates: User, TourPackage, Booking nodes and relationships
    """
    try:
        booking_id = booking['booking_id']
        package_id = booking['package_id']
        contact_phone = booking['contact_phone']
        contact_name = booking['contact_name']
        
        # Get tour package info
        package = booking.get('tour_packages', {})
        package_name = package.get('package_name', 'Unknown')
        destination = package.get('destination', 'Unknown')
        price = float(package.get('price', 0))
        duration_days = package.get('duration_days', 0)
        departure_location = package.get('departure_location', '')
        
        # Booking info
        number_of_people = booking['number_of_people']
        total_amount = float(booking['total_amount'])
        status = booking['status']
        special_requests = booking.get('special_requests', '')
        created_at = booking['created_at']
        
        # Cypher query to create/merge nodes and relationships
        query = """
        // Create or merge User node
        MERGE (u:User {phone: $phone})
        ON CREATE SET 
            u.name = $name,
            u.created_at = $timestamp
        
        // Create or merge TourPackage node
        MERGE (p:TourPackage {package_id: $package_id})
        ON CREATE SET
            p.name = $package_name,
            p.destination = $destination,
            p.price = $price,
            p.duration_days = $duration_days,
            p.departure_location = $departure_location
        
        // Create Booking node
        CREATE (b:Booking {
            booking_id: $booking_id,
            number_of_people: $number_of_people,
            total_amount: $total_amount,
            status: $status,
            special_requests: $special_requests,
            created_at: $created_at,
            travel_date: '',
            package_price: $price,
            contact_name: $name,
            contact_phone: $phone
        })
        
        // Create relationships
        CREATE (u)-[:MADE_BOOKING]->(b)
        CREATE (b)-[:FOR_PACKAGE]->(p)
        CREATE (u)-[:BOOKED {
            booking_date: $created_at,
            total_amount: $total_amount,
            status: $status
        }]->(p)
        
        RETURN b.booking_id as booking_id, u.phone as user_phone, p.name as package_name
        """
        
        params = {
            'phone': contact_phone,
            'name': contact_name,
            'booking_id': booking_id,
            'package_id': package_id,
            'package_name': package_name,
            'destination': destination,
            'price': price,
            'duration_days': duration_days,
            'departure_location': departure_location,
            'number_of_people': number_of_people,
            'total_amount': total_amount,
            'status': status,
            'special_requests': special_requests,
            'created_at': created_at,
            'timestamp': datetime.now().isoformat()
        }
        
        result = graph.query(query, params)
        
        if result.result_set:
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error migrating booking {booking.get('booking_id')}: {str(e)}")
        return False


def migrate_all_bookings(supabase: Client, graph):
    """Main migration function"""
    print("\n" + "=" * 60)
    print("🚀 Starting Booking Migration")
    print("=" * 60)
    
    # 1. Fetch all bookings
    bookings = fetch_all_bookings(supabase)
    
    if not bookings:
        print("\n⚠️  No bookings to migrate")
        return
    
    # 2. Migrate each booking
    print("\n" + "=" * 60)
    print("📤 Migrating bookings to FalkorDB...")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for idx, booking in enumerate(bookings, 1):
        booking_id = booking['booking_id']
        contact_name = booking['contact_name']
        package_name = booking.get('tour_packages', {}).get('package_name', 'Unknown')
        
        print(f"\n[{idx}/{len(bookings)}] Migrating booking {booking_id[:8]}...")
        print(f"   User: {contact_name}")
        print(f"   Package: {package_name}")
        
        if migrate_booking_to_falkordb(graph, booking):
            print(f"   ✅ Success")
            success_count += 1
        else:
            print(f"   ❌ Failed")
            failed_count += 1
    
    # 3. Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"✅ Successfully migrated: {success_count} booking(s)")
    print(f"❌ Failed: {failed_count} booking(s)")
    print(f"📈 Total: {len(bookings)} booking(s)")
    
    # 4. Verify in FalkorDB
    print("\n" + "=" * 60)
    print("🔍 Verifying Data in FalkorDB")
    print("=" * 60)
    
    try:
        # Count nodes
        user_count = graph.query("MATCH (u:User) RETURN count(u) as count")
        package_count = graph.query("MATCH (p:TourPackage) RETURN count(p) as count")
        booking_count = graph.query("MATCH (b:Booking) RETURN count(b) as count")
        
        print(f"👤 Total Users: {user_count.result_set[0][0]}")
        print(f"🎫 Total Tour Packages: {package_count.result_set[0][0]}")
        print(f"📋 Total Bookings: {booking_count.result_set[0][0]}")
        
        # Show sample data
        print("\n📝 Sample Bookings:")
        sample_query = """
        MATCH (u:User)-[:MADE_BOOKING]->(b:Booking)-[:FOR_PACKAGE]->(p:TourPackage)
        RETURN u.name, b.booking_id, p.name, b.total_amount, b.status
        LIMIT 5
        """
        sample_result = graph.query(sample_query)
        
        if sample_result.result_set:
            for idx, row in enumerate(sample_result.result_set, 1):
                print(f"   {idx}. {row[0]} - {row[2]}")
                print(f"      Booking ID: {row[1][:16]}...")
                print(f"      Amount: {row[3]:,.0f} VND")
                print(f"      Status: {row[4]}")
        
    except Exception as e:
        print(f"⚠️  Error verifying data: {str(e)}")


def show_graph_statistics(graph):
    """Show detailed graph statistics"""
    print("\n" + "=" * 60)
    print("📊 Detailed Graph Statistics")
    print("=" * 60)
    
    try:
        # Count relationships
        relationships_query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        """
        rel_result = graph.query(relationships_query)
        
        if rel_result.result_set:
            print("\n🔗 Relationships:")
            for row in rel_result.result_set:
                print(f"   {row[0]}: {row[1]}")
        
        # User booking statistics
        user_stats_query = """
        MATCH (u:User)-[:MADE_BOOKING]->(b:Booking)
        RETURN u.name, u.phone, count(b) as total_bookings, sum(b.total_amount) as total_spent
        ORDER BY total_bookings DESC
        LIMIT 10
        """
        user_stats = graph.query(user_stats_query)
        
        if user_stats.result_set:
            print("\n👥 Top Users by Bookings:")
            for idx, row in enumerate(user_stats.result_set, 1):
                print(f"   {idx}. {row[0]} ({row[1]})")
                print(f"      Bookings: {row[2]}, Total spent: {row[3]:,.0f} VND")
        
        # Popular packages
        package_stats_query = """
        MATCH (p:TourPackage)<-[:FOR_PACKAGE]-(b:Booking)
        RETURN p.name, p.destination, count(b) as booking_count, sum(b.total_amount) as revenue
        ORDER BY booking_count DESC
        LIMIT 5
        """
        package_stats = graph.query(package_stats_query)
        
        if package_stats.result_set:
            print("\n🎫 Most Booked Packages:")
            for idx, row in enumerate(package_stats.result_set, 1):
                print(f"   {idx}. {row[0]} ({row[1]})")
                print(f"      Bookings: {row[2]}, Revenue: {row[3]:,.0f} VND")
        
    except Exception as e:
        print(f"⚠️  Error getting statistics: {str(e)}")


def main():
    """Main execution"""
    print("\n" + "🌟" * 30)
    print("  BOOKING MIGRATION: Supabase → FalkorDB")
    print("🌟" * 30)
    
    try:
        # Connect to databases
        supabase = connect_supabase()
        graph = connect_falkordb()
        
        # Run migration
        migrate_all_bookings(supabase, graph)
        
        # Show statistics
        show_graph_statistics(graph)
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
