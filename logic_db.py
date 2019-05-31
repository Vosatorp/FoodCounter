#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import *
import re
import os
import psycopg2
import requests
from collections import Counter
from time import time

PERSON_NAME = 'DEFAULT_NAME'
PERSON_ID = 1


def isfloat(x):
    try:
        float(x)
        return True
    except:
        return False

all_params = [
    ('calories', 'kcal'),
    ('carb', 'g'),
    ('fat', 'g'),
    ('protein', 'g'),
    ('fibre', 'g'),
    ('potassium', 'mg'),
    ('vitaminA', 'mcg'),
    ('vitaminC', 'mg'),
    ('calcium', 'mg'),
    ('iron', 'mg'),
    ('sodium', 'mg'),
]

fields = [key for key, _ in all_params]

get_index = {}
SHIFT = 3
for i in range(len(fields)):
    get_index[fields[i]] = i + SHIFT

# key: (mn, mx) - minimum and maximum daily value
daily_norm = {
    'protein': (56, 300),
    'fibre': (38, 100),
    'potassium': (4700, 10000),
    'vitaminA': (900, 3000),
    'vitaminC': (90, 2000),
    'calcium': (1000, 2500),
    'iron': (8, 45),
    'sodium': (1500, 2300),
    'calories': (2000, 3000),
}


def dbi():
    with psycopg2.connect(dbname=DBNAME,
                          user=USER,
                          password=PASSWORD,
                          host='127.0.0.1') as conn:
        cur = conn.cursor()
        return cur, conn


def dbe(conn):
    conn.commit()
    conn.close()


class Food:
    def __init__(self, name=None, params=Counter()):
        self.name = name
        self.params = Counter()
        for param, _ in all_params:
            if params.get(param) is not None:
                self.params[param] = params[param]
            else:
                self.params[param] = 0


