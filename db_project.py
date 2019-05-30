from random import *
from config import *
import psycopg2
from collections import *

def dbi():
    global cur, conn
    with psycopg2.connect(dbname=DBNAME,
                          user=USER,
                          password=PASSWORD,
                          host='127.0.0.1') as conn:
        cur = conn.cursor()


def dbe():
    conn.commit()
    conn.close()
    
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


dates = ['2019-05-24', '2019-05-23', '2019-05-22']

times = ['09:00', '14:00', '16:30', '19:00']
    
names = [
    'Kate',
    'Andrey',
    'Piter',
    'Ann',
    'Artem',
    'Mikhail',
    'Alexander',
    'Dmitry',
    'Nikita',
    'Petr',
    'Vladimir',
    'Maxim',
    'Sergey',
    'Polina',
    'ELena',
    'Pavel',
    'PersonA',
    'PersonB',
    'PersonC',
    'PersonD',
    'PersonE',
    'PersonF',
]

def generate_name():
    return choice(names)

def fill_begin():
    dbi()
    cur.execute('''
    INSERT INTO categories (food_type)
    VALUES (''), ('fruit'), ('vegetable'), ('meat'), ('milk'), ('sweat'), ('bigfat')
    ON CONFLICT DO NOTHING;
    ''')
    cur.execute('''
    INSERT INTO cooking
    VALUES ('raw'), ('fry'), ('boil'), ('dry')
    ON CONFLICT DO NOTHING;
    ''')
    cur.execute('''
    INSERT INTO daily_noms (nutrient_name, min_val, max_val, nutrient_unit)
    VALUES
           ('calories', 2000, 3000, 'kcal'),
           ('carb', NULL, NULL, 'g'),
           ('fat', NULL, NULL, 'g'),
           ('protein', 56, 300, 'g'),
           ('fibre', 38, 100, 'g'),
           ('potassium', 4700, 11000, 'mg'),
           ('vitaminA', 900, 3000, 'mcg'),
           ('vitaminC', 90, 2000, 'mg'),
           ('calcium', 1000, 2500, 'mg'),
           ('iron', 8, 45, 'mg'),
           ('sodium', 1500, 2300, 'mg')
    ON CONFLICT DO NOTHING;
    ''')
    cur.execute('''
    INSERT INTO diets
    VALUES
           (1, 'Atkins'),
           (2, 'Semi-vegetarianism'),
           (3, 'Ovo vegetarianism'),
           (4, 'Intermittent fasting'),
           (5, 'Dukan Diet'),
           (6, 'Low-fat diet')
    ON CONFLICT DO NOTHING;
    ''')
    dbe()


def fill_persons():
    dbi()
    vals = []
    cur.execute('DELETE FROM Persons;')    
    for i in range(1, 101):
        vals.append("({}, '{}')".format(i, generate_name()))
    query = 'INSERT INTO Persons VALUES ' + ','.join(vals) + ';'
    cur.execute(query)
    dbe()


def fill_food():
    def get_food_type(food_name):
        cur.execute("SELECT * FROM Nutrients WHERE food_name = '{}' ".format(food_name))
        data = cur.fetchall()[0]
        if data[7] > 8:
            return 'vegetable'
        if data[4] > 18 and data[7] > 2:
            return 'fruit'
        if data[4] > 50:
            return 'sweat'
        if data[11] > 100:
            return 'milk'
        if data[4] > 18:
            return 'bigfat'
        if data[6] > 4:
            return 'meat'        
        return ''
    dbi()
    cur.execute('SELECT food_name FROM Nutrients;')
    arr = cur.fetchall()
    cur.execute('DELETE FROM food;')
    cur.execute("INSERT INTO food VALUES (0, '', '');")
    for i in range(len(arr)):
        food_name = arr[i][0]
        food_type = get_food_type(food_name)
        cur.execute('''
        INSERT INTO Food VALUES
        ({}, '{}', '{}')
        ON CONFLICT DO NOTHING;
        '''.format(i + 1, food_name, food_type))
        print(food_name)
    dbe()


