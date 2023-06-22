import os
import discord
import random
from collections import defaultdict
from dotenv import load_dotenv
from discord.ext import commands, menus
from datetime import datetime
from keep_alive import keep_alive
from table2ascii import table2ascii as t2a, PresetStyle
import math
import threading


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
channel_ids = [1063152988283220038, 1063162460883914882]


def parse_line(line: str):
    try:
        parts = line.split(" ")
        date = parts[0]
        player = parts[2]
        action = parts[3]
        amount = int(parts[4])
        if parts[6] == "for":
            item = parts[5]
            price = float(parts[7])
            recipient = parts[9]
            location = parts[11]
        elif parts[8] == "for":
            item = parts[5] + " " + parts[6] + " " + parts[7]
            price = float(parts[9])
            recipient = parts[11]
            location = parts[13]
        else:
            item = parts[5] + " " + parts[6]
            price = float(parts[8])
            recipient = parts[10]
            location = parts[12]
        return {
            "date": date,
            "player": player,
            "action": action,
            "item": item,
            "amount": amount,
            "price": price,
            "recipient": recipient,
            "location": location
        }
    except Exception as e:
        return None


def compute_prices(logs):
    if not logs:
        return 0
    prices = [log["price"] for log in logs]
    return prices


def compute_amounts(logs):
    if not logs:
        return 0
    amounts = [log["amount"] for log in logs]
    return amounts


async def monthly_prices(ctx, item, filtered_parsed_logs):
    monthly_prices = []
    months = [
        "August", "September", "October", "November", "December", 
"January"
    ]
    for i in range(6):
        filter = filter_logs(filtered_parsed_logs, months[i], item)
        prices = compute_prices(filter)
        amounts = compute_amounts(filter)
        median_transaction = compute_median_transaction(prices, amounts)
        price = median_transaction['price']
        amount = median_transaction['amount']
        await ctx.channel.send(
            f'In {months[i]} the median price was: {price} kr')
        monthly_prices.append(amount / price)
    return monthly_prices


def total_tax_paid_in_month(file_name: str, month: str):
    with open(file_name, 'r') as f:
        logs = f.readlines()
    month_tax = 0
    logs = [log for log in logs if log is not None]
    for log in logs:
        if "Applied a tax of" in log and "percent" in log and "to the 
received amount" in log:
            date_string = log.split(" ")[0]
            date_object = datetime.strptime(date_string, '%Y/%m/%d')
            if date_object.strftime("%B") == month:
                try:
                    tax = float(
                        log.split(" ")[8].replace('(', '').replace(')', 
''))
                    month_tax += tax
                except ValueError:
                    continue
    return month_tax


def compute_median_transaction(prices, amounts):
    transactions = list(zip(prices, amounts))
    transactions.sort(key=lambda x: x[0])

    median_index = len(transactions) // 2
    median_index = int(round(median_index))

    if len(transactions) % 2 == 0:
        median_price = (transactions[median_index - 1][0] +
                        transactions[median_index][0]) / 2
        median_amount = (transactions[median_index - 1][1] +
                         transactions[median_index][1]) / 2
    else:
        median_price = transactions[median_index][0]
        median_amount = transactions[median_index][1]

    return {'price': median_price, 'amount': median_amount}


def average_prices(logs):
    if not logs:
        return 0
    prices = [log["price"] for log in logs]
    return sum(prices) / len(prices)


