#!/usr/bin/env python3
"""
Cache Optimizer - Standalone Script
Optimizes cache memory by cleaning old files and managing cache size
Runs automatically every Sunday or can be run manually
"""

import os
import sys
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path
import gc

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger()

def get_env(var, default=None):
    """Get environment variable with default"""
    return os.getenv(var, default)

def optimize_cache_memory():
    """Optimize cache memory by cleaning old files and compressing data"""
    # Get cache directory
    cache_dir = Path(get_env('CACHE_DIR', 'cache'))
    if not cache_dir.exists():
        log.info("📁 Cache directory doesn't exist, creating...")
        cache_dir.mkdir(exist_ok=True)
        return
    
    # Get cache optimization settings
    max_cache_age_days = int(get_env('CACHE_MAX_AGE_DAYS', '7'))
    max_cache_size_mb = int(get_env('MAX_CACHE_SIZE_MB', '500'))
    compression_enabled = get_env('CACHE_COMPRESSION_ENABLED', 'true').lower() == 'true'
    
    log.info("🧹 Starting cache optimization...")
    log.info(f"📁 Cache directory: {cache_dir}")
    log.info(f"📅 Max age: {max_cache_age_days} days")
    log.info(f"📦 Max size: {max_cache_size_mb}MB")
    
    try:
        # Calculate cutoff time for old files
        cutoff_time = time.time() - (max_cache_age_days * 24 * 3600)
        
        # Get all cache files
        cache_files = list(cache_dir.glob("*.pkl"))
        total_files = len(cache_files)
        deleted_files = 0
        total_size_before = 0
        total_size_after = 0
        
        if total_files == 0:
            log.info("📭 No cache files found")
            return
        
        # Calculate total size before cleanup
        for cache_file in cache_files:
            total_size_before += cache_file.stat().st_size
        
        log.info(f"📊 Initial cache size: {total_size_before / (1024 * 1024):.1f}MB")
        
        # Remove old cache files
        for cache_file in cache_files:
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > cutoff_time:
                try:
                    cache_file.unlink()
                    deleted_files += 1
                    log.debug(f"🗑️ Deleted old cache file: {cache_file.name}")
                except Exception as e:
                    log.warning(f"Failed to delete cache file {cache_file.name}: {e}")
        
        # Check cache size and remove oldest files if needed
        remaining_files = list(cache_dir.glob("*.pkl"))
        if remaining_files:
            # Sort by modification time (oldest first)
            remaining_files.sort(key=lambda x: x.stat().st_mtime)
            
            current_size_mb = sum(f.stat().st_size for f in remaining_files) / (1024 * 1024)
            
            if current_size_mb > max_cache_size_mb:
                log.info(f"📦 Cache size ({current_size_mb:.1f}MB) exceeds limit ({max_cache_size_mb}MB)")
                
                # Remove oldest files until under limit
                for cache_file in remaining_files:
                    try:
                        file_size_mb = cache_file.stat().st_size / (1024 * 1024)
                        cache_file.unlink()
                        deleted_files += 1
                        current_size_mb -= file_size_mb
                        log.debug(f"🗑️ Removed cache file for size limit: {cache_file.name}")
                        
                        if current_size_mb <= max_cache_size_mb:
                            break
                    except Exception as e:
                        log.warning(f"Failed to delete cache file {cache_file.name}: {e}")
        
        # Calculate final size
        final_files = list(cache_dir.glob("*.pkl"))
        total_size_after = sum(f.stat().st_size for f in final_files)
        
        # Log optimization results
        size_saved_mb = (total_size_before - total_size_after) / (1024 * 1024)
        log.info(f"✅ Cache optimization complete:")
        log.info(f"   📁 Files processed: {total_files}")
        log.info(f"   🗑️ Files deleted: {deleted_files}")
        log.info(f"   💾 Size saved: {size_saved_mb:.1f}MB")
        log.info(f"   📦 Final cache size: {total_size_after / (1024 * 1024):.1f}MB")
        log.info(f"   📈 Space saved: {(size_saved_mb / (total_size_before / (1024 * 1024)) * 100):.1f}%")
        
        # Force garbage collection
        gc.collect()
        
    except Exception as e:
        log.error(f"❌ Cache optimization failed: {e}")

def should_run_weekly_optimization():
    """Check if weekly cache optimization should run (every Sunday)"""
    try:
        cache_dir = Path(get_env('CACHE_DIR', 'cache'))
        optimization_log_file = cache_dir / "last_optimization.txt"
        
        if optimization_log_file.exists():
            with open(optimization_log_file, 'r') as f:
                last_optimization = datetime.fromisoformat(f.read().strip())
            
            # Check if it's Sunday and more than 6 days since last optimization
            current_time = datetime.now()
            days_since_last = (current_time - last_optimization).days
            
            # Run on Sunday (weekday 6) or if more than 7 days have passed
            is_sunday = current_time.weekday() == 6
            should_run = is_sunday and days_since_last >= 6
            
            if should_run:
                log.info(f"📅 Weekly cache optimization scheduled for Sunday")
            
            return should_run
        else:
            # First time running, create log file and run optimization
            cache_dir.mkdir(exist_ok=True)
            with open(optimization_log_file, 'w') as f:
                f.write(datetime.now().isoformat())
            return True
            
    except Exception as e:
        log.warning(f"Failed to check weekly optimization schedule: {e}")
        return False

def run_scheduled_cache_optimization():
    """Run cache optimization if it's scheduled"""
    if should_run_weekly_optimization():
        optimize_cache_memory()
        
        # Update last optimization time
        try:
            cache_dir = Path(get_env('CACHE_DIR', 'cache'))
            optimization_log_file = cache_dir / "last_optimization.txt"
            with open(optimization_log_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            log.warning(f"Failed to update optimization log: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cache Optimizer - Clean up cache memory')
    parser.add_argument('--force', action='store_true', help='Force optimization regardless of schedule')
    parser.add_argument('--weekly', action='store_true', help='Check weekly schedule and run if needed')
    parser.add_argument('--info', action='store_true', help='Show cache information without cleaning')
    
    args = parser.parse_args()
    
    if args.info:
        # Show cache information
        cache_dir = Path(get_env('CACHE_DIR', 'cache'))
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            log.info(f"📊 Cache Information:")
            log.info(f"   📁 Directory: {cache_dir}")
            log.info(f"   📄 Files: {len(cache_files)}")
            log.info(f"   💾 Size: {total_size / (1024 * 1024):.1f}MB")
            
            # Show oldest and newest files
            if cache_files:
                cache_files.sort(key=lambda x: x.stat().st_mtime)
                oldest = datetime.fromtimestamp(cache_files[0].stat().st_mtime)
                newest = datetime.fromtimestamp(cache_files[-1].stat().st_mtime)
                log.info(f"   📅 Oldest file: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
                log.info(f"   📅 Newest file: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            log.info("📁 Cache directory doesn't exist")
        return
    
    if args.force:
        log.info("🔧 Force running cache optimization...")
        optimize_cache_memory()
    elif args.weekly:
        log.info("📅 Checking weekly schedule...")
        run_scheduled_cache_optimization()
    else:
        # Default: run weekly check
        log.info("📅 Running weekly cache optimization check...")
        run_scheduled_cache_optimization()

if __name__ == "__main__":
    main() 