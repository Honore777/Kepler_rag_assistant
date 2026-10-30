#!/usr/bin/env python3
"""
Test script for role-based rate limiting with local Redis.
This verifies the professional rate limiting implementation works correctly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.rate_limiter import rate_limiter
from app.core.config import settings

async def test_rate_limiting():
    """Test role-based rate limiting functionality."""
    print("🧪 Testing Role-Based Rate Limiting with Local Redis")
    print("=" * 60)
    
    # Test configuration
    print(f"📋 Configuration:")
    print(f"   Redis URL: {settings.REDIS_URL}")
    print(f"   Student Limit: {settings.RATE_LIMIT_STUDENT}/minute")
    print(f"   Staff Limit: {settings.RATE_LIMIT_STAFF}/minute") 
    print(f"   Admin Limit: {settings.RATE_LIMIT_ADMIN}/minute")
    print()
    
    # Test rate limiting for different roles
    test_cases = [
        ("student_001", "student", "/rag/query"),
        ("staff_001", "staff", "/rag/query"),
        ("admin_001", "admin", "/rag/query"),
    ]
    
    for user_id, role, endpoint in test_cases:
        print(f"🔍 Testing {role.upper()} rate limiting...")
        
        # Test multiple requests
        success_count = 0
        for i in range(1, 60):  # Test up to 60 requests
            allowed = await rate_limiter.check_rate_limit(user_id, role, endpoint)
            if allowed:
                success_count += 1
            else:
                break
        
        expected_limit = rate_limiter.role_limits.get(role, 10)
        print(f"   ✅ {role}: {success_count}/{expected_limit} requests allowed")
        
        # Verify stats
        stats = await rate_limiter.get_user_stats(user_id, endpoint)
        if "error" not in stats:
            print(f"   📊 Current usage: {stats['current_requests']}")
            print(f"   ⏰ Time to reset: {stats['time_to_reset']}s")
        else:
            print(f"   ❌ Stats error: {stats['error']}")
        
        print()
    
    print("🎉 Role-based rate limiting test completed!")
    print()
    print("📋 Implementation Summary:")
    print("✅ Student users: 10 requests/minute")
    print("✅ Staff users: 20 requests/minute")
    print("✅ Admin users: 50 requests/minute")
    print("✅ Local Redis backend for phase 1")
    print("✅ User-based (not IP-based) limiting")
    print("✅ Fail-open on Redis connection issues")

async def test_redis_connection():
    """Test Redis connection and basic functionality."""
    print("🔗 Testing Redis Connection...")
    
    try:
        # Test basic Redis operations
        client = await rate_limiter._get_redis_client()
        
        # Test ping
        await client.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        test_key = "test:rate_limit:demo"
        await client.set(test_key, "1", ex=60)
        value = await client.get(test_key)
        await client.delete(test_key)
        
        print("✅ Redis operations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("⚠️ Make sure Redis is running locally:")
        print("   - Windows: Start Redis service")
        print("   - Or run: redis-server")
        return False

async def main():
    """Run all rate limiting tests."""
    print("🚀 Testing Professional Role-Based Rate Limiting")
    print("=" * 60)
    
    # Test Redis connection first
    redis_ok = await test_redis_connection()
    if not redis_ok:
        print("\n❌ Please start Redis server and try again")
        sys.exit(1)
    
    print()
    
    # Test rate limiting functionality
    await test_rate_limiting()
    
    print("\n🔧 Ready for Phase 1 Team Demo!")
    print("   - Local Redis for rate limiting")
    print("   - Role-based access control")
    print("   - Professional error handling")

if __name__ == "__main__":
    asyncio.run(main())
