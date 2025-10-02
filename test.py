import httpx
import json
import time
import os


def user_login(username, password):
    login_url = "https://api.prp.icel.site/user/login"

    login_data = {
        "grant_type": "password",
        "username": username,
        "password": password
    }

    try:
        start_time = time.time()

        with httpx.Client() as client:
            response = client.post(
                login_url,
                data=login_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )

            end_time = time.time()
            request_duration = end_time - start_time

            if response.status_code == 200:
                token_data = response.json()
                print("登录成功")
                print(f"Access Token: {token_data.get('access_token')}")
                print(f"Token Type: {token_data.get('token_type')}")
                print(f"请求耗时: {request_duration:.2f} 秒")
                return token_data, request_duration
            elif response.status_code == 422:
                error_data = response.json()
                print("登录失败")
                print(f"错误详情: {error_data}")
                print(f"请求耗时: {request_duration:.2f} 秒")
                return None, request_duration
            else:
                print(f"登录失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"请求耗时: {request_duration:.2f} 秒")
                return None, request_duration

    except httpx.RequestError as e:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"请求错误: {e}")
        print(f"请求耗时: {request_duration:.2f} 秒")
        return None, request_duration
    except Exception as e:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"发生错误: {e}")
        print(f"请求耗时: {request_duration:.2f} 秒")
        return None, request_duration


def get_upload_token(access_token):
    """获取 upload_token"""
    upload_token_url = "https://api.prp.icel.site/user/me/upload-token"

    try:
        start_time = time.time()

        with httpx.Client() as client:
            response = client.post(
                upload_token_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            end_time = time.time()
            request_duration = end_time - start_time

            if response.status_code == 200:
                upload_data = response.json()
                upload_token = upload_data.get('upload_token')
                print("成功获取 upload_token")
                print(f"Upload Token: {upload_token}")
                print(f"请求耗时: {request_duration:.2f} 秒")
                return upload_token, request_duration
            else:
                print(f"获取 upload_token 失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"请求耗时: {request_duration:.2f} 秒")
                return None, request_duration

    except httpx.RequestError as e:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"请求错误: {e}")
        print(f"请求耗时: {request_duration:.2f} 秒")
        return None, request_duration
    except Exception as e:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"发生错误: {e}")
        print(f"请求耗时: {request_duration:.2f} 秒")
        return None, request_duration


def save_tokens_safely(token_info, upload_token, filename='tokens.json'):
    """安全地保存 tokens 到文件"""
    tokens_data = {
        'access_token': token_info.get('access_token'),
        'token_type': token_info.get('token_type'),
        'upload_token': upload_token,
        'created_at': time.time(),
        'expires_in': token_info.get('expires_in', 3600)  # 默认 1 小时
    }

    try:
        # 设置文件权限为仅当前用户可读写 (600)
        with open(filename, 'w') as f:
            json.dump(tokens_data, f, indent=2)

        # 在 Unix 系统上设置文件权限
        if os.name != 'nt':  # 不是 Windows 系统
            os.chmod(filename, 0o600)

        print(f"Tokens 已安全保存到 {filename}")
        return True
    except Exception as e:
        print(f"保存 tokens 失败: {e}")
        return False


def load_tokens(filename='tokens.json'):
    """从文件加载 tokens"""
    try:
        with open(filename, 'r') as f:
            tokens_data = json.load(f)
        print("Tokens 加载成功")
        return tokens_data
    except Exception as e:
        print(f"加载 tokens 失败: {e}")
        return None


def main():
    username = "Lzhyrifx"  # 替换为实际用户名
    password = "Lzhyrifx042420"  # 替换为实际密码

    # 记录程序开始时间
    program_start = time.time()

    # 执行登录
    token_info, login_duration = user_login(username, password)

    if token_info:
        # 获取 upload_token
        access_token = token_info.get('access_token')
        upload_token, upload_duration = get_upload_token(access_token)
        print(upload_token)

        if upload_token:
            # 安全地保存所有 tokens
            save_tokens_safely(token_info, upload_token, 'tokens.json')

            # 显示耗时信息
            print(f"\n登录请求耗时: {login_duration:.2f} 秒")
            print(f"获取 upload_token 耗时: {upload_duration:.2f} 秒")

            # 记录程序结束时间
            program_end = time.time()
            program_duration = program_end - program_start
            print(f"程序总执行时间: {program_duration:.2f} 秒")

            # 可选：验证加载功能
            print("\n验证 tokens 加载...")
            loaded_tokens = load_tokens('tokens.json')
            if loaded_tokens:
                print("Tokens 加载验证成功")
        else:
            print("获取 upload_token 失败")
    else:
        print("登录失败，请检查用户名和密码")
        print(f"登录请求耗时: {login_duration:.2f} 秒")


if __name__ == "__main__":
    main()