def parse_item_name(element: str):
    element = element.title()
    items = {
        'Fine Beer': 'Potion#1JI',
        'Orange Cake': 'Player Head#1qx',
        'Short Range Rocket': 'Firework Rocket#a2',
        'Medium Range Rocket': 'Firework Rocket#Cc',
        'Long Range Rocket': 'Firework Rocket#bV',
        'Ruined Potion': 'Potion#29X',
        'Golden Mead': 'Potion#O7',
        'Whiskey': 'Potion#1rg',
        'Russian Vodka': 'Potion#1rA',
        'Vodka': 'Potion#1U4',
        'Spicy Rum': 'Potion#1ub',
        'Strong Absinthe': 'Strong Absinthe',
        'Fine Wheatbeer': 'Potion#O4',
        'Sweet Golden Apple Mead': 'Potion#17b',
        'Gin': 'Potion#1sv',
        'Mulled Wine': 'Potion#1rh',
        'Lemonade': 'Potion#1rd',
        'Trick Or Treat!': 'Player Head#26B',
        'Mending': 'Enchanted Book#eQ',
        'Super Pickaxe': 'Netherite Pickaxe:112#29Z',
        'Fuel': 'Player Head:3#uR',
        'White Car': 'Chest#2a2',
        'Black Car': 'Chest#2a3',
        'Parachute': 'Chest#2a4',
        'Haste And Luck': 'Potion#eV',
        'Region Checker': 'Wooden Shovel#2a5',
        'Coca-Cola': 'Player Head#22N',
        'Coca Cola': 'Player Head#22N',
        'Fries': 'Player Head#1qy',
        'Pepsi': 'Player Head:3#1qD',
        'Tea': 'Player Head:1#1uc',
        'Pancakes': 'Player Head#1qE',
        'Beef Taco': 'Player Head:1#1qF',
        'Iced Coffee': 'Player Head:3#1r9',
        'Pepperoni Pizza': 'Player Head#1Pk',
        'Coffee': 'Player Head:1#1qS',
        'Espresso': 'Player Head:1#1wp'
    }
    if element in items:
        return items[element]
    else:
        words = element.split(" ")
        if len(words) == 1:
            return element.capitalize()
        elif len(words) == 2:
            return words[0].capitalize() + " " + words[1][0].upper(
            ) + words[1][1:]
        elif len(words) == 3:
            return " ".join([word.capitalize() for word in words])


def filter_logs(logs, month, item):
    # List to store the filtered logs
    filtered_logs = []

    for log in logs:
        try:
            date = datetime.strptime(log["date"], "%Y/%m/%d")
        except Exception as e:
            print(f'Line causing error: {log["date"]}')
            print(f'Exception is {e}')
        if item != None:
            if date.strftime("%B") == month and log["item"] == item:
                filtered_logs.append(log)
        else:
            if date.strftime("%B") == month:
                filtered_logs.append(log)
    return filtered_logs


def most_sold_items_by_player(logs, player, amount):
    # Create a dictionary to store the item counts
    item_counts = defaultdict(int)

    # Iterate over the logs
    for log in logs:
        if log["recipient"] == player and log["action"] == "bought":
            item_counts[log["item"]] += log["amount"]

    # Sort the dictionary by value in descending order
    sorted_item_counts = sorted(item_counts.items(),
                                key=lambda x: x[1],
                                reverse=True)

    # Return the top 10 items with the most count
    return sorted_item_counts[:amount]


def most_sold_items_table(logs, player, amount):
    item_counts = most_sold_items_by_player(logs, player, amount)
    header = ["Item", "Amount"]
    body = [[item[0], item[1]] for item in item_counts]
    return t2a(header=header, body=body, first_col_heading=True)


def most_sold_items_by_month(logs, month, top_n=10):
    item_counts = defaultdict(int)
    for log in logs:
        try:
            date = datetime.strptime(log["date"], "%Y/%m/%d")
        except ValueError as e:
            print(f'Line causing error: {log["date"]}')
            print(f'Error: {e}')
            continue
        if date.strftime("%B") == month:
            item_counts[log["item"]] += log["amount"]
    sorted_item_counts = sorted(item_counts.items(),
                                key=lambda x: x[1],
                                reverse=True)
    return sorted_item_counts[:top_n]


