#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests
import argparse


def isfloat(x):
    try:
        float(x)
        return True
    except:
        return False

commands = [
    'exit',
    'get_foodlist',
    'add_to_my_food',
    'actual_intake',
    'print_my_food',
    'add_new_food',
    'search_food',
]

line = {}
line[commands[0]] = 'Complete the work with the client'
line[commands[1]] = 'Receive a list of your possible food'
line[commands[2]] = 'Add this product to your meal'
line[commands[3]] = 'Receive a nutrient intake summary'
line[commands[4]] = 'Receive a list of your meal'
line[commands[5]] = 'Add a new product in the database of possible food'
line[commands[6]] = 'Finding food for the substring'

help_text = """
List of commands

№    Name                Description
"""
for i in range(len(commands)):
    help_text += '%-5s%-20s%-20s\n' % (str(i), commands[i], line[commands[i]])


def get_name():
    while 1:
        name = input('Enter the name of the food\n>>> ').strip().lower()
        if name in ('exit', 'quit'):
            exit()
        elif name in ('cancel', ''):
            return print('Request was cancelling')
        elif name[0].isdigit():
            print('The name must start with a letter')
        else:
            break
    return name.capitalize()


def command2():
    name = get_name()
    if name is None:
        return
    while 1:
        output = 'Enter the weight of the food in grams\n>>> '
        weight = input(output).strip().lower()
        if isfloat(weight):
            break
        elif weight in ('exit', 'quit'):
            exit()
        elif weight == 'cancel':
            return print('Request was cancelling')
        else:
            print('Sorry, weight must be a number')
    params = {'name': name, 'weight': float(weight)}
    res = requests.post(address + '/add_to_my_food', params).json()
    if res is not None:
        print('Ok, ' + res + ' was added in your meal')
    else:
        print('Sorry, ' + name + ' not found in base')


def command5():
    name = get_name()
    if name is None:
        return
    params = {'name': name, 'params': {}}
    all_params = requests.get(address + '/get_all_params').json()
    print('Enter the product data per 100 grams')
    for nutr_name, unit in all_params:
        output = 'Enter the amount of {} in {}\n>>> '.format(nutr_name, unit)
        cur_val = input(output).strip()
        if cur_val in ('exit', 'quit'):
            exit()
        elif cur_val == 'cancel':
            return print('Request was cancelling')
        if isfloat(cur_val):
            params['params'][nutr_name] = float(cur_val)
    params['params'] = str(params['params'])
    requests.post(address + '/add_new_food', params)
    print('Ok, ' + name + ' was added in base')


def command6():
    name = input('Enter the substring for searching\n>>> ').strip()
    if name == 'cancel':
        return print('Request was cancelling')
    params = {'name': name}
    list_lines = requests.get(address + '/search_food', params).json()
    print('\n'.join(list_lines))


def query(input_query):
    s = input_query.strip().split()
    if len(s) == 0:
        return
    command = s[0].lower()
    if command == 'help':
        print(help_text)
    elif command in ('exit', 'quit', '0'):
        exit()
    elif command == commands[1] or command == '1':
        res = requests.get(address + '/get_foodlist').json()
        print(res)
    elif command == commands[2] or command == '2':
        command2()
    elif command == commands[3] or command == '3':
        res = requests.get(address + '/actual_intake').json()
        print(res)
    elif command == commands[4] or command == '4':
        res = requests.get(address + '/print_my_food').json()
        print(res)
    elif command == commands[5] or command == '5':
        command5()
    elif command == commands[6] or command == '6':
        command6()
    else:
        print(command + ' is unknown command')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-address', default='127.0.0.1', type=str)
    parser.add_argument('--port', default=80, type=int)
    args = parser.parse_args()
    address = 'http://{}:{}'.format(args.server_address, args.port)

    print("""
Welcome to client of FoodCounterApp!
You can enter 'help' to find out information about possible commands.""")

    while 1:
        query(input('\n>>> ').strip())
