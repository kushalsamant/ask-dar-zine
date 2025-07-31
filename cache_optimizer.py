#!/usr/bin/env python3
"""
Cache Optimizer - Standalone Script
Optimize cache memory by removing old and large files
Can be run independently or scheduled
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('ask.env')

def get_env(var, default=None):
    """Get environment variable with default"""
    return os.getenv(var, default)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger()

def optimize_cache_memory():
    """Optimize cache memory by removing old and large files"""
    cache_enabled = get_env('CACHE_ENABLED', 'true').lower() == 'true'
    if not cache_enabled:
        log.info("Cache is disabled, skipping optimization")
        return
    
    log.info("🧹 Starting cache optimization...")
    
    # Cache optimization settings
    cache_dir = Path(get_env('CACHE_DIR', 'cache'))
    max_cache_age_days = int(get_env('CACHE_MAX_AGE_DAYS', '7'))
    max_cache_size_mb = int(get_env('CACHE_MAX_SIZE_MB', '500'))
    max_file_size_mb = int(get_env('CACHE_MAX_FILE_SIZE_MB', '50'))
    
    if not cache_dir.exists():
        log.info("Cache directory does not exist, nothing to optimize")
        return
    
    try:
        cache_files = list(cache_dir.glob("*.pkl"))
        total_files = len(cache_files)
        total_size_mb = 0
        removed_files = 0
        removed_size_mb = 0
        
        current_time = time.time()
        max_age_seconds = max_cache_age_days * 24 * 3600
        
        log.info(f"📊 Found {total_files} cache files")
        
        for cache_file in cache_files:
            try:
                # Get file stats
                stat = cache_file.stat()
                file_size_mb = stat.st_size / (1024 * 1024)
                file_age_seconds = current_time - stat.st_mtime
                
                # Check if file should be removed
                should_remove = False
                reason = ""
                
                # Remove old files
                if file_age_seconds > max_age_seconds:
                    should_remove = True
                    reason = f"old ({file_age_seconds / 3600 / 24:.1f} days)"
                
                # Remove large files
                elif file_size_mb > max_file_size_mb:
                    should_remove = True
                    reason = f"large ({file_size_mb:.1f} MB)"
                
                if should_remove:
                    removed_size_mb += file_size_mb
                    cache_file.unlink()
                    removed_files += 1
                    log.info(f"🗑️ Removed: {cache_file.name} ({reason})")
                else:
                    total_size_mb += file_size_mb
                    
            except Exception as e:
                log.warning(f"⚠️ Error processing {cache_file.name}: {e}")
                # Remove corrupted files
                try:
                    cache_file.unlink()
                    removed_files += 1
                    log.info(f"🗑️ Removed corrupted file: {cache_file.name}")
                except:
                    pass
        
        # Check total cache size
        if total_size_mb > max_cache_size_mb:
            log.warning(f"⚠️ Cache size ({total_size_mb:.1f} MB) exceeds limit ({max_cache_size_mb} MB)")
            # Remove oldest files to reduce size
            cache_files = sorted(cache_dir.glob("*.pkl"), key=lambda x: x.stat().st_mtime)
            for cache_file in cache_files:
                if total_size_mb <= max_cache_size_mb * 0.8:  # Leave 20% buffer
                    break
                try:
                    file_size_mb = cache_file.stat().st_size / (1024 * 1024)
                    cache_file.unlink()
                    total_size_mb -= file_size_mb
                    removed_files += 1
                    removed_size_mb += file_size_mb
                    log.info(f"🗑️ Removed for size limit: {cache_file.name}")
                except Exception as e:
                    log.warning(f"⚠️ Error removing {cache_file.name}: {e}")
        
        log.info(f"✅ Cache optimization complete:")
        log.info(f"   📊 Total files: {total_files}")
        log.info(f"   🗑️ Removed files: {removed_files}")
        log.info(f"   💾 Removed size: {removed_size_mb:.1f} MB")
        log.info(f"   📁 Remaining size: {total_size_mb:.1f} MB")
        
    except Exception as e:
        log.error(f"❌ Cache optimization failed: {e}")

def show_cache_stats():
    """Show current cache statistics"""
    cache_dir = Path(get_env('CACHE_DIR', 'cache'))
    
    if not cache_dir.exists():
        log.info("Cache directory does not exist")
        return
    
    try:
        cache_files = list(cache_dir.glob("*.pkl"))
        total_files = len(cache_files)
        total_size_mb = 0
        oldest_file = None
        newest_file = None
        
        for cache_file in cache_files:
            stat = cache_file.stat()
            file_size_mb = stat.st_size / (1024 * 1024)
            total_size_mb += file_size_mb
            
            if oldest_file is None or stat.st_mtime < oldest_file.stat().st_mtime:
                oldest_file = cache_file
            
            if newest_file is None or stat.st_mtime > newest_file.stat().st_mtime:
                newest_file = cache_file
        
        log.info(f"📊 Cache Statistics:")
        log.info(f"   📁 Directory: {cache_dir}")
        log.info(f"   📄 Total files: {total_files}")
        log.info(f"   💾 Total size: {total_size_mb:.1f} MB")
        
        if oldest_file:
            oldest_age = (time.time() - oldest_file.stat().st_mtime) / (24 * 3600)
            log.info(f"   🕰️ Oldest file: {oldest_file.name} ({oldest_age:.1f} days old)")
        
        if newest_file:
            newest_age = (time.time() - newest_file.stat().st_mtime) / (24 * 3600)
            log.info(f"   🆕 Newest file: {newest_file.name} ({newest_age:.1f} days old)")
        
    except Exception as e:
        log.error(f"❌ Error getting cache stats: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cache Optimizer - Clean up cache memory')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics only')
    parser.add_argument('--force', action='store_true', help='Force optimization even if not Sunday')
    
    args = parser.parse_args()
    
    if args.stats:
        show_cache_stats()
        return
    
    # Check if it's Sunday (optional)
    if not args.force:
        today = datetime.now()
        if today.weekday() != 6:  # Not Sunday
            log.info("📅 Today is not Sunday. Use --force to run anyway.")
            log.info("💡 Weekly cache optimization is scheduled for Sundays")
            return
    
    log.info("🚀 Starting cache optimization...")
    optimize_cache_memory()
    log.info("✅ Cache optimization completed!")

if __name__ == "__main__":
    main() 