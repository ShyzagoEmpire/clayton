from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    UnauthorizedError
)
from telethon.functions import messages
from telethon.sync import TelegramClient
from telethon.types import (
    InputBotAppShortName,
    AppWebViewResultUrl
)
from urllib.parse import unquote
import asyncio, json, os, sys

class Clayton:
    def __init__(self) -> None:
        config = json.load(open('config.json', 'r'))
        self.api_id = int(config['api_id'])
        self.api_hash = config['api_hash']
        self.games = config['games']
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'tonclayton.fun',
            'Pragma': 'no-cache',
            'Priority': 'u=3, i',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            client = TelegramClient(session=f'sessions/{session}', api_id=self.api_id, api_hash=self.api_hash)
            try:
                if not client.is_connected():
                    await client.connect()

                    me = await client.get_me()
                    name = me.first_name if me.first_name is not None else me.username
            except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedBanError, UserDeactivatedError) as error:
                raise error

            webapp_response: AppWebViewResultUrl = await client(messages.RequestAppWebViewRequest(
                peer='claytoncoinbot',
                app=InputBotAppShortName(bot_id=await client.get_input_entity('claytoncoinbot'), short_name='game'),
                platform='ios',
                write_allowed=True,
                start_param='6094625904'
            ))
            query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            
            if client.is_connected():
                await client.disconnect()

            return (name, query)
        except Exception as error:
            await client.disconnect()
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def generate_queries(self, sessions):
        tasks = [self.generate_query(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def authorization(self, query: str):
        url = 'https://tonclayton.fun/api/user/authorization'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    authorization = await response.json()
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ {authorization['user']['tokens']} Token ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ {authorization['user']['current_xp']} Experience Point ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Consecutive Days {authorization['user']['consecutive_days']} ]{Style.RESET_ALL}"
                    )
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While User Daily Claim: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While User Daily Claim: {str(error)} ]{Style.RESET_ALL}")

    async def user_daily_claim(self, query: str):
        url = 'https://tonclayton.fun/api/user/daily-claim'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 400:
                        error_user_daily_claim = await response.json()
                        if error_user_daily_claim['error'] == 'daily reward already claimed today':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Daily Reward Already Claimed Today ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    user_daily_claim = await response.json()
                    if user_daily_claim['message'] == 'Daily reward claimed successfully':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {user_daily_claim['tokens']} Token From Daily Reward ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While User Daily Claim: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While User Daily Claim: {str(error)} ]{Style.RESET_ALL}")

    async def tasks(self, query: str, type: str):
        url = f'https://tonclayton.fun/api/tasks/{type}'
        headers = {
            **self.headers,
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(error)} ]{Style.RESET_ALL}")
            return None
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def tasks_complete(self, query: str, task_id: int, task_title: str, task_reward_tokens: int, task_game_attempts: int):
        url = 'https://tonclayton.fun/api/tasks/complete'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_tasks_complete = await response.json()
                        if error_tasks_complete['error'] == 'task already completed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Completed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return await self.tasks_claim(query=query, task_id=task_id, task_title=task_title, task_reward_tokens=task_reward_tokens, task_game_attempts=task_game_attempts)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tasks Complete: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tasks Complete: {str(error)} ]{Style.RESET_ALL}")

    async def tasks_check(self, query: str, task_id: int, task_title: str, task_reward_tokens: int, task_game_attempts: int):
        url = 'https://tonclayton.fun/api/tasks/check'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_tasks_complete = await response.json()
                        if error_tasks_complete['error'] == 'task already completed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Completed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tasks_check = await response.json()
                    if not tasks_check['is_completed'] and tasks_check['message'] == 'task not completed yet':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Not Completed Yet ]{Style.RESET_ALL}")
                    return await self.tasks_claim(query=query, task_id=task_id, task_title=task_title, task_reward_tokens=task_reward_tokens, task_game_attempts=task_game_attempts)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tasks Check: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tasks Check: {str(error)} ]{Style.RESET_ALL}")

    async def tasks_claim(self, query: str, task_id: int, task_title: str, task_reward_tokens: int, task_game_attempts: int):
        url = 'https://tonclayton.fun/api/tasks/claim'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_tasks_claim = await response.json()
                        if error_tasks_claim['error'] == 'reward already claimed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Claimed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tasks_claim = await response.json()
                    if tasks_claim['message'] == 'Reward claimed':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {task_reward_tokens} Clayton Points & {task_game_attempts} Ticket From {task_title} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tasks Claim: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tasks Claim: {str(error)} ]{Style.RESET_ALL}")

    async def user_achievements_get(self, query: str):
        url = 'https://tonclayton.fun/api/user/achievements/get'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    user_achievements_get = await response.json()
                    for achievement_type, achievements in user_achievements_get.items():
                        if achievement_type in ["friends", "games", "stars"]:
                            for achievement in achievements:
                                if achievement['is_completed'] and not achievement['is_rewarded']:
                                    level = achievement['level']
                                    reward_amount = achievement['reward_amount']
                                    await self.user_achievements_claim(query, achievement_type, str(level), reward_amount)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While User Achievements Get: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While User Achievements Get: {str(error)} ]{Style.RESET_ALL}")

    async def user_achievements_claim(self, query: str, type: str, level: str, reward_amount: int):
        url = f'https://tonclayton.fun/api/user/achievements/claim/{type}/{level}'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 500:
                        error_user_achievements_claim = await response.json()
                        if error_user_achievements_claim['error'] == 'reward already claimed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Achievements {type} Level {level} Already Claimed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {reward_amount} Token From Achievements {type} Level {level} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While User Achievements Claim: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While User Achievements Claim: {str(error)} ]{Style.RESET_ALL}")

    async def stack_start(self, query: str):
        url = 'https://tonclayton.fun/api/stack/st-game'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, ssl=False) as response:
                        if response.status == 500:
                            error_user_achievements_claim = await response.json()
                            if error_user_achievements_claim['error'] == 'no daily attempts left':
                                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Stack Attempts Available ]{Style.RESET_ALL}")
                        response.raise_for_status()
                        stack_start = await response.json()
                        if 'session_id' in stack_start:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Stack Started With Session ID: {stack_start['session_id']} ]{Style.RESET_ALL}")
                            score = 10
                            while score <= 100:
                                await self.stack_update(query=query, score=score)
                                await asyncio.sleep(3)
                                score += 10
            except ClientResponseError as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Stack Start: {str(error)} ]{Style.RESET_ALL}")
            except Exception as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Stack Start: {str(error)} ]{Style.RESET_ALL}")

    async def stack_update(self, query: str, score: int):
        url = 'https://tonclayton.fun/api/stack/update-game'
        data = json.dumps({'score':score})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 500:
                        error_stack_update = await response.json()
                        if error_stack_update['error'] == 'score change error':
                            return await self.stack_end(query=query, score=score)
                    response.raise_for_status()
                    stack_update = await response.json()
                    if stack_update['message'] == 'Score updated successfully':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Successfully Updated Stack Score {score} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Stack Update: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Stack Update: {str(error)} ]{Style.RESET_ALL}")

    async def stack_end(self, query: str, score: int):
        url = 'https://tonclayton.fun/api/stack/en-game'
        data = json.dumps({'score':score,'multiplier':1})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 500:
                        error_stack_end = await response.json()
                        if error_stack_end['error'] == 'redis: nil':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Error Redis: Nil While Stack End ]{Style.RESET_ALL}")
                        elif error_stack_end['error'] == 'Internal Server Error':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Internal Server Error While Stack End ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    stack_end = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {stack_end['earn']} Clayton Points & {stack_end['xp_earned']} XP From Stack ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Stack End: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Stack End: {str(error)} ]{Style.RESET_ALL}")

    async def tile_start(self, query: str):
        url = 'https://tonclayton.fun/api/game/start'
        data = json.dumps({'score':score,'multiplier':1})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        if response.status == 409:
                            error_tile_start = await response.json()
                            if error_tile_start['error'] == 'An active game session already exists':
                                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Active Game Session Already Exists While Tile Start ]{Style.RESET_ALL}")
                        elif response.status == 500:
                            error_tile_start = await response.json()
                            if error_tile_start['error'] == 'No game attempts available':
                                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No 1024 Attempts Available ]{Style.RESET_ALL}")
                        response.raise_for_status()
                        tile_start = await response.json()
                        if tile_start['message'] == 'Game started successfully':
                            await self.tile_save(query=query)
                            await asyncio.sleep(2)
            except ClientResponseError as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tile Start: {str(error)} ]{Style.RESET_ALL}")
            except Exception as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tile Start: {str(error)} ]{Style.RESET_ALL}")

    async def tile_save(self, query: str):
        url = 'https://tonclayton.fun/api/game/save-tile'
        data = json.dumps({'maxTile':1024})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 500:
                        error_stack_end = await response.json()
                        if error_stack_end['error'] == 'redis: nil':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Error Redis: Nil While Tile Save ]{Style.RESET_ALL}")
                        elif error_stack_end['error'] == 'Internal Server Error':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Internal Server Error While Tile Save ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tile_save = await response.json()
                    if tile_save['message'] == 'MaxTile saved successfully':
                        return await self.tile_over(query=query)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tile Save: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tile Save: {str(error)} ]{Style.RESET_ALL}")

    async def tile_over(self, query: str):
        url = 'https://tonclayton.fun/api/game/over'
        data = json.dumps({'multiplier':1})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 500:
                        error_tile_over = await response.json()
                        if error_tile_over['error'] == 'redis: nil':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Error Redis: Nil While Tile Over ]{Style.RESET_ALL}")
                        elif error_tile_over['error'] == 'Internal Server Error':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Internal Server Error While Tile Over ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tile_over = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {tile_over['earn']} Clayton Points & {tile_over['xp_earned']} XP From 1024 ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tile Over: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tile Over: {str(error)} ]{Style.RESET_ALL}")

    async def main(self):
        while True:
            try:
                sessions = [file for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions:
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder. ]{Style.RESET_ALL}")
                accounts = await self.generate_queries(sessions)

                for (name, query) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.authorization(query=query)
                    await self.user_daily_claim(query=query)

                for (name, query) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Earn ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    for type in ['super-tasks', 'partner-tasks', 'default-tasks', 'daily-tasks']:
                        tasks = await self.tasks(query=query, type=type)
                        if tasks is not None:
                            for task in tasks:
                                if task['is_completed'] and not task['is_claimed']:
                                    await self.tasks_claim(query=query, task_id=task['task_id'], task_title=task['task']['title'], task_reward_tokens=task['task']['reward_tokens'], task_game_attempts=task['task']['game_attempts'])
                                if not task['is_completed']:
                                    if task['task']['requires_check']:
                                        await self.tasks_check(query=query, task_id=task['task_id'], task_title=task['task']['title'], task_reward_tokens=task['task']['reward_tokens'], task_game_attempts=task['task']['game_attempts'])
                                    else:
                                        await self.tasks_complete(query=query, task_id=task['task_id'], task_title=task['task']['title'], task_reward_tokens=task['task']['reward_tokens'], task_game_attempts=task['task']['game_attempts'])
                    await self.user_achievements_get(query=query)

                for (name, query) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Games ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    if self.games == '1024':
                        await self.tile_start(query=query)
                    elif self.games == 'stack':
                        await self.stack_start(query=query)

                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=(3 * 3600))).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(3 * 3600)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        init(autoreset=True)

        clayton = Clayton()
        asyncio.run(clayton.main())
    except (ValueError, IndexError, FileNotFoundError) as e:
        clayton.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)