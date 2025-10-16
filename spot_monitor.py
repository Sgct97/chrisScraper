"""
AWS Spot Instance Interruption Monitor
Monitors for Spot termination warnings and triggers graceful shutdown.
"""
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional, Callable
import httpx


class SpotMonitor:
    """Monitor AWS Spot instance for interruption warnings."""
    
    def __init__(self, shutdown_callback: Optional[Callable] = None):
        self.shutdown_callback = shutdown_callback
        self.monitoring = False
        self.interruption_detected = False
        self.metadata_url = "http://169.254.169.254/latest/meta-data/spot/instance-action"
        self.check_interval = 5  # Check every 5 seconds
        
    async def start_monitoring(self):
        """Start monitoring for Spot interruption warnings."""
        self.monitoring = True
        print(f"[SPOT MONITOR] Started monitoring for interruptions (checking every {self.check_interval}s)")
        
        while self.monitoring:
            try:
                await self._check_interruption()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                # If we can't reach metadata service, we're probably not on EC2
                # Just continue silently
                await asyncio.sleep(self.check_interval)
    
    async def _check_interruption(self):
        """Check AWS metadata for Spot interruption warning."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(self.metadata_url)
                
                if response.status_code == 200:
                    # Interruption warning received!
                    self.interruption_detected = True
                    interruption_time = response.text
                    
                    print(f"\n{'='*80}")
                    print(f"⚠️  AWS SPOT INTERRUPTION WARNING DETECTED!")
                    print(f"{'='*80}")
                    print(f"Scheduled termination: {interruption_time}")
                    print(f"Initiating graceful shutdown NOW...")
                    print(f"{'='*80}\n")
                    
                    # Stop monitoring
                    self.monitoring = False
                    
                    # Call shutdown callback if provided
                    if self.shutdown_callback:
                        if asyncio.iscoroutinefunction(self.shutdown_callback):
                            await self.shutdown_callback()
                        else:
                            self.shutdown_callback()
                    
                    # Give a moment for cleanup, then exit
                    await asyncio.sleep(2)
                    print("[SPOT MONITOR] Shutdown complete. Safe to terminate.")
                    sys.exit(0)
                    
        except httpx.TimeoutException:
            # Timeout is normal - metadata endpoint returns 404 when no interruption
            pass
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # 404 is normal - means no interruption scheduled
                pass
        except Exception:
            # Silently ignore other errors (e.g., not running on EC2)
            pass
    
    def stop_monitoring(self):
        """Stop monitoring for interruptions."""
        self.monitoring = False
        print("[SPOT MONITOR] Stopped monitoring")


class GracefulShutdown:
    """Handle graceful shutdown on SIGTERM, SIGINT, and Spot interruptions."""
    
    def __init__(self, cleanup_callback: Optional[Callable] = None):
        self.cleanup_callback = cleanup_callback
        self.shutting_down = False
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        if self.shutting_down:
            return
        
        self.shutting_down = True
        signal_name = signal.Signals(signum).name
        
        print(f"\n{'='*80}")
        print(f"⚠️  SHUTDOWN SIGNAL RECEIVED: {signal_name}")
        print(f"{'='*80}")
        print(f"Initiating graceful shutdown...")
        print(f"Database will be saved. Scraping will resume on restart.")
        print(f"{'='*80}\n")
        
        # Call cleanup callback if provided
        if self.cleanup_callback:
            try:
                if asyncio.iscoroutinefunction(self.cleanup_callback):
                    # For async callbacks, we need to run in event loop
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self.cleanup_callback())
                else:
                    self.cleanup_callback()
            except Exception as e:
                print(f"[ERROR] Cleanup failed: {e}")
        
        print("[GRACEFUL SHUTDOWN] Cleanup complete. Exiting.")
        sys.exit(0)


async def run_with_spot_monitoring(main_task, cleanup_callback=None):
    """
    Run main task with Spot interruption monitoring.
    
    Args:
        main_task: Coroutine to run (e.g., scraper.run_full_scrape())
        cleanup_callback: Function to call on shutdown (e.g., close connections)
    """
    # Setup graceful shutdown handler
    shutdown_handler = GracefulShutdown(cleanup_callback=cleanup_callback)
    
    # Setup Spot monitor
    spot_monitor = SpotMonitor(shutdown_callback=cleanup_callback)
    
    # Run both tasks concurrently
    monitor_task = asyncio.create_task(spot_monitor.start_monitoring())
    scraper_task = asyncio.create_task(main_task)
    
    try:
        # Wait for scraper to complete (monitor runs in background)
        await scraper_task
        
        # If scraper completes normally, stop monitoring
        spot_monitor.stop_monitoring()
        
    except Exception as e:
        print(f"\n[ERROR] Scraper task failed: {e}")
        spot_monitor.stop_monitoring()
        raise
    finally:
        # Ensure monitor task is cancelled
        if not monitor_task.done():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    # Test the monitor
    async def test():
        print("Testing Spot monitor for 30 seconds...")
        monitor = SpotMonitor()
        await asyncio.sleep(30)
        monitor.stop_monitoring()
    
    asyncio.run(test())

