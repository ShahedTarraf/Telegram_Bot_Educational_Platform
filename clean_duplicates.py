"""
Clean Duplicate Videos and Assignments
تنظيف الفيديوهات والواجبات المكررة
"""
import json
from pathlib import Path
from collections import defaultdict


def clean_videos():
    """Remove duplicate videos"""
    videos_file = Path('data/videos.json')
    
    if not videos_file.exists():
        print("❌ ملف videos.json غير موجود")
        return
    
    with open(videos_file, 'r', encoding='utf-8') as f:
        all_videos = json.load(f)
    
    print(f"\n📊 عدد الفيديوهات قبل التنظيف: {len(all_videos)}")
    
    # Remove duplicates based on file_id and title
    seen = set()
    unique_videos = []
    
    for video in all_videos:
        # Create unique key
        key = (video.get('file_id'), video.get('title'), video.get('item_id'))
        
        if key not in seen:
            seen.add(key)
            unique_videos.append(video)
        else:
            print(f"🗑️  حذف فيديو مكرر: {video.get('title')}")
    
    print(f"✅ عدد الفيديوهات بعد التنظيف: {len(unique_videos)}")
    
    # Save cleaned data
    with open(videos_file, 'w', encoding='utf-8') as f:
        json.dump(unique_videos, f, ensure_ascii=False, indent=2)
    
    return len(all_videos) - len(unique_videos)


def clean_assignments():
    """Remove duplicate assignments"""
    assignments_file = Path('data/assignments.json')
    
    if not assignments_file.exists():
        print("❌ ملف assignments.json غير موجود")
        return
    
    with open(assignments_file, 'r', encoding='utf-8') as f:
        all_assignments = json.load(f)
    
    print(f"\n📊 عدد الواجبات قبل التنظيف: {len(all_assignments)}")
    
    # Remove duplicates based on title and item_id
    seen = set()
    unique_assignments = []
    
    for assignment in all_assignments:
        # Create unique key - keep the latest one
        key = (assignment.get('title'), assignment.get('item_id'))
        
        if key not in seen:
            seen.add(key)
            unique_assignments.append(assignment)
        else:
            print(f"🗑️  حذف واجب مكرر: {assignment.get('title')}")
    
    print(f"✅ عدد الواجبات بعد التنظيف: {len(unique_assignments)}")
    
    # Save cleaned data
    with open(assignments_file, 'w', encoding='utf-8') as f:
        json.dump(unique_assignments, f, ensure_ascii=False, indent=2)
    
    return len(all_assignments) - len(unique_assignments)


def main():
    print("\n" + "="*60)
    print("🧹 تنظيف البيانات المكررة")
    print("="*60)
    
    videos_removed = clean_videos()
    assignments_removed = clean_assignments()
    
    print("\n" + "="*60)
    print("✅ اكتمل التنظيف!")
    print(f"🗑️  تم حذف {videos_removed} فيديو مكرر")
    print(f"🗑️  تم حذف {assignments_removed} واجب مكرر")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
