"""
MCP Tools - Booking Tools
Interactive booking collection và management
"""
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from datetime import datetime
import os
import threading
from dotenv import load_dotenv
from src.mcp_server.utils.falkordb_client import create_booking_in_falkordb, get_user_bookings_from_falkordb

load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def register_booking_tools(mcp: FastMCP):
    """Register booking-related tools"""
    
    @mcp.tool()
    async def create_user(
        user_phone: str,
        full_name: str,
        email: str
    ) -> Dict[str, Any]:
        """
        Tạo user mới trong hệ thống
        
        Args:
            user_phone: Số điện thoại user
            full_name: Tên đầy đủ của user
            email: Email của user 
            
        Returns:
            Thông tin user đã tạo
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Check if user already exists
            existing_user = supabase.table("users")\
                .select("*")\
                .eq("phone_number", user_phone)\
                .execute()
            
            if existing_user.data and len(existing_user.data) > 0:
                return {
                    "success": False,
                    "error": "Số điện thoại này đã được đăng ký trong hệ thống",
                    "user": existing_user.data[0]
                }
            
            # Create new user
            new_user = {
                "phone_number": user_phone,
                "full_name": full_name,
                "email": email
            }
            
            user_response = supabase.table("users").insert(new_user).execute()
            
            if not user_response.data:
                return {
                    "success": False,
                    "error": "Không thể tạo user profile"
                }
            
            return {
                "success": True,
                "message": "Tạo tài khoản thành công!",
                "user": user_response.data[0]
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    @mcp.tool()
    async def check_user_exists(user_phone: str) -> Dict[str, Any]:
        """
        Kiểm tra user có tồn tại trong hệ thống hay chưa
        
        QUAN TRỌNG: Tool này PHẢI được gọi ngay sau khi user cung cấp số điện thoại và TRƯỚC KHI hỏi thêm bất kỳ thông tin booking nào khác.
        
        Flow đúng:
        1. User cung cấp SĐT → Gọi tool này NGAY
        2. Nếu user_exists = false → Hỏi tên đầy đủ → Gọi create_user
        3. Nếu user_exists = true → Tiếp tục hỏi số người, ngày đi, etc.
        
        Args:
            user_phone: Số điện thoại cần kiểm tra
            
        Returns:
            Thông tin user nếu tồn tại, hoặc yêu cầu tạo user mới
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            user_response = supabase.table("users")\
                .select("*")\
                .eq("phone_number", user_phone)\
                .execute()
            
            if not user_response.data or len(user_response.data) == 0:
                return {
                    "success": True,
                    "user_exists": False,
                    "message": f"Số điện thoại {user_phone} chưa có trong hệ thống.",
                    "action_required": "Hỏi tên đầy đủ của khách hàng để tạo tài khoản.",
                    "next_step": "Sau khi có tên, gọi tool 'create_user' để tạo tài khoản trước khi tiếp tục đặt tour."
                }
            
            user = user_response.data[0]
            return {
                "success": True,
                "user_exists": True,
                "user": {
                    "user_id": user['user_id'],
                    "full_name": user['full_name'],
                    "phone_number": user['phone_number'],
                    "email": user.get('email')
                },
                "message": f"Chào mừng {user['full_name']}! Tài khoản đã tồn tại.",
                "next_step": "Tiếp tục thu thập thông tin booking (số người, ngày đi, yêu cầu đặc biệt)."
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi kiểm tra user: {str(e)}"
            }
    
    @mcp.tool()
    async def create_booking(
        user_phone: str,
        package_id: str,
        number_of_people: int,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tạo booking mới cho user
        
        ════════════════════════════════════════════════════════════════════
        📋 QUY TRÌNH ĐẶT TOUR (Flow tương tác với User)
        ════════════════════════════════════════════════════════════════════
        
        Bước 1️⃣: Hỏi SỐ ĐIỆN THOẠI
                → User cung cấp số điện thoại
        
        Bước 2️⃣: Kiểm tra User
                → Gọi tool 'check_user_exists(user_phone)'
                
                ↳ Nếu CHƯA CÓ tài khoản:
                  • Hỏi TÊN ĐẦY ĐỦ và EMAIL
                  • Gọi tool 'create_user(phone, name, email)'
                  
                ↳ Nếu ĐÃ CÓ tài khoản:
                  • Chào mừng user bằng tên
        
        Bước 3️⃣: Thu thập thông tin Booking
                • Số người tham gia
                • Yêu cầu đặc biệt (nếu có)
        
        Bước 4️⃣: Hiển thị bảng XÁC NHẬN
                → Chờ user CONFIRM
        
        Bước 5️⃣: Tạo Booking
                → Sau khi user confirm → Gọi tool này
        
        ════════════════════════════════════════════════════════════════════
        ⚙️ QUY TRÌNH XỬ LÝ (Internal Processing) - BẮT BUỘC THEO THỨ TỰ
        ════════════════════════════════════════════════════════════════════
        
        1️⃣. Verify user tồn tại trong database
        2️⃣. Lấy thông tin tour package
        3️⃣. Kiểm tra số chỗ còn trống
        4️⃣. Tính tổng tiền (price × number_of_people)
        5️⃣. TẠO BOOKING RECORD TRONG SUPABASE ← ĐẦU TIÊN
        6️⃣. Cập nhật available_slots của tour
        7️⃣. TRẢ THÔNG TIN CHO USER NGAY LẬP TỨC ← ƯU TIÊN CAO
        8️⃣. LƯU VÀO FALKORDB Ở BACKGROUND ← CUỐI CÙNG
        
        ════════════════════════════════════════════════════════════════════
        ⚠️ ĐIỀU KIỆN BẮT BUỘC
        ════════════════════════════════════════════════════════════════════
        
        ✓ User đã CONFIRM booking
        ✓ User đã tồn tại trong hệ thống
        ✓ Có đầy đủ thông tin: số người
        ✓ PHẢI lưu Supabase TRƯỚC, trả user NGAY, FalkorDB SAU
        
        ════════════════════════════════════════════════════════════════════
        
        Args:
            user_phone (str): Số điện thoại user (đã verified)
            package_id (str): ID của tour package
            number_of_people (int): Số người tham gia
            special_requests (str, optional): Yêu cầu đặc biệt
            
        Returns:
            Dict[str, Any]: {
                "success": bool,
                "booking_id": str,
                "message": str,
                "saved_to_falkordb": bool,
                "confirmation": {
                    "booking_id": str,
                    "user_name": str,
                    "user_phone": str,
                    "tour_name": str,
                    "destination": str,
                    "tour_dates": str,
                    "duration": str,
                    "number_of_people": int,
                    "total_amount": float,
                    "status": str,
                    "next_steps": list
                }
            }
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # 1️⃣. Verify user tồn tại trong database
            user_response = supabase.table("users")\
                .select("*")\
                .eq("phone_number", user_phone)\
                .execute()
            
            if not user_response.data or len(user_response.data) == 0:
                # User doesn't exist - return request for user creation
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": f"Số điện thoại {user_phone} chưa được đăng ký trong hệ thống.",
                    "action_required": "create_user",
                    "instruction": "Vui lòng hỏi tên đầy đủ của khách hàng và sử dụng tool 'create_user' để tạo tài khoản trước khi đặt tour."
                }
            
            user = user_response.data[0]
            
            # 2️⃣. Lấy thông tin tour package
            package_response = supabase.table("tour_packages")\
                .select("*")\
                .eq("package_id", package_id)\
                .eq("is_active", True)\
                .single()\
                .execute()
            
            if not package_response.data:
                return {
                    "success": False,
                    "error": f"Không tìm thấy tour package với ID: {package_id}"
                }
            
            package = package_response.data
            
            # 3️⃣. Kiểm tra số chỗ còn trống
            if package['available_slots'] < number_of_people:
                return {
                    "success": False,
                    "error": f"Tour chỉ còn {package['available_slots']} chỗ, không đủ cho {number_of_people} người"
                }
            
            # 4️⃣. Tính tổng tiền (price × number_of_people)
            total_amount = float(package['price']) * number_of_people
            
            # 5️⃣. TẠO BOOKING RECORD TRONG SUPABASE ← BƯỚC QUAN TRỌNG NHẤT
            booking_data = {
                "user_id": user['user_id'],
                "package_id": package_id,
                "number_of_people": number_of_people,
                "total_amount": total_amount,
                "contact_name": user.get('full_name', user_phone),
                "contact_phone": user_phone,
                "special_requests": special_requests,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            booking_response = supabase.table("bookings").insert(booking_data).execute()
            
            if not booking_response.data:
                return {
                    "success": False,
                    "error": "Không thể tạo booking"
                }
            
            booking = booking_response.data[0]
            
            # 6️⃣. Cập nhật available_slots của tour
            new_slots = package['available_slots'] - number_of_people
            supabase.table("tour_packages")\
                .update({"available_slots": new_slots})\
                .eq("package_id", package_id)\
                .execute()
            
            # 7️⃣. CHUẨN BỊ RESULT ĐỂ TRẢ VỀ USER NGAY LẬP TỨC
            result = {
                "success": True,
                "booking_id": booking['booking_id'],
                "message": "✅ ĐẶT TOUR THÀNH CÔNG!",
                "saved_to_falkordb": False,  # Chưa lưu FalkorDB lúc này
                "confirmation": {
                    "booking_id": booking['booking_id'],
                    "user_name": user['full_name'],
                    "user_phone": user['phone_number'],
                    "tour_name": package['package_name'],
                    "destination": package['destination'],
                    "tour_dates": f"{package['start_date']} đến {package['end_date']}",
                    "duration": f"{package['duration_days']} ngày {package['duration_days']-1} đêm",
                    "number_of_people": number_of_people,
                    "total_amount": total_amount,
                    "contact_name": booking['contact_name'],
                    "contact_phone": booking['contact_phone'],
                    "special_requests": special_requests or "Không có",
                    "status": "Đang chờ xác nhận",
                    "next_steps": [
                        "Chúng tôi sẽ liên hệ với bạn qua số điện thoại đã cung cấp trong vòng 24h",
                        "Vui lòng chuẩn bị thanh toán cọc 30% tổng giá trị tour",
                        "Còn lại 70% sẽ thanh toán trước ngày khởi hành 3 ngày"
                    ]
                }
            }
            
            # 8️⃣. LƯU VÀO FALKORDB Ở BACKGROUND THREAD (KHÔNG BLOCK RESPONSE)
            def save_to_falkordb_background():
                """Background task để lưu booking vào FalkorDB - KHÔNG ẢNH HƯỞNG ĐẾN RESPONSE"""
                try:
                    print(f"🔄 [Background] Bắt đầu lưu booking {booking['booking_id']} vào FalkorDB...")
                    
                    user_email = user.get('email', '') or ''
                    
                    falkordb_result = create_booking_in_falkordb(
                        booking_id=str(booking['booking_id']),
                        user_name=user.get('full_name', ''),
                        user_phone=user.get('phone_number', user_phone),
                        user_email=user_email,
                        package_id=package_id,
                        package_name=package['package_name'],
                        destination=package['destination'],
                        number_of_people=number_of_people,
                        total_amount=total_amount,
                        travel_date='',  # Có thể để trống hoặc lấy từ package
                        package_price=float(package['price']),
                        duration_days=package['duration_days'],
                        departure_location=package['departure_location'],
                        status=booking.get('status', 'pending'),
                        special_requests=special_requests or '',
                        contact_name=booking.get('contact_name', ''),
                        contact_phone=booking.get('contact_phone', user_phone)
                    )
                    
                    if falkordb_result.get('success'):
                        print(f"✅ [Background] Successfully saved booking {booking['booking_id']} to FalkorDB")
                    else:
                        print(f"⚠️ [Background] Failed to save to FalkorDB: {falkordb_result.get('error')}")
                        
                except Exception as e:
                    print(f"⚠️ [Background] Exception while saving to FalkorDB: {str(e)}")
            
            # 🚀 KHỞI ĐỘNG BACKGROUND THREAD - KHÔNG CHỜ ĐỢI
            falkordb_thread = threading.Thread(target=save_to_falkordb_background, daemon=True)
            falkordb_thread.start()
            
            # 🎯 TRẢ VỀ USER NGAY LẬP TỨC - KHÔNG CHỜ FALKORDB
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    @mcp.tool()
    async def get_user_bookings(user_phone: str) -> Dict[str, Any]:
        """
        Lấy danh sách bookings của user theo số điện thoại
        
        Args:
            phone_number: Số điện thoại của user
            
        Returns:
            Danh sách bookings với thông tin tour
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # 1. Get user by phone
            user_response = supabase.table("users")\
                .select("user_id, full_name")\
                .eq("phone_number", user_phone)\
                .execute()
            
            if not user_response.data or len(user_response.data) == 0:
                return {
                    "success": False,
                    "error": f"Không tìm thấy user với số điện thoại: {user_phone}",
                    "suggestion": "Bạn chưa có booking nào trong hệ thống"
                }
            
            user = user_response.data[0]
            
            # 2. Get bookings by user_id
            bookings_response = supabase.table("bookings")\
                .select("*, tour_packages(*)")\
                .eq("user_id", user['user_id'])\
                .order("created_at", desc=True)\
                .execute()
            
            bookings = bookings_response.data if bookings_response.data else []
            
            return {
                "success": True,
                "user_name": user['full_name'],
                "user_phone": user_phone,
                "total": len(bookings),
                "bookings": bookings
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    # @mcp.tool()
    # async def search_available_tours(
    #     destination: Optional[str] = None,
    #     max_price: Optional[float] = None,
    #     duration_days: Optional[int] = None
    # ) -> Dict[str, Any]:
    #     """
    #     Tìm kiếm tour packages có sẵn
    #     
    #     Args:
    #         destination: Điểm đến (optional)
    #         max_price: Giá tối đa (optional)
    #         duration_days: Số ngày (optional)
    #         
    #     Returns:
    #         Danh sách tour packages
    #     """
    #     try:
    #         supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    #         
    #         query = supabase.table("tour_packages")\
    #             .select("*")\
    #             .eq("is_active", True)
    #         
    #         if destination:
    #             query = query.ilike("destination", f"%{destination}%")
    #         
    #         if max_price:
    #             query = query.lte("price", max_price)
    #         
    #         if duration_days:
    #             query = query.eq("duration_days", duration_days)
    #         
    #         response = query.execute()
    #         tours = response.data if response.data else []
    #         
    #         return {
    #             "success": True,
    #             "total": len(tours),
    #             "tours": tours
    #         }
    #     
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": f"Lỗi: {str(e)}"
    #         }
    
    # @mcp.tool()
    # async def get_booking_details(booking_id: str) -> Dict[str, Any]:
    #     """
    #     Lấy chi tiết booking
    #     
    #     Args:
    #         booking_id: ID của booking
    #         
    #     Returns:
    #         Chi tiết booking
    #     """
    #     try:
    #         supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    #         
    #         response = supabase.table("bookings")\
    #             .select("*, tour_packages(*), users(*)")\
    #             .eq("booking_id", booking_id)\
    #             .single()\
    #             .execute()
    #         
    #         if response.data:
    #             return {
    #                 "success": True,
    #                 "booking": response.data
    #             }
    #         else:
    #             return {
    #                 "success": False,
    #                 "error": "Không tìm thấy booking"
    #             }
    #     
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": f"Lỗi: {str(e)}"
    #         }
    
    @mcp.tool()
    async def update_booking_status(
        booking_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Cập nhật trạng thái booking
        
        Args:
            booking_id: ID của booking
            status: Trạng thái mới (pending, confirmed, cancelled, completed)
            
        Returns:
            Kết quả cập nhật
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            response = supabase.table("bookings")\
                .update({
                    "status": status,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("booking_id", booking_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "message": f"Đã cập nhật trạng thái thành: {status}",
                    "booking": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Không thể cập nhật booking"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    @mcp.tool()
    async def view_booking_in_falkordb(booking_id: str) -> Dict[str, Any]:
        """
        Xem chi tiết booking từ FalkorDB graph database
        
        Args:
            booking_id: ID của booking cần xem
            
        Returns:
            Thông tin chi tiết booking từ graph database
        """
        try:
            from src.mcp_server.utils.falkordb_client import get_falkordb_graph
            
            graph = get_falkordb_graph()
            
            # Query để lấy thông tin booking với các relationships
            query = f"""
            MATCH (u:User)-[:MADE_BOOKING]->(b:Booking)-[:FOR_PACKAGE]->(p:TourPackage)
            WHERE b.booking_id = '{booking_id}'
            RETURN 
                u.name as user_name,
                u.phone as user_phone,
                b.booking_id as booking_id,
                b.number_of_people as number_of_people,
                b.total_amount as total_amount,
                b.travel_date as travel_date,
                b.status as status,
                b.special_requests as special_requests,
                b.contact_name as contact_name,
                b.contact_phone as contact_phone,
                b.created_at as created_at,
                b.package_price as package_price,
                p.package_id as package_id,
                p.name as package_name,
                p.price as package_price,
                p.duration_days as duration_days,
                p.destination as destination,
                p.departure_location as departure_location
            """
            
            result = graph.query(query)
            
            if not result.result_set or len(result.result_set) == 0:
                return {
                    "success": False,
                    "error": f"Không tìm thấy booking {booking_id} trong FalkorDB",
                    "suggestion": "Booking có thể chưa được đồng bộ vào graph database"
                }
            
            row = result.result_set[0]
            
            return {
                "success": True,
                "booking": {
                    "booking_id": row[2],
                    "user": {
                        "name": row[0],
                        "phone": row[1]
                    },
                    "tour": {
                        "package_id": row[12],
                        "name": row[13],
                        "destination": row[16] if row[16] else "N/A",
                        "departure_location": row[17] if row[17] else "N/A",
                        "price_per_person": row[14],
                        "duration_days": row[15]
                    },
                    "booking_details": {
                        "number_of_people": row[3],
                        "total_amount": row[4],
                        "travel_date": row[5],
                        "status": row[6],
                        "special_requests": row[7],
                        "contact_name": row[8],
                        "contact_phone": row[9],
                        "package_price": row[11]
                    },
                    "timestamps": {
                        "created_at": row[10]
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi truy vấn FalkorDB: {str(e)}"
            }
    
    @mcp.tool()
    async def get_falkordb_statistics() -> Dict[str, Any]:
        """
        Lấy thống kê tổng quan từ FalkorDB graph database
        
        Returns:
            Thống kê về Users, Bookings, TourPackages và các relationships
        """
        try:
            from src.mcp_server.utils.falkordb_client import get_falkordb_graph
            
            graph = get_falkordb_graph()
            
            # Count nodes
            users_count = graph.query("MATCH (u:User) RETURN count(u) as count")
            bookings_count = graph.query("MATCH (b:Booking) RETURN count(b) as count")
            packages_count = graph.query("MATCH (p:TourPackage) RETURN count(p) as count")
            destinations_count = graph.query("MATCH (d:Destination) RETURN count(d) as count")
            
            # Count by status
            status_query = """
            MATCH (b:Booking)
            RETURN b.status as status, count(b) as count
            """
            status_result = graph.query(status_query)
            
            status_breakdown = {}
            if status_result.result_set:
                for row in status_result.result_set:
                    status_breakdown[row[0]] = row[1]
            
            # Top packages
            top_packages_query = """
            MATCH (p:TourPackage)<-[:FOR_PACKAGE]-(b:Booking)
            RETURN p.name as package_name, count(b) as booking_count, sum(b.total_amount) as revenue
            ORDER BY booking_count DESC
            LIMIT 5
            """
            top_packages_result = graph.query(top_packages_query)
            
            top_packages = []
            if top_packages_result.result_set:
                for row in top_packages_result.result_set:
                    top_packages.append({
                        "package_name": row[0],
                        "booking_count": row[1],
                        "revenue": row[2]
                    })
            
            # Recent bookings
            recent_query = """
            MATCH (u:User)-[:MADE_BOOKING]->(b:Booking)-[:FOR_PACKAGE]->(p:TourPackage)
            RETURN u.name, b.booking_id, p.name, b.total_amount, b.status, b.created_at
            ORDER BY b.created_at DESC
            LIMIT 5
            """
            recent_result = graph.query(recent_query)
            
            recent_bookings = []
            if recent_result.result_set:
                for row in recent_result.result_set:
                    recent_bookings.append({
                        "user_name": row[0],
                        "booking_id": row[1],
                        "package_name": row[2],
                        "total_amount": row[3],
                        "status": row[4],
                        "created_at": row[5]
                    })
            
            return {
                "success": True,
                "statistics": {
                    "total_counts": {
                        "users": users_count.result_set[0][0] if users_count.result_set else 0,
                        "bookings": bookings_count.result_set[0][0] if bookings_count.result_set else 0,
                        "tour_packages": packages_count.result_set[0][0] if packages_count.result_set else 0,
                        "destinations": destinations_count.result_set[0][0] if destinations_count.result_set else 0
                    },
                    "booking_status_breakdown": status_breakdown,
                    "top_packages": top_packages,
                    "recent_bookings": recent_bookings
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi lấy thống kê: {str(e)}"
            }
    
    @mcp.tool()
    async def search_bookings_in_falkordb(
        user_phone: Optional[str] = None,
        status: Optional[str] = None,
        package_name: Optional[str] = None,
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tìm kiếm bookings trong FalkorDB theo nhiều tiêu chí
        
        Args:
            user_phone: Số điện thoại user (optional)
            status: Trạng thái booking (optional)
            package_name: Tên tour package (optional)
            destination: Điểm đến (optional)
            
        Returns:
            Danh sách bookings phù hợp với tiêu chí tìm kiếm
        """
        try:
            from src.mcp_server.utils.falkordb_client import get_falkordb_graph
            
            graph = get_falkordb_graph()
            
            # Build query dynamically based on filters
            where_clauses = []
            
            if user_phone:
                where_clauses.append(f"u.phone = '{user_phone}'")
            
            if status:
                where_clauses.append(f"b.status = '{status}'")
            
            if package_name:
                where_clauses.append(f"p.name CONTAINS '{package_name}'")
            
            if destination:
                where_clauses.append(f"p.destination CONTAINS '{destination}'")
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
            MATCH (u:User)-[:MADE_BOOKING]->(b:Booking)-[:FOR_PACKAGE]->(p:TourPackage)
            WHERE {where_clause}
            RETURN 
                u.name as user_name,
                u.phone as user_phone,
                b.booking_id as booking_id,
                b.number_of_people as number_of_people,
                b.total_amount as total_amount,
                b.status as status,
                p.name as package_name,
                p.destination as destination,
                b.created_at as created_at
            ORDER BY b.created_at DESC
            LIMIT 50
            """
            
            result = graph.query(query)
            
            bookings = []
            if result.result_set:
                for row in result.result_set:
                    bookings.append({
                        "user_name": row[0],
                        "user_phone": row[1],
                        "booking_id": row[2],
                        "number_of_people": row[3],
                        "total_amount": row[4],
                        "status": row[5],
                        "package_name": row[6],
                        "destination": row[7] if row[7] else "N/A",
                        "created_at": row[8]
                    })
            
            return {
                "success": True,
                "count": len(bookings),
                "bookings": bookings,
                "filters_applied": {
                    "user_phone": user_phone,
                    "status": status,
                    "package_name": package_name,
                    "destination": destination
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi tìm kiếm: {str(e)}"
            }
