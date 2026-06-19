import os
import requests

def wide_search_and_download():
    api_url = "https://mediathekviewweb.de/api/query"
    
    # 扩大搜索范围的 Payload
    payload = {
        "queries": [
            # 仅搜索最核心的特征词 "Unerschrocken"，避免被 "Echte Heldinnen" 等字眼限制
            {"fields": ["title", "topic", "description"], "query": "Unerschrocken"}
        ],
        "sortBy": "timestamp",
        "sortOrder": "desc",
        "future": False,  # 允许搜索历史已播出的节目
        "offset": 0,
        "size": 100       # 扩大返回结果数量到 100 条
    }
    
    print("正在扩大范围搜索（关键词: Unerschrocken...")
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"网络请求失败: {e}")
        return

    results = data.get("results", [])
    if not results:
        print("\n[提示] 扩大范围后仍未在 MediathekViewWeb 数据库中找到任何包含 'Unerschrocken' 的视频。")
        print("这通常意味着该节目在各大电视台（如 ARD, ZDF, ARTE）的在线播放限时（Media Library Period）已过，视频已被官方下架。")
        return

    print(f"\n成功找到 {len(results)} 个候选节目！正在为您筛选匹配的视频...")
    
    # 列出所有找到的结果供参考
    for index, item in enumerate(results):
        title = item.get("title", "")
        topic = item.get("topic", "")
        channel = item.get("channel", "未知电视台")
        print(f"[{index + 1}] 频道: {channel} | 主题: {topic} | 标题: {title}")

    # 默认尝试下载第一个匹配项
    target_video = results[0]
    video_url = target_video.get("url_video") or target_video.get("url_hd")
    
    if not video_url:
        print("\n未能提取到有效的视频下载链接。")
        return

    video_title = target_video.get("title", "Unerschrocken_Video")
    safe_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c in " ._-"]).strip()
    filename = f"{safe_title}.mp4"

    print(f"\n准备下载第 1 个视频: {video_title}")
    print(f"保存文件名: {filename}")
    
    try:
        with requests.get(video_url, stream=True) as video_response:
            video_response.raise_for_status()
            total_size = int(video_response.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(100 * downloaded / total_size)
                            print(f"\r下载进度: [{'>' * (percent // 2)}{' ' * (50 - percent // 2)}] {percent}%", end="")
                        else:
                            print(f"\r已下载: {downloaded / (1024*1024):.2f} MB", end="")
                            
        print("\n下载完成！")
    except Exception as e:
        print(f"\n下载过程中出错: {e}")

if __name__ == "__main__":
    wide_search_and_download()
