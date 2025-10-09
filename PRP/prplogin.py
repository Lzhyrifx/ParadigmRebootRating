import httpx
import json
import time


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


def main():
    username = "Lzhyrifx"
    password = input()

    program_start = time.time()

    # 执行登录
    token_info, login_duration = user_login(username, password)

    # 记录程序结束时间
    program_end = time.time()
    program_duration = program_end - program_start

    if token_info:
        # 登录成功，可以保存 token 供后续使用
        with open('../token.json', 'w') as f:
            json.dump(token_info, f, indent=2)
        print("Token 已保存到 token.json")

        # 后续可以使用这个 token 访问其他需要认证的 API
        access_token = token_info.get('access_token')

        # 显示总耗时
        print(f"\n登录请求耗时: {login_duration:.2f} 秒")
        print(f"程序总执行时间: {program_duration:.2f} 秒")

    else:
        print("登录失败，请检查用户名和密码")
        print(f"登录请求耗时: {login_duration:.2f} 秒")
        print(f"程序总执行时间: {program_duration:.2f} 秒")


if __name__ == "__main__":
    main()