class MyFood:
    def add_new_food(self, food=Food()):
        print(food.name, 'is adding')
        cur, conn = dbi()
        cur.execute('SELECT max(food_id) FROM nutrients')
        new_food_id = int(cur.fetchall()[0][0]) + 1
        query = 'INSERT INTO nutrients'
        query += '(food_id, food_name, aux_name, ' + ', '.join(fields) + ') '
        query += ''' VALUES ({}, '{}', '{}'
        '''.format(new_food_id, food.name, aux_transform(food.name))
        for key in fields:
            query += ', {}'.format(food.params[key])
        query += ')'
        print(new_food_id, query)
        cur.execute(query)
        dbe(conn)

    def add_to_my_food(self, name=None, weight=None):
        print('LOGIC nm={} wt={}'.format(name, weight))
        if not isfloat(weight):
            raise ValueError('weight must be a number, weight = ', weight)
        cur, conn = dbi()
        weight = float(weight)
        name = name.capitalize()
        cur.execute('''
        SELECT food_id, food_name
        FROM nutrients
        WHERE aux_name = '{}' '''.format(aux_transform(name)))
        _id = cur.fetchone()
        print('_id =', _id)
        if _id is None:
            dbe(conn)
            return None
        else:
            print('Ok, found ' + _id[1])
        cur.execute('''
        INSERT INTO MyFoodTable (dt, tm, food_id, weight)
        VALUES (now()::date, date_trunc('minute', now()::time), {}, {})
        '''.format(_id[0], weight))
        dbe(conn)
        return _id[1]

    def print_my_food(self):
        cur, conn = dbi()
        cur.execute('''SELECT * FROM MyFoodTable INNER JOIN nutrients
        ON nutrients.food_id = MyFoodTable.food_id ORDER BY (dt, tm)''')
        res = ['\ndate          time      weight      food_name\n']
        for i in cur.fetchall():
            hh, mm, ss = str(i[3]).split(':')
            tm = str(hh) + ':' + str(mm)
            dt = str(i[2])
            weight = (str(round(i[5], 2)) + 'g')
            name = i[7]
            res.append('%-14s%-10s%-12s%-20s' % (dt, tm, weight, name))
        dbe(conn)
        return '\n'.join(res)

    def actual_intake(self):
        sum_params = Counter()
        for key, _ in all_params:
            sum_params[key] = 0
        cur, conn = dbi()
        cur.execute('''
        SELECT food_id, sum(weight) FROM MyFoodTable
        WHERE dt = now()::date
        GROUP BY food_id
        ''')
        selfMy = dict()
        for key, val in cur.fetchall():
            selfMy[key] = val
        dbe(conn)
        for key in selfMy:
            cur, conn = dbi()
            cur.execute('''SELECT *
            FROM nutrients WHERE food_id = {}'''.format(key))
            CurFoodParams = cur.fetchall()[0]
            val = selfMy[key]
            # print(CurFoodParams)
            dbe(conn)
            for param in sum_params:
                if get_index.get(param) is None:
                    continue
                if CurFoodParams[get_index[param]] is None:
                    continue
                adding = CurFoodParams[get_index[param]] * val / 100
                sum_params[param] += adding
        res = ['\nNutrient intake summary\n\n']
        all_nut = sum(sum_params[i] for i in ('carb', 'fat', 'protein'))
        if all_nut > 0:
            get_val = lambda nm: sum_params[nm] / all_nut * 100
            res.append('Actual ratio:\n')
            vals = get_val('carb'), get_val('fat'), get_val('protein')
            template = '    carb: %.1f %%   fat: %.1f %%    protein: %.1f %%\n'
            res.append(template % vals)
        res.append('Recommended ratio:\n')
        res.append('    carb: 55.0 %   fat: 25.0 %   protein: 20.0 % \n\n')
        tab_fields = 'nutrient name', 'amount', 'type intake', 'min', 'max'
        res.append('%-20s%-14s%-20s%-6s%-6s\n\n' % tab_fields)
        for key, unit in all_params:
            val = sum_params[key]
            res.append('%-16s%8.1f %-9s' % (str(key), val, unit))
            if daily_norm.get(key) is not None:
                mn, mx = daily_norm[key]
                if val < mn:
                    type_intake = 'low intake'
                elif val > mx:
                    type_intake = 'high intake'
                else:
                    type_intake = 'recommended intake'
                res.append('%-20s%-6s%-6s' % (type_intake, str(mn), str(mx)))
            res.append('\n')
        return ''.join(res)

    def get_foodlist(self):
        cur, conn = dbi()
        cur.execute('SELECT food_name FROM nutrients ORDER BY food_name')
        res = ['FoodList:', '']
        for i in list(cur.fetchall()):
            res.append(i[0])
        dbe(conn)
        return '\n'.join(map(str, res))

    def search_food(self, pattern=None):
        if pattern is None:
            return ''
        cur, conn = dbi()
        query = ''' SELECT food_name
        FROM nutrients WHERE food_name LIKE '%{}%' '''
        cur.execute(query.format(pattern) +
                    ' union ' + query.format(pattern.capitalize()))
        data = cur.fetchall()
        dbe(conn)
        res = ['\nResults:'] + [i[0] for i in data]
        return res

    def delete_last(self):
        cur, conn = dbi()
        cur.execute("SELECT max(dt) FROM MyFoodTable")
        mx_dt = cur.fetchall()[0][0]
        if mx_dt is None:
            return
        cur.execute('''
        DELETE FROM MyFoodTable
        WHERE dt = '{0}'
        AND tm = (SELECT max(tm) FROM MyFoodTable
                WHERE dt = '{0}')
        '''.format(mx_dt))
        dbe(conn)

# -------------------------- DATABASE CREATING --------------------------


def aux_transform(word):
    word = re.split('-|\.|\(|\)| {,100}', word.strip())
    return ''.join(i[:5] for i in word)


def create_nutrients():
    cur, conn = dbi()
    cur.execute(''' DROP TABLE IF EXISTS nutrients; ''')
    cur.execute('''
    CREATE TABLE nutrients(
    food_id integer primary key,
    food_name varchar(255),
    aux_name varchar(255)''' +
    (', {} float default 0' * len(fields)).format(*tuple(fields)) + ')')
    dbe(conn)


