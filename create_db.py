import sqlite3

# Crear i connectar-se a la base de dades SQLite
conn = sqlite3.connect('activitats.db')
cursor = conn.cursor()

# Crear la taula activitats
cursor.execute('''
    CREATE TABLE IF NOT EXISTS activitats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        ubicacio TEXT NOT NULL,
        data TEXT NOT NULL,
        hora TEXT NOT NULL,
        categories TEXT NOT NULL
    )
''')

# Confirmar els canvis i tancar la connexió
conn.commit()
conn.close()

import sqlite3

# Connectar-se a la base de dades
conn = sqlite3.connect('activitats.db')
cursor = conn.cursor()

# Dades d'exemple
activitats = [
    ("Cursa Popular", "Parc Central", "2024-04-01", "10:00", ",Educació física,Carrera,Esports,"),
    ("Taller de Cuina", "Centre Cívic", "2024-04-05", "16:00", ",Cultura,Gastronomia,Tallers,"),
    ("Fira d'Ocupació", "Auditori Municipal", "2024-05-10", "09:00", ",Empleabilitat,Ocupació,Networking,"),
    ("Exposició d'Art", "Museu d'Art", "2024-05-15", "11:00", ",Cultura,Art,Exposicions,"),
    ("Classe de Ioga", "Platja", "2024-06-21", "08:00", ",Educació física,Salut,Bienestar,"),
    ("Conferència Administrativa", "Ajuntament", "2024-07-12", "14:00", ",Administració Pública,Formació,Conferències,")
]

# Inserir dades d'exemple a la taula
cursor.executemany('''
    INSERT INTO activitats (nom, ubicacio, data, hora, categories)
    VALUES (?, ?, ?, ?, ?)
''', activitats)

# Confirmar els canvis i tancar la connexió
conn.commit()
conn.close()

import sqlite3

# Connectar-se a la base de dades
conn = sqlite3.connect('activitats.db')
cursor = conn.cursor()

# Executar una consulta per obtenir totes les activitats
cursor.execute("SELECT * FROM activitats")
rows = cursor.fetchall()

# Mostrar els resultats
for row in rows:
    print(row)

# Tancar la connexió
conn.close()

def sql_query(categories):
    conn = sqlite3.connect('./activitats.db')
    cursor = conn.cursor()

    query = """
    SELECT nom, ubicacio, data, hora
    FROM activitats
    WHERE {}
    """.format(
        " OR ".join(["categories LIKE ?" for _ in categories])
    )

    params = [f'%,{category},%' for category in categories]

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    activitats = []
    for row in rows:
        activitats.append({
            "nom": row[0],
            "ubicacio": row[1],
            "data": row[2],
            "hora": row[3]
        })

    return activitats

categories_a_buscar = ["Cultura", "Educació física"]
resultats = sql_query(categories_a_buscar)
print(resultats)