async def most_sold_items_table_pagination(ctx, logs, player, amount):
    item_counts = most_sold_items_by_player(logs, player, int(amount))
    num_pages = math.ceil(len(item_counts) / 25)
    current_page = 1
    while current_page <= num_pages:
        items = item_counts[(current_page - 1) * 25:current_page * 25]
        embed = discord.Embed(
            title=
            f"Most Sold Items by {player} (page 
{current_page}/{num_pages})")
        for item, amount in items:
            embed.add_field(name=item, value=amount, inline=True)
        await ctx.send(embed=embed, delete_after=20.0)
        msg = await ctx.send(
            "Type `next` to see the next page or `exit` to stop.",
            delete_after=20.0)
        response = None
        while response != "next" and response != "exit":
            response = (await bot.wait_for(
                "message",
                check=lambda m: m.content in ["next", "exit"])).content
        if response == "exit":
            await clear(ctx, 1)
            break
        await clear(ctx, 1)
        current_page += 1


@bot.command()
async def price(ctx, *, arg):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]
            item = parse_item_name(arg)
        item_logs = [
            log for log in filtered_parsed_logs
            if log["item"] == item and log["action"] == "bought"
        ]
        if (len(item_logs) == 0):
            await ctx.channel.send('This item has never been sold 
before.',
                                   delete_after=20.0)
            return
        prices = compute_prices(item_logs)
        amounts = compute_amounts(item_logs)
        median_transaction = compute_median_transaction(prices, amounts)
        await ctx.channel.send(
            f"The median transaction is {median_transaction['price']} kr 
per {median_transaction['amount']} {parse_item_name(item)}",
            delete_after=20.0)
        await ctx.channel.send('\u200b', delete_after=20.0)
        await ctx.channel.send(
            f'Average price per stack: {round((sum(prices) / sum(amounts)) 
* 64, 2)} Krunas',
            delete_after=20.0)
        await ctx.channel.send(
            f'Average price per item: {round(sum(prices) / sum(amounts), 
2)} Krunas',
            delete_after=20.0)
        await ctx.channel.send(
            f'Average transaction: {round(average_prices(item_logs), 2)} 
Krunas',
            delete_after=20.0)


@bot.command()
async def inspect(ctx, *args):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]

        item = parse_item_name(' '.join(args[:-1]))

        item_logs = [
            log for log in filtered_parsed_logs
            if log["item"] == item and log["action"] == "bought"
        ]

        if (len(item_logs) == 0):
            await ctx.channel.send('This item has never been sold 
before.',
                                   delete_after=20.0)
            return
        await ctx.channel.send(
            f'The entire market volume until now logged is: 
{round(sum(compute_prices(filtered_parsed_logs)), 4):,} Krunas',
            delete_after=20.0)
        prices = compute_prices(item_logs)
        await ctx.channel.send(
            f'Of that, the trade volume of {item} was {round(sum(prices), 
2):,} Krunas',
            delete_after=20.0)
        await ctx.channel.send('\u200b', delete_after=20.0)
        item_filter = filter_logs(filtered_parsed_logs,
                                  str.capitalize(args[-1]), None)
        prices = compute_prices(item_filter)
        await ctx.channel.send(
            f'The trade volume in {str.capitalize(args[-1])} was: 
{round(sum(prices), 2):,} Krunas',
            delete_after=20.0)
        item_filter = filter_logs(filtered_parsed_logs,
                                  str.capitalize(args[-1]), item)
        if item_filter:
            _prices = compute_prices(item_filter)
            await ctx.channel.send(
                f'Of that, the trade volume of {item} was 
{round(sum(_prices), 2):,} Krunas',
                delete_after=20.0)
        else:
            await ctx.channel.send(
                f'Of that, the trade volume of {item} was 0.00 Krunas',
                delete_after=20.0)


async def clear(ctx, amount: int = 1000000):
    await ctx.channel.purge(limit=1)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 1000000):
    if ctx.author.id == 402242971656781855:
        await ctx.channel.purge(limit=amount)
    else:
        await ctx.send("You are not authorized to use this command.")
        return


