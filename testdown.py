import os
import requests
import sys


def wide_search_and_download():
    api_url = "https://mediathekviewweb.de/api/query"

    # 1. 构造符合官方实际接口的 Payload
    payload = {
        "queries": [
            {
                "fields": ["title", "topic", "description"],
                "query": "Wissen macht Ah!",
            }
        ],
        "sortBy": "timestamp",
        "sortOrder": "desc",
        "future": False,
        "offset": 0,
        "size": 100,  # 保持 100 条确保能搜索到 page 3 的历史内容
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }

    print("正在向 MediathekViewWeb 发起请求（搜索关键词: Wissen macht Ah!）...")
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"网络请求失败: {e}")
        return

    # 2. 修复核心 Bug：兼容处理官方包裹了 'result' 的返回结构
    if "result" in data and isinstance(data["result"], dict):
        results = data["result"].get("results", [])
    else:
        results = data.get("results", [])

    if not results:
        print("\n[提示] 仍未在返回数据中找到任何包含 'Wissen macht Ah!' 的视频。")
        print("这可能是由于 API 临时限流或结构变更，请检查传入的 Payload。")
        return

    print(f"\n成功获取到 {len(results)} 个候选节目！开始解析并自动下载...")

    # 创建统一的下载保存目录
    download_dir = "./downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    download_count = 0

    # 3. 循环解析并直接下载
    for index, item in enumerate(results):
        title = item.get("title", "未知视频")
        topic = item.get("topic", "")
        channel = item.get("channel", "未知电视台")

        # 优先提取高清(url_hd)，其次普通视频(url_video)
        video_url = item.get("url_hd") or item.get("url_video")

        if not video_url:
            continue

        download_count += 1
        # 清理文件名中的非法字符，防止 Linux 文件系统报错
        safe_title = "".join(
            [c for c in title if c.isalpha() or c.isdigit() or c in " ._-"]
        ).strip()
        filename = os.path.join(download_dir, f"{safe_title}.mp4")

        print(f"\n[{download_count}] 正在下载: {title} ({channel} | {topic})")
        print(f"    链接: {video_url}")
        print(f"    保存路径: {filename}")

        # 4. 自动选择最优下载方案
        # 方案 A：如果您的 Linux 服务器支持 wget 命令，则直接调用系统 wget（最稳定、速度最快且支持断点续传）
        if os.system("which wget > /dev/null 2>&1") == 0:
            print("    检测到系统支持 wget，正在调用 wget 进程加速下载...")
            # -c 支持断点续传，--no-check-certificate 防止 https 证书报错
            cmd = f'wget -c --no-check-certificate "{video_url}" -O "{filename}"'
            exit_code = os.system(cmd)
            if exit_code == 0:
                print("    该视频下载成功！")
            else:
                print(f"    wget 下载失败，错误码: {exit_code}")
        else:
            # 方案 B：如果系统没有 wget，则自动降级使用 Python 原生 requests 流式下载
            print("    未检测到 wget 命令，正在降级使用 Python requests 下载...")
            try:
                with requests.get(
                    video_url, stream=True, timeout=30
                ) as video_response:
                    video_response.raise_for_status()
                    total_size = int(
                        video_response.headers.get("content-length", 0)
                    )

                    with open(filename, "wb") as f:
                        downloaded = 0
                        for chunk in video_response.iter_content(
                            chunk_size=1024 * 64
                        ):  # 扩大缓冲区至 64KB 提高写入性能
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = int(100 * downloaded / total_size)
                                    sys.stdout.write(
                                        f"\r    进度: [{'>' * (percent // 2)}{' ' * (50 - percent // 2)}] {percent}%"
                                    )
                                    sys.stdout.flush()
                                else:
                                    sys.stdout.write(
                                        f"\r    已下载: {downloaded / (1024*1024):.2f} MB"
                                    )
                                    sys.stdout.flush()
                print("\n    该视频下载完成！")
            except Exception as e:
                print(f"\n    下载出错: {e}")

        # 【重要提示】默认会连续下载搜索到的全部 100 条视频。
        # 如果您只想下载列表里的第 1 个最新视频，请把下面这行 break 的注释取消掉：
        # break


if __name__ == "__main__":
    wide_search_and_download()
