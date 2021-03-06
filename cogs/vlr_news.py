import os
import time
import requests
import ujson as json
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from dhooks import Webhook, Embed, File
from utils.global_utils import news_exists, matches_exists

load_dotenv()
vlr_news_webhook = os.getenv("vlr_news_webhook_url")
vlr_matches_webhook = os.getenv("vlr_matches_webhook_url")

crimson = 0xDC143C


def getVLRNews():
    URL = "https://vlrggapi.herokuapp.com/news"
    response = requests.get(URL)
    return response.json()


def getVLRMatches():
    URL = "https://vlrggapi.herokuapp.com/match/results"
    response = requests.get(URL)
    return response.json()


def updater(d, inval, outval):
    for k, v in d.items():
        if isinstance(v, dict):
            updater(d[k], inval, outval)
        else:
            if v == "":
                d[k] = None
    return d


class VLR_News(commands.Cog, name="VLR News"):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(job_defaults={"misfire_grace_time": 900})

    async def vlr_news_monitor(self):
        await self.bot.wait_until_ready()

        saved_json = "vlr_news.json"

        # call API
        responseJSON = getVLRNews()

        title = responseJSON["data"]["segments"][0]["title"]
        description = responseJSON["data"]["segments"][0]["description"]
        author = responseJSON["data"]["segments"][0]["author"]
        url = responseJSON["data"]["segments"][0]["url_path"]
        full_url = "https://www.vlr.gg" + url

        # check if file exists
        news_exists(saved_json)

        time.sleep(5)
        # open saved_json and check title string
        f = open(
            saved_json,
        )
        data = json.load(f)
        res = updater(data, "", None)
        check_file_json = res["data"]["segments"][0]["title"]

        # compare title string from file to title string from api then overwrite file
        if check_file_json == title:
            # print("True")
            return
        elif check_file_json != title:
            # print("False")
            hook = Webhook(vlr_news_webhook)
            hook.send(full_url)

            f = open(saved_json, "w")
            print(json.dumps(responseJSON), file=f)

        f.close()

    async def vlr_matches_monitor(self):
        await self.bot.wait_until_ready()

        saved_json = "./vlr_matches.json"

        # call API
        responseJSON = getVLRMatches()

        team1 = responseJSON["data"]["segments"][0]["team1"]
        team2 = responseJSON["data"]["segments"][0]["team2"]
        score1 = responseJSON["data"]["segments"][0]["score1"]
        score2 = responseJSON["data"]["segments"][0]["score2"]
        flag1 = responseJSON["data"]["segments"][0]["flag1"]
        flag2 = responseJSON["data"]["segments"][0]["flag2"]
        time_completed = responseJSON["data"]["segments"][0]["time_completed"]
        round_info = responseJSON["data"]["segments"][0]["round_info"]
        tournament_name = responseJSON["data"]["segments"][0]["tournament_name"]
        url = responseJSON["data"]["segments"][0]["match_page"]
        tournament_icon = responseJSON["data"]["segments"][0]["tournament_icon"]
        full_url = "https://www.vlr.gg" + url

        # check if file exists
        matches_exists(saved_json)

        time.sleep(5)
        # open saved_json and check title string
        f = open(
            saved_json,
        )
        data = json.load(f)
        res = updater(data, "", None)

        check_file_json = res["data"]["segments"][0]["team1"]

        # compare title string from file to title string from api then overwrite file
        if check_file_json == team1:
            # print("True")
            return
        elif check_file_json != team1:
            # print("False")
            hook = Webhook(vlr_matches_webhook)

            embed = Embed(
                title=f"**VLR Match Results**",
                description=f"**{tournament_name}**\n\n[Match page]({full_url})\n\n",
                color=crimson,
                # timestamp="now",  # sets the timestamp to current time
            )
            embed.set_footer(text=f"{round_info} | {time_completed}")
            embed.add_field(
                name=f"__Teams__",
                value=f":{flag1}: **{team1}**\n:{flag2}: **{team2}**",
                inline=True,
            )
            embed.add_field(
                name=f"__Result__", value=f"**{score1}**\n**{score2}**", inline=True
            )
            embed.set_thumbnail(url=f"{tournament_icon}")

            hook.send(embed=embed)

            f = open(saved_json, "w")
            print(json.dumps(responseJSON), file=f)

        f.close()

    @commands.Cog.listener()
    async def on_ready(self):

        scheduler = self.scheduler

        # run job every 30 minutes
        scheduler.add_job(self.vlr_news_monitor, "interval", seconds=1800)
        # run job every 10 minutes
        scheduler.add_job(self.vlr_matches_monitor, "interval", seconds=600)

        # starting the scheduler
        scheduler.start()


def setup(bot):
    bot.add_cog(VLR_News(bot))