def fill_dish():
    dbi()
    cur.execute('DELETE FROM dish_composition;')    
    cur.execute('DELETE FROM dishes;')
    cur.execute('INSERT INTO Dishes (dish_id) VALUES (0);')
    for i in range(1, 101):
        cnt_ingr = randint(1, 4)
        cur.execute('''
        SELECT food_id FROM food
        ORDER BY RANDOM() LIMIT {};
        '''.format(cnt_ingr))
        data1 = cur.fetchall()
        dish_name = 'Dish{}'.format(i)
        cur.execute('''
        INSERT INTO dishes VALUES ({}, '{}');
        '''.format(i, dish_name))
        for j in range(cnt_ingr):
            cur.execute('''
            INSERT INTO dish_composition VALUES
            ({}, {}, (SELECT cooking_type
                    FROM cooking ORDER BY RANDOM() LIMIT 1), {});
            '''.format(i, data1[j][0], randint(1, 100)))
    dbe()
    

def fill_meals():
    dbi()
    cur.execute("DELETE FROM Meals_composition;")    
    cur.execute("DELETE FROM Meals;")
    for i in range(1, 301):
        cur.execute('''
        INSERT INTO Meals
        VALUES ({});
        '''.format(i))
        cnt_f = randint(0, 4)
        for j in range(cnt_f):
            cur.execute('''
            INSERT INTO Meals_composition
            VALUES ({}, 0, (SELECT food_id
            FROM Food ORDER BY RANDOM() LIMIT 1), {})
            ON CONFLICT DO NOTHING
            '''.format(i, randint(1, 100)))
        if cnt_f <= 1:
            cnt_d = randint(2, 4)
        else:
            cnt_d = choice([0, 0, 0, 1, 2])
        for j in range(cnt_d):
            cur.execute('''
            INSERT INTO Meals_composition
            VALUES ({}, (SELECT dish_id
            FROM dishes ORDER BY RANDOM() LIMIT 1), 0, 0)
            ON CONFLICT DO NOTHING
            '''.format(i))
    dbe()

