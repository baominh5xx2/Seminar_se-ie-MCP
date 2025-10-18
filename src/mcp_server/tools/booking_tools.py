"""
MCP Tools - Booking Tools
Interactive booking collection và management
"""
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from datetime import datetime
import os
from dotenv import load_dotenv

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
        travel_date: str,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tạo booking mới cho user
        
        QUY TRÌNH ĐẶT TOUR ĐÚNG:
        Bước 1: User muốn đặt tour → Hỏi SỐ ĐIỆN THOẠI
        Bước 2: Gọi tool 'check_user_exists' với số điện thoại
        Bước 3a: Nếu user_exists = false:
            - Hỏi TÊN ĐẦY ĐỦ và Email của khách hàng
            - Gọi 'create_user' để tạo tài khoản
        Bước 3b: Nếu user_exists = true:
            - Chào mừng user (hiển thị tên)
        Bước 4: Thu thập thông tin booking:
            - Số người tham gia
            - Ngày khởi hành
            - Yêu cầu đặc biệt (nếu có)
        Bước 5: Hiển thị bảng xác nhận đầy đủ, đợi user CONFIRM
        Bước 6: Sau khi user confirm → Gọi tool này để tạo booking
        
        QUAN TRỌNG: 
        - Tool này CHỈ được gọi SAU KHI user đã CONFIRM booking
        - User PHẢI đã tồn tại trong hệ thống (đã qua check_user_exists và create_user nếu cần)
        - ĐÃ có đầy đủ thông tin: số người, ngày đi
        
        Args:
            user_phone: Số điện thoại user (đã verified tồn tại)
            package_id: ID của tour package
            number_of_people: Số người tham gia
            travel_date: Ngày khởi hành (YYYY-MM-DD)
            special_requests: Yêu cầu đặc biệt (optional)
            
        Returns:
            Booking confirmation, booking_id thông tin cơ bản của user (full_name, phone_number) và chi tiết đầy đủ
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # 1. Check if user exists
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
            
            # 2. Get package info
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
            
            # 3. Check available slots
            if package['available_slots'] < number_of_people:
                return {
                    "success": False,
                    "error": f"Tour chỉ còn {package['available_slots']} chỗ, không đủ cho {number_of_people} người"
                }
            
            # 4. Calculate total amount
            total_amount = float(package['price']) * number_of_people
            
            # 5. Create booking
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
            
            # 6. Update available slots
            new_slots = package['available_slots'] - number_of_people
            supabase.table("tour_packages")\
                .update({"available_slots": new_slots})\
                .eq("package_id", package_id)\
                .execute()
            
            # 7. Return success with full details
            return {
                "success": True,
                "booking_id": booking['booking_id'],
                "message": "✅ ĐẶT TOUR THÀNH CÔNG!",
                "confirmation": {
                    "booking_id": booking['booking_id'],
                    "user_name": user['full_name'],
                    "user_phone": user['phone_number'],
                    "tour_name": package['package_name'],
                    "destination": package['destination'],
                    "travel_date": travel_date,
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
        
    #     Args:
    #         destination: Điểm đến (optional)
    #         max_price: Giá tối đa (optional)
    #         duration_days: Số ngày (optional)
            
    #     Returns:
    #         Danh sách tour packages
    #     """
    #     try:
    #         supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
    #         query = supabase.table("tour_packages")\
    #             .select("*")\
    #             .eq("is_active", True)
            
    #         if destination:
    #             query = query.ilike("destination", f"%{destination}%")
            
    #         if max_price:
    #             query = query.lte("price", max_price)
            
    #         if duration_days:
    #             query = query.eq("duration_days", duration_days)
            
    #         response = query.execute()
    #         tours = response.data if response.data else []
            
    #         return {
    #             "success": True,
    #             "total": len(tours),
    #             "tours": tours
    #         }
        
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": f"Lỗi: {str(e)}"
    #         }
    
    # @mcp.tool()
    # async def get_booking_details(booking_id: str) -> Dict[str, Any]:
    #     """
    #     Lấy chi tiết booking
        
    #     Args:
    #         booking_id: ID của booking
            
    #     Returns:
    #         Chi tiết booking
    #     """
    #     try:
    #         supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
    #         response = supabase.table("bookings")\
    #             .select("*, tour_packages(*), users(*)")\
    #             .eq("booking_id", booking_id)\
    #             .single()\
    #             .execute()
            
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
