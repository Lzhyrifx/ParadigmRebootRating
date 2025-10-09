import httpx
import json
import time


def upload_score(access_token, username, song_level_id, score):

    upload_url = f"https://api.prp.icel.site/records/{username}"


    upload_data = {
        "upload_token": "dcb3491329a4a626abbdd33a47274a08fceff50b9aad5413487dc79e65c949b0",
        "is_replace": True,
        "play_records": [
            {
                "song_level_id": song_level_id,
                "score": score
            }
        ]
    }

    try:

        start_time = time.time()


        with httpx.Client() as client:
            response = client.post(
                upload_url,
                json=upload_data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            end_time = time.time()
            upload_duration = end_time - start_time

            if response.status_code == 201:
                print("分数上传成功")
                print(f"上传耗时: {upload_duration:.2f} 秒")
                print(f"响应内容: {response.text}")
                return True
            else:
                print(f"分数上传失败,状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"上传耗时: {upload_duration:.2f} 秒")
                return False

    except Exception as e:
        print(f"上传请求错误: {e}")
        return False


def main():
    try:
        with open('../token.json', 'r') as f:
            token_info = json.load(f)
        access_token = token_info.get('access_token')
        if not access_token:
            print("未找到有效的access_token，请先登录")
            return
    except FileNotFoundError:
        print("未找到token.json文件，请先登录")
        return


    username = "lzhyrifx"



    song_level_id = 900
    score = 1005823


    program_start = time.time()


    success = upload_score(access_token, username, song_level_id, score)


    program_end = time.time()
    program_duration = program_end - program_start


    print(f"程序总执行时间: {program_duration:.2f} 秒")


if __name__ == "__main__":
    main()