def fill_persons_food():
    dbi()
    cur.execute("DELETE FROM Persons_food;")    
    for i in range(1, 101):
        cnt_m = randint(2, 3 + i // 10)
        for j in range(cnt_m):
            dt = choice(dates)
            tm = choice(times)
            cur.execute('''
            INSERT INTO Persons_food VALUES
            ({},
            (SELECT meal_id FROM Meals ORDER BY RANDOM() LIMIT 1), 
            '{}', '{}')
            ON CONFLICT DO NOTHING;
            '''.format(i, dt, tm))
    dbe()

def fill_food_recomendations():
    dbi()
    cur.execute("DELETE FROM food_recomendations;")
    for i in range(1, 6):
        cnt_f = 5
        for j in range(cnt_f):
            flag = "True" if random() < 0.5 else "False"
            cur.execute('''
            INSERT INTO food_recomendations VALUES
            ({},
            (SELECT food_type FROM Categories ORDER BY RANDOM() LIMIT 1),
            (SELECT cooking_type FROM cooking ORDER BY RANDOM() LIMIT 1),
            {})
            ON CONFLICT DO NOTHING;
            '''.format(i, flag))
    dbe()
    
def fill_diets_for_persons():
    dbi()
    cur.execute("DELETE FROM diets_for_person;")
    for i in range(1, 100):
        for dt in dates:
            cur.execute('''
            INSERT INTO diets_for_person VALUES
            ({},
            (SELECT diet_id FROM diets ORDER BY RANDOM() LIMIT 1),
            '{}');
            '''.format(i, dt))
    dbe()
    
def rating(field):
    dbi()
    cur.execute('''
    CREATE OR REPLACE VIEW rating AS
    SELECT food_name, {0} from nutrients
    ORDER BY {0} DESC;
    '''.format(field))
    dbe()

def super_rating(view_name, agg_fun):
    dbi()
    cur.execute('''
    CREATE OR REPLACE VIEW {} AS
    SELECT food_name, ({}) as param from nutrients
    ORDER BY param desc;
    '''.format(view_name, agg_fun))
    dbe()


def get_foodlist(day, person_id):
    dbi()
    cur.execute('''
    SELECT meal_id FROM Persons_food
    WHERE dt = '{}' and person_id = {};
    '''.format(day, person_id))
    data = cur.fetchall()
    print(data)
    foods = Counter()
    meals = [i[0] for i in data]
    for meal_id in meals:
        cur.execute('''
        SELECT dish_id from meals_composition
        WHERE meal_id = {} and food_id = 0;
        '''.format(meal_id))
        data = cur.fetchall()
        dd = [i[0] for i in data]
        cur.execute('''
        SELECT food_id, sum(weight) from meals_composition
        WHERE meal_id = {} and dish_id = 0 group by food_id;
        '''.format(meal_id))
        data = cur.fetchall()
        ff = [(i[0], i[1]) for i in data]
        for food_id, w in ff:
            foods[food_id] += w
        for dish_id in dd:
            cur.execute('''
            SELECT food_id, sum(weight) from dish_composition
            WHERE dish_id = {} GROUP BY food_id;
            '''.format(dish_id))
            data = cur.fetchall()
            ff = [(i[0], i[1]) for i in data]
            for food_id, w in ff:
                foods[food_id] += w
    cur.execute('''
    DROP TABLE IF EXISTS Cur_count;
    CREATE TABLE cur_count (
    food_id integer,
    weight float
    )
    ''')
    for key in foods:
        val = foods[key]
        cur.execute('''
        INSERT INTO cur_count VALUES
        ({}, {}) '''.format(key, val))
    
    cur.execute('''
    DROP TABLE IF EXISTS cur_categories;
    CREATE TABLE cur_categories AS
    (select distinct food_type from Food
    where food_id in (select food_id from cur_count))
    ''')    
    dbe()

def actual_intake(key):
    dbi()
    
    dbe()
    
def how_intake(day, person_id):
    dbi()
    cur.execute('''
    select * from actual_intake('{}', {});
    '''.format(day, person_id))
    data = cur.fetchall()
    cur.execute('''
    DROP TABLE IF EXISTS intake;
    CREATE TABLE intake
    AS (SELECT nutrient_name,
    CAST(0 as float) as cur_intake,
    CAST('' as VARCHAR(255)) as type_intake,
    min_val,
    max_val,
    nutrient_unit
    FROM daily_norms
    );
    ''')
    for key, val in zip(fields, data[0]):
        print(key, val)
        cur.execute('''
        UPDATE intake
        SET cur_intake = {0},
        type_intake = (
            CASE WHEN {0} < min_val THEN 'low_intake'
            WHEN {0} > max_val THEN 'high_intake'
            ELSE 'recommended_intake'
            END
        )
        WHERE nutrient_name = '{1}'
        '''.format(val, key))
    dbe()

def get_cooking(day, person_id):
    dbi()
    cur.execute('''
    SELECT meal_id FROM Persons_food
    WHERE dt = '{}' and person_id = {};
    '''.format(day, person_id))
    data = cur.fetchall()
    print(data)
    meals = [i[0] for i in data]
    cur.execute('''
    DROP TABLE IF EXISTS cook_list;
    CREATE TABLE cook_list (
    cooking_type VARCHAR(255)
    )
    ''')
    for meal_id in meals:
        cur.execute('''
        SELECT dish_id from meals_composition
        WHERE meal_id = {} and food_id = 0;
        '''.format(meal_id))
        data = cur.fetchall()
        dd = [i[0] for i in data]
        for dish_id in dd:
            
            
            """cur.execute('''
            INSERT INTO cook_list VALUES (SELECT cooking_type FROM dish_composition
            WHERE dish_id = {});
            '''.format(dish_id))"""
            
            cur.execute('''
            SELECT cooking_type FROM dish_composition
            WHERE dish_id = {};
            '''.format(dish_id))
            data = cur.fetchall()
            for i in data:
                cur.execute('''
                INSERT INTO cook_list VALUES
                ('{}')
                '''.format(i[0]))
    dbe()

def observe(day, person_id):
    dbi()
    cur.execute('''
    SELECT diet_id FROM diets_for_person
    WHERE day = '{}' and person_id = {}
    '''.format(day, person_id))
    data = cur.fetchall()
    if len(data) == 0:
        return print('No diet')
    cur_diet = data[0][0]
    
    dbe()
    get_foodlist(day, person_id)
    get_cooking(day, person_id)
    dbi()
    cur.execute('''
    DROP TABLE IF EXISTS answer;
    CREATE TABLE answer AS
    (SELECT cooking_type from cook_list)
    intersect
    (SELECT cooking_type from food_recomendations
    where diet_id = {});
    '''.format(cur_diet))
    dbe()
    
    
"""
Соблюдает ли пользователь диету в конкретный день

"""