def fill_nutrients_from_site(flag_create=0, debug=0):

    def get_cur_val(param):
        if param in ["carb", "fat", "protein"]:
            par = param
            if par == 'carb':
                par = 'carbohydrate'
            curl = 'href="https://fitaudit.ru/nutrients/{}">'.format(par)
            index = cur_s.find(curl)
            template = 'tbl-value">(\d{,10}.\d{,10})'
        elif param == 'calories':
            index = cur_s.find('Калорийность')
            template = '>(\d{,10}.\d{,10})кКал'
        elif param == 'fibre':
            index = cur_s.find('клетчатки')
            template = '>(\d{,10}.\d{,10})г</span>'
        else:
            index = cur_s.find(tr[param])
            template = 'tbl-value">(\d{,10}.\d{,10})'
        cur_t = form(cur_s[index:index + 200])
        arr_val = re.findall(template, cur_t)
        if len(arr_val) == 0:
            return None
        return float(arr_val[0])

    FILE = os.getcwd() + '\\db_data\\fitaudit.html'
    url = 'https://fitaudit.ru/food/abc'
    if flag_create or not os.path.isfile(FILE):
        print('create FILE')
        s = requests.get(url).text
        with open(FILE, 'w', encoding='utf-8') as fout:
            fout.write(s)
    with open(FILE, 'r', encoding='utf-8') as fin:
        s = fin.read()
    tr = {
        'calories': 'Калорийность',
        'carb': 'Углеводы',
        'fat': 'Жиры',
        'protein': 'Белки',
        'fibre': 'клетчатки',
        'potassium': 'Калий',
        'vitaminA': 'Витамин А',
        'vitaminC': 'Витамин C',
        'calcium': 'Кальций',
        'iron': 'Железо',
        'sodium': 'Натрий',
    }
    last_time = time()
    cur, conn = dbi()
    form = lambda s: s.replace('\n', '').replace(' ', '').replace(',', '.')
    num_links = re.findall('foodsprite-(\d{6})', s)
    for number in num_links:
        cur_url = 'https://fitaudit.ru/food/{}'.format(number)
        cur_file = '{}\\db_data\\fitaudit{}.html'.format(os.getcwd(), number)
        if not os.path.isfile(cur_file):
            cur_s = requests.get(cur_url).text
            with open(cur_file, 'w', encoding='utf-8') as fout:
                fout.write(cur_s)
        with open(cur_file, 'r', encoding='utf-8') as fin:
            cur_s = fin.read().replace('\t', '')
        template = '>(.+?) — химический состав, пищевая ценность'
        arr_name = re.findall(template, cur_s)
        if len(arr_name) == 0:
            continue
        food_name = arr_name[0]
        cur.execute('''
        INSERT INTO nutrients (food_id, food_name, aux_name)
        VALUES ( coalesce((select max(food_id) from nutrients), 0) + 1,
                 '{0}',
                 '{1}')
        '''.format(food_name, aux_transform(food_name)))
        for param in tr.keys():
            cur_val = get_cur_val(param)
            if cur_val is not None:
                cur.execute('''
                UPDATE nutrients
                SET {} = {}
                WHERE food_name = '{}'
                '''.format(param, cur_val, food_name))
    dbe(conn)
    print('site fitaudit finished!', 'TIME =', time() - last_time)


def create_MyFoodTable():
    cur, conn = dbi()
    cur.execute(''' DROP TABLE IF EXISTS MyFoodTable ''')
    cur.execute('''
        CREATE TABLE MyFoodTable (
            person_id integer,
            person_name varchar(255),
            dt date,
            tm time,
            food_id integer not null,
            weight float
        )
    ''')
    dbe(conn)


def init_db(mft_flag=True):
    print('Started DB Creating')
    create_nutrients()
    fill_nutrients_from_site()
    if mft_flag:
        print('Creating MyFoodTable')
        create_MyFoodTable()
    print('Finished DB Creating')
