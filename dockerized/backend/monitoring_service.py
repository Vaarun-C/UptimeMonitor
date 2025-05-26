import asyncio
import time
import aiohttp
from typing import Dict

from database_manager import DatabaseManager
from notification_service import NotificationService

class MonitoringService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        try:
            self.notification_service = NotificationService(db_manager=db_manager)
            print("✅ Notification service initialized successfully")
        except Exception as e:
            print(f"❌ Notification service failed to initialize: {e}")
            self.notification_service = None
            
        self.session = None
        self.running = False
    
    async def start_monitoring(self):
        self.running = True

        connector = aiohttp.TCPConnector(
            ssl=False,  # Keep SSL disabled for development
            limit=100,
            limit_per_host=10
        )
        
        headers = {
            'User-Agent': 'UptimeMonitor/1.0 (Monitoring Service)'
        }
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector,
            headers=headers
        )
        
        print("🔍 Starting uptime monitoring service...")
        
        # Do an initial check immediately
        await self.check_all_urls()
        
        while self.running:
            await asyncio.sleep(300)  # 5 minutes
            await self.check_all_urls()
            
            if self.notification_service:
                print("📧 Sending periodic notifications to all users...")
                self.notification_service.send_notifications_to_all_users()
            else:
                print("⚠️ Notification service not available - skipping emails")
    
    async def check_all_urls(self):
        urls = self.db_manager.get_all_urls()
        if not urls:
            print("📝 No URLs to monitor yet")
            return
        
        print(f"🔍 Checking {len(urls)} URLs...")
        
        # Check all URLs concurrently for efficiency
        tasks = [self.check_single_url(url_data) for url_data in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Error checking URL {urls[i]['url']}: {result}")
    
    async def check_single_url(self, url_data: Dict):
        url_id = url_data["id"]
        url = url_data["url"]
        start_time = time.time()
        
        try:
            async with self.session.get(
                url, 
                allow_redirects=True,
                ssl=False
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                status = "success" if response.status < 400 else "error"
                
                self.db_manager.add_check_result(
                    url_id=url_id,
                    response_code=response.status,
                    status=status,
                    response_time_ms=response_time_ms
                )
                
                print(f"✅ {url}: {response.status} ({response_time_ms}ms)")
                
        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            self.db_manager.add_check_result(
                url_id=url_id,
                response_code=0,
                status="error",
                response_time_ms=response_time_ms
            )
            print(f"⏰ {url}: Timeout after {response_time_ms}ms")
            
        except aiohttp.ClientError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self.db_manager.add_check_result(
                url_id=url_id,
                response_code=0,
                status="error",
                response_time_ms=response_time_ms
            )
            print(f"🌐 {url}: Connection Error - {str(e)}")
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self.db_manager.add_check_result(
                url_id=url_id,
                response_code=0,
                status="error",
                response_time_ms=response_time_ms
            )
            print(f"❌ {url}: Error - {str(e)}")
    
    async def check_single_url_immediately(self, url: str):
        urls = self.db_manager.get_all_urls()
        url_data = next((u for u in urls if u["url"] == url), None)
        
        if url_data and self.session:
            await self.check_single_url(url_data)
        elif url_data:
            # Create temporary session if main session not available
            connector = aiohttp.TCPConnector(ssl=False)
            
            headers = {
                'User-Agent': 'UptimeMonitor/1.0 (Monitoring Service)'
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=connector,
                headers=headers
            ) as temp_session:
                self.session = temp_session
                await self.check_single_url(url_data)
                self.session = None
    
    async def send_user_notification(self, user_id: int, user_email: str):
        if self.notification_service:
            return self.notification_service.send_user_uptime_summary(user_id, user_email)
        else:
            print("⚠️ Notification service not available")
            return False
    
    async def stop_monitoring(self):
        self.running = False
        if self.session:
            await self.session.close()