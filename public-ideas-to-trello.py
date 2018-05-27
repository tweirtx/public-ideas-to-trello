import json
import trello
import os
from discord.ext.commands import Bot

config = {
    'discord_token': "Put Discord API Token here.",
    'trello_api_key': "Put Trello API key here",
    'trello_list_id': "Put the ID of the Trello list that new cards should be created in here",
    'discord_channel_id': "Put the ID of the Discord channel you want to get public ideas from here",
    'trello_api_secret': "Put your Trello secret here",
    'trello_token': "Insert your Trello token here"
}

config_file = 'config.json'

if os.path.isfile(config_file):
    with open(config_file) as f:
        config.update(json.load(f))

with open('config.json', 'w') as f:
    json.dump(config, f, indent='\t')

bot = Bot(command_prefix='trello!')
trellobot = trello.TrelloClient(
    api_key=config['trello_api_key'],
    api_secret=config['trello_api_secret'],
    token=config['trello_token']
)


@bot.event
async def on_ready():
    print("Ready!")


@bot.event
async def on_message(message):
    if str(message.channel.id) == config['discord_channel_id']:
        author_info = "{}#{} ({})".format(message.author.name, message.author.discriminator, message.author.id)
        idea = message.clean_content
        trellobot.get_list(config['trello_list_id']).add_card(idea, author_info)
        await message.add_reaction('\N{SQUARED OK}')


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(config['discord_token'])
