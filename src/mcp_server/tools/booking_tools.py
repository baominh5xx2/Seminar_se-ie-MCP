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
    async def create_booking(
        user_phone: str,
        package_id: str,
        number_of_people: int,
        travel_date: str,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tạo booking mới cho user - YÊU CẦU THU THẬP ĐẦY ĐỦ THÔNG TIN TRƯỚC KHI GỌI
        
        Trước khi gọi tool này, PHẢI thu thập đầy đủ:
        - Số điện thoại (phone_number)
        - Tour muốn đặt (package_id)
        - Số người tham gia (number_of_people)
        - Yêu cầu đặc biệt nếu có (special_requests)
        
        Sau khi thu thập đủ, PHẢI gửi tin nhắn xác nhận cho user TRƯỚC KHI tạo booking:
        "Xác nhận thông tin đặt tour:
        - Tên khách hàng: [full_name]
        - Tour: [tên tour]
        - Điểm đi: [departure_location]
        - Điểm đến: [destination]
        - Số người: [X] người
        - Ngày đi: [date]
        - Tổng tiền: [amount] VNĐ
        - Yêu cầu: [special_requests]
        
        Bạn có xác nhận đặt tour này không?"
        
        Args:
            phone_number: Số điện thoại user
            package_id: ID của tour package
            number_of_people: Số người tham gia
            special_requests: Yêu cầu đặc biệt (optional)
            
        Returns:
            Booking information với booking_id và OTP code
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # 1. Check if user exists, if not create user profile
            user_response = supabase.table("users")\
                .select("*")\
                .eq("phone_number", user_phone)\
                .execute()
            
            if not user_response.data or len(user_response.data) == 0:
                # Create new user with phone number
                new_user = {
                    "phone_number": user_phone,
                    "full_name": user_phone,  # Temporary, will be updated later
                    "created_at": datetime.now().isoformat()
                }
                user_create_response = supabase.table("users").insert(new_user).execute()
                if not user_create_response.data:
                    return {
                        "success": False,
                        "error": "Không thể tạo user profile"
                    }
                user = user_create_response.data[0]
            else:
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
    
    @mcp.tool()
    async def search_available_tours(
        destination: Optional[str] = None,
        max_price: Optional[float] = None,
        duration_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tìm kiếm tour packages có sẵn
        
        Args:
            destination: Điểm đến (optional)
            max_price: Giá tối đa (optional)
            duration_days: Số ngày (optional)
            
        Returns:
            Danh sách tour packages
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            query = supabase.table("tour_packages")\
                .select("*")\
                .eq("is_active", True)
            
            if destination:
                query = query.ilike("destination", f"%{destination}%")
            
            if max_price:
                query = query.lte("price", max_price)
            
            if duration_days:
                query = query.eq("duration_days", duration_days)
            
            response = query.execute()
            tours = response.data if response.data else []
            
            return {
                "success": True,
                "total": len(tours),
                "tours": tours
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    @mcp.tool()
    async def get_booking_details(booking_id: str) -> Dict[str, Any]:
        """
        Lấy chi tiết booking
        
        Args:
            booking_id: ID của booking
            
        Returns:
            Chi tiết booking
        """
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            response = supabase.table("bookings")\
                .select("*, tour_packages(*), users(*)")\
                .eq("booking_id", booking_id)\
                .single()\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "booking": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "Không tìm thấy booking"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
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