@bot.command()
async def history(ctx, *args):

    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        monthly_median_prices = []
        average_monthly_prices = []
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]
        item = parse_item_name(' '.join(args))
        item_logs = [
            log for log in filtered_parsed_logs
            if log["item"] == item and log["action"] == "bought"
        ]
        if (len(item_logs) == 0):
            await ctx.channel.send('This item has never been sold 
before.',
                                   delete_after=20.0)
            return
        months = [
            "August", "September", "October", "November", "December", 
"January"
        ]
        await ctx.channel.send(
            'Please, wait a few seconds while I parse the logs...')
        for i in range(6):
            filter = filter_logs(filtered_parsed_logs, months[i], item)
            prices = compute_prices(filter)
            amounts = compute_amounts(filter)
            #average = average_prices(prices)
            median_transaction = compute_median_transaction(prices, 
amounts)
            price = median_transaction['price']
            amount = median_transaction['amount']
            monthly_median_prices.append(price)
            average_monthly_prices.append(round(sum(prices) / 
sum(amounts), 2))

        output = t2a(
            header=[
                f"{item}", "August", "September", "October", "November",
                "December", "January"
            ],
            body=[[
                "Median", monthly_median_prices[0], 
monthly_median_prices[1],
                monthly_median_prices[2], monthly_median_prices[3],
                monthly_median_prices[4], monthly_median_prices[5]
            ],
                  [
                      "Average", average_monthly_prices[0],
                      average_monthly_prices[1], 
average_monthly_prices[2],
                      average_monthly_prices[3], 
average_monthly_prices[4],
                      average_monthly_prices[5]
                  ]],
            first_col_heading=True)
        await clear(ctx, 1)
        await ctx.send(f"```\n{output}\n```", delete_after=20.0)


@bot.command()
async def player_table(ctx, username, amount):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]


