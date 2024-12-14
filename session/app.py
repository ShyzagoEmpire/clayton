from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from config import settings
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
from urllib.parse import parse_qs, unquote
import asyncio, json, os, random, sys

class Clayton:
    def __init__(self) -> None:
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'tonclayton.fun',
            'Origin': 'https://tonclayton.fun',
            'Referer': 'https://tonclayton.fun/games',
            'Pragma': 'no-cache',
            'Priority': 'u=3, i',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': FakeUserAgent().random
        }
        self.semaphore = asyncio.Semaphore(100)

    @staticmethod
    def clear_terminal():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_timestamp(message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            async with TelegramClient(
                session=f'sessions/{session}',
                api_id=settings.API_ID,
                api_hash=settings.API_HASH
            ) as client:
                try:
                    if not client.is_connected(): await client.connect()
                except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedBanError, UserDeactivatedError) as error:
                    raise error

                me = await client.me()
                name = me.username if me.username is not None else me.first_name

                webapp_response: AppWebViewResultUrl = await client(messages.RequestAppWebViewRequest(
                    peer=settings.MINIAPP_USERNAME,
                    app=InputBotAppShortName(bot_id=await client.get_input_entity(settings.MINIAPP_USERNAME), short_name='game'),
                    platform='ios',
                    write_allowed=True,
                    start_param=settings.REFERRAL
                ))
                query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

                if client.is_connected(): await client.disconnect()

                return query, name
        except Exception as err:
            await client.disconnect()
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(err)} ]{Style.RESET_ALL}")
            return None

    async def generate_query_with_semaphore(self, session):
        async with self.semaphore:
            return await self.generate_query(session)

    async def generate_queries(self, sessions):
        tasks = [self.generate_query_with_semaphore(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def authorization(self, query: str):
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/user/authorization',
                    headers=headers,
                    raise_for_status=True
                ) as response:
                    authorization = await response.json()
                    if authorization['dailyReward']['can_claim_today'] and authorization['dailyReward']['is_subscribed']:
                        await self.user_daily_claim(query=query)
                    self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Is Premium Telegram {str(authorization['user']['is_premium'])} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Referral To {authorization['user']['start_param']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Has OG Pass {str(authorization['user']['has_og_pass'])} ]{Style.RESET_ALL}"
                    )
                    self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Level {authorization['user']['level']} And {authorization['user']['current_xp']} Experience Point ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ {authorization['user']['tokens']} $CLAY ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Consecutive Days {authorization['user']['consecutive_days']} ]{Style.RESET_ALL}"
                    )
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ {authorization['user']['daily_attempts']} Game Tickets ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ {authorization['user']['free_spins']} Free Spins And {authorization['user']['paid_spins']} Paid Spins ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Wallet {authorization['user']['wallet']} ]{Style.RESET_ALL}"
                    )
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Authorization: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Authorization: {str(error)} ]{Style.RESET_ALL}")

    async def user_daily_claim(self, query: str):
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/user/daily-claim',
                    headers=headers
                ) as response:
                    if response.status == 400:
                        error_user_daily_claim = await response.json()
                        if error_user_daily_claim['error'] == 'daily reward already claimed today':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Daily Reward Already Claimed Today ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    user_daily_claim = await response.json()
                    if user_daily_claim['message'] == 'Daily reward claimed successfully':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {user_daily_claim['tokens']} $CLAY From Daily Reward ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError User Daily Claim: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception User Daily Claim: {str(error)} ]{Style.RESET_ALL}")

    async def tasks(self, query: str, type: str):
        headers = {
            **self.headers,
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(
                    url=f'{settings.END_POINT}/tasks/{type}',
                    headers=headers,
                    raise_for_status=True
                ) as response: return await response.json()
        except ClientResponseError as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Tasks: {str(error.message)} ]{Style.RESET_ALL}")
            return None
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Tasks: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def tasks_complete(self, query: str, task_id: int, task_title: str):
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/tasks/complete',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 400:
                        error_tasks_complete = await response.json()
                        if error_tasks_complete['error'] == 'task already completed':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Already Completed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tasks_complete = await response.json()
                    if tasks_complete['message'] == 'Task completed':
                        return await self.tasks_claim(query=query, task_id=task_id, task_title=task_title)
                    return None
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Tasks Complete: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Tasks Complete: {str(error)} ]{Style.RESET_ALL}")

    async def tasks_check(self, query: str, task_id: int, task_title: str):
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/tasks/check',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 400:
                        error_tasks_complete = await response.json()
                        if error_tasks_complete['error'] == 'task already completed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Completed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tasks_check = await response.json()
                    if not tasks_check['is_completed'] and tasks_check['message'] == 'task not completed yet':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Not Completed Yet ]{Style.RESET_ALL}")
                    return await self.tasks_claim(query=query, task_id=task_id, task_title=task_title)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Tasks Check: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Tasks Check: {str(error)} ]{Style.RESET_ALL}")

    async def tasks_claim(self, query: str, task_id: int, task_title: str):
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/tasks/claim',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 400:
                        error_tasks_claim = await response.json()
                        if error_tasks_claim['error'] == 'reward already claimed':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Claimed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    tasks_claim = await response.json()
                    if tasks_claim['message'] == 'Reward claimed':
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {tasks_claim['reward_tokens']} $CLAY And {tasks_claim['game_attempts']} Game Tickets From {task_title} ]{Style.RESET_ALL}")
                        return self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Total Game Tickets {tasks_claim['daily_attempts']} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Total $CLAY {tasks_claim['total_tokens']} ]{Style.RESET_ALL}"
                        )
                    return None
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Tasks Claim: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Tasks Claim: {str(error)} ]{Style.RESET_ALL}")

    async def user_achievements_get(self, query: str):
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/user/achievements/get',
                    headers=headers,
                    raise_for_status=True
                ) as response:
                    user_achievements_get = await response.json()
                    for achievement_type, achievements in user_achievements_get.items():
                        if achievement_type in ["friends", "games", "stars"]:
                            for achievement in achievements:
                                if achievement['is_completed'] and not achievement['is_rewarded']:
                                    level = achievement['level']
                                    reward_amount = achievement['reward_amount']
                                    await self.user_achievements_claim(query, achievement_type, str(level), reward_amount)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError User Achievements Get: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception User Achievements Get: {str(error)} ]{Style.RESET_ALL}")

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
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError User Achievements Claim: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception User Achievements Claim: {str(error)} ]{Style.RESET_ALL}")

    async def stack_start(self, query: str):
        headers = {
            **self.headers,
            'Content-Length': '0',
            'Init-Data': query
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.post(
                        url=f'{settings.END_POINT}/stack/st-game',
                        headers=headers
                    ) as response:
                        if response.status == 500:
                            error_user_achievements_claim = await response.json()
                            if error_user_achievements_claim['error'] == 'no daily attempts left':
                                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Stack Attempts Available ]{Style.RESET_ALL}")
                        response.raise_for_status()
                        stack_start = await response.json()
                        if 'session_id' in stack_start:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Stack Started With Session ID: {stack_start['session_id']} ]{Style.RESET_ALL}")
                            score = 10
                            while score <= 90:
                                await self.stack_update(query=query, score=score)
                                score += 10
            except ClientResponseError as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Stack Start: {str(error.message)} ]{Style.RESET_ALL}")
            except Exception as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Stack Start: {str(error)} ]{Style.RESET_ALL}")

    async def stack_update(self, query: str, score: int):
        data = json.dumps({'score':score})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/stack/update-game',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 500:
                        error_stack_update = await response.json()
                        if error_stack_update['error'] == 'score change error':
                            return await self.stack_end(query=query, score=score)
                    response.raise_for_status()
                    stack_update = await response.json()
                    if stack_update['message'] == 'Score updated successfully':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Successfully Updated Stack Score {score} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Stack Update: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Stack Update: {str(error)} ]{Style.RESET_ALL}")

    async def stack_end(self, query: str, score: int):
        data = json.dumps({'score':score,'multiplier':3})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Init-Data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(
                    url=f'{settings.END_POINT}/stack/en-game',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 500:
                        error_stack_end = await response.json()
                        if error_stack_end['error'] == 'redis: nil':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Error Redis: Nil While Stack End ]{Style.RESET_ALL}")
                        elif error_stack_end['error'] == 'Internal Server Error':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Internal Server Error While Stack End ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    stack_end = await response.json()
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {stack_end['earn']} $CLAY And {stack_end['xp_earned']} Experience Point From Stack ]{Style.RESET_ALL}")
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Level {stack_end['level']} And Current Experience Point {stack_end['current_xp']} ]{Style.RESET_ALL}"
                    )
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ ClientResponseError Stack End: {str(error.message)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Exception Stack End: {str(error)} ]{Style.RESET_ALL}")

    async def main(self):
        while True:
            try:
                sessions = [file for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions: raise ValueError(f"No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder")
                accounts = await self.generate_queries(sessions)

                for query, name in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.authorization(query=query)

                if settings.AUTO_TASKS:
                    for query, name in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Earn ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        for type in settings.TASKS:
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

                if settings.AUTO_GAMES_STACK:
                    for query, name in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Games ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        await self.stack_start(query=query)

                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=(3 * 3600))).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(3 * 3600)
                self.clear_terminal()
            except Exception as error:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
                pass

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        init(autoreset=True)

        clayton = Clayton()
        asyncio.run(clayton.main())
    except (ValueError, IndexError, FileNotFoundError) as error:
        clayton.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)