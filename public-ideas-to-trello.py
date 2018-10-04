import asyncio
import json
import trello
import os
import discord
import traceback
from discord.ext.commands import Bot
from datetime import datetime, timedelta

config = {
    'discord_token': "Put Discord API Token here.",
    'trello_api_key': "Put Trello API key here",
    'trello_list_id': "Put the ID of the Trello list that new cards should be created in here",
    'discord_channel_id': "Put the ID of the Discord channel you want to get public ideas from here",
    'discord_reactions_message': [
        "Put the channel ID of the message with all the reactions you want to purge here",
        "Put the ID of the message with all the reactions you want to purge here"
    ],
    'rule_reminder_message': [
        'Put the channel ID of the message you want to be sent to remind people of the rules here',
        'Put the ID of the message you want to be sent to remind people of the rules here'
    ],
    'trello_api_secret': "Put your Trello secret here",
    'trello_token': "Insert your Trello token here"
}

config_file = 'config.json'

if os.path.isfile(config_file):
    with open(config_file) as f:
        config.update(json.load(f))

with open('config.json', 'w') as f:
    json.dump(config, f, indent='\t')

bot = Bot(command_prefix='t!')
bot.rules_message = None
bot.purge_reactions = None

trellobot = trello.TrelloClient(
    api_key=config['trello_api_key'],
    api_secret=config['trello_api_secret'],
    token=config['trello_token']
)


async def description_reminder(ctx):
    authors = []
    async for message in ctx.channel.history(limit=20):
        authors.append(message.author)
    if bot.user not in authors:
        await ctx.channel.send(bot.rules_message)


@bot.event
async def on_ready():
    try:
        rule_reminder_channel, rule_reminder_message = config['rule_reminder_message']
        bot.rules_message = (await bot.get_channel(rule_reminder_channel).get_message(rule_reminder_message)).content
        purge_reactions_channel, purge_reactions_message = config['discord_reactions_message']
        bot.purge_reactions = (await bot.get_channel(purge_reactions_channel).get_message(purge_reactions_message)).content
    except discord.DiscordException:
        print("Error retrieving rules and reactions messages")
        traceback.print_exc()
        await bot.logout()
        raise
    else:
        print("Ready!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.channel.id == config['discord_channel_id']:
        author_info = "{}#{} ({})".format(message.author.name, message.author.discriminator, message.author.id)
        idea = message.clean_content
        trellobot.get_list(config['trello_list_id']).add_card(idea, author_info)
        await description_reminder(message)
        await message.add_reaction('\N{SQUARED OK}')


@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if str(before.channel.id) == config['discord_channel_id']:
        card = trellobot.search(before.content)[0]
        print(card)
        card.set_name(after.content)


@bot.command()
async def testtrellosearch(ctx, what_to_search_for):
    await ctx.send(trellobot.search(what_to_search_for))


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def purge(ctx):
    await ctx.send("Purging")
    channel = ctx.guild.get_channel(config['discord_channel_id'])
    print(config['discord_reactions_message'])
    messages = [m async for m in channel.history(limit=None) if any(str(r.emoji) in bot.purge_reactions for r in m.reactions)]
    bulk_cutoff = datetime.utcnow() - timedelta(days=14)
    bulk_delete = [m for m in messages if m.created_at >= bulk_cutoff]
    single_delete = [m for m in messages if m.created_at < bulk_cutoff]
    coros = [channel.delete_messages(bulk_delete[i:i + 100]) for i in range(0, len(bulk_delete), 100)]
    coros.extend(m.delete() for m in single_delete)
    return len(bulk_delete), len(single_delete), len(coros)


bot.run(config['discord_token'])