#    items_list = most_sold_items_by_player(filtered_parsed_logs, 
username)
#    for item in items_list:
#      await ctx.send(f'{username} has sold {item[1]} {item[0]}')
        await ctx.send(
            f"```\n{most_sold_items_table(filtered_parsed_logs, username, 
int(amount))}\n```",
            delete_after=20.0)


@bot.command()
async def player(ctx, username, amount=10, month=None):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        if username.islower() or username.isupper():
            username = username.capitalize()
        if month != None:
            await player_month(ctx, username, int(amount), month)
            return
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]
            username_filter = [
                log for log in filtered_parsed_logs
                if log['recipient'] == username and log['action'] == 
'bought'
            ]
        if len(username_filter) == 0:
            await ctx.send(
                f'{username} has never sold anything on the server.',
                delete_after=20.0)
            return
        await ctx.send(
            f'{username} has had {len(username_filter)} transactions on 
the server.',
            delete_after=20.0)
        if int(amount) > len(username_filter):
            await most_sold_items_table_pagination(ctx, 
filtered_parsed_logs,
                                                   username,
                                                   len(username_filter))
        else:
            await most_sold_items_table_pagination(ctx, 
filtered_parsed_logs,
                                                   username, int(amount))


@bot.command()
async def player_month(ctx, username, amount, month):
    if ctx.channel.id in channel_ids:
        month = str.capitalize(month)
        with open('logs.txt', 'r') as file:
            parsed_logs = [parse_line(line) for line in file]
            filtered_parsed_logs = [
                log for log in parsed_logs if log is not None
            ]
            username_filter = [
                log for log in filtered_parsed_logs
                if log['recipient'] == username
                and log['action'] == 'bought' and datetime.strptime(
                    log['date'], '%Y/%m/%d').strftime("%B") == month
            ]
        await ctx.send(
            f'In {month} the most sold items by {str.capitalize(username)} 
were:',
            delete_after=20.0)
        await most_sold_items_table_pagination(ctx, username_filter, 
username,
                                               int(amount))


@bot.command()
async def tax(ctx, month):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        month = month.capitalize()
        await ctx.send(
            f"ChestShop Tax in {month} was: 
{round(total_tax_paid_in_month('logs.txt', month), 2):,} Krunas",
            delete_after=20.0)


@bot.command()
async def commands(ctx):
    await clear(ctx, 1)
    if ctx.channel.id in channel_ids:
        await ctx.send(
            "The arguments in <> are required.\nThe arguments in [] are 
optional.",
            delete_after=20.0)
        header = ["Command:", "Description:"]
        body = [["price <item>", "Shows the price of a given item."],
                ["history <item>", "Shows the price history of a given 
item."],
                [
                    "inspect <item> [month]",
                    "Shows the trade volume of a given item."
                ],
                [
                    "player <player> [n_items] [month]",
                    "Shows the most sold items by a player."
                ],
                [
                    "player_table <player> <n_items>",
                    "Shows the most sold items by a player."
                ],
                ["tax <month>", "Shows the ChestShop tax in a given 
month."]]

        body = [[i[0].ljust(50), i[1]] for i in body]
        table = t2a(header=header, body=body, first_col_heading=True)
        await ctx.send("```\n" + table + "\n```", delete_after=20.0)


@bot.command()
async def parse(ctx, *, arg):
    await clear(ctx, 1)
    await ctx.send(f'`ID of {arg.title()} is: {parse_item_name(arg)}`')


@bot.command()
async def math(ctx, *, arg):
    await clear(ctx, 1)
    await ctx.send(f'{round(eval(arg), 2):,}', delete_after=5.0)


@bot.event
async def on_command_error(ctx, error):
    await ctx.send("Invalid command. Type !commands for a list of 
commands.", delete_after=5.0)


############### PRUNING STUFF #################


class RequestPruning(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        return await channel.send(
            "Please fill out the form to request pruning.")

    @menus.button("Username")
    async def on_username(self, payload):
        pass

    @menus.button("/bcseen")
    async def on_bcseen(self, payload):
        pass

    @menus.button("/seen")
    async def on_seen(self, payload):
        pass


@bot.event
async def on_ready():
    print("I'm in")
    bot.menu = RequestPruning()
    print(bot.user)

@bot.command()
async def prune(ctx, username, bcseen, *args):
    channel_id = 1025489764373254154
    embed = discord.Embed(title="Pruning Request", color=0x00ff00)
    embed.add_field(name="Username", value=username)
    embed.add_field(name="/bcseen", value=bcseen)
    embed.add_field(name="/seen", value=" ".join(args))
    embed.add_field(name="Note", value=f"@Sr. Analyst - Use 
commands:\n/prune <username> if /seen and /bcseen are not met\n/bankprune 
<username> if bank balance > 50,000kr\n\nRequested by {ctx.author.name} on 
{datetime.now().strftime('%Y/%m/%d')}", inline=False)
    embed.set_footer(text="Click the reaction to submit the request")
    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "✅"
    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, 
check=check)
    except TimeoutError:
        await message.delete()
        await ctx.send("Time out.", delete_after=5.0)
    else:
        await message.delete()
        await clear(ctx, 2)
        channel = bot.get_channel(channel_id)
        mention_message = await channel.send(f"<@986835311499816960>")
        new_message = await channel.send(embed=embed)
        event_thread = threading.Thread(target=on_reaction_add, 
args=(reaction, user, new_message, username, channel, mention_message))
        event_thread.start()
        await ctx.send("Your request has been sent.", delete_after=10.0)

@bot.event
async def on_reaction_add(reaction, user, new_message, username, channel, 
mention_message):
    username, mention_message, channel, new_message = await queue.get()
    message_reaction_map = {}
    message_reaction_map[new_message.id] = {"👍": "approved", "❌": 
"declined"}

    if reaction.message.id in message_reaction_map and str(reaction.emoji) 
in message_reaction_map[reaction.message.id]:
        if discord.utils.get(user.roles, name="Sr. Analyst"):
            action = 
message_reaction_map[reaction.message.id][str(reaction.emoji)]
            await new_message.delete()
            if action == "approved":
                await channel.send(f"`{user}` has pruned `{username}` on 
date `{datetime.now().strftime('%Y/%m/%d')}`")
                await mention_message.delete()
            elif action == "declined":
                await channel.send(f"`{username}` could not be pruned by 
`{user}`")
                await mention_message.delete()
        else:
            await channel.send("You are not authorized to approve or 
decline requests.", delete_after=5.0)


TOKEN = os.environ['DISCORD_BOT_SECRET']

bot.run(TOKEN)
bot.add_listener(on_reaction_add, "on_reaction_add")

