import os
import requests


def wide_search_and_download():
    api_url = "https://mediathekviewweb.de/api/query"

    # 修正后的正确 Payload 格式
    payload = {
        "queries": [
            {
                "fields": ["title", "topic"],
                "query": "Wissen macht Ah!",
            }  # 确保字段和词正确
        ],
        "sortBy": "timestamp",
        "sortOrder": "desc",
        "future": False,
        "offset": 0,
        "size": 20,  # 先拿20条测试
    }

    print("正在向 API 请求数据（关键词: Wissen macht Ah!）...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }

    try:
        # 注意：有时候服务器严格检查，添加 headers 避开拦截
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"网络请求失败: {e}")
        return

    # MediathekViewWeb 返回的实际数据在外层可能包裹在 result 字典中
    # 结构通常是 {"result": {"results": [...]}, "err": null}
    result_obj = data.get("result", {})
    results = result_obj.get("results", [])

    if not results:
        # 如果还是找不到，尝试用更宽松的全局字符串搜索格式
        print("标准搜索无结果，尝试备用全局搜索格式...")
        backup_payload = {
            "queries": [{"fields": ["title"], "query": "Wissen"}],
            "size": 10,
        }
        try:
            response = requests.post(
                api_url, json=backup_payload, headers=headers
            )
            results = response.json().get("result", {}).get("results", [])
        except:
            pass

    if not results:
        print("\n[提示] 仍未找到视频，请检查网络或 API 接口变动。")
        return

    print(f"\n成功找到 {len(results)} 个候选节目！")

    # 遍历所有找到的结果，并提取出下载链接和生成 wget 命令
    for index, item in enumerate(results):
        title = item.get("title", "未知标题")
        topic = item.get("topic", "未知主题")
        # 提取高清或普通视频链接
        video_url = item.get("url_video") or item.get("url_hd")

        if video_url:
            print(f"\n[{index + 1}] 主题: {topic} | 标题: {title}")
            print(f"    视频直链: {video_url}")
            # 打印 wget 命令，加上 -O 参数自定义文件名防止名字太长或报错
            safe_title = "".join(
                [c for c in title if c.isalpha() or c.isdigit() or c in " ._-"]
            ).strip()
            print(
                f"    Linux wget 下载命令: \n    wget -O \"{safe_title}.mp4\" \"{video_url}\""
            )

    # 默认下载第一个
    target_video = results[0]
    final_url = target_video.get("url_video") or target_video.get("url_hd")

    if final_url:
        print(
            f"\n[提示] 如需在当前服务器直接下载第一个视频，可复制运行以下命令："
        )
        print(f"wget -c \"{final_url}\"")  # -c 支持断点续传


if __name__ == "__main__":
    wide_search_and_download()
